from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List
from enum import Enum

class SignalTypeEnum(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class SignalStatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"

# Base schemas
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    subscription_active: bool
    
    class Config:
        from_attributes = True

class UserStatsOut(BaseModel):
    total_signals: int
    active_signals: int
    winning_signals: int
    losing_signals: int
    win_rate: float
    total_profit_loss: float
    average_reliability: float
    subscription_status: str
    subscription_days_left: Optional[int] = None

# Token schemas
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: Optional[str] = None

# Signal schemas
class SignalBase(BaseModel):
    symbol: str = Field(..., min_length=6, max_length=20)
    signal_type: SignalTypeEnum
    entry_price: float = Field(..., gt=0)
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    reliability: Optional[float] = Field(default=0.0, ge=0, le=100)

class SignalCreate(SignalBase):
    ai_analysis: Optional[str] = None
    confidence_score: Optional[float] = Field(default=0.0, ge=0, le=100)
    risk_level: Optional[str] = "MEDIUM"
    expires_at: Optional[datetime] = None

class SignalOut(SignalBase):
    id: int
    status: SignalStatusEnum
    reliability: float
    ai_analysis: Optional[str] = None
    confidence_score: float
    risk_level: str
    is_public: bool
    is_active: bool
    created_at: datetime
    expires_at: Optional[datetime] = None
    source: str
    
    class Config:
        from_attributes = True

class SignalResponse(BaseModel):
    signals: List[SignalOut]
    total: int
    page: int
    per_page: int

class TopSignalsResponse(BaseModel):
    signals: List[SignalOut]
    message: str = "Top 3 signals"

class SignalFilter(BaseModel):
    symbol: Optional[str] = None
    signal_type: Optional[SignalTypeEnum] = None
    min_reliability: Optional[float] = 0
    only_active: bool = True
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=10, ge=1, le=100)

# Signal execution schemas
class SignalExecutionCreate(BaseModel):
    signal_id: int
    execution_price: float = Field(..., gt=0)
    quantity: float = Field(default=1.0, gt=0)
    execution_type: str = "MANUAL"

class SignalExecutionOut(BaseModel):
    id: int
    signal_id: int
    execution_price: float
    quantity: float
    execution_type: str
    executed_at: datetime
    unrealized_pnl: float
    
    class Config:
        from_attributes = True


class HealthCheckResponse(BaseModel):
    status: str = "healthy"
    timestamp: datetime
    version: str = "2.0.0"
    database: str = "connected"
    services: dict = {
        "api": "operational",
        "database": "operational"
    }

class APIResponse(BaseModel):
    status: str
    message: str
    data: Optional[dict] = None
    timestamp: datetime = Field(default_factory=datetime.now)