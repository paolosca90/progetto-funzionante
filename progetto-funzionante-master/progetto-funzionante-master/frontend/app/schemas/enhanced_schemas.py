"""
Enhanced Pydantic Schemas with Comprehensive OpenAPI Documentation

This module provides detailed schemas with:
- Comprehensive field descriptions
- Validation rules and examples
- Request/response models
- Error handling schemas
- Trading system specific models
"""

from pydantic import BaseModel, Field, EmailStr, validator, constr
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from decimal import Decimal

# Enhanced Enum Types
class SignalTypeEnum(str, Enum):
    """Trading signal types with descriptions"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

class SignalStatusEnum(str, Enum):
    """Signal status types with descriptions"""
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"

class RiskLevelEnum(str, Enum):
    """Risk level classifications with descriptions"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class ExecutionTypeEnum(str, Enum):
    """Signal execution types with descriptions"""
    MANUAL = "MANUAL"
    AUTO = "AUTO"
    AI = "AI"

class MarketSessionEnum(str, Enum):
    """Market trading sessions with descriptions"""
    LONDON = "LONDON"
    NEW_YORK = "NEW_YORK"
    TOKYO = "TOKYO"
    SYDNEY = "SYDNEY"
    OVERLAP = "OVERLAP"
    WEEKEND = "WEEKEND"

class TimeframeEnum(str, Enum):
    """Chart timeframes with descriptions"""
    M1 = "M1"      # 1 minute
    M5 = "M5"      # 5 minutes
    M15 = "M15"    # 15 minutes
    M30 = "M30"    # 30 minutes
    H1 = "H1"      # 1 hour
    H4 = "H4"      # 4 hours
    D1 = "D1"      # Daily
    W1 = "W1"      # Weekly
    MN1 = "MN1"    # Monthly

# Enhanced User Schemas
class UserCreateEnhanced(BaseModel):
    """Enhanced user registration schema with comprehensive validation"""
    username: constr(min_length=3, max_length=50, regex=r'^[a-zA-Z0-9_]+$') = Field(
        ...,
        description="Unique username for login (alphanumeric and underscore only)",
        example="trader_pro_2024"
    )
    email: EmailStr = Field(
        ...,
        description="Valid email address for account verification and communication",
        example="trader@example.com"
    )
    password: constr(min_length=8, max_length=128) = Field(
        ...,
        description="Secure password (min 8 characters, must include uppercase, lowercase, number, and special character)",
        example="SecurePass123!"
    )
    full_name: constr(min_length=2, max_length=100) = Field(
        ...,
        description="User's full name for account management",
        example="John Trader Smith"
    )
    phone: Optional[constr(min_length=10, max_length=20)] = Field(
        None,
        description="Optional phone number for account verification",
        example="+1234567890"
    )
    country: Optional[constr(min_length=2, max_length=2)] = Field(
        None,
        description="Two-letter country code (ISO 3166-1 alpha-2)",
        example="US"
    )
    timezone: Optional[str] = Field(
        None,
        description="User's timezone for display purposes",
        example="America/New_York"
    )

    @validator('password')
    def validate_password_strength(cls, v: str) -> str:
        """Validate password strength requirements"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?`~' for c in v):
            raise ValueError('Password must contain at least one special character')
        return v

    @validator('phone')
    def validate_phone_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format"""
        if v is None:
            return v
        # Remove all non-digit characters for validation
        digits = ''.join(c for c in v if c.isdigit())
        if len(digits) < 10 or len(digits) > 15:
            raise ValueError('Phone number must be between 10 and 15 digits')
        return v

    @validator('country')
    def validate_country_code(cls, v: Optional[str]) -> Optional[str]:
        """Validate ISO country code"""
        if v is None:
            return v
        if len(v) != 2 or not v.isalpha():
            raise ValueError('Country code must be exactly 2 letters')
        return v.upper()

class UserLoginRequest(BaseModel):
    """User login request schema"""
    username_or_email: str = Field(
        ...,
        description="Username or email address for login",
        example="trader_pro_2024"
    )
    password: str = Field(
        ...,
        description="User password",
        example="SecurePass123!",
        min_length=8
    )

