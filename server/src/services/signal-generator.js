/**
 * Trading Signal Generation Service
 * Orchestrates multi-module analysis to generate trading signals
 */

const winston = require('winston');
const { getPrismaClient } = require('../config/database');
const { TradingSignal } = require('../models');

// Import individual analysis modules
const priceActionModule = require('../workflows/price-action');
const volumeProfileModule = require('../workflows/volume-profile');
const zeroDTEModule = require('../workflows/zero-dte');
const fundamentalModule = require('../workflows/fundamental');

const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  defaultMeta: { service: 'signal-generator' },
  transports: [
    new winston.transports.Console(),
  ],
});

/**
 * Generate a comprehensive trading signal
 */
async function generateTradingSignal(userId, instrumentId, riskPercentage = 1.0) {
  const startTime = Date.now();
  const signalId = `SIG-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

  logger.info(`Starting signal generation: ${signalId}`, {
    userId,
    instrumentId,
    riskPercentage,
  });

  try {
    const prisma = getPrismaClient();

    // 1. Validate and get instrument data
    const instrument = await prisma.tradingInstrument.findUnique({
      where: { id: instrumentId, isActive: true },
    });

    if (!instrument) {
      throw new Error('Instrument not found or inactive');
    }

    logger.info(`Generating signal for instrument: ${instrument.symbol}`);

    // 2. Run parallel analysis modules
    logger.info('Running analysis modules...');

    const analysisPromises = [
      runPriceActionAnalysis(instrument),
      runVolumeAnalysis(instrument),
      runZeroDTEAnalysis(instrument),
      runFundamentalAnalysis(instrument),
    ];

    const analysisResults = await Promise.allSettled(analysisPromises);
    const analysisData = {};

    // Process analysis results
    analysisResults.forEach((result, index) => {
      const moduleNames = ['priceAction', 'volumeProfile', 'zeroDTE', 'fundamental'];

      if (result.status === 'fulfilled') {
        analysisData[moduleNames[index]] = result.value;
        logger.debug(`${moduleNames[index]} analysis completed successfully`);
      } else {
        logger.warn(`${moduleNames[index]} analysis failed:`, result.reason);
        analysisData[moduleNames[index]] = {
          error: result.reason.message,
          timestamp: new Date(),
        };
      }
    });

    // 3. Synthesize cross-analysis signal
    const signal = await synthesizeSignal(analysisData, instrument, userId, riskPercentage);
    logger.info(`Signal synthesized: ${signal.direction} with confidence ${signal.confidence}`);

    // 4. Calculate SL/TP levels
    const riskLevels = calculateRiskLevels(signal.direction, signal.entryPrice, riskPercentage, instrument);
    signal.stopLoss = riskLevels.stopLoss;
    signal.takeProfit = riskLevels.takeProfit;
    signal.riskRewardRatio = riskLevels.riskRewardRatio;

    // 5. Generate motivations using Gemini
    const motivations = await generateMotivations(signal, analysisData);
    signal.motivations = motivations;

    // 6. Create database record
    const createdSignal = await prisma.$transaction(async (tx) => {
      const newSignal = await tx.tradingSignal.create({
        data: {
          userId,
          instrumentId,
          signalId: signal.signalId,
          direction: signal.direction,
          confidence: signal.confidence,
          entryPrice: signal.entryPrice,
          stopLoss: signal.stopLoss,
          takeProfit: signal.takeProfit,
          riskRewardRatio: signal.riskRewardRatio,
          timeFrame: 'intraday',
          analysisResults: analysisData,
          motivations: signal.motivations,
          generatedAt: new Date(),
          expiresAt: new Date(Date.now() + 4 * 60 * 60 * 1000), // 4 hours expiry
        },
        include: {
          instrument: {
            select: {
              symbol: true,
              name: true,
              type: true,
              category: true,
            },
          },
        },
      });

      // Create audit log
      await tx.auditLog.create({
        data: {
          userId,
          action: 'signal_generated',
          resource: 'trading_signal',
          resourceId: newSignal.id,
          newValues: {
            direction: signal.direction,
            confidence: signal.confidence,
            instrument: instrument.symbol,
          },
        },
      });

      return newSignal;
    });

    const generationTime = Date.now() - startTime;
    logger.info(`Signal generation completed in ${generationTime}ms:`, {
      signalId: createdSignal.signalId,
      direction: createdSignal.direction,
      confidence: createdSignal.confidence,
    });

    return {
      ...createdSignal,
      motivations: createdSignal.motivations,
      analysisResults: createdSignal.analysisResults,
    };

  } catch (error) {
    logger.error(`Signal generation failed for ${signalId}:`, error);
    throw new Error(`Signal generation failed: ${error.message}`);
  }
}

/**
 * Run price action analysis
 */
async function runPriceActionAnalysis(instrument) {
  try {
    return await priceActionModule.analyze({
      symbol: instrument.symbol,
      type: instrument.type,
      category: instrument.category,
    });
  } catch (error) {
    logger.error('Price action analysis failed:', error);
    throw new Error(`Price action analysis: ${error.message}`);
  }
}

/**
 * Run volume profile analysis
 */
async function runVolumeAnalysis(instrument) {
  try {
    return await volumeProfileModule.analyze({
      symbol: instrument.symbol,
      type: instrument.type,
      isFuturesBacked: instrument.metadata?.futuresBacked || false,
    });
  } catch (error) {
    logger.error('Volume analysis failed:', error);
    throw new Error(`Volume analysis: ${error.message}`);
  }
}

/**
 * Run zero DTE analysis (for indices only)
 */
async function runZeroDTEAnalysis(instrument) {
  try {
    // Only run for specific indices
    if (instrument.type === 'index' && ['NASDAQ', 'SPX'].includes(instrument.symbol)) {
      return await zeroDTEModule.analyze({
        symbol: instrument.symbol,
        category: instrument.category,
      });
    } else {
      return { applicable: false, reason: 'Not an index or not supported for 0DTE analysis' };
    }
  } catch (error) {
    logger.error('Zero DTE analysis failed:', error);
    throw new Error(`Zero DTE analysis: ${error.message}`);
  }
}

/**
 * Run fundamental/news analysis
 */
async function runFundamentalAnalysis(instrument) {
  try {
    return await fundamentalModule.analyze({
      symbol: instrument.symbol,
      type: instrument.type,
      category: instrument.category,
    });
  } catch (error) {
    logger.error('Fundamental analysis failed:', error);
    throw new Error(`Fundamental analysis: ${error.message}`);
  }
}

/**
 * Synthesize signal from analysis results
 */
async function synthesizeSignal(analysisData, instrument, userId, riskPercentage) {
  try {
    // Analysis weightings
    const weights = {
      priceAction: getWeight('priceAction', instrument),
      volumeProfile: getWeight('volumeProfile', instrument),
      zeroDTE: getWeight('zeroDTE', instrument),
      fundamental: getWeight('fundamental', instrument),
    };

    // Calculate directional scores
    let bullishScore = 0;
    let bearishScore = 0;
    let totalWeight = 0;

    // Price Action contribution
    if (analysisData.priceAction && !analysisData.priceAction.error) {
      const weight = weights.priceAction;
      totalWeight += weight;

      if (analysisData.priceAction.direction === 'bullish') {
        bullishScore += analysisData.priceAction.strength * weight;
      } else if (analysisData.priceAction.direction === 'bearish') {
        bearishScore += analysisData.priceAction.strength * weight;
      }
    }

    // Volume Profile contribution
    if (analysisData.volumeProfile && !analysisData.volumeProfile.error) {
      const weight = weights.volumeProfile;
      totalWeight += weight;

      if (analysisData.volumeProfile.supportStrong) {
        bullishScore += 0.8 * weight;
      }
      if (analysisData.volumeProfile.resistanceStrong) {
        bearishScore += 0.8 * weight;
      }
    }

    // Zero DTE contribution
    if (analysisData.zeroDTE && analysisData.zeroDTE.applicable && !analysisData.zeroDTE.error) {
      const weight = weights.zeroDTE;
      totalWeight += weight;

      bullishScore += analysisData.zeroDTE.bullishBias * weight;
      bearishScore += analysisData.zeroDTE.bearishBias * weight;
    }

    // Fundamental contribution
    if (analysisData.fundamental && !analysisData.fundamental.error) {
      const weight = weights.fundamental;
      totalWeight += weight;

      bullishScore += analysisData.fundamental.sentimentScore * weight;
    }

    // Determine direction and confidence
    const netScore = bullishScore - bearishScore;
    const confidence = Math.min(Math.abs(netScore / Math.max(totalWeight, 1)), 1.0);

    let direction = 'hold';
    if (netScore > 0.3 && confidence >= 0.6) {
      direction = 'long';
    } else if (netScore < -0.3 && confidence >= 0.6) {
      direction = 'short';
    }

    if (direction === 'hold') {
      throw new Error('Insufficient analysis confidence for signal generation');
    }

    // Get current price (placeholder - would integrate with Oanda API)
    const currentPrice = await getCurrentPrice(instrument.symbol);

    return {
      signalId: `SIG-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      direction,
      confidence: Math.round(confidence * 100) / 100,
      entryPrice: currentPrice,
      analysisData,
    };

  } catch (error) {
    logger.error('Signal synthesis failed:', error);
    throw error;
  }
}

