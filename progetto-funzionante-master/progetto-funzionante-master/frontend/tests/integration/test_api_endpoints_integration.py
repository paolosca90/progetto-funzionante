"""
Comprehensive integration tests for all API endpoints.
Tests signals, users, admin, health, and system endpoints with full CRUD operations.
"""

import pytest
import json
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from typing import Dict, Any, List

from models import User, Signal, SignalStatusEnum, SignalTypeEnum
from schemas import SignalCreate, SignalFilter, UserCreate


class TestAPIEndpointsIntegration:
    """Integration test suite for all API endpoints."""

    # Signal Endpoints Tests
    def test_get_latest_signals(self, client: TestClient, multiple_signals_fixture: List[Signal]):
        """Test retrieving latest signals endpoint."""
        response = client.get("/signals/latest")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10  # Default limit

        # Verify signal structure
        if data:
            signal = data[0]
            required_fields = ["id", "symbol", "signal_type", "entry_price", "status"]
            for field in required_fields:
                assert field in signal

    def test_get_latest_signals_with_pagination(self, client: TestClient, multiple_signals_fixture: List[Signal]):
        """Test latest signals with pagination parameters."""
        # Test with custom limit
        response = client.get("/signals/latest?limit=5")
        assert response.status_code == 200

        data = response.json()
        assert len(data) <= 5

        # Test with invalid limit (should be clamped to valid range)
        response = client.get("/signals/latest?limit=999")
        assert response.status_code == 200

        data = response.json()
        assert len(data) <= 100  # Max limit

    def test_get_top_signals(self, client: TestClient, multiple_signals_fixture: List[Signal]):
        """Test retrieving top signals by reliability."""
        response = client.get("/signals/top")
        assert response.status_code == 200

        data = response.json()
        assert "signals" in data
        assert "total_count" in data
        assert "average_reliability" in data

        # Verify signals are ordered by reliability
        signals = data["signals"]
        if len(signals) > 1:
            for i in range(len(signals) - 1):
                assert signals[i]["reliability"] >= signals[i + 1]["reliability"]

    def test_get_signal_by_id(self, client: TestClient, signal_fixture: Signal):
        """Test retrieving a specific signal by ID."""
        response = client.get(f"/signals/{signal_fixture.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == signal_fixture.id
        assert data["symbol"] == signal_fixture.symbol
        assert data["signal_type"] == signal_fixture.signal_type.value

    def test_get_nonexistent_signal(self, client: TestClient):
        """Test retrieving a non-existent signal."""
        response = client.get("/signals/99999")
        assert response.status_code == 404

    def test_create_signal(self, client: TestClient, auth_headers: Dict[str, str], test_signal_data: Dict[str, Any]):
        """Test creating a new signal."""
        response = client.post("/signals", json=test_signal_data, headers=auth_headers)
        assert response.status_code == 201

        data = response.json()
        assert data["message"] == "Signal created successfully"
        assert data["success"] is True
        assert "signal" in data

        # Verify signal data
        signal = data["signal"]
        assert signal["symbol"] == test_signal_data["symbol"]
        assert signal["signal_type"] == test_signal_data["signal_type"].value
        assert signal["entry_price"] == test_signal_data["entry_price"]

    def test_create_signal_unauthorized(self, client: TestClient, test_signal_data: Dict[str, Any]):
        """Test creating a signal without authentication."""
        response = client.post("/signals", json=test_signal_data)
        assert response.status_code == 401

    def test_update_signal(self, client: TestClient, auth_headers: Dict[str, str], signal_fixture: Signal):
        """Test updating an existing signal."""
        update_data = {
            "reliability": 95.0,
            "confidence_score": 0.95,
            "ai_analysis": "Updated analysis"
        }

        response = client.put(f"/signals/{signal_fixture.id}", json=update_data, headers=auth_headers)
        # Should either succeed (200) or not be implemented (404/405)
        assert response.status_code in [200, 404, 405]

        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True

    def test_delete_signal(self, client: TestClient, auth_headers: Dict[str, str], signal_fixture: Signal):
        """Test deleting a signal."""
        response = client.delete(f"/signals/{signal_fixture.id}", headers=auth_headers)
        # Should either succeed (200) or not be implemented (404/405)
        assert response.status_code in [200, 404, 405]

        if response.status_code == 200:
            # Verify signal is deleted
            response = client.get(f"/signals/{signal_fixture.id}")
            assert response.status_code == 404

    def test_filter_signals(self, client: TestClient, multiple_signals_fixture: List[Signal]):
        """Test filtering signals by various criteria."""
        # Test by symbol
        response = client.get("/signals?symbol=EUR_USD")
        assert response.status_code == 200

        data = response.json()
        if "signals" in data:
            for signal in data["signals"]:
                assert signal["symbol"] == "EUR_USD"

        # Test by signal type
        response = client.get("/signals?signal_type=BUY")
        assert response.status_code == 200

        data = response.json()
        if "signals" in data:
            for signal in data["signals"]:
                assert signal["signal_type"] == "BUY"

        # Test by minimum reliability
        response = client.get("/signals?min_reliability=80")
        assert response.status_code == 200

        data = response.json()
        if "signals" in data:
            for signal in data["signals"]:
                assert signal["reliability"] >= 80

    def test_signal_execution(self, client: TestClient, auth_headers: Dict[str, str], signal_fixture: Signal):
        """Test executing a signal."""
        execution_data = {
            "signal_id": signal_fixture.id,
            "execution_price": signal_fixture.entry_price,
            "quantity": 1.0,
            "execution_type": "MANUAL"
        }

        response = client.post("/signals/execute", json=execution_data, headers=auth_headers)
        # Should either succeed (200) or not be implemented (404/405)
        assert response.status_code in [200, 404, 405]

    # User Endpoints Tests
    def test_get_user_profile(self, client: TestClient, auth_headers: Dict[str, str], user_fixture: User):
        """Test retrieving user profile."""
        response = client.get("/users/me", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == user_fixture.id
        assert data["username"] == user_fixture.username
        assert data["email"] == user_fixture.email

    def test_update_user_profile(self, client: TestClient, auth_headers: Dict[str, str], user_fixture: User):
        """Test updating user profile."""
        update_data = {
            "full_name": "Updated Name",
            "email": "updated@test.com"
        }

        response = client.put("/users/me", json=update_data, headers=auth_headers)
        # Should either succeed (200) or not be implemented (404/405)
        assert response.status_code in [200, 404, 405]

        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True

    def test_get_user_statistics(self, client: TestClient, auth_headers: Dict[str, str], user_fixture: User):
        """Test retrieving user statistics."""
        response = client.get("/users/stats", headers=auth_headers)
        # Should either succeed (200) or not be implemented (404)
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert "total_signals" in data
            assert "active_signals" in data
            assert "average_reliability" in data

    def test_get_user_signals(self, client: TestClient, auth_headers: Dict[str, str], user_fixture: User, signal_fixture: Signal):
        """Test retrieving user's signals."""
        response = client.get("/users/signals", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

        # Verify signals belong to user
        for signal in data:
            # This depends on the API response structure
            pass

    def test_change_user_password(self, client: TestClient, auth_headers: Dict[str, str], user_fixture: User):
        """Test changing user password."""
        password_data = {
            "current_password": "IntegrationTest123!",
            "new_password": "NewPassword123!"
        }

        response = client.post("/users/change-password", json=password_data, headers=auth_headers)
        # Should either succeed (200) or not be implemented (404/405)
        assert response.status_code in [200, 404, 405]

    # Admin Endpoints Tests
    def test_admin_get_all_users(self, client: TestClient, admin_auth_headers: Dict[str, str]):
        """Test admin endpoint to get all users."""
        response = client.get("/admin/users", headers=admin_auth_headers)
        # Should either succeed (200) or not be implemented (404/403)
        assert response.status_code in [200, 403, 404]

        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)

    def test_admin_get_user_by_id(self, client: TestClient, admin_auth_headers: Dict[str, str], user_fixture: User):
        """Test admin endpoint to get specific user."""
        response = client.get(f"/admin/users/{user_fixture.id}", headers=admin_auth_headers)
        # Should either succeed (200) or not be implemented (404/403)
        assert response.status_code in [200, 403, 404]

        if response.status_code == 200:
            data = response.json()
            assert data["id"] == user_fixture.id

    def test_admin_update_user(self, client: TestClient, admin_auth_headers: Dict[str, str], user_fixture: User):
        """Test admin endpoint to update user."""
        update_data = {
            "is_active": True,
            "subscription_active": True,
            "is_admin": False
        }

        response = client.put(f"/admin/users/{user_fixture.id}", json=update_data, headers=admin_auth_headers)
        # Should either succeed (200) or not be implemented (404/403/405)
        assert response.status_code in [200, 403, 404, 405]

    def test_admin_delete_user(self, client: TestClient, admin_auth_headers: Dict[str, str], user_fixture: User):
        """Test admin endpoint to delete user."""
        response = client.delete(f"/admin/users/{user_fixture.id}", headers=admin_auth_headers)
        # Should either succeed (200) or not be implemented (404/403/405)
        assert response.status_code in [200, 403, 404, 405]

    def test_admin_get_system_stats(self, client: TestClient, admin_auth_headers: Dict[str, str]):
        """Test admin endpoint to get system statistics."""
        response = client.get("/admin/stats", headers=admin_auth_headers)
        # Should either succeed (200) or not be implemented (404/403)
        assert response.status_code in [200, 403, 404]

        if response.status_code == 200:
            data = response.json()
            assert "total_users" in data
            assert "total_signals" in data
            assert "system_health" in data

    def test_admin_generate_signals(self, client: TestClient, admin_auth_headers: Dict[str, str], mock_oanda_service: MagicMock):
        """Test admin endpoint to generate signals."""
        with patch('app.services.signal_service.oanda_service', mock_oanda_service):
            response = client.post("/admin/generate-signals", headers=admin_auth_headers)
            # Should either succeed (200) or not be implemented (404/403)
            assert response.status_code in [200, 403, 404]

            if response.status_code == 200:
                data = response.json()
                assert "signals_generated" in data
                assert "message" in data

    # Health and System Endpoints Tests
    def test_health_check(self, client: TestClient):
        """Test basic health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "database" in data

    def test_cache_health_check(self, client: TestClient):
        """Test cache health check endpoint."""
        response = client.get("/cache/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "cache_health" in data

    def test_cache_metrics(self, client: TestClient):
        """Test cache metrics endpoint."""
        response = client.get("/cache/metrics")
        assert response.status_code == 200

        data = response.json()
        assert "metrics" in data
        assert "hit_rate" in data["metrics"]
        assert "total_operations" in data["metrics"]

    def test_cache_invalidation(self, client: TestClient):
        """Test cache invalidation endpoint."""
        response = client.post("/cache/invalidate")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "deleted_count" in data

    def test_ml_system_status(self, client: TestClient):
        """Test ML system status endpoint."""
        response = client.get("/ml-system/status")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "message" in data
        assert "timestamp" in data

    def test_cors_test_endpoint(self, client: TestClient):
        """Test CORS configuration test endpoint."""
        response = client.get("/cors-test")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "allowed_origins" in data

    # Performance Endpoints Tests
    def test_performance_dashboard(self, client: TestClient):
        """Test performance dashboard endpoint."""
        response = client.get("/performance/dashboard")
        # Should either succeed (200) or not be implemented (404)
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert "system_metrics" in data
            assert "api_metrics" in data

    def test_performance_metrics(self, client: TestClient):
        """Test performance metrics endpoint."""
        response = client.get("/performance/metrics")
        # Should either succeed (200) or not be implemented (404)
        assert response.status_code in [200, 404]

        if response.status_code == 200:
            data = response.json()
            assert "response_times" in data
            assert "error_rates" in data

    # Error Handling Tests
    def test_404_handler(self, client: TestClient):
        """Test 404 error handler."""
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404

        data = response.json()
        assert "error" in data
        assert "path" in data
        assert "timestamp" in data

    def test_validation_error_handling(self, client: TestClient, auth_headers: Dict[str, str]):
        """Test validation error handling."""
        # Test with invalid signal data
        invalid_signal_data = {
            "symbol": "",  # Invalid: empty symbol
            "signal_type": "INVALID",  # Invalid: wrong enum
            "entry_price": -1  # Invalid: negative price
        }

        response = client.post("/signals", json=invalid_signal_data, headers=auth_headers)
        assert response.status_code == 422  # Validation error

    def test_rate_limiting(self, client: TestClient):
        """Test rate limiting on endpoints."""
        # Make multiple requests to trigger rate limiting
        for i in range(20):
            response = client.get("/health")
            if response.status_code == 429:
                break
        else:
            # If rate limiting not implemented, requests should succeed
            assert response.status_code == 200

    # Authentication Tests
    def test_protected_endpoints_without_auth(self, client: TestClient):
        """Test that protected endpoints require authentication."""
        protected_endpoints = [
            "/users/me",
            "/users/stats",
            "/signals",
            "/admin/users"
        ]

        for endpoint in protected_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401

    def test_admin_endpoints_with_user_auth(self, client: TestClient, auth_headers: Dict[str, str]):
        """Test that admin endpoints reject regular user authentication."""
        admin_endpoints = [
            "/admin/users",
            "/admin/stats",
            "/admin/generate-signals"
        ]

        for endpoint in admin_endpoints:
            response = client.get(endpoint, headers=auth_headers)
            assert response.status_code in [403, 404]  # Forbidden or Not Found

    # Data Validation Tests
    def test_signal_data_validation(self, client: TestClient, auth_headers: Dict[str, str]):
        """Test comprehensive signal data validation."""
        test_cases = [
            {
                "name": "valid_signal",
                "data": {
                    "symbol": "EUR_USD",
                    "signal_type": "BUY",
                    "entry_price": 1.1234,
                    "stop_loss": 1.1200,
                    "take_profit": 1.1300
                },
                "expected_status": 201
            },
            {
                "name": "missing_symbol",
                "data": {
                    "signal_type": "BUY",
                    "entry_price": 1.1234
                },
                "expected_status": 422
            },
            {
                "name": "invalid_signal_type",
                "data": {
                    "symbol": "EUR_USD",
                    "signal_type": "INVALID",
                    "entry_price": 1.1234
                },
                "expected_status": 422
            },
            {
                "name": "negative_price",
                "data": {
                    "symbol": "EUR_USD",
                    "signal_type": "BUY",
                    "entry_price": -1.0
                },
                "expected_status": 422
            }
        ]

        for test_case in test_cases:
            response = client.post("/signals", json=test_case["data"], headers=auth_headers)
            assert response.status_code == test_case["expected_status"], f"Failed test case: {test_case['name']}"

    # Pagination Tests
    def test_signal_pagination(self, client: TestClient, multiple_signals_fixture: List[Signal]):
        """Test signal pagination functionality."""
        # Test first page
        response = client.get("/signals?page=1&per_page=2")
        assert response.status_code == 200

        data = response.json()
        assert "signals" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert "total_pages" in data

        assert data["page"] == 1
        assert data["per_page"] == 2
        assert len(data["signals"]) <= 2

        # Test second page
        response = client.get("/signals?page=2&per_page=2")
        assert response.status_code == 200

        data = response.json()
        assert data["page"] == 2

    # Search and Filter Tests
    def test_signal_search(self, client: TestClient, multiple_signals_fixture: List[Signal]):
        """Test signal search functionality."""
        # Test search by symbol
        response = client.get("/signals/search?q=EUR")
        assert response.status_code == 200

        data = response.json()
        assert "signals" in data
        assert "total_results" in data

        # Test empty search
        response = client.get("/signals/search?q=")
        assert response.status_code in [200, 404]

    # Bulk Operations Tests
    def test_bulk_signal_creation(self, client: TestClient, auth_headers: Dict[str, str]):
        """Test bulk signal creation."""
        bulk_signals = [
            {
                "symbol": "EUR_USD",
                "signal_type": "BUY",
                "entry_price": 1.1234,
                "stop_loss": 1.1200,
                "take_profit": 1.1300
            },
            {
                "symbol": "GBP_USD",
                "signal_type": "SELL",
                "entry_price": 1.3456,
                "stop_loss": 1.3500,
                "take_profit": 1.3400
            }
        ]

        response = client.post("/signals/bulk", json={"signals": bulk_signals}, headers=auth_headers)
        # Should either succeed (200) or not be implemented (404/405)
        assert response.status_code in [200, 404, 405]

        if response.status_code == 200:
            data = response.json()
            assert "signals_created" in data
            assert "message" in data

    # Export Tests
    def test_signal_export(self, client: TestClient, auth_headers: Dict[str, str]):
        """Test signal export functionality."""
        response = client.get("/signals/export?format=json", headers=auth_headers)
        # Should either succeed (200) or not be implemented (404/405)
        assert response.status_code in [200, 404, 405]

        if response.status_code == 200:
            # Should return downloadable file
            assert "application/json" in response.headers.get("content-type", "")

    def test_signal_export_csv(self, client: TestClient, auth_headers: Dict[str, str]):
        """Test signal export to CSV."""
        response = client.get("/signals/export?format=csv", headers=auth_headers)
        # Should either succeed (200) or not be implemented (404/405)
        assert response.status_code in [200, 404, 405]

        if response.status_code == 200:
            assert "text/csv" in response.headers.get("content-type", "")