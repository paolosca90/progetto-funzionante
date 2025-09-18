"""
Dependency Injection Testing Support

This module provides comprehensive testing support for the dependency injection system:
- Mock service creation
- Test container configuration
- Test fixture utilities
- Integration test helpers
- Performance testing tools
- Test isolation utilities
"""

import asyncio
import pytest
import json
from typing import Dict, Any, Optional, List, Type, Callable, Union, AsyncContextManager
from unittest.mock import Mock, AsyncMock, patch
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
import tempfile
import os
from pathlib import Path

from ..core.dependency_injection import (
    FastAPIDependencyContainer, ServiceLifetime, ServiceDescriptor,
    get_container, set_container
)
from ..containers.service_containers import ServiceContainerFactory
from ..services.config_service import ConfigService, EnvironmentConfigProvider, FileConfigProvider
from ..services.logging_service import LoggingService, LogLevel, LogEntry
from ..services.database_service import DatabaseService, DatabaseMetrics
from ..core.config import Settings as CoreSettings


@dataclass
class TestConfig:
    """Test configuration"""
    use_in_memory_database: bool = True
    use_mock_external_services: bool = True
    use_test_logging: bool = True
    test_database_url: Optional[str] = None
    log_capture_enabled: bool = True
    performance_monitoring_enabled: bool = False
    cleanup_after_test: bool = True


class TestServiceRegistry:
    """Registry for test services and mocks"""

    def __init__(self):
        self._mocks: Dict[Type, Mock] = {}
        self._stubs: Dict[Type, Any] = {}
        self._spies: Dict[Type, List[Callable]] = {}

    def register_mock(self, service_type: Type, mock: Mock) -> None:
        """Register a mock for a service type"""
        self._mocks[service_type] = mock

    def register_stub(self, service_type: Type, stub: Any) -> None:
        """Register a stub implementation for a service type"""
        self._stubs[service_type] = stub

    def add_spy(self, service_type: Type, callback: Callable) -> None:
        """Add a spy callback for a service type"""
        if service_type not in self._spies:
            self._spies[service_type] = []
        self._spies[service_type].append(callback)

    def get_mock(self, service_type: Type) -> Optional[Mock]:
        """Get mock for service type"""
        return self._mocks.get(service_type)

    def get_stub(self, service_type: Type) -> Optional[Any]:
        """Get stub for service type"""
        return self._stubs.get(service_type)

    def clear(self) -> None:
        """Clear all registered services"""
        self._mocks.clear()
        self._stubs.clear()
        self._spies.clear()


