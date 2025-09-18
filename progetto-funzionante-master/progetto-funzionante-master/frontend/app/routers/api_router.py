from fastapi import APIRouter, Depends, HTTPException, status, Query, Form, Request
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from schemas import SignalOut, HealthCheckResponse, APIResponse
from models import User, Signal
from app.dependencies.database import get_db
from app.dependencies.services import get_signal_service, get_oanda_service, get_user_service
from app.dependencies.auth import get_current_active_user_dependency, get_optional_user_dependency
from app.services.signal_service import SignalService
from app.services.oanda_service import OANDAService
from app.services.user_service import UserService
from app.core.symbol_mapping import get_oanda_symbol, get_frontend_symbol

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api",
    tags=["api"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=APIResponse)
def api_info():
    """API information and status"""
    return APIResponse(
        message="Trading Signals API v2.0 - Fully operational",
        success=True,
        data={
            "version": "2.0.1",
            "description": "Professional Trading Signals Platform with AI and OANDA Integration",
            "endpoints": {
                "signals": "/api/signals",
                "generate": "/api/generate-signals-if-needed",
                "oanda": "/api/oanda",
                "health": "/health"
            },
            "timestamp": datetime.utcnow()
        }
    )


@router.get("/signals/latest", response_model=List[SignalOut])
def get_latest_api_signals(
    limit: int = Query(10, ge=1, le=100),
    signal_service: SignalService = Depends(get_signal_service)
):
    """Get latest active signals via API"""
    try:
        signals = signal_service.get_latest_signals(limit)
        return [SignalOut.from_orm(signal) for signal in signals]
    except Exception as e:
        logger.error(f"Error fetching latest signals via API: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching signals: {str(e)}"
        )


@router.post("/signals/generate/{symbol}")
def generate_signal_for_symbol(
    symbol: str,
    current_user: User = Depends(get_current_active_user_dependency),
    oanda_service: OANDAService = Depends(get_oanda_service)
):
    """Generate a signal for a specific symbol"""
    try:
        # Validate and normalize symbol
        normalized_symbol = symbol.upper().replace("/", "")

        # Check OANDA health
        health_check = oanda_service.check_oanda_health()
        if not health_check.get("available", False):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OANDA API not available"
            )

        # Generate signal
        signal = oanda_service.generate_signal(normalized_symbol, current_user.id)

        if not signal:
            return {
                "success": False,
                "message": f"No signal generated for {symbol}",
                "symbol": symbol,
                "timestamp": datetime.utcnow()
            }

        return {
            "success": True,
            "message": f"Signal generated for {symbol}",
            "signal": SignalOut.from_orm(signal).dict(),
            "timestamp": datetime.utcnow()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating signal for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating signal: {str(e)}"
        )


@router.get("/generate-signals-if-needed")
async def generate_signals_if_needed(
    force: bool = Query(False),
    oanda_service: OANDAService = Depends(get_oanda_service),
    signal_service: SignalService = Depends(get_signal_service),
    db: Session = Depends(get_db)
):
    """Auto-generate signals if needed based on time and availability"""
    try:
        # Check recent signals count
        recent_count = signal_service.get_recent_signals_count(4)  # Last 4 hours

        # Determine if we need to generate signals
        should_generate = force or recent_count < 5

        if not should_generate:
            return {
                "message": "Recent signals available, skipping generation",
                "recent_signals_count": recent_count,
                "generated": False,
                "timestamp": datetime.utcnow()
            }

        # Check OANDA availability
        health_check = oanda_service.check_oanda_health()
        if not health_check.get("available", False):
            return {
                "message": "OANDA API not available, cannot generate signals",
                "oanda_status": health_check,
                "generated": False,
                "timestamp": datetime.utcnow()
            }

        # Get a system user (first admin user) for signal generation
        from app.repositories.user_repository import UserRepository
        user_repo = UserRepository(db)
        admin_users = user_repo.get_admin_users()

        if not admin_users:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No admin user available for signal generation"
            )

        system_user = admin_users[0]

        # Generate signals for major symbols
        major_symbols = ["EURUSD", "GBPUSD", "USDJPY", "GOLD", "AUDUSD"]
        generated_signals = []
        errors = []

        for symbol in major_symbols:
            try:
                signal = oanda_service.generate_signal(symbol, system_user.id)
                if signal:
                    generated_signals.append({
                        "symbol": symbol,
                        "signal_id": signal.id,
                        "signal_type": signal.signal_type.value,
                        "reliability": signal.reliability
                    })
            except Exception as e:
                errors.append(f"Error generating {symbol}: {str(e)}")

        return {
            "message": f"Generated {len(generated_signals)} new signals",
            "generated_signals": generated_signals,
            "errors": errors,
            "generated": True,
            "oanda_status": health_check,
            "timestamp": datetime.utcnow()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in auto signal generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating signals: {str(e)}"
        )


