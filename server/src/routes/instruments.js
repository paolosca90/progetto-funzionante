/**
 * Trading instruments routes
 * Handles instrument listing, details, and instrument-related data
 */

const express = require('express');
const rateLimit = require('express-rate-limit');
const { param, query, validationResult } = require('express-validator');
const { getPrismaClient } = require('../config/database');
const { getCacheKey, setCacheKey } = require('../config/redis');
const winston = require('winston');

const router = express.Router();

// Initialize logger
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  defaultMeta: { service: 'instruments-routes' },
  transports: [
    new winston.transports.Console(),
  ],
});

// Rate limiting for instrument endpoints
const instrumentsLimiter = rateLimit({
  windowMs: 60 * 1000, // 1 minute
  max: 60, // Allow 60 requests per minute (1 per second)
  message: {
    error: 'Too many instrument requests, please try again later.',
    retryAfter: '60 seconds',
  },
  standardHeaders: true,
  legacyHeaders: false,
});

// Validation middleware
const validatePagination = [
  query('page')
    .optional()
    .isInt({ min: 1 })
    .withMessage('Page must be a positive integer'),
  query('limit')
    .optional()
    .isInt({ min: 1, max: 100 })
    .withMessage('Limit must be between 1 and 100'),
  query('type')
    .optional()
    .isIn(['forex', 'commodity', 'index'])
    .withMessage('Type must be forex, commodity, or index'),
  query('category')
    .optional()
    .isIn(['major', 'minor', 'exotic', 'energy', 'metals', 'indices'])
    .withMessage('Invalid category specified'),
];

