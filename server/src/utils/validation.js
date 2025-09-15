/**
 * Validation utilities and helpers
 */

const Joi = require('joi');

/**
 * User registration validation schema
 */
const userRegistrationSchema = Joi.object({
  email: Joi.string()
    .email()
    .lowercase()
    .required()
    .messages({
      'string.email': 'Please provide a valid email address',
      'string.empty': 'Email is required',
    }),

  password: Joi.string()
    .min(8)
    .pattern(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/)
    .required()
    .messages({
      'string.min': 'Password must be at least 8 characters long',
      'string.pattern.base': 'Password must contain at least one uppercase letter, one lowercase letter, and one number',
      'string.empty': 'Password is required',
    }),

  firstName: Joi.string()
    .min(1)
    .max(50)
    .optional()
    .messages({
      'string.min': 'First name must be at least 1 character long',
      'string.max': 'First name must not exceed 50 characters',
    }),

  lastName: Joi.string()
    .min(1)
    .max(50)
    .optional()
    .messages({
      'string.min': 'Last name must be at least 1 character long',
      'string.max': 'Last name must not exceed 50 characters',
    }),
});

/**
 * User login validation schema
 */
const userLoginSchema = Joi.object({
  email: Joi.string()
    .email()
    .lowercase()
    .required()
    .messages({
      'string.email': 'Please provide a valid email address',
      'string.empty': 'Email is required',
    }),

  password: Joi.string()
    .required()
    .messages({
      'string.empty': 'Password is required',
    }),
});

/**
 * Profile update validation schema
 */
const profileUpdateSchema = Joi.object({
  firstName: Joi.string()
    .min(1)
    .max(50)
    .optional()
    .messages({
      'string.min': 'First name must be at least 1 character long',
      'string.max': 'First name must not exceed 50 characters',
    }),

  lastName: Joi.string()
    .min(1)
    .max(50)
    .optional()
    .messages({
      'string.min': 'Last name must be at least 1 character long',
      'string.max': 'Last name must not exceed 50 characters',
    }),

  riskPercentage: Joi.number()
    .min(0.1)
    .max(5.0)
    .optional()
    .messages({
      'number.min': 'Risk percentage must be at least 0.1%',
      'number.max': 'Risk percentage must not exceed 5.0%',
    }),

  maxDailyLoss: Joi.number()
    .min(0)
    .optional()
    .messages({
      'number.min': 'Maximum daily loss must be a positive number',
    }),
});

/**
 * MT5 credentials validation schema
 */
const mt5CredentialsSchema = Joi.object({
  server: Joi.string()
    .min(3)
    .max(100)
    .required()
    .messages({
      'string.min': 'MT5 server must be at least 3 characters long',
      'string.max': 'MT5 server must not exceed 100 characters',
      'string.empty': 'MT5 server is required',
    }),

  login: Joi.string()
    .pattern(/^\d+$/)
    .min(5)
    .max(10)
    .required()
    .messages({
      'string.pattern.base': 'MT5 login must contain only numbers',
      'string.min': 'MT5 login must be at least 5 digits',
      'string.max': 'MT5 login must not exceed 10 digits',
      'string.empty': 'MT5 login is required',
    }),

  password: Joi.string()
    .min(8)
    .max(50)
    .required()
    .messages({
      'string.min': 'MT5 password must be at least 8 characters long',
      'string.max': 'MT5 password must not exceed 50 characters',
      'string.empty': 'MT5 password is required',
    }),
});

/**
 * Signal generation validation schema
 */
const signalGenerationSchema = Joi.object({
  instrumentId: Joi.string()
    .uuid()
    .required()
    .messages({
      'string.uuid': 'Valid instrument ID is required',
      'string.empty': 'Instrument ID is required',
    }),

  riskPercentage: Joi.number()
    .min(0.1)
    .max(5.0)
    .optional()
    .default(1.0)
    .messages({
      'number.min': 'Risk percentage must be at least 0.1%',
      'number.max': 'Risk percentage must not exceed 5.0%',
    }),
});

/**
 * Pagination validation schema
 */
const paginationSchema = Joi.object({
  page: Joi.number()
    .integer()
    .min(1)
    .optional()
    .messages({
      'number.min': 'Page must be at least 1',
    }),

  limit: Joi.number()
    .integer()
    .min(1)
    .max(100)
    .optional()
    .messages({
      'number.min': 'Limit must be at least 1',
      'number.max': 'Limit must not exceed 100',
    }),
});

/**
 * Generic validation helper
 */
function validateData(data, schema) {
  const { error, value } = schema.validate(data, { abortEarly: false });

  if (error) {
    const details = error.details.map(detail => ({
      field: detail.path.join('.'),
      message: detail.message,
    }));

    return {
      valid: false,
      error: {
        message: 'Validation failed',
        details,
      },
    };
  }

  return {
    valid: true,
    data: value,
  };
}

/**
 * Express middleware for validation
 */
function createValidationMiddleware(schema) {
  return (req, res, next) => {
    const { valid, data, error } = validateData(req.body, schema);

    if (!valid) {
      return res.status(400).json({
        error: 'Validation failed',
        details: error.details,
        timestamp: new Date().toISOString(),
      });
    }

    // Replace request body with validated data
    req.body = data;
    next();
  };
}

/**
 * Sanitize input data
 */
function sanitizeInput(input) {
  if (typeof input !== 'string') {
    return input;
  }

  // Basic XSS prevention
  return input
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;')
    .replace(/\//g, '&#x2F;');
}

/**
 * Validate email format
 */
function isValidEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * Validate password strength
 */
function validatePasswordStrength(password) {
  const strongRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]/;

  if (password.length < 8) {
    return { valid: false, reason: 'Password must be at least 8 characters long' };
  }

  if (!strongRegex.test(password)) {
    return { valid: false, reason: 'Password must contain at least one uppercase letter, one lowercase letter, one number, and one special character' };
  }

  return { valid: true };
}

/**
 * Validate instrument symbol format
 */
function isValidInstrumentSymbol(symbol) {
  // Forex: EURUSD, GBPUSD, etc.
  // Commodities: XAUUSD, XAGUSD, etc.
  // Indices: NASDAQ, SPX, etc.
  const symbolRegex = /^[A-Z]{3,6}(USD|EUR|GBP|JPY|CHF|CAD|AUD|NZD)?$/;
  return symbolRegex.test(symbol) || ['NASDAQ', 'SPX'].includes(symbol);
}

module.exports = {
  userRegistrationSchema,
  userLoginSchema,
  profileUpdateSchema,
  mt5CredentialsSchema,
  signalGenerationSchema,
  paginationSchema,
  validateData,
  createValidationMiddleware,
  sanitizeInput,
  isValidEmail,
  validatePasswordStrength,
  isValidInstrumentSymbol,
};