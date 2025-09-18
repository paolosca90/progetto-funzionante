"""
Comprehensive examples of cache usage throughout the application.

This file demonstrates how to integrate the caching system into various parts
of the application including services, repositories, and API endpoints.
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from app.services.cache_service import cache_service
from app.utils.cache_utils import (
    cache_database_query,
    cache_api_response,
    cache_user_data,
    cache_signal_data,
    cache_market_data,
    CacheInvalidator,
    CacheWarmer
)
from app.core.config import settings


# Example: Enhanced User Service with Caching
class CachedUserService:
    """Example user service with comprehensive caching"""

    @cache_user_data(ttl=1800)  # 30 minutes
    async def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user by ID with automatic caching.

        The cache key will be automatically generated as:
        ai_trading:user:get_user_by_id:{user_id}
        """
        # This would normally query the database
        # Simulating database call
        await asyncio.sleep(0.1)  # Simulate DB latency

        # Return mock user data
        return {
            "id": user_id,
            "username": f"user_{user_id}",
            "email": f"user_{user_id}@example.com",
            "is_active": True,
            "created_at": datetime.utcnow().isoformat()
        }

    @cache_user_data(ttl=300)  # 5 minutes for frequently changing data
    async def get_user_stats(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user statistics with caching"""
        # Simulate complex calculation
        await asyncio.sleep(0.05)

        return {
            "user_id": user_id,
            "total_signals": 150,
            "active_signals": 12,
            "success_rate": 78.5,
            "last_activity": datetime.utcnow().isoformat()
        }

    async def update_user_profile(self, user_id: int, profile_data: Dict) -> bool:
        """
        Update user profile and invalidate relevant cache

        Returns:
            bool: Success status
        """
        try:
            # Simulate database update
            await asyncio.sleep(0.1)

            # Invalidate user cache entries
            await CacheInvalidator.invalidate_user_cache(user_id)

            logger.info(f"Updated user {user_id} profile and invalidated cache")
            return True

        except Exception as e:
            logger.error(f"Failed to update user {user_id}: {e}")
            return False


# Example: Enhanced Signal Service with Caching
class CachedSignalService:
    """Example signal service with comprehensive caching"""

    @cache_signal_data(ttl=300)  # 5 minutes
    async def get_signal_by_id(self, signal_id: int) -> Optional[Dict[str, Any]]:
        """Get signal by ID with caching"""
        # Simulate database query
        await asyncio.sleep(0.05)

        return {
            "id": signal_id,
            "symbol": "EUR_USD",
            "signal_type": "BUY",
            "entry_price": 1.0850,
            "confidence_score": 85.2,
            "created_at": datetime.utcnow().isoformat()
        }

    @cache_signal_data(ttl=60)  # 1 minute for real-time data
    async def get_latest_signals(self, symbol: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get latest signals for a symbol with caching"""
        # Simulate database query
        await asyncio.sleep(0.03)

        # Generate mock signals
        signals = []
        for i in range(min(limit, 5)):
            signals.append({
                "id": f"signal_{i}",
                "symbol": symbol,
                "signal_type": "BUY" if i % 2 == 0 else "SELL",
                "entry_price": 1.0850 + (i * 0.001),
                "confidence_score": 80.0 + (i * 2),
                "created_at": datetime.utcnow().isoformat()
            })

        return signals

    async def create_signal(self, signal_data: Dict) -> Dict[str, Any]:
        """Create new signal and invalidate relevant cache"""
        try:
            # Simulate database insert
            await asyncio.sleep(0.05)

            symbol = signal_data.get("symbol", "EUR_USD")

            # Invalidate signal cache for this symbol
            await CacheInvalidator.invalidate_signal_cache(symbol)

            logger.info(f"Created new signal for {symbol} and invalidated cache")
            return {"id": "new_signal_123", **signal_data}

        except Exception as e:
            logger.error(f"Failed to create signal: {e}")
            raise


# Example: Enhanced OANDA Service with Caching
class CachedOANDAService:
    """Example OANDA service with API response caching"""

    @cache_api_response(ttl=60, ignore_params=['request_timestamp'])
    async def get_current_price(self, symbol: str, request_timestamp: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Get current price with API response caching.

        The request_timestamp parameter is ignored for cache key generation
        to ensure consistent caching regardless of when the request is made.
        """
        # Simulate API call
        await asyncio.sleep(0.2)  # Simulate network latency

        return {
            "symbol": symbol,
            "price": 1.0850,
            "timestamp": datetime.utcnow().isoformat(),
            "bid": 1.0849,
            "ask": 1.0851
        }

    @cache_market_data(ttl=30)  # 30 seconds for fast-changing market data
    async def get_market_data(self, symbol: str, timeframe: str) -> Dict[str, Any]:
        """Get market data with automatic caching"""
        # Simulate API call
        await asyncio.sleep(0.15)

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "data": [
                {"timestamp": "2024-01-01T00:00:00Z", "open": 1.0850, "high": 1.0860, "low": 1.0840, "close": 1.0855},
                {"timestamp": "2024-01-01T01:00:00Z", "open": 1.0855, "high": 1.0870, "low": 1.0850, "close": 1.0865}
            ]
        }


# Example: Enhanced Repository with Caching
class CachedSignalRepository:
    """Example repository with database query caching"""

    @cache_database_query(ttl=600, key_prefix="signals_by_user")
    async def get_signals_by_user(self, user_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Get signals by user with database query caching"""
        # Simulate database query
        await asyncio.sleep(0.1)

        return [
            {"id": i, "user_id": user_id, "symbol": "EUR_USD", "signal_type": "BUY"}
            for i in range(min(limit, 20))
        ]

    @cache_database_query(ttl=1200, key_prefix="signal_statistics")  # 20 minutes
    async def get_signal_statistics(self) -> Dict[str, Any]:
        """Get signal statistics with database query caching"""
        # Simulate complex aggregation query
        await asyncio.sleep(0.2)

        return {
            "total_signals": 1250,
            "active_signals": 45,
            "success_rate": 76.8,
            "average_confidence": 82.3,
            "top_symbols": ["EUR_USD", "GBP_USD", "USDJPY"]
        }


# Example: Cache Warming Strategies
class CacheWarmingExample:
    """Example cache warming strategies"""

    async def warm_user_data(self) -> int:
        """Warm up user data cache for active users"""
        user_service = CachedUserService()

        # Get active user IDs (would normally come from database)
        active_user_ids = [1, 2, 3, 4, 5]

        warmed_count = 0
        for user_id in active_user_ids:
            try:
                # Warm user profile
                await user_service.get_user_by_id(user_id)
                # Warm user stats
                await user_service.get_user_stats(user_id)
                warmed_count += 1

                logger.info(f"Warmed cache for user {user_id}")

            except Exception as e:
                logger.error(f"Failed to warm cache for user {user_id}: {e}")

        return warmed_count

    async def warm_signals_data(self) -> int:
        """Warm up signals data cache"""
        signal_service = CachedSignalService()

        # Warm latest signals for each symbol
        symbols = ["EUR_USD", "GBP_USD", "USDJPY", "AUDUSD", "USDCAD"]
        warmed_count = 0

        for symbol in symbols:
            try:
                await signal_service.get_latest_signals(symbol, limit=10)
                warmed_count += 1
                logger.info(f"Warmed signals cache for {symbol}")

            except Exception as e:
                logger.error(f"Failed to warm signals cache for {symbol}: {e}")

        return warmed_count

    async def warm_market_data(self) -> int:
        """Warm up market data cache"""
        oanda_service = CachedOANDAService()

        # Warm market data for major symbols and timeframes
        symbols = ["EUR_USD", "GBP_USD", "USDJPY"]
        timeframes = ["M1", "M5", "M15", "H1"]
        warmed_count = 0

        for symbol in symbols:
            for timeframe in timeframes:
                try:
                    await oanda_service.get_market_data(symbol, timeframe)
                    warmed_count += 1
                    logger.info(f"Warmed market data cache for {symbol}/{timeframe}")

                except Exception as e:
                    logger.error(f"Failed to warm market data for {symbol}/{timeframe}: {e}")

        return warmed_count


# Example: API Endpoint with Caching
async def cached_api_endpoint_example():
    """Example of how to use caching in API endpoints"""

    user_service = CachedUserService()
    signal_service = CachedSignalService()

    # This will be cached automatically
    user_data = await user_service.get_user_by_id(123)

    # This will also be cached automatically
    signals = await signal_service.get_latest_signals("EUR_USD", limit=5)

    return {
        "user": user_data,
        "signals": signals,
        "timestamp": datetime.utcnow().isoformat()
    }


# Example: Cache Management
async def cache_management_example():
    """Example of cache management operations"""

    # Invalidate specific user cache
    await CacheInvalidator.invalidate_user_cache(123)

    # Invalidate all signal cache
    await CacheInvalidator.invalidate_signal_cache()

    # Invalidate market data for specific symbol
    await CacheInvalidator.invalidate_market_cache("EUR_USD")

    # Invalidate API cache for specific endpoint
    await CacheInvalidator.invalidate_api_cache("/api/signals")

    # Invalidate all cache
    results = await CacheInvalidator.invalidate_all_cache()
    print(f"Invalidated {results['total']} cache entries")

    # Manually warm cache
    cache_warmer = CacheWarmingExample()
    users_warmed = await cache_warmer.warm_user_data()
    signals_warmed = await cache_warmer.warm_signals_data()
    market_warmed = await cache_warmer.warm_market_data()

    print(f"Warmed {users_warmed} users, {signals_warmed} signals, {market_warmed} market data items")


# Example: Performance Comparison
async def performance_comparison_example():
    """Example showing performance benefits of caching"""

    user_service = CachedUserService()

    # First call (cache miss)
    start_time = datetime.utcnow()
    await user_service.get_user_by_id(123)
    first_call_time = (datetime.utcnow() - start_time).total_seconds()

    # Second call (cache hit)
    start_time = datetime.utcnow()
    await user_service.get_user_by_id(123)
    second_call_time = (datetime.utcnow() - start_time).total_seconds()

    print(f"First call (cache miss): {first_call_time:.3f}s")
    print(f"Second call (cache hit): {second_call_time:.3f}s")
    print(f"Speed improvement: {(first_call_time / second_call_time):.1f}x faster")


# Example: Cache Health Check
async def cache_health_check_example():
    """Example of cache health monitoring"""

    # Check cache health
    health = await cache_service.health_check()
    print(f"Cache health: {health['status']}")
    print(f"Connection healthy: {health['connection_healthy']}")
    print(f"Hit rate: {health['metrics']['hit_rate']}%")

    # Get cache metrics
    metrics = cache_service.get_metrics()
    print(f"Total operations: {metrics.total_operations}")
    print(f"Average response time: {metrics.average_response_time * 1000:.2f}ms")

    # Get cache info
    info = await cache_service.get_cache_info()
    if info.get("status") == "connected":
        print(f"Redis version: {info.get('redis_version')}")
        print(f"Used memory: {info.get('used_memory')}")


# Main demonstration function
async def demonstrate_cache_usage():
    """Demonstrate various cache usage patterns"""

    print("=== Cache Usage Demonstration ===")

    print("\n1. Performance Comparison:")
    await performance_comparison_example()

    print("\n2. Cache Management:")
    await cache_management_example()

    print("\n3. Cache Health Check:")
    await cache_health_check_example()

    print("\n4. API Endpoint with Caching:")
    result = await cached_api_endpoint_example()
    print(f"API result: {result}")

    print("\n=== Demonstration Complete ===")


if __name__ == "__main__":
    # Run the demonstration
    asyncio.run(demonstrate_cache_usage())