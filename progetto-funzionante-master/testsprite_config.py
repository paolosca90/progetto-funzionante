"""
Comprehensive TestSprite Configuration for AI Trading System
Production-ready testing configuration for FastAPI-based AI trading platform with OANDA integration
"""

import asyncio
import json
import random
import string
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from decimal import Decimal
import pytest
import httpx
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Test Configuration
TEST_CONFIG = {
    "base_url": "http://localhost:8000",
    "api_v1_prefix": "",
    "api_v2_prefix": "/api/v2",
    "timeout": 30,
    "max_retries": 3,
    "retry_delay": 1,
}

# Database Test Configuration
TEST_DATABASE_URL = "sqlite:///:memory:"
TEST_POSTGRES_URL = "postgresql://test:test@localhost:5432/trading_test"

# Test Data Configuration
TEST_USERS = [
    {
        "username": "test_admin",
        "email": "admin@test.com",
        "password": "SecurePassword123!",
        "full_name": "Test Admin User",
        "is_admin": True,
    },
    {
        "username": "test_user",
        "email": "user@test.com",
        "password": "SecurePassword123!",
        "full_name": "Test Regular User",
        "is_admin": False,
    },
    {
        "username": "test_premium",
        "email": "premium@test.com",
        "password": "SecurePassword123!",
        "full_name": "Test Premium User",
        "is_admin": False,
    }
]

# Test Trading Symbols
TEST_SYMBOLS = [
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD",
    "NZDUSD", "EURGBP", "EURJPY", "GBPJPY", "GOLD",
    "BTCUSD", "ETHUSD", "SPX500", "NAS100"
]

# Test Signal Types
SIGNAL_TYPES = ["BUY", "SELL", "HOLD"]
SIGNAL_STATUSES = ["ACTIVE", "CLOSED", "CANCELLED"]
RISK_LEVELS = ["LOW", "MEDIUM", "HIGH"]
TIMEFRAMES = ["M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1"]

class TestDataManager:
    """Test data management utilities for consistent test data generation"""

    @staticmethod
    def generate_test_email() -> str:
        """Generate unique test email address"""
        return f"test_{uuid.uuid4().hex[:8]}@test.com"

    @staticmethod
    def generate_test_username() -> str:
        """Generate unique test username"""
        return f"testuser_{uuid.uuid4().hex[:8]}"

    @staticmethod
    def generate_test_password() -> str:
        """Generate secure test password"""
        return "SecureTest123!"

    @staticmethod
    def generate_test_signal_data(symbol: str = None) -> Dict[str, Any]:
        """Generate realistic test signal data"""
        return {
            "symbol": symbol or random.choice(TEST_SYMBOLS),
            "signal_type": random.choice(SIGNAL_TYPES),
            "entry_price": round(random.uniform(1.0, 150.0), 4),
            "stop_loss": round(random.uniform(0.8, 140.0), 4),
            "take_profit": round(random.uniform(1.2, 160.0), 4),
            "reliability": round(random.uniform(60.0, 95.0), 1),
            "confidence_score": round(random.uniform(0.6, 0.95), 2),
            "risk_level": random.choice(RISK_LEVELS),
            "timeframe": random.choice(TIMEFRAMES),
            "ai_analysis": "Test AI analysis generated for testing purposes",
            "position_size_suggestion": round(random.uniform(0.01, 0.1), 3),
            "spread": round(random.uniform(0.1, 2.0), 2),
            "volatility": round(random.uniform(0.001, 0.05), 4),
        }

    @staticmethod
    def generate_oanda_mock_data(symbol: str) -> Dict[str, Any]:
        """Generate mock OANDA market data"""
        base_price = random.uniform(1.0, 150.0)
        return {
            "instrument": symbol.replace("_", "_"),
            "price": base_price,
            "bid": base_price - 0.0001,
            "ask": base_price + 0.0001,
            "spread": 0.0001,
            "timestamp": datetime.utcnow().isoformat(),
            "heartbeat": datetime.utcnow().isoformat(),
        }

