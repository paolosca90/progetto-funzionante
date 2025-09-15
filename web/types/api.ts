/**
 * Comprehensive API Type Definitions for AI Cash Revolution Platform
 * Features advanced TypeScript patterns for maximum type safety
 */

// ============================================================================
// Utility Types and Template Literals
// ============================================================================

/** Extract keys that are optional from an object type */
type OptionalKeys<T> = {
  [K in keyof T]-?: {} extends Pick<T, K> ? K : never;
}[keyof T];

/** Extract keys that are required from an object type */
type RequiredKeys<T> = {
  [K in keyof T]-?: {} extends Pick<T, K> ? never : K;
}[keyof T];

/** Make specific keys optional while keeping others required */
type PartialBy<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;

/** Deep readonly type for immutable data structures */
type DeepReadonly<T> = {
  readonly [P in keyof T]: T[P] extends (infer U)[]
    ? DeepReadonlyArray<U>
    : T[P] extends object
    ? DeepReadonly<T[P]>
    : T[P];
};

interface DeepReadonlyArray<T> extends ReadonlyArray<DeepReadonly<T>> {}

/** Template literal type for API endpoints */
type APIEndpoint = `/api/${string}`;

/** HTTP method types */
type HTTPMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';

/** Status codes with semantic meaning */
type SuccessStatusCode = 200 | 201 | 202 | 204;
type ClientErrorStatusCode = 400 | 401 | 403 | 404 | 409 | 422 | 429;
type ServerErrorStatusCode = 500 | 502 | 503 | 504;
type StatusCode = SuccessStatusCode | ClientErrorStatusCode | ServerErrorStatusCode;

// ============================================================================
// Base Response Types
// ============================================================================

/** Standard API response wrapper */
interface APIResponse<TData = unknown> {
  readonly success: boolean;
  readonly data: TData;
  readonly message: string;
  readonly timestamp: string;
  readonly requestId: string;
}

/** Paginated response type */
interface PaginatedResponse<TData = unknown> extends APIResponse<TData[]> {
  readonly pagination: {
    readonly page: number;
    readonly limit: number;
    readonly total: number;
    readonly totalPages: number;
    readonly hasNext: boolean;
    readonly hasPrev: boolean;
  };
}

/** Error response structure */
interface APIError {
  readonly code: string;
  readonly message: string;
  readonly details?: Record<string, unknown>;
  readonly field?: string;
  readonly statusCode: StatusCode;
  readonly timestamp: string;
  readonly requestId: string;
}

/** Validation error structure */
interface ValidationError extends APIError {
  readonly field: string;
  readonly value: unknown;
  readonly constraints: string[];
}

// ============================================================================
// Authentication Types
// ============================================================================

/** User roles with hierarchical permissions */
const USER_ROLES = ['admin', 'trader', 'subscriber', 'demo'] as const;
type UserRole = typeof USER_ROLES[number];

/** Authentication request types */
interface LoginRequest {
  readonly email: string;
  readonly password: string;
  readonly rememberMe?: boolean;
  readonly deviceInfo?: DeviceInfo;
}

interface RegisterRequest {
  readonly email: string;
  readonly password: string;
  readonly firstName: string;
  readonly lastName: string;
  readonly phone?: string;
  readonly referralCode?: string;
  readonly acceptTerms: true;
  readonly acceptPrivacy: true;
}

interface ResetPasswordRequest {
  readonly email: string;
}

interface ChangePasswordRequest {
  readonly currentPassword: string;
  readonly newPassword: string;
  readonly confirmPassword: string;
}

/** Device information for security tracking */
interface DeviceInfo {
  readonly userAgent: string;
  readonly platform: string;
  readonly language: string;
  readonly timezone: string;
  readonly screenResolution?: string;
  readonly isTouch?: boolean;
}

/** JWT token payload structure */
interface TokenPayload {
  readonly sub: string; // user ID
  readonly email: string;
  readonly role: UserRole;
  readonly iat: number;
  readonly exp: number;
  readonly deviceId: string;
}