/**
 * Calculate risk levels (SL/TP)
 */
function calculateRiskLevels(direction, entryPrice, riskPercentage, instrument) {
  // Base SL calculations on instrument type and volatility
  const volatilityMultiplier = instrument.type === 'forex' ? 0.005 : 0.01;
  const pipValue = instrument.pipValue || 0.0001;

  // Calculate stop loss distance
  const slDistance = entryPrice * volatilityMultiplier * (riskPercentage / 2);
  const slPips = slDistance / pipValue;

  // Target 2:1 risk-reward ratio minimum
  const tpDistance = slDistance * 2;

  let stopLoss, takeProfit;

  if (direction === 'long') {
    stopLoss = entryPrice - slDistance;
    takeProfit = entryPrice + tpDistance;
  } else { // short
    stopLoss = entryPrice + slDistance;
    takeProfit = entryPrice - tpDistance;
  }

  // Calculate risk-reward ratio
  const risk = Math.abs(entryPrice - stopLoss);
  const reward = Math.abs(takeProfit - entryPrice);
  const riskRewardRatio = reward / risk;

  return {
    stopLoss,
    takeProfit,
    riskRewardRatio: Math.round(riskRewardRatio * 100) / 100,
  };
}

/**
 * Generate motivations using Gemini AI
 */
