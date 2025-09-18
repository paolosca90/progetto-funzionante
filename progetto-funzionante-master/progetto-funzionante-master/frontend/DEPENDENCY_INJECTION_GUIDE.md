# FastAPI Dependency Injection System Guide

## Overview

This comprehensive dependency injection (DI) system provides a robust, production-ready framework for managing service dependencies in your FastAPI application. The system supports:

- **Service Lifetime Management**: Transient, scoped, and singleton services
- **Circular Dependency Detection**: Automatic detection and prevention of circular dependencies
- **Configuration Management**: Centralized configuration with environment-specific settings
- **Database Session Management**: Connection pooling and transaction management
- **External Service Integration**: OANDA, Redis, and other external services
- **Middleware Integration**: Request-scoped dependency management
- **Testing Support**: Comprehensive testing utilities and mock services
- **Performance Monitoring**: Built-in metrics and health monitoring

## Architecture

### Core Components

1. **Dependency Container** (`app/core/dependency_injection.py`)
   - Central service registry and resolver
   - Service lifetime management
   - Circular dependency detection
   - Performance monitoring

2. **Service Containers** (`app/containers/service_containers.py`)
   - Organized by service type (Core, Business, External, Infrastructure, Repository)
   - Automatic service registration
   - Dependency validation

3. **Service Implementations** (`app/services/`)
   - **Core Services**: Configuration, Logging, Database
   - **Business Services**: Auth, Users, Signals, Subscriptions
   - **External Services**: OANDA, Redis, Email, AI
   - **Infrastructure Services**: HTTP, File, Task Scheduling, Performance Monitoring

4. **Middleware** (`app/middleware/dependency_injection_middleware.py`)
   - Request-scoped dependency management
   - Automatic service lifecycle management
   - Performance tracking
   - Error handling

5. **Testing Support** (`app/testing/dependency_injection_testing.py`)
   - Test container configuration
   - Mock service creation
   - Integration test helpers
   - Performance testing utilities

## Service Lifetimes

### Transient
- **Description**: New instance created every time the service is requested
- **Use Case**: Lightweight, stateless services
- **Example**: HTTP clients, file handlers

### Scoped
- **Description**: One instance per HTTP request
- **Use Case**: Services that maintain request-specific state
- **Example**: Database sessions, user contexts, request logging

### Singleton
- **Description**: One instance for the entire application lifetime
- **Use Case**: Expensive-to-create services, shared state
- **Example**: Configuration, logging, connection pools

## Quick Start

### 1. Basic Service Registration

```python
from app.core.dependency_injection import registrar, ServiceLifetime

# Register a service
registrar().register_scoped(
    UserService,
    UserService,
    tags={"business", "users"}
)

# Register a singleton
registrar().register_singleton(
    ConfigService,
    ConfigService,
    tags={"core", "config"}
)
```

### 2. Service Resolution

```python
from app.core.dependency_injection import get_container

# Get service instance
container = get_container()
user_service = container.resolve(UserService)

# In FastAPI routes
from app.core.dependency_injection import resolve_service

@app.get("/users")
async def get_users(user_service: UserService = Depends(resolve_service(UserService))):
    return await user_service.get_all_users()
```

### 3. Service with Dependencies

```python
class UserService:
    def __init__(self, database_service: DatabaseService, logging_service: LoggingService):
        self.database_service = database_service
        self.logging_service = logging_service

    async def get_user(self, user_id: int) -> Optional[User]:
        with self.database_service.get_session_context() as session:
            return session.query(User).filter(User.id == user_id).first()

# The DI system automatically injects DatabaseService and LoggingService
```

## Configuration Management

### Environment-Specific Configuration

```python
from app.services.config_service import ConfigService

# Get configuration service
config_service = container.resolve(ConfigService)

# Access configuration
db_url = config_service.get('database_url')
jwt_secret = config_service.get('jwt_secret_key')

# Get grouped configuration
db_config = config_service.get_database_config()
redis_config = config_service.get_redis_config()
```

### Dynamic Configuration Updates

```python
# Watch for configuration changes
await config_service.watch_changes()

# Add change callback
def on_config_change(key: str, old_value: Any, new_value: Any):
    print(f"Config changed: {key} = {new_value}")

config_service.add_change_callback(on_config_change)
```

## Database Integration

### Database Service Usage

```python
from app.services.database_service import DatabaseService

# Get database service
db_service = container.resolve(DatabaseService)

# Basic operations
with db_service.get_session_context() as session:
    user = session.query(User).first()

# Transaction management
async with db_service.get_transaction() as session:
    user = User(name="John", email="john@example.com")
    session.add(user)
    # Auto-commits on success, rolls back on error

# Health monitoring
health_status = await db_service.check_health()
metrics = db_service.get_metrics()
```

### Repository Pattern

```python
from app.repositories.user_repository import UserRepository

class UserService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def get_user_by_email(self, email: str) -> Optional[User]:
        return await self.user_repository.find_by_email(email)
```

## External Service Integration

### OANDA Service

