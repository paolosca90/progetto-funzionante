import React, { createContext, useContext, useReducer, ReactNode, useEffect } from 'react';
import { signalService } from '../services/signalService';
import { useAuth } from './AuthContext';

// Signal interface
interface TradingSignal {
  id: string;
  signalId: string;
  instrument: {
    id: string;
    symbol: string;
    name: string;
    type: string;
    category: string;
  };
  direction: 'long' | 'short';
  confidence: number;
  entryPrice: number;
  stopLoss: number;
  takeProfit: number;
  riskRewardRatio: number;
  motivations: string[];
  analysisResults: any;
  status: 'active' | 'expired' | 'executed' | 'cancelled';
  generatedAt: string;
  expiresAt: string;
  createdAt: string;
}

// Signal state interface
interface SignalState {
  activeSignals: TradingSignal[];
  recentSignals: TradingSignal[];
  selectedInstrument: string;
  isGeneratingSignal: boolean;
  isExecutingSignal: boolean;
  lastSignalTime: number | null;
  error: string | null;
}

// Signal actions
type SignalAction =
  | { type: 'SET_ACTIVE_SIGNALS'; payload: TradingSignal[] }
  | { type: 'SET_RECENT_SIGNALS'; payload: TradingSignal[] }
  | { type: 'ADD_SIGNAL'; payload: TradingSignal }
  | { type: 'UPDATE_SIGNAL'; payload: { signalId: string; updates: Partial<TradingSignal> } }
  | { type: 'REMOVE_SIGNAL'; payload: string }
  | { type: 'SET_GENERATING'; payload: boolean }
  | { type: 'SET_EXECUTING'; payload: boolean }
  | { type: 'SELECT_INSTRUMENT'; payload: string }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_LAST_SIGNAL_TIME'; payload: number };

interface SignalContextType {
  state: SignalState;
  generateSignal: (instrumentId: string, riskPercentage?: number) => Promise<TradingSignal>;
  executeSignal: (signalId: string, riskAmount: number) => Promise<void>;
  fetchActiveSignals: () => Promise<void>;
  fetchRecentSignals: (limit?: number) => Promise<void>;
  selectInstrument: (instrumentId: string) => void;
  clearError: () => void;
}

const SignalContext = createContext<SignalContextType | undefined>(undefined);

// Initial state
const initialState: SignalState = {
  activeSignals: [],
  recentSignals: [],
  selectedInstrument: 'EURUSD', // Default to EURUSD
  isGeneratingSignal: false,
  isExecutingSignal: false,
  lastSignalTime: null,
  error: null,
};

// Signal reducer
function signalReducer(state: SignalState, action: SignalAction): SignalState {
  switch (action.type) {
    case 'SET_ACTIVE_SIGNALS':
      return { ...state, activeSignals: action.payload };

    case 'SET_RECENT_SIGNALS':
      return { ...state, recentSignals: action.payload };

    case 'ADD_SIGNAL':
      return {
        ...state,
        activeSignals: state.activeSignals.some(s => s.id === action.payload.id)
          ? state.activeSignals.map(s => s.id === action.payload.id ? action.payload : s)
          : [action.payload, ...state.activeSignals],
        recentSignals: [action.payload, ...state.recentSignals.slice(0, 19)], // Keep last 20
      };

    case 'UPDATE_SIGNAL':
      return {
        ...state,
        activeSignals: state.activeSignals.map(signal =>
          signal.id === action.payload.signalId ? { ...signal, ...action.payload.updates } : signal
        ),
        recentSignals: state.recentSignals.map(signal =>
          signal.id === action.payload.signalId ? { ...signal, ...action.payload.updates } : signal
        ),
      };

    case 'REMOVE_SIGNAL':
      return {
        ...state,
        activeSignals: state.activeSignals.filter(signal => signal.id !== action.payload),
      };

    case 'SET_GENERATING':
      return { ...state, isGeneratingSignal: action.payload };

    case 'SET_EXECUTING':
      return { ...state, isExecutingSignal: action.payload };

    case 'SELECT_INSTRUMENT':
      return { ...state, selectedInstrument: action.payload };

    case 'SET_ERROR':
      return { ...state, error: action.payload };

    case 'SET_LAST_SIGNAL_TIME':
      return { ...state, lastSignalTime: action.payload };

    default:
      return state;
  }
}

