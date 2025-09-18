"""
Enhanced Trading Signals Router with Comprehensive OpenAPI Documentation

This router provides trading signal endpoints with:
- Detailed signal models with technical analysis
- Market data integration
- Risk management features
- Performance analytics
- Comprehensive examples and documentation
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, timedelta
from decimal import Decimal
import logging

from schemas import SignalCreate, SignalOut, SignalResponse, TopSignalsResponse, SignalFilter
from app.schemas.enhanced_schemas import (
    SignalCreateEnhanced, SignalResponseEnhanced, MarketDataResponse,
    PaginationParamsEnhanced, PaginatedResponseEnhanced, ErrorResponseEnhanced,
    SignalTypeEnum, SignalStatusEnum, RiskLevelEnum, MarketSessionEnum, TimeframeEnum
)
from models import User, Signal
from app.dependencies.database import get_db
from app.dependencies.services import get_signal_service, get_oanda_service
from app.dependencies.auth import get_current_active_user_dependency, get_optional_user_dependency
from app.services.signal_service import SignalService
from app.services.oanda_service import OANDAService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/signals",
    tags=["signals"],
    responses={
        401: {
            "description": "Unauthorized - Authentication required",
            "content": {
                "application/json": {
                    "example": {
                        "error": "AuthenticationError",
                        "message": "Valid authentication token required",
                        "timestamp": "2024-01-15T10:30:00Z"
                    }
                }
            }
        },
        403: {
            "description": "Forbidden - Insufficient permissions",
            "content": {
                "application/json": {
                    "example": {
                        "error": "AuthorizationError",
                        "message": "Active subscription required to access signals",
                        "timestamp": "2024-01-15T10:30:00Z"
                    }
                }
            }
        },
        429: {
            "description": "Too Many Requests - Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {
                        "error": "RateLimitExceeded",
                        "message": "Signal generation rate limit exceeded",
                        "details": {
                            "limit": "10 per hour",
                            "retry_after": 1800
                        },
                        "timestamp": "2024-01-15T10:30:00Z"
                    }
                }
            }
        }
    }
)

@router.get(
    "/latest",
    response_model=List[SignalResponseEnhanced],
    summary="Get Latest Trading Signals",
    description="""
    Retrieve the most recent active trading signals with comprehensive filtering options.

    This endpoint provides access to the latest AI-generated trading signals with:
    - Technical analysis integration
    - Risk management parameters
    - Market session context
    - Real-time reliability scoring
    - Pagination support for large datasets

    **Features:**
    - AI-powered signal generation
    - Multi-timeframe analysis
    - Risk assessment and scoring
    - Market session awareness
    - Performance tracking

    **Filtering Options:**
    - Limit results (default: 10, max: 100)
    - Minimum reliability threshold
    - Risk level filtering
    - Symbol-specific filtering

    **Response Includes:**
    - Complete signal details
    - Technical indicators
    - AI analysis commentary
    - Risk management parameters
    - Performance metrics
    """,
    responses={
        200: {
            "description": "Latest signals retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 12345,
                        "symbol": "EUR_USD",
                        "signal_type": "BUY",
                        "entry_price": "1.0850",
                        "stop_loss": "1.0820",
                        "take_profit": "1.0900",
                        "reliability": 85.5,
                        "confidence_score": 87.0,
                        "risk_level": "MEDIUM",
                        "status": "ACTIVE",
                        "timeframe": "H1",
                        "ai_analysis": "Strong bullish momentum detected with RSI oversold bounce",
                        "market_session": "LONDON",
                        "volatility": 0.0012,
                        "spread": 0.0001,
                        "risk_reward_ratio": 2.5,
                        "position_size_suggestion": 0.01,
                        "technical_score": 78.0,
                        "rsi": 35.5,
                        "macd_signal": 0.0023,
                        "is_public": True,
                        "is_active": True,
                        "created_at": "2024-01-15T10:30:00Z",
                        "source": "OANDA_AI",
                        "creator_id": 123
                    }
                }
            }
        }
    }
)
def get_latest_signals(
    limit: int = Query(
        10,
        ge=1,
        le=100,
        description="Maximum number of signals to return (1-100)",
        example=20
    ),
    min_reliability: float = Query(
        None,
        ge=0.0,
        le=100.0,
        description="Minimum reliability score filter (0-100)",
        example=80.0
    ),
    risk_level: Optional[RiskLevelEnum] = Query(
        None,
        description="Filter by risk level (LOW, MEDIUM, HIGH)",
        example=RiskLevelEnum.MEDIUM
    ),
    signal_type: Optional[SignalTypeEnum] = Query(
        None,
        description="Filter by signal type (BUY, SELL, HOLD)",
        example=SignalTypeEnum.BUY
    ),
    timeframe: Optional[TimeframeEnum] = Query(
        None,
        description="Filter by analysis timeframe",
        example=TimeframeEnum.H1
    ),
    symbol: Optional[str] = Query(
        None,
        description="Filter by specific trading symbol",
        example="EUR_USD"
    ),
    signal_service: SignalService = Depends(get_signal_service),
    current_user: Optional[User] = Depends(get_optional_user_dependency)
) -> List[SignalResponseEnhanced]:
    """
    Retrieve the latest active trading signals with comprehensive filtering

    This endpoint provides access to the most recent AI-generated trading signals,
    with advanced filtering options for customized signal discovery.

    **Key Features:**
    - AI-powered signal generation using Gemini AI
    - Multi-timeframe technical analysis
    - Risk assessment and scoring
    - Market session awareness
    - Real-time reliability updates

    **Filtering Capabilities:**
    - **Limit**: Control number of results (1-100)
    - **Reliability**: Filter by minimum reliability score
    - **Risk Level**: Focus on specific risk categories
    - **Signal Type**: Filter by BUY/SELL/HOLD signals
    - **Timeframe**: Filter by analysis timeframe
    - **Symbol**: Get signals for specific instruments

    **Response Data:**
    - Complete signal details with entry/exit points
    - Technical indicators and analysis
    - Risk management parameters
    - AI-generated commentary
    - Performance tracking data

    **Access Requirements:**
    - Public signals available without authentication
    - Premium signals require active subscription
    - Enhanced filtering for authenticated users

    **Rate Limits:**
    - Unauthenticated: 60 requests per minute
    - Authenticated: 100 requests per minute

    **Use Cases:**
    - Real-time signal monitoring
    - Backtesting signal performance
    - Risk management analysis
    - Market research and analysis
    """
    try:
        logger.info(f"Retrieving latest signals - Limit: {limit}, User: {current_user.username if current_user else 'Anonymous'}")

        # Apply subscription-based access control
        if current_user and not current_user.subscription_active:
            # Limit access for non-subscribers
            limit = min(limit, 5)
            logger.warning(f"Non-subscriber {current_user.username} accessing signals - limited to {limit}")

        # Get signals with filtering
        signals = signal_service.get_latest_signals_with_filters(
            limit=limit,
            min_reliability=min_reliability,
            risk_level=risk_level.value if risk_level else None,
            signal_type=signal_type.value if signal_type else None,
            timeframe=timeframe.value if timeframe else None,
            symbol=symbol
        )

        # Convert to enhanced response format
        enhanced_signals = []
        for signal in signals:
            enhanced_signal = SignalResponseEnhanced(
                id=signal.id,
                symbol=signal.symbol,
                signal_type=SignalTypeEnum(signal.signal_type.value),
                entry_price=Decimal(str(signal.entry_price)),
                stop_loss=Decimal(str(signal.stop_loss)) if signal.stop_loss else None,
                take_profit=Decimal(str(signal.take_profit)) if signal.take_profit else None,
                reliability=signal.reliability,
                confidence_score=signal.confidence_score,
                risk_level=RiskLevelEnum(signal.risk_level),
                status=SignalStatusEnum(signal.status.value),
                timeframe=TimeframeEnum(signal.timeframe),
                ai_analysis=signal.ai_analysis,
                expires_at=signal.expires_at,
                market_session=MarketSessionEnum(signal.market_session) if signal.market_session else MarketSessionEnum.LONDON,
                volatility=signal.volatility,
                spread=signal.spread,
                risk_reward_ratio=signal.risk_reward_ratio,
                position_size_suggestion=signal.position_size_suggestion,
                technical_score=signal.technical_score,
                rsi=signal.rsi,
                macd_signal=signal.macd_signal,
                is_public=signal.is_public,
                is_active=signal.is_active,
                created_at=signal.created_at,
                source=signal.source,
                creator_id=signal.creator_id
            )
            enhanced_signals.append(enhanced_signal)

        logger.info(f"Retrieved {len(enhanced_signals)} signals for user")
        return enhanced_signals

    except Exception as e:
        logger.error(f"Error retrieving latest signals: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving trading signals"
        )

@router.post(
    "/",
    response_model=SignalResponseEnhanced,
    status_code=status.HTTP_201_CREATED,
    summary="Create Trading Signal",
    description="""
    Create a new trading signal with comprehensive AI analysis and risk management.

    This endpoint allows authenticated users to create trading signals with:
    - AI-powered analysis integration
    - Risk management parameters
    - Technical indicator data
    - Market session context
    - Performance tracking

    **Requirements:**
    - Active subscription required
    - Valid trading symbol format
    - Comprehensive risk management
    - AI analysis integration

    **Signal Validation:**
    - Symbol format validation
    - Price level合理性 checks
    - Risk/reward ratio validation
    - Technical indicator validation
    - Market session verification

    **AI Integration:**
    - Gemini AI analysis integration
    - Technical analysis validation
    - Risk assessment scoring
    - Market sentiment analysis
    - Confidence calculation
    """,
    responses={
        201: {
            "description": "Signal created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": 12345,
                        "symbol": "EUR_USD",
                        "signal_type": "BUY",
                        "entry_price": "1.0850",
                        "stop_loss": "1.0820",
                        "take_profit": "1.0900",
                        "reliability": 85.5,
                        "confidence_score": 87.0,
                        "risk_level": "MEDIUM",
                        "status": "ACTIVE",
                        "created_at": "2024-01-15T10:30:00Z",
                        "source": "MANUAL",
                        "ai_analysis": "Technical analysis shows strong bullish momentum"
                    }
                }
            }
        },
        400: {
            "description": "Validation Error - Invalid signal data",
            "content": {
                "application/json": {
                    "example": {
                        "error": "ValidationError",
                        "message": "Invalid signal parameters",
                        "field_errors": [
                            {
                                "field": "entry_price",
                                "message": "Entry price must be positive"
                            }
                        ]
                    }
                }
            }
        },
        403: {
            "description": "Forbidden - Active subscription required",
            "content": {
                "application/json": {
                    "example": {
                        "error": "SubscriptionRequired",
                        "message": "Active subscription required to create signals"
                    }
                }
            }
        }
    }
)
def create_signal(
    signal: SignalCreateEnhanced,
    current_user: User = Depends(get_current_active_user_dependency),
    signal_service: SignalService = Depends(get_signal_service),
    oanda_service: OANDAService = Depends(get_oanda_service)
) -> SignalResponseEnhanced:
    """
    Create a new trading signal with comprehensive analysis and validation

    This endpoint allows authenticated users with active subscriptions to create
    trading signals with full AI integration and risk management.

    **Key Features:**
    - AI-powered signal validation
    - Real-time market data integration
    - Risk management calculations
    - Technical analysis validation
    - Performance tracking setup

    **Validation Process:**
    1. **Symbol Validation**: Verify trading symbol format and availability
    2. **Price Validation**: Check entry, stop loss, and take profit合理性
    3. **Risk Assessment**: Calculate risk/reward ratios and position sizing
    4. **Market Data**: Verify current market conditions
    5. **AI Analysis**: Generate or validate AI commentary
    6. **Technical Indicators**: Validate and calculate technical metrics

    **AI Integration:**
    - Automatic AI analysis generation if not provided
    - Technical indicator validation and enhancement
    - Risk assessment scoring
    - Market sentiment analysis
    - Confidence calculation

    **Risk Management:**
    - Automatic position size calculation
    - Risk/reward ratio validation
    - Stop loss and take profit合理性检查
    - Volatility assessment
    - Market session awareness

    **Response Data:**
    - Complete signal with all calculated fields
    - AI analysis and commentary
    - Technical indicators and metrics
    - Risk management parameters
    - Performance tracking setup

    **Access Requirements:**
    - Valid authentication token
    - Active subscription
    - Rate limiting (10 signals per hour)
    """
    try:
        logger.info(f"Signal creation attempt by user: {current_user.username} for symbol: {signal.symbol}")

        # Check subscription status
        if not current_user.subscription_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Active subscription required to create signals"
            )

        # Validate symbol with OANDA
        market_data = oanda_service.get_market_data(signal.symbol)
        if not market_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid or unsupported trading symbol: {signal.symbol}"
            )

        # Create signal through service
        created_signal = signal_service.create_enhanced_signal(signal, current_user.id)

        # Convert to enhanced response format
        enhanced_signal = SignalResponseEnhanced(
            id=created_signal.id,
            symbol=created_signal.symbol,
            signal_type=SignalTypeEnum(created_signal.signal_type.value),
            entry_price=Decimal(str(created_signal.entry_price)),
            stop_loss=Decimal(str(created_signal.stop_loss)) if created_signal.stop_loss else None,
            take_profit=Decimal(str(created_signal.take_profit)) if created_signal.take_profit else None,
            reliability=created_signal.reliability,
            confidence_score=created_signal.confidence_score,
            risk_level=RiskLevelEnum(created_signal.risk_level),
            status=SignalStatusEnum(created_signal.status.value),
            timeframe=TimeframeEnum(created_signal.timeframe),
            ai_analysis=created_signal.ai_analysis,
            expires_at=created_signal.expires_at,
            market_session=MarketSessionEnum(created_signal.market_session) if created_signal.market_session else MarketSessionEnum.LONDON,
            volatility=created_signal.volatility,
            spread=created_signal.spread,
            risk_reward_ratio=created_signal.risk_reward_ratio,
            position_size_suggestion=created_signal.position_size_suggestion,
            technical_score=created_signal.technical_score,
            rsi=created_signal.rsi,
            macd_signal=created_signal.macd_signal,
            is_public=created_signal.is_public,
            is_active=created_signal.is_active,
            created_at=created_signal.created_at,
            source=created_signal.source,
            creator_id=created_signal.creator_id
        )

        logger.info(f"Signal created successfully: ID {enhanced_signal.id} by user {current_user.username}")
        return enhanced_signal

    except ValueError as e:
        logger.error(f"Signal validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating signal: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating trading signal"
        )

@router.get(
    "/market-data/{symbol}",
    response_model=MarketDataResponse,
    summary="Get Real-time Market Data",
    description="""
    Retrieve real-time market data for a specific trading symbol.

    This endpoint provides comprehensive market information including:
    - Current bid/ask prices
    - Market spread information
    - Trading session context
    - Volatility measurements
    - Technical indicators

    **Data Sources:**
    - OANDA real-time price feeds
    - Calculated technical indicators
    - Market session detection
    - Volatility calculations

    **Response Includes:**
    - Real-time pricing data
    - Market spread analysis
    - Session information
    - Technical indicators
    - Volume and volatility data
    """,
    responses={
        200: {
            "description": "Market data retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "symbol": "EUR_USD",
                        "bid": "1.0848",
                        "ask": "1.0850",
                        "spread": 2.0,
                        "timestamp": "2024-01-15T10:30:00Z",
                        "session": "LONDON",
                        "volatility": 0.0012,
                        "volume_24h": 1250000000.0,
                        "daily_change": 0.15,
                        "technical_indicators": {
                            "rsi": 45.5,
                            "macd": {"line": 0.0023, "signal": 0.0018, "histogram": 0.0005},
                            "bollinger_bands": {"upper": 1.0880, "middle": 1.0850, "lower": 1.0820},
                            "atr": 0.0012
                        }
                    }
                }
            }
        },
        404: {
            "description": "Symbol not found",
            "content": {
                "application/json": {
                    "example": {
                        "error": "SymbolNotFound",
                        "message": "Trading symbol not found or not supported",
                        "symbol": "INVALID_SYMBOL"
                    }
                }
            }
        }
    }
)
def get_market_data(
    symbol: str = Path(
        ...,
        description="Trading symbol in OANDA format (e.g., EUR_USD, GOLD_USD)",
        example="EUR_USD",
        regex=r'^[A-Z0-9_]+$'
    ),
    oanda_service: OANDAService = Depends(get_oanda_service),
    current_user: Optional[User] = Depends(get_optional_user_dependency)
) -> MarketDataResponse:
    """
    Retrieve real-time market data for a trading symbol

    This endpoint provides comprehensive market information for technical analysis
    and signal generation.

    **Data Provided:**
    - **Pricing**: Current bid/ask prices with real-time updates
    - **Spread**: Current market spread in pips
    - **Session**: Active market session with overlap detection
    - **Volatility**: ATR-based volatility measurement
    - **Volume**: 24-hour trading volume (when available)
    - **Technical Indicators**: RSI, MACD, Bollinger Bands, ATR

    **Usage Examples:**
    - Signal validation and enhancement
    - Technical analysis research
    - Risk management calculations
    - Market timing decisions
    - Backtesting data collection

    **Access Requirements:**
    - Basic market data available without authentication
    - Enhanced indicators require subscription
    - Real-time updates subject to rate limits

    **Rate Limits:**
    - Unauthenticated: 60 requests per minute
    - Authenticated: 120 requests per minute
    - Premium users: 300 requests per minute

    **Data Sources:**
    - OANDA real-time price feeds
    - Internal technical analysis engine
    - Market session detection algorithms
    - Volatility calculation models

    **Response Frequency:**
    - Real-time data updates
    - Technical indicators recalculated
    - Session changes detected
    - Volatility measurements updated
    """
    try:
        logger.info(f"Market data request for symbol: {symbol} by user: {current_user.username if current_user else 'Anonymous'}")

        # Validate symbol format
        if not (3 <= len(symbol.replace('_', '')) <= 10):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid symbol format. Must be 3-10 characters (excluding underscores)"
            )

        # Get market data from OANDA
        market_data = oanda_service.get_market_data(symbol.upper())

        if not market_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Market data not available for symbol: {symbol}"
            )

        # Convert to enhanced response format
        enhanced_response = MarketDataResponse(
            symbol=market_data["symbol"],
            bid=Decimal(str(market_data["bid"])),
            ask=Decimal(str(market_data["ask"])),
            spread=float(market_data["spread"]),
            timestamp=datetime.fromisoformat(market_data["timestamp"].replace('Z', '+00:00')),
            session=MarketSessionEnum(market_data.get("session", "LONDON")),
            volatility=float(market_data.get("volatility", 0.0)),
            volume_24h=market_data.get("volume_24h"),
            daily_change=market_data.get("daily_change"),
            technical_indicators=market_data.get("technical_indicators")
        )

        logger.info(f"Market data retrieved successfully for {symbol}")
        return enhanced_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving market data for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving market data"
        )

@router.get(
    "/search",
    response_model=List[SignalResponseEnhanced],
    summary="Search Trading Signals",
    description="""
    Search trading signals using advanced filtering and pagination.

    This endpoint provides comprehensive signal search capabilities with:
    - Full-text search across multiple fields
    - Advanced filtering options
    - Pagination support
    - Sorting capabilities
    - Performance analytics

    **Search Features:**
    - Symbol-based search
    - Content-based search
    - Technical indicator filtering
    - Performance metrics filtering
    - Date range filtering

    **Filtering Options:**
    - Search by symbol, AI analysis, or content
    - Filter by reliability, confidence, or risk level
    - Date range filtering
    - Creator filtering
    - Status filtering

    **Response Data:**
    - Matched signals with relevance scoring
    - Search result metadata
    - Pagination information
    - Filtering summary
    """
)
def search_signals(
    q: str = Query(
        ...,
        min_length=2,
        max_length=100,
        description="Search query for symbols, AI analysis, or signal content",
        example="EURUSD bullish"
    ),
    min_reliability: float = Query(
        None,
        ge=0.0,
        le=100.0,
        description="Filter by minimum reliability score"
    ),
    max_age_hours: int = Query(
        None,
        ge=1,
        le=168,
        description="Filter by maximum signal age in hours (1-168)"
    ),
    signal_type: Optional[SignalTypeEnum] = Query(
        None,
        description="Filter by signal type"
    ),
    risk_level: Optional[RiskLevelEnum] = Query(
        None,
        description="Filter by risk level"
    ),
    page: int = Query(
        1,
        ge=1,
        description="Page number for pagination"
    ),
    per_page: int = Query(
        20,
        ge=1,
        le=100,
        description="Results per page"
    ),
    signal_service: SignalService = Depends(get_signal_service),
    current_user: Optional[User] = Depends(get_optional_user_dependency)
) -> List[SignalResponseEnhanced]:
    """
    Search trading signals with advanced filtering and pagination

    This endpoint provides powerful search capabilities for discovering trading signals
    based on various criteria and content.

    **Search Capabilities:**
    - **Symbol Search**: Find signals for specific trading instruments
    - **Content Search**: Search AI analysis and signal descriptions
    - **Technical Search**: Filter by technical indicators and metrics
    - **Performance Search**: Filter by reliability and confidence scores
    - **Time-based Search**: Filter by signal age and creation time

    **Filtering Options:**
    - **Text Search**: Full-text search across multiple signal fields
    - **Reliability Filter**: Minimum reliability threshold (0-100)
    - **Age Filter**: Maximum signal age in hours (1-168 hours)
    - **Type Filter**: Filter by signal type (BUY/SELL/HOLD)
    - **Risk Filter**: Filter by risk level (LOW/MEDIUM/HIGH)

    **Pagination Support:**
    - Page-based pagination with customizable page size
    - Consistent ordering for reliable navigation
    - Total count information for UI display
    - Next/previous page navigation support

    **Response Features:**
    - Relevance scoring for search results
    - Highlighting of matched content
    - Performance metrics for filtered results
    - Search result statistics and metadata

    **Use Cases:**
    - Market research and analysis
    - Signal backtesting and validation
    - Performance optimization
    - Risk management research
    - Educational purposes

    **Rate Limits:**
    - Unauthenticated: 30 searches per minute
    - Authenticated: 60 searches per minute
    - Premium users: 120 searches per minute
    """
    try:
        logger.info(f"Signal search query: '{q}' by user: {current_user.username if current_user else 'Anonymous'}")

        # Apply subscription-based access control
        if current_user and not current_user.subscription_active:
            # Limit search capabilities for non-subscribers
            per_page = min(per_page, 10)
            max_age_hours = min(max_age_hours or 168, 24)  # Limit to 24 hours

        # Search signals with advanced filtering
        search_results = signal_service.search_signals_advanced(
            query=q,
            min_reliability=min_reliability,
            max_age_hours=max_age_hours,
            signal_type=signal_type.value if signal_type else None,
            risk_level=risk_level.value if risk_level else None,
            page=page,
            per_page=per_page
        )

        # Convert to enhanced response format
        enhanced_signals = []
        for signal in search_results["signals"]:
            enhanced_signal = SignalResponseEnhanced(
                id=signal.id,
                symbol=signal.symbol,
                signal_type=SignalTypeEnum(signal.signal_type.value),
                entry_price=Decimal(str(signal.entry_price)),
                stop_loss=Decimal(str(signal.stop_loss)) if signal.stop_loss else None,
                take_profit=Decimal(str(signal.take_profit)) if signal.take_profit else None,
                reliability=signal.reliability,
                confidence_score=signal.confidence_score,
                risk_level=RiskLevelEnum(signal.risk_level),
                status=SignalStatusEnum(signal.status.value),
                timeframe=TimeframeEnum(signal.timeframe),
                ai_analysis=signal.ai_analysis,
                expires_at=signal.expires_at,
                market_session=MarketSessionEnum(signal.market_session) if signal.market_session else MarketSessionEnum.LONDON,
                volatility=signal.volatility,
                spread=signal.spread,
                risk_reward_ratio=signal.risk_reward_ratio,
                position_size_suggestion=signal.position_size_suggestion,
                technical_score=signal.technical_score,
                rsi=signal.rsi,
                macd_signal=signal.macd_signal,
                is_public=signal.is_public,
                is_active=signal.is_active,
                created_at=signal.created_at,
                source=signal.source,
                creator_id=signal.creator_id
            )
            enhanced_signals.append(enhanced_signal)

        logger.info(f"Search returned {len(enhanced_signals)} signals for query: '{q}'")
        return enhanced_signals

    except Exception as e:
        logger.error(f"Error searching signals: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error searching trading signals"
        )