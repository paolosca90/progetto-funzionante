/**
 * User profile routes
 * Handles user profile management, MT5 credentials, and subscription info
 */

const express = require('express');
const rateLimit = require('express-rate-limit');
const { body, validationResult } = require('express-validator');
const { authenticate } = require('../middleware/auth');
const { getPrismaClient } = require('../config/database');
const bcrypt = require('bcryptjs');
const winston = require('winston');

const router = express.Router();

// Initialize logger
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  defaultMeta: { service: 'profile-routes' },
  transports: [
    new winston.transports.Console(),
  ],
});

// Rate limiting for profile operations
const profileLimiter = rateLimit({
  windowMs: 60 * 1000, // 1 minute
  max: 30, // Allow 30 profile operations per minute
  message: {
    error: 'Too many profile requests, please try again later.',
    retryAfter: '60 seconds',
  },
  standardHeaders: true,
  legacyHeaders: false,
});

const credentialsLimiter = rateLimit({
  windowMs: 5 * 60 * 1000, // 5 minutes
  max: 5, // Limit credential updates
  message: {
    error: 'Too many credential updates, please wait before trying again.',
    retryAfter: '5 minutes',
  },
});

// Validation middleware
const validateProfileUpdate = [
  body('firstName')
    .optional()
    .isLength({ min: 1, max: 50 })
    .withMessage('First name must be between 1 and 50 characters'),
  body('lastName')
    .optional()
    .isLength({ min: 1, max: 50 })
    .withMessage('Last name must be between 1 and 50 characters'),
  body('riskPercentage')
    .optional()
    .isFloat({ min: 0.1, max: 5.0 })
    .withMessage('Risk percentage must be between 0.1% and 5.0%'),
  body('maxDailyLoss')
    .optional()
    .isFloat({ min: 0 })
    .withMessage('Maximum daily loss must be a positive number'),
];

const validateMTCredentials = [
  body('server')
    .isLength({ min: 3, max: 100 })
    .withMessage('MT5 server must be between 3 and 100 characters'),
  body('login')
    .isLength({ min: 5, max: 10 })
    .matches(/^\d+$/)
    .withMessage('MT5 login must be numeric and between 5-10 digits'),
  body('password')
    .isLength({ min: 8, max: 50 })
    .withMessage('MT5 password must be between 8 and 50 characters'),
];

// Encryption helper for sensitive data
async function encryptData(data) {
  // In production, use proper encryption (e.g., AES-256)
  // For now, using bcrypt as a placeholder (not recommended for encryption)
  const saltRounds = 12;
  return await bcrypt.hash(data, saltRounds);
}

async function decryptData(encryptedData, originalData) {
  // This is a placeholder - proper decryption would be needed
  // For demo purposes, we'll verify the data matches
  return encryptedData; // Placeholder
}

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
 * Get user profile
 */
router.get('/',
  authenticate,
  profileLimiter,
  async (req, res) => {
    try {
      const userId = req.user.id;
      const prisma = getPrismaClient();

      const user = await prisma.user.findUnique({
        where: { id: userId },
        include: {
          profiles: {
            select: {
              riskPercentage: true,
              maxDailyLoss: true,
              preferredInstruments: true,
              notificationSettings: true,
              createdAt: true,
              updatedAt: true,
            },
          },
          subscription: {
            select: {
              plan: true,
              startDate: true,
              endDate: true,
              isActive: true,
              nextPaymentDate: true,
            },
          },
        },
      });

      if (!user) {
        return res.status(404).json({
          error: 'User not found',
          timestamp: new Date().toISOString(),
        });
      }

      // Check MT5 credentials existence (without revealing them)
      const hasMTCredentials = await prisma.userProfile.findUnique({
        where: { userId },
        select: {
          mt5Server: true,
          mt5Login: true,
        },
      });

      res.json({
        profile: {
          id: user.id,
          email: user.email,
          firstName: user.firstName,
          lastName: user.lastName,
          profilePicture: user.profilePicture,
          isActive: user.isActive,
          subscriptionStatus: user.subscriptionStatus,
          riskPercentage: user.profiles?.[0]?.riskPercentage || 1.0,
          maxDailyLoss: user.profiles?.[0]?.maxDailyLoss,
          preferredInstruments: user.profiles?.[0]?.preferredInstruments,
          notificationSettings: user.profiles?.[0]?.notificationSettings,
          subscription: user.subscription,
          hasMTCredentials: !!(hasMTCredentials?.mt5Server && hasMTCredentials?.mt5Login),
        },
        timestamp: new Date().toISOString(),
      });

    } catch (error) {
      logger.error('Error retrieving user profile:', error);
      res.status(500).json({
        error: 'Failed to retrieve user profile',
        timestamp: new Date().toISOString(),
      });
    }
  }
);

