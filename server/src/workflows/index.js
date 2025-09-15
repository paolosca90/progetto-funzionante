/**
 * Trading Analysis Workflows Index
 * Orchestrates and initializes all analysis modules
 */

const winston = require('winston');
const priceActionModule = require('./price-action');
const volumeProfileModule = require('./volume-profile');
const zeroDTEModule = require('./zero-dte');
const fundamentalModule = require('./fundamental');
const { SystemHealth } = require('../models');

const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  defaultMeta: { service: 'workflows-index' },
  transports: [
    new winston.transports.Console(),
  ],
});

/**
 * Analysis modules registry
 */
const ANALYSIS_MODULES = {
  priceAction: {
    module: priceActionModule,
    name: 'Price Action Analysis',
    description: 'Advanced technical price action patterns and momentum',
    enabled: true,
    healthCheck: 'price-action-health',
  },
  volumeProfile: {
    module: volumeProfileModule,
    name: 'Volume Profile Analysis',
    description: 'Multi-day volume analysis with POC and imbalance detection',
    enabled: true,
    healthCheck: 'volume-profile-health',
  },
  zeroDTE: {
    module: zeroDTEModule,
    name: 'Zero DTE Analysis',
    description: 'Specialized 0DTE analysis for NDX and SPX futures',
    enabled: true,
    healthCheck: 'zero-dte-health',
  },
  fundamental: {
    module: fundamentalModule,
    name: 'Fundamental News Analysis',
    description: 'Economic news sentiment and macroeconomic impact analysis',
    enabled: true,
    healthCheck: 'fundamental-health',
  },
};

/**
 * Initialize all trading analysis workflows
 */
async function initializeWorkflows() {
  try {
    logger.info('Initializing trading analysis workflows...');

    // Initialize each module
    for (const [key, config] of Object.entries(ANALYSIS_MODULES)) {
      if (config.enabled) {
        logger.info(`Initializing ${config.name}...`);

        try {
          // Perform basic health check
          await checkModuleHealth(key);

          logger.info(`${config.name} initialized successfully`);
        } catch (error) {
          logger.error(`Failed to initialize ${config.name}:`, error);

          // Mark module as unhealthy but continue
          await updateModuleHealth(key, 'error', { error: error.message });
        }
      }
    }

    // Start continuous ML optimization if enabled
    if (process.env.ENABLE_CONTINUOUS_ML === 'true') {
      logger.info('Starting continuous ML optimization...');
      startContinuousMLOptimization();
    }

    // Set up periodic health monitoring
    setInterval(async () => {
      await performWorkflowsHealthCheck();
    }, 300000); // Check every 5 minutes

    logger.info('All trading workflows initialized successfully');

    return {
      modules: Object.keys(ANALYSIS_MODULES),
      status: 'initialized',
      timestamp: new Date().toISOString(),
    };

  } catch (error) {
    logger.error('Failed to initialize trading workflows:', error);

    // Attempt to initialize in degraded mode
    return {
      modules: [],
      status: 'degraded',
      error: error.message,
      timestamp: new Date().toISOString(),
    };
  }
}

/**
 * Run a specific analysis module
 */
async function runAnalysisModule(moduleKey, instrument) {
  try {
    const moduleConfig = ANALYSIS_MODULES[moduleKey];

    if (!moduleConfig || !moduleConfig.enabled) {
      throw new Error(`Analysis module ${moduleKey} not available`);
    }

    logger.debug(`Running ${moduleConfig.name} for ${instrument.symbol}`);

    const result = await moduleConfig.module.analyze(instrument);

    // Update module health
    await updateModuleHealth(moduleKey, 'healthy', {
      lastRun: new Date().toISOString(),
      responseTime: Date.now(),
    });

    return result;

  } catch (error) {
    logger.error(`Analysis module ${moduleKey} failed:`, error);

    // Update module health
    await updateModuleHealth(moduleKey, 'unhealthy', {
      error: error.message,
      lastError: new Date().toISOString(),
    });

    throw error;
  }
}

/**
 * Perform parallel analysis across all enabled modules
 */