```python
from app.services.external.oanda_service import OandaService

# Get OANDA service
oanda_service = container.resolve(OandaService)

# Get account information
account_info = await oanda_service.get_account_info()

# Get market data
pricing = await oanda_service.get_pricing(['EUR_USD', 'GBP_USD'])
candles = await oanda_service.get_candles('EUR_USD', 'H1', count=100)

# Create order
order_data = {
    'order': {
        'instrument': 'EUR_USD',
        'units': 1000,
        'type': 'MARKET'
    }
}
result = await oanda_service.create_order(order_data)

# Start price streaming
await oanda_service.start_price_streaming(['EUR_USD'])
oanda_service.add_price_callback(lambda price: print(f"New price: {price.mid}"))
```

### Redis Service

```python
from app.services.external.redis_service import RedisService

# Get Redis service
redis_service = container.resolve(RedisService)

# Basic operations
await redis_service.set('user:123', {'name': 'John', 'email': 'john@example.com'})
user_data = await redis_service.get('user:123')

# Hash operations
await redis_service.hset('user:123:profile', 'name', 'John')
await redis_service.hset('user:123:profile', 'email', 'john@example.com')
profile = await redis_service.hgetall('user:123:profile')

# Pub/Sub
async def on_message(channel: str, message: Any):
    print(f"Received message on {channel}: {message}")

await redis_service.subscribe('trading_signals', on_message)
await redis_service.publish('trading_signals', {'signal': 'BUY', 'symbol': 'EUR_USD'})
```

## Middleware Integration

### Adding DI Middleware

```python
from app.middleware.dependency_injection_middleware import add_all_di_middleware

# Add all DI middleware to FastAPI app
add_all_di_middleware(app)

# Or add specific middleware
from fastapi import FastAPI
from app.middleware.dependency_injection_middleware import (
    DependencyInjectionMiddleware,
    DatabaseSessionMiddleware,
    PerformanceMonitoringMiddleware
)

app = FastAPI()
app.add_middleware(DependencyInjectionMiddleware)
app.add_middleware(DatabaseSessionMiddleware)
app.add_middleware(PerformanceMonitoringMiddleware)
```

### Accessing Request-Scope Services

```python
from fastapi import Request, Depends

@app.get("/dashboard")
async def get_dashboard(request: Request):
    # Get dependency injection scope
    scope = request.state.di_scope

    # Get database session
    db_session = request.state.db_session

    # Get correlation ID
    correlation_id = request.state.correlation_id

    return {
        "correlation_id": correlation_id,
        "user_data": "dashboard data"
    }
```

## Testing

### Setting Up Test Container

```python
import pytest
from app.testing.dependency_injection_testing import (
    TestContainerFactory, TestConfig, with_test_container
)

@pytest.fixture
async def test_container():
    test_config = TestConfig(
        use_in_memory_database=True,
        use_mock_external_services=True,
        use_test_logging=True
    )

    async with TestContainerFactory.create_async_test_container(test_config) as container:
        yield container

@pytest.mark.asyncio
async def test_user_service(test_container):
    user_service = test_container.resolve(UserService)
    users = await user_service.get_all_users()
    assert len(users) >= 0
```

### Using Mock Services

```python
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_with_mocks():
    test_config = TestConfig(use_mock_external_services=True)

    async with TestContainerFactory.create_async_test_container(test_config) as container:
        # Get mock service
        mock_oanda = container.service_registry.get_mock(type(mock_oanda))

        # Configure mock behavior
        mock_oanda.get_account_info.return_value = {
            'id': 'test-account',
            'balance': 10000.0
        }

        # Test with mock
        oanda_service = container.resolve(type(mock_oanda))
        account = await oanda_service.get_account_info()
        assert account['balance'] == 10000.0
```

### Performance Testing

```python
from app.testing.dependency_injection_testing import PerformanceTestHelpers

@pytest.mark.asyncio
async def test_performance(test_container):
    # Measure service performance
    metrics = await PerformanceTestHelpers.measure_service_performance(
        test_container,
        UserService,
        lambda service: service.get_all_users(),
        iterations=100
    )

    assert metrics['avg_time'] < 0.1  # Should be fast
    print(f"Average time: {metrics['avg_time']:.3f}s")
```

## Performance Monitoring

### Built-in Metrics

```python
# Get container metrics
container = get_container()
metrics = container.get_metrics()

# Service-specific metrics
db_service = container.resolve(DatabaseService)
db_metrics = db_service.get_metrics()

# Health monitoring
health = await db_service.health_check()
```

### Custom Metrics

```python
from app.services.logging_service import LoggingService

# Add performance monitoring
logging_service = container.resolve(LoggingService)

def performance_callback(operation: str, duration: float, metadata: Dict):
    logging_service.log_performance(operation, duration, **metadata)

logging_service.add_performance_callback(performance_callback)
```

## Best Practices

### 1. Service Design

