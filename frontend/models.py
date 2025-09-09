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
    
    # Relationships
    signals = relationship("Signal", back_populates="creator")
    executions = relationship("SignalExecution", back_populates="user")
    mt5_connections = relationship("MT5Connection", back_populates="user")

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
    
    # VPS info
    vps_id = Column(String(50))  # ID della VPS che ha generato il segnale
    source = Column(String(50), default="VPS_AI")  # VPS_AI, MANUAL, API
    
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

class MT5Connection(Base):
    __tablename__ = "mt5_connections"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    account_number = Column(String(20), nullable=False)
    broker_server = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=False)
    last_connected = Column(DateTime)
    connection_status = Column(String(20), default="DISCONNECTED")
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationship
    user = relationship("User", back_populates="mt5_connections")

class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    plan_name = Column(String(50), default="TRIAL")
    is_active = Column(Boolean, default=True)
    start_date = Column(DateTime, default=func.now())
    end_date = Column(DateTime)
    
    created_at = Column(DateTime, default=func.now())

class VPSHeartbeat(Base):
    __tablename__ = "vps_heartbeats"
    
    id = Column(Integer, primary_key=True, index=True)
    vps_id = Column(String(50), nullable=False, index=True)
    
    status = Column(String(20), default="active")  # active, error, maintenance
    timestamp = Column(DateTime, default=func.now())
    
    # Metrics
    signals_generated = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    uptime_seconds = Column(Integer, default=0)
    
    # Additional data
    version = Column(String(20))
    last_signal_at = Column(DateTime)
    mt5_status = Column(String(20))  # connected, disconnected, error
    
    created_at = Column(DateTime, default=func.now())