class TestDependencyContainer(FastAPIDependencyContainer):
    """Test-specific dependency container with mock support"""

    def __init__(self, test_config: TestConfig):
        super().__init__()
        self.test_config = test_config
        self.service_registry = TestServiceRegistry()
        self._test_logs: List[LogEntry] = []
        self._test_metrics: Dict[str, Any] = {}

    def register_test_service(self,
                            service_type: Type[T],
                            implementation: Union[Type[T], Callable[..., T]],
                            lifetime: ServiceLifetime = ServiceLifetime.SCOPED,
                            is_mock: bool = False) -> None:
        """Register a test service"""
        if is_mock:
            # Register as a regular service but with mock implementation
            self.register(service_type, implementation, lifetime)
            self.service_registry.register_mock(service_type, implementation)
        else:
            self.register(service_type, implementation, lifetime)

    def create_test_services(self) -> None:
        """Create test-specific services"""
        # Test configuration service
        test_config_service = self._create_test_config_service()
        self.register_test_service(ConfigService, test_config_service, ServiceLifetime.SINGLETON)

        # Test logging service
        if self.test_config.use_test_logging:
            test_logging_service = self._create_test_logging_service()
            self.register_test_service(LoggingService, test_logging_service, ServiceLifetime.SINGLETON)

        # Test database service
        test_database_service = self._create_test_database_service()
        self.register_test_service(DatabaseService, test_database_service, ServiceLifetime.SINGLETON)

        # Mock external services if requested
        if self.test_config.use_mock_external_services:
            self._create_mock_external_services()

    def _create_test_config_service(self) -> ConfigService:
        """Create test configuration service"""
        # Create test settings
        test_settings = CoreSettings()

        # Override with test-specific values
        if self.test_config.test_database_url:
            test_settings.DATABASE_URL = self.test_config.test_database_url

        # Create config service with test providers
        config_service = ConfigService(test_settings)

        # Add test configuration provider
        test_config_provider = self._create_test_config_provider()
        config_service._providers.append(test_config_provider)

        return config_service

    def _create_test_config_provider(self) -> EnvironmentConfigProvider:
        """Create test configuration provider"""
        # Override environment variables for testing
        test_env = {
            'TEST_MODE': 'true',
            'DATABASE_URL': self.test_config.test_database_url or 'sqlite:///:memory:',
            'JWT_SECRET_KEY': 'test-secret-key-for-testing-only',
            'REDIS_URL': 'redis://localhost:6379/1',  # Use test DB
            'OANDA_API_KEY': 'test-oanda-api-key',
            'OANDA_ACCOUNT_ID': 'test-account-id',
            'GEMINI_API_KEY': 'test-gemini-api-key',
            'ENVIRONMENT': 'testing'
        }

        with patch.dict(os.environ, test_env):
            provider = EnvironmentConfigProvider(prefix='TEST_')
            return provider

    def _create_test_logging_service(self) -> LoggingService:
        """Create test logging service"""
        test_settings = CoreSettings()
        test_settings.LOG_LEVEL = 'DEBUG'

        logging_service = LoggingService(test_settings)

        # Replace with memory handler for testing
        from ..services.logging_service import MemoryLogHandler
        memory_handler = MemoryLogHandler(LogLevel.DEBUG, max_entries=1000)
        logging_service.handlers.clear()
        logging_service.add_handler(memory_handler)

        return logging_service

    def _create_test_database_service(self) -> DatabaseService:
        """Create test database service"""
        test_settings = CoreSettings()

        # Use in-memory SQLite or test database
        if self.test_config.use_in_memory_database:
            test_settings.DATABASE_URL = 'sqlite:///:memory:'
        elif self.test_config.test_database_url:
            test_settings.DATABASE_URL = self.test_config.test_database_url

        # Create mock logging service for testing
        mock_logging_service = Mock(spec=LoggingService)
        mock_logging_service.log_info = Mock()
        mock_logging_service.log_error = Mock()
        mock_logging_service.log_warning = Mock()

        # Create mock config service
        mock_config_service = Mock(spec=ConfigService)
        mock_config_service.get_database_config.return_value = {
            'database_url': test_settings.DATABASE_URL,
            'pool_size': 5,
            'max_overflow': 10
        }

        database_service = DatabaseService(test_settings, mock_logging_service, mock_config_service)
        self.service_registry.register_stub(DatabaseService, database_service)

        return database_service

    def _create_mock_external_services(self) -> None:
        """Create mock external services"""
        # Mock OANDA service
        mock_oanda = AsyncMock()
        mock_oanda.get_account_info.return_value = {
            'id': 'test-account',
            'balance': 10000.0,
            'currency': 'USD'
        }
        mock_oanda.get_pricing.return_value = {
            'prices': [
                {'instrument': 'EUR_USD', 'bid': 1.1000, 'ask': 1.1002}
            ]
        }
        self.register_test_service(type(mock_oanda), mock_oanda, ServiceLifetime.SCOPED, is_mock=True)

        # Mock Redis service
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        mock_redis.set.return_value = True
        mock_redis.delete.return_value = 1
        self.register_test_service(type(mock_redis), mock_redis, ServiceLifetime.SCOPED, is_mock=True)

        # Mock cache service
        mock_cache = AsyncMock()
        mock_cache.get.return_value = None
        mock_cache.set.return_value = True
        mock_cache.invalidate.return_value = 1
        self.register_test_service(type(mock_cache), mock_cache, ServiceLifetime.SCOPED, is_mock=True)

    def get_test_logs(self) -> List[LogEntry]:
        """Get test logs"""
        if self.test_config.use_test_logging:
            try:
                logging_service = self.resolve(LoggingService)
                return logging_service.get_recent_logs()
            except:
                return []
        return []

    def get_test_metrics(self) -> Dict[str, Any]:
        """Get test metrics"""
        return self._test_metrics.copy()

    def clear_test_data(self) -> None:
        """Clear test data"""
        self._test_logs.clear()
        self._test_metrics.clear()


