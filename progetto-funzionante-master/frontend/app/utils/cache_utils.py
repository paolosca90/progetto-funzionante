"""
Cache utilities and helpers for application integration.

This module provides:
- Enhanced caching decorators
- Cache key generation helpers
- Cache warming strategies
- Database query caching utilities
- API response caching helpers
"""

import json
import hashlib
from typing import Any, Optional, List, Dict, Union, Callable, AsyncContextManager
from functools import wraps
from datetime import datetime, timedelta
import logging

from app.services.cache_service import cache_service, CacheService
from app.core.config import settings

logger = logging.getLogger(__name__)


def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Generate standardized cache key with application prefix

    Args:
        prefix: Cache key prefix
        *args: Positional arguments for key generation
        **kwargs: Keyword arguments for key generation

    Returns:
        str: Generated cache key
    """
    return cache_service._generate_cache_key(prefix, *args, **kwargs)


def cache_database_query(ttl: Optional[int] = None, key_prefix: str = "db_query"):
    """
    Decorator for caching database query results

    Args:
        ttl: Cache TTL in seconds (uses config default if None)
        key_prefix: Cache key prefix

    Usage:
        @cache_database_query(ttl=300)
        async def get_user_by_id(self, user_id: int):
            # Database query logic
            return user_data
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = generate_cache_key(key_prefix, func.__name__, *args[1:], **kwargs)

            # Try cache first
            cached_result = await cache_service.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Database query cache hit: {func.__name__}")
                return cached_result

            # Execute query
            result = await func(*args, **kwargs)

            # Cache result if not None
            if result is not None:
                await cache_service.set(cache_key, result, ttl or settings.CACHE_TTL_MEDIUM)
                logger.debug(f"Database query cached: {func.__name__}")

            return result
        return wrapper
    return decorator


def cache_api_response(ttl: Optional[int] = None, ignore_params: Optional[List[str]] = None):
    """
    Decorator for caching API responses

    Args:
        ttl: Cache TTL in seconds (uses config default if None)
        ignore_params: List of parameter names to ignore in cache key generation

    Usage:
        @cache_api_response(ttl=60, ignore_params=['timestamp'])
        async def get_oanda_prices(self, symbol: str, timeframe: str, timestamp: datetime):
            # API call logic
            return data
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Filter parameters for cache key generation
            filtered_kwargs = {
                k: v for k, v in kwargs.items()
                if ignore_params is None or k not in ignore_params
            }

            # Generate cache key
            cache_key = generate_cache_key("api", func.__name__, *args[1:], **filtered_kwargs)

            # Try cache first
            cached_result = await cache_service.get(cache_key)
            if cached_result is not None:
                logger.debug(f"API response cache hit: {func.__name__}")
                return cached_result

            # Execute API call
            result = await func(*args, **kwargs)

            # Cache result if not None
            if result is not None:
                await cache_service.set(cache_key, result, ttl or settings.CACHE_TTL_SHORT)
                logger.debug(f"API response cached: {func.__name__}")

            return result
        return wrapper
    return decorator


def cache_user_data(ttl: Optional[int] = None):
    """
    Decorator for caching user-specific data

    Args:
        ttl: Cache TTL in seconds (uses config default if None)

    Usage:
        @cache_user_data(ttl=1800)
        async def get_user_profile(self, user_id: int):
            # User data retrieval logic
            return profile_data
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user_id from first argument after self
            user_id = args[1] if len(args) > 1 else kwargs.get('user_id')

            if not user_id:
                return await func(*args, **kwargs)

            # Generate user-specific cache key
            cache_key = generate_cache_key("user", func.__name__, user_id, **kwargs)

            # Try cache first
            cached_result = await cache_service.get(cache_key)
            if cached_result is not None:
                logger.debug(f"User data cache hit: {func.__name__} for user {user_id}")
                return cached_result

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result if not None
            if result is not None:
                await cache_service.set(cache_key, result, ttl or settings.CACHE_TTL_LONG)
                logger.debug(f"User data cached: {func.__name__} for user {user_id}")

            return result
        return wrapper
    return decorator


def cache_signal_data(ttl: Optional[int] = None):
    """
    Decorator for caching signal-related data

    Args:
        ttl: Cache TTL in seconds (uses config default if None)

    Usage:
        @cache_signal_data(ttl=300)
        async def get_signal_analysis(self, signal_id: int, timeframe: str):
            # Signal analysis logic
            return analysis_data
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate signal-specific cache key
            cache_key = generate_cache_key("signal", func.__name__, *args[1:], **kwargs)

            # Try cache first
            cached_result = await cache_service.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Signal data cache hit: {func.__name__}")
                return cached_result

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result if not None
            if result is not None:
                await cache_service.set(cache_key, result, ttl or settings.CACHE_TTL_MEDIUM)
                logger.debug(f"Signal data cached: {func.__name__}")

            return result
        return wrapper
    return decorator


def cache_market_data(ttl: Optional[int] = None):
    """
    Decorator for caching market data

    Args:
        ttl: Cache TTL in seconds (uses config default if None)

    Usage:
        @cache_market_data(ttl=60)
        async def get_market_price(self, symbol: str, timeframe: str):
            # Market data retrieval logic
            return price_data
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract symbol and timeframe
            symbol = kwargs.get('symbol') or (args[1] if len(args) > 1 else None)
            timeframe = kwargs.get('timeframe') or (args[2] if len(args) > 2 else None)

            if not symbol or not timeframe:
                return await func(*args, **kwargs)

            # Generate market data cache key
            cache_key = generate_cache_key("market", symbol, timeframe, func.__name__, **kwargs)

            # Try cache first
            cached_result = await cache_service.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Market data cache hit: {symbol}/{timeframe}")
                return cached_result

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result if not None
            if result is not None:
                await cache_service.set(cache_key, result, ttl or settings.CACHE_TTL_SHORT)
                logger.debug(f"Market data cached: {symbol}/{timeframe}")

            return result
        return wrapper
    return decorator