/** Authentication response */
interface AuthResponse {
  readonly user: User;
  readonly tokens: {
    readonly accessToken: string;
    readonly refreshToken: string;
    readonly expiresIn: number;
  };
  readonly sessionId: string;
}

// ============================================================================
// User Types
// ============================================================================

/** Base user interface */
interface User {
  readonly id: string;
  readonly email: string;
  readonly firstName: string;
  readonly lastName: string;
  readonly phone?: string;
  readonly role: UserRole;
  readonly status: 'active' | 'suspended' | 'pending' | 'inactive';
  readonly emailVerified: boolean;
  readonly phoneVerified: boolean;
  readonly twoFactorEnabled: boolean;
  readonly lastLoginAt?: string;
  readonly createdAt: string;
  readonly updatedAt: string;
  readonly profile: UserProfile;
  readonly subscription: UserSubscription;
  readonly settings: UserSettings;
}

/** Extended user profile */
interface UserProfile {
  readonly avatar?: string;
  readonly bio?: string;
  readonly country?: string;
  readonly timezone: string;
  readonly language: string;
  readonly experience: 'beginner' | 'intermediate' | 'advanced' | 'expert';
  readonly tradingGoals: string[];
  readonly riskTolerance: 'conservative' | 'moderate' | 'aggressive';
  readonly preferredAssets: string[];
}

/** User subscription details */
interface UserSubscription {
  readonly planId: string;
  readonly planName: string;
  readonly status: 'active' | 'cancelled' | 'expired' | 'trial';
  readonly startDate: string;
  readonly endDate?: string;
  readonly autoRenew: boolean;
  readonly features: string[];
  readonly limits: SubscriptionLimits;
}

/** Subscription limits */
interface SubscriptionLimits {
  readonly maxSignals: number;
  readonly maxPortfolios: number;
  readonly maxAlerts: number;
  readonly apiCallsPerHour: number;
  readonly dataRetentionDays: number;
}

/** User preferences and settings */
interface UserSettings {
  readonly notifications: NotificationSettings;
  readonly trading: TradingSettings;
  readonly display: DisplaySettings;
  readonly privacy: PrivacySettings;
}

interface NotificationSettings {
  readonly email: boolean;
  readonly push: boolean;
  readonly sms: boolean;
  readonly signalAlerts: boolean;
  readonly priceAlerts: boolean;
  readonly newsAlerts: boolean;
  readonly accountAlerts: boolean;
}

interface TradingSettings {
  readonly defaultLotSize: number;
  readonly maxRiskPerTrade: number;
  readonly autoExecution: boolean;
  readonly stopLossEnabled: boolean;
  readonly takeProfitEnabled: boolean;
  readonly trailingStopEnabled: boolean;
}

interface DisplaySettings {
  readonly theme: 'light' | 'dark' | 'auto';
  readonly currency: string;
  readonly dateFormat: string;
  readonly timeFormat: '12h' | '24h';
  readonly chartType: 'candlestick' | 'line' | 'area';
  readonly language: string;
}

interface PrivacySettings {
  readonly profileVisibility: 'public' | 'private' | 'friends';
  readonly showTradingStats: boolean;
  readonly allowDataCollection: boolean;
  readonly allowMarketing: boolean;
}

// ============================================================================
// Trading Signal Types
// ============================================================================

/** Trading instrument/symbol */
interface TradingSymbol {
  readonly symbol: string;
  readonly name: string;
  readonly type: 'forex' | 'crypto' | 'stocks' | 'commodities' | 'indices';
  readonly category: string;
  readonly baseCurrency: string;
  readonly quoteCurrency: string;
  readonly precision: number;
  readonly minLotSize: number;
  readonly maxLotSize: number;
  readonly lotStep: number;
  readonly spread: number;
  readonly commission: number;
  readonly swapLong: number;
  readonly swapShort: number;
  readonly marginRequired: number;
  readonly active: boolean;
}

