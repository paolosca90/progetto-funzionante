/**
 * Fundamental & News Sentiment Analysis Module
 * Analyzes macroeconomic news and market sentiment from recent data
 */

const winston = require('winston');
const { getPrismaClient } = require('../config/database');

const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  defaultMeta: { service: 'fundamental-workflow' },
  transports: [
    new winston.transports.Console(),
  ],
});

/**
 * Analyze fundamental news and sentiment for trading decisions
 */
async function analyze(instrument) {
  try {
    logger.info(`Starting fundamental analysis for ${instrument.symbol}`);

    const prisma = getPrismaClient();

    // Get recent sentiment data (last 24 hours)
    const recentSentiment = await prisma.newsSentimentData.findMany({
      where: {
        publishedAt: {
          gte: new Date(Date.now() - 24 * 60 * 60 * 1000), // Last 24 hours
        },
        relevance: {
          gte: 0.3, // Minimum relevance threshold
        },
        instruments: {
          has: instrument.symbol,
        },
      },
      orderBy: {
        publishedAt: 'desc',
      },
      take: 50,
    });

    // TODO: Replace with actual news API integration (Bloomberg, Reuters, etc.)
    // This is placeholder fundamental analysis

    await simulateProcessingDelay(700); // Simulate API call

    const analysis = await generateFundamentalAnalysis(instrument, recentSentiment);

    logger.info(`Fundamental analysis completed for ${instrument.symbol}: sentiment ${analysis.sentimentScore > 0 ? 'positive' : 'negative'} (${Math.round(analysis.sentimentScore * 1000) / 1000})`);

    return {
      symbol: instrument.symbol,
      sentimentScore: analysis.sentimentScore, // -1 to +1 scale
      confidence: analysis.confidence,
      keyEvents: analysis.keyEvents,
      categoryImpact: analysis.categoryImpact,
      volatilityImpact: analysis.volatilityImpact,
      regionalFocus: analysis.regionalFocus,
      currencyPairs: analysis.currencyPairs,
      commodities: analysis.commodities,
      timestamp: new Date().toISOString(),
    };

  } catch (error) {
    logger.error(`Fundamental analysis failed for ${instrument.symbol}:`, error);
    throw error;
  }
}

/**
 * Generate fundamental analysis from news data
 */
async function generateFundamentalAnalysis(instrument, sentimentData = []) {
  // Use existing sentiment data or generate synthetic analysis
  if (sentimentData.length > 0) {
    return aggregateSentimentData(sentimentData);
  } else {
    return generateSyntheticFundamentalAnalysis(instrument);
  }
}

/**
 * Aggregate sentiment from existing news data
 */
function aggregateSentimentData(sentimentData) {
  try {
    // Calculate weighted sentiment score
    const totalWeight = sentimentData.reduce((sum, item) => sum + item.relevance, 0);
    const weightedSentiment = sentimentData.reduce(
      (sum, item) => sum + (item.sentiment * item.relevance),
      0
    );

    const sentimentScore = totalWeight > 0 ? weightedSentiment / totalWeight : 0;

    // Calculate confidence based on data quality and quantity
    const dataQuality = Math.min(sentimentData.length / 20, 1); // More data = higher confidence
    const averageRelevance = sentimentData.reduce((sum, item) => sum + item.relevance, 0) / sentimentData.length;
    const confidence = (dataQuality + averageRelevance) / 2;

    // Extract key events
    const keyEvents = sentimentData
      .filter(item => item.impactScore > 0.7)
      .slice(0, 5)
      .map(item => ({
        headline: item.headline.substring(0, 100),
        impact: item.impactScore,
        sentiment: item.sentiment,
        published: item.publishedAt,
      }));

    // Determine category impacts
    const categoryImpacts = sentimentData.reduce((acc, item) => {
      item.categories.forEach(category => {
        if (!acc[category]) acc[category] = { positive: 0, negative: 0, neutral: 0 };
        if (item.sentiment > 0.2) acc[category].positive++;
        else if (item.sentiment < -0.2) acc[category].negative++;
        else acc[category].neutral++;
      });
      return acc;
    }, {});

    // Calculate volatility impact
    const highImpactEvents = sentimentData.filter(item => Math.abs(item.sentiment) > 0.5);
    const volatilityImpact = highImpactEvents.length > 0
      ? highImpactEvents.reduce((sum, item) => sum + Math.abs(item.sentiment), 0) / highImpactEvents.length
      : 0.1;

    return {
      sentimentScore,
      confidence,
      keyEvents,
      categoryImpact: categoryImpacts,
      volatilityImpact,
      regionalFocus: generateRegionalFocus(sentimentData),
      currencyPairs: generateCurrencyImpact(sentimentData),
      commodities: generateCommodityImpact(sentimentData),
    };

  } catch (error) {
    logger.error('Sentiment data aggregation failed:', error);
    return generateSyntheticFundamentalAnalysis(sentimentData[0]?.instruments?.[0] || 'UNKNOWN');
  }
}

