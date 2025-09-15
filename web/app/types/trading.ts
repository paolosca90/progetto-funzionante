export interface TradingSignal {
  id: string;
  symbol: string;
  instrumentName: string;
  type: 'BUY' | 'SELL';
  status: 'active' | 'expired' | 'executed' | 'cancelled';
  confidence: number;
  currentPrice: number;
  entryPrice: number;
  stopLoss: number;
  takeProfit: number;
  volume: number;
  risk: number;
  reward: number;
  riskRewardRatio: number;
  motivations: string[];
  timestamp: string;
  expiresAt: string;
  executedAt?: string;
  pnl?: number;
  isRealTime?: boolean;
}

export interface PriceData {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface MarketStats {
  totalSignals: number;
  activeSignals: number;
  successRate: number;
  totalPnL: number;
  dailyPnL: number;
  weeklyPnL: number;
  monthlyPnL: number;
  winRate: number;
  averageRisk: number;
  averageReward: number;
  totalVolume: number;
  bestPerformer: string;
  worstPerformer: string;
}

export interface TouchGesture {
  type: 'tap' | 'long-press' | 'swipe' | 'pinch';
  data: any;
}

export interface ChartTimeframe {
  label: string;
  value: string;
  interval: number;
}

export interface FormFieldProps {
  name: string;
  label: string;
  placeholder?: string;
  type?: 'text' | 'number' | 'email' | 'password' | 'select';
  options?: Array<{ label: string; value: string | number }>;
  validation?: {
    required?: boolean;
    min?: number;
    max?: number;
    pattern?: RegExp;
  };
}

export interface WebSocketMessage {
  type: 'signal_update' | 'price_update' | 'stats_update' | 'connection_status';
  data: any;
  timestamp: number;
}

export interface PerformanceMetrics {
  renderTime: number;
  dataFetchTime: number;
  chartRenderTime: number;
  memoryUsage: number;
  fps: number;
}