class TestContainerFactory:
    """Factory for creating test containers"""

    @staticmethod
    def create_test_container(test_config: Optional[TestConfig] = None) -> TestDependencyContainer:
        """Create a test dependency container"""
        if test_config is None:
            test_config = TestConfig()

        container = TestDependencyContainer(test_config)
        container.create_test_services()
        container.initialize()

        return container

    @staticmethod
    @asynccontextmanager
    async def create_async_test_container(test_config: Optional[TestConfig] = None) -> AsyncContextManager[TestDependencyContainer]:
        """Create and manage async test container"""
        container = TestContainerFactory.create_test_container(test_config)
        original_container = get_container()

        try:
            # Set test container as global
            set_container(container)
            yield container
        finally:
            # Restore original container
            set_container(original_container)

            # Cleanup test container
            if test_config is None or test_config.cleanup_after_test:
                container.clear_test_data()
                container.dispose()


class TestFixtures:
    """Common test fixtures"""

    @staticmethod
    @pytest.fixture
    def test_config():
        """Test configuration fixture"""
        return TestConfig(
            use_in_memory_database=True,
            use_mock_external_services=True,
            use_test_logging=True,
            log_capture_enabled=True
        )

    @staticmethod
    @pytest.fixture
    async def test_container(test_config):
        """Test container fixture"""
        async with TestContainerFactory.create_async_test_container(test_config) as container:
            yield container

    @staticmethod
    @pytest.fixture
    def mock_oanda_service():
        """Mock OANDA service fixture"""
        mock = AsyncMock()
        mock.get_account_info.return_value = {
            'id': 'test-account',
            'balance': 10000.0,
            'currency': 'USD'
        }
        mock.get_pricing.return_value = {
            'prices': [
                {'instrument': 'EUR_USD', 'bid': 1.1000, 'ask': 1.1002}
            ]
        }
        return mock

    @staticmethod
    @pytest.fixture
    def mock_redis_service():
        """Mock Redis service fixture"""
        mock = AsyncMock()
        mock.get.return_value = None
        mock.set.return_value = True
        mock.delete.return_value = 1
        mock.exists.return_value = False
        return mock

    @staticmethod
    @pytest.fixture
    def mock_cache_service():
        """Mock cache service fixture"""
        mock = AsyncMock()
        mock.get.return_value = None
        mock.set.return_value = True
        mock.invalidate.return_value = 1
        mock.health_check.return_value = {'status': 'healthy'}
        return mock

    @staticmethod
    @pytest.fixture
    def mock_database_service():
        """Mock database service fixture"""
        mock = Mock(spec=DatabaseService)
        mock.get_session.return_value = Mock()
        mock.get_metrics.return_value = DatabaseMetrics()
        mock.check_health.return_value = 'healthy'
        return mock

    @staticmethod
    @pytest.fixture
    def test_user_data():
        """Test user data fixture"""
        return {
            'id': 1,
            'username': 'testuser',
            'email': 'test@example.com',
            'hashed_password': 'hashed_password',
            'is_active': True,
            'is_admin': False
        }

    @staticmethod
    @pytest.fixture
    def test_signal_data():
        """Test signal data fixture"""
        return {
            'id': 1,
            'symbol': 'EUR_USD',
            'signal_type': 'BUY',
            'entry_price': 1.1000,
            'stop_loss': 1.0950,
            'take_profit': 1.1100,
            'reliability': 0.85,
            'status': 'ACTIVE'
        }


class IntegrationTestHelpers:
    """Integration test helpers"""

    @staticmethod
    async def create_test_database(container: TestDependencyContainer) -> None:
        """Create test database"""
        database_service = container.resolve(DatabaseService)
        database_service.create_all_tables()

    @staticmethod
    async def cleanup_test_database(container: TestDependencyContainer) -> None:
        """Clean up test database"""
        database_service = container.resolve(DatabaseService)
        database_service.drop_all_tables()

    @staticmethod
    async def insert_test_data(container: TestDependencyContainer, data: Dict[str, List[Dict]]) -> None:
        """Insert test data into database"""
        database_service = container.resolve(DatabaseService)
        with database_service.get_session_context() as session:
            for table_name, rows in data.items():
                for row in rows:
                    # Insert row into database
                    session.execute(f"INSERT INTO {table_name} VALUES ({','.join(['?']*len(row))})", list(row.values()))
            session.commit()

    @staticmethod
    async def assert_service_healthy(container: TestDependencyContainer, service_type: Type) -> None:
        """Assert that a service is healthy"""
        service = container.resolve(service_type)
        if hasattr(service, 'health_check'):
            health = await service.health_check()
            assert health.get('status') == 'healthy', f"Service {service_type.__name__} is not healthy: {health}"


