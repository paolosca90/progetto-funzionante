"""
Integration test configuration and shared fixtures for FastAPI frontend application.
Provides comprehensive testing setup for API endpoints, database operations, and external services.
"""

import os
import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Generator, Dict, Any, Optional, List
from datetime import datetime, timedelta
import tempfile
import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import httpx
from fastapi.testclient import TestClient

# Import application modules
from models import Base, User, Signal, SignalStatusEnum, SignalTypeEnum, OANDAConnection, Subscription
from schemas import UserCreate, SignalCreate, Token, SignalFilter
from app.services.signal_service import SignalService
from app.services.user_service import UserService
from app.services.auth_service import AuthService
from app.services.cache_service import CacheService
from app.services.oanda_service import OANDAService
from app.repositories.signal_repository import SignalRepository
from app.repositories.user_repository import UserRepository
from app.dependencies.database import get_db
from main import app
from app.core.config import settings

# Test configuration
TEST_DATABASE_URL = "sqlite:///:memory:"
TEST_REDIS_URL = "redis://localhost:6379/1"

# Integration test specific settings
os.environ.update({
    "DATABASE_URL": TEST_DATABASE_URL,
    "REDIS_URL": TEST_REDIS_URL,
    "JWT_SECRET_KEY": "test-integration-secret-key",
    "EMAIL_HOST": "smtp.test.com",
    "EMAIL_USER": "test@test.com",
    "EMAIL_PASSWORD": "testpassword",
    "OANDA_API_KEY": "test-oanda-api-key",
    "OANDA_ACCOUNT_ID": "test-account-id",
    "OANDA_ENVIRONMENT": "demo",
    "GEMINI_API_KEY": "test-gemini-api-key",
    "TESTING": "true",
    "SKIP_CACHE_SETUP": "true"  # Skip cache setup for tests
})


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_db_engine():
    """Create test database engine for the entire test session."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    yield engine

    # Cleanup
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def test_session_factory(test_db_engine):
    """Create test session factory."""
    return sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)


@pytest.fixture
def db_session(test_session_factory) -> Generator[Session, None, None]:
    """Create a database session for each test function with transaction rollback."""
    session = test_session_factory()

    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def test_app(db_session):
    """Create FastAPI test application with test database."""
    # Override the database dependency
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    yield app

    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def client(test_app) -> TestClient:
    """Create FastAPI test client."""
    return TestClient(test_app)


@pytest.fixture
async def async_client(test_app) -> AsyncMock:
    """Create async HTTP client for testing."""
    async with httpx.AsyncClient(app=test_app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_cache_service() -> AsyncMock:
    """Mock cache service for integration tests."""
    mock = AsyncMock()
    mock.get_cached_signals = AsyncMock(return_value=None)
    mock.cache_signals = AsyncMock(return_value=True)
    mock.invalidate_signals_cache = AsyncMock(return_value=True)
    mock.get_cached_signal_statistics = AsyncMock(return_value=None)
    mock.cache_signal_statistics = AsyncMock(return_value=True)
    mock.health_check = AsyncMock(return_value={"status": "healthy", "redis_connected": True})
    mock.get_cache_info = AsyncMock(return_value={"hit_rate": 0.85, "total_keys": 100})
    return mock


@pytest.fixture
def mock_oanda_service() -> MagicMock:
    """Mock OANDA service for integration tests."""
    mock = MagicMock()

    # Mock market data responses
    mock.get_market_data = MagicMock(return_value={
        "price": 1.1234,
        "timestamp": datetime.utcnow().isoformat(),
        "spread": 0.0001,
        "bid": 1.1233,
        "ask": 1.1235,
        "volume": 1000
    })

    # Mock signal generation
    mock.generate_signal = MagicMock(return_value={
        "signal_type": "BUY",
        "entry_price": 1.1234,
        "confidence": 0.85,
        "analysis": "Technical analysis indicates buying opportunity",
        "stop_loss": 1.1200,
        "take_profit": 1.1300,
        "reliability": 85.5
    })

    # Mock account data
    mock.get_account_data = MagicMock(return_value={
        "account_id": "test-account-id",
        "balance": 10000.0,
        "equity": 10500.0,
        "margin_used": 1000.0,
        "margin_available": 9000.0,
        "unrealized_pl": 500.0
    })

    return mock


@pytest.fixture
def test_user_data() -> Dict[str, Any]:
    """Test user data for integration tests."""
    return {
        "username": "integration_test_user",
        "email": "integration@test.com",
        "full_name": "Integration Test User",
        "password": "IntegrationTest123!",
        "is_active": True,
        "is_admin": False,
        "subscription_active": True,
        "trial_end": datetime.utcnow() + timedelta(days=30)
    }


@pytest.fixture
def test_admin_data() -> Dict[str, Any]:
    """Test admin user data for integration tests."""
    return {
        "username": "integration_admin",
        "email": "admin@test.com",
        "full_name": "Integration Admin User",
        "password": "AdminTest123!",
        "is_active": True,
        "is_admin": True,
        "subscription_active": True
    }


@pytest.fixture
def test_signal_data() -> Dict[str, Any]:
    """Test signal data for integration tests."""
    return {
        "symbol": "EUR_USD",
        "signal_type": SignalTypeEnum.BUY,
        "entry_price": 1.1234,
        "stop_loss": 1.1200,
        "take_profit": 1.1300,
        "reliability": 85.5,
        "confidence_score": 0.85,
        "risk_level": "MEDIUM",
        "is_public": True,
        "is_active": True,
        "source": "OANDA_AI",
        "timeframe": "H1",
        "ai_analysis": "Technical analysis indicates buying opportunity",
        "risk_reward_ratio": 2.5,
        "position_size_suggestion": 0.1,
        "spread": 0.0001,
        "volatility": 0.15,
        "technical_score": 75.0,
        "rsi": 45.2,
        "macd_signal": 0.0023,
        "market_session": "London",
        "expires_at": datetime.utcnow() + timedelta(hours=24)
    }


@pytest.fixture
def user_fixture(db_session: Session, test_user_data: Dict[str, Any]) -> User:
    """Create a test user in the database for integration tests."""
    user = User(**test_user_data)
    # Hash password using auth service
    auth_service = AuthService(db_session)
    user.hashed_password = auth_service.get_password_hash(test_user_data["password"])

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_fixture(db_session: Session, test_admin_data: Dict[str, Any]) -> User:
    """Create a test admin user in the database."""
    admin = User(**test_admin_data)
    auth_service = AuthService(db_session)
    admin.hashed_password = auth_service.get_password_hash(test_admin_data["password"])

    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture
def signal_fixture(db_session: Session, test_signal_data: Dict[str, Any], user_fixture: User) -> Signal:
    """Create a test signal in the database."""
    signal_data = test_signal_data.copy()
    signal_data["creator_id"] = user_fixture.id

    signal = Signal(**signal_data)
    db_session.add(signal)
    db_session.commit()
    db_session.refresh(signal)
    return signal


@pytest.fixture
def multiple_signals_fixture(db_session: Session, user_fixture: User) -> List[Signal]:
    """Create multiple test signals for bulk testing."""
    signals_data = [
        {
            "symbol": "EUR_USD",
            "signal_type": SignalTypeEnum.BUY,
            "entry_price": 1.1234,
            "stop_loss": 1.1200,
            "take_profit": 1.1300,
            "reliability": 85.5,
            "confidence_score": 0.85,
            "risk_level": "MEDIUM",
            "creator_id": user_fixture.id,
            "expires_at": datetime.utcnow() + timedelta(hours=24)
        },
        {
            "symbol": "GBP_USD",
            "signal_type": SignalTypeEnum.SELL,
            "entry_price": 1.3456,
            "stop_loss": 1.3500,
            "take_profit": 1.3400,
            "reliability": 78.2,
            "confidence_score": 0.78,
            "risk_level": "HIGH",
            "creator_id": user_fixture.id,
            "expires_at": datetime.utcnow() + timedelta(hours=12)
        },
        {
            "symbol": "USD_JPY",
            "signal_type": SignalTypeEnum.HOLD,
            "entry_price": 110.45,
            "stop_loss": 109.50,
            "take_profit": 111.50,
            "reliability": 65.0,
            "confidence_score": 0.65,
            "risk_level": "LOW",
            "creator_id": user_fixture.id,
            "expires_at": datetime.utcnow() + timedelta(hours=48)
        }
    ]

    signals = [Signal(**data) for data in signals_data]
    db_session.add_all(signals)
    db_session.commit()

    for signal in signals:
        db_session.refresh(signal)

    return signals


@pytest.fixture
def oanda_connection_fixture(db_session: Session, user_fixture: User) -> OANDAConnection:
    """Create a test OANDA connection."""
    connection = OANDAConnection(
        user_id=user_fixture.id,
        account_id="test-oanda-account",
        environment="demo",
        account_currency="USD",
        is_active=True,
        connection_status="CONNECTED",
        auto_trading_enabled=False,
        risk_tolerance="MEDIUM",
        max_position_size=1.0,
        daily_loss_limit=1000.0
    )

    db_session.add(connection)
    db_session.commit()
    db_session.refresh(connection)
    return connection


@pytest.fixture
def subscription_fixture(db_session: Session, user_fixture: User) -> Subscription:
    """Create a test subscription."""
    subscription = Subscription(
        user_id=user_fixture.id,
        plan_name="PREMIUM",
        status="ACTIVE",
        is_active=True,
        start_date=datetime.utcnow(),
        end_date=datetime.utcnow() + timedelta(days=30),
        payment_status="COMPLETED"
    )

    db_session.add(subscription)
    db_session.commit()
    db_session.refresh(subscription)
    return subscription


@pytest.fixture
def auth_headers(client: TestClient, user_fixture: User) -> Dict[str, str]:
    """Create authentication headers for testing protected endpoints."""
    # Login to get token
    login_data = {
        "username": user_fixture.username,
        "password": "IntegrationTest123!"
    }

    response = client.post("/auth/token", data=login_data)
    assert response.status_code == 200

    token_data = response.json()
    return {"Authorization": f"Bearer {token_data['access_token']}"}


@pytest.fixture
def admin_auth_headers(client: TestClient, admin_fixture: User) -> Dict[str, str]:
    """Create admin authentication headers for testing admin endpoints."""
    login_data = {
        "username": admin_fixture.username,
        "password": "AdminTest123!"
    }

    response = client.post("/auth/token", data=login_data)
    assert response.status_code == 200

    token_data = response.json()
    return {"Authorization": f"Bearer {token_data['access_token']}"}


@pytest.fixture
def signal_service_fixture(db_session: Session, mock_cache_service: AsyncMock) -> SignalService:
    """Create SignalService instance with mocked cache."""
    with patch('app.services.signal_service.cache_service', mock_cache_service):
        service = SignalService(db_session)
        yield service


@pytest.fixture
def user_service_fixture(db_session: Session) -> UserService:
    """Create UserService instance."""
    return UserService(db_session)


@pytest.fixture
def auth_service_fixture(db_session: Session) -> AuthService:
    """Create AuthService instance."""
    return AuthService(db_session)


@pytest.fixture
def signal_repository_fixture(db_session: Session) -> SignalRepository:
    """Create SignalRepository instance."""
    return SignalRepository(db_session)


@pytest.fixture
def user_repository_fixture(db_session: Session) -> UserRepository:
    """Create UserRepository instance."""
    return UserRepository(db_session)


@pytest.fixture
def sample_market_data() -> Dict[str, Any]:
    """Sample market data for testing."""
    return {
        "EUR_USD": {
            "price": 1.1234,
            "timestamp": datetime.utcnow().isoformat(),
            "spread": 0.0001,
            "bid": 1.1233,
            "ask": 1.1235,
            "volume": 1000
        },
        "GBP_USD": {
            "price": 1.3456,
            "timestamp": datetime.utcnow().isoformat(),
            "spread": 0.0002,
            "bid": 1.3454,
            "ask": 1.3458,
            "volume": 800
        }
    }


@pytest.fixture
def sample_api_responses() -> Dict[str, Any]:
    """Sample API responses for testing."""
    return {
        "health_check": {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "2.0.0",
            "database": "connected"
        },
        "user_profile": {
            "id": 1,
            "username": "testuser",
            "email": "test@example.com",
            "is_active": True,
            "subscription_active": True
        },
        "signal_list": {
            "signals": [],
            "total_count": 0,
            "average_reliability": 0.0
        }
    }


@pytest.fixture
def performance_test_data() -> Dict[str, Any]:
    """Performance test data."""
    return {
        "concurrent_users": 100,
        "requests_per_second": 50,
        "duration_seconds": 30,
        "endpoints": [
            "/health",
            "/signals/latest",
            "/auth/me"
        ]
    }


@pytest.fixture
def error_test_cases() -> List[Dict[str, Any]]:
    """Error test cases for integration tests."""
    return [
        {
            "name": "invalid_credentials",
            "endpoint": "/auth/token",
            "method": "POST",
            "data": {"username": "invalid", "password": "invalid"},
            "expected_status": 401
        },
        {
            "name": "missing_auth_header",
            "endpoint": "/users/me",
            "method": "GET",
            "expected_status": 401
        },
        {
            "name": "invalid_signal_data",
            "endpoint": "/signals",
            "method": "POST",
            "data": {"invalid": "data"},
            "expected_status": 422
        },
        {
            "name": "nonexistent_signal",
            "endpoint": "/signals/99999",
            "method": "GET",
            "expected_status": 404
        }
    ]


@pytest.fixture
def rate_limit_test_data() -> Dict[str, Any]:
    """Rate limit test data."""
    return {
        "max_attempts": 5,
        "window_minutes": 15,
        "endpoints": ["/auth/token", "/auth/register"]
    }