/**
 * Generate synthetic fundamental analysis for demo
 */
function generateSyntheticFundamentalAnalysis(instrument) {
  // Generate realistic sentiment based on instrument type
  const baseSentiment = generateBaseSentiment(instrument.type);

  const sentimentVariation = (Math.random() - 0.5) * 0.6; // ±0.3 variation
  const sentimentScore = Math.max(-1.0, Math.min(1.0, baseSentiment + sentimentVariation));

  const confidence = 0.4 + Math.random() * 0.4; // 0.4-0.8 confidence range

  // Generate key events
  const keyEvents = generateKeyEvents(sentimentScore);

  // Category impacts
  const categoryImpact = generateCategoryImpacts(sentimentScore);

  // Volatility impact (higher with extreme sentiment)
  const volatilityImpact = Math.abs(sentimentScore) * 0.5 + Math.random() * 0.2;

  return {
    sentimentScore,
    confidence,
    keyEvents,
    categoryImpact,
    volatilityImpact,
    regionalFocus: generateRegionalFocus([]),
    currencyPairs: generateCurrencyImpact([]),
    commodities: generateCommodityImpact([]),
  };
}

/**
 * Generate base sentiment by instrument type
 */
function generateBaseSentiment(type) {
  const sentimentMap = {
    forex: 0.0, // Forex typically neutral
    commodity: 0.1, // Slight bullish for commodities
    index: 0.05, // Slight upward bias for indices
  };

  return sentimentMap[type] || 0.0;
}

/**
 * Generate key market events
 */
function generateKeyEvents(sentimentScore) {
  const eventTemplates = {
    positive: [
      'Fed Signals Potential Rate Pause in Coming Months',
      'Economic Data Beats Expectations Across Major Economies',
      'Corporate Earnings Surge Past Analyst Forecasts',
      'Trade Tensions Ease with New Agreement Framework',
      'Employment Data Shows Strong Labor Market Recovery',
    ],
    negative: [
      'Central Bank Announces Surprise Rate Hike',
      'Economic Contraction Deepens in Major Markets',
      'Geopolitical Tensions Escalate with New Sanctions',
      'Recession Fears Intensify on Weak Manufacturing Data',
      'Inflation Spike Raises Concerns Over Interest Rates',
    ],
    neutral: [
      'Economic Indicators Show Mixed Performance',
      'Policy Makers Maintain Current Monetary Stance',
      'Economic Data Aligns with Market Expectations',
      'No Major Catalysts in Current Economic Landscape',
      'Market Conditions Remain Stable Despite Uncertainty',
    ],
  };

  const sentiment = sentimentScore > 0.2 ? 'positive' :
                   sentimentScore < -0.2 ? 'negative' : 'neutral';

  const events = eventTemplates[sentiment];
  const numEvents = Math.floor(Math.random() * 3) + 1; // 1-3 events

  return events
    .sort(() => Math.random() - 0.5)
    .slice(0, numEvents)
    .map(event => ({
      headline: event,
      impact: 0.6 + Math.random() * 0.4, // 0.6-1.0 impact
      sentiment: sentimentScore,
      published: new Date(Date.now() - Math.random() * 24 * 60 * 60 * 1000), // Random time in last 24h
    }));
}

