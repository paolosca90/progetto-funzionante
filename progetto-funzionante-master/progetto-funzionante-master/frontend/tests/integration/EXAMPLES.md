# Integration Test Examples

This file provides practical examples of how to use the integration test framework and fixtures effectively.

## Basic Usage Examples

### 1. Simple API Testing

```python
import pytest
from fastapi.testclient import TestClient

def test_health_check(client: TestClient):
    """Test basic health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_unauthorized_access(client: TestClient):
    """Test that protected endpoints require authentication."""
    response = client.get("/signals")
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]
```

### 2. Authentication Testing

```python
def test_user_registration_and_login(client: TestClient, db_session):
    """Test complete user registration and login flow."""
    # Register new user
    registration_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "SecurePassword123!"
    }

    response = client.post("/auth/register", json=registration_data)
    assert response.status_code == 201

    # Login with created user
    login_data = {
        "username": "testuser",
        "password": "SecurePassword123!"
    }

    response = client.post("/auth/login", json=login_data)
    assert response.status_code == 200

    token_data = response.json()
    assert "access_token" in token_data
    assert "token_type" in token_data

    return token_data["access_token"]
```

### 3. Using Authentication Headers

```python
def test_protected_endpoint_with_auth(client: TestClient, auth_headers):
    """Test accessing protected endpoint with valid authentication."""
    response = client.get("/users/me", headers=auth_headers)
    assert response.status_code == 200

    user_data = response.json()
    assert "id" in user_data
    assert "username" in user_data
    assert "email" in user_data
```

## Database Testing Examples

### 4. Database Operations

```python
def test_create_and_retrieve_signal(client: TestClient, auth_headers, db_session):
    """Test creating a signal and retrieving it from database."""
    # Create signal
    signal_data = {
        "instrument": "EUR_USD",
        "action": "BUY",
        "entry_price": 1.1234,
        "stop_loss": 1.1200,
        "take_profit": 1.1300,
        "confidence": 0.85
    }

    response = client.post("/signals", json=signal_data, headers=auth_headers)
    assert response.status_code == 201

    created_signal = response.json()
    assert created_signal["instrument"] == "EUR_USD"

    # Verify signal exists in database
    from models import Signal
    db_signal = db_session.query(Signal).filter(Signal.id == created_signal["id"]).first()
    assert db_signal is not None
    assert db_signal.instrument == "EUR_USD"
```

### 5. Testing with Multiple Test Users

```python
def test_multiple_users_signals(client: TestClient, multiple_users_fixture, db_session):
    """Test signals from multiple users."""
    signals_data = []

    for i, user in enumerate(multiple_users_fixture):
        # Create auth headers for each user
        login_data = {"username": user.username, "password": "password123"}
        response = client.post("/auth/login", json=login_data)
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create signal for each user
        signal_data = {
            "instrument": f"EUR_USD_{i}",
            "action": "BUY" if i % 2 == 0 else "SELL",
            "entry_price": 1.1234 + (i * 0.001),
            "stop_loss": 1.1200,
            "take_profit": 1.1300,
            "confidence": 0.8 + (i * 0.02)
        }

        response = client.post("/signals", json=signal_data, headers=headers)
        assert response.status_code == 201
        signals_data.append(response.json())

    # Verify all signals were created
    from models import Signal
    all_signals = db_session.query(Signal).all()
    assert len(all_signals) == len(multiple_users_fixture)
```

## Mock Service Testing Examples

### 6. Testing with Mock External Services

```python
def test_oanda_service_with_mock(client: TestClient, mock_oanda_service, auth_headers):
    """Test OANDA service integration with mocked responses."""
    # Configure mock response
    mock_oanda_service.get_instrument_candles.return_value = {
        "instrument": "EUR_USD",
        "granularity": "H1",
        "candles": [
            {
                "time": "2023-01-01T00:00:00Z",
                "open": 1.1234,
                "high": 1.1256,
                "low": 1.1221,
                "close": 1.1245,
                "volume": 1000
            }
        ]
    }

    # Test endpoint that uses OANDA service
    response = client.get("/market-data/EUR_USD/H1", headers=auth_headers)
    assert response.status_code == 200

    market_data = response.json()
    assert market_data["instrument"] == "EUR_USD"
    assert len(market_data["candles"]) == 1

    # Verify mock was called
    mock_oanda_service.get_instrument_candles.assert_called_once_with("EUR_USD", "H1")
```