/** AI-generated trading signal */
interface TradingSignal {
  readonly id: string;
  readonly symbol: TradingSymbol;
  readonly type: 'buy' | 'sell';
  readonly confidence: number; // 0-100
  readonly strength: 'weak' | 'moderate' | 'strong' | 'very_strong';
  readonly timeframe: '1m' | '5m' | '15m' | '30m' | '1h' | '4h' | '1d' | '1w';
  readonly entryPrice: number;
  readonly stopLoss?: number;
  readonly takeProfit?: number;
  readonly targets: PriceTarget[];
  readonly risk: number; // Risk percentage
  readonly reward: number; // Reward percentage
  readonly riskRewardRatio: number;
  readonly analysis: SignalAnalysis;
  readonly metadata: SignalMetadata;
  readonly status: SignalStatus;
  readonly createdAt: string;
  readonly expiresAt?: string;
  readonly executedAt?: string;
  readonly closedAt?: string;
}

/** Price targets for scaled entries/exits */
interface PriceTarget {
  readonly level: number;
  readonly probability: number;
  readonly action: 'entry' | 'partial_exit' | 'full_exit';
  readonly percentage: number; // Percentage of position
}

/** Detailed signal analysis */
interface SignalAnalysis {
  readonly technicalScore: number;
  readonly fundamentalScore: number;
  readonly sentimentScore: number;
  readonly indicators: TechnicalIndicator[];
  readonly patterns: ChartPattern[];
  readonly keyLevels: KeyLevel[];
  readonly marketCondition: 'trending' | 'ranging' | 'volatile' | 'consolidating';
  readonly newsImpact: 'none' | 'low' | 'medium' | 'high';
  readonly economicEvents: EconomicEvent[];
}

/** Technical indicator data */
interface TechnicalIndicator {
  readonly name: string;
  readonly value: number;
  readonly signal: 'bullish' | 'bearish' | 'neutral';
  readonly strength: number;
  readonly timeframe: string;
}

/** Chart pattern recognition */
interface ChartPattern {
  readonly name: string;
  readonly type: 'bullish' | 'bearish' | 'neutral';
  readonly confidence: number;
  readonly targetPrice?: number;
  readonly invalidationPrice?: number;
}

/** Key price levels */
interface KeyLevel {
  readonly price: number;
  readonly type: 'support' | 'resistance' | 'pivot';
  readonly strength: number;
  readonly timeframe: string;
  readonly touchCount: number;
}

/** Economic events affecting signals */
interface EconomicEvent {
  readonly name: string;
  readonly country: string;
  readonly currency: string;
  readonly impact: 'low' | 'medium' | 'high';
  readonly actual?: number;
  readonly forecast?: number;
  readonly previous?: number;
  readonly time: string;
}

/** Signal metadata */
interface SignalMetadata {
  readonly modelVersion: string;
  readonly backtestResults: BacktestResults;
  readonly marketSession: 'asian' | 'european' | 'american' | 'overlap';
  readonly volatility: number;
  readonly volume: number;
  readonly spread: number;
  readonly correlations: SymbolCorrelation[];
}

/** Backtest performance data */
interface BacktestResults {
  readonly winRate: number;
  readonly profitFactor: number;
  readonly sharpeRatio: number;
  readonly maxDrawdown: number;
  readonly avgProfit: number;
  readonly avgLoss: number;
  readonly totalTrades: number;
  readonly period: string;
}

/** Symbol correlation data */
interface SymbolCorrelation {
  readonly symbol: string;
  readonly correlation: number;
  readonly timeframe: string;
}

/** Signal execution status */
type SignalStatus =
  | 'pending'
  | 'active'
  | 'executed'
  | 'partial_filled'
  | 'filled'
  | 'cancelled'
  | 'expired'
  | 'stopped_out'
  | 'target_hit'
  | 'closed';

// ============================================================================
// Portfolio and Trading Types
// ============================================================================