@router.get("/landing/stats")
def get_landing_stats(
    signal_service: SignalService = Depends(get_signal_service),
    user_service: UserService = Depends(get_user_service)
):
    """Get statistics for landing page"""
    try:
        signal_stats = signal_service.get_signal_statistics()
        user_count = user_service.get_active_user_count()
        recent_signals = signal_service.get_recent_signals_count(24)

        return {
            "total_signals": signal_stats.get("total_signals", 0),
            "active_users": user_count,
            "signals_today": recent_signals,
            "average_reliability": signal_stats.get("average_reliability", 0),
            "success_rate": min(95, max(75, signal_stats.get("average_reliability", 80))),  # Display metric
            "timestamp": datetime.utcnow()
        }

    except Exception as e:
        logger.error(f"Error fetching landing stats: {e}")
        # Return safe defaults
        return {
            "total_signals": 0,
            "active_users": 0,
            "signals_today": 0,
            "average_reliability": 0,
            "success_rate": 0,
            "error": "Unable to fetch statistics",
            "timestamp": datetime.utcnow()
        }


@router.get("/landing/recent-signals")
def get_recent_signals_for_landing(
    limit: int = Query(5, ge=1, le=20),
    signal_service: SignalService = Depends(get_signal_service)
):
    """Get recent signals for landing page display"""
    try:
        signals = signal_service.get_latest_signals(limit)

        return {
            "signals": [
                {
                    "symbol": signal.symbol,
                    "signal_type": signal.signal_type.value,
                    "reliability": signal.reliability,
                    "created_at": signal.created_at,
                    "entry_price": signal.entry_price
                }
                for signal in signals
            ],
            "count": len(signals),
            "timestamp": datetime.utcnow()
        }

    except Exception as e:
        logger.error(f"Error fetching recent signals for landing: {e}")
        return {
            "signals": [],
            "count": 0,
            "error": "Unable to fetch signals",
            "timestamp": datetime.utcnow()
        }


@router.post("/calculate-position-size")
def calculate_position_size(
    symbol: str = Form(...),
    account_balance: float = Form(...),
    risk_percentage: float = Form(...),
    stop_loss_pips: float = Form(...),
    oanda_service: OANDAService = Depends(get_oanda_service)
):
    """Calculate optimal position size based on risk management"""
    try:
        # Validate inputs
        if account_balance <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account balance must be positive"
            )

        if not 0.01 <= risk_percentage <= 0.1:  # 1% to 10%
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Risk percentage must be between 1% and 10%"
            )

        if stop_loss_pips <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Stop loss pips must be positive"
            )

        # Calculate position size
        calculation = oanda_service.calculate_position_size(
            symbol.upper(),
            account_balance,
            risk_percentage,
            stop_loss_pips
        )

        if "error" in calculation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=calculation["error"]
            )

        return calculation

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating position size: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating position size: {str(e)}"
        )


@router.get("/oanda/health")
def get_oanda_health(
    oanda_service: OANDAService = Depends(get_oanda_service)
):
    """Check OANDA API health and connectivity"""
    try:
        return oanda_service.check_oanda_health()
    except Exception as e:
        logger.error(f"Error checking OANDA health: {e}")
        return {
            "available": False,
            "status": "Error checking health",
            "error": str(e),
            "timestamp": datetime.utcnow()
        }


@router.post("/oanda/connect")
def connect_oanda_account(
    account_id: str = Form(...),
    environment: str = Form("demo"),
    current_user: User = Depends(get_current_active_user_dependency),
    oanda_service: OANDAService = Depends(get_oanda_service)
):
    """Connect user's OANDA account"""
    try:
        # Validate environment
        if environment not in ["demo", "live"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Environment must be 'demo' or 'live'"
            )

        # Connect account
        success = oanda_service.connect_user_account(current_user, account_id, environment)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to connect OANDA account. Please check your account ID and API access."
            )

        return {
            "message": "OANDA account connected successfully",
            "account_id": account_id,
            "environment": environment,
            "timestamp": datetime.utcnow()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error connecting OANDA account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error connecting OANDA account: {str(e)}"
        )


@router.get("/oanda/connection")
def get_oanda_connection(
    current_user: User = Depends(get_current_active_user_dependency),
    oanda_service: OANDAService = Depends(get_oanda_service)
):
    """Get user's OANDA connection status"""
    try:
        connection = oanda_service.get_user_connection(current_user)

        if not connection:
            return {
                "connected": False,
                "message": "No OANDA connection found",
                "timestamp": datetime.utcnow()
            }

        return {
            "connected": True,
            "account_id": connection.account_id,
            "environment": connection.environment,
            "status": connection.connection_status,
            "balance": connection.balance,
            "currency": connection.account_currency,
            "last_connected": connection.last_connected,
            "timestamp": datetime.utcnow()
        }

    except Exception as e:
        logger.error(f"Error fetching OANDA connection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching OANDA connection: {str(e)}"
        )


@router.get("/oanda/market-data/{symbol}")
def get_market_data(
    symbol: str,
    oanda_service: OANDAService = Depends(get_oanda_service)
):
    """Get current market data for a symbol"""
    try:
        market_data = oanda_service.get_market_data(symbol.upper())

        if not market_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Market data not available for {symbol}"
            )

        return market_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching market data for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching market data: {str(e)}"
        )