/**
 * Type-Safe HTTP Client with Advanced Error Handling
 * Features request/response interceptors, retry logic, and offline support
 */

import axios, {
  AxiosInstance,
  AxiosRequestConfig,
  AxiosResponse,
  AxiosError,
  InternalAxiosRequestConfig
} from 'axios';
import type {
  APIResponse,
  APIError,
  HTTPMethod,
  APIEndpoint,
  StatusCode,
  ValidationError
} from '@/types/api';

// ============================================================================
// Advanced Type Definitions
// ============================================================================

/** Request configuration with type safety */
interface TypedRequestConfig<TData = unknown> extends Omit<AxiosRequestConfig<TData>, 'method' | 'url'> {
  readonly method?: HTTPMethod;
  readonly url?: APIEndpoint;
  readonly retryCount?: number;
  readonly skipRetry?: boolean;
  readonly skipAuth?: boolean;
  readonly cache?: boolean;
  readonly deduplication?: boolean;
  readonly priority?: 'low' | 'normal' | 'high';
  readonly timeout?: number;
  readonly metadata?: Record<string, unknown>;
}

/** HTTP client configuration */
interface HTTPClientConfig {
  readonly baseURL: string;
  readonly timeout: number;
  readonly retryAttempts: number;
  readonly retryDelay: number;
  readonly maxRetryDelay: number;
  readonly retryCondition: (error: AxiosError) => boolean;
  readonly enableOfflineSupport: boolean;
  readonly enableRequestDeduplication: boolean;
  readonly enableCaching: boolean;
  readonly cacheMaxAge: number;
  readonly requestIdHeader: string;
  readonly correlationIdHeader: string;
}

/** Request interceptor function type */
type RequestInterceptor = (
  config: InternalAxiosRequestConfig
) => InternalAxiosRequestConfig | Promise<InternalAxiosRequestConfig>;

/** Response interceptor function type */
type ResponseInterceptor = (
  response: AxiosResponse
) => AxiosResponse | Promise<AxiosResponse>;

/** Error interceptor function type */
type ErrorInterceptor = (
  error: AxiosError
) => Promise<never>;

/** Network connectivity status */
interface NetworkStatus {
  readonly isOnline: boolean;
  readonly connectionType: 'wifi' | 'cellular' | 'ethernet' | 'unknown';
  readonly effectiveType: '2g' | '3g' | '4g' | '5g' | 'unknown';
  readonly downlink: number;
  readonly rtt: number;
}

/** Request metrics for monitoring */
interface RequestMetrics {
  readonly requestId: string;
  readonly url: string;
  readonly method: HTTPMethod;
  readonly startTime: number;
  readonly endTime?: number;
  readonly duration?: number;
  readonly size?: number;
  readonly cached: boolean;
  readonly retryCount: number;
  readonly error?: APIError;
}

/** Cache entry structure */
interface CacheEntry<TData = unknown> {
  readonly data: TData;
  readonly timestamp: number;
  readonly expiresAt: number;
  readonly etag?: string;
  readonly lastModified?: string;
}

// ============================================================================
// Custom Error Classes
// ============================================================================

/** Base API error class */
class APIClientError extends Error {
  constructor(
    message: string,
    public readonly code: string,
    public readonly statusCode?: StatusCode,
    public readonly details?: Record<string, unknown>
  ) {
    super(message);
    this.name = 'APIClientError';

    // Ensure proper prototype chain
    Object.setPrototypeOf(this, APIClientError.prototype);
  }
}

/** Network connectivity error */
class NetworkError extends APIClientError {
  constructor(message: string, public readonly isOffline: boolean = false) {
    super(message, 'NETWORK_ERROR', undefined, { isOffline });
    this.name = 'NetworkError';
    Object.setPrototypeOf(this, NetworkError.prototype);
  }
}

