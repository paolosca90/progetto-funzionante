import axios from 'axios';

// API base URL - configure based on environment
const API_BASE_URL = __DEV__
  ? 'http://localhost:3000/api'
  : 'https://api.ai-cash-revolution.com/api';

// Create axios instance with default configuration
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  async (config) => {
    // Add authorization header if token exists
    const token = await getStoredToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle token refresh
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    if (error.response?.status === 401 && !error.config._retry) {
      // Token expired, try refresh
      try {
        const refreshToken = await getStoredRefreshToken();
        if (refreshToken) {
          const refreshResponse = await apiClient.post('/auth/refresh-token', {
            refreshToken,
          });

          const newToken = refreshResponse.data.token;
          await storeToken(newToken);

          // Retry original request
          error.config.headers.Authorization = `Bearer ${newToken}`;
          error.config._retry = true;
          return apiClient.request(error.config);
        }
      } catch (refreshError) {
        // Refresh failed, logout
        await clearStoredTokens();
      }
    }

    return Promise.reject(error);
  }
);

// Helper functions for token management
const getStoredToken = async (): Promise<string | null> => {
  try {
    const token = localStorage.getItem('userToken');
    return token;
  } catch (error) {
    return null;
  }
};

const getStoredRefreshToken = async (): Promise<string | null> => {
  try {
    const token = localStorage.getItem('refreshToken');
    return token;
  } catch (error) {
    return null;
  }
};

const storeToken = async (token: string): Promise<void> => {
  try {
    localStorage.setItem('userToken', token);
  } catch (error) {
    console.error('Failed to store token:', error);
  }
};

const clearStoredTokens = async (): Promise<void> => {
  try {
    localStorage.removeItem('userToken');
    localStorage.removeItem('userData');
    localStorage.removeItem('refreshToken');
  } catch (error) {
    console.error('Failed to clear tokens:', error);
  }
};

// Auth service functions
export const authService = {
  // User login
  async login(email: string, password: string) {
    return apiClient.post('/auth/login', { email, password });
  },

  // Google OAuth login
  async googleAuth(googleId: string, email: string, firstName?: string, lastName?: string, profilePicture?: string) {
    return apiClient.post('/auth/google', {
      googleId,
      email,
      firstName,
      lastName,
      profilePicture,
    });
  },

  // User registration
  async register(userData: { email: string; password: string; firstName?: string; lastName?: string }) {
    return apiClient.post('/auth/register', userData);
  },

  // User logout
  async logout(token?: string) {
    return apiClient.post('/auth/logout');
  },

  // Forgot password
  async forgotPassword(email: string) {
    return apiClient.post('/auth/forgot-password', { email });
  },

  // Reset password
  async resetPassword(token: string, newPassword: string) {
    return apiClient.post('/auth/reset-password', { token, newPassword });
  },

  // Refresh token
  async refreshToken(refreshToken: string) {
    return apiClient.post('/auth/refresh-token', { refreshToken });
  },

  // Validate current token
  async validateToken(token: string): Promise<boolean> {
    try {
      await apiClient.get('/auth/validate');
      return true;
    } catch (error) {
      return false;
    }
  },

  // Update user profile
  async updateProfile(token: string, userData: any) {
    return apiClient.put('/auth/profile', userData);
  },

  // Get current user data
  async getCurrentUser() {
    return apiClient.get('/auth/me');
  },
};

export default authService;