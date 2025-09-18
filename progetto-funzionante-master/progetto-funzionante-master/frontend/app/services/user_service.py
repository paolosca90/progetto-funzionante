from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from models import User
from schemas import UserStatsOut
from app.repositories.user_repository import UserRepository
from app.repositories.signal_repository import SignalRepository


class UserService:
    """Service for user operations."""

    def __init__(self, db: Session):
        self.db = db
        self.user_repository = UserRepository(db)
        self.signal_repository = SignalRepository(db)

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return self.user_repository.get(user_id)

    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return self.user_repository.get_by_username(username)

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.user_repository.get_by_email(email)

    def get_all_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users with pagination."""
        return self.user_repository.get_multi(skip=skip, limit=limit)

    def get_active_users(self) -> List[User]:
        """Get all active users."""
        return self.user_repository.get_active_users()

    def get_admin_users(self) -> List[User]:
        """Get all admin users."""
        return self.user_repository.get_admin_users()

    def search_users(self, search_term: str) -> List[User]:
        """Search users by username, email, or full name."""
        return self.user_repository.search_users(search_term)

    def get_user_stats(self, user: User) -> UserStatsOut:
        """
        Get comprehensive user statistics.

        Args:
            user: User object

        Returns:
            UserStatsOut with user statistics
        """
        # Get user's signals
        user_signals = self.signal_repository.get_signals_by_user(user.id, limit=1000)

        # Calculate signal statistics
        total_signals = len(user_signals)
        active_signals = len([s for s in user_signals if s.is_active])

        # Calculate average reliability
        avg_reliability = 0.0
        if user_signals:
            total_reliability = sum([s.reliability or 0 for s in user_signals])
            avg_reliability = total_reliability / total_signals

        # Get recent activity (signals in last 30 days)
        recent_cutoff = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        recent_cutoff = recent_cutoff.replace(day=recent_cutoff.day - 30 if recent_cutoff.day > 30 else 1)

        recent_signals = [s for s in user_signals if s.created_at >= recent_cutoff]

        return UserStatsOut(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_admin=user.is_admin,
            subscription_active=user.subscription_active,
            created_at=user.created_at,
            last_login=user.last_login,
            total_signals=total_signals,
            active_signals=active_signals,
            average_reliability=round(avg_reliability, 2),
            recent_signals_count=len(recent_signals)
        )

    def update_user_profile(
        self,
        user: User,
        full_name: Optional[str] = None,
        email: Optional[str] = None
    ) -> User:
        """
        Update user profile information.

        Args:
            user: User to update
            full_name: New full name (optional)
            email: New email (optional)

        Returns:
            Updated user object
        """
        update_data = {}

        if full_name is not None:
            update_data["full_name"] = full_name

        if email is not None:
            # Check if email is already taken by another user
            existing_user = self.user_repository.get_by_email(email)
            if existing_user and existing_user.id != user.id:
                raise ValueError("Email already in use by another user")
            update_data["email"] = email

        if update_data:
            return self.user_repository.update(user, update_data)

        return user

    def activate_user(self, user_id: int) -> Optional[User]:
        """Activate a user account."""
        user = self.user_repository.get(user_id)
        if not user:
            return None
        return self.user_repository.activate_user(user)

    def deactivate_user(self, user_id: int) -> Optional[User]:
        """Deactivate a user account."""
        user = self.user_repository.get(user_id)
        if not user:
            return None
        return self.user_repository.deactivate_user(user)

    def make_admin(self, user_id: int) -> Optional[User]:
        """Grant admin privileges to a user."""
        user = self.user_repository.get(user_id)
        if not user:
            return None
        return self.user_repository.make_admin(user)

    def remove_admin(self, user_id: int) -> Optional[User]:
        """Remove admin privileges from a user."""
        user = self.user_repository.get(user_id)
        if not user:
            return None
        return self.user_repository.remove_admin(user)

    def get_user_count(self) -> int:
        """Get total number of users."""
        return self.user_repository.get_users_count()

    def get_active_user_count(self) -> int:
        """Get count of active users."""
        return self.user_repository.get_active_users_count()

    def get_users_with_active_subscription(self) -> List[User]:
        """Get users with active subscriptions."""
        return self.user_repository.get_users_with_active_subscription()

    def update_subscription_status(self, user_id: int, is_active: bool) -> Optional[User]:
        """
        Update user's subscription status.

        Args:
            user_id: User ID
            is_active: New subscription status

        Returns:
            Updated user object if successful
        """
        user = self.user_repository.get(user_id)
        if not user:
            return None

        update_data = {"subscription_active": is_active}
        return self.user_repository.update(user, update_data)

    def get_user_dashboard_data(self, user: User) -> Dict[str, Any]:
        """
        Get data for user dashboard.

        Args:
            user: User object

        Returns:
            Dictionary with dashboard data
        """
        # Get user statistics
        user_stats = self.get_user_stats(user)

        # Get recent signals
        recent_signals = self.signal_repository.get_signals_by_user(user.id, limit=10)

        # Get user's signal performance
        user_signals = self.signal_repository.get_signals_by_user(user.id, limit=100)

        # Calculate performance metrics
        total_signals = len(user_signals)

        if total_signals > 0:
            # Calculate reliability distribution
            high_reliability = len([s for s in user_signals if (s.reliability or 0) >= 80])
            medium_reliability = len([s for s in user_signals if 50 <= (s.reliability or 0) < 80])
            low_reliability = len([s for s in user_signals if (s.reliability or 0) < 50])

            # Calculate signal type distribution
            buy_signals = len([s for s in user_signals if s.signal_type.value == "BUY"])
            sell_signals = len([s for s in user_signals if s.signal_type.value == "SELL"])
            hold_signals = len([s for s in user_signals if s.signal_type.value == "HOLD"])
        else:
            high_reliability = medium_reliability = low_reliability = 0
            buy_signals = sell_signals = hold_signals = 0

        return {
            "user_stats": user_stats.dict(),
            "recent_signals": [
                {
                    "id": signal.id,
                    "symbol": signal.symbol,
                    "signal_type": signal.signal_type.value,
                    "entry_price": signal.entry_price,
                    "reliability": signal.reliability,
                    "created_at": signal.created_at,
                    "status": signal.status.value
                }
                for signal in recent_signals
            ],
            "signal_distribution": {
                "buy": buy_signals,
                "sell": sell_signals,
                "hold": hold_signals
            },
            "reliability_distribution": {
                "high": high_reliability,
                "medium": medium_reliability,
                "low": low_reliability
            },
            "total_signals": total_signals
        }

    def delete_user(self, user_id: int, performing_user: User) -> bool:
        """
        Delete a user account.

        Args:
            user_id: ID of user to delete
            performing_user: User performing the action

        Returns:
            True if deletion successful
        """
        # Only admins can delete users, and users can delete their own account
        if not performing_user.is_admin and performing_user.id != user_id:
            return False

        user = self.user_repository.get(user_id)
        if not user:
            return False

        # Don't allow deleting the last admin
        if user.is_admin:
            admin_count = len(self.user_repository.get_admin_users())
            if admin_count <= 1:
                return False

        # Delete user (this will cascade to related records)
        deleted_user = self.user_repository.delete(user_id)
        return deleted_user is not None