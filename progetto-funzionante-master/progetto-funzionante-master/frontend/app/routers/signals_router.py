from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from schemas import SignalCreate, SignalOut, SignalResponse, TopSignalsResponse, SignalFilter
from models import User, Signal
from app.dependencies.database import get_db
from app.dependencies.services import get_signal_service, get_oanda_service
from app.dependencies.auth import get_current_active_user_dependency, get_optional_user_dependency
from app.services.signal_service import SignalService
from app.services.oanda_service import OANDAService

router = APIRouter(
    prefix="/signals",
    tags=["signals"],
    responses={404: {"description": "Not found"}},
)


@router.get("/latest", response_model=List[SignalOut])
def get_latest_signals(
    limit: int = Query(10, ge=1, le=100, description="Maximum number of signals to return"),
    signal_service: SignalService = Depends(get_signal_service),
    current_user: Optional[User] = Depends(get_optional_user_dependency)
) -> List[SignalOut]:
    """Get latest active signals

    Args:
        limit: Maximum number of signals to return (1-100)
        signal_service: Signal service dependency
        current_user: Currently authenticated user (optional)

    Returns:
        List[SignalOut]: List of latest active signals

    Raises:
        HTTPException: If signal fetching fails
    """
    try:
        signals = signal_service.get_latest_signals(limit)
        return [SignalOut.from_orm(signal) for signal in signals]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching latest signals: {str(e)}"
        )


@router.get("/top", response_model=TopSignalsResponse)
def get_top_signals(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of top signals to return"),
    signal_service: SignalService = Depends(get_signal_service)
) -> TopSignalsResponse:
    """Get top performing signals based on reliability

    Args:
        limit: Maximum number of signals to return (1-50)
        signal_service: Signal service dependency

    Returns:
        TopSignalsResponse: Response containing top signals and statistics

    Raises:
        HTTPException: If signal fetching fails
    """
    try:
        return signal_service.get_top_signals(limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching top signals: {str(e)}"
        )


@router.get("/", response_model=List[SignalOut])
def get_signals(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    symbol: Optional[str] = Query(None),
    signal_type: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    signal_service: SignalService = Depends(get_signal_service)
):
    """Get signals with filtering options"""
    try:
        if symbol:
            signals = signal_service.get_signals_by_symbol(symbol, limit)
        elif signal_type:
            signals = signal_service.get_signals_by_type(signal_type, limit)
        elif risk_level:
            signals = signal_service.get_signals_by_risk_level(risk_level, limit)
        elif source:
            signals = signal_service.get_signals_by_source(source, limit)
        else:
            signals = signal_service.get_public_signals(limit)

        return [SignalOut.from_orm(signal) for signal in signals]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching signals: {str(e)}"
        )


@router.post("/", response_model=SignalResponse, status_code=status.HTTP_201_CREATED)
def create_signal(
    signal: SignalCreate,
    current_user: User = Depends(get_current_active_user_dependency),
    signal_service: SignalService = Depends(get_signal_service)
):
    """Create a new trading signal"""
    try:
        created_signal = signal_service.create_signal(signal, current_user.id)

        return SignalResponse(
            signal=SignalOut.from_orm(created_signal),
            message="Signal created successfully",
            success=True
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating signal: {str(e)}"
        )


@router.get("/by-symbol/{symbol}", response_model=List[SignalOut])
def get_signals_by_symbol(
    symbol: str,
    limit: int = Query(10, ge=1, le=100),
    signal_service: SignalService = Depends(get_signal_service)
):
    """Get signals for a specific trading symbol"""
    try:
        signals = signal_service.get_signals_by_symbol(symbol.upper(), limit)
        return [SignalOut.from_orm(signal) for signal in signals]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching signals for {symbol}: {str(e)}"
        )


@router.get("/search", response_model=List[SignalOut])
def search_signals(
    q: str = Query(..., min_length=2),
    limit: int = Query(100, ge=1, le=1000),
    signal_service: SignalService = Depends(get_signal_service)
):
    """Search signals by symbol or content"""
    try:
        signals = signal_service.search_signals(q, limit)
        return [SignalOut.from_orm(signal) for signal in signals]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching signals: {str(e)}"
        )


@router.get("/high-confidence", response_model=List[SignalOut])
def get_high_confidence_signals(
    min_confidence: float = Query(0.8, ge=0.0, le=1.0),
    limit: int = Query(100, ge=1, le=1000),
    signal_service: SignalService = Depends(get_signal_service)
):
    """Get signals with high confidence scores"""
    try:
        signals = signal_service.get_high_confidence_signals(min_confidence, limit)
        return [SignalOut.from_orm(signal) for signal in signals]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching high confidence signals: {str(e)}"
        )


