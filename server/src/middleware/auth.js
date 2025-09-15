/**
 * Authentication middleware
 * Handles JWT validation and user authentication
 */

const jwt = require('jsonwebtoken');
const { getPrismaClient } = require('../config/database');
const winston = require('winston');

const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  defaultMeta: { service: 'auth-middleware' },
  transports: [
    new winston.transports.Console(),
  ],
});

/**
 * JWT authentication middleware
 * Validates JWT token and attaches user to request
 */
async function authenticate(req, res, next) {
  try {
    // Get token from Authorization header
    const authHeader = req.headers.authorization;

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res.status(401).json({
        error: 'Access token required',
        message: 'Authentication token must be provided in Authorization header',
        timestamp: new Date().toISOString(),
      });
    }

    const token = authHeader.substring(7); // Remove 'Bearer ' prefix

    // Verify token
    let decoded;
    try {
      decoded = jwt.verify(token, process.env.JWT_SECRET);
    } catch (tokenError) {
      let errorMessage = 'Invalid authentication token';
      let statusCode = 401;

      if (tokenError.name === 'TokenExpiredError') {
        errorMessage = 'Authentication token has expired';
        statusCode = 401;
      } else if (tokenError.name === 'JsonWebTokenError') {
        errorMessage = 'Invalid token format';
        statusCode = 401;
      } else {
        errorMessage = 'Token verification failed';
        statusCode = 500;
      }

      logger.warn(`JWT verification failed:`, { error: tokenError.message, token: token.substring(0, 20) + '...' });

      return res.status(statusCode).json({
        error: errorMessage,
        timestamp: new Date().toISOString(),
      });
    }

    // Verify user exists and is active
    const prisma = getPrismaClient();
    const user = await prisma.user.findUnique({
      where: { id: decoded.userId },
      select: {
        id: true,
        email: true,
        firstName: true,
        lastName: true,
        isActive: true,
        subscriptionStatus: true,
        createdAt: true,
        updatedAt: true,
      },
    });

    if (!user) {
      return res.status(401).json({
        error: 'User not found',
        message: 'The user associated with this token no longer exists',
        timestamp: new Date().toISOString(),
      });
    }

    if (!user.isActive) {
      return res.status(403).json({
        error: 'Account disabled',
        message: 'Your account has been disabled. Please contact support.',
        timestamp: new Date().toISOString(),
      });
    }

    // Attach user to request object
    req.user = user;

    // Log successful authentication (only in debug mode for performance)
    if (logger.level === 'debug') {
      logger.debug(`User authenticated: ${user.email}`);
    }

    next();

  } catch (error) {
    logger.error('Authentication middleware error:', error);
    res.status(500).json({
      error: 'Authentication service temporarily unavailable',
      timestamp: new Date().toISOString(),
    });
  }
}

/**
 * Optional authentication middleware
 * Doesn't require authentication but attaches user if token is valid
 */
async function optionalAuthenticate(req, res, next) {
  try {
    const authHeader = req.headers.authorization;

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      // No token provided, continue without user
      return next();
    }

    const token = authHeader.substring(7);

    try {
      const decoded = jwt.verify(token, process.env.JWT_SECRET);

      const prisma = getPrismaClient();
      const user = await prisma.user.findUnique({
        where: { id: decoded.userId },
        select: {
          id: true,
          email: true,
          firstName: true,
          lastName: true,
          isActive: true,
          subscriptionStatus: true,
        },
      });

      if (user && user.isActive) {
        req.user = user;
      }
    } catch (error) {
      // Invalid token, but continue without user
      logger.debug('Optional authentication failed:', error.message);
    }

    next();

  } catch (error) {
    // Continue without user on error
    next();
  }
}

/**
 * Subscription-based access control middleware
 * Checks if user has required subscription level
 */
