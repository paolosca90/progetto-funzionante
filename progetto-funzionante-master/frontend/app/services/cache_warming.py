"""
Cache warming service for pre-loading frequently accessed data.

This module provides:
- Automatic cache warming strategies
- Scheduled cache warming tasks
- Performance-optimized warmup procedures
- Cache warmup monitoring and metrics
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass

from app.services.cache_service import cache_service
from app.utils.cache_utils import CacheWarmer
from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class WarmupConfig:
    """Configuration for cache warming strategies"""
    enabled: bool = True
    interval_seconds: int = 300  # 5 minutes
    max_concurrent_warmups: int = 5
    enable_user_warmup: bool = True
    enable_signals_warmup: bool = True
    enable_market_data_warmup: bool = True
    enable_stats_warmup: bool = True


@dataclass
class WarmupResult:
    """Result of a cache warming operation"""
    strategy_name: str
    success: bool
    items_processed: int
    execution_time_seconds: float
    error_message: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class CacheWarmingService:
    """
    Service for managing cache warming strategies and schedules
    """

    def __init__(self, config: WarmupConfig = None):
        self.config = config or WarmupConfig()
        self._warmup_tasks: Dict[str, Callable] = {}
        self._running_tasks: Dict[str, asyncio.Task] = {}
        self._last_warmup_times: Dict[str, datetime] = {}
        self._warmup_metrics: Dict[str, List[WarmupResult]] = {}

    def register_warmup_strategy(self, name: str, strategy: Callable) -> None:
        """
        Register a cache warming strategy

        Args:
            name: Unique name for the strategy
            strategy: Async function that performs the warmup
        """
        self._warmup_tasks[name] = strategy
        logger.info(f"Registered cache warmup strategy: {name}")

    async def warm_all_strategies(self) -> Dict[str, WarmupResult]:
        """
        Execute all registered warmup strategies

        Returns:
            Dict[str, WarmupResult]: Results for each strategy
        """
        if not self.config.enabled:
            logger.info("Cache warming disabled, skipping warmup")
            return {}

        results = {}
        semaphore = asyncio.Semaphore(self.config.max_concurrent_warmups)

        async def warm_strategy(name: str, strategy: Callable) -> tuple[str, WarmupResult]:
            async with semaphore:
                start_time = datetime.utcnow()
                try:
                    logger.info(f"Starting cache warmup strategy: {name}")
                    items_processed = await strategy()
                    execution_time = (datetime.utcnow() - start_time).total_seconds()

                    result = WarmupResult(
                        strategy_name=name,
                        success=True,
                        items_processed=items_processed,
                        execution_time_seconds=execution_time
                    )

                    logger.info(f"Cache warmup completed: {name}, "
                              f"processed {items_processed} items in {execution_time:.2f}s")

                except Exception as e:
                    execution_time = (datetime.utcnow() - start_time).total_seconds()
                    result = WarmupResult(
                        strategy_name=name,
                        success=False,
                        items_processed=0,
                        execution_time_seconds=execution_time,
                        error_message=str(e)
                    )
                    logger.error(f"Cache warmup failed for {name}: {e}")

                return name, result

        # Create tasks for all strategies
        tasks = [
            warm_strategy(name, strategy)
            for name, strategy in self._warmup_tasks.items()
        ]

        # Execute all tasks concurrently with semaphore limit
        strategy_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for result in strategy_results:
            if isinstance(result, Exception):
                logger.error(f"Cache warmup task failed: {result}")
            else:
                name, warmup_result = result
                results[name] = warmup_result
                self._last_warmup_times[name] = warmup_result.timestamp

                # Store metrics
                if name not in self._warmup_metrics:
                    self._warmup_metrics[name] = []
                self._warmup_metrics[name].append(warmup_result)

                # Keep only last 100 results per strategy
                if len(self._warmup_metrics[name]) > 100:
                    self._warmup_metrics[name] = self._warmup_metrics[name][-100:]

        return results

    async def start_scheduled_warming(self) -> None:
        """Start scheduled cache warming tasks"""
        if not self.config.enabled:
            logger.info("Cache warming disabled, not starting scheduled tasks")
            return

        logger.info(f"Starting scheduled cache warming with {self.config.interval_seconds}s interval")

        async def warming_loop():
            while True:
                try:
                    await self.warm_all_strategies()
                    await asyncio.sleep(self.config.interval_seconds)
                except asyncio.CancelledError:
                    logger.info("Cache warming loop cancelled")
                    break
                except Exception as e:
                    logger.error(f"Error in cache warming loop: {e}")
                    await asyncio.sleep(self.config.interval_seconds)

        # Start the warming loop
        task = asyncio.create_task(warming_loop())
        self._running_tasks['scheduled_warming'] = task

    async def stop_scheduled_warming(self) -> None:
        """Stop all scheduled cache warming tasks"""
        for name, task in self._running_tasks.items():
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        self._running_tasks.clear()
        logger.info("Stopped all scheduled cache warming tasks")

    def get_warmup_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get cache warming metrics and statistics

        Returns:
            Dict[str, Dict[str, Any]]: Metrics for each warmup strategy
        """
        metrics = {}
        for name, results in self._warmup_metrics.items():
            if not results:
                continue

            success_count = sum(1 for r in results if r.success)
            total_items = sum(r.items_processed for r in results)
            avg_execution_time = sum(r.execution_time_seconds for r in results) / len(results)
            last_execution = results[-1].timestamp if results else None

            metrics[name] = {
                'total_executions': len(results),
                'success_rate': (success_count / len(results)) * 100,
                'total_items_processed': total_items,
                'average_execution_time_seconds': avg_execution_time,
                'last_execution': last_execution.isoformat() if last_execution else None,
                'last_successful': next(
                    (r.timestamp.isoformat() for r in reversed(results) if r.success),
                    None
                )
            }

        return metrics

    def get_last_warmup_times(self) -> Dict[str, Optional[str]]:
        """Get last warmup execution times"""
        return {
            name: time.isoformat() if time else None
            for name, time in self._last_warmup_times.items()
        }