### 7. Testing Email Service Integration

```python
def test_email_notification_on_registration(client: TestClient, mock_email_service):
    """Test that email notifications are sent on user registration."""
    user_data = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "SecurePassword123!"
    }

    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 201

    # Verify email service was called
    mock_email_service.send_welcome_email.assert_called_once()
    call_args = mock_email_service.send_welcome_email.call_args
    assert call_args[0][0] == "newuser@example.com"  # email address
    assert "Welcome" in call_args[0][1]  # subject
```

## Performance Testing Examples

### 8. Concurrent Request Testing

```python
import threading
import time

def test_concurrent_login_requests(client: TestClient, test_user_data):
    """Test handling of concurrent login requests."""
    results = []
    errors = []

    def make_login_request():
        try:
            response = client.post("/auth/login", json=test_user_data)
            results.append(response.status_code)
        except Exception as e:
            errors.append(str(e))

    # Create multiple threads for concurrent requests
    threads = []
    for _ in range(10):
        thread = threading.Thread(target=make_login_request)
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # Verify all requests succeeded
    assert len(errors) == 0, f"Errors occurred: {errors}"
    assert all(status == 200 for status in results)
    assert len(results) == 10
```

### 9. Performance Benchmarking

```python
def test_api_response_time_benchmark(client: TestClient, auth_headers):
    """Test API response time against performance benchmarks."""
    import time

    endpoints = [
        ("GET", "/health"),
        ("GET", "/users/me"),
        ("GET", "/signals"),
        ("GET", "/signals/latest")
    ]

    results = {}

    for method, endpoint in endpoints:
        start_time = time.time()

        if method == "GET":
            response = client.get(endpoint, headers=auth_headers)
        elif method == "POST":
            response = client.post(endpoint, headers=auth_headers)

        end_time = time.time()
        response_time = end_time - start_time

        results[endpoint] = {
            "status_code": response.status_code,
            "response_time": response_time
        }

        # Assert performance benchmarks
        assert response.status_code == 200
        assert response_time < 1.0, f"{endpoint} took {response_time:.3f}s, expected < 1.0s"

    # Print performance results
    for endpoint, metrics in results.items():
        print(f"{endpoint}: {metrics['response_time']:.3f}s")
```

## Error Handling Testing Examples

### 10. Testing Error Scenarios

```python
def test_invalid_signal_creation(client: TestClient, auth_headers):
    """Test error handling for invalid signal creation."""
    # Test with invalid data
    invalid_signal_data = {
        "instrument": "INVALID_PAIR",  # Invalid forex pair
        "action": "INVALID_ACTION",   # Invalid action
        "entry_price": -1.0,          # Negative price
        "stop_loss": "invalid",       # Invalid type
        "take_profit": 1.1300,
        "confidence": 1.5             # Confidence > 1.0
    }

    response = client.post("/signals", json=invalid_signal_data, headers=auth_headers)
    assert response.status_code == 422  # Validation error

    error_detail = response.json()["detail"]
    assert len(error_detail) > 0  # Should have validation errors

def test_database_constraint_violation(client: TestClient, auth_headers, db_session):
    """Test database constraint violation handling."""
    # Create a signal
    signal_data = {
        "instrument": "EUR_USD",
        "action": "BUY",
        "entry_price": 1.1234,
        "stop_loss": 1.1200,
        "take_profit": 1.1300,
        "confidence": 0.85
    }

    # Create first signal (should succeed)
    response1 = client.post("/signals", json=signal_data, headers=auth_headers)
    assert response1.status_code == 201

    # Try to create duplicate signal (should fail if constraints exist)
    response2 = client.post("/signals", json=signal_data, headers=auth_headers)
    # Either 400 (business logic) or 500 (database constraint) is acceptable
    assert response2.status_code in [400, 500]
```

## Custom Fixture Examples

### 11. Creating Custom Fixtures

