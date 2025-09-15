import axios from 'axios';

// API base URL - configure based on environment
const API_BASE_URL = __DEV__
  ? 'http://localhost:3000/api'
  : 'https://api.ai-cash-revolution.com/api';

// Create axios instance for instruments API
const instrumentApiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000, // 10 seconds
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
instrumentApiClient.interceptors.request.use(
  async (config) => {
    try {
      // Try AsyncStorage for React Native, fallback to localStorage for web
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

// Instrument service functions
export const instrumentService = {
  // Get list of available trading instruments
  async getInstruments(page: number = 1, limit: number = 50, type?: string, category?: string) {
    return instrumentApiClient.get('/instruments', {
      params: { page, limit, type, category },
    });
  },

  // Get instrument categories and types
  async getCategories() {
    return instrumentApiClient.get('/instruments/categories');
  },

  // Get detailed information about a specific instrument
  async getInstrumentDetails(instrumentId: string) {
    return instrumentApiClient.get(`/instruments/${instrumentId}`);
  },

  // Get real-time quotes for an instrument
  async getQuotes(instrumentId: string) {
    return instrumentApiClient.get(`/instruments/${instrumentId}/quote`);
  },

  // Get multiple quotes at once
  async getMultipleQuotes(instrumentIds: string[]) {
    return instrumentApiClient.post('/instruments/quotes', {
      instrumentIds,
    });
  },
};

// Instrument utility functions
export const instrumentUtils = {
  // Get instrument display symbol (with type indicator)
  formatInstrumentSymbol: (symbol: string, type: string): string => {
    const typeIndicators: { [key: string]: string } = {
      forex: '💱',
      commodity: '🏗️',
      index: '📈',
    };
    return `${typeIndicators[type] || '📊'} ${symbol}`;
  },

  // Get category display name
  formatCategoryName: (category: string): string => {
    const categoryNames: { [key: string]: string } = {
      major: 'MAGGIORE',
      minor: 'MINORE',
      exotic: 'ESOTICO',
      energy: 'ENERGIA',
      metals: 'METALLI',
      indices: 'INDICI',
    };
    return categoryNames[category] || category.toUpperCase();
  },

  // Check if instrument is supported for signals
  isSupportedForSignals: (type: string, category: string): boolean => {
    // All CME-backed instruments are supported
    const cmeInstruments = ['major', 'minor', 'energy', 'metals', 'indices'];
    return ['forex', 'commodity', 'index'].includes(type) && cmeInstruments.includes(category);
  },

  // Get instrument volatility level (estimated)
  getVolatilityLevel: (symbol: string): 'low' | 'medium' | 'high' => {
    // High volatility instruments
    const highVolatility = ['BTC', 'ETH', 'OIL', 'GAS', 'NASDAQ', 'SPX'];

    // Low volatility instruments
    const lowVolatility = ['CHF', 'JPY'];

    // Medium volatility is default
    if (highVolatility.some(inst => symbol.includes(inst))) {
      return 'high';
    }
    if (lowVolatility.some(inst => symbol.includes(inst))) {
      return 'low';
    }

    return 'medium';
  },

  // Get recommended timeframes for instrument
  getRecommendedTimeframes: (symbol: string): string[] => {
    const volatility = instrumentUtils.getVolatilityLevel(symbol);

    switch (volatility) {
      case 'high':
        return ['M5', 'M15', 'H1'];
      case 'low':
        return ['H1', 'H4', 'D1'];
      case 'medium':
      default:
        return ['M15', 'H1', 'H4'];
    }
  },

  // Group instruments by type
  groupInstrumentsByType: (instruments: any[]): { [key: string]: any[] } => {
    return instruments.reduce((groups, instrument) => {
      if (!groups[instrument.type]) {
        groups[instrument.type] = [];
      }
      groups[instrument.type].push(instrument);
      return groups;
    }, {});
  },

  // Sort instruments by popularity/relevance
  sortInstrumentsByRelevance: (instruments: any[]): any[] => {
    // Order: Major forex first, then commodities, then indices
    const typeOrder = { forex: 1, commodity: 2, index: 3 };
    const categoryOrder = { major: 1, minor: 2, exotic: 3, metals: 1, energy: 1, indices: 1 };

    return instruments.sort((a, b) => {
      // First by type
      const typeComparison = typeOrder[a.type] - typeOrder[b.type];
      if (typeComparison !== 0) return typeComparison;

      // Then by category popularity
      const categoryComparison = categoryOrder[a.category] - categoryOrder[b.category];
      if (categoryComparison !== 0) return categoryComparison;

      // Then alphabetically
      return a.symbol.localeCompare(b.symbol);
    });
  },
};

export default instrumentService;