async function generateMotivations(signal, analysisData) {
  try {
    // TODO: Integrate with Google Gemini API
    // For now, generate placeholder motivations

    const motivations = [];

    if (analysisData.priceAction && !analysisData.priceAction.error) {
      motivations.push(`Price action shows strong ${signal.direction} momentum with key support level at ${analysisData.priceAction.keyLevel}`);
    }

    if (analysisData.volumeProfile && !analysisData.volumeProfile.error) {
      motivations.push(`Volume profile indicates ${signal.direction === 'long' ? 'accumulation' : 'distribution'} pattern with POC at ${analysisData.volumeProfile.poc}`);
    }

    if (analysisData.zeroDTE && analysisData.zeroDTE.applicable && !analysisData.zeroDTE.error) {
      motivations.push(`0DTE options flow confirms institutional ${signal.direction} positioning`);
    }

    if (analysisData.fundamental && !analysisData.fundamental.error) {
      motivations.push(`Recent macroeconomic data supports ${analysisData.fundamental.sentimentScore > 0.5 ? 'bullish' : 'bearish'} market environment`);
    }

    return motivations.length > 0
      ? motivations
      : [`Auto-generated signal based on multi-timeframe analysis with ${Math.round(signal.confidence * 100)}% confidence`];

  } catch (error) {
    logger.error('Motivation generation failed:', error);
    return [`Technical analysis suggests ${signal.direction} opportunity with ${Math.round(signal.confidence * 100)}% confidence`];
  }
}

/**
 * Get analysis weight for instrument
 */
function getWeight(moduleName, instrument) {
  const baseWeights = {
    forex: { priceAction: 0.4, volumeProfile: 0.3, zeroDTE: 0.0, fundamental: 0.3 },
    commodity: { priceAction: 0.3, volumeProfile: 0.4, zeroDTE: 0.0, fundamental: 0.3 },
    index: { priceAction: 0.3, volumeProfile: 0.3, zeroDTE: 0.2, fundamental: 0.2 },
  };

  return baseWeights[instrument.type]?.[moduleName] || 0.25;
}

/**
 * Get current price from trading API
 */
async function getCurrentPrice(symbol) {
  // TODO: Integrate with Oanda API for real prices
  // Placeholder prices for demo
  const basePrices = {
    'EURUSD': 1.0850,
    'GBPUSD': 1.2750,
    'USDJPY': 150.50,
    'USDCHF': 0.8950,
    'USDCAD': 1.3250,
    'AUDUSD': 0.6750,
    'XAUUSD': 1825.50,
    'NASDAQ': 15850.25,
    'SPX': 4380.75,
  };

  return basePrices[symbol] || 1.0000;
}

module.exports = {
  generateTradingSignal,
};