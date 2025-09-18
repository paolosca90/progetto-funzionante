"""
Enhanced OpenAPI Documentation for Trading Signals API

This module provides comprehensive OpenAPI 3.0 documentation with:
- Detailed request/response models
- Authentication and security schemes
- Error handling documentation
- Trading system specific extensions
- API versioning strategy
- Interactive examples
"""

from fastapi.openapi.utils import get_openapi
from fastapi import FastAPI
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from app.core.openapi_tags import get_openapi_extensions

# Trading system specific OpenAPI extensions
TRADING_SYSTEM_EXTENSIONS = {
    "x-trading-system": {
        "name": "AI Cash Revolution Trading Platform",
        "version": "2.0.1",
        "description": "Professional AI-powered trading signals platform with OANDA integration",
        "features": [
            "Real-time market data analysis",
            "AI-generated trading signals",
            "Multi-timeframe technical analysis",
            "Risk management and position sizing",
            "OANDA API integration",
            "User subscription management",
            "Performance analytics",
            "Backtesting capabilities",
            "Automated execution",
            "Portfolio management"
        ],
        "supported-instruments": {
            "forex": [
                "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD",
                "NZDUSD", "EURGBP", "EURJPY", "GBPJPY", "USDCHF",
                "EURCHF", "GBPCHF", "AUDJPY", "NZDJPY", "CADJPY"
            ],
            "commodities": ["GOLD", "SILVER", "OIL", "COPPER", "NATURAL_GAS"],
            "crypto": ["BTCUSD", "ETHUSD", "LTCUSD", "XRPUSD", "BCHUSD"],
            "indices": ["US30", "US500", "US100", "UK100", "GER30", "JP225"]
        },
        "timeframes": {
            "short_term": ["M1", "M5", "M15"],
            "medium_term": ["M30", "H1", "H4"],
            "long_term": ["D1", "W1", "MN1"],
            "description": "Multiple timeframe analysis for comprehensive trading strategies"
        },
        "risk-management": {
            "risk-levels": ["LOW", "MEDIUM", "HIGH"],
            "position-sizing": "ATR-based dynamic sizing",
            "stop-loss": "Automatic calculation based on volatility",
            "take-profit": "Risk-reward ratio optimization",
            "max-risk-per-trade": "2% of account balance",
            "max-daily-risk": "6% of account balance"
        },
        "signal-types": {
            "directional": ["BUY", "SELL"],
            "neutral": ["HOLD"],
            "complex": ["BUY_LIMIT", "SELL_LIMIT", "BUY_STOP", "SELL_STOP"]
        },
        "ai-models": {
            "primary": "Google Gemini Pro",
            "technical": "Multi-indicator Analysis Engine",
            "risk": "Dynamic Risk Assessment AI",
            "sentiment": "Market Sentiment Analyzer",
            "pattern": "Chart Pattern Recognition AI"
        },
        "technical-indicators": {
            "trend": ["SMA", "EMA", "MACD", "ADX"],
            "momentum": ["RSI", "Stochastic", "CCI", "Williams %R"],
            "volatility": ["Bollinger Bands", "ATR", "Standard Deviation"],
            "volume": ["Volume Profile", "On Balance Volume", "Money Flow Index"]
        },
        "market-sessions": {
            "sydney": {"open": "22:00", "close": "07:00", "timezone": "GMT"},
            "tokyo": {"open": "00:00", "close": "09:00", "timezone": "GMT"},
            "london": {"open": "08:00", "close": "17:00", "timezone": "GMT"},
            "new_york": {"open": "13:00", "close": "22:00", "timezone": "GMT"}
        },
        "performance-metrics": {
            "win-rate": "Percentage of profitable trades",
            "profit-factor": "Ratio of gross profit to gross loss",
            "sharpe-ratio": "Risk-adjusted return metric",
            "max-drawdown": "Maximum peak to trough decline",
            "recovery-factor": "Net profit divided by maximum drawdown"
        }
    },
    "x-oanda-integration": {
        "api-version": "v20",
        "environment": "Demo and Live",
        "data-feeds": ["Real-time pricing", "Historical data", "Economic calendar"],
        "execution": ["Market orders", "Limit orders", "Stop orders", "Trailing stops"],
        "account-features": ["Multi-currency accounts", "Hedging capability", "Margin management"],
        "rate-limits": {
            "requests-per-second": 100,
            "requests-per-minute": 6000,
            "burst-limit": 200
        }
    },
    "x-risk-parameters": {
        "account-risk": {
            "max-daily-drawdown": "10%",
            "max-monthly-drawdown": "20%",
            "min-balance": "1000 USD",
            "leverage-limits": {
                "forex": "1:500",
                "commodities": "1:100",
                "crypto": "1:50",
                "indices": "1:200"
            }
        },
        "trade-risk": {
            "min-risk-reward": "1:1.5",
            "max-position-size": "5% of account",
            "max-concurrent-trades": 10,
            "stop-loss-distance": "ATR * 2",
            "take-profit-distance": "ATR * 3"
        }
    }
}

