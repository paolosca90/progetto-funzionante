"""
Factory classes for creating test user data.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from uuid import uuid4
import random
import string

from models import User


class UserFactory:
    """Factory for creating test user instances."""

    @staticmethod
    def create_user_data(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create user data dictionary with optional overrides.

        Args:
            overrides: Dictionary of values to override defaults

        Returns:
            Dictionary with user data
        """
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))

        default_data = {
            "username": f"testuser_{random_suffix}",
            "email": f"test_{random_suffix}@example.com",
            "full_name": "Test User",
            "password": "SecurePassword123!",
            "is_active": True,
            "is_admin": False,
            "subscription_active": True,
            "last_login": None
        }

        if overrides:
            default_data.update(overrides)

        return default_data

    @staticmethod
    def create_admin_data(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create admin user data dictionary with optional overrides.

        Args:
            overrides: Dictionary of values to override defaults

        Returns:
            Dictionary with admin user data
        """
        admin_data = UserFactory.create_user_data(overrides)
        admin_data.update({
            "username": f"admin_{random_suffix}" if 'random_suffix' in locals() else "admin_user",
            "email": f"admin_{random_suffix}@example.com" if 'random_suffix' in locals() else "admin@example.com",
            "full_name": "Admin User",
            "is_admin": True
        })

        if overrides:
            admin_data.update(overrides)

        return admin_data

    @staticmethod
    def create_inactive_user_data(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create inactive user data dictionary with optional overrides.

        Args:
            overrides: Dictionary of values to override defaults

        Returns:
            Dictionary with inactive user data
        """
        inactive_data = UserFactory.create_user_data(overrides)
        inactive_data.update({
            "is_active": False,
            "subscription_active": False
        })

        if overrides:
            inactive_data.update(overrides)

        return inactive_data

    @staticmethod
    def create_users_batch(count: int, include_admin: bool = True) -> list:
        """
        Create a batch of user data dictionaries.

        Args:
            count: Number of users to create
            include_admin: Whether to include one admin user

        Returns:
            List of user data dictionaries
        """
        users = []

        for i in range(count):
            if i == 0 and include_admin:
                user_data = UserFactory.create_admin_data()
            else:
                user_data = UserFactory.create_user_data()
            users.append(user_data)

        return users

    @staticmethod
    def create_user_instance(db_session, overrides: Optional[Dict[str, Any]] = None) -> User:
        """
        Create and persist a User instance in the database.

        Args:
            db_session: Database session
            overrides: Dictionary of values to override defaults

        Returns:
            User instance
        """
        user_data = UserFactory.create_user_data(overrides)
        user = User(**user_data)
        user.set_password(user_data["password"])

        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        return user

    @staticmethod
    def create_admin_instance(db_session, overrides: Optional[Dict[str, Any]] = None) -> User:
        """
        Create and persist an admin User instance in the database.

        Args:
            db_session: Database session
            overrides: Dictionary of values to override defaults

        Returns:
            User instance
        """
        user_data = UserFactory.create_admin_data(overrides)
        user = User(**user_data)
        user.set_password(user_data["password"])

        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        return user

    @staticmethod
    def create_users_batch_instances(db_session, count: int, include_admin: bool = True) -> list:
        """
        Create and persist a batch of User instances in the database.

        Args:
            db_session: Database session
            count: Number of users to create
            include_admin: Whether to include one admin user

        Returns:
            List of User instances
        """
        users_data = UserFactory.create_users_batch(count, include_admin)
        users = []

        for user_data in users_data:
            user = User(**user_data)
            user.set_password(user_data["password"])
            users.append(user)

        db_session.add_all(users)
        db_session.commit()

        for user in users:
            db_session.refresh(user)

        return users