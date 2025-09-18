from fastapi import Depends
from sqlalchemy.orm import Session

from app.services.auth_service import AuthService
from app.services.signal_service import SignalService
from app.services.user_service import UserService
from app.services.oanda_service import OANDAService
from .database import get_db


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """
    Dependency to get authentication service.

    Args:
        db: Database session

    Returns:
        AuthService instance
    """
    return AuthService(db)


def get_signal_service(db: Session = Depends(get_db)) -> SignalService:
    """
    Dependency to get signal service.

    Args:
        db: Database session

    Returns:
        SignalService instance
    """
    return SignalService(db)


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """
    Dependency to get user service.

    Args:
        db: Database session

    Returns:
        UserService instance
    """
    return UserService(db)


def get_oanda_service(db: Session = Depends(get_db)) -> OANDAService:
    """
    Dependency to get OANDA service.

    Args:
        db: Database session

    Returns:
        OANDAService instance
    """
    return OANDAService(db)