SECURITY_SCHEMES = {
    "bearerAuth": {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "JWT token obtained from /token endpoint. Include 'Bearer ' prefix in Authorization header."
    }
}

TAGS_METADATA = [
    {
        "name": "authentication",
        "description": "User authentication and registration endpoints",
        "externalDocs": {
            "description": "Authentication Guide",
            "url": "https://docs.example.com/authentication"
        }
    },
    {
        "name": "users",
        "description": "User management and profile endpoints"
    },
    {
        "name": "signals",
        "description": "Trading signals creation, retrieval, and management",
        "externalDocs": {
            "description": "Trading Signals Guide",
            "url": "https://docs.example.com/signals"
        }
    },
    {
        "name": "api",
        "description": "General API endpoints and market data"
    },
    {
        "name": "admin",
        "description": "Administrative endpoints (requires admin privileges)"
    },
    {
        "name": "health",
        "description": "System health and monitoring endpoints"
    },
    {
        "name": "cache",
        "description": "Cache management and performance metrics"
    }
]

EXAMPLES = {
    "user_registration": {
        "username": "trader123",
        "email": "trader@example.com",
        "password": "SecurePass123!",
        "full_name": "John Trader"
    },
    "signal_creation": {
        "symbol": "EURUSD",
        "signal_type": "BUY",
        "entry_price": 1.0850,
        "stop_loss": 1.0820,
        "take_profit": 1.0900,
        "reliability": 85.5,
        "ai_analysis": "Strong bullish momentum detected with RSI oversold bounce",
        "confidence_score": 87.0,
        "risk_level": "MEDIUM",
        "expires_at": "2024-12-31T23:59:59Z"
    },
    "login_request": {
        "username": "trader123",
        "password": "SecurePass123!"
    }
}

ERROR_RESPONSES = {
    400: {
        "description": "Bad Request - Invalid input data",
        "content": {
            "application/json": {
                "example": {
                    "error": "ValidationError",
                    "message": "Invalid input data provided",
                    "details": {
                        "field": "email",
                        "issue": "Invalid email format"
                    },
                    "timestamp": "2024-01-15T10:30:00Z"
                }
            }
        }
    },
    401: {
        "description": "Unauthorized - Authentication required",
        "content": {
            "application/json": {
                "example": {
                    "error": "AuthenticationError",
                    "message": "Invalid authentication credentials",
                    "details": {
                        "token": "Invalid or expired JWT token"
                    },
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
                    "message": "Access denied - insufficient privileges",
                    "details": {
                        "required_role": "admin",
                        "current_role": "user"
                    },
                    "timestamp": "2024-01-15T10:30:00Z"
                }
            }
        }
    },
    404: {
        "description": "Not Found - Resource not found",
        "content": {
            "application/json": {
                "example": {
                    "error": "NotFound",
                    "message": "The requested resource was not found",
                    "details": {
                        "resource": "Signal",
                        "id": 999999
                    },
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
                    "message": "Too many requests - please try again later",
                    "details": {
                        "limit": "10 requests per 15 minutes",
                        "retry_after": 300
                    },
                    "timestamp": "2024-01-15T10:30:00Z"
                }
            }
        }
    },
    500: {
        "description": "Internal Server Error",
        "content": {
            "application/json": {
                "example": {
                    "error": "InternalServerError",
                    "message": "An unexpected error occurred",
                    "details": {
                        "error_id": "ERR-12345",
                        "trace_id": "trace_abc123"
                    },
                    "timestamp": "2024-01-15T10:30:00Z"
                }
            }
        }
    }
}

