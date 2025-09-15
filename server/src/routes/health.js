/**
 * Health check routes
 * Provides system health monitoring and status endpoints
 */

const express = require('express');
const rateLimit = require('express-rate-limit');
const winston = require('winston');

// Import health check functions
const { getDatabaseHealth } = require('../config/database');
const { getRedisHealth } = require('../config/redis');
const { SystemHealth, MLAnalysisRun } = require('../models');

const router = express.Router();

// Initialize logger
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  defaultMeta: { service: 'health-routes' },
  transports: [
    new winston.transports.Console(),
  ],
});

// Health check rate limiting (less restrictive for monitoring)
const healthLimiter = rateLimit({
  windowMs: 60 * 1000, // 1 minute
  max: 120, // Allow 120 health checks per minute
  standardHeaders: true,
  legacyHeaders: false,
});

// System start time for uptime calculation
const START_TIME = Date.now();

/**
 * Basic health check
 * Used by load balancers and monitoring systems
 */
router.get('/', healthLimiter, async (req, res) => {
  try {
    res.status(200).send('OK');
  } catch (error) {
    logger.error('Basic health check failed:', error);
    res.status(503).send('Service Unavailable');
  }
});

/**
 * Comprehensive health check
 * Returns detailed system status
 */
router.get('/status', healthLimiter, async (req, res) => {
  try {
    const startTime = Date.now();
    const healthChecks = {};

    // System information
    const uptime = Math.floor((Date.now() - START_TIME) / 1000);
    const memoryUsage = process.memoryUsage();

    // Database health
    healthChecks.database = await getDatabaseHealth();

    // Redis health
    healthChecks.redis = await getRedisHealth();

    // Trading workflows health
    healthChecks.signals = await checkSignalGenerationHealth();
    healthChecks.ml = await checkMLAnalysisHealth();
    healthChecks.mt5 = await checkMT5BridgeHealth();

    // Data services health
    healthChecks.oanda = await checkOandaAPIHealth();
    healthChecks.cme = await checkCMEDataHealth();
    healthChecks.gemini = await checkGeminiAPIHealth();
    healthChecks.sierra = await checkSierraChartHealth();

    // Overall system status
    const allHealthy = Object.values(healthChecks).every(
      check => check.status === 'healthy'
    );

    const totalResponseTime = Date.now() - startTime;

    const healthStatus = {
      service: 'AI Cash Revolution API',
      version: '1.0.0',
      status: allHealthy ? 'healthy' : 'degraded',
      timestamp: new Date().toISOString(),
      uptime: `${Math.floor(uptime / 86400)}d ${Math.floor((uptime % 86400) / 3600)}h ${Math.floor((uptime % 3600) / 60)}m`,
      responseTime: `${totalResponseTime}ms`,

      system: {
        nodeVersion: process.version,
        environment: process.env.NODE_ENV || 'development',
        memory: {
          used: `${Math.round(memoryUsage.heapUsed / 1024 / 1024)}MB`,
          total: `${Math.round(memoryUsage.heapTotal / 1024 / 1024)}MB`,
          external: `${Math.round(memoryUsage.external / 1024 / 1024)}MB`,
          rss: `${Math.round(memoryUsage.rss / 1024 / 1024)}MB`,
        },
        cpu: process.cpuUsage(),
      },

      services: healthChecks,
    };

    // Log detailed health status periodically (every 5 minutes)
    if (Math.floor(Date.now() / 300000) !== Math.floor((Date.now() - totalResponseTime) / 300000)) {
      logger.info('Comprehensive health check completed', {
        status: healthStatus.status,
        responseTime: totalResponseTime,
        services: Object.keys(healthChecks).reduce((acc, key) => {
          acc[key] = healthChecks[key].status;
          return acc;
        }, {}),
      });
    }

    // Return appropriate HTTP status
    const httpStatus = allHealthy ? 200 : 503;
    res.status(httpStatus).json(healthStatus);

  } catch (error) {
    logger.error('Comprehensive health check failed:', error);
    res.status(503).json({
      service: 'AI Cash Revolution API',
      status: 'unhealthy',
      timestamp: new Date().toISOString(),
      error: error.message,
    });
  }
});