# Global cache warming service instance
cache_warming_service = CacheWarmingService()


async def warm_user_data_strategy() -> int:
    """
    Strategy for warming up user data cache

    Returns:
        int: Number of users processed
    """
    if not cache_warming_service.config.enable_user_warmup:
        return 0

    try:
        # Import here to avoid circular dependencies
        from app.services.user_service import user_service

        # Get active users (last 30 days)
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        active_users = await user_service.get_active_users_since(cutoff_date)

        if not active_users:
            return 0

        processed_count = 0
        for user in active_users:
            try:
                # Warm user profile
                user_data = await user_service.get_user_by_id(user.id)
                if user_data:
                    await cache_service.cache_user_data(user.id, user_data.dict())
                    processed_count += 1

                # Warm user session data if available
                session_data = await user_service.get_user_session_data(user.id)
                if session_data:
                    await cache_service.cache_user_session(f"user_{user.id}", session_data)

                # Small delay to avoid overwhelming the system
                await asyncio.sleep(0.01)

            except Exception as e:
                logger.warning(f"Failed to warm cache for user {user.id}: {e}")

        logger.info(f"Warmed user data cache for {processed_count} users")
        return processed_count

    except Exception as e:
        logger.error(f"Error in user data warming strategy: {e}")
        raise


async def warm_signals_data_strategy() -> int:
    """
    Strategy for warming up signals data cache

    Returns:
        int: Number of signals processed
    """
    if not cache_warming_service.config.enable_signals_warmup:
        return 0

    try:
        # Import here to avoid circular dependencies
        from app.services.signal_service import signal_service

        # Get latest signals for each symbol
        processed_count = 0
        for symbol in settings.DEFAULT_SYMBOLS:
            try:
                # Get latest signals for this symbol
                latest_signals = await signal_service.get_latest_signals_by_symbol(
                    symbol, limit=10
                )

                if latest_signals:
                    # Cache signals data
                    signals_data = [signal.dict() for signal in latest_signals]
                    await cache_service.cache_signals(f"latest_{symbol}", signals_data)
                    processed_count += len(latest_signals)

                # Small delay to avoid overwhelming the system
                await asyncio.sleep(0.01)

            except Exception as e:
                logger.warning(f"Failed to warm cache for symbol {symbol}: {e}")

        logger.info(f"Warmed signals data cache for {processed_count} signals")
        return processed_count

    except Exception as e:
        logger.error(f"Error in signals data warming strategy: {e}")
        raise


async def warm_market_data_strategy() -> int:
    """
    Strategy for warming up market data cache

    Returns:
        int: Number of market data items processed
    """
    if not cache_warming_service.config.enable_market_data_warmup:
        return 0

    try:
        # Import here to avoid circular dependencies
        from app.services.oanda_service import oanda_service

        processed_count = 0
        timeframes = ['M1', 'M5', 'M15', 'H1', 'H4', 'D1']

        # Warm market data for each symbol and timeframe
        for symbol in settings.DEFAULT_SYMBOLS[:5]:  # Limit to top 5 symbols for performance
            for timeframe in timeframes:
                try:
                    # Get current market data
                    market_data = await oanda_service.get_current_price(symbol)

                    if market_data:
                        # Cache market data with short TTL
                        await cache_service.cache_market_data(symbol, timeframe, market_data)
                        processed_count += 1

                    # Small delay to avoid API rate limits
                    await asyncio.sleep(0.1)

                except Exception as e:
                    logger.warning(f"Failed to warm market cache for {symbol}/{timeframe}: {e}")

        logger.info(f"Warmed market data cache for {processed_count} items")
        return processed_count

    except Exception as e:
        logger.error(f"Error in market data warming strategy: {e}")
        raise


async def warm_statistics_strategy() -> int:
    """
    Strategy for warming up statistics cache

    Returns:
        int: Number of statistics processed (always 1 for this strategy)
    """
    if not cache_warming_service.config.enable_stats_warmup:
        return 0

    try:
        # Import here to avoid circular dependencies
        from app.services.signal_service import signal_service

        # Get and cache signal statistics
        stats = await signal_service.get_signal_statistics()

        if stats:
            await cache_service.cache_signal_statistics(stats.dict())
            logger.info("Warmed signal statistics cache")
            return 1

        return 0

    except Exception as e:
        logger.error(f"Error in statistics warming strategy: {e}")
        raise


# Register default warmup strategies
cache_warming_service.register_warmup_strategy('user_data', warm_user_data_strategy)
cache_warming_service.register_warmup_strategy('signals_data', warm_signals_data_strategy)
cache_warming_service.register_warmup_strategy('market_data', warm_market_data_strategy)
cache_warming_service.register_warmup_strategy('statistics', warm_statistics_strategy)


async def start_cache_warming() -> None:
    """Start cache warming service"""
    await cache_warming_service.start_scheduled_warming()


async def stop_cache_warming() -> None:
    """Stop cache warming service"""
    await cache_warming_service.stop_scheduled_warming()


def get_cache_warming_metrics() -> Dict[str, Dict[str, Any]]:
    """Get cache warming metrics"""
    return cache_warming_service.get_warmup_metrics()