from fastapi import APIRouter, Depends, HTTPException, status, Response, Form
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from models import User, Signal
from app.dependencies.database import get_db
from app.dependencies.services import get_signal_service, get_user_service, get_oanda_service
from app.dependencies.auth import get_admin_user_dependency
from app.services.signal_service import SignalService
from app.services.user_service import UserService
from app.services.oanda_service import OANDAService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(get_admin_user_dependency)],
    responses={404: {"description": "Not found"}},
)


@router.post("/generate-signals")
async def generate_signals_manually(
    symbols: Optional[str] = Form(None),  # Comma-separated symbols
    current_user: User = Depends(get_admin_user_dependency),
    oanda_service: OANDAService = Depends(get_oanda_service),
    db: Session = Depends(get_db)
):
    """Generate signals manually using OANDA API (admin only)"""
    try:
        # Check OANDA availability
        health_check = oanda_service.check_oanda_health()
        if not health_check.get("available", False):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"OANDA API not available: {health_check.get('error', 'Unknown error')}"
            )

        # Default symbols if none provided
        if not symbols:
            default_symbols = [
                "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD",
                "NZDUSD", "EURGBP", "EURJPY", "GBPJPY", "GOLD"
            ]
        else:
            default_symbols = [s.strip().upper() for s in symbols.split(",") if s.strip()]

        logger.info(f"Admin {current_user.username} requesting signal generation for: {default_symbols}")

        # Generate signals for each symbol
        generated_signals = []
        errors = []

        for symbol in default_symbols:
            try:
                signal = oanda_service.generate_signal(symbol, current_user.id)
                if signal:
                    generated_signals.append({
                        "symbol": symbol,
                        "signal_id": signal.id,
                        "signal_type": signal.signal_type.value,
                        "entry_price": signal.entry_price,
                        "reliability": signal.reliability,
                        "created_at": signal.created_at
                    })
                    logger.info(f"Generated signal for {symbol}: {signal.id}")
                else:
                    errors.append(f"No signal generated for {symbol}")
            except Exception as e:
                error_msg = f"Error generating signal for {symbol}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)

        return {
            "message": f"Signal generation completed. Generated {len(generated_signals)} signals.",
            "generated_signals": generated_signals,
            "errors": errors,
            "total_requested": len(default_symbols),
            "total_generated": len(generated_signals),
            "oanda_status": health_check
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in manual signal generation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating signals: {str(e)}"
        )


@router.get("/signals-by-source")
async def get_signals_by_source(
    current_user: User = Depends(get_admin_user_dependency),
    signal_service: SignalService = Depends(get_signal_service)
):
    """Admin only: Show all signals grouped by source"""
    try:
        # Get signals by different sources
        oanda_signals = signal_service.get_signals_by_source("OANDA_AI", limit=1000)
        manual_signals = signal_service.get_signals_by_source("MANUAL", limit=1000)
        api_signals = signal_service.get_signals_by_source("API", limit=1000)

        # Get overall statistics
        stats = signal_service.get_signal_statistics()

        return {
            "sources": {
                "OANDA_AI": {
                    "count": len(oanda_signals),
                    "signals": [
                        {
                            "id": s.id,
                            "symbol": s.symbol,
                            "signal_type": s.signal_type.value,
                            "reliability": s.reliability,
                            "created_at": s.created_at,
                            "status": s.status.value
                        }
                        for s in oanda_signals[:50]  # Limit to 50 for display
                    ]
                },
                "MANUAL": {
                    "count": len(manual_signals),
                    "signals": [
                        {
                            "id": s.id,
                            "symbol": s.symbol,
                            "signal_type": s.signal_type.value,
                            "reliability": s.reliability,
                            "created_at": s.created_at,
                            "status": s.status.value
                        }
                        for s in manual_signals[:50]
                    ]
                },
                "API": {
                    "count": len(api_signals),
                    "signals": [
                        {
                            "id": s.id,
                            "symbol": s.symbol,
                            "signal_type": s.signal_type.value,
                            "reliability": s.reliability,
                            "created_at": s.created_at,
                            "status": s.status.value
                        }
                        for s in api_signals[:50]
                    ]
                }
            },
            "overall_stats": stats,
            "timestamp": datetime.utcnow()
        }

    except Exception as e:
        logger.error(f"Error fetching signals by source: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching signals by source: {str(e)}"
        )


@router.post("/migrate-database")
async def migrate_database(
    current_user: User = Depends(get_admin_user_dependency),
    db: Session = Depends(get_db)
):
    """Admin-only endpoint to migrate database schema"""
    try:
        # This would typically run database migrations
        # For now, just return status
        return {
            "message": "Database migration endpoint - Not implemented in refactored version",
            "note": "Database migrations should be handled via alembic or similar tools",
            "admin_user": current_user.username,
            "timestamp": datetime.utcnow()
        }

    except Exception as e:
        logger.error(f"Database migration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database migration error: {str(e)}"
        )