/**
 * Update user profile
 */
router.put('/',
  authenticate,
  profileLimiter,
  validateProfileUpdate,
  handleValidationErrors,
  async (req, res) => {
    try {
      const userId = req.user.id;
      const { firstName, lastName, riskPercentage, maxDailyLoss } = req.body;
      const prisma = getPrismaClient();

      // Update user basic info
      const userUpdate = {};
      if (firstName !== undefined) userUpdate.firstName = firstName;
      if (lastName !== undefined) userUpdate.lastName = lastName;

      // Update profile settings
      const profileUpdate = {};
      if (riskPercentage !== undefined) profileUpdate.riskPercentage = riskPercentage;
      if (maxDailyLoss !== undefined) profileUpdate.maxDailyLoss = maxDailyLoss;

      // Execute updates in transaction
      const result = await prisma.$transaction(async (tx) => {
        const updatedUser = {};
        if (Object.keys(userUpdate).length > 0) {
          updatedUser.user = await tx.user.update({
            where: { id: userId },
            data: userUpdate,
          });
        }

        let updatedProfile = null;
        if (Object.keys(profileUpdate).length > 0) {
          updatedProfile = await tx.userProfile.upsert({
            where: { userId },
            update: profileUpdate,
            create: { userId, ...profileUpdate },
          });
        }

        // Create audit log
        await tx.auditLog.create({
          data: {
            userId,
            action: 'profile_updated',
            resource: 'user_profile',
            resourceId: userId,
            oldValues: { /* would need to track old values */ },
            newValues: { ...userUpdate, ...profileUpdate },
          },
        });

        return { updatedUser, updatedProfile };
      });

      logger.info(`Profile updated for user: ${userId}`);

      res.json({
        message: 'Profile updated successfully',
        changes: {
          user: !!result.updatedUser,
          profile: !!result.updatedProfile,
        },
        timestamp: new Date().toISOString(),
      });

    } catch (error) {
      logger.error('Error updating user profile:', error);
      res.status(500).json({
        error: 'Failed to update user profile',
        timestamp: new Date().toISOString(),
      });
    }
  }
);

/**
 * Update MT5 credentials
 */
router.put('/mt5-credentials',
  authenticate,
  credentialsLimiter,
  validateMTCredentials,
  handleValidationErrors,
  async (req, res) => {
    try {
      const userId = req.user.id;
      const { server, login, password } = req.body;
      const prisma = getPrismaClient();

      // Encrypt sensitive data
      const encryptedPassword = await encryptData(password);

      // Update MT5 credentials
      const updatedProfile = await prisma.userProfile.upsert({
        where: { userId },
        update: {
          mt5Server: server,
          mt5Login: login,
          mt5Password: encryptedPassword,
        },
        create: {
          userId,
          mt5Server: server,
          mt5Login: login,
          mt5Password: encryptedPassword,
        },
      });

      // Create audit log (without sensitive data)
      await prisma.auditLog.create({
        data: {
          userId,
          action: 'mt5_credentials_updated',
          resource: 'user_profile',
          resourceId: userId,
          newValues: { mt5Server: server, mt5Login: login },
        },
      });

      logger.info(`MT5 credentials updated for user: ${userId}`);

      res.json({
        message: 'MT5 credentials updated successfully',
        timestamp: new Date().toISOString(),
      });

    } catch (error) {
      logger.error('Error updating MT5 credentials:', error);
      res.status(500).json({
        error: 'Failed to update MT5 credentials',
        timestamp: new Date().toISOString(),
      });
    }
  }
);

/**
 * Test MT5 connection
 */
