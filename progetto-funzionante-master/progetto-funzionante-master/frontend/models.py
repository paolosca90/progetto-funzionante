from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

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
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(128), nullable=False)
    full_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    trial_end = Column(DateTime)
    subscription_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    
    # Password reset functionality
    reset_token = Column(String(100))
    reset_token_expires = Column(DateTime)
    
    # Relationships
    signals = relationship("Signal", back_populates="creator")
    executions = relationship("SignalExecution", back_populates="user")
    oanda_connection = relationship("OANDAConnection", back_populates="user", uselist=False)

class Signal(Base):
    __tablename__ = "signals"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    signal_type = Column(Enum(SignalTypeEnum), nullable=False)
    entry_price = Column(Float, nullable=False)
    stop_loss = Column(Float)
    take_profit = Column(Float)
    reliability = Column(Float, default=0.0)  # 0-100%
    status = Column(Enum(SignalStatusEnum), default=SignalStatusEnum.ACTIVE)
    
    # AI Analysis
    ai_analysis = Column(Text)
    confidence_score = Column(Float, default=0.0)
    risk_level = Column(String(20), default="MEDIUM")  # LOW, MEDIUM, HIGH
    
    # Meta info
    is_public = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    expires_at = Column(DateTime)
    
    # Data source info
    source = Column(String(50), default="OANDA_AI")  # OANDA_AI, MANUAL, API
    
    # OANDA-specific fields
    # oanda_instrument = Column(String(20))  # OANDA format instrument (e.g., EUR_USD)
    timeframe = Column(String(10), default="H1")  # Analysis timeframe
    risk_reward_ratio = Column(Float, default=0.0)  # Risk/reward ratio
    position_size_suggestion = Column(Float, default=0.01)  # Suggested position size
    spread = Column(Float, default=0.0)  # Market spread at signal generation
    volatility = Column(Float, default=0.0)  # Market volatility (ATR-based)
    
    # Technical analysis metadata
    technical_score = Column(Float, default=0.0)  # Overall technical score
    rsi = Column(Float)  # RSI at signal generation
    macd_signal = Column(Float)  # MACD signal
    market_session = Column(String(20))  # Market session (Asian/European/US)
    
    # Foreign keys
    creator_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    creator = relationship("User", back_populates="signals")
    executions = relationship("SignalExecution", back_populates="signal")

class SignalExecution(Base):
    __tablename__ = "signal_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    signal_id = Column(Integer, ForeignKey("signals.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    
    execution_price = Column(Float, nullable=False)
    quantity = Column(Float, default=1.0)
    execution_type = Column(String(20), default="MANUAL")  # MANUAL, AUTO
    executed_at = Column(DateTime, default=func.now())
    
    # P&L tracking
    current_price = Column(Float)
    unrealized_pnl = Column(Float, default=0.0)
    realized_pnl = Column(Float)
    
    # Relationships
    signal = relationship("Signal", back_populates="executions")
    user = relationship("User", back_populates="executions")


class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    plan_name = Column(String(50), default="TRIAL")
    status = Column(String(20), default="ACTIVE")  # ACTIVE, EXPIRED, CANCELLED
    is_active = Column(Boolean, default=True)
    start_date = Column(DateTime, default=func.now())
    end_date = Column(DateTime)
    payment_status = Column(String(20), default="PENDING")  # PENDING, PAID, FAILED
    last_payment_date = Column(DateTime)
    
    created_at = Column(DateTime, default=func.now())

class OANDAConnection(Base):
    __tablename__ = "oanda_connections"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    
    # OANDA Account Info
    account_id = Column(String(50), nullable=False)
    environment = Column(String(10), default="demo")  # demo or live
    account_currency = Column(String(3), default="USD")
    
    # Connection Status
    is_active = Column(Boolean, default=True)
    last_connected = Column(DateTime)
    connection_status = Column(String(20), default="DISCONNECTED")  # CONNECTED, DISCONNECTED, ERROR
    
    # Account Balance Info (cached)
    balance = Column(Float, default=0.0)
    equity = Column(Float, default=0.0)
    margin_used = Column(Float, default=0.0)
    margin_available = Column(Float, default=0.0)
    unrealized_pl = Column(Float, default=0.0)
    
    # Settings
    auto_trading_enabled = Column(Boolean, default=False)
    risk_tolerance = Column(String(10), default="MEDIUM")  # LOW, MEDIUM, HIGH
    max_position_size = Column(Float, default=1.0)
    daily_loss_limit = Column(Float, default=1000.0)
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_sync_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="oanda_connection")


