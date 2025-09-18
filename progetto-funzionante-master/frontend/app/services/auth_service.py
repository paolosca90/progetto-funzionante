from typing import Optional
from datetime import datetime, timedelta
import secrets
from sqlalchemy.orm import Session

from models import User
from schemas import UserCreate, Token
from app.repositories.user_repository import UserRepository
from jwt_auth import (
    authenticate_user, create_access_token, create_refresh_token,
    hash_password, ACCESS_TOKEN_EXPIRE_MINUTES
)
from email_utils import send_registration_email, send_password_reset_email


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)

    async def register_user(self, user_create: UserCreate) -> User:
        """
        Register a new user.

        Args:
            user_create: User registration data

        Returns:
            Created user object

        Raises:
            ValueError: If username or email already exists
        """
        # Check if username exists
        if self.user_repository.get_by_username(user_create.username):
            raise ValueError("Username already registered")

        # Check if email exists
        if self.user_repository.get_by_email(user_create.email):
            raise ValueError("Email already registered")

        # Hash password
        hashed_password = hash_password(user_create.password)

        # Create user
        user = self.user_repository.create_user(user_create, hashed_password)

        # Send registration email
        try:
            await send_registration_email(user.email, user.full_name or user.username)
        except Exception as e:
            # Log the error but don't fail registration
            print(f"Failed to send registration email: {e}")

        return user

    def login_user(self, username: str, password: str) -> Optional[Token]:
        """
        Authenticate user and return token.

        Args:
            username: Username or email
            password: Plain text password

        Returns:
            Token object if authentication successful, None otherwise
        """
        # Authenticate user
        user = authenticate_user(self.db, username, password)
        if not user:
            return None

        # Update last login
        self.user_repository.update_last_login(user)

        # Create tokens
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        refresh_token = create_refresh_token(data={"sub": user.username})

        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )

    async def forgot_password(self, email: str) -> bool:
        """
        Send password reset email.

        Args:
            email: User's email address

        Returns:
            True if email was sent successfully
        """
        user = self.user_repository.get_by_email(email)
        if not user:
            # Don't reveal whether email exists
            return True

        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=1)

        # Save reset token
        self.user_repository.set_reset_token(user, reset_token, expires_at)

        # Send reset email
        try:
            await send_password_reset_email(
                user.email,
                user.full_name or user.username,
                reset_token
            )
            return True
        except Exception as e:
            print(f"Failed to send password reset email: {e}")
            return False

    def reset_password(self, reset_token: str, new_password: str) -> bool:
        """
        Reset user password using reset token.

        Args:
            reset_token: Password reset token
            new_password: New plain text password

        Returns:
            True if password was reset successfully
        """
        user = self.user_repository.get_by_reset_token(reset_token)
        if not user:
            return False

        # Hash new password
        hashed_password = hash_password(new_password)

        # Update password and clear reset token
        self.user_repository.update_password(user, hashed_password)
        self.user_repository.clear_reset_token(user)

        return True

    def refresh_token(self, refresh_token: str) -> Optional[Token]:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            New token object if refresh successful
        """
        # This would need to be implemented with proper JWT refresh token validation
        # For now, returning None as placeholder
        return None

    def logout_user(self, token: str) -> bool:
        """
        Logout user (invalidate token).

        Args:
            token: Access token to invalidate

        Returns:
            True if logout successful
        """
        # In a full implementation, you would add the token to a blacklist
        # For now, just return True as tokens will expire naturally
        return True

    def change_password(self, user: User, current_password: str, new_password: str) -> bool:
        """
        Change user password.

        Args:
            user: User object
            current_password: Current plain text password
            new_password: New plain text password

        Returns:
            True if password was changed successfully
        """
        # Verify current password
        if not authenticate_user(self.db, user.username, current_password):
            return False

        # Hash new password
        hashed_password = hash_password(new_password)

        # Update password
        self.user_repository.update_password(user, hashed_password)
        return True

    def activate_user(self, user_id: int) -> Optional[User]:
        """
        Activate a user account.

        Args:
            user_id: User ID to activate

        Returns:
            Updated user object if successful
        """
        user = self.user_repository.get(user_id)
        if not user:
            return None

        return self.user_repository.activate_user(user)

    def deactivate_user(self, user_id: int) -> Optional[User]:
        """
        Deactivate a user account.

        Args:
            user_id: User ID to deactivate

        Returns:
            Updated user object if successful
        """
        user = self.user_repository.get(user_id)
        if not user:
            return None

        return self.user_repository.deactivate_user(user)