interface SignalProviderProps {
  children: ReactNode;
}

export const SignalProvider: React.FC<SignalProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(signalReducer, initialState);
  const { state: authState } = useAuth();

  // Fetch signals on auth change
  useEffect(() => {
    if (authState.isAuthenticated && authState.user) {
      fetchActiveSignals();
      fetchRecentSignals();
    } else {
      // Clear signals on logout
      dispatch({ type: 'SET_ACTIVE_SIGNALS', payload: [] });
      dispatch({ type: 'SET_RECENT_SIGNALS', payload: [] });
    }
  }, [authState.isAuthenticated]);

  // Generate signal function
  const generateSignal = async (instrumentId: string, riskPercentage: number = 1.0): Promise<TradingSignal> => {
    try {
      dispatch({ type: 'SET_GENERATING', payload: true });
      dispatch({ type: 'SET_ERROR', payload: null });

      // Check if we recently generated a signal (rate limiting)
      if (state.lastSignalTime && Date.now() - state.lastSignalTime < 30000) { // 30 seconds
        throw new Error('Attendi almeno 30 secondi tra una generazione e l\'altra');
      }

      const response = await signalService.generateSignal(instrumentId, riskPercentage);
      const newSignal = response.data.signal;

      // Add to state
      dispatch({ type: 'ADD_SIGNAL', payload: newSignal });
      dispatch({ type: 'SET_LAST_SIGNAL_TIME', payload: Date.now() });

      return newSignal;

    } catch (error: any) {
      const errorMessage = error.response?.data?.error || error.message || 'Errore nella generazione del segnale';
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
      throw new Error(errorMessage);
    } finally {
      dispatch({ type: 'SET_GENERATING', payload: false });
    }
  };

  // Execute signal function
  const executeSignal = async (signalId: string, riskAmount: number): Promise<void> => {
    try {
      dispatch({ type: 'SET_EXECUTING', payload: true });
      dispatch({ type: 'SET_ERROR', payload: null });

      await signalService.executeSignal(signalId, riskAmount);

      // Update signal status
      dispatch({
        type: 'UPDATE_SIGNAL',
        payload: {
          signalId,
          updates: { status: 'executed' as const },
        },
      });

    } catch (error: any) {
      const errorMessage = error.response?.data?.error || error.message || 'Errore nell\'esecuzione del segnale';
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
      throw new Error(errorMessage);
    } finally {
      dispatch({ type: 'SET_EXECUTING', payload: false });
    }
  };

  // Fetch active signals
  const fetchActiveSignals = async (): Promise<void> => {
    try {
      const response = await signalService.getActiveSignals();
      dispatch({ type: 'SET_ACTIVE_SIGNALS', payload: response.data.signals });

    } catch (error: any) {
      console.error('Failed to fetch active signals:', error);
      dispatch({ type: 'SET_ERROR', payload: 'Errore nel caricamento dei segnali attivi' });
    }
  };

  // Fetch recent signals
  const fetchRecentSignals = async (limit: number = 20): Promise<void> => {
    try {
      const response = await signalService.getRecentSignals(limit);
      dispatch({ type: 'SET_RECENT_SIGNALS', payload: response.data.signals });

    } catch (error: any) {
      console.error('Failed to fetch recent signals:', error);
      dispatch({ type: 'SET_ERROR', payload: 'Errore nel caricamento dei segnali recenti' });
    }
  };

  // Select instrument
  const selectInstrument = (instrumentId: string): void => {
    dispatch({ type: 'SELECT_INSTRUMENT', payload: instrumentId });
  };

  // Clear error
  const clearError = (): void => {
    dispatch({ type: 'SET_ERROR', payload: null });
  };

  const value: SignalContextType = {
    state,
    generateSignal,
    executeSignal,
    fetchActiveSignals,
    fetchRecentSignals,
    selectInstrument,
    clearError,
  };

  return (
    <SignalContext.Provider value={value}>
      {children}
    </SignalContext.Provider>
  );
};

export const useSignals = (): SignalContextType => {
  const context = useContext(SignalContext);
  if (context === undefined) {
    throw new Error('useSignals must be used within a SignalProvider');
  }
  return context;
};