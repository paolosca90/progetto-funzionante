from typing import Optional, List
from sqlalchemy.orm import Session, joinedload, selectinload
from datetime import datetime

from models import User
from schemas import UserCreate
from .base_repository import BaseRepository


class UserRepository(BaseRepository[User, UserCreate, dict]):
    """Repository for User model operations."""

    def __init__(self, db: Session):
        super().__init__(User, db)

    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username with relationships preloaded."""
        return self.db.query(User).options(
            selectinload(User.signals),
            selectinload(User.executions),
            joinedload(User.oanda_connection)
        ).filter(User.username == username).first()

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email with relationships preloaded."""
        return self.db.query(User).options(
            selectinload(User.signals),
            selectinload(User.executions),
            joinedload(User.oanda_connection)
        ).filter(User.email == email).first()

    def get_by_reset_token(self, reset_token: str) -> Optional[User]:
        """Get user by password reset token."""
        return self.db.query(User).filter(
            User.reset_token == reset_token,
            User.reset_token_expires > datetime.utcnow()
        ).first()

    def create_user(self, user_create: UserCreate, hashed_password: str) -> User:
        """Create a new user with hashed password."""
        db_user = User(
            username=user_create.username,
            email=user_create.email,
            full_name=user_create.full_name,
            hashed_password=hashed_password,
            is_active=True,
            is_admin=False,
            subscription_active=True,
            created_at=datetime.utcnow()
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def update_last_login(self, user: User) -> User:
        """Update user's last login timestamp."""
        user.last_login = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        return user

    def set_reset_token(self, user: User, reset_token: str, expires_at: datetime) -> User:
        """Set password reset token for user."""
        user.reset_token = reset_token
        user.reset_token_expires = expires_at
        self.db.commit()
        self.db.refresh(user)
        return user

    def clear_reset_token(self, user: User) -> User:
        """Clear password reset token."""
        user.reset_token = None
        user.reset_token_expires = None
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_password(self, user: User, hashed_password: str) -> User:
        """Update user's password."""
        user.hashed_password = hashed_password
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_active_users(self) -> List[User]:
        """Get all active users with optimized loading."""
        return self.db.query(User).options(
            selectinload(User.signals),
            selectinload(User.executions),
            joinedload(User.oanda_connection)
        ).filter(User.is_active == True).all()

    def get_admin_users(self) -> List[User]:
        """Get all admin users with optimized loading."""
        return self.db.query(User).options(
            selectinload(User.signals),
            selectinload(User.executions),
            joinedload(User.oanda_connection)
        ).filter(User.is_admin == True).all()

    def get_users_with_active_subscription(self) -> List[User]:
        """Get users with active subscriptions with optimized loading."""
        return self.db.query(User).options(
            selectinload(User.signals),
            selectinload(User.executions),
            joinedload(User.oanda_connection)
        ).filter(User.subscription_active == True).all()

    def get_users_count(self) -> int:
        """Get total number of users."""
        return self.db.query(User).count()

    def get_active_users_count(self) -> int:
        """Get count of active users."""
        return self.db.query(User).filter(User.is_active == True).count()

    def search_users(self, search_term: str) -> List[User]:
        """Search users by username, email, or full name with optimized loading."""
        search_pattern = f"%{search_term}%"
        return self.db.query(User).options(
            selectinload(User.signals),
            selectinload(User.executions),
            joinedload(User.oanda_connection)
        ).filter(
            (User.username.ilike(search_pattern)) |
            (User.email.ilike(search_pattern)) |
            (User.full_name.ilike(search_pattern))
        ).all()

    def activate_user(self, user: User) -> User:
        """Activate a user account."""
        user.is_active = True
        self.db.commit()
        self.db.refresh(user)
        return user

    def deactivate_user(self, user: User) -> User:
        """Deactivate a user account."""
        user.is_active = False
        self.db.commit()
        self.db.refresh(user)
        return user

    def make_admin(self, user: User) -> User:
        """Grant admin privileges to user."""
        user.is_admin = True
        self.db.commit()
        self.db.refresh(user)
        return user

    def remove_admin(self, user: User) -> User:
        """Remove admin privileges from user."""
        user.is_admin = False
        self.db.commit()
        self.db.refresh(user)
        return user