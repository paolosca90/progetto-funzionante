/**
 * MT5 Bridge Service
 * Handles low-latency communication with MT5 trading platform
 */

const WebSocket = require('ws');
const winston = require('winston');
const { getPrismaClient } = require('../config/database');
const { SystemHealth, AuditLog } = require('../models');

const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  defaultMeta: { service: 'mt5-bridge' },
  transports: [
    new winston.transports.Console(),
  ],
});

// MT5 connection configuration
const MT5_CONFIG = {
  host: process.env.MT5_HOST || 'localhost',
  port: parseInt(process.env.MT5_PORT) || 9999,
  reconnectDelay: 5000,
  maxReconnectAttempts: 5,
  heartbeatInterval: 30000, // 30 seconds
  connectionTimeout: 10000, // 10 seconds
};

// Connection state
let mt5Socket = null;
let isConnected = false;
let reconnectAttempts = 0;
let lastHeartbeat = Date.now();
let connectionId = null;

/**
 * Initialize MT5 connection
 */
async function initializeMT5Connection() {
  try {
    logger.info('Initializing MT5 bridge connection...');

    connectToMT5();

    // Periodic health checks
    setInterval(async () => {
      const healthStatus = await checkMT5Health();
      await SystemHealth.updateServiceHealth('mt5-bridge', healthStatus.status);
    }, 60000); // Check every minute

  } catch (error) {
    logger.error('Failed to initialize MT5 connection:', error);
    await SystemHealth.updateServiceHealth('mt5-bridge', 'down', { error: error.message });
  }
}

/**
 * Connect to MT5 platform
 */