@router.get("/reset-database-confirm")
def reset_database_confirmation(
    current_user: User = Depends(get_admin_user_dependency)
):
    """GET endpoint to confirm database reset (safe - no action, just information)"""
    return {
        "warning": "Database reset is a destructive operation",
        "message": "This endpoint would reset the entire database",
        "admin_user": current_user.username,
        "timestamp": datetime.utcnow(),
        "note": "DANGEROUS OPERATION - Should be removed in production"
    }


@router.post("/reset-database")
async def reset_database_complete(
    confirmation_code: str = Form(...),
    current_user: User = Depends(get_admin_user_dependency)
):
    """DANGEROUS: Admin-only endpoint to completely reset database - REMOVE IN PRODUCTION"""
    # Security check
    if confirmation_code != "RESET_CONFIRM_2025":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid confirmation code"
        )

    try:
        # This would be a destructive operation
        # For safety, not implementing the actual reset in refactored version
        logger.warning(f"Database reset requested by admin {current_user.username}")

        return {
            "warning": "Database reset not implemented in refactored version",
            "message": "For safety, this destructive operation requires manual execution",
            "admin_user": current_user.username,
            "timestamp": datetime.utcnow(),
            "note": "This endpoint should be removed in production"
        }

    except Exception as e:
        logger.error(f"Database reset error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database reset error: {str(e)}"
        )


@router.get("/dashboard")
def get_admin_dashboard(
    current_user: User = Depends(get_admin_user_dependency),
    signal_service: SignalService = Depends(get_signal_service),
    user_service: UserService = Depends(get_user_service),
    oanda_service: OANDAService = Depends(get_oanda_service)
):
    """Get comprehensive admin dashboard data"""
    try:
        # Get system statistics
        signal_stats = signal_service.get_signal_statistics()
        user_stats = {
            "total_users": user_service.get_user_count(),
            "active_users": user_service.get_active_user_count(),
            "admin_users": len(user_service.get_admin_users()),
            "subscribed_users": len(user_service.get_users_with_active_subscription())
        }

        # Get OANDA status
        oanda_health = oanda_service.check_oanda_health()

        # Get recent signals
        recent_signals = signal_service.get_latest_signals(20)

        # Get recent signals count
        recent_24h = signal_service.get_recent_signals_count(24)
        recent_week = signal_service.get_recent_signals_count(168)

        return {
            "signal_statistics": signal_stats,
            "user_statistics": user_stats,
            "oanda_health": oanda_health,
            "recent_activity": {
                "signals_24h": recent_24h,
                "signals_week": recent_week,
                "latest_signals": [
                    {
                        "id": s.id,
                        "symbol": s.symbol,
                        "signal_type": s.signal_type.value,
                        "reliability": s.reliability,
                        "source": s.source,
                        "created_at": s.created_at
                    }
                    for s in recent_signals
                ]
            },
            "system_info": {
                "admin_user": current_user.username,
                "timestamp": datetime.utcnow(),
                "version": "2.0.1"
            }
        }

    except Exception as e:
        logger.error(f"Error fetching admin dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching admin dashboard: {str(e)}"
        )


@router.get("/system-health")
def get_system_health(
    current_user: User = Depends(get_admin_user_dependency),
    oanda_service: OANDAService = Depends(get_oanda_service),
    db: Session = Depends(get_db)
):
    """Get overall system health status"""
    try:
        # Check database connectivity
        try:
            db.execute("SELECT 1")
            db_status = {"status": "healthy", "message": "Database connection OK"}
        except Exception as e:
            db_status = {"status": "unhealthy", "message": f"Database error: {str(e)}"}

        # Check OANDA API
        oanda_health = oanda_service.check_oanda_health()

        # Overall system status
        overall_healthy = (
            db_status["status"] == "healthy" and
            oanda_health.get("available", False)
        )

        return {
            "overall_status": "healthy" if overall_healthy else "degraded",
            "components": {
                "database": db_status,
                "oanda_api": oanda_health,
            },
            "timestamp": datetime.utcnow(),
            "checked_by": current_user.username
        }

    except Exception as e:
        logger.error(f"Error checking system health: {e}")
        return {
            "overall_status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow(),
            "checked_by": current_user.username
        }


@router.post("/cleanup-expired-signals")
def cleanup_expired_signals(
    current_user: User = Depends(get_admin_user_dependency),
    signal_service: SignalService = Depends(get_signal_service)
):
    """Close all expired signals (admin only)"""
    try:
        count = signal_service.cleanup_expired_signals()
        logger.info(f"Admin {current_user.username} cleaned up {count} expired signals")

        return {
            "message": f"Successfully closed {count} expired signals",
            "count": count,
            "admin_user": current_user.username,
            "timestamp": datetime.utcnow()
        }

    except Exception as e:
        logger.error(f"Error cleaning up expired signals: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cleaning up expired signals: {str(e)}"
        )