```python
# ✅ Good: Clear dependencies and single responsibility
class UserService:
    def __init__(self, user_repository: UserRepository, logging_service: LoggingService):
        self.user_repository = user_repository
        self.logging_service = logging_service

# ❌ Avoid: Hidden dependencies and multiple responsibilities
class BadUserService:
    def __init__(self):
        self.db = SessionLocal()  # Hidden dependency
        self.cache = {}  # Mixed responsibilities
```

### 2. Lifetime Selection

```python
# ✅ Singleton: Configuration, logging, connection pools
registrar().register_singleton(ConfigService, ConfigService)

# ✅ Scoped: Database sessions, user contexts, request logging
registrar().register_scoped(UserService, UserService)

# ✅ Transient: HTTP clients, file handlers, validators
registrar().register_transient(HTTPClientService, HTTPClientService)
```

### 3. Error Handling

```python
# ✅ Good: Proper error handling with DI
class OrderService:
    def __init__(self, oanda_service: OandaService, logging_service: LoggingService):
        self.oanda_service = oanda_service
        self.logging_service = logging_service

    async def place_order(self, order_data: Dict) -> Optional[Dict]:
        try:
            return await self.oanda_service.create_order(order_data)
        except Exception as e:
            self.logging_service.log_error(f"Order placement failed: {e}", exception=e)
            raise

# ❌ Avoid: Silent failures and inadequate logging
class BadOrderService:
    async def place_order(self, order_data: Dict):
        # No error handling, no logging
        return await self.oanda_service.create_order(order_data)
```

### 4. Configuration Management

```python
# ✅ Good: Centralized configuration with validation
class AppConfig:
    def __init__(self, config_service: ConfigService):
        self.config_service = config_service
        self.db_url = config_service.get('database_url')
        self.jwt_secret = config_service.get('jwt_secret_key')

        # Validate configuration
        if not self.jwt_secret or len(self.jwt_secret) < 32:
            raise ValueError("JWT secret must be at least 32 characters")

# ❌ Avoid: Hardcoded configuration and no validation
class BadAppConfig:
    def __init__(self):
        self.db_url = "postgresql://localhost/mydb"  # Hardcoded
        self.jwt_secret = "secret"  # Too short, no validation
```

## Troubleshooting

### Common Issues

1. **Circular Dependencies**
   ```
   Error: Circular dependency detected: A -> B -> C -> A
   ```
   **Solution**: Refactor to remove circular dependency or use lazy loading

2. **Service Not Registered**
   ```
   Error: Service UserService is not registered
   ```
   **Solution**: Register the service before trying to resolve it

3. **Container Already Initialized**
   ```
   Error: Cannot register services after container is initialized
   ```
   **Solution**: Register all services before the first resolve call

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Get container diagnostics
container = get_container()
print(f"Registered services: {len(container._services)}")
print(f"Dependency graph: {container._dependency_graph}")
```

### Health Checks

```python
# System health check
async def system_health_check():
    container = get_container()

    # Check database
    db_service = container.resolve(DatabaseService)
    db_health = await db_service.health_check()

    # Check Redis
    redis_service = container.resolve(RedisService)
    redis_health = await redis_service.health_check()

    # Check OANDA
    oanda_service = container.resolve(OandaService)
    oanda_health = await oanda_service.health_check()

    return {
        'database': db_health,
        'redis': redis_health,
        'oanda': oanda_health,
        'overall': 'healthy' if all(
            h.get('status') == 'healthy'
            for h in [db_health, redis_health, oanda_health]
        ) else 'degraded'
    }
```

## Migration Guide

### From Manual Dependency Management

**Before:**
```python
class UserService:
    def __init__(self):
        self.db = SessionLocal()
        self.logger = logging.getLogger(__name__)

class UserController:
    def __init__(self):
        self.user_service = UserService()

@app.get("/users")
def get_users():
    controller = UserController()
    return controller.get_users()
```

**After:**
```python
class UserService:
    def __init__(self, database_service: DatabaseService, logging_service: LoggingService):
        self.database_service = database_service
        self.logging_service = logging_service

# Register services
registrar().register_scoped(UserService, UserService)

@app.get("/users")
async def get_users(user_service: UserService = Depends(resolve_service(UserService))):
    return await user_service.get_all_users()
```

### From Factory Pattern

**Before:**
```python
class ServiceFactory:
    @staticmethod
    def create_user_service():
        return UserService(
            database=SessionLocal(),
            logger=logging.getLogger(__name__)
        )

# Usage
user_service = ServiceFactory.create_user_service()
```

**After:**
```python
# Register once
registrar().register_scoped(UserService, UserService)

# Usage anywhere
user_service = container.resolve(UserService)
```

## Conclusion

This dependency injection system provides a robust, scalable foundation for your FastAPI application. It promotes:

- **Loose Coupling**: Services depend on abstractions, not implementations
- **Testability**: Easy to mock and test individual components
- **Maintainability**: Clear dependency graph and service lifecycle
- **Performance**: Optimized service instantiation and connection pooling
- **Observability**: Built-in metrics and health monitoring

The system is designed to grow with your application, from simple prototypes to complex, production-grade systems.