@router.get("/by-timeframe/{timeframe}", response_model=List[SignalOut])
def get_signals_by_timeframe(
    timeframe: str,
    limit: int = Query(100, ge=1, le=1000),
    signal_service: SignalService = Depends(get_signal_service)
):
    """Get signals by analysis timeframe"""
    try:
        signals = signal_service.get_signals_by_timeframe(timeframe, limit)
        return [SignalOut.from_orm(signal) for signal in signals]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching signals for timeframe {timeframe}: {str(e)}"
        )


@router.get("/my-signals", response_model=List[SignalOut])
def get_my_signals(
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user_dependency),
    signal_service: SignalService = Depends(get_signal_service)
):
    """Get signals created by the current user"""
    try:
        signals = signal_service.get_user_signals(current_user.id, limit)
        return [SignalOut.from_orm(signal) for signal in signals]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching user signals: {str(e)}"
        )


@router.get("/statistics", response_model=Dict[str, Any])
def get_signal_statistics(
    signal_service: SignalService = Depends(get_signal_service)
):
    """Get overall signal statistics"""
    try:
        return signal_service.get_signal_statistics()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching signal statistics: {str(e)}"
        )


@router.get("/recent-count")
def get_recent_signals_count(
    hours: int = Query(24, ge=1, le=168),  # Max 1 week
    signal_service: SignalService = Depends(get_signal_service)
):
    """Get count of signals created in the last N hours"""
    try:
        count = signal_service.get_recent_signals_count(hours)
        return {"count": count, "hours": hours}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching recent signals count: {str(e)}"
        )


@router.get("/with-executions", response_model=List[SignalOut])
def get_signals_with_executions(
    limit: int = Query(100, ge=1, le=1000),
    signal_service: SignalService = Depends(get_signal_service)
):
    """Get signals that have been executed by users"""
    try:
        signals = signal_service.get_signals_with_executions(limit)
        return [SignalOut.from_orm(signal) for signal in signals]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching signals with executions: {str(e)}"
        )


@router.get("/report")
def generate_signal_report(
    days: int = Query(30, ge=1, le=365),
    signal_service: SignalService = Depends(get_signal_service),
    current_user: User = Depends(get_current_active_user_dependency)
):
    """Generate a comprehensive signal report"""
    try:
        report = signal_service.generate_signal_report(days)
        return report
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating signal report: {str(e)}"
        )


@router.patch("/{signal_id}/close")
def close_signal(
    signal_id: int,
    current_user: User = Depends(get_current_active_user_dependency),
    signal_service: SignalService = Depends(get_signal_service)
):
    """Close a signal"""
    try:
        signal = signal_service.close_signal(signal_id, current_user)
        if not signal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Signal not found or you don't have permission to close it"
            )

        return {"message": "Signal closed successfully", "signal_id": signal_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error closing signal: {str(e)}"
        )


@router.patch("/{signal_id}/cancel")
def cancel_signal(
    signal_id: int,
    current_user: User = Depends(get_current_active_user_dependency),
    signal_service: SignalService = Depends(get_signal_service)
):
    """Cancel a signal"""
    try:
        signal = signal_service.cancel_signal(signal_id, current_user)
        if not signal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Signal not found or you don't have permission to cancel it"
            )

        return {"message": "Signal cancelled successfully", "signal_id": signal_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cancelling signal: {str(e)}"
        )


@router.patch("/{signal_id}/reliability")
def update_signal_reliability(
    signal_id: int,
    reliability: float = Query(..., ge=0.0, le=100.0),
    current_user: User = Depends(get_current_active_user_dependency),
    signal_service: SignalService = Depends(get_signal_service)
):
    """Update signal reliability score"""
    try:
        signal = signal_service.update_signal_reliability(signal_id, reliability, current_user)
        if not signal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Signal not found or you don't have permission to update it"
            )

        return {
            "message": "Signal reliability updated successfully",
            "signal_id": signal_id,
            "new_reliability": reliability
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating signal reliability: {str(e)}"
        )


@router.post("/cleanup-expired")
def cleanup_expired_signals(
    current_user: User = Depends(get_current_active_user_dependency),
    signal_service: SignalService = Depends(get_signal_service)
):
    """Close all expired signals (admin or user's own signals)"""
    try:
        if current_user.is_admin:
            # Admin can cleanup all expired signals
            count = signal_service.cleanup_expired_signals()
            return {"message": f"Closed {count} expired signals", "count": count}
        else:
            # Regular users can only see this info, not perform cleanup
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can perform global signal cleanup"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cleaning up expired signals: {str(e)}"
        )