async function runParallelAnalysis(instrument) {
  try {
    logger.info(`Starting parallel analysis for ${instrument.symbol}`);

    const analysisPromises = Object.entries(ANALYSIS_MODULES)
      .filter(([_, config]) => config.enabled)
      .map(async ([key, config]) => {
        try {
          const result = await runAnalysisModule(key, instrument);
          return { key, result, success: true };
        } catch (error) {
          logger.warn(`${config.name} failed:`, error.message);
          return { key, error: error.message, success: false };
        }
      });

    const analysisResults = await Promise.allSettled(analysisPromises);

    // Organize results
    const results = {};

    analysisResults.forEach(promiseResult => {
      if (promiseResult.status === 'fulfilled') {
        const { key, result, success } = promiseResult.value;
        results[key] = success ? result : { error: result.error };
      }
    });

    logger.info(`Parallel analysis completed for ${instrument.symbol}`);

    return results;

  } catch (error) {
    logger.error('Parallel analysis failed:', error);
    throw error;
  }
}

/**
 * Get analysis module metadata
 */
function getModuleMetadata(moduleKey) {
  const config = ANALYSIS_MODULES[moduleKey];

  if (!config) {
    return null;
  }

  return {
    key: moduleKey,
    name: config.name,
    description: config.description,
    enabled: config.enabled,
    healthCheck: config.healthCheck,
  };
}

/**
 * Get all available analysis modules
 */
function getAvailableModules() {
  return Object.entries(ANALYSIS_MODULES).map(([key, config]) => ({
    key,
    ...getModuleMetadata(key),
  }));
}

/**
 * Check if a specific module is available
 */
function isModuleAvailable(moduleKey) {
  const config = ANALYSIS_MODULES[moduleKey];
  return config && config.enabled;
}

/**
 * Perform health check for all workflows
 */
async function performWorkflowsHealthCheck() {
  try {
    const healthResults = {};

    for (const [key, config] of Object.entries(ANALYSIS_MODULES)) {
      healthResults[key] = await checkModuleHealth(key);
    }

    // Check if any modules are failing
    const failingModules = Object.entries(healthResults)
      .filter(([_, health]) => health.status !== 'healthy')
      .map(([key, _]) => key);

    if (failingModules.length > 0) {
      logger.warn(`Workflow health issues detected: ${failingModules.join(', ')}`);
    }

    return {
      services: healthResults,
      overallStatus: failingModules.length === 0 ? 'healthy' : 'degraded',
      timestamp: new Date().toISOString(),
    };

  } catch (error) {
    logger.error('Workflows health check failed:', error);
    return {
      services: {},
      overallStatus: 'error',
      error: error.message,
      timestamp: new Date().toISOString(),
    };
  }
}

/**
 * Start continuous ML optimization
 */
async function startContinuousMLOptimization() {
  try {
    const intervalMinutes = parseInt(process.env.ML_OPTIMIZATION_INTERVAL) || 5;

    logger.info(`Starting continuous ML optimization every ${intervalMinutes} minutes`);

    const optimizationJob = async () => {
      try {
        // Import ML service if it exists
        // const mlService = require('../services/ml-optimization');

        // TODO: Implement ML optimization logic
        logger.debug('Running ML optimization cycle');

        // Placeholder for ML optimization
        // await mlService.runOptimizationCycle();

      } catch (error) {
        logger.error('ML optimization cycle failed:', error);
      }
    };

    // Run initial cycle
    await optimizationJob();

    // Set up interval
    setInterval(optimizationJob, intervalMinutes * 60 * 1000);

  } catch (error) {
    logger.error('Failed to start continuous ML optimization:', error);
  }
}

/**
 * Check module health
 */
async function checkModuleHealth(moduleKey) {
  try {
    const config = ANALYSIS_MODULES[moduleKey];

    if (!config) {
      return { status: 'error', error: 'Module not found' };
    }

    // Basic health check - module exists and is enabled
    const isEnabled = config.enabled;
    const moduleExists = typeof config.module.analyze === 'function';

    if (isEnabled && moduleExists) {
      return { status: 'healthy', checkedAt: new Date().toISOString() };
    } else {
      return {
        status: 'unhealthy',
        error: isEnabled ? 'Module function not available' : 'Module disabled',
        checkedAt: new Date().toISOString(),
      };
    }

  } catch (error) {
    return {
      status: 'error',
      error: error.message,
      checkedAt: new Date().toISOString(),
    };
  }
}

/**
 * Update module health status
 */
async function updateModuleHealth(moduleKey, status, metadata = {}) {
  try {
    const serviceName = `workflow-${moduleKey}`;

    await SystemHealth.updateServiceHealth(serviceName, status, {
      module: moduleKey,
      ...metadata,
    });

  } catch (error) {
    logger.error(`Failed to update health for ${moduleKey}:`, error);
  }
}

module.exports = {
  initializeWorkflows,
  runAnalysisModule,
  runParallelAnalysis,
  getModuleMetadata,
  getAvailableModules,
  isModuleAvailable,
  performWorkflowsHealthCheck,
};