from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
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
    """Base user schema with common fields"""
    username: str = Field(..., min_length=3, max_length=50, description="Username for login")
    email: EmailStr = Field(..., description="User email address")
    full_name: Optional[str] = Field(None, description="User's full name")

    @validator('username')
    def username_alphanumeric(cls, v: str) -> str:
        """Validate username contains only alphanumeric characters and underscores"""
        if not v.isalnum() and '_' not in v:
            raise ValueError('Username must contain only alphanumeric characters and underscores')
        return v

class UserCreate(UserBase):
    """User creation schema with password"""
    password: str = Field(..., min_length=6, max_length=128, description="User password (min 6 characters)")

    @validator('password')
    def password_strength(cls, v: str) -> str:
        """Validate password strength"""
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

class UserResponse(UserBase):
    """User response schema for API responses"""
    id: int = Field(..., description="User ID")
    is_active: bool = Field(..., description="Whether the user account is active")
    created_at: datetime = Field(..., description="When the user was created")
    subscription_active: bool = Field(..., description="Whether the user has an active subscription")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class UserStatsOut(BaseModel):
    """User statistics output schema"""
    id: int = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="User email")
    full_name: Optional[str] = Field(None, description="User's full name")
    is_active: bool = Field(..., description="Whether the user account is active")
    is_admin: bool = Field(..., description="Whether the user has admin privileges")
    subscription_active: bool = Field(..., description="Whether the user has an active subscription")
    created_at: datetime = Field(..., description="When the user was created")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    total_signals: int = Field(..., ge=0, description="Total number of signals created by user")
    active_signals: int = Field(..., ge=0, description="Number of active signals")
    average_reliability: float = Field(..., ge=0, le=100, description="Average reliability score of signals")
    recent_signals_count: int = Field(..., ge=0, description="Number of recent signals")

    @validator('average_reliability')
    def validate_reliability(cls, v: float) -> float:
        """Validate reliability score is within bounds"""
        if not 0 <= v <= 100:
            raise ValueError('Reliability must be between 0 and 100')
        return v

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# Token schemas
class Token(BaseModel):
    """JWT token response schema"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field("bearer", description="Token type")

class TokenData(BaseModel):
    """Token data schema for JWT payload validation"""
    username: Optional[str] = Field(None, description="Username from token")
    exp: Optional[datetime] = Field(None, description="Token expiration time")

# Signal schemas
class SignalBase(BaseModel):
    """Base signal schema with common trading signal fields"""
    symbol: str = Field(..., min_length=6, max_length=20, description="Trading symbol (e.g., EUR_USD)")
    signal_type: SignalTypeEnum = Field(..., description="Type of trading signal")
    entry_price: float = Field(..., gt=0, description="Entry price for the trade")
    stop_loss: Optional[float] = Field(None, gt=0, description="Stop loss price")
    take_profit: Optional[float] = Field(None, gt=0, description="Take profit price")
    reliability: Optional[float] = Field(0.0, ge=0, le=100, description="Reliability score (0-100)")

    @validator('symbol')
    def validate_symbol(cls, v: str) -> str:
        """Validate trading symbol format"""
        if not v.isalnum() and '_' not in v:
            raise ValueError('Symbol must contain only alphanumeric characters and underscores')
        return v.upper()

    @validator('stop_loss', 'take_profit')
    def validate_prices(cls, v: Optional[float], values: Dict[str, Any]) -> Optional[float]:
        """Validate stop loss and take profit prices"""
        if v is not None and 'entry_price' in values:
            entry_price = values['entry_price']
            if v <= 0:
                raise ValueError('Price must be greater than 0')
        return v

class SignalCreate(SignalBase):
    """Signal creation schema with additional fields"""
    ai_analysis: Optional[str] = Field(None, description="AI analysis of the signal")
    confidence_score: Optional[float] = Field(0.0, ge=0, le=100, description="AI confidence score (0-100)")
    risk_level: Optional[str] = Field("MEDIUM", description="Risk level (LOW, MEDIUM, HIGH)")
    expires_at: Optional[datetime] = Field(None, description="Signal expiration time")

    @validator('risk_level')
    def validate_risk_level(cls, v: str) -> str:
        """Validate risk level"""
        allowed_levels = ['LOW', 'MEDIUM', 'HIGH']
        if v.upper() not in allowed_levels:
            raise ValueError(f'Risk level must be one of: {allowed_levels}')
        return v.upper()

class SignalOut(SignalBase):
    """Signal output schema for API responses"""
    id: int = Field(..., description="Signal ID")
    status: SignalStatusEnum = Field(..., description="Current status of the signal")
    reliability: float = Field(..., ge=0, le=100, description="Reliability score (0-100)")
    ai_analysis: Optional[str] = Field(None, description="AI analysis of the signal")
    confidence_score: float = Field(..., ge=0, le=100, description="AI confidence score (0-100)")
    risk_level: str = Field(..., description="Risk level")
    is_public: bool = Field(..., description="Whether the signal is public")
    is_active: bool = Field(..., description="Whether the signal is active")
    created_at: datetime = Field(..., description="When the signal was created")
    expires_at: Optional[datetime] = Field(None, description="Signal expiration time")
    source: str = Field(..., description="Source of the signal")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class SignalResponse(BaseModel):
    """Signal creation response schema"""
    signal: SignalOut = Field(..., description="Created signal data")
    message: str = Field(..., description="Response message")
    success: bool = Field(..., description="Whether the operation was successful")

class TopSignalsResponse(BaseModel):
    """Top signals response schema"""
    signals: List[SignalOut] = Field(..., description="List of top signals")
    total_count: int = Field(..., ge=0, description="Total number of signals")
    average_reliability: float = Field(..., ge=0, le=100, description="Average reliability score")

class SignalFilter(BaseModel):
    """Signal filter schema for querying signals"""
    symbol: Optional[str] = Field(None, description="Filter by symbol")
    signal_type: Optional[SignalTypeEnum] = Field(None, description="Filter by signal type")
    min_reliability: Optional[float] = Field(0, ge=0, le=100, description="Minimum reliability score")
    only_active: bool = Field(True, description="Filter only active signals")
    page: int = Field(1, ge=1, description="Page number for pagination")
    per_page: int = Field(10, ge=1, le=100, description="Items per page")

# Signal execution schemas
class SignalExecutionCreate(BaseModel):
    """Signal execution creation schema"""
    signal_id: int = Field(..., gt=0, description="ID of the signal to execute")
    execution_price: float = Field(..., gt=0, description="Price at which the signal was executed")
    quantity: float = Field(1.0, gt=0, description="Quantity/size of the execution")
    execution_type: str = Field("MANUAL", description="Type of execution (MANUAL, AUTO)")

    @validator('execution_type')
    def validate_execution_type(cls, v: str) -> str:
        """Validate execution type"""
        allowed_types = ['MANUAL', 'AUTO']
        if v.upper() not in allowed_types:
            raise ValueError(f'Execution type must be one of: {allowed_types}')
        return v.upper()

class SignalExecutionOut(BaseModel):
    """Signal execution output schema"""
    id: int = Field(..., description="Execution ID")
    signal_id: int = Field(..., description="ID of the executed signal")
    execution_price: float = Field(..., gt=0, description="Execution price")
    quantity: float = Field(..., gt=0, description="Execution quantity")
    execution_type: str = Field(..., description="Type of execution")
    executed_at: datetime = Field(..., description="When the execution occurred")
    unrealized_pnl: float = Field(..., description="Current unrealized profit/loss")

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class HealthCheckResponse(BaseModel):
    """Health check response schema"""
    status: str = Field("healthy", description="Overall health status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    version: str = Field("2.0.0", description="Application version")
    database: str = Field("connected", description="Database connection status")
    services: Dict[str, str] = Field(
        default_factory=lambda: {
            "api": "operational",
            "database": "operational"
        },
        description="Status of various services"
    )

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class APIResponse(BaseModel):
    """Generic API response schema"""
    message: str = Field(..., description="Response message")
    success: bool = Field(..., description="Whether the operation was successful")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    errors: Optional[List[str]] = Field(None, description="List of errors if any")

class PaginationParams(BaseModel):
    """Pagination parameters schema"""
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(10, ge=1, le=100, description="Items per page")

class PaginatedResponse(BaseModel):
    """Generic paginated response schema"""
    items: List[Any] = Field(..., description="List of items")
    total: int = Field(..., ge=0, description="Total number of items")
    page: int = Field(..., ge=1, description="Current page number")
    per_page: int = Field(..., ge=1, description="Items per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")

class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