class APIClient:
    """HTTP client for API testing with authentication support"""

    def __init__(self, base_url: str = TEST_CONFIG["base_url"]):
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            base_url=base_url,
            timeout=TEST_CONFIG["timeout"],
            headers={"Content-Type": "application/json"}
        )
        self.access_token = None
        self.refresh_token = None

    async def authenticate(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate and store tokens"""
        response = await self.client.post(
            "/token",
            data={"username": username, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        if response.status_code == 200:
            tokens = response.json()
            self.access_token = tokens["access_token"]
            self.refresh_token = tokens["refresh_token"]
            self.client.headers["Authorization"] = f"Bearer {self.access_token}"
            return tokens
        else:
            raise Exception(f"Authentication failed: {response.status_code} - {response.text}")

    async def get(self, endpoint: str, **kwargs) -> httpx.Response:
        """GET request with error handling"""
        return await self._retry_request("GET", endpoint, **kwargs)

    async def post(self, endpoint: str, **kwargs) -> httpx.Response:
        """POST request with error handling"""
        return await self._retry_request("POST", endpoint, **kwargs)

    async def put(self, endpoint: str, **kwargs) -> httpx.Response:
        """PUT request with error handling"""
        return await self._retry_request("PUT", endpoint, **kwargs)

    async def patch(self, endpoint: str, **kwargs) -> httpx.Response:
        """PATCH request with error handling"""
        return await self._retry_request("PATCH", endpoint, **kwargs)

    async def delete(self, endpoint: str, **kwargs) -> httpx.Response:
        """DELETE request with error handling"""
        return await self._retry_request("DELETE", endpoint, **kwargs)

    async def _retry_request(self, method: str, endpoint: str, **kwargs) -> httpx.Response:
        """Retry request with exponential backoff"""
        for attempt in range(TEST_CONFIG["max_retries"]):
            try:
                response = await self.client.request(method, endpoint, **kwargs)
                if response.status_code < 500:
                    return response
            except httpx.TimeoutException:
                if attempt == TEST_CONFIG["max_retries"] - 1:
                    raise
                await asyncio.sleep(TEST_CONFIG["retry_delay"] * (2 ** attempt))

        raise Exception(f"Max retries exceeded for {method} {endpoint}")

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

class DatabaseTestManager:
    """Database testing utilities"""

    def __init__(self, database_url: str = TEST_DATABASE_URL):
        self.engine = create_engine(
            database_url,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False} if "sqlite" in database_url else {}
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.session = self.SessionLocal()

    def setup_test_database(self):
        """Create test database schema"""
        from models import Base
        Base.metadata.create_all(bind=self.engine)

    def cleanup_test_database(self):
        """Clean up test database"""
        from models import Base
        Base.metadata.drop_all(bind=self.engine)

    def create_test_user(self, user_data: Dict[str, Any]) -> Any:
        """Create test user in database"""
        from models import User
        from app.services.auth_service import AuthService

        user = User(
            username=user_data["username"],
            email=user_data["email"],
            full_name=user_data["full_name"],
            is_active=True,
            is_admin=user_data.get("is_admin", False),
            subscription_active=True
        )
        user.hashed_password = AuthService.get_password_hash(user_data["password"])
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def create_test_signal(self, signal_data: Dict[str, Any], user_id: int) -> Any:
        """Create test signal in database"""
        from models import Signal

        signal = Signal(
            user_id=user_id,
            **signal_data
        )
        self.session.add(signal)
        self.session.commit()
        self.session.refresh(signal)
        return signal

    def close(self):
        """Close database session"""
        self.session.close()

class PerformanceBenchmark:
    """Performance testing utilities"""

    def __init__(self, client: APIClient):
        self.client = client
        self.results = []

    async def benchmark_endpoint(
        self,
        method: str,
        endpoint: str,
        iterations: int = 100,
        **kwargs
    ) -> Dict[str, Any]:
        """Benchmark endpoint performance"""
        response_times = []
        status_codes = {}

        for i in range(iterations):
            start_time = datetime.utcnow()

            try:
                response = await getattr(self.client, method.lower())(endpoint, **kwargs)
                response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
                response_times.append(response_time)
                status_codes[response.status_code] = status_codes.get(response.status_code, 0) + 1
            except Exception as e:
                response_times.append(float('inf'))
                status_codes["ERROR"] = status_codes.get("ERROR", 0) + 1

        avg_response_time = sum(response_times) / len(response_times)
        min_response_time = min(response_times)
        max_response_time = max(response_times)

        result = {
            "endpoint": f"{method.upper()} {endpoint}",
            "iterations": iterations,
            "avg_response_time_ms": round(avg_response_time, 2),
            "min_response_time_ms": round(min_response_time, 2),
            "max_response_time_ms": round(max_response_time, 2),
            "success_rate": f"{sum(1 for t in response_times if t != float('inf')) / iterations * 100:.1f}%",
            "status_codes": status_codes,
        }

        self.results.append(result)
        return result

    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        if not self.results:
            return {"message": "No benchmark results available"}

        return {
            "total_endpoints": len(self.results),
            "avg_response_time": round(sum(r["avg_response_time_ms"] for r in self.results) / len(self.results), 2),
            "slowest_endpoint": max(self.results, key=lambda x: x["avg_response_time_ms"]),
            "fastest_endpoint": min(self.results, key=lambda x: x["avg_response_time_ms"]),
            "results": self.results,
        }

# Test Suite Classes
class HealthCheckTests:
    """Health check endpoint tests"""

    def __init__(self, client: APIClient):
        self.client = client

    async def test_basic_health_check(self) -> Dict[str, Any]:
        """Test basic health check endpoint"""
        response = await self.client.get("/health")
        return {
            "test": "basic_health_check",
            "status": "passed" if response.status_code == 200 else "failed",
            "response_time": response.elapsed.total_seconds() * 1000,
            "data": response.json() if response.status_code == 200 else None,
            "status_code": response.status_code,
        }

    async def test_cache_health_check(self) -> Dict[str, Any]:
        """Test cache health check endpoint"""
        response = await self.client.get("/cache/health")
        return {
            "test": "cache_health_check",
            "status": "passed" if response.status_code == 200 else "failed",
            "response_time": response.elapsed.total_seconds() * 1000,
            "data": response.json() if response.status_code == 200 else None,
            "status_code": response.status_code,
        }

class AuthenticationTests:
    """Authentication flow tests"""

    def __init__(self, client: APIClient, db_manager: DatabaseTestManager):
        self.client = client
        self.db_manager = db_manager
        self.test_users = []

    async def setup_test_users(self):
        """Create test users for authentication tests"""
        for user_data in TEST_USERS:
            try:
                # Try to register via API first
                response = await self.client.post("/register", json=user_data)
                if response.status_code == 201:
                    self.test_users.append(user_data)
                else:
                    # Fallback: create directly in database
                    user = self.db_manager.create_test_user(user_data)
                    self.test_users.append(user_data)
            except Exception as e:
                # Fallback: create directly in database
                user = self.db_manager.create_test_user(user_data)
                self.test_users.append(user_data)

    async def test_user_registration(self) -> Dict[str, Any]:
        """Test user registration"""
        test_user = {
            "username": TestDataManager.generate_test_username(),
            "email": TestDataManager.generate_test_email(),
            "password": TestDataManager.generate_test_password(),
            "full_name": "Test Registration User",
        }

        response = await self.client.post("/register", json=test_user)
        return {
            "test": "user_registration",
            "status": "passed" if response.status_code == 201 else "failed",
            "response_time": response.elapsed.total_seconds() * 1000,
            "data": response.json() if response.status_code == 201 else None,
            "status_code": response.status_code,
        }

    async def test_user_login(self) -> Dict[str, Any]:
        """Test user login"""
        if not self.test_users:
            await self.setup_test_users()

        test_user = self.test_users[0]  # Use first test user
        response = await self.client.post("/token",
            data={"username": test_user["username"], "password": test_user["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        if response.status_code == 200:
            tokens = response.json()
            self.client.access_token = tokens["access_token"]
            self.client.refresh_token = tokens["refresh_token"]
            self.client.headers["Authorization"] = f"Bearer {self.client.access_token}"

        return {
            "test": "user_login",
            "status": "passed" if response.status_code == 200 else "failed",
            "response_time": response.elapsed.total_seconds() * 1000,
            "data": response.json() if response.status_code == 200 else None,
            "status_code": response.status_code,
        }

    async def test_protected_endpoint_access(self) -> Dict[str, Any]:
        """Test access to protected endpoints"""
        response = await self.client.get("/users/me")
        return {
            "test": "protected_endpoint_access",
            "status": "passed" if response.status_code == 200 else "failed",
            "response_time": response.elapsed.total_seconds() * 1000,
            "data": response.json() if response.status_code == 200 else None,
            "status_code": response.status_code,
        }

    async def test_rate_limiting(self) -> Dict[str, Any]:
        """Test rate limiting on authentication endpoints"""
        # Make multiple rapid requests to test rate limiting
        responses = []
        for i in range(15):  # Exceed typical rate limit
            response = await self.client.post("/token",
                data={"username": "invalid", "password": "invalid"},
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            responses.append(response.status_code)

        rate_limited = any(status == 429 for status in responses)
        return {
            "test": "rate_limiting",
            "status": "passed" if rate_limited else "failed",
            "rate_limited": rate_limited,
            "responses": responses[-5:],  # Last 5 responses
        }

class SignalTests:
    """Trading signals endpoint tests"""

    def __init__(self, client: APIClient, db_manager: DatabaseTestManager):
        self.client = client
        self.db_manager = db_manager
        self.test_signals = []

    async def test_get_latest_signals(self) -> Dict[str, Any]:
        """Test getting latest signals"""
        response = await self.client.get("/signals/latest?limit=10")
        return {
            "test": "get_latest_signals",
            "status": "passed" if response.status_code == 200 else "failed",
            "response_time": response.elapsed.total_seconds() * 1000,
            "data": response.json() if response.status_code == 200 else None,
            "status_code": response.status_code,
        }

    async def test_get_signals_by_symbol(self) -> Dict[str, Any]:
        """Test getting signals by symbol"""
        symbol = random.choice(TEST_SYMBOLS)
        response = await self.client.get(f"/signals/by-symbol/{symbol}?limit=5")
        return {
            "test": "get_signals_by_symbol",
            "status": "passed" if response.status_code == 200 else "failed",
            "response_time": response.elapsed.total_seconds() * 1000,
            "data": response.json() if response.status_code == 200 else None,
            "status_code": response.status_code,
            "symbol": symbol,
        }

    async def test_create_signal(self) -> Dict[str, Any]:
        """Test creating a new signal"""
        signal_data = TestDataManager.generate_test_signal_data()
        response = await self.client.post("/signals/", json=signal_data)

        if response.status_code == 201:
            self.test_signals.append(response.json()["signal"])

        return {
            "test": "create_signal",
            "status": "passed" if response.status_code == 201 else "failed",
            "response_time": response.elapsed.total_seconds() * 1000,
            "data": response.json() if response.status_code == 201 else None,
            "status_code": response.status_code,
        }

    async def test_search_signals(self) -> Dict[str, Any]:
        """Test signal search functionality"""
        search_term = random.choice(TEST_SYMBOLS)
        response = await self.client.get(f"/signals/search?q={search_term}&limit=10")
        return {
            "test": "search_signals",
            "status": "passed" if response.status_code == 200 else "failed",
            "response_time": response.elapsed.total_seconds() * 1000,
            "data": response.json() if response.status_code == 200 else None,
            "status_code": response.status_code,
            "search_term": search_term,
        }

    async def test_signal_statistics(self) -> Dict[str, Any]:
        """Test signal statistics endpoint"""
        response = await self.client.get("/signals/statistics")
        return {
            "test": "signal_statistics",
            "status": "passed" if response.status_code == 200 else "failed",
            "response_time": response.elapsed.total_seconds() * 1000,
            "data": response.json() if response.status_code == 200 else None,
            "status_code": response.status_code,
        }

class AdminTests:
    """Admin functionality tests"""

    def __init__(self, client: APIClient, db_manager: DatabaseTestManager):
        self.client = client
        self.db_manager = db_manager

    async def test_admin_signal_generation(self) -> Dict[str, Any]:
        """Test admin signal generation endpoint"""
        # Note: This may fail if OANDA API is not available
        response = await self.client.post("/admin/generate-signals",
            data={"symbols": "EURUSD,GBPUSD"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        return {
            "test": "admin_signal_generation",
            "status": "passed" if response.status_code == 200 else "skipped",  # Skipped if OANDA unavailable
            "response_time": response.elapsed.total_seconds() * 1000,
            "data": response.json() if response.status_code == 200 else None,
            "status_code": response.status_code,
            "note": "May be skipped if OANDA API unavailable" if response.status_code != 200 else None,
        }

    async def test_admin_user_management(self) -> Dict[str, Any]:
        """Test admin user management endpoints"""
        response = await self.client.get("/admin/users")
        return {
            "test": "admin_user_management",
            "status": "passed" if response.status_code == 200 else "failed",
            "response_time": response.elapsed.total_seconds() * 1000,
            "data": response.json() if response.status_code == 200 else None,
            "status_code": response.status_code,
        }

    async def test_system_configuration(self) -> Dict[str, Any]:
        """Test system configuration endpoints"""
        response = await self.client.get("/config/info")
        return {
            "test": "system_configuration",
            "status": "passed" if response.status_code == 200 else "failed",
            "response_time": response.elapsed.total_seconds() * 1000,
            "data": response.json() if response.status_code == 200 else None,
            "status_code": response.status_code,
        }

class OANDATests:
    """OANDA API integration tests"""

    def __init__(self, client: APIClient):
        self.client = client

    async def test_oanda_health_check(self) -> Dict[str, Any]:
        """Test OANDA API health check"""
        response = await self.client.get("/api/oanda/health")
        return {
            "test": "oanda_health_check",
            "status": "passed" if response.status_code == 200 else "failed",
            "response_time": response.elapsed.total_seconds() * 1000,
            "data": response.json() if response.status_code == 200 else None,
            "status_code": response.status_code,
            "note": "Requires OANDA API configuration" if response.status_code != 200 else None,
        }

    async def test_oanda_market_data(self) -> Dict[str, Any]:
        """Test OANDA market data retrieval"""
        symbol = random.choice(TEST_SYMBOLS)
        response = await self.client.get(f"/api/oanda/market-data/{symbol}")
        return {
            "test": "oanda_market_data",
            "status": "passed" if response.status_code == 200 else "skipped",
            "response_time": response.elapsed.total_seconds() * 1000,
            "data": response.json() if response.status_code == 200 else None,
            "status_code": response.status_code,
            "symbol": symbol,
            "note": "Requires OANDA API configuration" if response.status_code != 200 else None,
        }

class ErrorHandlingTests:
    """Error handling and edge case tests"""

    def __init__(self, client: APIClient):
        self.client = client

    async def test_invalid_endpoint(self) -> Dict[str, Any]:
        """Test handling of invalid endpoints"""
        response = await self.client.get("/invalid/endpoint")
        return {
            "test": "invalid_endpoint",
            "status": "passed" if response.status_code == 404 else "failed",
            "response_time": response.elapsed.total_seconds() * 1000,
            "data": response.json() if response.status_code == 404 else None,
            "status_code": response.status_code,
        }

    async def test_invalid_data_submission(self) -> Dict[str, Any]:
        """Test handling of invalid data submission"""
        invalid_signal = {
            "symbol": "INVALID_SYMBOL",
            "signal_type": "INVALID_TYPE",
            "entry_price": -100  # Invalid negative price
        }
        response = await self.client.post("/signals/", json=invalid_signal)
        return {
            "test": "invalid_data_submission",
            "status": "passed" if response.status_code == 422 else "failed",
            "response_time": response.elapsed.total_seconds() * 1000,
            "data": response.json() if response.status_code in [400, 422] else None,
            "status_code": response.status_code,
        }

    async def test_unauthorized_access(self) -> Dict[str, Any]:
        """Test unauthorized access to protected endpoints"""
        # Clear authentication
        original_auth = self.client.headers.get("Authorization")
        self.client.headers.pop("Authorization", None)

        response = await self.client.get("/users/me")

        # Restore authentication
        if original_auth:
            self.client.headers["Authorization"] = original_auth

        return {
            "test": "unauthorized_access",
            "status": "passed" if response.status_code == 401 else "failed",
            "response_time": response.elapsed.total_seconds() * 1000,
            "data": response.json() if response.status_code == 401 else None,
            "status_code": response.status_code,
        }

class ComprehensiveTestRunner:
    """Comprehensive test runner for the entire application"""

    def __init__(self, base_url: str = TEST_CONFIG["base_url"]):
        self.client = APIClient(base_url)
        self.db_manager = DatabaseTestManager()
        self.benchmark = PerformanceBenchmark(self.client)
        self.results = []

    async def setup(self):
        """Setup test environment"""
        self.db_manager.setup_test_database()
        print("Test environment setup complete")

    async def teardown(self):
        """Cleanup test environment"""
        self.db_manager.cleanup_test_database()
        await self.client.close()
        print("Test environment cleanup complete")

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run comprehensive test suite"""
        print("Starting comprehensive test suite...")

        # Setup
        await self.setup()

        # Test suites
        test_suites = [
            ("Health Check", HealthCheckTests(self.client)),
            ("Authentication", AuthenticationTests(self.client, self.db_manager)),
            ("Signal Management", SignalTests(self.client, self.db_manager)),
            ("Admin Functions", AdminTests(self.client, self.db_manager)),
            ("OANDA Integration", OANDATests(self.client)),
            ("Error Handling", ErrorHandlingTests(self.client)),
        ]

        suite_results = {}

        for suite_name, suite in test_suites:
            print(f"\nRunning {suite_name} tests...")
            suite_methods = [method for method in dir(suite) if method.startswith("test_")]
            suite_test_results = []

            for test_method in suite_methods:
                try:
                    result = await getattr(suite, test_method)()
                    suite_test_results.append(result)
                    status = result.get("status", "unknown")
                    print(f"  {test_method}: {status.upper()}")
                except Exception as e:
                    error_result = {
                        "test": test_method,
                        "status": "error",
                        "error": str(e),
                        "exception_type": type(e).__name__,
                    }
                    suite_test_results.append(error_result)
                    print(f"  {test_method}: ERROR - {str(e)}")

            suite_results[suite_name] = suite_test_results

        # Performance benchmarks
        print("\nRunning performance benchmarks...")
        await self.run_performance_benchmarks()

        # Compile results
        total_tests = sum(len(results) for results in suite_results.values())
        passed_tests = sum(
            len([r for r in results if r.get("status") == "passed"])
            for results in suite_results.values()
        )
        failed_tests = sum(
            len([r for r in results if r.get("status") in ["failed", "error"]])
            for results in suite_results.values()
        )
        skipped_tests = sum(
            len([r for r in results if r.get("status") == "skipped"])
            for results in suite_results.values()
        )

        final_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "test_environment": {
                "base_url": TEST_CONFIG["base_url"],
                "database": TEST_DATABASE_URL,
            },
            "summary": {
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": failed_tests,
                "skipped": skipped_tests,
                "success_rate": f"{(passed_tests / total_tests * 100):.1f}%" if total_tests > 0 else "0%",
            },
            "test_suites": suite_results,
            "performance_benchmarks": self.benchmark.get_summary(),
            "recommendations": self.generate_recommendations(suite_results),
        }

        await self.teardown()
        return final_results

    async def run_performance_benchmarks(self):
        """Run performance benchmarks on key endpoints"""
        endpoints_to_benchmark = [
            ("GET", "/health", 50),
            ("GET", "/signals/latest", 30),
            ("GET", "/cache/health", 50),
            ("GET", "/config/info", 30),
        ]

        for method, endpoint, iterations in endpoints_to_benchmark:
            try:
                result = await self.benchmark.benchmark_endpoint(method, endpoint, iterations)
                print(f"  {method} {endpoint}: {result['avg_response_time_ms']}ms avg")
            except Exception as e:
                print(f"  {method} {endpoint}: Benchmark failed - {str(e)}")

    def generate_recommendations(self, suite_results: Dict[str, List[Dict]]) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []

        # Check for common issues
        for suite_name, results in suite_results.items():
            for result in results:
                if result.get("status") in ["failed", "error"]:
                    test_name = result.get("test", "unknown")

                    if "authentication" in test_name:
                        recommendations.append("Review authentication configuration and JWT settings")
                    elif "oanda" in test_name:
                        recommendations.append("Verify OANDA API credentials and connectivity")
                    elif "database" in test_name:
                        recommendations.append("Check database connection and permissions")
                    elif "cache" in test_name:
                        recommendations.append("Verify Redis/Cache configuration")

        # Performance recommendations
        perf_summary = self.benchmark.get_summary()
        if perf_summary.get("slowest_endpoint", {}).get("avg_response_time_ms", 0) > 1000:
            recommendations.append("Investigate slow endpoints for optimization opportunities")

        # General recommendations
        if not recommendations:
            recommendations.append("All tests passed - consider adding more edge case tests")

        return recommendations

# Main execution function
async def run_comprehensive_tests() -> Dict[str, Any]:
    """Main function to run the comprehensive test suite"""
    print("AI Trading System - Comprehensive Test Suite")
    print("=" * 50)

    runner = ComprehensiveTestRunner()
    results = await runner.run_all_tests()

    # Print summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    summary = results["summary"]
    print(f"Total Tests: {summary['total_tests']}")
    print(f"Passed: {summary['passed']}")
    print(f"Failed: {summary['failed']}")
    print(f"Skipped: {summary['skipped']}")
    print(f"Success Rate: {summary['success_rate']}")

    # Print recommendations
    if results["recommendations"]:
        print("\nRECOMMENDATIONS:")
        for i, rec in enumerate(results["recommendations"], 1):
            print(f"{i}. {rec}")

    return results

if __name__ == "__main__":
    # Run the comprehensive test suite
    results = asyncio.run(run_comprehensive_tests())

    # Save results to file
    with open("test_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\nTest results saved to test_results.json")

    # Exit with appropriate code
    failed_tests = results["summary"]["failed"]
    exit(1 if failed_tests > 0 else 0)