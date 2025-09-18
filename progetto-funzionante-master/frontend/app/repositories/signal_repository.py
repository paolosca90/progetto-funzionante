from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import desc, and_, func
from datetime import datetime, timedelta

from models import Signal, SignalExecution, SignalStatusEnum, SignalTypeEnum
from schemas import SignalCreate
from .base_repository import BaseRepository
from app.core.pagination import PaginationService, PaginationParams, PaginatedResponse, paginate_signals


class SignalRepository(BaseRepository[Signal, SignalCreate, dict]):
    """Repository for Signal model operations with optimized pagination."""

    def __init__(self, db: Session):
        super().__init__(Signal, db)

    def _add_eager_loading(self, query):
        """Add optimized eager loading for Signal queries."""
        return query.options(
            joinedload(Signal.creator),
            selectinload(Signal.executions)
        )

    def get_latest_signals(self, limit: int = 10) -> List[Signal]:
        """Get latest active signals with eager loading."""
        return self.db.query(Signal).options(
            joinedload(Signal.creator),
            selectinload(Signal.executions)
        ).filter(
            Signal.is_active == True,
            Signal.status == SignalStatusEnum.ACTIVE
        ).order_by(desc(Signal.created_at)).limit(limit).all()

    def get_latest_signals_paginated(
        self,
        page: int = 1,
        per_page: int = 20,
        use_cursor: bool = False
    ) -> PaginatedResponse[Signal]:
        """Get latest active signals with pagination."""
        query = self.db.query(Signal).options(
            joinedload(Signal.creator),
            selectinload(Signal.executions)
        ).filter(
            Signal.is_active == True,
            Signal.status == SignalStatusEnum.ACTIVE
        ).order_by(desc(Signal.created_at))

        return paginate_signals(query, page, per_page, use_cursor)

    def get_signals_by_symbol(self, symbol: str, limit: int = 10) -> List[Signal]:
        """Get signals for a specific symbol with eager loading."""
        return self.db.query(Signal).options(
            joinedload(Signal.creator),
            selectinload(Signal.executions)
        ).filter(
            Signal.symbol == symbol,
            Signal.is_active == True
        ).order_by(desc(Signal.created_at)).limit(limit).all()

    def get_signals_by_symbol_paginated(
        self,
        symbol: str,
        page: int = 1,
        per_page: int = 20,
        use_cursor: bool = False
    ) -> PaginatedResponse[Signal]:
        """Get signals for a specific symbol with pagination."""
        query = self.db.query(Signal).options(
            joinedload(Signal.creator),
            selectinload(Signal.executions)
        ).filter(
            Signal.symbol == symbol,
            Signal.is_active == True
        ).order_by(desc(Signal.created_at))

        return paginate_signals(query, page, per_page, use_cursor)

    def get_signals_by_user(self, user_id: int, limit: int = 100) -> List[Signal]:
        """Get signals created by a specific user with eager loading."""
        return self.db.query(Signal).options(
            joinedload(Signal.creator),
            selectinload(Signal.executions)
        ).filter(
            Signal.creator_id == user_id
        ).order_by(desc(Signal.created_at)).limit(limit).all()

    def get_signals_by_user_paginated(
        self,
        user_id: int,
        page: int = 1,
        per_page: int = 20,
        use_cursor: bool = False
    ) -> PaginatedResponse[Signal]:
        """Get signals created by a specific user with pagination."""
        query = self.db.query(Signal).options(
            joinedload(Signal.creator),
            selectinload(Signal.executions)
        ).filter(
            Signal.creator_id == user_id
        ).order_by(desc(Signal.created_at))

        return paginate_signals(query, page, per_page, use_cursor)

    def get_public_signals(self, limit: int = 100) -> List[Signal]:
        """Get public signals with eager loading."""
        return self.db.query(Signal).options(
            joinedload(Signal.creator),
            selectinload(Signal.executions)
        ).filter(
            Signal.is_public == True,
            Signal.is_active == True
        ).order_by(desc(Signal.created_at)).limit(limit).all()

    def get_top_signals(self, limit: int = 10) -> List[Signal]:
        """Get top performing signals based on reliability with eager loading."""
        return self.db.query(Signal).options(
            joinedload(Signal.creator),
            selectinload(Signal.executions)
        ).filter(
            Signal.is_active == True,
            Signal.status == SignalStatusEnum.ACTIVE
        ).order_by(desc(Signal.reliability)).limit(limit).all()

    def get_signals_by_source(self, source: str, limit: int = 100) -> List[Signal]:
        """Get signals by source (OANDA_AI, MANUAL, API)."""
        return self.db.query(Signal).filter(
            Signal.source == source,
            Signal.is_active == True
        ).order_by(desc(Signal.created_at)).limit(limit).all()

    def get_signals_by_risk_level(self, risk_level: str, limit: int = 100) -> List[Signal]:
        """Get signals by risk level."""
        return self.db.query(Signal).filter(
            Signal.risk_level == risk_level,
            Signal.is_active == True
        ).order_by(desc(Signal.created_at)).limit(limit).all()

    def get_signals_by_type(self, signal_type: SignalTypeEnum, limit: int = 100) -> List[Signal]:
        """Get signals by type (BUY, SELL, HOLD)."""
        return self.db.query(Signal).filter(
            Signal.signal_type == signal_type,
            Signal.is_active == True
        ).order_by(desc(Signal.created_at)).limit(limit).all()

    def get_signals_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 1000
    ) -> List[Signal]:
        """Get signals within a date range."""
        return self.db.query(Signal).filter(
            Signal.created_at >= start_date,
            Signal.created_at <= end_date
        ).order_by(desc(Signal.created_at)).limit(limit).all()

    def get_expired_signals(self) -> List[Signal]:
        """Get signals that have expired."""
        current_time = datetime.utcnow()
        return self.db.query(Signal).filter(
            Signal.expires_at <= current_time,
            Signal.status == SignalStatusEnum.ACTIVE
        ).all()

    def close_signal(self, signal: Signal) -> Signal:
        """Close an active signal."""
        signal.status = SignalStatusEnum.CLOSED
        self.db.commit()
        self.db.refresh(signal)
        return signal

    def cancel_signal(self, signal: Signal) -> Signal:
        """Cancel an active signal."""
        signal.status = SignalStatusEnum.CANCELLED
        self.db.commit()
        self.db.refresh(signal)
        return signal

    def update_reliability(self, signal: Signal, reliability: float) -> Signal:
        """Update signal reliability score."""
        signal.reliability = reliability
        self.db.commit()
        self.db.refresh(signal)
        return signal

    def get_signal_statistics(self) -> Dict[str, Any]:
        """Get overall signal statistics."""
        total_signals = self.db.query(Signal).count()
        active_signals = self.db.query(Signal).filter(Signal.status == SignalStatusEnum.ACTIVE).count()
        closed_signals = self.db.query(Signal).filter(Signal.status == SignalStatusEnum.CLOSED).count()

        avg_reliability = self.db.query(func.avg(Signal.reliability)).scalar() or 0.0

        # Get signals by type
        buy_signals = self.db.query(Signal).filter(Signal.signal_type == SignalTypeEnum.BUY).count()
        sell_signals = self.db.query(Signal).filter(Signal.signal_type == SignalTypeEnum.SELL).count()
        hold_signals = self.db.query(Signal).filter(Signal.signal_type == SignalTypeEnum.HOLD).count()

        return {
            "total_signals": total_signals,
            "active_signals": active_signals,
            "closed_signals": closed_signals,
            "average_reliability": round(avg_reliability, 2),
            "buy_signals": buy_signals,
            "sell_signals": sell_signals,
            "hold_signals": hold_signals
        }

    def get_signals_by_timeframe(self, timeframe: str, limit: int = 100) -> List[Signal]:
        """Get signals by analysis timeframe."""
        return self.db.query(Signal).filter(
            Signal.timeframe == timeframe,
            Signal.is_active == True
        ).order_by(desc(Signal.created_at)).limit(limit).all()

    def get_recent_signals_count(self, hours: int = 24) -> int:
        """Get count of signals created in the last N hours."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return self.db.query(Signal).filter(
            Signal.created_at >= cutoff_time
        ).count()

    def search_signals(self, search_term: str, limit: int = 100) -> List[Signal]:
        """Search signals by symbol or AI analysis content with eager loading."""
        search_pattern = f"%{search_term}%"
        return self.db.query(Signal).options(
            joinedload(Signal.creator),
            selectinload(Signal.executions)
        ).filter(
            (Signal.symbol.ilike(search_pattern)) |
            (Signal.ai_analysis.ilike(search_pattern))
        ).order_by(desc(Signal.created_at)).limit(limit).all()

    def search_signals_paginated(
        self,
        search_term: str,
        page: int = 1,
        per_page: int = 20,
        use_cursor: bool = False
    ) -> PaginatedResponse[Signal]:
        """Search signals with pagination and optimized loading."""
        search_pattern = f"%{search_term}%"
        query = self.db.query(Signal).options(
            joinedload(Signal.creator),
            selectinload(Signal.executions)
        ).filter(
            (Signal.symbol.ilike(search_pattern)) |
            (Signal.ai_analysis.ilike(search_pattern))
        ).order_by(desc(Signal.created_at))

        return paginate_signals(query, page, per_page, use_cursor)

    def get_high_confidence_signals(self, min_confidence: float = 0.8, limit: int = 100) -> List[Signal]:
        """Get signals with high confidence scores."""
        return self.db.query(Signal).filter(
            Signal.confidence_score >= min_confidence,
            Signal.is_active == True,
            Signal.status == SignalStatusEnum.ACTIVE
        ).order_by(desc(Signal.confidence_score)).limit(limit).all()

    def get_signals_with_executions(self, limit: int = 100) -> List[Signal]:
        """Get signals that have executions with optimized loading."""
        return self.db.query(Signal).options(
            joinedload(Signal.creator),
            selectinload(Signal.executions).selectinload(SignalExecution.user)
        ).join(SignalExecution).order_by(
            desc(Signal.created_at)
        ).limit(limit).all()

    def bulk_close_expired_signals(self) -> int:
        """Close all expired signals and return count."""
        current_time = datetime.utcnow()
        expired_signals = self.db.query(Signal).filter(
            Signal.expires_at <= current_time,
            Signal.status == SignalStatusEnum.ACTIVE
        )

        count = expired_signals.count()
        expired_signals.update({Signal.status: SignalStatusEnum.CLOSED})
        self.db.commit()

        return count

    def get_signals_with_advanced_pagination(
        self,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        per_page: int = 20,
        order_by: str = "created_at",
        order_direction: str = "desc",
        use_cursor: bool = False
    ) -> PaginatedResponse[Signal]:
        """Get signals with advanced filtering and pagination options."""
        query = self.db.query(Signal).options(
            joinedload(Signal.creator),
            selectinload(Signal.executions)
        )

        # Apply filters
        if filters:
            if filters.get("is_active") is not None:
                query = query.filter(Signal.is_active == filters["is_active"])
            if filters.get("status"):
                query = query.filter(Signal.status == filters["status"])
            if filters.get("symbol"):
                query = query.filter(Signal.symbol == filters["symbol"])
            if filters.get("signal_type"):
                query = query.filter(Signal.signal_type == filters["signal_type"])
            if filters.get("risk_level"):
                query = query.filter(Signal.risk_level == filters["risk_level"])
            if filters.get("source"):
                query = query.filter(Signal.source == filters["source"])
            if filters.get("creator_id"):
                query = query.filter(Signal.creator_id == filters["creator_id"])
            if filters.get("min_confidence"):
                query = query.filter(Signal.confidence_score >= filters["min_confidence"])
            if filters.get("max_confidence"):
                query = query.filter(Signal.confidence_score <= filters["max_confidence"])
            if filters.get("created_after"):
                query = query.filter(Signal.created_at >= filters["created_after"])
            if filters.get("created_before"):
                query = query.filter(Signal.created_at <= filters["created_before"])

        # Apply ordering
        order_column = getattr(Signal, order_by, Signal.created_at)
        if order_direction.lower() == "desc":
            query = query.order_by(desc(order_column))
        else:
            query = query.order_by(order_column)

        # Apply pagination
        pagination_params = PaginationParams(page=page, per_page=per_page)

        if use_cursor and order_by in ["created_at", "id"]:
            return PaginationService.paginate_cursor(
                query, pagination_params, cursor_column=order_by,
                cursor_direction=order_direction
            )
        else:
            return PaginationService.paginate_query(query, pagination_params)

    def stream_all_signals(self, batch_size: int = 1000):
        """Stream all signals in batches for memory-efficient processing."""
        from app.core.pagination import StreamingPagination

        query = self.db.query(Signal).order_by(Signal.id)
        return StreamingPagination.stream_query_results(
            query, batch_size=batch_size, order_by="id"
        )