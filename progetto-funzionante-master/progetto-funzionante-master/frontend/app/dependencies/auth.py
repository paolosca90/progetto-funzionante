from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional

from jwt_auth import get_current_user, get_current_active_user
from models import User
from .database import get_db

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_current_user_dependency(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    Dependency to get current authenticated user.

    Args:
        db: Database session
        token: JWT token from request

    Returns:
        Current user object

    Raises:
        HTTPException: If authentication fails
    """
    user = get_current_user(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_current_active_user_dependency(
    current_user: User = Depends(get_current_user_dependency)
) -> User:
    """
    Dependency to get current active user.

    Args:
        current_user: Current authenticated user

    Returns:
        Current active user object

    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def get_admin_user_dependency(
    current_user: User = Depends(get_current_active_user_dependency)
) -> User:
    """
    Dependency to get current admin user.

    Args:
        current_user: Current active user

    Returns:
        Current admin user object

    Raises:
        HTTPException: If user is not admin
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


def get_optional_user_dependency(
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme)
) -> Optional[User]:
    """
    Dependency to get current user if authenticated, None otherwise.

    Args:
        db: Database session
        token: JWT token from request (optional)

    Returns:
        Current user object or None
    """
    if not token:
        return None

    try:
        return get_current_user(db, token)
    except Exception:
        return None