/**
 * Generate economic category impacts
 */
function generateCategoryImpacts(sentimentScore) {
  const categories = [
    'economic_growth', 'employment', 'inflation', 'monetary_policy',
    'trade', 'geopolitical', 'corporate_earnings', 'consumer_confidence'
  ];

  return categories.reduce((acc, category) => {
    const impactBias = Math.random() * 0.4 - 0.2; // Small random bias
    const impact = Math.max(0, Math.min(3, sentimentScore + impactBias));
    const count = Math.floor(impact) + (Math.random() > 0.5 ? 1 : 0);

    acc[category] = {
      positive: impact > 0.5 ? count : 0,
      negative: impact < -0.5 ? count : 0,
      neutral: 3 - (acc[category]?.positive || 0) - (acc[category]?.negative || 0),
    };

    return acc;
  }, {});
}

/**
 * Generate regional focus
 */
function generateRegionalFocus(sentimentData) {
  const regions = ['north_america', 'europe', 'asia_pacific', 'emerging_markets'];

  // If we have real data, use it; otherwise distribute randomly
  if (sentimentData.length > 0) {
    return sentimentData.reduce((acc, item) => {
      // Simplified regional attribution
      const region = regions[Math.floor(Math.random() * regions.length)];
      acc[region] = (acc[region] || 0) + 1;
      return acc;
    }, {});
  }

  // Generate synthetic regional focus
  return regions.reduce((acc, region) => {
    acc[region] = Math.floor(Math.random() * 10) + 1; // 1-10 mentions
    return acc;
  }, {});
}

/**
 * Generate currency pair impacts
 */
function generateCurrencyImpact(sentimentData) {
  const currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD'];

  return currencies.reduce((acc, currency) => {
    // Simplified impact generation
    const strength = (Math.random() - 0.5) * 0.4; // ±0.2 range
    acc[currency] = {
      sentiment: strength,
      volatility: Math.abs(strength) * 0.5 + 0.1,
    };
    return acc;
  }, {});
}

/**
 * Generate commodity impacts
 */
function generateCommodityImpact(sentimentData) {
  const commodities = ['gold', 'silver', 'oil', 'copper', 'natural_gas'];

  return commodities.reduce((acc, commodity) => {
    const strength = (Math.random() - 0.5) * 0.6; // ±0.3 range
    acc[commodity] = {
      sentiment: strength,
      safeHaven: commodity === 'gold' && strength > 0.1,
    };
    return acc;
  }, {});
}

/**
 * Store sentiment analysis results
 */
async function storeSentimentAnalysis(newsData) {
  try {
    const prisma = getPrismaClient();

    if (Array.isArray(newsData)) {
      await prisma.newsSentimentData.createMany({
        data: newsData,
        skipDuplicates: true,
      });
    } else {
      await prisma.newsSentimentData.create({
        data: newsData,
      });
    }

  } catch (error) {
    logger.error('Failed to store sentiment analysis:', error);
  }
}

/**
 * Get sentiment impact on specific instruments
 */
async function getSentimentImpact(instruments) {
  try {
    const prisma = getPrismaClient();

    const impacts = await prisma.newsSentimentData.findMany({
      where: {
        publishedAt: {
          gte: new Date(Date.now() - 24 * 60 * 60 * 1000),
        },
        relevance: {
          gte: 0.4,
        },
        OR: instruments.map(symbol => ({
          instruments: { has: symbol },
        })),
      },
      orderBy: {
        impactScore: 'desc',
      },
      take: 20,
    });

    // Aggregate by instrument
    return impacts.reduce((acc, item) => {
      item.instruments.forEach(instrument => {
        if (!acc[instrument]) acc[instrument] = [];
        acc[instrument].push({
          headline: item.headline,
          sentiment: item.sentiment,
          impact: item.impactScore,
          categories: item.categories,
        });
      });
      return acc;
    }, {});

  } catch (error) {
    logger.error('Failed to get sentiment impact:', error);
    return {};
  }
}

/**
 * Simulate processing delay
 */
function simulateProcessingDelay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

module.exports = {
  analyze,
};