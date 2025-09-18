"""
Unit tests for UserRepository.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from models import User
from app.repositories.user_repository import UserRepository
from tests.factories.user_factory import UserFactory


class TestUserRepository:
    """Test cases for UserRepository functionality."""

    @pytest.mark.unit
    def test_user_repository_init(self, db_session):
        """Test UserRepository initialization."""
        repo = UserRepository(db_session)
        assert repo.db == db_session
        assert repo.model == User

    @pytest.mark.unit
    def test_get_user(self, user_repository_fixture, user_fixture):
        """Test get user by ID."""
        # Act
        result = user_repository_fixture.get(user_fixture.id)

        # Assert
        assert result is not None
        assert result.id == user_fixture.id
        assert result.username == user_fixture.username

    @pytest.mark.unit
    def test_get_user_not_found(self, user_repository_fixture):
        """Test get user by ID when user doesn't exist."""
        # Act
        result = user_repository_fixture.get(999)

        # Assert
        assert result is None

    @pytest.mark.unit
    def test_get_by_username(self, user_repository_fixture, user_fixture):
        """Test get user by username."""
        # Act
        result = user_repository_fixture.get_by_username(user_fixture.username)

        # Assert
        assert result is not None
        assert result.username == user_fixture.username
        assert result.id == user_fixture.id

    @pytest.mark.unit
    def test_get_by_username_not_found(self, user_repository_fixture):
        """Test get user by username when user doesn't exist."""
        # Act
        result = user_repository_fixture.get_by_username("nonexistent")

        # Assert
        assert result is None

    @pytest.mark.unit
    def test_get_by_email(self, user_repository_fixture, user_fixture):
        """Test get user by email."""
        # Act
        result = user_repository_fixture.get_by_email(user_fixture.email)

        # Assert
        assert result is not None
        assert result.email == user_fixture.email
        assert result.id == user_fixture.id

    @pytest.mark.unit
    def test_get_by_email_not_found(self, user_repository_fixture):
        """Test get user by email when user doesn't exist."""
        # Act
        result = user_repository_fixture.get_by_email("nonexistent@example.com")

        # Assert
        assert result is None

    @pytest.mark.unit
    def test_get_multi(self, user_repository_fixture, user_fixture):
        """Test get multiple users with pagination."""
        # Arrange
        UserFactory.create_users_batch_instances(user_repository_fixture.db, 5, include_admin=True)

        # Act
        result = user_repository_fixture.get_multi(skip=0, limit=10)

        # Assert
        assert len(result) >= 1  # At least our fixture user
        assert all(isinstance(user, User) for user in result)

    @pytest.mark.unit
    def test_get_active_users(self, user_repository_fixture):
        """Test get active users."""
        # Arrange
        # Create mix of active and inactive users
        active_user = UserFactory.create_user_instance(user_repository_fixture.db)
        inactive_user = UserFactory.create_inactive_user_instance(user_repository_fixture.db)

        # Act
        result = user_repository_fixture.get_active_users()

        # Assert
        assert len(result) >= 1
        for user in result:
            assert user.is_active is True

    @pytest.mark.unit
    def test_get_admin_users(self, user_repository_fixture):
        """Test get admin users."""
        # Arrange
        # Create mix of admin and regular users
        admin_user = UserFactory.create_admin_instance(user_repository_fixture.db)
        regular_user = UserFactory.create_user_instance(user_repository_fixture.db)

        # Act
        result = user_repository_fixture.get_admin_users()

        # Assert
        assert len(result) >= 1
        for user in result:
            assert user.is_admin is True

    @pytest.mark.unit
    def test_search_users_by_username(self, user_repository_fixture):
        """Test search users by username."""
        # Arrange
        search_term = "test"
        UserFactory.create_users_batch_instances(user_repository_fixture.db, 3, include_admin=True)

        # Act
        result = user_repository_fixture.search_users(search_term)

        # Assert
        assert len(result) >= 1
        for user in result:
            # Check if search term matches username, email, or full name
            assert (
                search_term in user.username.lower() or
                search_term in user.email.lower() or
                (user.full_name and search_term in user.full_name.lower())
            )

    @pytest.mark.unit
    def test_search_users_by_email(self, user_repository_fixture):
        """Test search users by email."""
        # Arrange
        search_term = "example.com"
        UserFactory.create_users_batch_instances(user_repository_fixture.db, 3, include_admin=True)

        # Act
        result = user_repository_fixture.search_users(search_term)

        # Assert
        assert len(result) >= 1
        for user in result:
            assert (
                search_term in user.username.lower() or
                search_term in user.email.lower() or
                (user.full_name and search_term in user.full_name.lower())
            )

    @pytest.mark.unit
    def test_search_users_by_full_name(self, user_repository_fixture):
        """Test search users by full name."""
        # Arrange
        search_term = "User"
        user_data = {"full_name": "Test User"}
        UserFactory.create_user_instance(user_repository_fixture.db, user_data)

        # Act
        result = user_repository_fixture.search_users(search_term)

        # Assert
        assert len(result) >= 1
        for user in result:
            assert (
                search_term in user.username.lower() or
                search_term in user.email.lower() or
                (user.full_name and search_term in user.full_name.lower())
            )

    @pytest.mark.unit
    def test_activate_user(self, user_repository_fixture, user_fixture):
        """Test activate a user."""
        # Arrange
        user_fixture.is_active = False

        # Act
        result = user_repository_fixture.activate_user(user_fixture)

        # Assert
        assert result.is_active is True
        assert result.id == user_fixture.id

    @pytest.mark.unit
    def test_deactivate_user(self, user_repository_fixture, user_fixture):
        """Test deactivate a user."""
        # Act
        result = user_repository_fixture.deactivate_user(user_fixture)

        # Assert
        assert result.is_active is False
        assert result.id == user_fixture.id

    @pytest.mark.unit
    def test_make_admin(self, user_repository_fixture, user_fixture):
        """Test make a user admin."""
        # Arrange
        user_fixture.is_admin = False

        # Act
        result = user_repository_fixture.make_admin(user_fixture)

        # Assert
        assert result.is_admin is True
        assert result.id == user_fixture.id

    @pytest.mark.unit
    def test_remove_admin(self, user_repository_fixture, admin_fixture):
        """Test remove admin privileges from a user."""
        # Act
        result = user_repository_fixture.remove_admin(admin_fixture)

        # Assert
        assert result.is_admin is False
        assert result.id == admin_fixture.id

    @pytest.mark.unit
    def test_get_users_count(self, user_repository_fixture):
        """Test get total number of users."""
        # Arrange
        UserFactory.create_users_batch_instances(user_repository_fixture.db, 5, include_admin=True)

        # Act
        result = user_repository_fixture.get_users_count()

        # Assert
        assert result >= 1  # At least our fixture users

    @pytest.mark.unit
    def test_get_active_users_count(self, user_repository_fixture):
        """Test get count of active users."""
        # Arrange
        # Create mix of active and inactive users
        active_user = UserFactory.create_user_instance(user_repository_fixture.db)
        inactive_user = UserFactory.create_inactive_user_instance(user_repository_fixture.db)

        # Act
        result = user_repository_fixture.get_active_users_count()

        # Assert
        assert result >= 1  # At least our active fixture user

    @pytest.mark.unit
    def test_get_users_with_active_subscription(self, user_repository_fixture):
        """Test get users with active subscriptions."""
        # Arrange
        # Create users with different subscription statuses
        active_sub_user = UserFactory.create_user_instance(
            user_repository_fixture.db, {"subscription_active": True}
        )
        inactive_sub_user = UserFactory.create_user_instance(
            user_repository_fixture.db, {"subscription_active": False}
        )

        # Act
        result = user_repository_fixture.get_users_with_active_subscription()

        # Assert
        assert len(result) >= 1
        for user in result:
            assert user.subscription_active is True

    @pytest.mark.unit
    def test_create_user(self, user_repository_fixture):
        """Test create a new user."""
        # Arrange
        user_data = UserFactory.create_user_data()
        user_data.pop("password")  # Remove password as it should be handled separately

        # Act
        result = user_repository_fixture.create(user_data)

        # Assert
        assert result is not None
        assert result.username == user_data["username"]
        assert result.email == user_data["email"]
        assert result.is_active is True

    @pytest.mark.unit
    def test_update_user(self, user_repository_fixture, user_fixture):
        """Test update a user."""
        # Arrange
        update_data = {
            "full_name": "Updated Name",
            "is_active": False
        }

        # Act
        result = user_repository_fixture.update(user_fixture, update_data)

        # Assert
        assert result.full_name == "Updated Name"
        assert result.is_active is False
        assert result.id == user_fixture.id

    @pytest.mark.unit
    def test_delete_user(self, user_repository_fixture, user_fixture):
        """Test delete a user."""
        # Act
        result = user_repository_fixture.delete(user_fixture.id)

        # Assert
        assert result is not None

        # Verify user is deleted
        deleted_user = user_repository_fixture.get(user_fixture.id)
        assert deleted_user is None

    @pytest.mark.unit
    def test_delete_user_not_found(self, user_repository_fixture):
        """Test delete a user that doesn't exist."""
        # Act
        result = user_repository_fixture.delete(999)

        # Assert
        assert result is None

    @pytest.mark.unit
    def test_update_user_email(self, user_repository_fixture, user_fixture):
        """Test update user email."""
        # Arrange
        new_email = "updated@example.com"

        # Act
        result = user_repository_fixture.update(user_fixture, {"email": new_email})

        # Assert
        assert result.email == new_email

    @pytest.mark.unit
    def test_update_user_password(self, user_repository_fixture, user_fixture):
        """Test update user password."""
        # Arrange
        new_password = "NewSecurePassword123!"

        # Act
        result = user_repository_fixture.update(user_fixture, {"password": new_password})

        # Assert
        # Password should be hashed, so we can't check directly
        # But we can verify the user was updated
        assert result.id == user_fixture.id

    @pytest.mark.unit
    def test_get_user_by_credentials_valid(self, user_repository_fixture, user_fixture):
        """Test get user by valid credentials."""
        # Arrange
        username = user_fixture.username
        password = "testpassword123"  # Original password from fixture

        # Act
        result = user_repository_fixture.get_user_by_credentials(username, password)

        # Assert
        assert result is not None
        assert result.id == user_fixture.id
        assert result.username == username

    @pytest.mark.unit
    def test_get_user_by_credentials_invalid_password(self, user_repository_fixture, user_fixture):
        """Test get user by invalid password."""
        # Arrange
        username = user_fixture.username
        wrong_password = "wrongpassword"

        # Act
        result = user_repository_fixture.get_user_by_credentials(username, wrong_password)

        # Assert
        assert result is None

    @pytest.mark.unit
    def test_get_user_by_credentials_invalid_username(self, user_repository_fixture):
        """Test get user by invalid username."""
        # Arrange
        invalid_username = "nonexistent"
        password = "testpassword123"

        # Act
        result = user_repository_fixture.get_user_by_credentials(invalid_username, password)

        # Assert
        assert result is None

    @pytest.mark.unit
    def test_update_last_login(self, user_repository_fixture, user_fixture):
        """Test update user's last login timestamp."""
        # Arrange
        old_last_login = user_fixture.last_login

        # Act
        result = user_repository_fixture.update_last_login(user_fixture)

        # Assert
        assert result.last_login is not None
        if old_last_login:
            assert result.last_login > old_last_login

    @pytest.mark.unit
    def test_get_users_created_after(self, user_repository_fixture):
        """Test get users created after a specific date."""
        # Arrange
        cutoff_date = datetime.utcnow() - timedelta(days=1)
        recent_user = UserFactory.create_user_instance(user_repository_fixture.db)

        # Act
        result = user_repository_fixture.get_users_created_after(cutoff_date)

        # Assert
        assert len(result) >= 1
        for user in result:
            assert user.created_at > cutoff_date

    @pytest.mark.unit
    def test_get_users_created_before(self, user_repository_fixture):
        """Test get users created before a specific date."""
        # Arrange
        cutoff_date = datetime.utcnow() + timedelta(days=1)  # Future date

        # Act
        result = user_repository_fixture.get_users_created_before(cutoff_date)

        # Assert
        assert len(result) >= 1
        for user in result:
            assert user.created_at < cutoff_date

    @pytest.mark.unit
    def test_get_users_by_subscription_status(self, user_repository_fixture):
        """Test get users by subscription status."""
        # Arrange
        # Create users with different subscription statuses
        active_sub_user = UserFactory.create_user_instance(
            user_repository_fixture.db, {"subscription_active": True}
        )
        inactive_sub_user = UserFactory.create_user_instance(
            user_repository_fixture.db, {"subscription_active": False}
        )

        # Test active subscriptions
        result_active = user_repository_fixture.get_users_by_subscription_status(True)
        assert len(result_active) >= 1
        for user in result_active:
            assert user.subscription_active is True

        # Test inactive subscriptions
        result_inactive = user_repository_fixture.get_users_by_subscription_status(False)
        assert len(result_inactive) >= 1
        for user in result_inactive:
            assert user.subscription_active is False

    @pytest.mark.unit
    def test_bulk_update_users(self, user_repository_fixture):
        """Test bulk update multiple users."""
        # Arrange
        users = UserFactory.create_users_batch_instances(user_repository_fixture.db, 3, include_admin=False)
        user_ids = [user.id for user in users]
        update_data = {"is_active": False}

        # Act
        result = user_repository_fixture.bulk_update_users(user_ids, update_data)

        # Assert
        assert result == 3  # 3 users should be updated

        # Verify updates
        for user_id in user_ids:
            updated_user = user_repository_fixture.get(user_id)
            assert updated_user.is_active is False

    @pytest.mark.unit
    def test_get_user_statistics(self, user_repository_fixture):
        """Test get user statistics."""
        # Arrange
        UserFactory.create_users_batch_instances(user_repository_fixture.db, 5, include_admin=True)

        # Act
        result = user_repository_fixture.get_user_statistics()

        # Assert
        assert isinstance(result, dict)
        assert "total_users" in result
        assert "active_users" in result
        assert "admin_users" in result
        assert "users_with_active_subscription" in result

        assert result["total_users"] >= 1
        assert result["active_users"] >= 1
        assert result["admin_users"] >= 1
        assert result["users_with_active_subscription"] >= 0