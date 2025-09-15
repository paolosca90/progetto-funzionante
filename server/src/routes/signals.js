/**
 * Trading signals routes
 * Handles signal generation, execution, and history retrieval
 */

const express = require('express');
const rateLimit = require('express-rate-limit');
const { body, param, query, validationResult } = require('express-validator');
const { authenticate } = require('../middleware/auth');
const { getPrismaClient } = require('../config/database');
const winston = require('winston');

const router = express.Router();

// Initialize logger
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  defaultMeta: { service: 'signals-routes' },
  transports: [
    new winston.transports.Console(),
  ],
});

// Rate limiting for signal operations
const signalLimiter = rateLimit({
  windowMs: 60 * 1000, // 1 minute
  max: 10, // Limit to 10 signal generations per minute
  message: {
    error: 'Too many signal requests, please wait before generating another signal.',
    retryAfter: '60 seconds',
  },
  standardHeaders: true,
  legacyHeaders: false,
});

// Validation middleware
const validateSignalGeneration = [
  body('instrumentId')
    .isUUID()
    .withMessage('Valid instrument ID is required'),
  body('riskPercentage')
    .optional()
    .isFloat({ min: 0.1, max: 5.0 })
    .withMessage('Risk percentage must be between 0.1% and 5.0%'),
];

const validateSignalExecution = [
  param('signalId')
    .isUUID()
    .withMessage('Valid signal ID is required'),
  body('riskAmount')
    .isFloat({ min: 1, max: 10000 })
    .withMessage('Risk amount must be between $1 and $10,000'),
];

const validatePagination = [
  query('page')
    .optional()
    .isInt({ min: 1 })
    .withMessage('Page must be a positive integer'),
  query('limit')
    .optional()
    .isInt({ min: 1, max: 100 })
    .withMessage('Limit must be between 1 and 100'),
];

// Validation error handler
const handleValidationErrors = (req, res, next) => {
  const errors = validationResult(req);
  if (!errors.isEmpty()) {
    return res.status(400).json({
      error: 'Validation failed',
      details: errors.array(),
      timestamp: new Date().toISOString(),
    });
  }
  next();
};

/**
 * Generate a new trading signal
 */
router.post('/generate',
  authenticate,
  signalLimiter,
  validateSignalGeneration,
  handleValidationErrors,
  async (req, res) => {
    try {
      const { instrumentId, riskPercentage = 1.0 } = req.body;
      const userId = req.user.id;

      logger.info(`Signal generation requested: User ${userId}, Instrument ${instrumentId}`);

      // Import signal generation service
      const { generateTradingSignal } = require('../services/signal-generator');

      // Generate the signal
      const signal = await generateTradingSignal(userId, instrumentId, riskPercentage);

      logger.info(`Signal generated successfully: ${signal.id}`);

      res.status(201).json({
        message: 'Trading signal generated successfully',
        signal: {
          id: signal.id,
          signalId: signal.signalId,
          instrument: {
            symbol: signal.instrument.symbol,
            name: signal.instrument.name,
          },
          direction: signal.direction,
          confidence: signal.confidence,
          entryPrice: signal.entryPrice,
          stopLoss: signal.stopLoss,
          takeProfit: signal.takeProfit,
          riskRewardRatio: signal.riskRewardRatio,
          motivations: signal.motivations,
          expiresAt: signal.expiresAt,
          createdAt: signal.generatedAt,
        },
        timestamp: new Date().toISOString(),
      });

    } catch (error) {
      logger.error('Error generating trading signal:', error);
      res.status(500).json({
        error: 'Failed to generate trading signal',
        timestamp: new Date().toISOString(),
      });
    }
  }
);

/**
 * Get user's active signals
 */
router.get('/active',
  authenticate,
  validatePagination,
  handleValidationErrors,
  async (req, res) => {
    try {
      const userId = req.user.id;
      const page = parseInt(req.query.page) || 1;
      const limit = parseInt(req.query.limit) || 20;
      const offset = (page - 1) * limit;

      const prisma = getPrismaClient();

      const [signals, totalCount] = await Promise.all([
        prisma.tradingSignal.findMany({
          where: {
            userId,
            status: 'active',
            expiresAt: {
              gt: new Date(),
            },
          },
          include: {
            instrument: {
              select: {
                symbol: true,
                name: true,
                type: true,
              },
            },
          },
          orderBy: {
            generatedAt: 'desc',
          },
          skip: offset,
          take: limit,
        }),
        prisma.tradingSignal.count({
          where: {
            userId,
            status: 'active',
            expiresAt: {
              gt: new Date(),
            },
          },
        }),
      ]);

      const totalPages = Math.ceil(totalCount / limit);

      res.json({
        signals: signals.map(signal => ({
          id: signal.id,
          signalId: signal.signalId,
          instrument: signal.instrument,
          direction: signal.direction,
          confidence: signal.confidence,
          entryPrice: signal.entryPrice,
          stopLoss: signal.stopLoss,
          takeProfit: signal.takeProfit,
          riskRewardRatio: signal.riskRewardRatio,
          motivations: signal.motivations,
          expiresAt: signal.expiresAt,
          createdAt: signal.generatedAt,
        })),
        pagination: {
          currentPage: page,
          totalPages,
          totalCount,
          hasNext: page < totalPages,
          hasPrev: page > 1,
        },
        timestamp: new Date().toISOString(),
      });

    } catch (error) {
      logger.error('Error retrieving active signals:', error);
      res.status(500).json({
        error: 'Failed to retrieve active signals',
        timestamp: new Date().toISOString(),
      });
    }
  }
);

/**
 * Get signal history
 */