router.post('/test-mt5-connection',
  authenticate,
  rateLimit({
    windowMs: 5 * 60 * 1000, // 5 minutes
    max: 3, // Limit connection tests
    message: {
      error: 'Too many connection tests, please wait before trying again.',
      retryAfter: '5 minutes',
    },
  }),
  async (req, res) => {
    try {
      const userId = req.user.id;
      const prisma = getPrismaClient();

      // Get MT5 credentials
      const profile = await prisma.userProfile.findUnique({
        where: { userId },
        select: {
          mt5Server: true,
          mt5Login: true,
          mt5Password: true,
        },
      });

      if (!profile?.mt5Server || !profile?.mt5Login || !profile?.mt5Password) {
        return res.status(400).json({
          error: 'MT5 credentials not configured',
          timestamp: new Date().toISOString(),
        });
      }

      // TODO: Implement actual MT5 connection test
      // This is a placeholder response
      const testResult = {
        server: profile.mt5Server,
        login: profile.mt5Login,
        connected: true,
        balance: null, // Would be retrieved from MT5
        demo: profile.mt5Server.includes('demo') || profile.mt5Server.includes('practice'),
      };

      logger.info(`MT5 connection test for user: ${userId} - Success`);

      res.json({
        message: 'MT5 connection test completed',
        connection: testResult,
        notice: 'Actual MT5 integration pending',
        timestamp: new Date().toISOString(),
      });

    } catch (error) {
      logger.error('Error testing MT5 connection:', error);
      res.status(500).json({
        error: 'MT5 connection test failed',
        details: error.message,
        timestamp: new Date().toISOString(),
      });
    }
  }
);

/**
 * Update notification preferences
 */
router.put('/notifications',
  authenticate,
  profileLimiter,
  async (req, res) => {
    try {
      const userId = req.user.id;
      const notificationSettings = req.body;
      const prisma = getPrismaClient();

      // Validate notification settings structure
      const validKeys = [
        'emailAlerts', 'pushNotifications', 'signalAlerts',
        'executionAlerts', 'performanceReports', 'dailySummary'
      ];

      const invalidKeys = Object.keys(notificationSettings).filter(
        key => !validKeys.includes(key)
      );

      if (invalidKeys.length > 0) {
        return res.status(400).json({
          error: 'Invalid notification preference keys',
          invalidKeys,
          timestamp: new Date().toISOString(),
        });
      }

      // Update notification settings
      await prisma.userProfile.upsert({
        where: { userId },
        update: { notificationSettings },
        create: { userId, notificationSettings },
      });

      logger.info(`Notification preferences updated for user: ${userId}`);

      res.json({
        message: 'Notification preferences updated successfully',
        preferences: notificationSettings,
        timestamp: new Date().toISOString(),
      });

    } catch (error) {
      logger.error('Error updating notification preferences:', error);
      res.status(500).json({
        error: 'Failed to update notification preferences',
        timestamp: new Date().toISOString(),
      });
    }
  }
);

/**
 * Update preferred instruments and risk settings
 */
router.put('/trading-preferences',
  authenticate,
  profileLimiter,
  async (req, res) => {
    try {
      const userId = req.user.id;
      const { preferredInstruments } = req.body;
      const prisma = getPrismaClient();

      // Validate preferred instruments
      if (preferredInstruments) {
        const instrumentIds = Array.isArray(preferredInstruments)
          ? preferredInstruments
          : Object.keys(preferredInstruments);

        if (instrumentIds.length > 0) {
          // Check if instruments exist and are active
          const existingInstruments = await prisma.tradingInstrument.findMany({
            where: {
              id: { in: instrumentIds },
              isActive: true,
            },
            select: { id: true },
          });

          const validInstrumentIds = existingInstruments.map(inst => inst.id);

          if (validInstrumentIds.length !== instrumentIds.length) {
            return res.status(400).json({
              error: 'Some specified instruments are not available',
              validInstruments: validInstrumentIds,
              timestamp: new Date().toISOString(),
            });
          }
        }
      }

      // Update trading preferences
      await prisma.userProfile.upsert({
        where: { userId },
        update: { preferredInstruments },
        create: { userId, preferredInstruments },
      });

      logger.info(`Trading preferences updated for user: ${userId}`);

      res.json({
        message: 'Trading preferences updated successfully',
        preferences: { preferredInstruments },
        timestamp: new Date().toISOString(),
      });

    } catch (error) {
      logger.error('Error updating trading preferences:', error);
      res.status(500).json({
        error: 'Failed to update trading preferences',
        timestamp: new Date().toISOString(),
      });
    }
  }
);

module.exports = router;