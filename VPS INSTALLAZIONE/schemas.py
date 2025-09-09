from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List
from enum import Enum

# Signal type enum
class SignalTypeEnum(str, Enum):
    BUY = "BUY"
    SELL = "SELL" 
    HOLD = "HOLD"

# User schemas
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    is_admin: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    message: str
    user: UserOut

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

# Auth schemas
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int

# Signal schemas
class SignalCreate(BaseModel):
    asset: str
    signal_type: str
    entry_price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    is_public: bool = False

class SignalOut(BaseModel):
    id: int
    asset: str
    signal_type: str
    entry_price: float
    current_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    reliability: float
    is_active: bool
    is_public: bool
    outcome: Optional[str] = None
    profit_loss: Optional[float] = None
    gemini_explanation: Optional[str] = None
    created_at: datetime
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class SignalResponse(BaseModel):
    message: str
    signal: SignalOut

class TopSignalsResponse(BaseModel):
    signals: List[SignalOut]
    count: int
    generated_at: datetime

class SignalFilter(BaseModel):
    asset: Optional[str] = None
    signal_type: Optional[str] = None
    min_reliability: Optional[float] = None
    max_reliability: Optional[float] = None
    outcome: Optional[str] = None
    is_active: Optional[bool] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    offset: int = 0
    limit: int = 50

# MT5 schemas
class MT5ConnectionCreate(BaseModel):
    broker: str
    account_type: str

class MT5ConnectionOut(BaseModel):
    id: int
    broker: str
    account_type: str
    is_active: bool
    last_connection: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Signal execution schemas
class SignalExecutionCreate(BaseModel):
    signal_id: int
    execution_price: float
    quantity: float
    execution_type: str

class SignalExecutionOut(BaseModel):
    id: int
    signal_id: int
    execution_price: float
    quantity: float
    execution_type: str
    profit_loss: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True
