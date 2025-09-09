# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

This is a distributed AI trading system with two main components:

### Railway Frontend (`frontend/` directory)
- **Framework**: FastAPI with Jinja2 templates
- **Database**: PostgreSQL (Railway hosted)
- **Purpose**: Web dashboard for user management, signal display, and VPS communication
- **Key Files**:
  - `main.py`: Main FastAPI application server
  - `jwt_auth.py`: JWT authentication system
  - `email_utils.py`: Email handling (registration confirmations)
  - `models.py`: SQLAlchemy ORM models (User, Signal, VPSHeartbeat, etc.)
  - `HTML templates`: Web interface pages (dashboard, login, register, signals)

### VPS Backend (`VPS INSTALLAZIONE/` directory)
- **Framework**: Python 3.8+ with FastAPI
- **Database**: Local SQLite
- **Purpose**: Trading engine with MT5 integration and AI signal analysis
- **Key Files**:
  - `vps_main_server.py`: Main VPS FastAPI server
  - `auto_trader.py`: Trading automation logic
  - `signal_engine.py`: AI signal generation and analysis
  - `mt5_bridge_vps/`: MT5 integration modules
  - `ml_data_storage.py`: Machine learning data management

## Common Development Commands

### Frontend Development
```bash
# Install dependencies
pip install -r frontend/requirements.txt

# Run development server (frontend only)
cd frontend && uvicorn main:app --reload --host 127.0.0.1 --port 8000

# VPS integration testing
python frontend/test_vps_endpoints.py

# Database management
python frontend/reset_database.py  # Reset development database
```

### VPS Backend Setup (Windows VPS)
```bash
# Deploy VPS system
# 1. Upload "VPS INSTALLAZIONE" folder to Windows VPS
# 2. Run installer
./quick_installer.bat

# 3. Configure environment
edit .env_vps

# 4. Start VPS system
python vps_auto_launcher.py
```

## Project Architecture

### Communication Flow
```
                        +-------------------+
                        |   Railway VPS     |
                        |   (Web Frontend)  |
                        +-------------------+
                                ^
                                |
                        API Communication
                                |
                                v
                        +-------------------+
                        |   Windows VPS     |
                        |   (Trading Engine)|
                        +-------------------+
```

### API Endpoints (Key Ones)
- `POST /api/signals/receive`: Receive trading signals from VPS
- `POST /api/vps/heartbeat`: VPS heartbeat monitoring
- `GET /api/signals/latest`: Get latest signals for dashboard
- `GET /health`: System health check

### Environment Variables Required
#### Railway Frontend
- `DATABASE_URL`: PostgreSQL connection string
- `JWT_SECRET_KEY`: JWT encryption key
- `EMAIL_HOST`, `EMAIL_USER`, `EMAIL_PASSWORD`: Email configuration
- `VPS_API_KEY`: VPS communication authentication
- `GEMINI_API_KEY`: Google Gemini AI API key

#### VPS Backend
- `MT5_LOGIN`, `MT5_PASSWORD`, `MT5_SERVER`: MT5 credentials
- `VPS_API_KEY`: API key for Railway communication
- `GEMINI_API_KEY`: AI signal generation