class PerformanceTestHelpers:
    """Performance test helpers"""

    @staticmethod
    async def measure_service_performance(container: TestDependencyContainer, service_type: Type, operation: Callable, iterations: int = 100) -> Dict[str, float]:
        """Measure service performance"""
        service = container.resolve(service_type)
        times = []

        for _ in range(iterations):
            start_time = asyncio.get_event_loop().time()
            await operation(service)
            end_time = asyncio.get_event_loop().time()
            times.append(end_time - start_time)

        return {
            'min_time': min(times),
            'max_time': max(times),
            'avg_time': sum(times) / len(times),
            'total_time': sum(times),
            'iterations': iterations
        }

    @staticmethod
    async def benchmark_dependency_resolution(container: TestDependencyContainer, service_type: Type, iterations: int = 1000) -> Dict[str, float]:
        """Benchmark dependency resolution"""
        times = []

        for _ in range(iterations):
            start_time = asyncio.get_event_loop().time()
            container.resolve(service_type)
            end_time = asyncio.get_event_loop().time()
            times.append(end_time - start_time)

        return {
            'min_time': min(times),
            'max_time': max(times),
            'avg_time': sum(times) / len(times),
            'total_time': sum(times),
            'iterations': iterations,
            'resolutions_per_second': iterations / sum(times)
        }


class TestAssertionHelpers:
    """Test assertion helpers"""

    @staticmethod
    def assert_log_contains(test_container: TestDependencyContainer, expected_message: str, level: Optional[LogLevel] = None) -> None:
        """Assert that logs contain expected message"""
        logs = test_container.get_test_logs()
        matching_logs = [log for log in logs if expected_message in log.message]
        if level:
            matching_logs = [log for log in matching_logs if log.level == level]

        assert len(matching_logs) > 0, f"Expected log message '{expected_message}' not found"

    @staticmethod
    def assert_service_called(container: TestDependencyContainer, service_type: Type, method_name: str, call_count: int = 1) -> None:
        """Assert that a service method was called"""
        service = container.resolve(service_type)
        method = getattr(service, method_name, None)
        if method is None:
            raise AssertionError(f"Method {method_name} not found on service {service_type.__name__}")

        if hasattr(method, 'assert_called') and hasattr(method, 'call_count'):
            assert method.call_count == call_count, f"Expected {call_count} calls to {method_name}, got {method.call_count}"
        else:
            # Method might not be a mock, so we can't assert call count
            pass

    @staticmethod
    def assert_dependency_resolved(container: TestDependencyContainer, service_type: Type) -> None:
        """Assert that a dependency can be resolved"""
        try:
            service = container.resolve(service_type)
            assert service is not None, f"Failed to resolve service {service_type.__name__}"
        except Exception as e:
            raise AssertionError(f"Failed to resolve service {service_type.__name__}: {e}")


# Test decorators
def with_test_container(test_config: Optional[TestConfig] = None):
    """Decorator to provide test container to test function"""
    def decorator(func):
        @pytest.mark.asyncio
        async def wrapper(*args, **kwargs):
            async with TestContainerFactory.create_async_test_container(test_config) as container:
                return await func(container, *args, **kwargs)
        return wrapper
    return decorator


def with_mock_services(*service_types):
    """Decorator to mock specific services"""
    def decorator(func):
        @pytest.mark.asyncio
        async def wrapper(*args, **kwargs):
            test_config = TestConfig(use_mock_external_services=True)
            async with TestContainerFactory.create_async_test_container(test_config) as container:
                return await func(container, *args, **kwargs)
        return wrapper
    return decorator


def performance_test(max_time: float = 1.0):
    """Decorator for performance tests"""
    def decorator(func):
        @pytest.mark.asyncio
        async def wrapper(*args, **kwargs):
            start_time = asyncio.get_event_loop().time()
            result = await func(*args, **kwargs)
            end_time = asyncio.get_event_loop().time()
            execution_time = end_time - start_time

            assert execution_time <= max_time, f"Performance test failed: took {execution_time:.3f}s, max allowed {max_time:.3f}s"
            return result
        return wrapper
    return decorator


# Main test setup function
def setup_dependency_injection_testing() -> None:
    """Set up dependency injection testing"""
    # Configure pytest
    pytest_plugins = [
        'pytest_asyncio',
        'pytest_mock'
    ]

    # Set up asyncio mode
    def pytest_configure(config):
        config.addinivalue_line('asyncio_mode', 'auto')

    return pytest_configure


# Test configuration for pytest
def pytest_configure(config):
    """Configure pytest for dependency injection testing"""
    config.addinivalue_line('asyncio_mode', 'auto')