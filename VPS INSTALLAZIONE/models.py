from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    signals = relationship("Signal", back_populates="user")
    subscriptions = relationship("Subscription", back_populates="user")
    mt5_connections = relationship("MT5Connection", back_populates="user")

class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Null for public signals
    asset = Column(String, nullable=False)
    signal_type = Column(String, nullable=False)  # BUY/SELL
    entry_price = Column(Float, nullable=False)
    current_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    reliability = Column(Float, nullable=False)  # 0-100
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)
    outcome = Column(String, nullable=True)  # WIN/LOSS/PENDING
    profit_loss = Column(Float, nullable=True)
    gemini_explanation = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="signals")
    executions = relationship("SignalExecution", back_populates="signal")

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String, nullable=False)  # ACTIVE/INACTIVE/TRIAL/EXPIRED
    plan_name = Column(String, nullable=False)
    start_date = Column(DateTime(timezone=True), server_default=func.now())
    end_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="subscriptions")

class MT5Connection(Base):
    __tablename__ = "mt5_connections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    encrypted_credentials = Column(Text, nullable=False)
    broker = Column(String, nullable=False)
    account_type = Column(String, nullable=False)  # REAL/DEMO
    is_active = Column(Boolean, default=True)
    last_connection = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="mt5_connections")

class SignalExecution(Base):
    __tablename__ = "signal_executions"

    id = Column(Integer, primary_key=True, index=True)
    signal_id = Column(Integer, ForeignKey("signals.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    execution_price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    execution_type = Column(String, nullable=False)  # MANUAL/AUTO
    profit_loss = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    signal = relationship("Signal", back_populates="executions")