/** User's trading portfolio */
interface Portfolio {
  readonly id: string;
  readonly userId: string;
  readonly name: string;
  readonly type: 'live' | 'demo' | 'paper';
  readonly broker: 'mt5' | 'binance' | 'paper' | 'demo';
  readonly accountId: string;
  readonly balance: number;
  readonly equity: number;
  readonly margin: number;
  readonly freeMargin: number;
  readonly marginLevel: number;
  readonly profit: number;
  readonly unrealizedPnL: number;
  readonly realizedPnL: number;
  readonly totalTrades: number;
  readonly winningTrades: number;
  readonly losingTrades: number;
  readonly winRate: number;
  readonly profitFactor: number;
  readonly sharpeRatio: number;
  readonly maxDrawdown: number;
  readonly positions: Position[];
  readonly orders: Order[];
  readonly history: TradeHistory[];
  readonly performance: PerformanceMetrics;
  readonly riskMetrics: RiskMetrics;
  readonly createdAt: string;
  readonly updatedAt: string;
}

/** Trading position */
interface Position {
  readonly id: string;
  readonly portfolioId: string;
  readonly signalId?: string;
  readonly symbol: TradingSymbol;
  readonly type: 'buy' | 'sell';
  readonly lotSize: number;
  readonly entryPrice: number;
  readonly currentPrice: number;
  readonly stopLoss?: number;
  readonly takeProfit?: number;
  readonly unrealizedPnL: number;
  readonly commission: number;
  readonly swap: number;
  readonly margin: number;
  readonly openTime: string;
  readonly comment?: string;
  readonly magic?: number;
}

/** Pending order */
interface Order {
  readonly id: string;
  readonly portfolioId: string;
  readonly signalId?: string;
  readonly symbol: TradingSymbol;
  readonly type: 'buy_limit' | 'sell_limit' | 'buy_stop' | 'sell_stop';
  readonly lotSize: number;
  readonly price: number;
  readonly stopLoss?: number;
  readonly takeProfit?: number;
  readonly expiration?: string;
  readonly status: 'pending' | 'cancelled' | 'executed' | 'expired';
  readonly createdAt: string;
  readonly comment?: string;
}

/** Trade history record */
interface TradeHistory {
  readonly id: string;
  readonly portfolioId: string;
  readonly signalId?: string;
  readonly symbol: TradingSymbol;
  readonly type: 'buy' | 'sell';
  readonly lotSize: number;
  readonly entryPrice: number;
  readonly exitPrice: number;
  readonly stopLoss?: number;
  readonly takeProfit?: number;
  readonly profit: number;
  readonly commission: number;
  readonly swap: number;
  readonly pips: number;
  readonly duration: number; // in minutes
  readonly openTime: string;
  readonly closeTime: string;
  readonly closeReason: 'manual' | 'stop_loss' | 'take_profit' | 'margin_call';
  readonly comment?: string;
}

/** Portfolio performance metrics */
interface PerformanceMetrics {
  readonly totalReturn: number;
  readonly annualizedReturn: number;
  readonly monthlyReturn: number;
  readonly weeklyReturn: number;
  readonly dailyReturn: number;
  readonly volatility: number;
  readonly sharpeRatio: number;
  readonly sortinoRatio: number;
  readonly calmarRatio: number;
  readonly maxDrawdown: number;
  readonly avgDrawdown: number;
  readonly drawdownDuration: number;
  readonly winRate: number;
  readonly profitFactor: number;
  readonly payoffRatio: number;
  readonly expectancy: number;
  readonly averageWin: number;
  readonly averageLoss: number;
  readonly largestWin: number;
  readonly largestLoss: number;
  readonly consecutiveWins: number;
  readonly consecutiveLosses: number;
}

