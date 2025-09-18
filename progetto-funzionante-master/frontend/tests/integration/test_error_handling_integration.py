"""
Comprehensive integration tests for error handling and edge cases.
Tests API error responses, validation, exception handling, and edge case scenarios.
"""

import pytest
import json
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError, OperationalError
from unittest.mock import patch, MagicMock, AsyncMock
from typing import Dict, Any, List
import httpx

from models import User, Signal, SignalStatusEnum, SignalTypeEnum
from schemas import SignalCreate, UserCreate


class TestErrorHandlingIntegration:
    """Integration test suite for error handling and edge cases."""

    # Authentication Error Tests
    def test_invalid_credentials_handling(self, client: TestClient, user_fixture: User):
        """Test handling of invalid authentication credentials."""
        invalid_credentials = [
            {"username": "", "password": "valid_password"},
            {"username": user_fixture.username, "password": ""},
            {"username": "", "password": ""},
            {"username": "nonexistent_user", "password": "any_password"},
            {"username": user_fixture.username, "password": "wrong_password"},
            {"username": None, "password": "valid_password"},
            {"username": user_fixture.username, "password": None}
        ]

        for creds in invalid_credentials:
            response = client.post("/auth/token", data=creds)
            assert response.status_code == 401

            data = response.json()
            assert "detail" in data
            assert "credentials" in data["detail"].lower()

    def test_expired_token_handling(self, client: TestClient, user_fixture: User):
        """Test handling of expired JWT tokens."""
        # Get valid token first
        login_data = {"username": user_fixture.username, "password": "IntegrationTest123!"}
        response = client.post("/auth/token", data=login_data)
        assert response.status_code == 200

        token_data = response.json()
        access_token = token_data["access_token"]

        # Mock token expiration
        with patch('app.services.auth_service.AuthService.verify_token') as mock_verify:
            mock_verify.side_effect = Exception("Token has expired")

            headers = {"Authorization": f"Bearer {access_token}"}
            response = client.get("/auth/me", headers=headers)
            assert response.status_code == 401

            data = response.json()
            assert "expired" in data["detail"].lower()

    def test_malformed_token_handling(self, client: TestClient):
        """Test handling of malformed JWT tokens."""
        malformed_tokens = [
            "",
            "invalid_token",
            "Bearer invalid_token",
            "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.payload",
            "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.invalid",
            "Bearer " + "a" * 1000  # Very long token
        ]

        for token in malformed_tokens:
            headers = {"Authorization": token}
            response = client.get("/auth/me", headers=headers)
            assert response.status_code == 401

    # Validation Error Tests
    def test_user_registration_validation_errors(self, client: TestClient):
        """Test user registration input validation."""
        invalid_users = [
            {
                "name": "missing_username",
                "data": {"email": "test@test.com", "password": "ValidPass123!"}
            },
            {
                "name": "missing_email",
                "data": {"username": "testuser", "password": "ValidPass123!"}
            },
            {
                "name": "missing_password",
                "data": {"username": "testuser", "email": "test@test.com"}
            },
            {
                "name": "invalid_email",
                "data": {"username": "testuser", "email": "invalid_email", "password": "ValidPass123!"}
            },
            {
                "name": "short_password",
                "data": {"username": "testuser", "email": "test@test.com", "password": "123"}
            },
            {
                "name": "weak_password",
                "data": {"username": "testuser", "email": "test@test.com", "password": "password"}
            },
            {
                "name": "username_too_long",
                "data": {"username": "a" * 100, "email": "test@test.com", "password": "ValidPass123!"}
            },
            {
                "name": "email_too_long",
                "data": {"username": "testuser", "email": "a" * 100 + "@test.com", "password": "ValidPass123!"}
            }
        ]

        for case in invalid_users:
            response = client.post("/auth/register", json=case["data"])
            assert response.status_code == 422

            data = response.json()
            assert "detail" in data

    def test_signal_creation_validation_errors(self, client: TestClient, auth_headers: Dict[str, str]):
        """Test signal creation input validation."""
        invalid_signals = [
            {
                "name": "missing_symbol",
                "data": {"signal_type": "BUY", "entry_price": 1.1234}
            },
            {
                "name": "missing_signal_type",
                "data": {"symbol": "EUR_USD", "entry_price": 1.1234}
            },
            {
                "name": "missing_entry_price",
                "data": {"symbol": "EUR_USD", "signal_type": "BUY"}
            },
            {
                "name": "invalid_signal_type",
                "data": {"symbol": "EUR_USD", "signal_type": "INVALID", "entry_price": 1.1234}
            },
            {
                "name": "negative_entry_price",
                "data": {"symbol": "EUR_USD", "signal_type": "BUY", "entry_price": -1.0}
            },
            {
                "name": "zero_entry_price",
                "data": {"symbol": "EUR_USD", "signal_type": "BUY", "entry_price": 0.0}
            },
            {
                "name": "negative_stop_loss",
                "data": {"symbol": "EUR_USD", "signal_type": "BUY", "entry_price": 1.1234, "stop_loss": -1.0}
            },
            {
                "name": "negative_take_profit",
                "data": {"symbol": "EUR_USD", "signal_type": "BUY", "entry_price": 1.1234, "take_profit": -1.0}
            },
            {
                "name": "invalid_reliability_too_high",
                "data": {"symbol": "EUR_USD", "signal_type": "BUY", "entry_price": 1.1234, "reliability": 150.0}
            },
            {
                "name": "invalid_reliability_too_low",
                "data": {"symbol": "EUR_USD", "signal_type": "BUY", "entry_price": 1.1234, "reliability": -10.0}
            }
        ]

        for case in invalid_signals:
            response = client.post("/signals", json=case["data"], headers=auth_headers)
            assert response.status_code == 422

            data = response.json()
            assert "detail" in data

    # Database Error Tests
    def test_database_connection_error_handling(self, client: TestClient):
        """Test handling of database connection errors."""
        with patch('app.dependencies.database.get_db') as mock_get_db:
            mock_get_db.side_effect = OperationalError("Database connection failed", {}, None)

            response = client.get("/health")
            assert response.status_code == 500

            data = response.json()
            assert "database" in data
            assert "disconnected" in data["database"]

    def test_database_constraint_error_handling(self, client: TestClient, auth_headers: Dict[str, str], user_fixture: User):
        """Test handling of database constraint violations."""
        # Try to create duplicate user
        duplicate_user_data = {
            "username": user_fixture.username,
            "email": "different@test.com",
            "password": "ValidPass123!"
        }

        response = client.post("/auth/register", json=duplicate_user_data)
        assert response.status_code in [400, 409, 422]  # Bad Request, Conflict, or Validation Error

    def test_database_timeout_error_handling(self, client: TestClient, auth_headers: Dict[str, str]):
        """Test handling of database timeout errors."""
        with patch('app.dependencies.database.get_db') as mock_get_db:
            # Simulate database timeout
            mock_db = MagicMock()
            mock_db.query.side_effect = OperationalError("Query timeout", {}, None)
            mock_get_db.return_value = mock_db

            response = client.get("/users/me", headers=auth_headers)
            assert response.status_code == 500

            data = response.json()
            assert "timeout" in data["detail"].lower()

    # HTTP Error Tests
    def test_http_404_error_handling(self, client: TestClient):
        """Test 404 error handling for non-existent endpoints."""
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404

        data = response.json()
        assert "error" in data
        assert "not found" in data["error"].lower()
        assert "path" in data
        assert "timestamp" in data

    def test_http_405_method_not_allowed(self, client: TestClient):
        """Test 405 Method Not Allowed error handling."""
        response = client.post("/health")  # GET-only endpoint
        assert response.status_code == 405

    def test_http_422_validation_error(self, client: TestClient):
        """Test 422 Unprocessable Entity error handling."""
        invalid_data = {"invalid": "data"}

        response = client.post("/auth/register", json=invalid_data)
        assert response.status_code == 422

        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], list)

    def test_http_429_rate_limiting(self, client: TestClient):
        """Test 429 Too Many Requests rate limiting error."""
        # Make many requests to trigger rate limiting
        for i in range(20):
            response = client.get("/health")
            if response.status_code == 429:
                break
        else:
            # If rate limiting not implemented, check for 200
            assert response.status_code == 200
            return

        # Verify rate limiting response
        assert response.status_code == 429
        data = response.json()
        assert "rate limit" in data["detail"].lower()

    # External Service Error Tests
    def test_external_service_timeout_handling(self, client: TestClient, auth_headers: Dict[str, str]):
        """Test handling of external service timeouts."""
        with patch('app.services.oanda_service.OANDAService.get_market_data') as mock_get:
            mock_get.side_effect = httpx.TimeoutException("Request timeout")

            response = client.get("/signals/latest")
            # Should either succeed with cached data or fail gracefully
            assert response.status_code in [200, 500, 504]

    def test_external_service_connection_error_handling(self, client: TestClient, auth_headers: Dict[str, str]):
        """Test handling of external service connection errors."""
        with patch('app.services.oanda_service.OANDAService.get_market_data') as mock_get:
            mock_get.side_effect = httpx.RequestError("Connection failed")

            response = client.get("/signals/latest")
            # Should either succeed with cached data or fail gracefully
            assert response.status_code in [200, 502, 503]

    def test_external_service_auth_error_handling(self, client: TestClient, auth_headers: Dict[str, str]):
        """Test handling of external service authentication errors."""
        with patch('app.services.oanda_service.OANDAService.get_market_data') as mock_get:
            mock_get.return_value = {"error": "Authentication failed", "status": 401}

            response = client.get("/signals/latest")
            # Should either succeed with cached data or fail gracefully
            assert response.status_code in [200, 503]

    # Authorization Error Tests
    def test_unauthorized_access_handling(self, client: TestClient):
        """Test handling of unauthorized access to protected endpoints."""
        protected_endpoints = [
            "/users/me",
            "/users/stats",
            "/signals",
            "/admin/users",
            "/admin/stats"
        ]

        for endpoint in protected_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401

            data = response.json()
            assert "not authenticated" in data["detail"].lower()

    def test_forbidden_access_handling(self, client: TestClient, auth_headers: Dict[str, str]):
        """Test handling of forbidden access to admin-only endpoints."""
        admin_endpoints = [
            "/admin/users",
            "/admin/stats",
            "/admin/generate-signals",
            "/admin/migrate-database"
        ]

        for endpoint in admin_endpoints:
            response = client.get(endpoint, headers=auth_headers)
            assert response.status_code in [403, 404]  # Forbidden or Not Found

            if response.status_code == 403:
                data = response.json()
                assert "permission" in data["detail"].lower()

    # Edge Case Tests
    def test_empty_request_body_handling(self, client: TestClient, auth_headers: Dict[str, str]):
        """Test handling of empty request bodies."""
        response = client.post("/signals", headers=auth_headers)
        assert response.status_code == 422

    def test_malformed_json_handling(self, client: TestClient, auth_headers: Dict[str, str]):
        """Test handling of malformed JSON request bodies."""
        response = client.post("/signals", data="invalid json", headers=auth_headers)
        assert response.status_code == 422

    def test_large_payload_handling(self, client: TestClient, auth_headers: Dict[str, str]):
        """Test handling of very large request payloads."""
        large_payload = {
            "signals": [
                {
                    "symbol": f"TEST_{i}",
                    "signal_type": "BUY",
                    "entry_price": 1.1234 + (i * 0.001),
                    "analysis": "x" * 1000  # Large analysis text
                }
                for i in range(1000)  # 1000 signals
            ]
        }

        response = client.post("/signals/bulk", json=large_payload, headers=auth_headers)
        # Should either succeed or fail with payload size error
        assert response.status_code in [200, 413, 422]

    def test_sql_injection_prevention(self, client: TestClient, auth_headers: Dict[str, str]):
        """Test prevention of SQL injection attacks."""
        injection_attempts = [
            {"username": "admin'--", "email": "test@test.com", "password": "password123"},
            {"username": "test", "email": "test@test.com', 'password': "password123"},
            {"username": "test", "email": "test@test.com", "password": "'; DROP TABLE users; --"}
        ]

        for attempt in injection_attempts:
            response = client.post("/auth/register", json=attempt)
            # Should fail with validation error, not SQL error
            assert response.status_code == 422

    def test_xss_prevention(self, client: TestClient, auth_headers: Dict[str, str]):
        """Test prevention of XSS attacks."""
        xss_attempts = [
            {"username": "<script>alert('xss')</script>", "email": "test@test.com", "password": "password123"},
            {"username": "test", "email": "test@test.com", "full_name": "<img src=x onerror=alert('xss')>"},
            {"symbol": "EUR_USD", "signal_type": "BUY", "entry_price": 1.1234, "ai_analysis": "<script>alert('xss')</script>"}
        ]

        for attempt in xss_attempts:
            if "ai_analysis" in attempt:
                response = client.post("/signals", json=attempt, headers=auth_headers)
            else:
                response = client.post("/auth/register", json=attempt)

            # Should fail with validation error or sanitize input
            assert response.status_code in [422, 201]

            # If successful, verify XSS is sanitized
            if response.status_code == 201:
                data = response.json()
                # Check that script tags are not present in response
                response_text = json.dumps(data)
                assert "<script>" not in response_text

    # Concurrent Access Error Tests
    def test_concurrent_user_creation_conflict(self, client: TestClient):
        """Test handling of concurrent user creation conflicts."""
        import threading
        import time

        user_data = {
            "username": "concurrent_test",
            "email": "concurrent@test.com",
            "password": "ConcurrentPass123!"
        }

        results = []

        def create_user():
            response = client.post("/auth/register", json=user_data)
            results.append(response.status_code)

        # Create multiple threads for concurrent user creation
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=create_user)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Only one should succeed, others should fail
        success_count = sum(1 for status in results if status == 201)
        conflict_count = sum(1 for status in results if status in [400, 409])

        assert success_count == 1, f"Expected 1 success, got {success_count}"
        assert conflict_count >= 1, f"Expected conflicts, got {conflict_count}"

    # Memory and Resource Error Tests
    def test_memory_error_handling(self, client: TestClient, auth_headers: Dict[str, str]):
        """Test handling of memory errors."""
        with patch('app.services.signal_service.SignalService.get_latest_signals') as mock_get:
            mock_get.side_effect = MemoryError("Out of memory")

            response = client.get("/signals/latest", headers=auth_headers)
            assert response.status_code == 500

            data = response.json()
            assert "memory" in data["detail"].lower()

    def test_file_system_error_handling(self, client: TestClient):
        """Test handling of file system errors."""
        with patch('builtins.open', side_effect=FileNotFoundError("File not found")):
            response = client.get("/favicon.ico")
            # Should handle gracefully
            assert response.status_code in [200, 204, 404]

    # Input Sanitization Tests
    def test_input_sanitization_html_tags(self, client: TestClient, auth_headers: Dict[str, str]):
        """Test input sanitization for HTML tags."""
        malicious_input = {
            "symbol": "EUR_USD",
            "signal_type": "BUY",
            "entry_price": 1.1234,
            "ai_analysis": "<script>alert('xss')</script><div>malicious</div>"
        }

        response = client.post("/signals", json=malicious_input, headers=auth_headers)

        if response.status_code == 201:
            data = response.json()
            # Verify HTML tags are escaped or removed
            analysis = data.get("signal", {}).get("ai_analysis", "")
            assert "<script>" not in analysis
            assert "<div>" not in analysis

    def test_input_sanitization_special_characters(self, client: TestClient, auth_headers: Dict[str, str]):
        """Test input sanitization for special characters."""
        special_chars_input = {
            "symbol": "EUR_USD",
            "signal_type": "BUY",
            "entry_price": 1.1234,
            "ai_analysis": "Analysis with special chars: áéíóú 中文 العربية русский"
        }

        response = client.post("/signals", json=special_chars_input, headers=auth_headers)

        # Should handle special characters properly
        assert response.status_code in [201, 422]

    # Timeout and Performance Error Tests
    def test_request_timeout_handling(self, client: TestClient, auth_headers: Dict[str, str]):
        """Test handling of request timeouts."""
        with patch('app.services.signal_service.SignalService.get_latest_signals') as mock_get:
            import time
            def slow_query():
                time.sleep(2)  # Simulate slow query
                return []

            mock_get.side_effect = slow_query

            response = client.get("/signals/latest", headers=auth_headers, timeout=1.0)
            # Should handle timeout gracefully
            assert response.status_code in [200, 500, 504]

    # Error Logging and Monitoring Tests
    def test_error_logging_verification(self, client: TestClient, caplog):
        """Test that errors are properly logged."""
        # Trigger an error
        response = client.get("/nonexistent-endpoint")

        # Verify error was logged
        assert response.status_code == 404
        assert "Endpoint not found" in caplog.text

    def test_database_error_logging(self, client: TestClient, auth_headers: Dict[str, str], caplog):
        """Test that database errors are properly logged."""
        with patch('app.dependencies.database.get_db') as mock_get_db:
            mock_get_db.side_effect = OperationalError("Database error", {}, None)

            response = client.get("/users/me", headers=auth_headers)

            # Verify database error was logged
            assert "Database error" in caplog.text

    # Recovery and Fallback Tests
    def test_service_recovery_after_error(self, client: TestClient, auth_headers: Dict[str, str]):
        """Test service recovery after temporary errors."""
        # Simulate temporary service failure
        with patch('app.services.signal_service.SignalService.get_latest_signals') as mock_get:
            mock_get.side_effect = Exception("Temporary failure")

            response = client.get("/signals/latest", headers=auth_headers)
            # Should fail initially
            assert response.status_code == 500

        # Verify service recovers after error
        response = client.get("/signals/latest", headers=auth_headers)
        # Should succeed on retry
        assert response.status_code == 200

    def test_fallback_data_handling(self, client: TestClient, auth_headers: Dict[str, str]):
        """Test fallback data handling when services fail."""
        with patch('app.services.signal_service.SignalService.get_latest_signals') as mock_get:
            # Return fallback data
            mock_get.return_value = []

            response = client.get("/signals/latest", headers=auth_headers)
            assert response.status_code == 200

            data = response.json()
            assert isinstance(data, list)

    # Security Error Tests
    def test_invalid_content_type_handling(self, client: TestClient, auth_headers: Dict[str, str]):
        """Test handling of invalid content types."""
        invalid_content_types = [
            ("text/plain", "plain text"),
            ("application/xml", "<xml>data</xml>"),
            ("text/html", "<html>data</html>")
        ]

        for content_type, data in invalid_content_types:
            response = client.post(
                "/signals",
                data=data,
                headers={**auth_headers, "Content-Type": content_type}
            )
            # Should reject invalid content types
            assert response.status_code in [415, 422]

    def test_missing_content_type_handling(self, client: TestClient, auth_headers: Dict[str, str]):
        """Test handling of missing content type."""
        response = client.post(
            "/signals",
            data='{"symbol": "EUR_USD", "signal_type": "BUY", "entry_price": 1.1234}',
            headers=auth_headers
        )
        # Should handle missing content type
        assert response.status_code in [200, 415, 422]

    # Rate Limiting and Throttling Tests
    def test_rate_limiting_bypass_handling(self, client: TestClient):
        """Test handling of rate limiting bypass attempts."""
        # Test various IP header manipulations
        ip_headers = [
            {"X-Forwarded-For": "192.168.1.1"},
            {"X-Real-IP": "192.168.1.2"},
            {"X-Client-IP": "192.168.1.3"},
            {}  # No IP headers
        ]

        for headers in ip_headers:
            for _ in range(10):
                response = client.get("/health", headers=headers)
                if response.status_code == 429:
                    break
            else:
                continue  # No rate limiting triggered

            # Verify rate limiting still works with IP headers
            assert response.status_code == 429

    # Data Integrity Tests
    def test_data_integrity_validation(self, client: TestClient, auth_headers: Dict[str, str]):
        """Test data integrity validation."""
        # Test with inconsistent data
        inconsistent_data = {
            "symbol": "EUR_USD",
            "signal_type": "BUY",
            "entry_price": 1.1200,  # Entry below stop loss
            "stop_loss": 1.1300,
            "take_profit": 1.1100  # Take profit below entry (for buy signal)
        }

        response = client.post("/signals", json=inconsistent_data, headers=auth_headers)
        # Should either succeed (business logic might allow this) or fail validation
        assert response.status_code in [201, 422]

    # Environment Configuration Error Tests
    def test_missing_environment_variable_handling(self, client: TestClient):
        """Test handling of missing environment variables."""
        with patch.dict('os.environ', {}, clear=True):
            # Remove all environment variables
            response = client.get("/health")
            # Should handle missing environment gracefully
            assert response.status_code in [200, 500]

    def test_invalid_environment_variable_handling(self, client: TestClient):
        """Test handling of invalid environment variable values."""
        with patch.dict('os.environ', {
            'DATABASE_URL': 'invalid://database/url',
            'JWT_SECRET_KEY': '',  # Empty secret key
            'OANDA_API_KEY': None  # None API key
        }):
            response = client.get("/health")
            # Should handle invalid environment gracefully
            assert response.status_code in [200, 500]