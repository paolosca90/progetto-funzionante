/**
 * Winston Logger Configuration for AI Cash Revolution
 * Comprehensive logging system for production monitoring
 */

const winston = require('winston');
const path = require('path');

// Define log levels
const levels = {
  error: 0,
  warn: 1,
  info: 2,
  http: 3,
  debug: 4,
};

// Define log colors
const colors = {
  error: 'red',
  warn: 'yellow',
  info: 'green',
  http: 'magenta',
  debug: 'white',
};

// Tell winston that we want to link the colors
winston.addColors(colors);

// Define which logs to show based on environment
const level = () => {
  const env = process.env.NODE_ENV || 'development';
  const isDevelopment = env === 'development';
  return isDevelopment ? 'debug' : 'warn';
};

// Define log format
const format = winston.format.combine(
  winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss:ms' }),
  winston.format.colorize({ all: true }),
  winston.format.printf(
    (info) => `${info.timestamp} ${info.level}: ${info.message}`
  )
);

// Define transports
const transports = [
  // Console transport
  new winston.transports.Console({
    format: winston.format.combine(
      winston.format.colorize({ all: true }),
      winston.format.simple()
    )
  }),

  // Error log file
  new winston.transports.File({
    filename: path.join(process.cwd(), 'logs', 'error.log'),
    level: 'error',
    format: winston.format.combine(
      winston.format.timestamp(),
      winston.format.json()
    )
  }),

  // Combined log file
  new winston.transports.File({
    filename: path.join(process.cwd(), 'logs', 'combined.log'),
    format: winston.format.combine(
      winston.format.timestamp(),
      winston.format.json()
    )
  })
];

// Create the logger instance
const logger = winston.createLogger({
  level: level(),
  levels,
  format,
  transports,
  exitOnError: false
});

// Create logs directory if it doesn't exist
const fs = require('fs');
const logsDir = path.join(process.cwd(), 'logs');
if (!fs.existsSync(logsDir)) {
  fs.mkdirSync(logsDir, { recursive: true });
}

// Trading-specific logging methods
logger.trade = (message, data = {}) => {
  logger.info(`[TRADE] ${message}`, data);
};

logger.signal = (message, data = {}) => {
  logger.info(`[SIGNAL] ${message}`, data);
};

logger.mt5 = (message, data = {}) => {
  logger.info(`[MT5] ${message}`, data);
};

logger.api = (message, data = {}) => {
  logger.info(`[API] ${message}`, data);
};

logger.auth = (message, data = {}) => {
  logger.info(`[AUTH] ${message}`, data);
};

logger.db = (message, data = {}) => {
  logger.info(`[DB] ${message}`, data);
};

logger.perf = (message, data = {}) => {
  logger.info(`[PERF] ${message}`, data);
};

module.exports = logger;