/** Risk management metrics */
interface RiskMetrics {
  readonly varDaily: number; // Value at Risk
  readonly varWeekly: number;
  readonly varMonthly: number;
  readonly expectedShortfall: number;
  readonly betaToMarket: number;
  readonly correlation: number;
  readonly concentrationRisk: number;
  readonly leverageRatio: number;
  readonly marginUtilization: number;
  readonly riskPerTrade: number;
  readonly maxRiskPerTrade: number;
  readonly portfolioHeatValue: number;
}

// ============================================================================
// WebSocket Event Types
// ============================================================================

/** WebSocket message base interface */
interface WebSocketMessage<TData = unknown> {
  readonly type: string;
  readonly data: TData;
  readonly timestamp: string;
  readonly id: string;
}

/** Real-time price update */
interface PriceUpdate {
  readonly symbol: string;
  readonly bid: number;
  readonly ask: number;
  readonly last: number;
  readonly change: number;
  readonly changePercent: number;
  readonly volume: number;
  readonly high: number;
  readonly low: number;
  readonly timestamp: string;
}

/** Signal notification */
interface SignalNotification {
  readonly signal: TradingSignal;
  readonly action: 'new' | 'updated' | 'cancelled' | 'executed';
  readonly priority: 'low' | 'medium' | 'high' | 'critical';
}

/** Portfolio update */
interface PortfolioUpdate {
  readonly portfolioId: string;
  readonly balance: number;
  readonly equity: number;
  readonly margin: number;
  readonly freeMargin: number;
  readonly unrealizedPnL: number;
  readonly positions: Position[];
  readonly orders: Order[];
}

/** Trade execution update */
interface TradeExecution {
  readonly orderId: string;
  readonly positionId?: string;
  readonly status: 'pending' | 'executed' | 'rejected' | 'cancelled';
  readonly executionPrice?: number;
  readonly executionTime?: string;
  readonly error?: string;
}

/** Market news */
interface MarketNews {
  readonly id: string;
  readonly title: string;
  readonly content: string;
  readonly source: string;
  readonly category: string;
  readonly impact: 'low' | 'medium' | 'high';
  readonly currencies: string[];
  readonly publishedAt: string;
  readonly url?: string;
}

/** WebSocket event type mapping */
interface WebSocketEvents {
  'price_update': PriceUpdate;
  'signal_notification': SignalNotification;
  'portfolio_update': PortfolioUpdate;
  'trade_execution': TradeExecution;
  'market_news': MarketNews;
  'user_notification': UserNotification;
  'system_status': SystemStatus;
  'error': APIError;
}

/** User notification */
interface UserNotification {
  readonly id: string;
  readonly type: 'info' | 'warning' | 'error' | 'success';
  readonly title: string;
  readonly message: string;
  readonly actionRequired: boolean;
  readonly actionUrl?: string;
  readonly expiresAt?: string;
}

/** System status */
interface SystemStatus {
  readonly status: 'online' | 'maintenance' | 'degraded' | 'offline';
  readonly services: ServiceStatus[];
  readonly message?: string;
  readonly estimatedResolution?: string;
}

interface ServiceStatus {
  readonly name: string;
  readonly status: 'operational' | 'degraded' | 'down' | 'maintenance';
  readonly responseTime?: number;
  readonly uptime?: number;
}

// ============================================================================
// Request/Response Type Mappings
// ============================================================================

/** Map HTTP methods to allowed request body types */
type RequestBodyForMethod<TMethod extends HTTPMethod> =
  TMethod extends 'GET' | 'DELETE'
    ? never
    : Record<string, unknown>;

/** API endpoint configuration */
interface APIEndpointConfig<
  TMethod extends HTTPMethod = HTTPMethod,
  TRequest = unknown,
  TResponse = unknown
> {
  readonly method: TMethod;
  readonly path: APIEndpoint;
  readonly requestSchema?: unknown; // Zod schema for validation
  readonly responseSchema?: unknown; // Zod schema for validation
  readonly authRequired?: boolean;
  readonly rateLimit?: number;
  readonly cache?: boolean;
  readonly timeout?: number;
}

