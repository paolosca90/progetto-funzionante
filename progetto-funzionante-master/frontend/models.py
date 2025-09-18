from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, Enum, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models import Signal, SignalExecution, Subscription, OANDAConnection

Base = declarative_base()

class SignalTypeEnum(enum.Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class SignalStatusEnum(enum.Enum):
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"

class User(Base):
    """User model for authentication and user management"""

    __tablename__ = "users"

    # Primary key and basic info
    id: int = Column(Integer, primary_key=True, index=True)
    username: str = Column(String(50), unique=True, index=True, nullable=False)
    email: str = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password: str = Column(String(128), nullable=False)
    full_name: Optional[str] = Column(String(100))

    # Status and subscription
    is_active: bool = Column(Boolean, default=True, index=True)  # Add index for active users query
    is_admin: bool = Column(Boolean, default=False, index=True)  # Add index for admin queries
    created_at: datetime = Column(DateTime, default=func.now(), index=True)  # Add index for date queries
    trial_end: Optional[datetime] = Column(DateTime, index=True)  # Add index for trial expiration queries
    subscription_active: bool = Column(Boolean, default=True, index=True)  # Add index for subscription queries
    last_login: Optional[datetime] = Column(DateTime, index=True)  # Add index for login analytics

    # Password reset functionality
    reset_token: Optional[str] = Column(String(100), index=True)  # Add index for token lookup
    reset_token_expires: Optional[datetime] = Column(DateTime, index=True)  # Add index for token expiration

    # Relationships
    signals: List["Signal"] = relationship("Signal", back_populates="creator")
    executions: List["SignalExecution"] = relationship("SignalExecution", back_populates="user")
    oanda_connection: Optional["OANDAConnection"] = relationship("OANDAConnection", back_populates="user", uselist=False)

    # Composite indexes for common query patterns
    __table_args__ = (
        Index('idx_user_active_subscription', 'is_active', 'subscription_active'),
        Index('idx_user_created_active', 'created_at', 'is_active'),
        Index('idx_user_login_active', 'last_login', 'is_active'),
        Index('idx_user_reset_token_expires', 'reset_token', 'reset_token_expires'),
    )

    def __repr__(self) -> str:
        """String representation of the User"""
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}', is_active={self.is_active})>"