/** Request timeout error */
class TimeoutError extends APIClientError {
  constructor(message: string, public readonly timeout: number) {
    super(message, 'TIMEOUT_ERROR', 408, { timeout });
    this.name = 'TimeoutError';
    Object.setPrototypeOf(this, TimeoutError.prototype);
  }
}

/** Validation error */
class ClientValidationError extends APIClientError {
  constructor(
    message: string,
    public readonly field: string,
    public readonly value: unknown,
    public readonly constraints: string[]
  ) {
    super(message, 'VALIDATION_ERROR', 422, { field, value, constraints });
    this.name = 'ClientValidationError';
    Object.setPrototypeOf(this, ClientValidationError.prototype);
  }
}

// ============================================================================
// Utility Functions
// ============================================================================

/** Generate unique request ID */
const generateRequestId = (): string => {
  return `req_${Date.now()}_${Math.random().toString(36).substring(2, 15)}`;
};

/** Generate correlation ID for tracing */
const generateCorrelationId = (): string => {
  return `corr_${Date.now()}_${Math.random().toString(36).substring(2, 15)}`;
};

/** Create cache key from request config */
const createCacheKey = (config: InternalAxiosRequestConfig): string => {
  const { method, url, params, data } = config;
  return `${method}:${url}:${JSON.stringify({ params, data })}`;
};

/** Check if error is retryable */
const isRetryableError = (error: AxiosError): boolean => {
  if (error.code === 'ENOTFOUND' || error.code === 'ECONNREFUSED') {
    return true;
  }

  const status = error.response?.status;
  return !status || status >= 500 || status === 429 || status === 408;
};

/** Calculate retry delay with exponential backoff */
const calculateRetryDelay = (attempt: number, baseDelay: number, maxDelay: number): number => {
  const delay = baseDelay * Math.pow(2, attempt);
  const jitter = Math.random() * 0.1 * delay;
  return Math.min(delay + jitter, maxDelay);
};

/** Get network status (if available in browser) */
const getNetworkStatus = (): NetworkStatus => {
  if (typeof navigator === 'undefined' || !('connection' in navigator)) {
    return {
      isOnline: typeof navigator !== 'undefined' ? navigator.onLine : true,
      connectionType: 'unknown',
      effectiveType: 'unknown',
      downlink: 0,
      rtt: 0
    };
  }

  const connection = (navigator as any).connection || (navigator as any).mozConnection || (navigator as any).webkitConnection;

  return {
    isOnline: navigator.onLine,
    connectionType: connection?.type || 'unknown',
    effectiveType: connection?.effectiveType || 'unknown',
    downlink: connection?.downlink || 0,
    rtt: connection?.rtt || 0
  };
};

// ============================================================================
// HTTP Client Implementation
// ============================================================================

/** Type-safe HTTP client with advanced features */
export class TypedHTTPClient {
  private readonly client: AxiosInstance;
  private readonly config: HTTPClientConfig;
  private readonly cache = new Map<string, CacheEntry>();
  private readonly pendingRequests = new Map<string, Promise<AxiosResponse>>();
  private readonly requestMetrics = new Map<string, RequestMetrics>();
  private readonly offlineQueue: Array<{ config: InternalAxiosRequestConfig; resolve: (value: any) => void; reject: (reason: any) => void }> = [];

  private networkStatus: NetworkStatus = getNetworkStatus();

  constructor(config: Partial<HTTPClientConfig> = {}) {
    this.config = {
      baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001',
      timeout: 30000,
      retryAttempts: 3,
      retryDelay: 1000,
      maxRetryDelay: 10000,
      retryCondition: isRetryableError,
      enableOfflineSupport: true,
      enableRequestDeduplication: true,
      enableCaching: true,
      cacheMaxAge: 300000, // 5 minutes
      requestIdHeader: 'X-Request-ID',
      correlationIdHeader: 'X-Correlation-ID',
      ...config
    };

    this.client = axios.create({
      baseURL: this.config.baseURL,
      timeout: this.config.timeout,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      }
    });