function requireSubscription(minimumPlan = 'free') {
  const planHierarchy = {
    'free': 0,
    'trial': 1,
    'basic': 2,
    'premium': 3,
    'enterprise': 4,
  };

  return (req, res, next) => {
    if (!req.user) {
      return res.status(401).json({
        error: 'Authentication required',
        timestamp: new Date().toISOString(),
      });
    }

    const userPlan = req.user.subscriptionStatus || 'free';
    const minPlanLevel = planHierarchy[minimumPlan] || 0;
    const userPlanLevel = planHierarchy[userPlan] || 0;

    if (userPlanLevel < minPlanLevel) {
      return res.status(403).json({
        error: 'Insufficient subscription',
        message: `This feature requires ${minimumPlan} plan or higher. Current plan: ${userPlan}`,
        timestamp: new Date().toISOString(),
      });
    }

    next();
  };
}

/**
 * Role-based access control middleware
 * Checks if user has required role/permissions
 */
function requirePermission(permission) {
  return (req, res, next) => {
    if (!req.user) {
      return res.status(401).json({
        error: 'Authentication required',
        timestamp: new Date().toISOString(),
      });
    }

    // TODO: Implement role-based permissions system
    // For now, allow all authenticated users
    // In future versions, check user.roles or user.permissions

    const userPermissions = req.user.permissions || [];

    if (!userPermissions.includes(permission)) {
      return res.status(403).json({
        error: 'Insufficient permissions',
        message: `Required permission: ${permission}`,
        timestamp: new Date().toISOString(),
      });
    }

    next();
  };
}

/**
 * Admin-only access middleware
 * Restricts access to admin users only
 */
function requireAdmin(req, res, next) {
  if (!req.user) {
    return res.status(401).json({
      error: 'Authentication required',
      timestamp: new Date().toISOString(),
    });
  }

  // TODO: Implement admin role checking
  // Check if user has admin role or is in admin user list
  const isAdmin = req.user.isAdmin === true ||
                  req.user.email?.endsWith('@aicash-revolution.com') ||
                  false;

  if (!isAdmin) {
    return res.status(403).json({
      error: 'Admin access required',
      message: 'This endpoint is restricted to administrators',
      timestamp: new Date().toISOString(),
    });
  }

  next();
}

/**
 * Refresh token middleware
 * Handles JWT token refresh without re-authentication
 */
async function refreshToken(req, res) {
  try {
    const { refreshToken } = req.body;

    if (!refreshToken) {
      return res.status(400).json({
        error: 'Refresh token required',
        timestamp: new Date().toISOString(),
      });
    }

    // Verify refresh token
    let decoded;
    try {
      decoded = jwt.verify(refreshToken, process.env.JWT_REFRESH_SECRET || process.env.JWT_SECRET);
    } catch (error) {
      return res.status(401).json({
        error: 'Invalid refresh token',
        timestamp: new Date().toISOString(),
      });
    }

    // Verify user still exists and is active
    const prisma = getPrismaClient();
    const user = await prisma.user.findUnique({
      where: { id: decoded.userId },
      select: { id: true, isActive: true },
    });

    if (!user || !user.isActive) {
      return res.status(401).json({
        error: 'User not found or inactive',
        timestamp: new Date().toISOString(),
      });
    }

    // Generate new access token
    const newToken = jwt.sign(
      { userId: user.id },
      process.env.JWT_SECRET,
      { expiresIn: process.env.JWT_EXPIRY || '24h' }
    );

    // Optionally generate new refresh token
    const newRefreshToken = jwt.sign(
      { userId: user.id },
      process.env.JWT_REFRESH_SECRET || process.env.JWT_SECRET,
      { expiresIn: process.env.JWT_REFRESH_EXPIRY || '7d' }
    );

    logger.info(`Token refreshed for user: ${user.id}`);

    res.json({
      message: 'Token refreshed successfully',
      token: newToken,
      refreshToken: newRefreshToken,
      timestamp: new Date().toISOString(),
    });

  } catch (error) {
    logger.error('Token refresh error:', error);
    res.status(500).json({
      error: 'Token refresh failed',
      timestamp: new Date().toISOString(),
    });
  }
}

module.exports = {
  authenticate,
  optionalAuthenticate,
  requireSubscription,
  requirePermission,
  requireAdmin,
  refreshToken,
};