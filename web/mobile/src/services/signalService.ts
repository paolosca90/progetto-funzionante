import axios from 'axios';

// API base URL - configure based on environment
const API_BASE_URL = __DEV__
  ? 'http://localhost:3000/api'
  : 'https://api.ai-cash-revolution.com/api';

// Create axios instance for signals API
const signalApiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60 seconds for signal generation
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
signalApiClient.interceptors.request.use(
  async (config) => {
    try {
      // Try AsyncStorage for React Native, fallback to localStorage
      const AsyncStorage = require('@react-native-async-storage/async-storage').default;
      const token = await AsyncStorage.getItem('userToken');

      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch (error) {
      // Fallback to localStorage for web builds
      const token = localStorage.getItem('userToken');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Signal service functions
export const signalService = {
  // Generate a new trading signal
  async generateSignal(instrumentId: string, riskPercentage: number = 1.0) {
    return signalApiClient.post('/signals/generate', {
      instrumentId,
      riskPercentage,
    });
  },

  // Execute a trading signal via MT5
  async executeSignal(signalId: string, riskAmount: number) {
    return signalApiClient.post(`/signals/${signalId}/execute`, {
      riskAmount,
    });
  },

  // Get user's active signals
  async getActiveSignals(page: number = 1, limit: number = 20) {
    return signalApiClient.get('/signals/active', {
      params: { page, limit },
    });
  },

  // Get user's recent signals (history)
  async getRecentSignals(limit: number = 20, status?: string) {
    return signalApiClient.get('/signals/history', {
      params: { limit, status },
    });
  },

  // Get specific signal details
  async getSignalDetails(signalId: string) {
    return signalApiClient.get(`/signals/${signalId}`);
  },

  // Get signal performance statistics
  async getSignalStats(timeframe: string = '30d') {
    return signalApiClient.get('/signals/stats', {
      params: { timeframe },
    });
  },

  // Cancel an active signal (if still active)
  async cancelSignal(signalId: string) {
    return signalApiClient.post(`/signals/${signalId}/cancel`);
  },

  // Get real-time prices for instruments
  async getRealTimePrices(instrumentIds: string[]) {
    return signalApiClient.post('/instruments/prices', {
      instrumentIds,
    });
  },

  // Get instrument quotes
  async getInstrumentQuote(instrumentId: string) {
    return signalApiClient.get(`/instruments/${instrumentId}/quote`);
  },

  // Get signal execution history for a specific signal
  async getSignalExecutionHistory(signalId: string) {
    return signalApiClient.get(`/signals/${signalId}/executions`);
  },
};

// Utility functions for signal management
export const signalUtils = {
  // Format price for display based on instrument type
  formatPrice: (price: number, instrumentType: string): string => {
    if (instrumentType === 'forex') {
      return price.toFixed(price >= 100 ? 2 : 5);
    } else if (instrumentType === 'index') {
      return Math.round(price).toLocaleString();
    } else {
      return price.toFixed(2);
    }
  },

  // Calculate risk/reward ratio
  calculateRiskRewardRatio: (entry: number, stopLoss: number, takeProfit: number, direction: 'long' | 'short'): number => {
    const risk = direction === 'long'
      ? entry - stopLoss
      : stopLoss - entry;

    const reward = direction === 'long'
      ? takeProfit - entry
      : entry - takeProfit;

    return reward / risk;
  },

  // Get signal confidence color
  getConfidenceColor: (confidence: number): string => {
    if (confidence >= 0.8) return '#00ff88'; // High confidence - green
    if (confidence >= 0.6) return '#ffaa00'; // Medium confidence - yellow
    return '#ff4444'; // Low confidence - red
  },

  // Check if signal is still valid (not expired)
  isSignalValid: (expiresAt: string): boolean => {
    return new Date(expiresAt) > new Date();
  },

  // Get time remaining until signal expires
  getTimeUntilExpiry: (expiresAt: string): string => {
    const now = new Date();
    const expiry = new Date(expiresAt);
    const diffMs = expiry.getTime() - now.getTime();

    if (diffMs <= 0) return 'Scaduto';

    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffMinutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));

    if (diffHours > 0) {
      return `${diffHours}h ${diffMinutes}m`;
    }
    return `${diffMinutes}m`;
  },

  // Get signal direction icon
  getDirectionIconName: (direction: 'long' | 'short'): string => {
    return direction === 'long' ? 'trending-up' : 'trending-down';
  },

  // Get signal status text and color
  getSignalStatus: (status: string): { text: string; color: string } => {
    switch (status) {
      case 'active':
        return { text: 'ATTIVO', color: '#00ff88' };
      case 'executed':
        return { text: 'ESEGUITO', color: '#4a90e2' };
      case 'expired':
        return { text: 'SCADUTO', color: '#ffaa00' };
      case 'cancelled':
        return { text: 'CANCELLATO', color: '#ff4444' };
      default:
        return { text: 'SCONOSCIUTO', color: '#666' };
    }
  },

  // Validate risk amount based on user balance and risk settings
  validateRiskAmount: (riskAmount: number, maxDailyLoss?: number, accountBalance?: number): { valid: boolean; message?: string } => {
    if (maxDailyLoss && riskAmount > maxDailyLoss) {
      return {
        valid: false,
        message: `Il rischio supera il limite giornaliero di $${maxDailyLoss}`,
      };
    }

    if (accountBalance && riskAmount > accountBalance * 0.02) { // Max 2% of balance
      return {
        valid: false,
        message: 'Il rischio non può superare il 2% del saldo del conto',
      };
    }

    if (riskAmount < 1) {
      return {
        valid: false,
        message: 'Il rischio minimo è di $1',
      };
    }

    if (riskAmount > 10000) {
      return {
        valid: false,
        message: 'Il rischio massimo è di $10,000',
      };
    }

    return { valid: true };
  },
};

export default signalService;