```python
@pytest.fixture
def custom_signal_data():
    """Custom fixture for signal test data."""
    return {
        "instrument": "GBP_USD",
        "action": "SELL",
        "entry_price": 1.2567,
        "stop_loss": 1.2600,
        "take_profit": 1.2500,
        "confidence": 0.92
    }

@pytest.fixture
def custom_test_user(db_session):
    """Create a custom test user."""
    from models import User
    user = User(
        username="custom_user",
        email="custom@example.com",
        hashed_password="hashed_password",
        is_active=True,
        is_admin=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

def test_custom_fixtures_usage(client: TestClient, custom_signal_data, custom_test_user):
    """Test using custom fixtures."""
    # Login with custom user
    login_data = {"username": custom_test_user.username, "password": "password123"}
    response = client.post("/auth/login", json=login_data)
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create signal with custom data
    response = client.post("/signals", json=custom_signal_data, headers=headers)
    assert response.status_code == 201

    created_signal = response.json()
    assert created_signal["instrument"] == "GBP_USD"
```

## Test Data Seeding Examples

### 12. Using TestDataSeeder

```python
def test_data_seeding_usage(db_session):
    """Test using the TestDataSeeder for bulk data creation."""
    from test_data_seeding import TestDataSeeder

    seeder = TestDataSeeder(db_session)

    # Create realistic user dataset
    users = seeder.create_realistic_user_dataset(count=10)
    assert len(users) == 10

    # Create signal dataset
    signals = seeder.create_signal_dataset(count=50)
    assert len(signals) == 50

    # Create performance data
    seeder.create_performance_data(user_count=10, signal_count=20)

    # Verify data was created
    from models import User, Signal, UserPerformance
    assert db_session.query(User).count() >= 10
    assert db_session.query(Signal).count() >= 50
    assert db_session.query(UserPerformance).count() >= 10
```

## Async Testing Examples

### 13. Async Database Operations

```python
@pytest.mark.asyncio
async def test_async_database_operations(db_session):
    """Test async database operations."""
    import asyncio
    from models import User, Signal

    async def create_user_async(user_data):
        user = User(**user_data)
        db_session.add(user)
        await asyncio.sleep(0.1)  # Simulate async operation
        db_session.commit()
        return user

    # Create multiple users concurrently
    user_data_list = [
        {"username": f"async_user_{i}", "email": f"async{i}@example.com", "hashed_password": "hash"}
        for i in range(5)
    ]

    tasks = [create_user_async(data) for data in user_data_list]
    created_users = await asyncio.gather(*tasks)

    # Verify all users were created
    assert len(created_users) == 5
    assert db_session.query(User).count() >= 5
```

## Test Configuration Examples

### 14. Test Configuration Override

```python
@pytest.fixture
def custom_performance_config():
    """Override performance configuration for specific test."""
    return {
        "concurrent_users": 5,
        "duration": 10,
        "requests_per_second": 2,
        "max_response_time": 1.0
    }

def test_custom_performance_config(client: TestClient, custom_performance_config):
    """Test with custom performance configuration."""
    import time
    import threading

    start_time = time.time()
    end_time = start_time + custom_performance_config["duration"]

    def make_requests():
        while time.time() < end_time:
            response = client.get("/health")
            assert response.status_code == 200
            time.sleep(1.0 / custom_performance_config["requests_per_second"])

    # Start concurrent users
    threads = []
    for _ in range(custom_performance_config["concurrent_users"]):
        thread = threading.Thread(target=make_requests)
        threads.append(thread)
        thread.start()

    # Wait for completion
    for thread in threads:
        thread.join()

    print(f"Completed performance test with custom config: {custom_performance_config}")
```

## Running Tests with Different Configurations

### 15. Command Line Examples

```bash
# Run all integration tests with coverage
pytest tests/integration/ -v --cov=. --cov-report=html

# Run only authentication tests
pytest tests/integration/test_auth_integration.py -v

# Run tests with specific marker
pytest tests/integration/ -m "slow" -v

# Run tests with custom performance configuration
pytest tests/integration/test_performance_load_integration.py -v --performance-level=heavy

# Run tests with debug output
pytest tests/integration/ -v -s --tb=short

# Run tests and generate XML report
pytest tests/integration/ -v --junitxml=test-results.xml

# Run tests with specific Python path
PYTHONPATH=. pytest tests/integration/ -v
```

These examples provide a comprehensive guide for using the integration test framework effectively. Each example demonstrates specific patterns and best practices for testing different aspects of the FastAPI application.