class UserResponseEnhanced(BaseModel):
    """Enhanced user response schema with comprehensive user information"""
    id: int = Field(
        ...,
        description="Unique user identifier",
        example=12345,
        ge=1
    )
    username: str = Field(
        ...,
        description="Unique username",
        example="trader_pro_2024"
    )
    email: str = Field(
        ...,
        description="User email address",
        example="trader@example.com"
    )
    full_name: str = Field(
        ...,
        description="User's full name",
        example="John Trader Smith"
    )
    is_active: bool = Field(
        ...,
        description="Whether the user account is active",
        example=True
    )
    is_admin: bool = Field(
        ...,
        description="Whether the user has administrative privileges",
        example=False
    )
    subscription_active: bool = Field(
        ...,
        description="Whether the user has an active subscription",
        example=True
    )
    created_at: datetime = Field(
        ...,
        description="Account creation timestamp",
        example="2024-01-15T10:30:00Z"
    )
    last_login: Optional[datetime] = Field(
        None,
        description="Last successful login timestamp",
        example="2024-01-15T15:45:30Z"
    )
    trial_end: Optional[datetime] = Field(
        None,
        description="Trial subscription end date",
        example="2024-02-15T10:30:00Z"
    )
    phone: Optional[str] = Field(
        None,
        description="User's phone number",
        example="+1234567890"
    )
    country: Optional[str] = Field(
        None,
        description="User's country code",
        example="US"
    )
    timezone: Optional[str] = Field(
        None,
        description="User's timezone",
        example="America/New_York"
    )
    email_verified: bool = Field(
        False,
        description="Whether the user's email has been verified",
        example=True
    )
    profile_complete: bool = Field(
        False,
        description="Whether the user has completed their profile",
        example=True
    )

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# Enhanced Trading Signal Schemas
class SignalCreateEnhanced(BaseModel):
    """Enhanced signal creation schema with comprehensive trading information"""
    symbol: constr(min_length=6, max_length=20, regex=r'^[A-Z0-9_]+$') = Field(
        ...,
        description="Trading symbol in OANDA format (e.g., EUR_USD, GOLD_USD)",
        example="EUR_USD"
    )
    signal_type: SignalTypeEnum = Field(
        ...,
        description="Type of trading signal",
        example=SignalTypeEnum.BUY
    )
    entry_price: Decimal = Field(
        ...,
        description="Recommended entry price for the trade",
        example=Decimal("1.0850"),
        gt=0
    )
    stop_loss: Optional[Decimal] = Field(
        None,
        description="Stop loss price for risk management",
        example=Decimal("1.0820"),
        gt=0
    )
    take_profit: Optional[Decimal] = Field(
        None,
        description="Take profit price for profit target",
        example=Decimal("1.0900"),
        gt=0
    )
    reliability: float = Field(
        ...,
        description="Signal reliability score (0-100) based on AI analysis",
        example=85.5,
        ge=0,
        le=100
    )
    confidence_score: float = Field(
        ...,
        description="AI confidence score (0-100) for this signal",
        example=87.0,
        ge=0,
        le=100
    )
    risk_level: RiskLevelEnum = Field(
        ...,
        description="Risk level classification",
        example=RiskLevelEnum.MEDIUM
    )
    timeframe: TimeframeEnum = Field(
        ...,
        description="Primary timeframe used for signal generation",
        example=TimeframeEnum.H1
    )
    ai_analysis: Optional[str] = Field(
        None,
        description="Detailed AI analysis and reasoning for the signal",
        example="Strong bullish momentum detected with RSI oversold bounce and MACD crossover"
    )
    expires_at: Optional[datetime] = Field(
        None,
        description="Signal expiration time after which it should not be used",
        example="2024-12-31T23:59:59Z"
    )
    market_session: MarketSessionEnum = Field(
        ...,
        description="Market session when signal was generated",
        example=MarketSessionEnum.LONDON
    )
    volatility: float = Field(
        ...,
        description="Market volatility measurement (ATR-based)",
        example=0.0012,
        ge=0
    )
    spread: float = Field(
        ...,
        description="Current market spread at signal generation",
        example=0.0001,
        ge=0
    )
    risk_reward_ratio: float = Field(
        ...,
        description="Calculated risk/reward ratio",
        example=2.5,
        ge=0
    )
    position_size_suggestion: float = Field(
        ...,
        description="Suggested position size based on risk management",
        example=0.01,
        gt=0
    )
    technical_score: float = Field(
        ...,
        description="Overall technical analysis score (0-100)",
        example=78.0,
        ge=0,
        le=100
    )
    rsi: Optional[float] = Field(
        None,
        description="RSI indicator value",
        example=35.5,
        ge=0,
        le=100
    )
    macd_signal: Optional[float] = Field(
        None,
        description="MACD signal line value",
        example=0.0023
    )
    is_public: bool = Field(
        True,
        description="Whether this signal is visible to all users",
        example=True
    )

    @validator('symbol')
    def validate_symbol_format(cls, v: str) -> str:
        """Validate trading symbol format"""
        v = v.upper()
        # Basic validation for common symbol formats
        if not (3 <= len(v.replace('_', '')) <= 10):
            raise ValueError('Symbol must be between 3 and 10 characters long (excluding underscores)')
        return v

    @validator('stop_loss', 'take_profit')
    def validate_price_levels(cls, v: Optional[Decimal], values: Dict[str, Any]) -> Optional[Decimal]:
        """Validate stop loss and take profit prices"""
        if v is not None and 'entry_price' in values:
            entry_price = values['entry_price']
            signal_type = values.get('signal_type')

            if signal_type == SignalTypeEnum.BUY:
                if v >= entry_price:
                    raise ValueError('For BUY signals, stop loss must be below entry price')
                if values.get('take_profit') and values['take_profit'] <= entry_price:
                    raise ValueError('For BUY signals, take profit must be above entry price')
            elif signal_type == SignalTypeEnum.SELL:
                if v <= entry_price:
                    raise ValueError('For SELL signals, stop loss must be above entry price')
                if values.get('take_profit') and values['take_profit'] >= entry_price:
                    raise ValueError('For SELL signals, take profit must be below entry price')

        return v

    @validator('expires_at')
    def validate_expiration(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Validate signal expiration time"""
        if v is not None:
            now = datetime.utcnow()
            max_expiration = now + timedelta(days=30)  # Max 30 days in advance
            if v <= now:
                raise ValueError('Expiration time must be in the future')
            if v > max_expiration:
                raise ValueError('Expiration time cannot be more than 30 days in the future')
        return v

class SignalResponseEnhanced(BaseModel):
    """Enhanced signal response schema with comprehensive trading information"""
    id: int = Field(
        ...,
        description="Unique signal identifier",
        example=12345,
        ge=1
    )
    symbol: str = Field(
        ...,
        description="Trading symbol",
        example="EUR_USD"
    )
    signal_type: SignalTypeEnum = Field(
        ...,
        description="Type of trading signal",
        example=SignalTypeEnum.BUY
    )
    entry_price: Decimal = Field(
        ...,
        description="Recommended entry price",
        example=Decimal("1.0850")
    )
    stop_loss: Optional[Decimal] = Field(
        None,
        description="Stop loss price",
        example=Decimal("1.0820")
    )
    take_profit: Optional[Decimal] = Field(
        None,
        description="Take profit price",
        example=Decimal("1.0900")
    )
    reliability: float = Field(
        ...,
        description="Signal reliability score (0-100)",
        example=85.5,
        ge=0,
        le=100
    )
    confidence_score: float = Field(
        ...,
        description="AI confidence score (0-100)",
        example=87.0,
        ge=0,
        le=100
    )
    risk_level: RiskLevelEnum = Field(
        ...,
        description="Risk level classification",
        example=RiskLevelEnum.MEDIUM
    )
    status: SignalStatusEnum = Field(
        ...,
        description="Current signal status",
        example=SignalStatusEnum.ACTIVE
    )
    timeframe: TimeframeEnum = Field(
        ...,
        description="Primary timeframe used",
        example=TimeframeEnum.H1
    )
    ai_analysis: Optional[str] = Field(
        None,
        description="AI analysis and reasoning",
        example="Strong bullish momentum detected with RSI oversold bounce"
    )
    expires_at: Optional[datetime] = Field(
        None,
        description="Signal expiration time",
        example="2024-12-31T23:59:59Z"
    )
    market_session: MarketSessionEnum = Field(
        ...,
        description="Market session at generation",
        example=MarketSessionEnum.LONDON
    )
    volatility: float = Field(
        ...,
        description="Market volatility measurement",
        example=0.0012,
        ge=0
    )
    spread: float = Field(
        ...,
        description="Market spread at generation",
        example=0.0001,
        ge=0
    )
    risk_reward_ratio: float = Field(
        ...,
        description="Risk/reward ratio",
        example=2.5,
        ge=0
    )
    position_size_suggestion: float = Field(
        ...,
        description="Suggested position size",
        example=0.01,
        gt=0
    )
    technical_score: float = Field(
        ...,
        description="Technical analysis score",
        example=78.0,
        ge=0,
        le=100
    )
    rsi: Optional[float] = Field(
        None,
        description="RSI indicator value",
        example=35.5,
        ge=0,
        le=100
    )
    macd_signal: Optional[float] = Field(
        None,
        description="MACD signal value",
        example=0.0023
    )
    is_public: bool = Field(
        ...,
        description="Whether signal is public",
        example=True
    )
    is_active: bool = Field(
        ...,
        description="Whether signal is active",
        example=True
    )
    created_at: datetime = Field(
        ...,
        description="Signal creation timestamp",
        example="2024-01-15T10:30:00Z"
    )
    source: str = Field(
        ...,
        description="Signal source",
        example="OANDA_AI"
    )
    creator_id: int = Field(
        ...,
        description="Creator user ID",
        example=123,
        ge=1
    )

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }

# Enhanced Market Data Schemas
class MarketDataResponse(BaseModel):
    """Real-time market data response schema"""
    symbol: str = Field(
        ...,
        description="Trading symbol",
        example="EUR_USD"
    )
    bid: Decimal = Field(
        ...,
        description="Current bid price",
        example=Decimal("1.0848")
    )
    ask: Decimal = Field(
        ...,
        description="Current ask price",
        example=Decimal("1.0850")
    )
    spread: float = Field(
        ...,
        description="Current spread in pips",
        example=2.0,
        ge=0
    )
    timestamp: datetime = Field(
        ...,
        description="Market data timestamp",
        example="2024-01-15T10:30:00Z"
    )
    session: MarketSessionEnum = Field(
        ...,
        description="Current market session",
        example=MarketSessionEnum.LONDON
    )
    volatility: float = Field(
        ...,
        description="Current market volatility (ATR-based)",
        example=0.0012,
        ge=0
    )
    volume_24h: Optional[float] = Field(
        None,
        description="24-hour trading volume",
        example=1250000000.0,
        ge=0
    )
    daily_change: Optional[float] = Field(
        None,
        description="Daily price change percentage",
        example=0.15
    )
    technical_indicators: Optional[Dict[str, Any]] = Field(
        None,
        description="Technical indicator values",
        example={
            "rsi": 45.5,
            "macd": {"line": 0.0023, "signal": 0.0018, "histogram": 0.0005},
            "bollinger_bands": {"upper": 1.0880, "middle": 1.0850, "lower": 1.0820},
            "atr": 0.0012
        }
    )

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            Decimal: lambda v: float(v)
        }

# Enhanced Error Response Schemas
class ErrorResponseEnhanced(BaseModel):
    """Enhanced error response schema with detailed information"""
    error: str = Field(
        ...,
        description="Error type or code",
        example="ValidationError"
    )
    message: str = Field(
        ...,
        description="Human-readable error message",
        example="Invalid input data provided"
    )
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Detailed error information",
        example={
            "field": "email",
            "issue": "Invalid email format"
        }
    )
    field_errors: Optional[List[Dict[str, str]]] = Field(
        None,
        description="Field-specific validation errors",
        example=[
            {
                "field": "password",
                "message": "Password must contain at least one uppercase letter"
            }
        ]
    )
    request_id: Optional[str] = Field(
        None,
        description="Unique request identifier for debugging",
        example="req_123456789"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Error timestamp"
    )
    help_url: Optional[str] = Field(
        None,
        description="URL to help documentation",
        example="https://docs.cash-revolution.com/errors/validation"
    )

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# Enhanced API Response Schemas
class APIResponseEnhanced(BaseModel):
    """Enhanced API response schema with metadata"""
    success: bool = Field(
        ...,
        description="Whether the operation was successful",
        example=True
    )
    message: str = Field(
        ...,
        description="Response message",
        example="Operation completed successfully"
    )
    data: Optional[Dict[str, Any]] = Field(
        None,
        description="Response data"
    )
    errors: Optional[List[str]] = Field(
        None,
        description="List of error messages if any"
    )
    meta: Optional[Dict[str, Any]] = Field(
        None,
        description="Response metadata",
        example={
            "request_id": "req_123456789",
            "execution_time_ms": 45,
            "api_version": "v2"
        }
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Response timestamp"
    )

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# Enhanced Pagination Schemas
class PaginationParamsEnhanced(BaseModel):
    """Enhanced pagination parameters"""
    page: int = Field(
        1,
        description="Page number (1-based)",
        ge=1,
        example=1
    )
    per_page: int = Field(
        20,
        description="Items per page",
        ge=1,
        le=100,
        example=20
    )
    sort_by: Optional[str] = Field(
        None,
        description="Field to sort by",
        example="created_at"
    )
    sort_order: Optional[str] = Field(
        "desc",
        description="Sort order",
        regex=r'^(asc|desc)$',
        example="desc"
    )
    search: Optional[str] = Field(
        None,
        description="Search term",
        example="EURUSD"
    )
    filters: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional filters",
        example={"signal_type": "BUY", "min_reliability": 80}
    )

class PaginatedResponseEnhanced(BaseModel):
    """Enhanced paginated response schema"""
    items: List[Any] = Field(
        ...,
        description="List of items on current page"
    )
    pagination: Dict[str, Any] = Field(
        ...,
        description="Pagination information",
        example={
            "page": 1,
            "per_page": 20,
            "total_items": 100,
            "total_pages": 5,
            "has_next": True,
            "has_prev": False,
            "next_page": 2,
            "prev_page": None
        }
    )
    filters: Optional[Dict[str, Any]] = Field(
        None,
        description="Applied filters"
    )
    sorting: Optional[Dict[str, str]] = Field(
        None,
        description="Applied sorting",
        example={"sort_by": "created_at", "sort_order": "desc"}
    )
    meta: Optional[Dict[str, Any]] = Field(
        None,
        description="Response metadata"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Response timestamp"
    )

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }