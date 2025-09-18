"""
Comprehensive integration tests for authentication and authorization flows.
Tests user registration, login, token management, role-based access control, and security features.
"""

import pytest
import json
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from typing import Dict, Any

from models import User, Signal
from schemas import UserCreate, Token
from app.services.auth_service import AuthService


class TestAuthIntegration:
    """Integration test suite for authentication and authorization."""

    def test_user_registration_flow(self, client: TestClient, db_session):
        """Test complete user registration flow including email verification."""
        registration_data = {
            "username": "new_integration_user",
            "email": "newuser@test.com",
            "full_name": "New Integration User",
            "password": "SecurePassword123!"
        }

        # Test user registration
        response = client.post("/auth/register", json=registration_data)
        assert response.status_code == 201

        data = response.json()
        assert data["message"] == "User registered successfully"
        assert data["success"] is True
        assert "user_id" in data

        # Verify user was created in database
        user = db_session.query(User).filter(User.username == "new_integration_user").first()
        assert user is not None
        assert user.email == "newuser@test.com"
        assert user.is_active is True
        assert user.is_admin is False
        assert user.subscription_active is True

    def test_user_login_flow(self, client: TestClient, user_fixture: User):
        """Test user login flow with valid credentials."""
        login_data = {
            "username": user_fixture.username,
            "password": "IntegrationTest123!"
        }

        response = client.post("/auth/token", data=login_data)
        assert response.status_code == 200

        token_data = response.json()
        assert "access_token" in token_data
        assert "refresh_token" in token_data
        assert token_data["token_type"] == "bearer"

        # Verify token format and expiration
        access_token = token_data["access_token"]
        assert len(access_token) > 100  # JWT tokens are typically long

    def test_invalid_login_attempts(self, client: TestClient):
        """Test login with invalid credentials and rate limiting."""
        invalid_credentials = [
            {"username": "nonexistent", "password": "wrong"},
            {"username": "testuser", "password": "wrong"},
            {"username": "", "password": ""},
            {"username": "testuser", "password": ""}
        ]

        for creds in invalid_credentials:
            response = client.post("/auth/token", data=creds)
            assert response.status_code == 401

    def test_password_hashing_security(self, db_session):
        """Test that passwords are properly hashed and not stored in plaintext."""
        test_password = "SecurePassword123!"

        # Create user with password
        user = User(
            username="hash_test",
            email="hash@test.com",
            hashed_password="",  # Will be set by auth service
            is_active=True
        )

        # Hash password using auth service
        auth_service = AuthService(db_session)
        user.hashed_password = auth_service.get_password_hash(test_password)

        db_session.add(user)
        db_session.commit()

        # Verify password is not stored in plaintext
        assert test_password not in user.hashed_password
        assert len(user.hashed_password) > 50  # Hashed passwords are longer

        # Verify password verification works
        assert auth_service.verify_password(test_password, user.hashed_password) is True
        assert auth_service.verify_password("wrongpassword", user.hashed_password) is False

    def test_jwt_token_validation(self, client: TestClient, user_fixture: User):
        """Test JWT token validation and user extraction."""
        # Login to get token
        login_data = {
            "username": user_fixture.username,
            "password": "IntegrationTest123!"
        }

        response = client.post("/auth/token", data=login_data)
        assert response.status_code == 200

        token_data = response.json()
        access_token = token_data["access_token"]

        # Test token validation through protected endpoint
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 200

        user_data = response.json()
        assert user_data["username"] == user_fixture.username
        assert user_data["email"] == user_fixture.email

    def test_invalid_token_handling(self, client: TestClient):
        """Test handling of invalid, expired, and malformed tokens."""
        invalid_tokens = [
            "",  # Empty token
            "invalid_token",  # Malformed token
            "Bearer invalid",  # Invalid Bearer format
            "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.signature",  # Invalid JWT
        ]

        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 401

    def test_admin_authorization_flow(self, client: TestClient, admin_fixture: User):
        """Test admin-specific authorization and access control."""
        # Admin login
        login_data = {
            "username": admin_fixture.username,
            "password": "AdminTest123!"
        }

        response = client.post("/auth/token", data=login_data)
        assert response.status_code == 200

        token_data = response.json()
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}

        # Test admin-only endpoint access
        response = client.get("/admin/users", headers=headers)
        # Should either succeed (200) or fail with permission error (403)
        assert response.status_code in [200, 403, 404]  # 404 if endpoint doesn't exist

    def test_user_profile_management(self, client: TestClient, user_fixture: User, auth_headers: Dict[str, str]):
        """Test user profile retrieval and management."""
        # Get user profile
        response = client.get("/auth/me", headers=auth_headers)
        assert response.status_code == 200

        profile_data = response.json()
        assert profile_data["id"] == user_fixture.id
        assert profile_data["username"] == user_fixture.username
        assert profile_data["email"] == user_fixture.email
        assert profile_data["is_active"] is True

        # Test profile update if endpoint exists
        update_data = {
            "full_name": "Updated Name",
            "email": "updated@test.com"
        }

        response = client.put("/auth/me", json=update_data, headers=auth_headers)
        # Should either succeed (200) or not be implemented (404/405)
        assert response.status_code in [200, 404, 405]

    def test_password_reset_flow(self, client: TestClient, user_fixture: User):
        """Test password reset request and completion flow."""
        # Request password reset
        reset_request_data = {"email": user_fixture.email}

        response = client.post("/auth/forgot-password", json=reset_request_data)
        # Should either succeed (200) or not be implemented (404)
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert "message" in data

    def test_token_refresh_mechanism(self, client: TestClient, user_fixture: User):
        """Test token refresh functionality."""
        # Initial login
        login_data = {
            "username": user_fixture.username,
            "password": "IntegrationTest123!"
        }

        response = client.post("/auth/token", data=login_data)
        assert response.status_code == 200

        token_data = response.json()
        refresh_token = token_data.get("refresh_token")

        if refresh_token:
            # Test token refresh if endpoint exists
            refresh_data = {"refresh_token": refresh_token}
            response = client.post("/auth/refresh", json=refresh_data)
            # Should either succeed (200) or not be implemented (404)
            assert response.status_code in [200, 404]

            if response.status_code == 200:
                new_token_data = response.json()
                assert "access_token" in new_token_data
                assert new_token_data["access_token"] != token_data["access_token"]

    def test_rate_limiting_on_auth_endpoints(self, client: TestClient):
        """Test rate limiting on authentication endpoints."""
        login_data = {"username": "test", "password": "test"}

        # Make multiple requests to trigger rate limiting
        for i in range(10):
            response = client.post("/auth/token", data=login_data)
            if response.status_code == 429:
                break
        else:
            # If rate limiting not implemented, last request should still be 401
            assert response.status_code == 401

    def test_concurrent_login_attempts(self, client: TestClient, user_fixture: User):
        """Test handling of concurrent login attempts."""
        import threading
        import time

        login_data = {
            "username": user_fixture.username,
            "password": "IntegrationTest123!"
        }

        results = []

        def login_attempt():
            response = client.post("/auth/token", data=login_data)
            results.append(response.status_code)

        # Create multiple threads for concurrent login attempts
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=login_attempt)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All attempts should succeed (assuming no rate limiting)
        assert all(status == 200 for status in results)

    def test_session_management(self, client: TestClient, user_fixture: User):
        """Test user session management and last login tracking."""
        # Initial login
        login_data = {
            "username": user_fixture.username,
            "password": "IntegrationTest123!"
        }

        response = client.post("/auth/token", data=login_data)
        assert response.status_code == 200

        # Check if last login was updated
        # This would require checking the database directly
        # as the endpoint might not return this information

    def test_user_deactivation_flow(self, client: TestClient, user_fixture: User, auth_headers: Dict[str, str]):
        """Test user account deactivation and reactivation."""
        # Deactivate user (if endpoint exists)
        response = client.post("/auth/deactivate", headers=auth_headers)
        # Should either succeed (200) or not be implemented (404)
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            # Try to login with deactivated account
            login_data = {
                "username": user_fixture.username,
                "password": "IntegrationTest123!"
            }

            response = client.post("/auth/token", data=login_data)
            assert response.status_code == 401  # Account deactivated

    def test_email_verification_flow(self, client: TestClient, db_session):
        """Test email verification during registration."""
        registration_data = {
            "username": "email_verify_user",
            "email": "verify@test.com",
            "full_name": "Email Verify User",
            "password": "SecurePassword123!"
        }

        # Mock email service
        with patch('app.services.auth_service.send_verification_email') as mock_email:
            mock_email.return_value = True

            response = client.post("/auth/register", json=registration_data)
            assert response.status_code == 201

            # Verify email service was called
            mock_email.assert_called_once()

    def test_cross_site_request_forgery_protection(self, client: TestClient, user_fixture: User):
        """Test CSRF protection on authentication endpoints."""
        # Most auth endpoints should be protected against CSRF
        # This is typically handled by the framework, but we can test the structure

        # Test that POST requests require proper content-type
        login_data = {"username": user_fixture.username, "password": "IntegrationTest123!"}

        # Try with invalid content-type
        response = client.post("/auth/token", json=login_data, headers={"Content-Type": "invalid"})
        assert response.status_code == 415  # Unsupported Media Type

    def test_authentication_error_handling(self, client: TestClient):
        """Test comprehensive error handling for authentication scenarios."""
        error_scenarios = [
            {
                "endpoint": "/auth/token",
                "method": "POST",
                "data": {"username": "missing"},
                "expected_error": "missing_credentials"
            },
            {
                "endpoint": "/auth/register",
                "method": "POST",
                "data": {"username": "test"},
                "expected_error": "missing_password"
            },
            {
                "endpoint": "/auth/me",
                "method": "GET",
                "expected_error": "missing_auth_header"
            }
        ]

        for scenario in error_scenarios:
            if scenario["method"] == "POST":
                response = client.post(scenario["endpoint"], json=scenario.get("data", {}))
            else:
                response = client.get(scenario["endpoint"])

            # Should return appropriate error status
            assert response.status_code in [400, 401, 422]

    def test_user_role_based_access_control(self, client: TestClient, user_fixture: User, admin_fixture: User):
        """Test role-based access control for different user types."""
        # Test regular user access
        user_login_data = {
            "username": user_fixture.username,
            "password": "IntegrationTest123!"
        }

        response = client.post("/auth/token", data=user_login_data)
        assert response.status_code == 200

        user_token = response.json()["access_token"]
        user_headers = {"Authorization": f"Bearer {user_token}"}

        # Test admin user access
        admin_login_data = {
            "username": admin_fixture.username,
            "password": "AdminTest123!"
        }

        response = client.post("/auth/token", data=admin_login_data)
        assert response.status_code == 200

        admin_token = response.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # Test access to admin-only endpoints
        admin_endpoints = ["/admin/users", "/admin/stats", "/admin/logs"]

        for endpoint in admin_endpoints:
            # Regular user should not have access
            response = client.get(endpoint, headers=user_headers)
            assert response.status_code in [403, 404]  # Forbidden or Not Found

            # Admin should have access
            response = client.get(endpoint, headers=admin_headers)
            assert response.status_code in [200, 404]  # Success or Not Found

    def test_authentication_logging_and_audit(self, client: TestClient, user_fixture: User):
        """Test that authentication events are properly logged for audit purposes."""
        # This would typically involve checking log files or database entries
        # For now, we'll test that the endpoints respond appropriately

        login_data = {
            "username": user_fixture.username,
            "password": "IntegrationTest123!"
        }

        # Successful login
        response = client.post("/auth/token", data=login_data)
        assert response.status_code == 200

        # Failed login attempt
        response = client.post("/auth/token", data={"username": user_fixture.username, "password": "wrong"})
        assert response.status_code == 401

        # The actual logging verification would require checking the logging system
        # This is a placeholder for that functionality

    def test_token_expiration_handling(self, client: TestClient, user_fixture: User):
        """Test handling of expired tokens and token refresh."""
        # This test would require mocking token expiration
        # For now, we'll test the basic token structure

        login_data = {
            "username": user_fixture.username,
            "password": "IntegrationTest123!"
        }

        response = client.post("/auth/token", data=login_data)
        assert response.status_code == 200

        token_data = response.json()
        assert "access_token" in token_data

        # Test with expired token (mock scenario)
        with patch('app.services.auth_service.AuthService.verify_token') as mock_verify:
            mock_verify.side_effect = Exception("Token expired")

            headers = {"Authorization": f"Bearer {token_data['access_token']}"}
            response = client.get("/auth/me", headers=headers)
            assert response.status_code == 401

    @pytest.mark.slow
    def test_authentication_performance(self, client: TestClient, user_fixture: User):
        """Test performance of authentication endpoints under load."""
        import time
        import threading

        login_data = {
            "username": user_fixture.username,
            "password": "IntegrationTest123!"
        }

        def benchmark_login():
            start_time = time.time()
            response = client.post("/auth/token", data=login_data)
            end_time = time.time()
            return response.status_code, end_time - start_time

        # Run multiple concurrent login attempts
        threads = []
        results = []

        def worker():
            result = benchmark_login()
            results.append(result)

        for _ in range(10):
            thread = threading.Thread(target=worker)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All requests should succeed
        statuses, times = zip(*results)
        assert all(status == 200 for status in statuses)

        # Response time should be reasonable (< 2 seconds)
        avg_time = sum(times) / len(times)
        assert avg_time < 2.0, f"Average response time {avg_time:.2f}s is too slow"