const validateInstrumentId = [
  param('instrumentId')
    .isUUID()
    .withMessage('Valid instrument ID is required'),
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

// Cache key constants
const INSTRUMENTS_CACHE_KEY = 'trading_instruments:active';
const CACHE_TTL = 300; // 5 minutes

/**
 * Get list of available trading instruments
 */
router.get('/',
  instrumentsLimiter,
  validatePagination,
  handleValidationErrors,
  async (req, res) => {
    try {
      const {
        page = 1,
        limit = 50,
        type,
        category,
        search
      } = req.query;

      const pageNum = parseInt(page);
      const limitNum = parseInt(limit);
      const offset = (pageNum - 1) * limitNum;

      // Try to get from cache first
      let instruments;
      let totalCount;
      let fromCache = false;

      if (!search && pageNum === 1 && !req.fresh) {
        const cacheKey = `${INSTRUMENTS_CACHE_KEY}:${type || 'all'}:${category || 'all'}:${limitNum}`;
        try {
          const cachedData = await getCacheKey(cacheKey);
          if (cachedData && cachedData.instruments && cachedData.totalCount) {
            instruments = cachedData.instruments;
            totalCount = cachedData.totalCount;
            fromCache = true;
          }
        } catch (cacheError) {
          logger.warn('Failed to read from cache:', cacheError);
        }
      }

      // If not in cache, fetch from database
      if (!fromCache) {
        const prisma = getPrismaClient();

        const whereClause = { isActive: true };

        if (type) {
          whereClause.type = type;
        }

        if (category) {
          whereClause.category = category;
        }

        if (search) {
          whereClause.OR = [
            { symbol: { contains: search, mode: 'insensitive' } },
            { name: { contains: search, mode: 'insensitive' } },
          ];
        }

        const [instrumentsData, count] = await Promise.all([
          prisma.tradingInstrument.findMany({
            where: whereClause,
            select: {
              id: true,
              symbol: true,
              name: true,
              type: true,
              category: true,
              pipValue: true,
              contractSize: true,
              metadata: true,
            },
            orderBy: [
              { type: 'asc' },
              { category: 'asc' },
              { symbol: 'asc' },
            ],
            skip: offset,
            take: limitNum,
          }),
          prisma.tradingInstrument.count({ where: whereClause }),
        ]);

        instruments = instrumentsData;
        totalCount = count;

        // Cache the results if it's the first page and no search
        if (pageNum === 1 && !search) {
          const cacheKey = `${INSTRUMENTS_CACHE_KEY}:${type || 'all'}:${category || 'all'}:${limitNum}`;
          try {
            await setCacheKey(cacheKey, { instruments, totalCount }, CACHE_TTL);
          } catch (cacheError) {
            logger.warn('Failed to write to cache:', cacheError);
          }
        }
      }

      const totalPages = Math.ceil(totalCount / limitNum);

      logger.info(`Retrieved ${instruments.length} instruments (page ${pageNum}/${totalPages}, cache: ${fromCache})`);

      res.json({
        instruments,
        pagination: {
          currentPage: pageNum,
          totalPages,
          totalCount,
          hasNext: pageNum < totalPages,
          hasPrev: pageNum > 1,
        },
        cached: fromCache,
        timestamp: new Date().toISOString(),
      });

    } catch (error) {
      logger.error('Error retrieving instruments:', error);
      res.status(500).json({
        error: 'Failed to retrieve trading instruments',
        timestamp: new Date().toISOString(),
      });
    }
  }
);

/**
 * Get instrument categories and types
 */
router.get('/categories', instrumentsLimiter, async (req, res) => {
  try {
    const prisma = getPrismaClient();

    // Get unique types and categories from active instruments
    const types = await prisma.tradingInstrument.findMany({
      where: { isActive: true },
      select: {
        type: true,
        category: true,
      },
      distinct: ['type', 'category'],
      orderBy: [
        { type: 'asc' },
        { category: 'asc' },
      ],
    });

    // Group categories by type
    const groupedCategories = types.reduce((acc, item) => {
      if (!acc[item.type]) {
        acc[item.type] = [];
      }
      if (!acc[item.type].includes(item.category)) {
        acc[item.type].push(item.category);
      }
      return acc;
    }, {});

    const instrumentTypes = Object.keys(groupedCategories);

    res.json({
      instrumentTypes,
      categoriesByType: groupedCategories,
      timestamp: new Date().toISOString(),
    });

  } catch (error) {
    logger.error('Error retrieving instrument categories:', error);
    res.status(500).json({
      error: 'Failed to retrieve instrument categories',
      timestamp: new Date().toISOString(),
    });
  }
});

/**
 * Get detailed information about a specific instrument
 */
router.get('/:instrumentId',
  instrumentsLimiter,
  validateInstrumentId,
  handleValidationErrors,
  async (req, res) => {
    try {
      const { instrumentId } = req.params;

      const prisma = getPrismaClient();

      const instrument = await prisma.tradingInstrument.findFirst({
        where: {
          id: instrumentId,
          isActive: true,
        },
      });

      if (!instrument) {
        return res.status(404).json({
          error: 'Trading instrument not found',
          timestamp: new Date().toISOString(),
        });
      }

      // Get recent volume analysis data if available
      const recentVolumeData = await prisma.volumeAnalysisData.findMany({
        where: {
          instrument: instrument.symbol,
          date: {
            gte: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000), // Last 7 days
          },
        },
        orderBy: {
          date: 'desc',
        },
        take: 7, // Last 7 data points
      });

      // Get recent signal performance for this instrument
      const performanceData = await prisma.mLSignalPerformance.findMany({
        where: {
          instrument: instrument.symbol,
          executionTime: {
            gte: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), // Last 30 days
          },
        },
        select: {
          pnlPoints: true,
          pnlAmount: true,
          executionTime: true,
          signalType: true,
        },
        orderBy: {
          executionTime: 'desc',
        },
        take: 100,
      });

      // Calculate basic statistics
      const totalSignals = performanceData.length;
      const profitableSignals = performanceData.filter(p => (p.pnlAmount || 0) > 0).length;
      const winRate = totalSignals > 0 ? (profitableSignals / totalSignals) * 100 : 0;
      const avgProfit = totalSignals > 0 ?
        performanceData.reduce((sum, p) => sum + (p.pnlAmount || 0), 0) / totalSignals : 0;

      logger.info(`Retrieved details for instrument: ${instrument.symbol}`);

      res.json({
        instrument: {
          id: instrument.id,
          symbol: instrument.symbol,
          name: instrument.name,
          type: instrument.type,
          category: instrument.category,
          pipValue: instrument.pipValue,
          contractSize: instrument.contractSize,
          metadata: instrument.metadata,
          createdAt: instrument.createdAt,
        },
        analytics: {
          recentVolume: recentVolumeData.slice(0, 3), // Last 3 days
          statistics: {
            totalSignals,
            winRate: Math.round(winRate * 100) / 100,
            avgProfit: Math.round(avgProfit * 100) / 100,
          },
        },
        timestamp: new Date().toISOString(),
      });

    } catch (error) {
      logger.error('Error retrieving instrument details:', error);
      res.status(500).json({
        error: 'Failed to retrieve instrument details',
        timestamp: new Date().toISOString(),
      });
    }
  }
);

/**
 * Get real-time quotes for an instrument
 * This is a placeholder - in production this would integrate with trading APIs
 */
router.get('/:instrumentId/quote',
  instrumentsLimiter,
  validateInstrumentId,
  handleValidationErrors,
  async (req, res) => {
    try {
      const { instrumentId } = req.params;

      const prisma = getPrismaClient();
      const instrument = await prisma.tradingInstrument.findUnique({
        where: { id: instrumentId },
      });

      if (!instrument) {
        return res.status(404).json({
          error: 'Trading instrument not found',
          timestamp: new Date().toISOString(),
        });
      }

      // TODO: Integrate with Oanda/Trading API for real quotes
      // This is a placeholder response
      const mockQuote = {
        instrument: instrument.symbol,
        bid: 1.0850,
        ask: 1.0852,
        spread: 0.02,
        timestamp: new Date().toISOString(),
        source: 'mock',
      };

      res.json({
        quote: mockQuote,
        notice: 'Real-time quotes integration pending',
        timestamp: new Date().toISOString(),
      });

    } catch (error) {
      logger.error('Error retrieving instrument quote:', error);
      res.status(500).json({
        error: 'Failed to retrieve instrument quote',
        timestamp: new Date().toISOString(),
      });
    }
  }
);

module.exports = router;