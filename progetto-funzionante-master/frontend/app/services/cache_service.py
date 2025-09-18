"""
Redis Cache Service for Performance Optimization
Implements comprehensive caching strategies for frequently accessed data with:
- Connection pooling and health monitoring
- TTL support with automatic expiration
- Cache key generation and management
- Cache invalidation strategies
- Performance metrics and monitoring
- Fallback mechanisms
"""

import json
import pickle
import logging
import hashlib
import time
from typing import Any, Optional, List, Dict, Union, AsyncContextManager
from datetime import datetime, timedelta
import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
import aioredis

from config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class CacheMetrics:
    """Cache performance metrics"""
    hits: int = 0
    misses: int = 0
    errors: int = 0
    total_operations: int = 0
    average_response_time: float = 0.0
    last_health_check: Optional[datetime] = None

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate"""
        if self.total_operations == 0:
            return 0.0
        return (self.hits / self.total_operations) * 100

    @property
    def error_rate(self) -> float:
        """Calculate cache error rate"""
        if self.total_operations == 0:
            return 0.0
        return (self.errors / self.total_operations) * 100


@dataclass
class CacheConfig:
    """Cache configuration settings"""
    redis_url: str = settings.cache.redis_url
    redis_password: Optional[str] = None
    redis_db: int = 0
    default_ttl: int = 3600  # 1 hour default TTL
    max_connections: int = 10
    encoding: str = "utf-8"
    timeout: int = 5
    retry_on_timeout: bool = True
    fallback_enabled: bool = True
    metrics_enabled: bool = True


class CacheService:
    """
    Redis-based caching service with comprehensive features:
    - Connection pooling and health monitoring
    - TTL support with automatic expiration
    - Cache key generation and management
    - Performance metrics and monitoring
    - Fallback mechanisms for graceful degradation
    """

    def __init__(self, config: CacheConfig = None):
        self.config = config or CacheConfig()
        self.redis: Optional[aioredis.Redis] = None
        self._connection_pool: Optional[aioredis.ConnectionPool] = None
        self._metrics = CacheMetrics()
        self._fallback_cache: Dict[str, Any] = {}
        self._connection_healthy = False
        self._fallback_enabled = self.config.fallback_enabled

    async def connect(self) -> bool:
        """
        Initialize Redis connection with connection pooling and health monitoring

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Create connection pool for better performance
            self._connection_pool = aioredis.ConnectionPool.from_url(
                self.config.redis_url,
                max_connections=self.config.max_connections,
                encoding=self.config.encoding,
                decode_responses=True,
                socket_timeout=self.config.timeout,
                socket_connect_timeout=self.config.timeout,
                retry_on_timeout=self.config.retry_on_timeout
            )

            self.redis = aioredis.Redis(connection_pool=self._connection_pool)

            # Test connection and health
            if await self._ping():
                self._connection_healthy = True
                logger.info("Redis cache service connected successfully")
                return True
            else:
                raise ConnectionError("Redis ping failed")

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis = None
            self._connection_healthy = False
            self._fallback_enabled = True
            return False

    async def _ping(self) -> bool:
        """Test Redis connectivity"""
        if not self.redis:
            return False
        try:
            return await self.redis.ping()
        except Exception as e:
            logger.error(f"Redis ping failed: {e}")
            return False

    async def disconnect(self):
        """Close Redis connection and cleanup"""
        if self.redis:
            await self.redis.close()
        if self._connection_pool:
            await self._connection_pool.disconnect()
        self._fallback_cache.clear()
        logger.info("Cache service disconnected")

    def _generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Generate consistent cache key from arguments with application prefixes

        Args:
            prefix: Cache key prefix (e.g., 'signals', 'users')
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            str: Generated cache key
        """
        # Use application-specific prefix
        app_prefix = settings.CACHE_PREFIX

        # Create deterministic key from arguments
        key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"{app_prefix}{prefix}:{key_hash}"

    def _update_metrics(self, hit: bool = False, miss: bool = False, error: bool = False, response_time: float = 0) -> None:
        """Update cache performance metrics"""
        if not self.config.metrics_enabled:
            return

        self._metrics.total_operations += 1

        if hit:
            self._metrics.hits += 1
        elif miss:
            self._metrics.misses += 1
        elif error:
            self._metrics.errors += 1

        # Update average response time using weighted average
        if self._metrics.total_operations == 1:
            self._metrics.average_response_time = response_time
        else:
            weight = 0.1  # 10% weight for new measurements
            self._metrics.average_response_time = (
                (1 - weight) * self._metrics.average_response_time +
                weight * response_time
            )

    async def get(self, key: str, default: Any = None) -> Any:
        """
        Get value from cache with fallback support and metrics

        Args:
            key: Cache key
            default: Default value to return if cache miss

        Returns:
            Cached value or default if not found
        """
        start_time = time.time()
        response_time = 0

        try:
            # Try Redis first if connection is healthy
            if self._connection_healthy and self.redis:
                cached_data = await self.redis.get(key)
                response_time = time.time() - start_time

                if cached_data:
                    # Try JSON first (for simple data), fall back to pickle
                    try:
                        decoded_value = json.loads(cached_data)
                        self._update_metrics(hit=True, response_time=response_time)
                        logger.debug(f"Cache hit for key: {key}")
                        return decoded_value
                    except json.JSONDecodeError:
                        try:
                            decoded_value = pickle.loads(cached_data.encode('latin1'))
                            self._update_metrics(hit=True, response_time=response_time)
                            logger.debug(f"Cache hit (pickle) for key: {key}")
                            return decoded_value
                        except Exception as e:
                            logger.warning(f"Failed to decode cached data for key {key}: {e}")

            # Check fallback cache
            if key in self._fallback_cache:
                fallback_value = self._fallback_cache[key]
                self._update_metrics(hit=True, response_time=time.time() - start_time)
                logger.debug(f"Cache hit (fallback) for key: {key}")
                return fallback_value

            self._update_metrics(miss=True, response_time=time.time() - start_time)
            logger.debug(f"Cache miss for key: {key}")
            return default

        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            self._update_metrics(error=True, response_time=time.time() - start_time)

            # Try fallback cache
            return self._fallback_cache.get(key, default)

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache with TTL support and fallback

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (uses default if None)

        Returns:
            bool: True if successful, False otherwise
        """
        start_time = time.time()
        ttl = ttl or self.config.default_ttl

        try:
            # Serialize value for storage
            try:
                serialized_value = json.dumps(value, default=str)
            except (TypeError, ValueError):
                serialized_value = pickle.dumps(value).decode('latin1')

            # Set in Redis if connection is healthy
            if self._connection_healthy and self.redis:
                await self.redis.setex(key, ttl, serialized_value)

            # Always update fallback cache for reliability
            self._fallback_cache[key] = value

            # Limit fallback cache size (keep most recent 1000 items)
            if len(self._fallback_cache) > 1000:
                # Remove oldest 20% of items
                items_to_remove = len(self._fallback_cache) - 800
                for fallback_key in list(self._fallback_cache.keys())[:items_to_remove]:
                    self._fallback_cache.pop(fallback_key, None)

            self._update_metrics(response_time=time.time() - start_time)
            logger.debug(f"Cache set for key: {key}, TTL: {ttl}s")
            return True

        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            self._update_metrics(error=True, response_time=time.time() - start_time)

            # Always try to set in fallback cache
            self._fallback_cache[key] = value
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache with fallback support"""
        start_time = time.time()

        try:
            # Delete from Redis if connection is healthy
            deleted = False
            if self._connection_healthy and self.redis:
                result = await self.redis.delete(key)
                deleted = result > 0

            # Delete from fallback cache
            if key in self._fallback_cache:
                self._fallback_cache.pop(key, None)
                deleted = True

            self._update_metrics(response_time=time.time() - start_time)
            logger.debug(f"Cache delete for key: {key}, success: {deleted}")
            return deleted

        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            self._update_metrics(error=True, response_time=time.time() - start_time)

            # Try to delete from fallback cache
            if key in self._fallback_cache:
                self._fallback_cache.pop(key, None)
                return True
            return False

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            if self._connection_healthy and self.redis:
                return await self.redis.exists(key) > 0
            return key in self._fallback_cache
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return key in self._fallback_cache

    async def ttl(self, key: str) -> int:
        """Get TTL for key in seconds (-1 if no TTL, -2 if key doesn't exist)"""
        try:
            if self._connection_healthy and self.redis:
                return await self.redis.ttl(key)
            return -1  # Unknown TTL for fallback cache
        except Exception as e:
            logger.error(f"Cache TTL error for key {key}: {e}")
            return -1

    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration for existing key"""
        try:
            if self._connection_healthy and self.redis:
                return await self.redis.expire(key, ttl)
            return False  # No expiration in fallback cache
        except Exception as e:
            logger.error(f"Cache expire error for key {key}: {e}")
            return False

    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching pattern with fallback support

        Args:
            pattern: Redis pattern (e.g., 'signals:*')

        Returns:
            int: Number of keys deleted
        """
        start_time = time.time()

        try:
            count = 0

            # Invalidate from Redis if connection is healthy
            if self._connection_healthy and self.redis:
                keys = []
                async for key in self.redis.scan_iter(match=pattern):
                    keys.append(key)

                if keys:
                    count = await self.redis.delete(*keys)
                    logger.info(f"Invalidated {count} Redis keys matching pattern: {pattern}")

            # Invalidate from fallback cache
            fallback_keys = [k for k in self._fallback_cache.keys() if pattern.replace("*", "") in k]
            for key in fallback_keys:
                self._fallback_cache.pop(key, None)

            if fallback_keys:
                logger.info(f"Invalidated {len(fallback_keys)} fallback cache keys matching pattern: {pattern}")
                count += len(fallback_keys)

            self._update_metrics(response_time=time.time() - start_time)
            return count

        except Exception as e:
            logger.error(f"Cache invalidate pattern error for {pattern}: {e}")
            self._update_metrics(error=True, response_time=time.time() - start_time)

            # Try to invalidate from fallback cache only
            fallback_keys = [k for k in self._fallback_cache.keys() if pattern.replace("*", "") in k]
            for key in fallback_keys:
                self._fallback_cache.pop(key, None)

            return len(fallback_keys)

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check

        Returns:
            Dict: Health check results with detailed metrics
        """
        start_time = time.time()

        health_info = {
            "status": "healthy",
            "connection_healthy": self._connection_healthy,
            "fallback_enabled": self._fallback_enabled,
            "pool_size": self.config.max_connections,
            "fallback_cache_size": len(self._fallback_cache),
            "metrics_enabled": self.config.metrics_enabled,
            "timestamp": datetime.utcnow().isoformat()
        }

        if self.config.metrics_enabled:
            health_info["metrics"] = {
                "hit_rate": round(self._metrics.hit_rate, 2),
                "error_rate": round(self._metrics.error_rate, 2),
                "total_operations": self._metrics.total_operations,
                "hits": self._metrics.hits,
                "misses": self._metrics.misses,
                "errors": self._metrics.errors,
                "average_response_time_ms": round(self._metrics.average_response_time * 1000, 2)
            }

        # Test Redis connection
        if self._connection_healthy and self.redis:
            try:
                ping_time = time.time()
                ping_success = await self._ping()
                ping_response_time = time.time() - ping_time

                health_info.update({
                    "ping_success": ping_success,
                    "ping_response_time_ms": round(ping_response_time * 1000, 2),
                    "total_response_time_ms": round((time.time() - start_time) * 1000, 2)
                })

                if not ping_success:
                    health_info["status"] = "degraded"
                    self._connection_healthy = False
                    self._fallback_enabled = True

            except Exception as e:
                health_info.update({
                    "status": "unhealthy",
                    "error": str(e),
                    "ping_success": False,
                    "total_response_time_ms": round((time.time() - start_time) * 1000, 2)
                })
                self._connection_healthy = False
                self._fallback_enabled = True

        self._metrics.last_health_check = datetime.utcnow()
        return health_info

    def get_metrics(self) -> CacheMetrics:
        """Get cache performance metrics"""
        return self._metrics

    def reset_metrics(self) -> None:
        """Reset cache performance metrics"""
        self._metrics = CacheMetrics()
        logger.info("Cache metrics reset")

    @asynccontextmanager
    async def get_connection(self):
        """Get Redis connection from pool for manual operations"""
        if not self.redis:
            raise RuntimeError("Redis not initialized")

        try:
            yield self.redis
        except Exception as e:
            logger.error(f"Redis connection error: {e}")
            raise

    # High-level caching methods for specific use cases with configuration-based TTLs

    async def cache_signals(self, key_suffix: str, signals: List[Dict], ttl: Optional[int] = None) -> bool:
        """
        Cache signals data with configurable TTL

        Args:
            key_suffix: Unique identifier for the signals query
            signals: List of signal dictionaries
            ttl: Cache TTL in seconds (uses config default if None)
        """
        cache_key = f"{settings.CACHE_PREFIX_SIGNALS}{key_suffix}"
        return await self.set(cache_key, signals, ttl or settings.CACHE_TTL_MEDIUM)

    async def get_cached_signals(self, key_suffix: str) -> Optional[List[Dict]]:
        """Get cached signals data"""
        cache_key = f"{settings.CACHE_PREFIX_SIGNALS}{key_suffix}"
        return await self.get(cache_key)

    async def cache_user_data(self, user_id: Union[int, str], user_data: Dict, ttl: Optional[int] = None) -> bool:
        """
        Cache user data with configurable TTL

        Args:
            user_id: User ID
            user_data: User data dictionary
            ttl: Cache TTL in seconds (uses config default if None)
        """
        cache_key = f"{settings.CACHE_PREFIX_USERS}{user_id}"
        return await self.set(cache_key, user_data, ttl or settings.CACHE_TTL_LONG)

    async def get_cached_user_data(self, user_id: Union[int, str]) -> Optional[Dict]:
        """Get cached user data"""
        cache_key = f"{settings.CACHE_PREFIX_USERS}{user_id}"
        return await self.get(cache_key)

    async def cache_market_data(self, symbol: str, timeframe: str, data: Dict, ttl: Optional[int] = None) -> bool:
        """
        Cache market data with configurable TTL

        Args:
            symbol: Trading symbol (e.g., EUR_USD)
            timeframe: Timeframe (e.g., M1, H1)
            data: Market data dictionary
            ttl: Cache TTL in seconds (uses config default if None)
        """
        cache_key = f"{settings.CACHE_PREFIX_MARKET_DATA}{symbol}:{timeframe}"
        return await self.set(cache_key, data, ttl or settings.CACHE_TTL_SHORT)

    async def get_cached_market_data(self, symbol: str, timeframe: str) -> Optional[Dict]:
        """Get cached market data"""
        cache_key = f"{settings.CACHE_PREFIX_MARKET_DATA}{symbol}:{timeframe}"
        return await self.get(cache_key)

    async def cache_api_response(self, endpoint: str, params: Dict, data: Any, ttl: Optional[int] = None) -> bool:
        """
        Cache API response with configurable TTL

        Args:
            endpoint: API endpoint path
            params: Request parameters (for key generation)
            data: Response data to cache
            ttl: Cache TTL in seconds (uses config default if None)
        """
        param_hash = hashlib.md5(str(sorted(params.items())).encode()).hexdigest()
        cache_key = f"{settings.CACHE_PREFIX_API}{endpoint}:{param_hash}"
        return await self.set(cache_key, data, ttl or settings.CACHE_TTL_MEDIUM)

    async def get_cached_api_response(self, endpoint: str, params: Dict) -> Optional[Any]:
        """Get cached API response"""
        param_hash = hashlib.md5(str(sorted(params.items())).encode()).hexdigest()
        cache_key = f"{settings.CACHE_PREFIX_API}{endpoint}:{param_hash}"
        return await self.get(cache_key)

    async def cache_signal_statistics(self, stats: Dict, ttl: Optional[int] = None) -> bool:
        """
        Cache signal statistics with configurable TTL

        Args:
            stats: Statistics dictionary
            ttl: Cache TTL in seconds (uses config default if None)
        """
        cache_key = f"{settings.CACHE_PREFIX_SIGNALS}statistics"
        return await self.set(cache_key, stats, ttl or settings.CACHE_TTL_MEDIUM)

    async def get_cached_signal_statistics(self) -> Optional[Dict]:
        """Get cached signal statistics"""
        cache_key = f"{settings.CACHE_PREFIX_SIGNALS}statistics"
        return await self.get(cache_key)

    async def cache_user_session(self, session_id: str, session_data: Dict, ttl: Optional[int] = None) -> bool:
        """
        Cache user session data

        Args:
            session_id: Session ID
            session_data: Session data dictionary
            ttl: Cache TTL in seconds (uses config default if None)
        """
        cache_key = f"{settings.CACHE_PREFIX_USERS}session:{session_id}"
        return await self.set(cache_key, session_data, ttl or settings.CACHE_TTL_VERY_LONG)

    async def get_cached_user_session(self, session_id: str) -> Optional[Dict]:
        """Get cached user session data"""
        cache_key = f"{settings.CACHE_PREFIX_USERS}session:{session_id}"
        return await self.get(cache_key)

    async def invalidate_user_cache(self, user_id: Union[int, str]) -> bool:
        """Invalidate all cache entries for a specific user"""
        pattern = f"{settings.CACHE_PREFIX_USERS}*{user_id}*"
        deleted_count = await self.invalidate_pattern(pattern)
        logger.info(f"Invalidated {deleted_count} cache entries for user {user_id}")
        return deleted_count > 0

    async def invalidate_signals_cache(self, pattern: Optional[str] = None) -> bool:
        """
        Invalidate signals cache entries

        Args:
            pattern: Specific pattern to invalidate (all signals if None)
        """
        if pattern:
            full_pattern = f"{settings.CACHE_PREFIX_SIGNALS}{pattern}"
        else:
            full_pattern = f"{settings.CACHE_PREFIX_SIGNALS}*"

        deleted_count = await self.invalidate_pattern(full_pattern)
        logger.info(f"Invalidated {deleted_count} signals cache entries")
        return deleted_count > 0

    async def invalidate_market_data_cache(self, symbol: Optional[str] = None, timeframe: Optional[str] = None) -> bool:
        """
        Invalidate market data cache entries

        Args:
            symbol: Specific symbol to invalidate (all if None)
            timeframe: Specific timeframe to invalidate (all if None)
        """
        pattern_parts = [settings.CACHE_PREFIX_MARKET_DATA]
        if symbol:
            pattern_parts.append(symbol)
        if timeframe:
            pattern_parts.append(timeframe)

        pattern = "*".join(pattern_parts) + "*"
        deleted_count = await self.invalidate_pattern(pattern)
        logger.info(f"Invalidated {deleted_count} market data cache entries")
        return deleted_count > 0

    async def invalidate_api_cache(self, endpoint: Optional[str] = None) -> bool:
        """
        Invalidate API cache entries

        Args:
            endpoint: Specific endpoint to invalidate (all if None)
        """
        if endpoint:
            pattern = f"{settings.CACHE_PREFIX_API}{endpoint}*"
        else:
            pattern = f"{settings.CACHE_PREFIX_API}*"

        deleted_count = await self.invalidate_pattern(pattern)
        logger.info(f"Invalidated {deleted_count} API cache entries")
        return deleted_count > 0

    async def warm_cache(self, warmup_functions: List[callable]) -> Dict[str, Any]:
        """
        Warm up cache by pre-loading frequently accessed data

        Args:
            warmup_functions: List of async functions that return data to cache

        Returns:
            Dict: Warmup results summary
        """
        results = {
            "total_functions": len(warmup_functions),
            "successful": 0,
            "failed": 0,
            "errors": [],
            "start_time": datetime.utcnow().isoformat(),
            "end_time": None
        }

        logger.info(f"Starting cache warmup with {len(warmup_functions)} functions")

        for func in warmup_functions:
            try:
                func_name = func.__name__
                logger.debug(f"Warming cache with function: {func_name}")

                # Execute warmup function
                data = await func()

                if data is not None:
                    results["successful"] += 1
                    logger.debug(f"Cache warmup successful for {func_name}")
                else:
                    results["failed"] += 1
                    logger.warning(f"Cache warmup function {func_name} returned None")

            except Exception as e:
                results["failed"] += 1
                error_info = f"Cache warmup failed for {func.__name__}: {str(e)}"
                results["errors"].append(error_info)
                logger.error(error_info)

        results["end_time"] = datetime.utcnow().isoformat()
        logger.info(f"Cache warmup completed: {results['successful']} successful, {results['failed']} failed")

        return results

    # Decorator for automatic caching with advanced features
def cache_result(cache_service: CacheService, key_prefix: str, ttl: Optional[int] = None,
                ignore_args: Optional[List[int]] = None, use_params_for_key: bool = True):
    """
    Advanced decorator to automatically cache function results

    Args:
        cache_service: CacheService instance
        key_prefix: Cache key prefix
        ttl: Cache TTL in seconds (uses service default if None)
        ignore_args: List of argument indices to ignore in key generation
        use_params_for_key: Whether to include parameters in cache key generation
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key from function arguments
            cache_args = args[1:] if ignore_args and 0 in ignore_args else args
            cache_kwargs = kwargs if use_params_for_key else {}

            if ignore_args:
                # Filter out ignored arguments
                filtered_args = [arg for i, arg in enumerate(cache_args) if i not in ignore_args]
                cache_key = cache_service._generate_cache_key(key_prefix, *filtered_args, **cache_kwargs)
            else:
                cache_key = cache_service._generate_cache_key(key_prefix, *cache_args, **cache_kwargs)

            # Try to get from cache first
            cached_result = await cache_service.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {key_prefix}: {cache_key}")
                return cached_result

            # Execute function and cache result
            result = await func(*args, **kwargs)
            if result is not None:
                success = await cache_service.set(cache_key, result, ttl)
                if success:
                    logger.debug(f"Cache miss, stored result for {key_prefix}: {cache_key}")

            return result
        return wrapper
    return decorator


def cache_by_user(cache_service: CacheService, key_prefix: str, ttl: Optional[int] = None):
    """
    Decorator that caches results by user ID (first argument after self)

    Args:
        cache_service: CacheService instance
        key_prefix: Cache key prefix
        ttl: Cache TTL in seconds (uses service default if None)
    """
    return cache_result(cache_service, key_prefix, ttl, ignore_args=[0])


# Global cache service instance with configuration from settings
cache_service = CacheService(CacheConfig(
    redis_url=settings.cache.redis_url,
    redis_password=settings.cache.redis_password,
    redis_db=settings.cache.redis_db,
    max_connections=settings.cache.redis_max_connections,
    timeout=settings.cache.redis_timeout,
    retry_on_timeout=settings.cache.redis_retry_on_timeout,
    fallback_enabled=True,
    metrics_enabled=True
))


async def init_cache(redis_url: str = None) -> bool:
    """
    Initialize global cache service with configuration

    Args:
        redis_url: Redis connection URL (optional, overrides config)

    Returns:
        bool: True if initialization successful
    """
    if redis_url:
        cache_service.config.redis_url = redis_url

    logger.info("Initializing cache service...")
    success = await cache_service.connect()

    if success:
        logger.info("Cache service initialized successfully")
    else:
        logger.warning("Cache service initialization failed, fallback cache enabled")

    return success


async def cleanup_cache():
    """Cleanup global cache service"""
    logger.info("Cleaning up cache service...")
    await cache_service.disconnect()


# Cache initialization and cleanup utilities