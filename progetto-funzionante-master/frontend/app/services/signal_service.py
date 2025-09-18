from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging

from models import Signal, User, SignalStatusEnum, SignalTypeEnum
from schemas import SignalCreate, SignalOut, TopSignalsResponse
from app.repositories.signal_repository import SignalRepository
from app.services.cache_service import cache_service

logger = logging.getLogger(__name__)


class SignalService:
    """Service for signal operations with caching support."""

    def __init__(self, db: Session):
        self.db = db
        self.signal_repository = SignalRepository(db)
        self.cache_enabled = True  # Enable/disable caching

    def create_signal(self, signal_create: SignalCreate, creator_id: int) -> Signal:
        """
        Create a new trading signal.

        Args:
            signal_create: Signal creation data
            creator_id: ID of the user creating the signal

        Returns:
            Created signal object
        """
        # Convert schema to dict and add creator_id
        signal_data = signal_create.dict()
        signal_data["creator_id"] = creator_id

        # Set default expiration if not provided (24 hours)
        if not signal_data.get("expires_at"):
            signal_data["expires_at"] = datetime.utcnow() + timedelta(hours=24)

        # Create signal
        signal = self.signal_repository.create(signal_data)

        # Invalidate relevant caches when new signal is created
        if self.cache_enabled:
            await cache_service.invalidate_signals_cache()
            logger.debug("Invalidated signals cache after signal creation")

        return signal

    async def get_latest_signals(self, limit: int = 10) -> List[Signal]:
        """Get latest active signals with caching."""
        if self.cache_enabled:
            cache_key = f"latest_{limit}"
            cached_signals = await cache_service.get_cached_signals(cache_key)
            if cached_signals:
                logger.debug(f"Cache hit for latest signals (limit={limit})")
                return [Signal(**signal_data) for signal_data in cached_signals]

        # Get from database
        signals = self.signal_repository.get_latest_signals(limit)

        # Cache the results (5 minute TTL for latest signals)
        if self.cache_enabled and signals:
            signals_data = [self._signal_to_dict(signal) for signal in signals]
            await cache_service.cache_signals(f"latest_{limit}", signals_data, ttl=300)
            logger.debug(f"Cached latest signals (limit={limit})")

        return signals

    async def get_signals_by_symbol(self, symbol: str, limit: int = 10) -> List[Signal]:
        """Get signals for a specific trading symbol with caching."""
        if self.cache_enabled:
            cache_key = f"symbol_{symbol}_{limit}"
            cached_signals = await cache_service.get_cached_signals(cache_key)
            if cached_signals:
                logger.debug(f"Cache hit for signals by symbol {symbol} (limit={limit})")
                return [Signal(**signal_data) for signal_data in cached_signals]

        # Get from database
        signals = self.signal_repository.get_signals_by_symbol(symbol, limit)

        # Cache the results (10 minute TTL for symbol-specific signals)
        if self.cache_enabled and signals:
            signals_data = [self._signal_to_dict(signal) for signal in signals]
            await cache_service.cache_signals(f"symbol_{symbol}_{limit}", signals_data, ttl=600)
            logger.debug(f"Cached signals for symbol {symbol} (limit={limit})")

        return signals

    def get_user_signals(self, user_id: int, limit: int = 100) -> List[Signal]:
        """Get signals created by a specific user."""
        return self.signal_repository.get_signals_by_user(user_id, limit)

    def get_public_signals(self, limit: int = 100) -> List[Signal]:
        """Get all public signals."""
        return self.signal_repository.get_public_signals(limit)

    async def get_top_signals(self, limit: int = 10) -> TopSignalsResponse:
        """
        Get top performing signals with caching.

        Returns:
            TopSignalsResponse with signals and statistics
        """
        # Try to get cached statistics first
        stats = None
        if self.cache_enabled:
            stats = await cache_service.get_cached_signal_statistics()

        if not stats:
            stats = self.signal_repository.get_signal_statistics()
            if self.cache_enabled:
                await cache_service.cache_signal_statistics(stats, ttl=600)  # 10 minute TTL

        # Get top signals with caching
        if self.cache_enabled:
            cache_key = f"top_{limit}"
            cached_signals = await cache_service.get_cached_signals(cache_key)
            if cached_signals:
                signals = [Signal(**signal_data) for signal_data in cached_signals]
            else:
                signals = self.signal_repository.get_top_signals(limit)
                if signals:
                    signals_data = [self._signal_to_dict(signal) for signal in signals]
                    await cache_service.cache_signals(f"top_{limit}", signals_data, ttl=600)
        else:
            signals = self.signal_repository.get_top_signals(limit)

        return TopSignalsResponse(
            signals=[SignalOut.from_orm(signal) for signal in signals],
            total_count=stats["total_signals"],
            average_reliability=stats["average_reliability"]
        )

    def get_signals_by_source(self, source: str, limit: int = 100) -> List[Signal]:
        """Get signals by source (OANDA_AI, MANUAL, API)."""
        return self.signal_repository.get_signals_by_source(source, limit)

    def get_signals_by_risk_level(self, risk_level: str, limit: int = 100) -> List[Signal]:
        """Get signals by risk level (LOW, MEDIUM, HIGH)."""
        return self.signal_repository.get_signals_by_risk_level(risk_level, limit)

    def get_signals_by_type(self, signal_type: str, limit: int = 100) -> List[Signal]:
        """Get signals by type (BUY, SELL, HOLD)."""
        try:
            signal_type_enum = SignalTypeEnum(signal_type.upper())
            return self.signal_repository.get_signals_by_type(signal_type_enum, limit)
        except ValueError:
            return []

    def get_signal_by_id(self, signal_id: int) -> Optional[Signal]:
        """Get a specific signal by ID."""
        return self.signal_repository.get(signal_id)

    def close_signal(self, signal_id: int, user: User) -> Optional[Signal]:
        """
        Close a signal.

        Args:
            signal_id: Signal ID to close
            user: User performing the action

        Returns:
            Updated signal if successful
        """
        signal = self.signal_repository.get(signal_id)
        if not signal:
            return None

        # Check permissions - only creator or admin can close
        if signal.creator_id != user.id and not user.is_admin:
            return None

        # Close signal
        updated_signal = self.signal_repository.close_signal(signal)

        # Invalidate relevant caches
        if self.cache_enabled and updated_signal:
            await cache_service.invalidate_signals_cache()
            logger.debug("Invalidated signals cache after signal closure")

        return updated_signal

    def cancel_signal(self, signal_id: int, user: User) -> Optional[Signal]:
        """
        Cancel a signal.

        Args:
            signal_id: Signal ID to cancel
            user: User performing the action

        Returns:
            Updated signal if successful
        """
        signal = self.signal_repository.get(signal_id)
        if not signal:
            return None

        # Check permissions - only creator or admin can cancel
        if signal.creator_id != user.id and not user.is_admin:
            return None

        # Cancel signal
        updated_signal = self.signal_repository.cancel_signal(signal)

        # Invalidate relevant caches
        if self.cache_enabled and updated_signal:
            await cache_service.invalidate_signals_cache()
            logger.debug("Invalidated signals cache after signal cancellation")

        return updated_signal

    def update_signal_reliability(self, signal_id: int, reliability: float, user: User) -> Optional[Signal]:
        """
        Update signal reliability score.

        Args:
            signal_id: Signal ID to update
            reliability: New reliability score (0-100)
            user: User performing the action

        Returns:
            Updated signal if successful
        """
        signal = self.signal_repository.get(signal_id)
        if not signal:
            return None

        # Check permissions - only creator or admin can update
        if signal.creator_id != user.id and not user.is_admin:
            return None

        # Validate reliability score
        if not 0 <= reliability <= 100:
            return None

        # Update reliability
        updated_signal = self.signal_repository.update_reliability(signal, reliability)

        # Invalidate relevant caches
        if self.cache_enabled and updated_signal:
            await cache_service.invalidate_signals_cache()
            logger.debug("Invalidated signals cache after reliability update")

        return updated_signal

    async def get_signal_statistics(self) -> Dict[str, Any]:
        """Get overall signal statistics with caching."""
        if self.cache_enabled:
            cached_stats = await cache_service.get_cached_signal_statistics()
            if cached_stats:
                logger.debug("Cache hit for signal statistics")
                return cached_stats

        # Get from database
        stats = self.signal_repository.get_signal_statistics()

        # Cache the results (10 minute TTL)
        if self.cache_enabled:
            await cache_service.cache_signal_statistics(stats, ttl=600)
            logger.debug("Cached signal statistics")

        return stats

    def search_signals(self, search_term: str, limit: int = 100) -> List[Signal]:
        """Search signals by symbol or content."""
        return self.signal_repository.search_signals(search_term, limit)

    def get_high_confidence_signals(self, min_confidence: float = 0.8, limit: int = 100) -> List[Signal]:
        """Get signals with high confidence scores."""
        return self.signal_repository.get_high_confidence_signals(min_confidence, limit)

    def get_signals_by_timeframe(self, timeframe: str, limit: int = 100) -> List[Signal]:
        """Get signals by analysis timeframe."""
        return self.signal_repository.get_signals_by_timeframe(timeframe, limit)

    def get_recent_signals_count(self, hours: int = 24) -> int:
        """Get count of signals created in the last N hours."""
        return self.signal_repository.get_recent_signals_count(hours)

    def cleanup_expired_signals(self) -> int:
        """
        Close all expired signals.

        Returns:
            Number of signals that were closed
        """
        # Close expired signals
        count = self.signal_repository.bulk_close_expired_signals()

        # Invalidate caches if signals were closed
        if self.cache_enabled and count > 0:
            await cache_service.invalidate_signals_cache()
            logger.debug(f"Invalidated signals cache after closing {count} expired signals")

        return count

    def get_signals_with_executions(self, limit: int = 100) -> List[Signal]:
        """Get signals that have been executed by users."""
        return self.signal_repository.get_signals_with_executions(limit)

    def get_signals_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 1000
    ) -> List[Signal]:
        """Get signals within a specific date range."""
        return self.signal_repository.get_signals_by_date_range(start_date, end_date, limit)

    def generate_signal_report(self, days: int = 30) -> Dict[str, Any]:
        """
        Generate a comprehensive signal report for the last N days.

        Args:
            days: Number of days to include in the report

        Returns:
            Dictionary containing signal analytics
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        signals = self.get_signals_by_date_range(start_date, end_date)
        stats = self.get_signal_statistics()

        # Calculate performance metrics
        buy_signals = len([s for s in signals if s.signal_type == SignalTypeEnum.BUY])
        sell_signals = len([s for s in signals if s.signal_type == SignalTypeEnum.SELL])
        hold_signals = len([s for s in signals if s.signal_type == SignalTypeEnum.HOLD])

        # Calculate average confidence and reliability
        total_signals = len(signals)
        avg_confidence = sum([s.confidence_score or 0 for s in signals]) / total_signals if total_signals > 0 else 0
        avg_reliability = sum([s.reliability or 0 for s in signals]) / total_signals if total_signals > 0 else 0

        # Group by symbol
        symbol_counts = {}
        for signal in signals:
            symbol_counts[signal.symbol] = symbol_counts.get(signal.symbol, 0) + 1

        # Group by source
        source_counts = {}
        for signal in signals:
            source_counts[signal.source] = source_counts.get(signal.source, 0) + 1

        return {
            "period_days": days,
            "total_signals": total_signals,
            "buy_signals": buy_signals,
            "sell_signals": sell_signals,
            "hold_signals": hold_signals,
            "average_confidence": round(avg_confidence, 2),
            "average_reliability": round(avg_reliability, 2),
            "signals_by_symbol": symbol_counts,
            "signals_by_source": source_counts,
            "overall_stats": stats
        }

    def _signal_to_dict(self, signal: Signal) -> Dict[str, Any]:
        """Convert Signal object to dictionary for caching."""
        return {
            "id": signal.id,
            "symbol": signal.symbol,
            "signal_type": signal.signal_type.value if signal.signal_type else None,
            "entry_price": signal.entry_price,
            "stop_loss": signal.stop_loss,
            "take_profit": signal.take_profit,
            "reliability": signal.reliability,
            "status": signal.status.value if signal.status else None,
            "ai_analysis": signal.ai_analysis,
            "confidence_score": signal.confidence_score,
            "risk_level": signal.risk_level,
            "is_public": signal.is_public,
            "is_active": signal.is_active,
            "created_at": signal.created_at.isoformat() if signal.created_at else None,
            "expires_at": signal.expires_at.isoformat() if signal.expires_at else None,
            "source": signal.source,
            "timeframe": signal.timeframe,
            "risk_reward_ratio": signal.risk_reward_ratio,
            "position_size_suggestion": signal.position_size_suggestion,
            "spread": signal.spread,
            "volatility": signal.volatility,
            "technical_score": signal.technical_score,
            "rsi": signal.rsi,
            "macd_signal": signal.macd_signal,
            "market_session": signal.market_session,
            "creator_id": signal.creator_id
        }