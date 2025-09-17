# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

This is an AI trading system with OANDA integration for real-time market data and signal generation.

### Railway Application (`frontend/` directory)
- **Framework**: FastAPI with Jinja2 templates
- **Database**: PostgreSQL (Railway hosted)
- **Data Source**: OANDA REST API
- **Purpose**: Complete trading signals platform with AI analysis
- **Key Files**:
  - `main.py`: Main FastAPI application server
  - `jwt_auth.py`: JWT authentication system
  - `email_utils.py`: Email handling (registration confirmations)
  - `models.py`: SQLAlchemy ORM models (User, Signal, OANDAConnection, etc.)
  - `oanda_api_integration.py`: OANDA REST API client
  - `oanda_signal_engine.py`: AI-powered signal generation engine
  - `HTML templates`: Web interface pages (dashboard, login, register, signals)

## Common Development Commands

### Application Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn main:app --reload --host 127.0.0.1 --port 8000

# Database management
python frontend/reset_database.py  # Reset development database (if available)
```

## Project Architecture

### System Flow
```
                        +-------------------+
                        |   Railway App     |
                        |   (FastAPI)       |
                        +-------------------+
                                ^
                                |
                        OANDA REST API
                                |
                                v
                        +-------------------+
                        |   OANDA Servers   |
                        |   (Market Data)   |
                        +-------------------+
```

### API Endpoints (Key Ones)
- `POST /admin/generate-signals`: Generate trading signals using OANDA (admin only)
- `GET /api/generate-signals-if-needed`: Auto-generate signals if needed
- `GET /api/signals/latest`: Get latest signals for dashboard
- `GET /health`: System health check

### Environment Variables Required
- `DATABASE_URL`: PostgreSQL connection string
- `JWT_SECRET_KEY`: JWT encryption key
- `EMAIL_HOST`, `EMAIL_USER`, `EMAIL_PASSWORD`: Email configuration
- `OANDA_API_KEY`: OANDA API authentication key
- `OANDA_ACCOUNT_ID`: OANDA account ID
- `OANDA_ENVIRONMENT`: demo or live environment
- `GEMINI_API_KEY`: Google Gemini AI API key

## OANDA Integration Features

### Real-time Market Data
- Live price feeds for major currency pairs
- Historical candlestick data
- Market sentiment analysis
- Session detection and volatility metrics

### AI Signal Generation
- Technical analysis (RSI, MACD, Bollinger Bands, ATR)
- Multi-timeframe analysis
- AI-powered market commentary via Google Gemini
- Professional risk management with stop-loss/take-profit levels

### Risk Management
- ATR-based position sizing
- Dynamic risk levels based on market volatility
- Risk/reward ratio optimization
- Market session-aware adjustments

## Testing and Deployment

The system is designed to run on Railway with PostgreSQL database and includes:
- Automatic OANDA engine initialization on startup
- Error handling and fallback mechanisms
- Production-ready logging and monitoring
- CORS configuration for web access

All VPS dependencies have been removed and replaced with OANDA API integration for reliable, cloud-based signal generation.