router.get('/history',
  authenticate,
  validatePagination,
  handleValidationErrors,
  async (req, res) => {
    try {
      const userId = req.user.id;
      const page = parseInt(req.query.page) || 1;
      const limit = parseInt(req.query.limit) || 20;
      const offset = (page - 1) * limit;
      const status = req.query.status; // active, expired, executed, cancelled

      const prisma = getPrismaClient();

      const whereClause = { userId };
      if (status) {
        whereClause.status = status;
      }

      const [signals, totalCount] = await Promise.all([
        prisma.tradingSignal.findMany({
          where: whereClause,
          include: {
            instrument: {
              select: {
                symbol: true,
                name: true,
                type: true,
              },
            },
            executions: {
              select: {
                executedPrice: true,
                actualStopLoss: true,
                actualTakeProfit: true,
                executionStatus: true,
                executedAt: true,
                pnlAmount: true,
              },
            },
          },
          orderBy: {
            generatedAt: 'desc',
          },
          skip: offset,
          take: limit,
        }),
        prisma.tradingSignal.count({ where: whereClause }),
      ]);

      const totalPages = Math.ceil(totalCount / limit);

      res.json({
        signals: signals.map(signal => ({
          id: signal.id,
          signalId: signal.signalId,
          instrument: signal.instrument,
          direction: signal.direction,
          confidence: signal.confidence,
          entryPrice: signal.entryPrice,
          stopLoss: signal.stopLoss,
          takeProfit: signal.takeProfit,
          riskRewardRatio: signal.riskRewardRatio,
          motivations: signal.motivations,
          status: signal.status,
          expiresAt: signal.expiresAt,
          createdAt: signal.generatedAt,
          executions: signal.executions,
        })),
        pagination: {
          currentPage: page,
          totalPages,
          totalCount,
          hasNext: page < totalPages,
          hasPrev: page > 1,
        },
        timestamp: new Date().toISOString(),
      });

    } catch (error) {
      logger.error('Error retrieving signal history:', error);
      res.status(500).json({
        error: 'Failed to retrieve signal history',
        timestamp: new Date().toISOString(),
      });
    }
  }
);

/**
 * Execute a trading signal via MT5
 */
router.post('/:signalId/execute',
  authenticate,
  validateSignalExecution,
  handleValidationErrors,
  async (req, res) => {
    try {
      const { signalId } = req.params;
      const { riskAmount } = req.body;
      const userId = req.user.id;

      logger.info(`Signal execution requested: User ${userId}, Signal ${signalId}, Risk Amount: $${riskAmount}`);

      // Import MT5 execution service
      const { executeSignalViaMT5 } = require('../services/mt5-bridge');

      // Execute the signal
      const execution = await executeSignalViaMT5(signalId, userId, riskAmount);

      logger.info(`Signal executed successfully: Execution ID ${execution.id}`);

      res.json({
        message: 'Signal execution initiated',
        execution: {
          id: execution.id,
          signalId: execution.signalId,
          executedPrice: execution.executedPrice,
          lotSize: execution.lotSize,
          riskAmount: execution.riskAmount,
          executionStatus: execution.executionStatus,
          executedAt: execution.executedAt,
        },
        timestamp: new Date().toISOString(),
      });

    } catch (error) {
      logger.error('Error executing trading signal:', error);

      // Handle different types of errors
      let statusCode = 500;
      let errorMessage = 'Failed to execute trading signal';

      if (error.message.includes('signal not found')) {
        statusCode = 404;
        errorMessage = 'Trading signal not found';
      } else if (error.message.includes('MT5 connection')) {
        statusCode = 503;
        errorMessage = 'MT5 connection temporarily unavailable';
      } else if (error.message.includes('balance')) {
        statusCode = 400;
        errorMessage = 'Insufficient account balance for execution';
      }

      res.status(statusCode).json({
        error: errorMessage,
        timestamp: new Date().toISOString(),
      });
    }
  }
);

/**
 * Get specific signal details
 */
router.get('/:signalId',
  authenticate,
  param('signalId').isUUID().withMessage('Valid signal ID is required'),
  handleValidationErrors,
  async (req, res) => {
    try {
      const { signalId } = req.params;
      const userId = req.user.id;

      const prisma = getPrismaClient();

      const signal = await prisma.tradingSignal.findFirst({
        where: {
          id: signalId,
          userId,
        },
        include: {
          instrument: {
            select: {
              id: true,
              symbol: true,
              name: true,
              type: true,
              category: true,
            },
          },
          executions: {
            select: {
              id: true,
              executedPrice: true,
              lotSize: true,
              riskAmount: true,
              actualStopLoss: true,
              actualTakeProfit: true,
              executionStatus: true,
              pnlAmount: true,
              executedAt: true,
            },
            orderBy: {
              executedAt: 'desc',
            },
          },
        },
      });

      if (!signal) {
        return res.status(404).json({
          error: 'Trading signal not found',
          timestamp: new Date().toISOString(),
        });
      }

      res.json({
        signal: {
          id: signal.id,
          signalId: signal.signalId,
          instrument: signal.instrument,
          direction: signal.direction,
          confidence: signal.confidence,
          entryPrice: signal.entryPrice,
          stopLoss: signal.stopLoss,
          takeProfit: signal.takeProfit,
          riskRewardRatio: signal.riskRewardRatio,
          timeFrame: signal.timeFrame,
          motivations: signal.motivations,
          analysisResults: signal.analysisResults,
          status: signal.status,
          expiresAt: signal.expiresAt,
          createdAt: signal.generatedAt,
          executions: signal.executions,
        },
        timestamp: new Date().toISOString(),
      });

    } catch (error) {
      logger.error('Error retrieving signal details:', error);
      res.status(500).json({
        error: 'Failed to retrieve signal details',
        timestamp: new Date().toISOString(),
      });
    }
  }
);

module.exports = router;