class Signal(Base):
    """Signal model for trading signals with AI analysis"""

    __tablename__ = "signals"

    # Primary key and basic info
    id: int = Column(Integer, primary_key=True, index=True)
    symbol: str = Column(String(20), nullable=False, index=True)
    signal_type: SignalTypeEnum = Column(Enum(SignalTypeEnum), nullable=False, index=True)  # Add index for type queries
    entry_price: float = Column(Float, nullable=False)
    stop_loss: Optional[float] = Column(Float)
    take_profit: Optional[float] = Column(Float)
    reliability: float = Column(Float, default=0.0, index=True)  # Add index for top signals query
    status: SignalStatusEnum = Column(Enum(SignalStatusEnum), default=SignalStatusEnum.ACTIVE, index=True)  # Add index for status queries

    # AI Analysis
    ai_analysis: Optional[str] = Column(Text)
    confidence_score: float = Column(Float, default=0.0, index=True)  # Add index for confidence queries
    risk_level: str = Column(String(20), default="MEDIUM", index=True)  # Add index for risk level queries

    # Meta info
    is_public: bool = Column(Boolean, default=True, index=True)  # Add index for public signals
    is_active: bool = Column(Boolean, default=True, index=True)  # Add index for active signals
    created_at: datetime = Column(DateTime, default=func.now(), index=True)  # Add index for date ordering
    expires_at: Optional[datetime] = Column(DateTime, index=True)  # Add index for expiration queries

    # Data source info
    source: str = Column(String(50), default="OANDA_AI", index=True)  # Add index for source queries

    # OANDA-specific fields
    # oanda_instrument = Column(String(20))  # OANDA format instrument (e.g., EUR_USD)
    timeframe: str = Column(String(10), default="H1", index=True)  # Add index for timeframe queries
    risk_reward_ratio: float = Column(Float, default=0.0)  # Risk/reward ratio
    position_size_suggestion: float = Column(Float, default=0.01)  # Suggested position size
    spread: float = Column(Float, default=0.0)  # Market spread at signal generation
    volatility: float = Column(Float, default=0.0)  # Market volatility (ATR-based)

    # Technical analysis metadata
    technical_score: float = Column(Float, default=0.0, index=True)  # Add index for technical score queries
    rsi: Optional[float] = Column(Float)
    macd_signal: Optional[float] = Column(Float)
    market_session: Optional[str] = Column(String(20), index=True)  # Add index for session queries

    # Foreign keys
    creator_id: int = Column(Integer, ForeignKey("users.id"), index=True)  # Add index for creator queries

    # Relationships
    creator: "User" = relationship("User", back_populates="signals")
    executions: List["SignalExecution"] = relationship("SignalExecution", back_populates="signal")

    # Composite indexes for common query patterns
    __table_args__ = (
        Index('idx_signal_active_status', 'is_active', 'status'),
        Index('idx_signal_symbol_active', 'symbol', 'is_active'),
        Index('idx_signal_created_active', 'created_at', 'is_active'),
        Index('idx_signal_public_active', 'is_public', 'is_active'),
        Index('idx_signal_creator_created', 'creator_id', 'created_at'),
        Index('idx_signal_source_active', 'source', 'is_active'),
        Index('idx_signal_expires_status', 'expires_at', 'status'),
        Index('idx_signal_reliability_active', 'reliability', 'is_active', 'status'),
        Index('idx_signal_confidence_active', 'confidence_score', 'is_active', 'status'),
        Index('idx_signal_timeframe_active', 'timeframe', 'is_active'),
        Index('idx_signal_risk_active', 'risk_level', 'is_active'),
        Index('idx_signal_type_active', 'signal_type', 'is_active'),
    )

    def __repr__(self) -> str:
        """String representation of the Signal"""
        return f"<Signal(id={self.id}, symbol='{self.symbol}', type='{self.signal_type.value}', status='{self.status.value}')>"

class SignalExecution(Base):
    """Signal execution model for tracking signal trades"""

    __tablename__ = "signal_executions"

    # Primary key and foreign keys
    id: int = Column(Integer, primary_key=True, index=True)
    signal_id: int = Column(Integer, ForeignKey("signals.id"), index=True)  # Add index for signal lookups
    user_id: int = Column(Integer, ForeignKey("users.id"), index=True)  # Add index for user lookups

    # Execution details
    execution_price: float = Column(Float, nullable=False)
    quantity: float = Column(Float, default=1.0)
    execution_type: str = Column(String(20), default="MANUAL", index=True)  # Add index for execution type queries
    executed_at: datetime = Column(DateTime, default=func.now(), index=True)  # Add index for date queries

    # P&L tracking
    current_price: Optional[float] = Column(Float)
    unrealized_pnl: float = Column(Float, default=0.0, index=True)  # Add index for P&L analysis
    realized_pnl: Optional[float] = Column(Float, index=True)  # Add index for P&L analysis

    # Relationships
    signal: "Signal" = relationship("Signal", back_populates="executions")
    user: "User" = relationship("User", back_populates="executions")

    # Composite indexes for common query patterns
    __table_args__ = (
        Index('idx_execution_signal_user', 'signal_id', 'user_id'),
        Index('idx_execution_user_executed', 'user_id', 'executed_at'),
        Index('idx_execution_signal_executed', 'signal_id', 'executed_at'),
        Index('idx_execution_type_executed', 'execution_type', 'executed_at'),
    )

    def __repr__(self) -> str:
        """String representation of the SignalExecution"""
        return f"<SignalExecution(id={self.id}, signal_id={self.signal_id}, user_id={self.user_id}, price={self.execution_price})>"