/** Type-safe API endpoint definitions */
interface APIEndpoints {
  // Authentication
  'auth/login': APIEndpointConfig<'POST', LoginRequest, AuthResponse>;
  'auth/register': APIEndpointConfig<'POST', RegisterRequest, AuthResponse>;
  'auth/refresh': APIEndpointConfig<'POST', { refreshToken: string }, AuthResponse>;
  'auth/logout': APIEndpointConfig<'POST', never, { success: boolean }>;
  'auth/reset-password': APIEndpointConfig<'POST', ResetPasswordRequest, { success: boolean }>;
  'auth/change-password': APIEndpointConfig<'PUT', ChangePasswordRequest, { success: boolean }>;

  // User Management
  'user/profile': APIEndpointConfig<'GET', never, User>;
  'user/profile': APIEndpointConfig<'PUT', Partial<UserProfile>, User>;
  'user/settings': APIEndpointConfig<'GET', never, UserSettings>;
  'user/settings': APIEndpointConfig<'PUT', Partial<UserSettings>, UserSettings>;

  // Trading Signals
  'signals': APIEndpointConfig<'GET', never, PaginatedResponse<TradingSignal>>;
  'signals/{id}': APIEndpointConfig<'GET', never, TradingSignal>;
  'signals/subscribe': APIEndpointConfig<'POST', { symbols: string[] }, { success: boolean }>;
  'signals/{id}/execute': APIEndpointConfig<'POST', { portfolioId: string; lotSize: number }, TradeExecution>;

  // Portfolio Management
  'portfolios': APIEndpointConfig<'GET', never, Portfolio[]>;
  'portfolios/{id}': APIEndpointConfig<'GET', never, Portfolio>;
  'portfolios/{id}/positions': APIEndpointConfig<'GET', never, Position[]>;
  'portfolios/{id}/orders': APIEndpointConfig<'GET', never, Order[]>;
  'portfolios/{id}/history': APIEndpointConfig<'GET', never, PaginatedResponse<TradeHistory>>;

  // Market Data
  'market/symbols': APIEndpointConfig<'GET', never, TradingSymbol[]>;
  'market/prices': APIEndpointConfig<'GET', never, PriceUpdate[]>;
  'market/news': APIEndpointConfig<'GET', never, PaginatedResponse<MarketNews>>;
}

// ============================================================================
// Export all types
// ============================================================================

export type {
  // Utility types
  OptionalKeys,
  RequiredKeys,
  PartialBy,
  DeepReadonly,
  APIEndpoint,
  HTTPMethod,
  StatusCode,

  // Base response types
  APIResponse,
  PaginatedResponse,
  APIError,
  ValidationError,

  // Authentication
  UserRole,
  LoginRequest,
  RegisterRequest,
  ResetPasswordRequest,
  ChangePasswordRequest,
  DeviceInfo,
  TokenPayload,
  AuthResponse,

  // User types
  User,
  UserProfile,
  UserSubscription,
  SubscriptionLimits,
  UserSettings,
  NotificationSettings,
  TradingSettings,
  DisplaySettings,
  PrivacySettings,

  // Trading signals
  TradingSymbol,
  TradingSignal,
  PriceTarget,
  SignalAnalysis,
  TechnicalIndicator,
  ChartPattern,
  KeyLevel,
  EconomicEvent,
  SignalMetadata,
  BacktestResults,
  SymbolCorrelation,
  SignalStatus,

  // Portfolio and trading
  Portfolio,
  Position,
  Order,
  TradeHistory,
  PerformanceMetrics,
  RiskMetrics,

  // WebSocket events
  WebSocketMessage,
  WebSocketEvents,
  PriceUpdate,
  SignalNotification,
  PortfolioUpdate,
  TradeExecution,
  MarketNews,
  UserNotification,
  SystemStatus,
  ServiceStatus,

  // API configuration
  RequestBodyForMethod,
  APIEndpointConfig,
  APIEndpoints
};

// Export constants
export { USER_ROLES };