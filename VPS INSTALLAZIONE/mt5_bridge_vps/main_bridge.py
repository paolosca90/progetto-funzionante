import os
import MetaTrader5 as mt5
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import logging
from dotenv import load_dotenv

load_dotenv()

# Configuration
API_KEY = os.getenv("API_KEY", "your-bridge-api-key-change-this")
MT5_TERMINAL_PATH = os.getenv("MT5_TERMINAL_PATH", "")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Setup logging
logging.basicConfig(level=getattr(logging, LOG_LEVEL.upper()))
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="MT5 Bridge API",
    description="MetaTrader 5 Bridge Service",
    version="1.0.0"
)

# CORS - restrict in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global MT5 state
mt5_initialized = False
current_login = None

# === MODELS ===

class LoginRequest(BaseModel):
    login: int
    password: str
    server: str
    timeout: int = 60000

class OrderRequest(BaseModel):
    action: str  # BUY/SELL
    symbol: str
    volume: float
    price: Optional[float] = None
    sl: Optional[float] = None
    tp: Optional[float] = None
    comment: Optional[str] = "API Order"

class RatesRequest(BaseModel):
    symbol: str
    timeframe: str  # M1, M5, H1, D1
    count: int = 100
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

# === SECURITY ===

def verify_api_key(x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return x_api_key

# === UTILITY FUNCTIONS ===

def timeframe_to_mt5(timeframe: str) -> int:
    """Convert string timeframe to MT5 constant"""
    timeframes = {
        "M1": mt5.TIMEFRAME_M1,
        "M5": mt5.TIMEFRAME_M5,
        "M15": mt5.TIMEFRAME_M15,
        "M30": mt5.TIMEFRAME_M30,
        "H1": mt5.TIMEFRAME_H1,
        "H4": mt5.TIMEFRAME_H4,
        "D1": mt5.TIMEFRAME_D1,
        "W1": mt5.TIMEFRAME_W1,
        "MN1": mt5.TIMEFRAME_MN1
    }
    return timeframes.get(timeframe, mt5.TIMEFRAME_H1)

def get_mt5_error():
    """Get last MT5 error"""
    error = mt5.last_error()
    return {"code": error[0], "description": error[1]} if error else None

# === ENDPOINTS ===

@app.get("/")
def root():
    return {
        "service": "MT5 Bridge API",
        "version": "1.0.0",
        "status": "active",
        "mt5_initialized": mt5_initialized,
        "current_login": current_login
    }

@app.get("/health")
def health_check():
    global mt5_initialized

    # Check if MT5 is still connected
    if mt5_initialized:
        account_info = mt5.account_info()
        if account_info is None:
            mt5_initialized = False

    return {
        "status": "healthy",
        "mt5_initialized": mt5_initialized,
        "current_login": current_login,
        "timestamp": datetime.utcnow()
    }

@app.post("/bridge/initialize")
def initialize_mt5(api_key: str = Depends(verify_api_key)):
    """Initialize MT5 terminal"""
    global mt5_initialized

    try:
        if not mt5_initialized:
            if MT5_TERMINAL_PATH:
                result = mt5.initialize(path=MT5_TERMINAL_PATH)
            else:
                result = mt5.initialize()

            if result:
                mt5_initialized = True
                logger.info("MT5 initialized successfully")
                return {"status": "success", "message": "MT5 initialized"}
            else:
                error = get_mt5_error()
                logger.error(f"MT5 initialization failed: {error}")
                raise HTTPException(status_code=500, detail=f"MT5 initialization failed: {error}")
        else:
            return {"status": "success", "message": "MT5 already initialized"}

    except Exception as e:
        logger.error(f"Error initializing MT5: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error initializing MT5: {str(e)}")

@app.post("/bridge/login")
def login_mt5(request: LoginRequest, api_key: str = Depends(verify_api_key)):
    """Login to MT5 account"""
    global current_login, mt5_initialized

    try:
        # Initialize if not done
        if not mt5_initialized:
            initialize_mt5()

        # Attempt login
        result = mt5.login(
            login=request.login,
            password=request.password,
            server=request.server,
            timeout=request.timeout
        )

        if result:
            current_login = request.login
            account_info = mt5.account_info()
            if account_info:
                logger.info(f"Login successful for account {request.login}")
                return {
                    "status": "success",
                    "message": "Login successful",
                    "login": request.login,
                    "server": request.server,
                    "account_info": {
                        "name": account_info.name,
                        "server": account_info.server,
                        "currency": account_info.currency,
                        "balance": account_info.balance,
                        "equity": account_info.equity,
                        "margin": account_info.margin,
                        "free_margin": account_info.margin_free,
                        "margin_level": account_info.margin_level
                    }
                }
            else:
                error = get_mt5_error()
                raise HTTPException(status_code=500, detail=f"Failed to get account info: {error}")
        else:
            error = get_mt5_error()
            logger.error(f"Login failed for account {request.login}: {error}")
            raise HTTPException(status_code=401, detail=f"Login failed: {error}")

    except Exception as e:
        logger.error(f"Error during login: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error during login: {str(e)}")

@app.get("/bridge/account")
def get_account_info(api_key: str = Depends(verify_api_key)):
    """Get current account information"""
    try:
        if not mt5_initialized:
            raise HTTPException(status_code=400, detail="MT5 not initialized")

        account_info = mt5.account_info()
        if account_info is None:
            error = get_mt5_error()
            raise HTTPException(status_code=500, detail=f"Failed to get account info: {error}")

        return {
            "status": "success",
            "account_info": {
                "login": account_info.login,
                "name": account_info.name,
                "server": account_info.server,
                "currency": account_info.currency,
                "balance": account_info.balance,
                "equity": account_info.equity,
                "profit": account_info.profit,
                "margin": account_info.margin,
                "free_margin": account_info.margin_free,
                "margin_level": account_info.margin_level,
                "trade_allowed": account_info.trade_allowed,
                "trade_expert": account_info.trade_expert
            }
        }

    except Exception as e:
        logger.error(f"Error getting account info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting account info: {str(e)}")

@app.get("/bridge/symbols")
def get_symbols(api_key: str = Depends(verify_api_key)):
    """Get available symbols"""
    try:
        if not mt5_initialized:
            raise HTTPException(status_code=400, detail="MT5 not initialized")

        symbols = mt5.symbols_get()
        if symbols is None:
            error = get_mt5_error()
            raise HTTPException(status_code=500, detail=f"Failed to get symbols: {error}")

        symbol_list = []
        for symbol in symbols:
            symbol_list.append({
                "name": symbol.name,
                "description": symbol.description,
                "path": symbol.path,
                "currency_base": symbol.currency_base,
                "currency_profit": symbol.currency_profit,
                "currency_margin": symbol.currency_margin,
                "digits": symbol.digits,
                "point": symbol.point,
                "spread": symbol.spread,
                "visible": symbol.visible,
                "select": symbol.select
            })

        return {
            "status": "success",
            "symbols": symbol_list[:50]  # Limit to first 50 for performance
        }

    except Exception as e:
        logger.error(f"Error getting symbols: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting symbols: {str(e)}")

@app.post("/bridge/rates")
def get_rates(request: RatesRequest, api_key: str = Depends(verify_api_key)):
    """Get historical rates for symbol"""
    try:
        if not mt5_initialized:
            raise HTTPException(status_code=400, detail="MT5 not initialized")

        # Enable symbol if not selected
        if not mt5.symbol_select(request.symbol, True):
            error = get_mt5_error()
            raise HTTPException(status_code=400, detail=f"Failed to select symbol {request.symbol}: {error}")

        timeframe = timeframe_to_mt5(request.timeframe)

        # Get rates based on parameters
        if request.date_from and request.date_to:
            rates = mt5.copy_rates_range(request.symbol, timeframe, request.date_from, request.date_to)
        elif request.date_from:
            rates = mt5.copy_rates_from(request.symbol, timeframe, request.date_from, request.count)
        else:
            rates = mt5.copy_rates_from_pos(request.symbol, timeframe, 0, request.count)

        if rates is None:
            error = get_mt5_error()
            raise HTTPException(status_code=500, detail=f"Failed to get rates: {error}")

        # Convert to list of dicts
        rates_list = []
        for rate in rates:
            rates_list.append({
                "time": datetime.fromtimestamp(rate['time']),
                "open": float(rate['open']),
                "high": float(rate['high']),
                "low": float(rate['low']),
                "close": float(rate['close']),
                "tick_volume": int(rate['tick_volume']),
                "spread": int(rate['spread']),
                "real_volume": int(rate['real_volume'])
            })

        return {
            "status": "success",
            "symbol": request.symbol,
            "timeframe": request.timeframe,
            "count": len(rates_list),
            "rates": rates_list
        }

    except Exception as e:
        logger.error(f"Error getting rates: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting rates: {str(e)}")

@app.get("/bridge/positions")
def get_positions(api_key: str = Depends(verify_api_key)):
    """Get current positions"""
    try:
        if not mt5_initialized:
            raise HTTPException(status_code=400, detail="MT5 not initialized")

        positions = mt5.positions_get()
        if positions is None:
            error = get_mt5_error()
            return {"status": "success", "positions": []}  # No positions is not an error

        positions_list = []
        for pos in positions:
            positions_list.append({
                "ticket": pos.ticket,
                "symbol": pos.symbol,
                "type": pos.type,
                "volume": pos.volume,
                "price_open": pos.price_open,
                "price_current": pos.price_current,
                "profit": pos.profit,
                "swap": pos.swap,
                "comment": pos.comment,
                "time": datetime.fromtimestamp(pos.time)
            })

        return {
            "status": "success",
            "positions": positions_list
        }

    except Exception as e:
        logger.error(f"Error getting positions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting positions: {str(e)}")

@app.post("/bridge/logout")
def logout_mt5(api_key: str = Depends(verify_api_key)):
    """Logout and shutdown MT5"""
    global mt5_initialized, current_login

    try:
        if mt5_initialized:
            mt5.shutdown()
            mt5_initialized = False
            current_login = None
            logger.info("MT5 shutdown successful")
            return {"status": "success", "message": "MT5 logout and shutdown successful"}
        else:
            return {"status": "success", "message": "MT5 not initialized"}

    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error during logout: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