class CacheInvalidator:
    """Utility class for cache invalidation strategies"""

    @staticmethod
    async def invalidate_user_cache(user_id: Union[int, str]) -> bool:
        """Invalidate all cache entries for a specific user"""
        return await cache_service.invalidate_user_cache(user_id)

    @staticmethod
    async def invalidate_signal_cache(signal_id: Optional[Union[int, str]] = None) -> bool:
        """Invalidate signal cache entries"""
        pattern = f"*{signal_id}*" if signal_id else None
        return await cache_service.invalidate_signals_cache(pattern)

    @staticmethod
    async def invalidate_market_cache(symbol: Optional[str] = None, timeframe: Optional[str] = None) -> bool:
        """Invalidate market data cache entries"""
        return await cache_service.invalidate_market_data_cache(symbol, timeframe)

    @staticmethod
    async def invalidate_api_cache(endpoint: Optional[str] = None) -> bool:
        """Invalidate API response cache entries"""
        return await cache_service.invalidate_api_cache(endpoint)

    @staticmethod
    async def invalidate_all_cache() -> Dict[str, int]:
        """Invalidate all cache entries and return counts"""
        results = {}

        # Invalidate each cache type
        results['signals'] = await cache_service.invalidate_signals_cache()
        results['users'] = await cache_service.invalidate_pattern(f"{settings.CACHE_PREFIX_USERS}*")
        results['market_data'] = await cache_service.invalidate_market_data_cache()
        results['api'] = await cache_service.invalidate_api_cache()

        total = sum(results.values())
        results['total'] = total

        logger.info(f"Invalidated all cache entries: {total} total")
        return results


class CacheWarmer:
    """Utility class for cache warming strategies"""

    @staticmethod
    async def warm_user_data(user_ids: List[Union[int, str]], data_provider: Callable) -> Dict[str, Any]:
        """
        Warm up user data cache

        Args:
            user_ids: List of user IDs to warm up
            data_provider: Async function that provides user data for a user ID

        Returns:
            Dict: Warmup results
        """
        warmup_functions = []
        for user_id in user_ids:
            async def get_user_data(uid=user_id):
                data = await data_provider(uid)
                if data:
                    await cache_service.cache_user_data(uid, data)
                return data

            warmup_functions.append(get_user_data)

        return await cache_service.warm_cache(warmup_functions)

    @staticmethod
    async def warm_signals_data(symbols: List[str], data_provider: Callable) -> Dict[str, Any]:
        """
        Warm up signals data cache

        Args:
            symbols: List of symbols to warm up
            data_provider: Async function that provides signals data for a symbol

        Returns:
            Dict: Warmup results
        """
        warmup_functions = []
        for symbol in symbols:
            async def get_symbol_data(sym=symbol):
                data = await data_provider(sym)
                if data:
                    await cache_service.cache_signals(f"latest_{sym}", data)
                return data

            warmup_functions.append(get_symbol_data)

        return await cache_service.warm_cache(warmup_functions)

    @staticmethod
    async def warm_market_data(symbols: List[str], timeframes: List[str], data_provider: Callable) -> Dict[str, Any]:
        """
        Warm up market data cache

        Args:
            symbols: List of symbols to warm up
            timeframes: List of timeframes to warm up
            data_provider: Async function that provides market data for symbol/timeframe

        Returns:
            Dict: Warmup results
        """
        warmup_functions = []
        for symbol in symbols:
            for timeframe in timeframes:
                async def get_market_data(sym=symbol, tf=timeframe):
                    data = await data_provider(sym, tf)
                    if data:
                        await cache_service.cache_market_data(sym, tf, data)
                    return data

                warmup_functions.append(get_market_data)

        return await cache_service.warm_cache(warmup_functions)


def create_cache_manager() -> CacheService:
    """
    Create a new cache service instance with current configuration

    Returns:
        CacheService: Configured cache service instance
    """
    from app.services.cache_service import CacheConfig
    return CacheService(CacheConfig(
        redis_url=settings.REDIS_URL,
        redis_password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
        redis_db=settings.REDIS_DB,
        max_connections=settings.REDIS_POOL_SIZE,
        timeout=settings.REDIS_TIMEOUT,
        retry_on_timeout=settings.REDIS_RETRY_ON_TIMEOUT,
        fallback_enabled=True,
        metrics_enabled=True
    ))