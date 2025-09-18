"""
Pytest configuration and shared fixtures for the FastAPI frontend application.
"""

import os
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import Generator, Dict, Any, Optional
from datetime import datetime, timedelta
import tempfile
import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from models import Base, User, Signal, SignalStatusEnum, SignalTypeEnum, OANDAConnection
from schemas import UserCreate, SignalCreate, OANDAConnectionCreate
from app.services.signal_service import SignalService
from app.services.user_service import UserService
from app.services.auth_service import AuthService
from app.services.cache_service import CacheService
from app.repositories.signal_repository import SignalRepository
from app.repositories.user_repository import UserRepository
from app.dependencies.database import get_db
from main import app

# Test configuration
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="session")
def test_db():
    """
    Create a test database for the entire test session.
    Uses SQLite in-memory database for fast testing.
    """
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create session factory
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    yield TestingSessionLocal

    # Cleanup
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(test_db) -> Generator[Session, None, None]:
    """
    Create a database session for each test function.
    """
    db = test_db()

    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture
def mock_cache_service() -> AsyncMock:
    """
    Mock cache service for testing.
    """
    mock = AsyncMock()
    mock.get_cached_signals = AsyncMock(return_value=None)
    mock.cache_signals = AsyncMock()
    mock.invalidate_signals_cache = AsyncMock()
    mock.get_cached_signal_statistics = AsyncMock(return_value=None)
    mock.cache_signal_statistics = AsyncMock()
    return mock


@pytest.fixture
def mock_oanda_service() -> MagicMock:
    """
    Mock OANDA service for testing.
    """
    mock = MagicMock()
    mock.get_market_data = MagicMock(return_value={
        "price": 1.1234,
        "timestamp": datetime.utcnow().isoformat(),
        "spread": 0.0001
    })
    mock.generate_signal = MagicMock(return_value={
        "signal_type": "BUY",
        "entry_price": 1.1234,
        "confidence": 0.85,
        "analysis": "Technical analysis indicates buying opportunity"
    })
    return mock


@pytest.fixture
def mock_auth_service() -> MagicMock:
    """
    Mock authentication service for testing.
    """
    mock = MagicMock()
    mock.create_access_token = MagicMock(return_value="test_access_token")
    mock.verify_token = MagicMock(return_value={"sub": "1", "username": "testuser"})
    mock.get_current_user = MagicMock(return_value=None)
    return mock


@pytest.fixture
def test_user_data() -> Dict[str, Any]:
    """
    Test user data for creating users.
    """
    return {
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "testpassword123",
        "is_active": True,
        "is_admin": False,
        "subscription_active": True
    }


@pytest.fixture
def test_admin_data() -> Dict[str, Any]:
    """
    Test admin user data.
    """
    return {
        "username": "admin",
        "email": "admin@example.com",
        "full_name": "Admin User",
        "password": "adminpassword123",
        "is_active": True,
        "is_admin": True,
        "subscription_active": True
    }


@pytest.fixture
def test_signal_data() -> Dict[str, Any]:
    """
    Test signal data for creating signals.
    """
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
        "position_size_suggestion": "0.1 lots",
        "spread": 0.0001,
        "volatility": 0.15,
        "technical_score": 75,
        "rsi": 45.2,
        "macd_signal": 0.0023,
        "market_session": "London"
    }


@pytest.fixture
def user_fixture(db_session: Session, test_user_data: Dict[str, Any]) -> User:
    """
    Create a test user in the database.
    """
    user = User(**test_user_data)
    user.set_password(test_user_data["password"])
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_fixture(db_session: Session, test_admin_data: Dict[str, Any]) -> User:
    """
    Create a test admin user in the database.
    """
    admin = User(**test_admin_data)
    admin.set_password(test_admin_data["password"])
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture
def signal_fixture(db_session: Session, test_signal_data: Dict[str, Any], user_fixture: User) -> Signal:
    """
    Create a test signal in the database.
    """
    signal_data = test_signal_data.copy()
    signal_data["creator_id"] = user_fixture.id
    signal_data["expires_at"] = datetime.utcnow() + timedelta(hours=24)

    signal = Signal(**signal_data)
    db_session.add(signal)
    db_session.commit()
    db_session.refresh(signal)
    return signal


@pytest.fixture
def signal_service_fixture(db_session: Session, mock_cache_service: AsyncMock) -> SignalService:
    """
    Create SignalService instance with mocked cache.
    """
    # Replace the cache service in the module
    import app.services.signal_service
    original_cache = app.services.signal_service.cache_service
    app.services.signal_service.cache_service = mock_cache_service

    service = SignalService(db_session)

    yield service

    # Restore original cache service
    app.services.signal_service.cache_service = original_cache


@pytest.fixture
def user_service_fixture(db_session: Session) -> UserService:
    """
    Create UserService instance.
    """
    return UserService(db_session)


@pytest.fixture
def auth_service_fixture(db_session: Session) -> AuthService:
    """
    Create AuthService instance.
    """
    return AuthService(db_session)


@pytest.fixture
def signal_repository_fixture(db_session: Session) -> SignalRepository:
    """
    Create SignalRepository instance.
    """
    return SignalRepository(db_session)


@pytest.fixture
def user_repository_fixture(db_session: Session) -> UserRepository:
    """
    Create UserRepository instance.
    """
    return UserRepository(db_session)


@pytest.fixture
def client(db_session: Session):
    """
    Create FastAPI test client with test database.
    """
    # Override the database dependency
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    from fastapi.testclient import TestClient
    test_client = TestClient(app)

    yield test_client

    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client: TestClient, user_fixture: User):
    """
    Create authentication headers for testing protected endpoints.
    """
    from app.services.auth_service import AuthService

    # Create access token
    auth_service = AuthService(client.app.dependency_overrides.get(get_db, lambda: None)())
    access_token = auth_service.create_access_token(data={"sub": str(user_fixture.id)})

    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def admin_auth_headers(client: TestClient, admin_fixture: User):
    """
    Create admin authentication headers for testing admin endpoints.
    """
    from app.services.auth_service import AuthService

    # Create access token
    auth_service = AuthService(client.app.dependency_overrides.get(get_db, lambda: None)())
    access_token = auth_service.create_access_token(data={"sub": str(admin_fixture.id)})

    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def test_environment():
    """
    Set up test environment variables.
    """
    # Store original environment variables
    original_env = os.environ.copy()

    # Set test environment variables
    os.environ.update({
        "DATABASE_URL": TEST_DATABASE_URL,
        "JWT_SECRET_KEY": "test-secret-key-for-testing",
        "EMAIL_HOST": "smtp.test.com",
        "EMAIL_USER": "test@test.com",
        "EMAIL_PASSWORD": "testpassword",
        "OANDA_API_KEY": "test-oanda-api-key",
        "OANDA_ACCOUNT_ID": "test-account-id",
        "OANDA_ENVIRONMENT": "demo",
        "GEMINI_API_KEY": "test-gemini-api-key",
        "REDIS_URL": "redis://localhost:6379/0",
        "TESTING": "true"
    })

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def sample_signals_data() -> list:
    """
    Sample signals data for bulk testing.
    """
    return [
        {
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
            "ai_analysis": "Technical analysis indicates buying opportunity"
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
            "is_public": True,
            "is_active": True,
            "source": "MANUAL",
            "timeframe": "H4",
            "ai_analysis": "Market sentiment indicates selling pressure"
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
            "is_public": False,
            "is_active": True,
            "source": "API",
            "timeframe": "D1",
            "ai_analysis": "Market in consolidation phase"
        }
    ]