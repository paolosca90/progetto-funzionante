import React, { createContext, useContext, useReducer, ReactNode, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { authService } from '../services/authService';

// User interface
interface User {
  id: string;
  email: string;
  firstName?: string;
  lastName?: string;
  profilePicture?: string;
  subscriptionStatus: string;
  isActive: boolean;
}

// Auth state interface
interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

// Auth actions
type AuthAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'LOGIN_SUCCESS'; payload: { user: User; token: string } }
  | { type: 'LOGOUT' }
  | { type: 'UPDATE_USER'; payload: Partial<User> }
  | { type: 'TOKEN_REFRESH'; payload: string };

interface AuthContextType {
  state: AuthState;
  login: (email: string, password: string) => Promise<void>;
  googleLogin: (googleId: string, email: string, firstName?: string, lastName?: string, profilePicture?: string) => Promise<void>;
  register: (userData: { email: string; password: string; firstName?: string; lastName?: string }) => Promise<void>;
  logout: () => Promise<void>;
  forgotPassword: (email: string) => Promise<void>;
  resetPassword: (token: string, newPassword: string) => Promise<void>;
  refreshToken: () => Promise<boolean>;
  updateProfile: (userData: Partial<User>) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Initial state
const initialState: AuthState = {
  user: null,
  token: null,
  isLoading: true,
  isAuthenticated: false,
};

// Auth reducer
function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };

    case 'LOGIN_SUCCESS':
      return {
        ...state,
        user: action.payload.user,
        token: action.payload.token,
        isLoading: false,
        isAuthenticated: true,
      };

    case 'LOGOUT':
      return {
        ...state,
        user: null,
        token: null,
        isLoading: false,
        isAuthenticated: false,
      };

    case 'UPDATE_USER':
      return {
        ...state,
        user: state.user ? { ...state.user, ...action.payload } : null,
      };

    case 'TOKEN_REFRESH':
      return {
        ...state,
        token: action.payload,
      };

    default:
      return state;
  }
}

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // Initialize auth on app start
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const token = await AsyncStorage.getItem('userToken');
        const userString = await AsyncStorage.getItem('userData');

        if (token && userString) {
          const user = JSON.parse(userString);

          // Validate token with server
          const isValid = await authService.validateToken(token);

          if (isValid) {
            dispatch({
              type: 'LOGIN_SUCCESS',
              payload: { user, token },
            });
          } else {
            // Token invalid, clear storage
            await AsyncStorage.multiRemove(['userToken', 'userData']);
            dispatch({ type: 'SET_LOADING', payload: false });
          }
        } else {
          dispatch({ type: 'SET_LOADING', payload: false });
        }
      } catch (error) {
        console.error('Auth initialization error:', error);
        dispatch({ type: 'SET_LOADING', payload: false });
      }
    };

    initializeAuth();
  }, []);

  // Login function
  const login = async (email: string, password: string): Promise<void> => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });

      const response = await authService.login(email, password);
      const { user, token } = response.data;

      // Store in AsyncStorage
      await AsyncStorage.setItem('userToken', token);
      await AsyncStorage.setItem('userData', JSON.stringify(user));

      dispatch({
        type: 'LOGIN_SUCCESS',
        payload: { user, token },
      });

    } catch (error: any) {
      dispatch({ type: 'SET_LOADING', payload: false });
      throw new Error(error.response?.data?.error || 'Login failed');
    }
  };

  // Google login function
  const googleLogin = async (
    googleId: string,
    email: string,
    firstName?: string,
    lastName?: string,
    profilePicture?: string
  ): Promise<void> => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });

      const response = await authService.googleAuth(googleId, email, firstName, lastName, profilePicture);
      const { user, token } = response.data;

      // Store in AsyncStorage
      await AsyncStorage.setItem('userToken', token);
      await AsyncStorage.setItem('userData', JSON.stringify(user));

      dispatch({
        type: 'LOGIN_SUCCESS',
        payload: { user, token },
      });

    } catch (error: any) {
      dispatch({ type: 'SET_LOADING', payload: false });
      throw new Error(error.response?.data?.error || 'Google login failed');
    }
  };

  // Register function
  const register = async (userData: { email: string; password: string; firstName?: string; lastName?: string }): Promise<void> => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });

      const response = await authService.register(userData);
      const { user, token } = response.data;

      // Store in AsyncStorage
      await AsyncStorage.setItem('userToken', token);
      await AsyncStorage.setItem('userData', JSON.stringify(user));

      dispatch({
        type: 'LOGIN_SUCCESS',
        payload: { user, token },
      });

    } catch (error: any) {
      dispatch({ type: 'SET_LOADING', payload: false });
      throw new Error(error.response?.data?.error || 'Registration failed');
    }
  };

  // Logout function
  const logout = async (): Promise<void> => {
    try {
      // Clear AsyncStorage
      await AsyncStorage.multiRemove(['userToken', 'userData', 'refreshToken']);

      // Call logout API (optional, for server-side cleanup)
      if (state.token) {
        try {
          await authService.logout(state.token);
        } catch (error) {
          console.log('Server logout failed, but local logout successful');
        }
      }

      dispatch({ type: 'LOGOUT' });

    } catch (error) {
      console.error('Logout error:', error);
      // Even if logout fails, clear local state
      dispatch({ type: 'LOGOUT' });
    }
  };

  // Forgot password function
  const forgotPassword = async (email: string): Promise<void> => {
    try {
      await authService.forgotPassword(email);
    } catch (error: any) {
      throw new Error(error.response?.data?.error || 'Password reset request failed');
    }
  };

  // Reset password function
  const resetPassword = async (token: string, newPassword: string): Promise<void> => {
    try {
      await authService.resetPassword(token, newPassword);
    } catch (error: any) {
      throw new Error(error.response?.data?.error || 'Password reset failed');
    }
  };

  // Refresh token function
  const refreshToken = async (): Promise<boolean> => {
    try {
      const refreshToken = await AsyncStorage.getItem('refreshToken');

      if (!refreshToken) {
        return false;
      }

      const response = await authService.refreshToken(refreshToken);
      const newToken = response.data.token;

      // Store new token
      await AsyncStorage.setItem('userToken', newToken);

      dispatch({ type: 'TOKEN_REFRESH', payload: newToken });

      return true;

    } catch (error) {
      console.error('Token refresh failed:', error);
      // Token refresh failed, logout user
      await logout();
      return false;
    }
  };

  // Update profile function
  const updateProfile = async (userData: Partial<User>): Promise<void> => {
    try {
      if (!state.user || !state.token) {
        throw new Error('User not authenticated');
      }

      await authService.updateProfile(state.token, userData);

      // Update local user state
      dispatch({ type: 'UPDATE_USER', payload: userData });

      // Update AsyncStorage
      const updatedUser = { ...state.user, ...userData };
      await AsyncStorage.setItem('userData', JSON.stringify(updatedUser));

    } catch (error: any) {
      throw new Error(error.response?.data?.error || 'Profile update failed');
    }
  };

  const value: AuthContextType = {
    state,
    login,
    googleLogin,
    register,
    logout,
    forgotPassword,
    resetPassword,
    refreshToken,
    updateProfile,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};