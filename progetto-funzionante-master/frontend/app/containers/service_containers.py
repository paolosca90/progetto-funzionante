"""
Service Containers for Different Service Types

This module provides specialized containers for different types of services:
- Core services (configuration, logging, database)
- Business logic services (auth, users, signals)
- External services (OANDA, Redis, cache)
- Infrastructure services (HTTP clients, file services)
"""

from typing import Dict, Any, Optional, List, Set
import logging
from abc import ABC, abstractmethod

from ..core.dependency_injection import (
    FastAPIDependencyContainer, ServiceLifetime, ServiceRegistrar,
    get_container, registrar
)
from ..core.config import Settings

logger = logging.getLogger(__name__)


class BaseContainer(ABC):
    """Base class for service containers"""

    def __init__(self, container: FastAPIDependencyContainer):
        self.container = container
        self.registrar = ServiceRegistrar(container)

    @abstractmethod
    def register_services(self) -> None:
        """Register all services for this container type"""
        pass


class CoreServicesContainer(BaseContainer):
    """Container for core application services"""

    def register_services(self) -> None:
        """Register core services"""
        logger.info("Registering core services...")

        # Configuration service
        self._register_configuration_service()

        # Logging service
        self._register_logging_service()

        # Database service
        self._register_database_service()

        logger.info("Core services registered successfully")

    def _register_configuration_service(self) -> None:
        """Register configuration service"""
        from ..services.config_service import ConfigService

        self.registrar.register_singleton(
            Settings,
            Settings,
            tags={"core", "config"}
        )

        self.registrar.register_singleton(
            ConfigService,
            ConfigService,
            tags={"core", "config"}
        )

    def _register_logging_service(self) -> None:
        """Register logging service"""
        from ..services.logging_service import LoggingService

        self.registrar.register_singleton(
            LoggingService,
            LoggingService,
            tags={"core", "logging"}
        )

    def _register_database_service(self) -> None:
        """Register database service"""
        from ..services.database_service import DatabaseService

        self.registrar.register_singleton(
            DatabaseService,
            DatabaseService,
            tags={"core", "database"}
        )


class BusinessServicesContainer(BaseContainer):
    """Container for business logic services"""

    def register_services(self) -> None:
        """Register business logic services"""
        logger.info("Registering business services...")

        # Authentication service
        self._register_authentication_service()

        # User service
        self._register_user_service()

        # Signal service
        self._register_signal_service()

        # Subscription service
        self._register_subscription_service()

        logger.info("Business services registered successfully")

    def _register_authentication_service(self) -> None:
        """Register authentication service"""
        from ..services.auth_service import AuthService

        self.registrar.register_scoped(
            AuthService,
            AuthService,
            tags={"business", "auth"}
        )

    def _register_user_service(self) -> None:
        """Register user service"""
        from ..services.user_service import UserService

        self.registrar.register_scoped(
            UserService,
            UserService,
            tags={"business", "users"}
        )

    def _register_signal_service(self) -> None:
        """Register signal service"""
        from ..services.signal_service import SignalService

        self.registrar.register_scoped(
            SignalService,
            SignalService,
            tags={"business", "signals"}
        )

    def _register_subscription_service(self) -> None:
        """Register subscription service"""
        from ..services.subscription_service import SubscriptionService

        self.registrar.register_scoped(
            SubscriptionService,
            SubscriptionService,
            tags={"business", "subscription"}
        )


class ExternalServicesContainer(BaseContainer):
    """Container for external services"""

    def register_services(self) -> None:
        """Register external services"""
        logger.info("Registering external services...")

        # OANDA service
        self._register_oanda_service()

        # Redis service
        self._register_redis_service()

        # Cache service
        self._register_cache_service()

        # Email service
        self._register_email_service()

        # AI service
        self._register_ai_service()

        logger.info("External services registered successfully")

    def _register_oanda_service(self) -> None:
        """Register OANDA service"""
        from ..services.oanda_service import OANDAService

        self.registrar.register_scoped(
            OANDAService,
            OANDAService,
            tags={"external", "oanda", "trading"}
        )

    def _register_redis_service(self) -> None:
        """Register Redis service"""
        from ..services.redis_service import RedisService

        self.registrar.register_singleton(
            RedisService,
            RedisService,
            tags={"external", "redis", "cache"}
        )

    def _register_cache_service(self) -> None:
        """Register cache service"""
        from ..services.cache_service import CacheService

        self.registrar.register_scoped(
            CacheService,
            CacheService,
            tags={"external", "cache"}
        )

    def _register_email_service(self) -> None:
        """Register email service"""
        from ..services.email_service import EmailService

        self.registrar.register_scoped(
            EmailService,
            EmailService,
            tags={"external", "email"}
        )

    def _register_ai_service(self) -> None:
        """Register AI service"""
        from ..services.ai_service import AIService

        self.registrar.register_scoped(
            AIService,
            AIService,
            tags={"external", "ai", "gemini"}
        )


