/**
 * Test environment setup
 * Configures the test environment before running tests
 */

// Load environment variables for testing
require('dotenv').config({ path: '.env.test' });

// Set test environment
process.env.NODE_ENV = 'test';
process.env.JWT_SECRET = 'test_jwt_secret_for_testing_only';
process.env.DATABASE_URL = 'postgresql://test:test@localhost:5432/aicash_test';

// Mock external dependencies during testing
jest.mock('redis');
jest.mock('ws');

// Global test utilities
global.testUtils = {
  // Create mock user for testing
  mockUser: {
    id: 'user123',
    email: 'test@example.com',
    firstName: 'Test',
    lastName: 'User',
    role: 'user',
  },

  // Create mock signal for testing
  mockSignal: {
    id: 'signal123',
    signalId: 'SIG-TEST-123',
    direction: 'long',
    confidence: 0.85,
    entryPrice: 1.0850,
    stopLoss: 1.0820,
    takeProfit: 1.0920,
    riskRewardRatio: 2.05,
  },

  // Generate random instrument
  generateMockInstrument: () => ({
    id: `inst${Date.now()}`,
    symbol: 'EURUSD',
    name: 'Euro vs US Dollar',
    type: 'forex',
    category: 'major',
    pipValue: 0.0001,
    contractSize: 100000,
  }),

  // Clean up after each test
  async cleanup() {
    // Database cleanup would go here
    jest.clearAllMocks();
  },
};

// Test helpers
global.helpers = {
  // Wait for async operations
  delay: (ms) => new Promise(resolve => setTimeout(resolve, ms)),

  // Generate JWT token for testing
  generateTestToken: (userId = 'test-user-id') => {
    const jwt = require('jsonwebtoken');
    return jwt.sign(
      { userId },
      process.env.JWT_SECRET,
      { expiresIn: '1h' }
    );
  },

  // Setup authenticated request for tests
  setupAuthRequest: (user = global.testUtils.mockUser) => {
    return {
      headers: {
        authorization: `Bearer ${global.helpers.generateTestToken(user.id)}`,
      },
      user: user,
    };
  },
};

// Setup global before/after hooks
beforeAll(async () => {
  // Global test setup
  console.log('Setting up test environment...');
});

afterAll(async () => {
  // Global test cleanup
  console.log('Cleaning up test environment...');
});

afterEach(async () => {
  // Cleanup after each test
  await global.testUtils.cleanup();
});