    this.setupInterceptors();
    this.setupNetworkMonitoring();
  }

  /** Setup request and response interceptors */
  private setupInterceptors(): void {
    // Request interceptor
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const requestId = generateRequestId();
        const correlationId = generateCorrelationId();

        config.headers = config.headers || {};
        config.headers[this.config.requestIdHeader] = requestId;
        config.headers[this.config.correlationIdHeader] = correlationId;

        // Track request metrics
        this.requestMetrics.set(requestId, {
          requestId,
          url: `${config.baseURL}${config.url}`,
          method: (config.method?.toUpperCase() as HTTPMethod) || 'GET',
          startTime: Date.now(),
          cached: false,
          retryCount: 0
        });

        return config;
      },
      (error: AxiosError) => {
        return Promise.reject(this.transformError(error));
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response: AxiosResponse) => {
        const requestId = response.config.headers?.[this.config.requestIdHeader] as string;

        if (requestId && this.requestMetrics.has(requestId)) {
          const metrics = this.requestMetrics.get(requestId)!;
          const endTime = Date.now();

          this.requestMetrics.set(requestId, {
            ...metrics,
            endTime,
            duration: endTime - metrics.startTime,
            size: JSON.stringify(response.data).length
          });
        }

        return response;
      },
      async (error: AxiosError) => {
        const requestId = error.config?.headers?.[this.config.requestIdHeader] as string;

        if (requestId && this.requestMetrics.has(requestId)) {
          const metrics = this.requestMetrics.get(requestId)!;
          this.requestMetrics.set(requestId, {
            ...metrics,
            endTime: Date.now(),
            error: this.transformError(error) as APIError
          });
        }

        // Handle retry logic
        if (this.shouldRetry(error)) {
          return this.retryRequest(error);
        }

        // Handle offline scenarios
        if (!this.networkStatus.isOnline && this.config.enableOfflineSupport) {
          return this.handleOfflineRequest(error);
        }

        return Promise.reject(this.transformError(error));
      }
    );
  }

  /** Setup network connectivity monitoring */
  private setupNetworkMonitoring(): void {
    if (typeof window === 'undefined') return;

    const updateNetworkStatus = () => {
      this.networkStatus = getNetworkStatus();

      // Process offline queue when coming back online
      if (this.networkStatus.isOnline && this.offlineQueue.length > 0) {
        this.processOfflineQueue();
      }
    };

    window.addEventListener('online', updateNetworkStatus);
    window.addEventListener('offline', updateNetworkStatus);

    // Listen for connection changes
    if ('connection' in navigator) {
      (navigator as any).connection?.addEventListener('change', updateNetworkStatus);
    }
  }

  /** Check if request should be retried */
  private shouldRetry(error: AxiosError): boolean {
    const config = error.config as InternalAxiosRequestConfig & { retryCount?: number; skipRetry?: boolean };

    if (config?.skipRetry) return false;

    const retryCount = config?.retryCount || 0;
    return retryCount < this.config.retryAttempts && this.config.retryCondition(error);
  }

  /** Retry failed request with exponential backoff */
  private async retryRequest(error: AxiosError): Promise<AxiosResponse> {
    const config = error.config as InternalAxiosRequestConfig & { retryCount?: number };
    const retryCount = (config?.retryCount || 0) + 1;

    const delay = calculateRetryDelay(retryCount - 1, this.config.retryDelay, this.config.maxRetryDelay);

    await new Promise(resolve => setTimeout(resolve, delay));

    return this.client({
      ...config,
      retryCount
    });
  }

  /** Handle offline request queueing */
  private async handleOfflineRequest(error: AxiosError): Promise<never> {
    if (!error.config) {
      throw this.transformError(error);
    }

    return new Promise((resolve, reject) => {
      this.offlineQueue.push({
        config: error.config!,
        resolve,
        reject
      });
    });
  }

  /** Process queued offline requests */
  private async processOfflineQueue(): Promise<void> {
    const queue = [...this.offlineQueue];
    this.offlineQueue.length = 0;

    for (const { config, resolve, reject } of queue) {
      try {
        const response = await this.client(config);
        resolve(response);
      } catch (error) {
        reject(error);
      }
    }
  }

  /** Transform axios error to typed API error */
  private transformError(error: AxiosError): APIError | NetworkError | TimeoutError {
    // Network errors
    if (error.code === 'ENOTFOUND' || error.code === 'ECONNREFUSED') {
      return new NetworkError('Network connection failed', !this.networkStatus.isOnline);
    }

    // Timeout errors
    if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
      return new TimeoutError('Request timeout', this.config.timeout);
    }

    // API errors with structured response
    if (error.response?.data) {
      const errorData = error.response.data as APIError;
      return {
        code: errorData.code || 'UNKNOWN_ERROR',
        message: errorData.message || error.message,
        details: errorData.details,
        field: errorData.field,
        statusCode: error.response.status as StatusCode,
        timestamp: errorData.timestamp || new Date().toISOString(),
        requestId: error.config?.headers?.[this.config.requestIdHeader] as string || generateRequestId()
      };
    }

    // Generic error
    return {
      code: 'REQUEST_FAILED',
      message: error.message || 'Request failed',
      statusCode: (error.response?.status as StatusCode) || 500,
      timestamp: new Date().toISOString(),
      requestId: error.config?.headers?.[this.config.requestIdHeader] as string || generateRequestId()
    };
  }

  /** Get data from cache */
  private getCachedData<TData>(key: string): TData | null {
    if (!this.config.enableCaching) return null;

    const entry = this.cache.get(key);
    if (!entry || Date.now() > entry.expiresAt) {
      this.cache.delete(key);
      return null;
    }

    return entry.data as TData;
  }

  /** Store data in cache */
  private setCachedData<TData>(key: string, data: TData, maxAge: number = this.config.cacheMaxAge): void {
    if (!this.config.enableCaching) return;

    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      expiresAt: Date.now() + maxAge
    });
  }

  /** Make typed HTTP request */
  public async request<TResponse = unknown, TRequest = unknown>(
    config: TypedRequestConfig<TRequest>
  ): Promise<APIResponse<TResponse>> {
    const fullConfig: InternalAxiosRequestConfig = {
      ...config,
      url: config.url || '/',
      method: config.method || 'GET'
    };

    // Check cache for GET requests
    if (fullConfig.method === 'GET' && config.cache !== false) {
      const cacheKey = createCacheKey(fullConfig);
      const cachedData = this.getCachedData<APIResponse<TResponse>>(cacheKey);

      if (cachedData) {
        // Update metrics for cached request
        const requestId = generateRequestId();
        this.requestMetrics.set(requestId, {
          requestId,
          url: `${this.config.baseURL}${fullConfig.url}`,
          method: fullConfig.method as HTTPMethod,
          startTime: Date.now(),
          endTime: Date.now(),
          duration: 0,
          cached: true,
          retryCount: 0
        });

        return cachedData;
      }
    }

    // Request deduplication
    if (this.config.enableRequestDeduplication && config.deduplication !== false) {
      const deduplicationKey = createCacheKey(fullConfig);

      if (this.pendingRequests.has(deduplicationKey)) {
        const pendingRequest = this.pendingRequests.get(deduplicationKey)!;
        return (await pendingRequest).data;
      }

      const requestPromise = this.client(fullConfig);
      this.pendingRequests.set(deduplicationKey, requestPromise);

      try {
        const response = await requestPromise;

        // Cache successful GET responses
        if (fullConfig.method === 'GET' && config.cache !== false) {
          const cacheKey = createCacheKey(fullConfig);
          this.setCachedData(cacheKey, response.data);
        }

        return response.data;
      } finally {
        this.pendingRequests.delete(deduplicationKey);
      }
    }

    const response = await this.client<APIResponse<TResponse>>(fullConfig);

    // Cache successful GET responses
    if (fullConfig.method === 'GET' && config.cache !== false) {
      const cacheKey = createCacheKey(fullConfig);
      this.setCachedData(cacheKey, response.data);
    }

    return response.data;
  }

  /** Convenience methods for different HTTP verbs */
  public get<TResponse = unknown>(
    url: APIEndpoint,
    config?: Omit<TypedRequestConfig, 'method' | 'url' | 'data'>
  ): Promise<APIResponse<TResponse>> {
    return this.request<TResponse>({ ...config, method: 'GET', url });
  }

  public post<TResponse = unknown, TRequest = unknown>(
    url: APIEndpoint,
    data?: TRequest,
    config?: Omit<TypedRequestConfig<TRequest>, 'method' | 'url' | 'data'>
  ): Promise<APIResponse<TResponse>> {
    return this.request<TResponse, TRequest>({ ...config, method: 'POST', url, data });
  }

  public put<TResponse = unknown, TRequest = unknown>(
    url: APIEndpoint,
    data?: TRequest,
    config?: Omit<TypedRequestConfig<TRequest>, 'method' | 'url' | 'data'>
  ): Promise<APIResponse<TResponse>> {
    return this.request<TResponse, TRequest>({ ...config, method: 'PUT', url, data });
  }

  public patch<TResponse = unknown, TRequest = unknown>(
    url: APIEndpoint,
    data?: TRequest,
    config?: Omit<TypedRequestConfig<TRequest>, 'method' | 'url' | 'data'>
  ): Promise<APIResponse<TResponse>> {
    return this.request<TResponse, TRequest>({ ...config, method: 'PATCH', url, data });
  }

  public delete<TResponse = unknown>(
    url: APIEndpoint,
    config?: Omit<TypedRequestConfig, 'method' | 'url' | 'data'>
  ): Promise<APIResponse<TResponse>> {
    return this.request<TResponse>({ ...config, method: 'DELETE', url });
  }

  /** Add request interceptor */
  public addRequestInterceptor(interceptor: RequestInterceptor): number {
    return this.client.interceptors.request.use(interceptor);
  }

  /** Add response interceptor */
  public addResponseInterceptor(interceptor: ResponseInterceptor): number {
    return this.client.interceptors.response.use(interceptor);
  }

  /** Add error interceptor */
  public addErrorInterceptor(interceptor: ErrorInterceptor): number {
    return this.client.interceptors.response.use(undefined, interceptor);
  }

  /** Remove interceptor */
  public removeInterceptor(type: 'request' | 'response', id: number): void {
    this.client.interceptors[type].eject(id);
  }

  /** Get request metrics */
  public getRequestMetrics(requestId?: string): RequestMetrics | RequestMetrics[] {
    if (requestId) {
      return this.requestMetrics.get(requestId) || ({} as RequestMetrics);
    }
    return Array.from(this.requestMetrics.values());
  }

  /** Clear cache */
  public clearCache(): void {
    this.cache.clear();
  }

  /** Get network status */
  public getNetworkStatus(): NetworkStatus {
    return { ...this.networkStatus };
  }

  /** Get client configuration */
  public getConfig(): HTTPClientConfig {
    return { ...this.config };
  }
}

// ============================================================================
// Default client instance
// ============================================================================

/** Default HTTP client instance */
export const httpClient = new TypedHTTPClient();

/** Export error classes for external use */
export {
  APIClientError,
  NetworkError,
  TimeoutError,
  ClientValidationError
};

/** Export types */
export type {
  TypedRequestConfig,
  HTTPClientConfig,
  RequestInterceptor,
  ResponseInterceptor,
  ErrorInterceptor,
  NetworkStatus,
  RequestMetrics,
  CacheEntry
};