def custom_openapi(app: FastAPI) -> Dict[str, Any]:
    """Generate custom OpenAPI documentation with trading system extensions"""

    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="AI Cash Revolution Trading API",
        version="2.0.1",
        description=openapi_description,
        routes=app.routes,
    )

    # Add custom extensions
    openapi_schema["info"]["x-logo"] = {
        "url": "https://example.com/logo.png",
        "backgroundColor": "#FFFFFF",
        "altText": "AI Cash Revolution Logo"
    }

    # Add trading system extensions
    openapi_schema.update(TRADING_SYSTEM_EXTENSIONS)

    # Add contact information
    openapi_schema["info"]["contact"] = {
        "name": "API Support",
        "email": "support@cash-revolution.com",
        "url": "https://www.cash-revolution.com/support"
    }

    # Add license information
    openapi_schema["info"]["license"] = {
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    }

    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = SECURITY_SCHEMES

    # Add global security requirement
    openapi_schema["security"] = [{"bearerAuth": []}]

    # Add tags
    openapi_schema["tags"] = TAGS_METADATA

    # Add examples to components
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}

    openapi_schema["components"]["examples"] = {
        "UserRegistrationExample": {
            "summary": "Example user registration request",
            "value": EXAMPLES["user_registration"]
        },
        "SignalCreationExample": {
            "summary": "Example signal creation request",
            "value": EXAMPLES["signal_creation"]
        },
        "LoginRequestExample": {
            "summary": "Example login request",
            "value": EXAMPLES["login_request"]
        }
    }

    # Add error response schemas
    openapi_schema["components"]["schemas"]["ErrorResponse"] = {
        "type": "object",
        "properties": {
            "error": {
                "type": "string",
                "description": "Error type/class",
                "example": "ValidationError"
            },
            "message": {
                "type": "string",
                "description": "Human-readable error message",
                "example": "Invalid input data provided"
            },
            "details": {
                "type": "object",
                "description": "Additional error details",
                "properties": {
                    "field": {"type": "string"},
                    "issue": {"type": "string"},
                    "required_role": {"type": "string"},
                    "current_role": {"type": "string"},
                    "resource": {"type": "string"},
                    "id": {"type": "integer"}
                }
            },
            "timestamp": {
                "type": "string",
                "format": "date-time",
                "description": "Error timestamp"
            }
        },
        "required": ["error", "message", "timestamp"]
    }

    # Add trading system specific schemas
    openapi_schema["components"]["schemas"]["MarketData"] = {
        "type": "object",
        "description": "Real-time market data for a trading instrument",
        "properties": {
            "symbol": {
                "type": "string",
                "description": "Trading symbol",
                "example": "EUR_USD"
            },
            "bid": {
                "type": "number",
                "format": "float",
                "description": "Current bid price"
            },
            "ask": {
                "type": "number",
                "format": "float",
                "description": "Current ask price"
            },
            "spread": {
                "type": "number",
                "format": "float",
                "description": "Current spread"
            },
            "timestamp": {
                "type": "string",
                "format": "date-time",
                "description": "Market data timestamp"
            },
            "session": {
                "type": "string",
                "enum": ["LONDON", "NEW_YORK", "TOKYO", "SYDNEY", "OVERLAP"],
                "description": "Current market session"
            },
            "volatility": {
                "type": "number",
                "format": "float",
                "description": "Current market volatility (ATR-based)"
            }
        }
    }

    # Add server configurations
    openapi_schema["servers"] = [
        {
            "url": "https://api.cash-revolution.com/v1",
            "description": "Production server"
        },
        {
            "url": "https://staging-api.cash-revolution.com/v1",
            "description": "Staging server"
        },
        {
            "url": "http://localhost:8000",
            "description": "Local development server"
        }
    ]

    # Add external documentation
    openapi_schema["externalDocs"] = {
        "description": "AI Cash Revolution API Documentation",
        "url": "https://docs.cash-revolution.com"
    }

    # Add enhanced OpenAPI extensions from tags module
    enhanced_extensions = get_openapi_extensions()
    openapi_schema.update(enhanced_extensions)

    app.openapi_schema = openapi_schema
    return app.openapi_schema

# Detailed OpenAPI description
openapi_description = """
# AI Cash Revolution Trading API

Welcome to the comprehensive API documentation for the AI Cash Revolution Trading Platform.
This API provides access to AI-powered trading signals, real-time market data, and portfolio management features.

## Overview

Our platform combines cutting-edge AI analysis with professional trading expertise to deliver high-quality trading signals. The API is built with FastAPI and follows REST principles with comprehensive OpenAPI documentation.

## Key Features

### 🤖 AI-Powered Analysis
- **Gemini AI Integration**: Advanced market analysis using Google's Gemini AI
- **Multi-Timeframe Analysis**: Signals generated across multiple timeframes (M1 to MN1)
- **Technical Indicators**: Comprehensive technical analysis including RSI, MACD, Bollinger Bands, ATR
- **Market Sentiment**: Real-time sentiment analysis and session-aware signals

### 📊 Professional Trading Signals
- **High Reliability**: Signals with 75-95% reliability scores
- **Risk Management**: Built-in risk assessment with ATR-based position sizing
- **Real-time Data**: Live market data via OANDA API integration
- **Multiple Instruments**: Support for Forex, Commodities, and Cryptocurrencies

### 🔒 Security & Authentication
- **JWT Authentication**: Secure token-based authentication
- **Role-based Access**: User and admin privilege levels
- **Rate Limiting**: Protection against abuse
- **Data Encryption**: Secure data transmission

### 🚀 Performance & Scalability
- **Async Processing**: High-performance async operations
- **Redis Caching**: Intelligent caching for fast responses
- **Database Optimization**: PostgreSQL with comprehensive indexing
- **Health Monitoring**: Real-time system health checks

## Getting Started

1. **Register an Account**: Create an account via the registration endpoint
2. **Get API Token**: Authenticate to receive your JWT token
3. **Start Trading**: Access signals and market data immediately

## Rate Limits

- **Authentication endpoints**: 5 requests per minute
- **General API endpoints**: 100 requests per minute
- **Signal generation**: 10 requests per hour
- **Market data**: 60 requests per minute

## Authentication

All API endpoints require authentication using Bearer tokens. Include your JWT token in the Authorization header:

```
Authorization: Bearer your_jwt_token_here
```

## Error Handling

The API uses standard HTTP status codes and provides detailed error information in the response body. All error responses follow a consistent format with error type, message, details, and timestamp.

## Support

For API support and questions:
- **Email**: support@cash-revolution.com
- **Documentation**: https://docs.cash-revolution.com
- **Status Page**: https://status.cash-revolution.com

---

*API Version: 2.0.1 | Last Updated: January 2024*
"""