/**
 * Readiness check
 * Used by orchestrators to determine if service is ready to accept traffic
 */
router.get('/ready', healthLimiter, async (req, res) => {
  try {
    // Check critical dependencies
    const dbHealth = await getDatabaseHealth();
    const redisHealth = await getRedisHealth();

    const isReady = dbHealth.status === 'healthy' && redisHealth.status === 'healthy';

    const status = {
      service: 'AI Cash Revolution API',
      status: isReady ? 'ready' : 'not ready',
      timestamp: new Date().toISOString(),
      checks: {
        database: dbHealth.status,
        redis: redisHealth.status,
      },
    };

    res.status(isReady ? 200 : 503).json(status);

  } catch (error) {
    logger.error('Readiness check failed:', error);
    res.status(503).json({
      service: 'AI Cash Revolution API',
      status: 'error',
      timestamp: new Date().toISOString(),
      error: error.message,
    });
  }
});

/**
 * Liveness check
 * Used by orchestrators to determine if service is alive (not stuck)
 */
router.get('/live', healthLimiter, async (req, res) => {
  try {
    // Simple liveness check - if we can respond, we're alive
    res.status(200).json({
      service: 'AI Cash Revolution API',
      status: 'alive',
      timestamp: new Date().toISOString(),
      pid: process.pid,
    });

  } catch (error) {
    logger.error('Liveness check failed:', error);
    res.status(503).json({
      service: 'AI Cash Revolution API',
      status: 'dead',
      timestamp: new Date().toISOString(),
      error: error.message,
    });
  }
});

/**
 * Service-specific health checks
 */

// Signal generation health
async function checkSignalGenerationHealth() {
  try {
    // Check if signal generation is working
    const now = new Date();
    const fiveMinutesAgo = new Date(now.getTime() - 5 * 60 * 1000);

    // Check for recent signal generations
    const recentSignals = await MLAnalysisRun.findMany({
      where: {
        runStatus: 'completed',
        updatedAt: {
          gte: fiveMinutesAgo,
        },
      },
      take: 1,
    });

    return {
      status: recentSignals.length > 0 ? 'healthy' : 'warning',
      lastActivity: recentSignals[0]?.updatedAt || null,
      message: recentSignals.length > 0
        ? 'Signal generation active'
        : 'No recent signal generation activity',
    };
  } catch (error) {
    return { status: 'unhealthy', error: error.message };
  }
}

// ML analysis health
async function checkMLAnalysisHealth() {
  try {
    // Check ML optimization loop
    const serviceName = 'ml-analysis';
    const health = await SystemHealth.checkService(serviceName);

    return health ? { status: 'healthy' } : { status: 'warning', message: 'ML service not reporting' };
  } catch (error) {
    return { status: 'unhealthy', error: error.message };
  }
}

// MT5 bridge health
async function checkMT5BridgeHealth() {
  try {
    const serviceName = 'mt5-bridge';
    const health = await SystemHealth.checkService(serviceName);

    return health ? { status: 'healthy' } : { status: 'degraded', message: 'MT5 connection issues' };
  } catch (error) {
    return { status: 'unhealthy', error: error.message };
  }
}

// External API health checks (placeholders - would need real implementations)
async function checkOandaAPIHealth() {
  return { status: 'unknown', message: 'API health check not implemented yet' };
}

async function checkCMEDataHealth() {
  return { status: 'unknown', message: 'CME data health check not implemented yet' };
}

async function checkGeminiAPIHealth() {
  return { status: 'unknown', message: 'Gemini API health check not implemented yet' };
}

async function checkSierraChartHealth() {
  return { status: 'unknown', message: 'Sierra Chart health check not implemented yet' };
}

module.exports = router;