function connectToMT5() {
  try {
    if (mt5Socket && mt5Socket.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    logger.info(`Attempting to connect to MT5 at ${MT5_CONFIG.host}:${MT5_CONFIG.port}`);

    const wsUrl = `ws://${MT5_CONFIG.host}:${MT5_CONFIG.port}`;
    mt5Socket = new WebSocket(wsUrl, {
      handshakeTimeout: MT5_CONFIG.connectionTimeout,
    });

    // Connection event handlers
    mt5Socket.on('open', () => {
      isConnected = true;
      reconnectAttempts = 0;
      connectionId = `MT5-${Date.now()}`;
      lastHeartbeat = Date.now();

      logger.info(`MT5 connection established: ${connectionId}`);

      // Send initial handshake
      sendMT5Message({
        type: 'handshake',
        connectionId,
        timestamp: new Date().toISOString(),
      });

      // Start heartbeat
      startHeartbeat();
    });

    mt5Socket.on('message', (data) => {
      handleMT5Message(data);
    });

    mt5Socket.on('error', (error) => {
      logger.error('MT5 connection error:', error);
      isConnected = false;
    });

    mt5Socket.on('close', (code, reason) => {
      logger.warn(`MT5 connection closed: Code ${code}, Reason: ${reason}`);
      isConnected = false;

      // Attempt reconnection
      if (reconnectAttempts < MT5_CONFIG.maxReconnectAttempts) {
        reconnectAttempts++;
        logger.info(`Attempting reconnection ${reconnectAttempts}/${MT5_CONFIG.maxReconnectAttempts}`);
        setTimeout(connectToMT5, MT5_CONFIG.reconnectDelay);
      } else {
        logger.error('Max reconnection attempts reached');
        SystemHealth.updateServiceHealth('mt5-bridge', 'down', {
          error: 'Max reconnection attempts reached'
        });
      }
    });

  } catch (error) {
    logger.error('Failed to connect to MT5:', error);
  }
}

/**
 * Send message to MT5
 */
function sendMT5Message(message) {
  try {
    if (!mt5Socket || mt5Socket.readyState !== WebSocket.OPEN) {
      throw new Error('MT5 connection not available');
    }

    const messageStr = JSON.stringify(message);
    mt5Socket.send(messageStr);

    logger.debug('Message sent to MT5:', message.type);

  } catch (error) {
    logger.error('Failed to send message to MT5:', error);
    throw error;
  }
}

/**
 * Handle incoming messages from MT5
 */
function handleMT5Message(data) {
  try {
    const message = JSON.parse(data.toString());
    logger.debug('Received message from MT5:', message.type);

    switch (message.type) {
      case 'handshake_ack':
        handleHandshakeAck(message);
        break;

      case 'order_executed':
        handleOrderExecuted(message);
        break;

      case 'order_failed':
        handleOrderFailed(message);
        break;

      case 'balance_update':
        handleBalanceUpdate(message);
        break;

      case 'heartbeat_ack':
        lastHeartbeat = Date.now();
        break;

      default:
        logger.warn('Unknown message type from MT5:', message.type);
    }

  } catch (error) {
    logger.error('Failed to handle MT5 message:', error);
  }
}

/**
 * Execute a trading signal via MT5
 */
async function executeSignalViaMT5(signalId, userId, riskAmount) {
  try {
    logger.info(`Executing signal via MT5: ${signalId}, User: ${userId}, Risk: $${riskAmount}`);

    const prisma = getPrismaClient();

    // Get signal and user profile
    const signal = await prisma.tradingSignal.findFirst({
      where: {
        id: signalId,
        userId,
        status: { in: ['active', 'pending'] },
        expiresAt: { gt: new Date() },
      },
      include: {
        instrument: true,
        user: {
          include: {
            profiles: true,
          },
        },
      },
    });

    if (!signal) {
      throw new Error('Signal not found, expired, or already executed');
    }

    if (!signal.user.profiles?.[0]) {
      throw new Error('User MT5 credentials not configured');
    }

    const profile = signal.user.profiles[0];

    if (!profile.mt5Server || !profile.mt5Login) {
      throw new Error('Incomplete MT5 credentials');
    }

    // Calculate position sizing
    const lotSize = calculateLotSize(riskAmount, signal.stopLoss, signal.entryPrice);

    // Prepare MT5 execution request
    const executionData = {
      ticket: `EX-${Date.now()}`,
      signalId: signal.signalId,
      symbol: signal.instrument.symbol,
      operation: signal.direction === 'long' ? 'BUY' : 'SELL',
      lotSize: lotSize,
      price: signal.entryPrice,
      sl: signal.stopLoss,
      tp: signal.takeProfit,
      account: {
        server: profile.mt5Server,
        login: profile.mt5Login,
        // Password should be validated server-side for security
      },
      comment: `AI Signal: ${signal.signalId}`,
    };

    // Create execution record
    const execution = await prisma.signalExecution.create({
      data: {
        signalId,
        userId,
        mt5TicketId: executionData.ticket,
        executedPrice: signal.entryPrice,
        lotSize,
        riskAmount,
        actualStopLoss: signal.stopLoss,
        actualTakeProfit: signal.takeProfit,
        executionStatus: 'pending',
        notes: `MT5 execution initiated`,
      },
    });

    // Send execution request to MT5
    if (!isConnected) {
      throw new Error('MT5 connection unavailable');
    }

    sendMT5Message({
      type: 'execute_order',
      executionId: execution.id,
      data: executionData,
      timestamp: new Date().toISOString(),
    });

    logger.info(`MT5 execution initiated: ${execution.id}`);

    // Create audit log
    await prisma.auditLog.create({
      data: {
        userId,
        action: 'signal_execution_initiated',
        resource: 'signal_execution',
        resourceId: execution.id,
        newValues: {
          lotSize,
          riskAmount,
          symbol: signal.instrument.symbol,
        },
      },
    });

    return execution;

  } catch (error) {
    logger.error('Signal execution failed:', error);
    throw new Error(`MT5 execution failed: ${error.message}`);
  }
}

/**
 * Calculate position sizing based on risk amount
 */
function calculateLotSize(riskAmount, stopLoss, entryPrice) {
  try {
    // Calculate pip risk
    const pipRisk = Math.abs(entryPrice - stopLoss) * 10000; // in pips (4 decimal places)
    const lotSize = riskAmount / (pipRisk * 10); // Assuming $10 per pip per lot

    // Min/Max limits
    const minLotSize = 0.01;
    const maxLotSize = 10.0;

    return Math.max(minLotSize, Math.min(maxLotSize, lotSize));

  } catch (error) {
    logger.error('Lot size calculation failed:', error);
    return 0.01; // Default minimum
  }
}

/**
 * Handle MT5 response messages
 */
async function handleHandshakeAck(message) {
  logger.info('MT5 handshake acknowledged');
}

async function handleOrderExecuted(message) {
  try {
    const prisma = getPrismaClient();

    // Update execution status
    await prisma.signalExecution.update({
      where: { id: message.executionId },
      data: {
        executionStatus: 'executed',
        executedPrice: message.executedPrice,
        executedAt: new Date(),
        notes: `MT5 execution successful. Ticket: ${message.mt5Ticket}`,
      },
    });

    logger.info(`Order executed successfully: ${message.executionId}`);

  } catch (error) {
    logger.error('Failed to update executed order:', error);
  }
}

async function handleOrderFailed(message) {
  try {
    const prisma = getPrismaClient();

    await prisma.signalExecution.update({
      where: { id: message.executionId },
      data: {
        executionStatus: 'failed',
        executedAt: new Date(),
        notes: `MT5 execution failed: ${message.error}`,
      },
    });

    logger.error(`Order execution failed: ${message.executionId}, Error: ${message.error}`);

  } catch (error) {
    logger.error('Failed to update failed order:', error);
  }
}

async function handleBalanceUpdate(message) {
  // Handle account balance updates
  logger.debug('Balance update received:', message.data);
}

/**
 * Heartbeat mechanism
 */
function startHeartbeat() {
  setInterval(() => {
    if (isConnected && mt5Socket.readyState === WebSocket.OPEN) {
      sendMT5Message({
        type: 'heartbeat',
        timestamp: new Date().toISOString(),
      });
    }
  }, MT5_CONFIG.heartbeatInterval);
}

/**
 * Check MT5 health status
 */
async function checkMT5Health() {
  try {
    const timeSinceLastHeartbeat = Date.now() - lastHeartbeat;
    const isHealthy = isConnected && timeSinceLastHeartbeat < (MT5_CONFIG.heartbeatInterval * 2);

    return {
      status: isHealthy ? 'healthy' : 'degraded',
      connected: isConnected,
      lastHeartbeat: new Date(lastHeartbeat).toISOString(),
      reconnectAttempts,
      connectionId,
    };

  } catch (error) {
    logger.error('MT5 health check failed:', error);
    return {
      status: 'unhealthy',
      error: error.message,
    };
  }
}

/**
 * Get MT5 account information
 */
async function getAccountInfo(mt5Server, mt5Login) {
  try {
    if (!isConnected) {
      throw new Error('MT5 connection unavailable');
    }

    return new Promise((resolve, reject) => {
      const requestId = `REQ-${Date.now()}`;

      const timeout = setTimeout(() => {
        reject(new Error('Account info request timeout'));
      }, 5000);

      // Set up one-time response handler for this request
      const originalHandler = mt5Socket.onmessage;
      mt5Socket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          if (message.requestId === requestId) {
            clearTimeout(timeout);
            mt5Socket.onmessage = originalHandler;
            resolve(message.data);
          }
        } catch (error) {
          // Continue listening
        }
      };

      // Send request
      sendMT5Message({
        type: 'get_account_info',
        requestId,
        account: { server: mt5Server, login: mt5Login },
        timestamp: new Date().toISOString(),
      });
    });

  } catch (error) {
    logger.error('Failed to get account info:', error);
    throw error;
  }
}

module.exports = {
  initializeMT5Connection,
  executeSignalViaMT5,
  checkMT5Health,
  getAccountInfo,
};