class Subscription(Base):
    """Subscription model for user subscription management"""

    __tablename__ = "subscriptions"

    # Primary key and foreign key
    id: int = Column(Integer, primary_key=True, index=True)
    user_id: int = Column(Integer, ForeignKey("users.id"), index=True)  # Add index for user lookups

    # Subscription details
    plan_name: str = Column(String(50), default="TRIAL", index=True)  # Add index for plan queries
    status: str = Column(String(20), default="ACTIVE", index=True)  # Add index for status queries
    is_active: bool = Column(Boolean, default=True, index=True)  # Add index for active subscription queries
    start_date: datetime = Column(DateTime, default=func.now(), index=True)  # Add index for date queries
    end_date: Optional[datetime] = Column(DateTime, index=True)  # Add index for expiration queries
    payment_status: str = Column(String(20), default="PENDING", index=True)  # Add index for payment queries
    last_payment_date: Optional[datetime] = Column(DateTime, index=True)  # Add index for payment analytics

    created_at: datetime = Column(DateTime, default=func.now(), index=True)  # Add index for date queries

    # Composite indexes for common query patterns
    __table_args__ = (
        Index('idx_subscription_user_active', 'user_id', 'is_active'),
        Index('idx_subscription_status_active', 'status', 'is_active'),
        Index('idx_subscription_end_status', 'end_date', 'status'),
        Index('idx_subscription_payment_status', 'payment_status', 'status'),
    )

    def __repr__(self) -> str:
        """String representation of the Subscription"""
        return f"<Subscription(id={self.id}, user_id={self.user_id}, plan='{self.plan_name}', status='{self.status}')>"

class OANDAConnection(Base):
    """OANDA connection model for trading platform integration"""

    __tablename__ = "oanda_connections"

    # Primary key and foreign key
    id: int = Column(Integer, primary_key=True, index=True)
    user_id: int = Column(Integer, ForeignKey("users.id"), unique=True, index=True)  # Already unique, add index

    # OANDA Account Info
    account_id: str = Column(String(50), nullable=False, index=True)  # Add index for account lookups
    environment: str = Column(String(10), default="demo", index=True)  # Add index for environment queries
    account_currency: str = Column(String(3), default="USD")

    # Connection Status
    is_active: bool = Column(Boolean, default=True, index=True)  # Add index for active connection queries
    last_connected: Optional[datetime] = Column(DateTime, index=True)  # Add index for connection analytics
    connection_status: str = Column(String(20), default="DISCONNECTED", index=True)  # Add index for status queries

    # Account Balance Info (cached)
    balance: float = Column(Float, default=0.0)
    equity: float = Column(Float, default=0.0)
    margin_used: float = Column(Float, default=0.0)
    margin_available: float = Column(Float, default=0.0)
    unrealized_pl: float = Column(Float, default=0.0)

    # Settings
    auto_trading_enabled: bool = Column(Boolean, default=False, index=True)  # Add index for auto trading queries
    risk_tolerance: str = Column(String(10), default="MEDIUM", index=True)  # Add index for risk tolerance queries
    max_position_size: float = Column(Float, default=1.0)
    daily_loss_limit: float = Column(Float, default=1000.0)

    # Metadata
    created_at: datetime = Column(DateTime, default=func.now(), index=True)  # Add index for date queries
    updated_at: datetime = Column(DateTime, default=func.now(), onupdate=func.now(), index=True)  # Add index for update queries
    last_sync_at: Optional[datetime] = Column(DateTime, index=True)  # Add index for sync analytics

    # Relationships
    user: "User" = relationship("User", back_populates="oanda_connection")

    # Composite indexes for common query patterns
    __table_args__ = (
        Index('idx_oanda_active_status', 'is_active', 'connection_status'),
        Index('idx_oanda_env_active', 'environment', 'is_active'),
        Index('idx_oanda_auto_active', 'auto_trading_enabled', 'is_active'),
        Index('idx_oanda_sync_active', 'last_sync_at', 'is_active'),
    )

    def __repr__(self) -> str:
        """String representation of the OANDAConnection"""
        return f"<OANDAConnection(id={self.id}, user_id={self.user_id}, account_id='{self.account_id}', environment='{self.environment}')>"
