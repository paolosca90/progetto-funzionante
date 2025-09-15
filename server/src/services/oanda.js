/**
 * OANDA API Integration for Real-Time Market Data
 * Provides forex prices, account management, and demo trading
 */

const axios = require('axios');
const logger = require('../utils/logger');

class OandaService {
  constructor() {
    this.apiUrl = process.env.OANDA_API_URL || 'https://api-fxpractice.oanda.com';
    this.streamUrl = process.env.OANDA_STREAM_URL || 'https://stream-fxpractice.oanda.com';
    this.apiKey = process.env.OANDA_API_KEY;
    this.accountId = process.env.OANDA_ACCOUNT_ID;

    if (!this.apiKey) {
      logger.warn('[OANDA] API key not configured - using demo data');
    }

    this.client = axios.create({
      timeout: 5000,
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json',
      },
    });

    // Rate limiting variables
    this.lastRequest = 0;
    this.requestInterval = 500; // 500ms between requests (120/min)
  }

  /**
   * Rate limiting helper
   */
  async rateLimit() {
    const now = Date.now();
    const timeSinceLastRequest = now - this.lastRequest;

    if (timeSinceLastRequest < this.requestInterval) {
      const waitTime = this.requestInterval - timeSinceLastRequest;
      await new Promise(resolve => setTimeout(resolve, waitTime));
    }

    this.lastRequest = Date.now();
  }

  /**
   * Get real-time price for a trading instrument
   */
  async getCurrentPrice(instrument) {
    if (!this.apiKey) {
      return this.getMockPrice(instrument);
    }

    try {
      await this.rateLimit();

      const response = await this.client.get(`/v3/accounts/${this.accountId}/pricing`, {
        params: {
          instruments: instrument,
          includeHomeConversions: false,
          includeUnitsAvailable: false
        }
      });

      const pricing = response.data.prices[0];

      if (!pricing) {
        throw new Error(`No pricing data for ${instrument}`);
      }

      const price = {
        instrument: pricing.instrument,
        bid: parseFloat(pricing.bids[0].price),
        ask: parseFloat(pricing.asks[0].price),
        spread: parseFloat(pricing.asks[0].price) - parseFloat(pricing.bids[0].price),
        timestamp: new Date(pricing.time),
        tradeable: pricing.tradeable
      };

      logger.api(`Price fetched for ${instrument}`, { price: price.ask, bid: price.bid });
      return price;

    } catch (error) {
      logger.error(`[OANDA] Failed to fetch price for ${instrument}:`, error.message);
      return this.getMockPrice(instrument);
    }
  }

  /**
   * Get historical candle data
   */
  async getHistoricalData(instrument, granularity = 'M5', count = 100) {
    if (!this.apiKey) {
      return this.getMockHistoricalData(instrument, count);
    }

    try {
      await this.rateLimit();

      const response = await this.client.get(`/v3/instruments/${instrument}/candles`, {
        params: {
          granularity,
          count,
          price: 'MBA' // Mid, Bid, Ask prices
        }
      });

      const candles = response.data.candles.map(candle => ({
        timestamp: new Date(candle.time),
        open: parseFloat(candle.mid.o),
        high: parseFloat(candle.mid.h),
        low: parseFloat(candle.mid.l),
        close: parseFloat(candle.mid.c),
        volume: candle.volume
      }));

      logger.api(`Historical data fetched for ${instrument}`, {
        granularity,
        candleCount: candles.length
      });

      return candles;

    } catch (error) {
      logger.error(`[OANDA] Failed to fetch historical data for ${instrument}:`, error.message);
      return this.getMockHistoricalData(instrument, count);
    }
  }

  /**
   * Get account information
   */
  async getAccountInfo() {
    if (!this.apiKey) {
      return this.getMockAccountInfo();
    }

    try {
      await this.rateLimit();

      const response = await this.client.get(`/v3/accounts/${this.accountId}`);
      const account = response.data.account;

      return {
        id: account.id,
        currency: account.currency,
        balance: parseFloat(account.balance),
        unrealizedPL: parseFloat(account.unrealizedPL),
        realizedPL: parseFloat(account.pl),
        marginUsed: parseFloat(account.marginUsed),
        marginAvailable: parseFloat(account.marginAvailable),
        openTradeCount: account.openTradeCount,
        openPositionCount: account.openPositionCount
      };

    } catch (error) {
      logger.error('[OANDA] Failed to fetch account info:', error.message);
      return this.getMockAccountInfo();
    }
  }

  /**
   * Place a demo order (for testing signal execution)
   */
  async placeDemoOrder(orderRequest) {
    if (!this.apiKey) {
      return this.getMockOrderResponse(orderRequest);
    }

    try {
      await this.rateLimit();

      const response = await this.client.post(
        `/v3/accounts/${this.accountId}/orders`,
        { order: orderRequest }
      );

      logger.trade('Demo order placed', {
        instrument: orderRequest.instrument,
        units: orderRequest.units,
        type: orderRequest.type
      });

      return {
        orderId: response.data.orderCreateTransaction.id,
        status: 'filled',
        fillPrice: response.data.orderFillTransaction?.price,
        fillTime: response.data.orderFillTransaction?.time,
        tradeId: response.data.orderFillTransaction?.tradeOpened?.tradeID
      };

    } catch (error) {
      logger.error('[OANDA] Failed to place demo order:', error.message);
      return this.getMockOrderResponse(orderRequest);
    }
  }

  /**
   * Get tradeable instruments
   */
  async getInstruments() {
    if (!this.apiKey) {
      return this.getMockInstruments();
    }

    try {
      await this.rateLimit();

      const response = await this.client.get(`/v3/accounts/${this.accountId}/instruments`);

      return response.data.instruments.map(instrument => ({
        name: instrument.name,
        displayName: instrument.displayName,
        type: instrument.type,
        pipLocation: instrument.pipLocation,
        marginRate: parseFloat(instrument.marginRate),
        minimumTradeSize: parseFloat(instrument.minimumTradeSize),
        maximumOrderUnits: parseFloat(instrument.maximumOrderUnits)
      }));

    } catch (error) {
      logger.error('[OANDA] Failed to fetch instruments:', error.message);
      return this.getMockInstruments();
    }
  }

  // Mock data methods for development/fallback
  getMockPrice(instrument) {
    const baseRates = {
      'EUR_USD': 1.0950,
      'GBP_USD': 1.2750,
      'USD_JPY': 149.50,
      'AUD_USD': 0.6650,
      'USD_CAD': 1.3580,
      'USD_CHF': 0.8920,
      'NZD_USD': 0.6180,
      'EUR_GBP': 0.8590
    };

    const basePrice = baseRates[instrument] || 1.0000;
    const variation = (Math.random() - 0.5) * 0.01; // ±0.5% variation
    const spread = basePrice * 0.0002; // 2 pips spread

    const ask = basePrice + variation + spread/2;
    const bid = ask - spread;

    return {
      instrument,
      bid: parseFloat(bid.toFixed(5)),
      ask: parseFloat(ask.toFixed(5)),
      spread: parseFloat(spread.toFixed(5)),
      timestamp: new Date(),
      tradeable: true
    };
  }

  getMockHistoricalData(instrument, count) {
    const candles = [];
    const basePrice = this.getMockPrice(instrument).ask;
    let currentPrice = basePrice;

    for (let i = count; i > 0; i--) {
      const variation = (Math.random() - 0.5) * 0.02; // ±1% variation
      const open = currentPrice;
      const close = open * (1 + variation);
      const high = Math.max(open, close) * (1 + Math.random() * 0.005);
      const low = Math.min(open, close) * (1 - Math.random() * 0.005);

      candles.push({
        timestamp: new Date(Date.now() - i * 5 * 60 * 1000), // 5 min intervals
        open: parseFloat(open.toFixed(5)),
        high: parseFloat(high.toFixed(5)),
        low: parseFloat(low.toFixed(5)),
        close: parseFloat(close.toFixed(5)),
        volume: Math.floor(Math.random() * 1000) + 100
      });

      currentPrice = close;
    }

    return candles.reverse();
  }

  getMockAccountInfo() {
    return {
      id: 'DEMO-123456789',
      currency: 'USD',
      balance: 100000.00,
      unrealizedPL: 0.00,
      realizedPL: 0.00,
      marginUsed: 0.00,
      marginAvailable: 100000.00,
      openTradeCount: 0,
      openPositionCount: 0
    };
  }

  getMockOrderResponse(orderRequest) {
    return {
      orderId: `ORDER-${Date.now()}`,
      status: 'filled',
      fillPrice: this.getMockPrice(orderRequest.instrument).ask,
      fillTime: new Date().toISOString(),
      tradeId: `TRADE-${Date.now()}`
    };
  }

  getMockInstruments() {
    return [
      { name: 'EUR_USD', displayName: 'EUR/USD', type: 'CURRENCY', pipLocation: -4, marginRate: 0.02, minimumTradeSize: 1, maximumOrderUnits: 100000000 },
      { name: 'GBP_USD', displayName: 'GBP/USD', type: 'CURRENCY', pipLocation: -4, marginRate: 0.02, minimumTradeSize: 1, maximumOrderUnits: 100000000 },
      { name: 'USD_JPY', displayName: 'USD/JPY', type: 'CURRENCY', pipLocation: -2, marginRate: 0.02, minimumTradeSize: 1, maximumOrderUnits: 100000000 },
      { name: 'AUD_USD', displayName: 'AUD/USD', type: 'CURRENCY', pipLocation: -4, marginRate: 0.03, minimumTradeSize: 1, maximumOrderUnits: 100000000 },
      { name: 'USD_CAD', displayName: 'USD/CAD', type: 'CURRENCY', pipLocation: -4, marginRate: 0.02, minimumTradeSize: 1, maximumOrderUnits: 100000000 }
    ];
  }
}

module.exports = new OandaService();