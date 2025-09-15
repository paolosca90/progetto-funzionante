import React, { createContext, useContext, useState, ReactNode } from 'react';
import { Appearance } from 'react-native';

// Matrix theme inspired color palette
export const themeColors = {
  // Primary Matrix colors
  matrix: {
    background: '#0a0a0a',     // Deep black
    surface: '#141414',        // Slightly lighter black for cards
    primary: '#00ff88',        // Bright matrix green
    secondary: '#00cc66',      // Darker green
    accent: '#ffffff',         // White for contrast
    text: '#ffffff',           // Primary text color
    textSecondary: '#cccccc',  // Secondary text
    error: '#ff4444',          // Red for errors
    success: '#00ff88',        // Green for success
    warning: '#ffaa00',        // Orange for warnings
    info: '#4a90e2',           // Blue for info
    disabled: '#666666',       // Gray for disabled elements
    border: '#333333',         // Subtle borders
    shadow: '#00ff88',         // Matrix green shadows
  },
};

// Theme configuration
interface Theme {
  colors: typeof themeColors.matrix;
  fonts: {
    regular: string;
    medium: string;
    monospace: string;
  };
  spacing: {
    xs: number;
    sm: number;
    md: number;
    lg: number;
    xl: number;
    xxl: number;
  };
  borderRadius: {
    sm: number;
    md: number;
    lg: number;
    xl: number;
  };
}

// Define the theme
const theme: Theme = {
  colors: themeColors.matrix,
  fonts: {
    regular: 'System',
    medium: 'System',
    monospace: 'Courier New',
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
    xxl: 48,
  },
  borderRadius: {
    sm: 4,
    md: 8,
    lg: 12,
    xl: 16,
  },
};

interface ThemeContextType {
  theme: Theme;
  isDarkMode: boolean;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

interface ThemeProviderProps {
  children: ReactNode;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  // Matrix theme is always dark - no toggle needed
  const [isDarkMode] = useState(true);

  const toggleTheme = () => {
    // Matrix theme doesn't support light mode - it's always dark
    console.log('⚠️  Matrix theme cannot be toggled to light mode');
  };

  const value = {
    theme,
    isDarkMode,
    toggleTheme,
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

// Export theme object for direct access
export { theme };
export default ThemeProvider;