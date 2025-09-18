"""
Unit tests for UserService.
"""

import pytest
from unittest.mock import MagicMock, patch
from typing import List, Dict, Any
from datetime import datetime, timedelta

from models import User, Signal, SignalTypeEnum
from schemas import UserStatsOut
from app.services.user_service import UserService
from tests.factories.user_factory import UserFactory
from tests.factories.signal_factory import SignalFactory


class TestUserService:
    """Test cases for UserService functionality."""

    @pytest.mark.unit
    def test_user_service_init(self, db_session):
        """Test UserService initialization."""
        service = UserService(db_session)
        assert service.db == db_session
        assert service.user_repository is not None
        assert service.signal_repository is not None

    @pytest.mark.unit
    def test_get_user_by_id_found(self, user_service_fixture, user_fixture):
        """Test get user by ID when user exists."""
        # Act
        result = user_service_fixture.get_user_by_id(user_fixture.id)

        # Assert
        assert result is not None
        assert result.id == user_fixture.id
        assert result.username == user_fixture.username

    @pytest.mark.unit
    def test_get_user_by_id_not_found(self, user_service_fixture):
        """Test get user by ID when user doesn't exist."""
        # Act
        result = user_service_fixture.get_user_by_id(999)

        # Assert
        assert result is None

    @pytest.mark.unit
    def test_get_user_by_username_found(self, user_service_fixture, user_fixture):
        """Test get user by username when user exists."""
        # Act
        result = user_service_fixture.get_user_by_username(user_fixture.username)

        # Assert
        assert result is not None
        assert result.username == user_fixture.username
        assert result.id == user_fixture.id

    @pytest.mark.unit
    def test_get_user_by_username_not_found(self, user_service_fixture):
        """Test get user by username when user doesn't exist."""
        # Act
        result = user_service_fixture.get_user_by_username("nonexistent")

        # Assert
        assert result is None

    @pytest.mark.unit
    def test_get_user_by_email_found(self, user_service_fixture, user_fixture):
        """Test get user by email when user exists."""
        # Act
        result = user_service_fixture.get_user_by_email(user_fixture.email)

        # Assert
        assert result is not None
        assert result.email == user_fixture.email
        assert result.id == user_fixture.id

    @pytest.mark.unit
    def test_get_user_by_email_not_found(self, user_service_fixture):
        """Test get user by email when user doesn't exist."""
        # Act
        result = user_service_fixture.get_user_by_email("nonexistent@example.com")

        # Assert
        assert result is None

    @pytest.mark.unit
    def test_get_all_users(self, user_service_fixture, user_fixture):
        """Test get all users with pagination."""
        # Arrange
        skip = 0
        limit = 10
        expected_users = [user_fixture]

        user_service_fixture.user_repository.get_multi.return_value = expected_users

        # Act
        result = user_service_fixture.get_all_users(skip, limit)

        # Assert
        assert len(result) == 1
        assert result[0].id == user_fixture.id
        user_service_fixture.user_repository.get_multi.assert_called_once_with(skip=skip, limit=limit)

    @pytest.mark.unit
    def test_get_active_users(self, user_service_fixture):
        """Test get active users."""
        # Arrange
        mock_user = MagicMock()
        mock_user.is_active = True
        expected_users = [mock_user]

        user_service_fixture.user_repository.get_active_users.return_value = expected_users

        # Act
        result = user_service_fixture.get_active_users()

        # Assert
        assert len(result) == 1
        assert result[0].is_active is True
        user_service_fixture.user_repository.get_active_users.assert_called_once()

    @pytest.mark.unit
    def test_get_admin_users(self, user_service_fixture):
        """Test get admin users."""
        # Arrange
        mock_admin = MagicMock()
        mock_admin.is_admin = True
        expected_admins = [mock_admin]

        user_service_fixture.user_repository.get_admin_users.return_value = expected_admins

        # Act
        result = user_service_fixture.get_admin_users()

        # Assert
        assert len(result) == 1
        assert result[0].is_admin is True
        user_service_fixture.user_repository.get_admin_users.assert_called_once()

    @pytest.mark.unit
    def test_search_users(self, user_service_fixture):
        """Test user search functionality."""
        # Arrange
        search_term = "test"
        mock_user = MagicMock()
        mock_user.username = "testuser"
        expected_users = [mock_user]

        user_service_fixture.user_repository.search_users.return_value = expected_users

        # Act
        result = user_service_fixture.search_users(search_term)

        # Assert
        assert len(result) == 1
        assert "test" in result[0].username.lower()
        user_service_fixture.user_repository.search_users.assert_called_once_with(search_term)

    @pytest.mark.unit
    def test_get_user_stats_with_signals(self, user_service_fixture, user_fixture):
        """Test get user statistics when user has signals."""
        # Arrange
        mock_signal1 = MagicMock()
        mock_signal1.reliability = 85.0
        mock_signal1.is_active = True
        mock_signal1.created_at = datetime.utcnow() - timedelta(days=15)

        mock_signal2 = MagicMock()
        mock_signal2.reliability = 75.0
        mock_signal2.is_active = False
        mock_signal2.created_at = datetime.utcnow() - timedelta(days=45)

        user_signals = [mock_signal1, mock_signal2]
        user_service_fixture.signal_repository.get_signals_by_user.return_value = user_signals

        # Act
        result = user_service_fixture.get_user_stats(user_fixture)

        # Assert
        assert isinstance(result, UserStatsOut)
        assert result.id == user_fixture.id
        assert result.username == user_fixture.username
        assert result.total_signals == 2
        assert result.active_signals == 1
        assert result.average_reliability == 80.0  # (85 + 75) / 2
        assert result.recent_signals_count == 1  # Only signal1 is recent

    @pytest.mark.unit
    def test_get_user_stats_no_signals(self, user_service_fixture, user_fixture):
        """Test get user statistics when user has no signals."""
        # Arrange
        user_service_fixture.signal_repository.get_signals_by_user.return_value = []

        # Act
        result = user_service_fixture.get_user_stats(user_fixture)

        # Assert
        assert isinstance(result, UserStatsOut)
        assert result.id == user_fixture.id
        assert result.total_signals == 0
        assert result.active_signals == 0
        assert result.average_reliability == 0.0
        assert result.recent_signals_count == 0

    @pytest.mark.unit
    def test_update_user_profile_full_name(self, user_service_fixture, user_fixture):
        """Test update user profile with full name."""
        # Arrange
        new_full_name = "Updated Test User"
        updated_user = MagicMock()
        updated_user.full_name = new_full_name

        user_service_fixture.user_repository.update.return_value = updated_user

        # Act
        result = user_service_fixture.update_user_profile(user_fixture, full_name=new_full_name)

        # Assert
        assert result == updated_user
        user_service_fixture.user_repository.update.assert_called_once_with(
            user_fixture, {"full_name": new_full_name}
        )

    @pytest.mark.unit
    def test_update_user_profile_email_available(self, user_service_fixture, user_fixture):
        """Test update user profile with available email."""
        # Arrange
        new_email = "updated@example.com"
        updated_user = MagicMock()
        updated_user.email = new_email

        user_service_fixture.user_repository.get_by_email.return_value = None  # Email not taken
        user_service_fixture.user_repository.update.return_value = updated_user

        # Act
        result = user_service_fixture.update_user_profile(user_fixture, email=new_email)

        # Assert
        assert result == updated_user
        user_service_fixture.user_repository.get_by_email.assert_called_once_with(new_email)
        user_service_fixture.user_repository.update.assert_called_once_with(
            user_fixture, {"email": new_email}
        )

    @pytest.mark.unit
    def test_update_user_profile_email_taken(self, user_service_fixture, user_fixture):
        """Test update user profile with taken email."""
        # Arrange
        new_email = "existing@example.com"
        existing_user = MagicMock()
        existing_user.id = user_fixture.id + 1  # Different user

        user_service_fixture.user_repository.get_by_email.return_value = existing_user

        # Act & Assert
        with pytest.raises(ValueError, match="Email already in use by another user"):
            user_service_fixture.update_user_profile(user_fixture, email=new_email)

    @pytest.mark.unit
    def test_update_user_profile_no_changes(self, user_service_fixture, user_fixture):
        """Test update user profile with no changes."""
        # Act
        result = user_service_fixture.update_user_profile(user_fixture)

        # Assert
        assert result == user_fixture
        user_service_fixture.user_repository.update.assert_not_called()

    @pytest.mark.unit
    def test_activate_user_success(self, user_service_fixture, user_fixture):
        """Test successful user activation."""
        # Arrange
        user_fixture.is_active = False
        activated_user = MagicMock()
        activated_user.is_active = True

        user_service_fixture.user_repository.get.return_value = user_fixture
        user_service_fixture.user_repository.activate_user.return_value = activated_user

        # Act
        result = user_service_fixture.activate_user(user_fixture.id)

        # Assert
        assert result == activated_user
        user_service_fixture.user_repository.get.assert_called_once_with(user_fixture.id)
        user_service_fixture.user_repository.activate_user.assert_called_once_with(user_fixture)

    @pytest.mark.unit
    def test_activate_user_not_found(self, user_service_fixture):
        """Test user activation when user doesn't exist."""
        # Arrange
        user_service_fixture.user_repository.get.return_value = None

        # Act
        result = user_service_fixture.activate_user(999)

        # Assert
        assert result is None

    @pytest.mark.unit
    def test_deactivate_user_success(self, user_service_fixture, user_fixture):
        """Test successful user deactivation."""
        # Arrange
        deactivated_user = MagicMock()
        deactivated_user.is_active = False

        user_service_fixture.user_repository.get.return_value = user_fixture
        user_service_fixture.user_repository.deactivate_user.return_value = deactivated_user

        # Act
        result = user_service_fixture.deactivate_user(user_fixture.id)

        # Assert
        assert result == deactivated_user
        user_service_fixture.user_repository.deactivate_user.assert_called_once_with(user_fixture)

    @pytest.mark.unit
    def test_make_admin_success(self, user_service_fixture, user_fixture):
        """Test successful admin promotion."""
        # Arrange
        admin_user = MagicMock()
        admin_user.is_admin = True

        user_service_fixture.user_repository.get.return_value = user_fixture
        user_service_fixture.user_repository.make_admin.return_value = admin_user

        # Act
        result = user_service_fixture.make_admin(user_fixture.id)

        # Assert
        assert result == admin_user
        user_service_fixture.user_repository.make_admin.assert_called_once_with(user_fixture)

    @pytest.mark.unit
    def test_remove_admin_success(self, user_service_fixture, user_fixture):
        """Test successful admin removal."""
        # Arrange
        regular_user = MagicMock()
        regular_user.is_admin = False

        user_service_fixture.user_repository.get.return_value = user_fixture
        user_service_fixture.user_repository.remove_admin.return_value = regular_user

        # Act
        result = user_service_fixture.remove_admin(user_fixture.id)

        # Assert
        assert result == regular_user
        user_service_fixture.user_repository.remove_admin.assert_called_once_with(user_fixture)

    @pytest.mark.unit
    def test_get_user_count(self, user_service_fixture):
        """Test get total user count."""
        # Arrange
        expected_count = 42
        user_service_fixture.user_repository.get_users_count.return_value = expected_count

        # Act
        result = user_service_fixture.get_user_count()

        # Assert
        assert result == expected_count
        user_service_fixture.user_repository.get_users_count.assert_called_once()

    @pytest.mark.unit
    def test_get_active_user_count(self, user_service_fixture):
        """Test get active user count."""
        # Arrange
        expected_count = 25
        user_service_fixture.user_repository.get_active_users_count.return_value = expected_count

        # Act
        result = user_service_fixture.get_active_user_count()

        # Assert
        assert result == expected_count
        user_service_fixture.user_repository.get_active_users_count.assert_called_once()

    @pytest.mark.unit
    def test_get_users_with_active_subscription(self, user_service_fixture):
        """Test get users with active subscriptions."""
        # Arrange
        mock_user = MagicMock()
        mock_user.subscription_active = True
        expected_users = [mock_user]

        user_service_fixture.user_repository.get_users_with_active_subscription.return_value = expected_users

        # Act
        result = user_service_fixture.get_users_with_active_subscription()

        # Assert
        assert len(result) == 1
        assert result[0].subscription_active is True
        user_service_fixture.user_repository.get_users_with_active_subscription.assert_called_once()

    @pytest.mark.unit
    def test_update_subscription_status_success(self, user_service_fixture, user_fixture):
        """Test successful subscription status update."""
        # Arrange
        is_active = True
        updated_user = MagicMock()
        updated_user.subscription_active = is_active

        user_service_fixture.user_repository.get.return_value = user_fixture
        user_service_fixture.user_repository.update.return_value = updated_user

        # Act
        result = user_service_fixture.update_subscription_status(user_fixture.id, is_active)

        # Assert
        assert result == updated_user
        user_service_fixture.user_repository.update.assert_called_once_with(
            user_fixture, {"subscription_active": is_active}
        )

    @pytest.mark.unit
    def test_update_subscription_status_user_not_found(self, user_service_fixture):
        """Test subscription status update when user doesn't exist."""
        # Arrange
        user_service_fixture.user_repository.get.return_value = None

        # Act
        result = user_service_fixture.update_subscription_status(999, True)

        # Assert
        assert result is None

    @pytest.mark.unit
    def test_get_user_dashboard_data_with_signals(self, user_service_fixture, user_fixture):
        """Test get user dashboard data when user has signals."""
        # Arrange
        # Create mock signals
        mock_signal1 = MagicMock()
        mock_signal1.id = 1
        mock_signal1.symbol = "EUR_USD"
        mock_signal1.signal_type = SignalTypeEnum.BUY
        mock_signal1.entry_price = 1.1234
        mock_signal1.reliability = 85.0
        mock_signal1.created_at = datetime.utcnow() - timedelta(days=5)
        mock_signal1.status.value = "ACTIVE"

        mock_signal2 = MagicMock()
        mock_signal2.id = 2
        mock_signal2.symbol = "GBP_USD"
        mock_signal2.signal_type = SignalTypeEnum.SELL
        mock_signal2.entry_price = 1.3456
        mock_signal2.reliability = 78.0
        mock_signal2.created_at = datetime.utcnow() - timedelta(days=1)
        mock_signal2.status.value = "CLOSED"

        mock_signal3 = MagicMock()
        mock_signal3.id = 3
        mock_signal3.symbol = "USD_JPY"
        mock_signal3.signal_type = SignalTypeEnum.HOLD
        mock_signal3.reliability = 65.0
        mock_signal3.created_at = datetime.utcnow() - timedelta(days=10)

        recent_signals = [mock_signal1, mock_signal2]
        all_signals = [mock_signal1, mock_signal2, mock_signal3]

        user_service_fixture.signal_repository.get_signals_by_user.side_effect = [
            recent_signals,  # First call (limit=10)
            all_signals      # Second call (limit=100)
        ]

        # Mock user stats
        mock_stats = MagicMock()
        mock_stats.dict.return_value = {
            "id": user_fixture.id,
            "username": user_fixture.username,
            "total_signals": 3,
            "active_signals": 1
        }
        user_service_fixture.get_user_stats.return_value = mock_stats

        # Act
        result = user_service_fixture.get_user_dashboard_data(user_fixture)

        # Assert
        assert isinstance(result, dict)
        assert "user_stats" in result
        assert "recent_signals" in result
        assert "signal_distribution" in result
        assert "reliability_distribution" in result
        assert "total_signals" in result

        # Check signal distribution
        signal_dist = result["signal_distribution"]
        assert signal_dist["buy"] == 1
        assert signal_dist["sell"] == 1
        assert signal_dist["hold"] == 1

        # Check reliability distribution
        rel_dist = result["reliability_distribution"]
        assert rel_dist["high"] == 1  # reliability >= 80
        assert rel_dist["medium"] == 1  # 50 <= reliability < 80
        assert rel_dist["low"] == 1  # reliability < 50

        # Check recent signals
        assert len(result["recent_signals"]) == 2

    @pytest.mark.unit
    def test_get_user_dashboard_data_no_signals(self, user_service_fixture, user_fixture):
        """Test get user dashboard data when user has no signals."""
        # Arrange
        user_service_fixture.signal_repository.get_signals_by_user.return_value = []

        # Mock user stats
        mock_stats = MagicMock()
        mock_stats.dict.return_value = {
            "id": user_fixture.id,
            "username": user_fixture.username,
            "total_signals": 0,
            "active_signals": 0
        }
        user_service_fixture.get_user_stats.return_value = mock_stats

        # Act
        result = user_service_fixture.get_user_dashboard_data(user_fixture)

        # Assert
        assert isinstance(result, dict)
        assert result["total_signals"] == 0

        # Check signal distribution (all zeros)
        signal_dist = result["signal_distribution"]
        assert signal_dist["buy"] == 0
        assert signal_dist["sell"] == 0
        assert signal_dist["hold"] == 0

        # Check reliability distribution (all zeros)
        rel_dist = result["reliability_distribution"]
        assert rel_dist["high"] == 0
        assert rel_dist["medium"] == 0
        assert rel_dist["low"] == 0

        # Check recent signals (empty)
        assert len(result["recent_signals"]) == 0

    @pytest.mark.unit
    def test_delete_user_success_by_admin(self, user_service_fixture, user_fixture):
        """Test successful user deletion by admin."""
        # Arrange
        admin_user = MagicMock()
        admin_user.is_admin = True
        admin_user.id = user_fixture.id + 1

        user_service_fixture.user_repository.get.return_value = user_fixture
        user_service_fixture.user_repository.delete.return_value = user_fixture
        user_service_fixture.user_repository.get_admin_users.return_value = [admin_user, user_fixture]

        # Act
        result = user_service_fixture.delete_user(user_fixture.id, admin_user)

        # Assert
        assert result is True
        user_service_fixture.user_repository.delete.assert_called_once_with(user_fixture.id)

    @pytest.mark.unit
    def test_delete_user_success_by_owner(self, user_service_fixture, user_fixture):
        """Test successful user deletion by owner."""
        # Arrange
        user_service_fixture.user_repository.get.return_value = user_fixture
        user_service_fixture.user_repository.delete.return_value = user_fixture
        user_service_fixture.user_repository.get_admin_users.return_value = [user_fixture]

        # Act
        result = user_service_fixture.delete_user(user_fixture.id, user_fixture)

        # Assert
        assert result is True
        user_service_fixture.user_repository.delete.assert_called_once_with(user_fixture.id)

    @pytest.mark.unit
    def test_delete_user_unauthorized(self, user_service_fixture, user_fixture):
        """Test user deletion by unauthorized user."""
        # Arrange
        other_user = MagicMock()
        other_user.is_admin = False
        other_user.id = user_fixture.id + 1

        user_service_fixture.user_repository.get.return_value = user_fixture

        # Act
        result = user_service_fixture.delete_user(user_fixture.id, other_user)

        # Assert
        assert result is False
        user_service_fixture.user_repository.delete.assert_not_called()

    @pytest.mark.unit
    def test_delete_last_admin(self, user_service_fixture, user_fixture):
        """Test deletion of last admin user (should fail)."""
        # Arrange
        user_fixture.is_admin = True
        admin_user = MagicMock()
        admin_user.is_admin = True

        user_service_fixture.user_repository.get.return_value = user_fixture
        user_service_fixture.user_repository.get_admin_users.return_value = [user_fixture]  # Only one admin

        # Act
        result = user_service_fixture.delete_user(user_fixture.id, admin_user)

        # Assert
        assert result is False
        user_service_fixture.user_repository.delete.assert_not_called()

    @pytest.mark.unit
    def test_delete_user_not_found(self, user_service_fixture, admin_fixture):
        """Test deletion of non-existent user."""
        # Arrange
        user_service_fixture.user_repository.get.return_value = None

        # Act
        result = user_service_fixture.delete_user(999, admin_fixture)

        # Assert
        assert result is False