class InfrastructureServicesContainer(BaseContainer):
    """Container for infrastructure services"""

    def register_services(self) -> None:
        """Register infrastructure services"""
        logger.info("Registering infrastructure services...")

        # HTTP client service
        self._register_http_client_service()

        # File service
        self._register_file_service()

        # Task scheduler service
        self._register_task_scheduler_service()

        # Performance monitoring service
        self._register_performance_monitoring_service()

        logger.info("Infrastructure services registered successfully")

    def _register_http_client_service(self) -> None:
        """Register HTTP client service"""
        from ..services.http_client_service import HTTPClientService

        self.registrar.register_singleton(
            HTTPClientService,
            HTTPClientService,
            tags={"infrastructure", "http"}
        )

    def _register_file_service(self) -> None:
        """Register file service"""
        from ..services.file_service import FileService

        self.registrar.register_scoped(
            FileService,
            FileService,
            tags={"infrastructure", "file"}
        )

    def _register_task_scheduler_service(self) -> None:
        """Register task scheduler service"""
        from ..services.task_scheduler_service import TaskSchedulerService

        self.registrar.register_singleton(
            TaskSchedulerService,
            TaskSchedulerService,
            tags={"infrastructure", "scheduler"}
        )

    def _register_performance_monitoring_service(self) -> None:
        """Register performance monitoring service"""
        from ..services.performance_monitoring_service import PerformanceMonitoringService

        self.registrar.register_singleton(
            PerformanceMonitoringService,
            PerformanceMonitoringService,
            tags={"infrastructure", "monitoring"}
        )


class RepositoryContainer(BaseContainer):
    """Container for repository services"""

    def register_services(self) -> None:
        """Register repository services"""
        logger.info("Registering repository services...")

        # Base repository
        self._register_base_repository()

        # User repository
        self._register_user_repository()

        # Signal repository
        self._register_signal_repository()

        # Subscription repository
        self._register_subscription_repository()

        # OANDA connection repository
        self._register_oanda_connection_repository()

        logger.info("Repository services registered successfully")

    def _register_base_repository(self) -> None:
        """Register base repository"""
        from ..repositories.base_repository import BaseRepository

        self.registrar.register_scoped(
            BaseRepository,
            BaseRepository,
            tags={"repository", "base"}
        )

    def _register_user_repository(self) -> None:
        """Register user repository"""
        from ..repositories.user_repository import UserRepository

        self.registrar.register_scoped(
            UserRepository,
            UserRepository,
            tags={"repository", "users"}
        )

    def _register_signal_repository(self) -> None:
        """Register signal repository"""
        from ..repositories.signal_repository import SignalRepository

        self.registrar.register_scoped(
            SignalRepository,
            SignalRepository,
            tags={"repository", "signals"}
        )

    def _register_subscription_repository(self) -> None:
        """Register subscription repository"""
        from ..repositories.subscription_repository import SubscriptionRepository

        self.registrar.register_scoped(
            SubscriptionRepository,
            SubscriptionRepository,
            tags={"repository", "subscription"}
        )

    def _register_oanda_connection_repository(self) -> None:
        """Register OANDA connection repository"""
        from ..repositories.oanda_connection_repository import OANDAConnectionRepository

        self.registrar.register_scoped(
            OANDAConnectionRepository,
            OANDAConnectionRepository,
            tags={"repository", "oanda"}
        )


class ServiceContainerFactory:
    """Factory for creating and managing service containers"""

    def __init__(self, container: Optional[FastAPIDependencyContainer] = None):
        self.container = container or get_container()
        self._containers: List[BaseContainer] = []

    def register_all_services(self) -> None:
        """Register all services from all containers"""
        logger.info("Starting service registration...")

        # Create and register core services
        core_container = CoreServicesContainer(self.container)
        core_container.register_services()
        self._containers.append(core_container)

        # Create and register business services
        business_container = BusinessServicesContainer(self.container)
        business_container.register_services()
        self._containers.append(business_container)

        # Create and register external services
        external_container = ExternalServicesContainer(self.container)
        external_container.register_services()
        self._containers.append(external_container)

        # Create and register infrastructure services
        infrastructure_container = InfrastructureServicesContainer(self.container)
        infrastructure_container.register_services()
        self._containers.append(infrastructure_container)

        # Create and register repository services
        repository_container = RepositoryContainer(self.container)
        repository_container.register_services()
        self._containers.append(repository_container)

        # Initialize the container
        self.container.initialize()

        logger.info("All services registered successfully")

    def get_containers(self) -> List[BaseContainer]:
        """Get all registered containers"""
        return self._containers.copy()

    def get_services_by_tag(self, tag: str) -> List[Any]:
        """Get all services with a specific tag"""
        service_types = self.container.get_services_by_tag(tag)
        return [self.container.resolve(service_type) for service_type in service_types]

    def dispose(self) -> None:
        """Dispose all containers and services"""
        for container in self._containers:
            if hasattr(container, 'dispose'):
                try:
                    container.dispose()
                except Exception as e:
                    logger.warning(f"Error disposing container {container.__class__.__name__}: {e}")

        self.container.dispose()
        self._containers.clear()


def create_service_container_factory() -> ServiceContainerFactory:
    """Create a new service container factory"""
    return ServiceContainerFactory()


# Global factory instance
_factory: Optional[ServiceContainerFactory] = None


def get_service_container_factory() -> ServiceContainerFactory:
    """Get the global service container factory"""
    global _factory
    if _factory is None:
        _factory = create_service_container_factory()
    return _factory


def initialize_dependency_injection() -> ServiceContainerFactory:
    """Initialize the dependency injection system"""
    factory = get_service_container_factory()
    factory.register_all_services()
    return factory


def dispose_dependency_injection() -> None:
    """Dispose the dependency injection system"""
    global _factory
    if _factory is not None:
        _factory.dispose()
        _factory = None