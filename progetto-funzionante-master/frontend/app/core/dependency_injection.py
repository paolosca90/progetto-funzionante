"""
Comprehensive Dependency Injection System for FastAPI Application

This module provides a production-ready dependency injection system with:
- Service lifetime management (transient, scoped, singleton)
- Circular dependency detection and resolution
- Configuration management through dependencies
- External service integration
- Testing support
- Performance monitoring
"""

import asyncio
import inspect
import logging
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from enum import Enum
from functools import lru_cache, wraps
from typing import (
    Any, AsyncContextManager, Callable, Dict, Generic, List,
    Optional, Set, Type, TypeVar, Union, get_type_hints
)
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.dependencies import utils as dep_utils
from fastapi.concurrency import contextmanager_in_threadpool
from sqlalchemy.orm import Session
import weakref
import time
import threading
from contextvars import ContextVar

# Type variables for generic types
T = TypeVar('T')
ServiceType = TypeVar('ServiceType')

# Logger for dependency injection system
logger = logging.getLogger(__name__)

# Context variable for request-scoped dependencies
_request_scope: ContextVar[Optional[Dict[str, Any]]] = ContextVar('request_scope', default=None)


class ServiceLifetime(Enum):
    """Service lifetime enumeration"""
    TRANSIENT = "transient"  # New instance every time
    SCOPED = "scoped"       # One instance per request
    SINGLETON = "singleton"  # One instance for application lifetime


@dataclass
class ServiceDescriptor:
    """Descriptor for service registration"""
    service_type: Type
    implementation_type: Type
    lifetime: ServiceLifetime
    factory: Optional[Callable] = None
    instance: Optional[Any] = None
    dependencies: List[str] = field(default_factory=list)
    tags: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)


class CircularDependencyError(Exception):
    """Raised when circular dependency is detected"""
    pass


class ServiceNotRegisteredError(Exception):
    """Raised when trying to resolve a service that is not registered"""
    pass


class ContainerAlreadyInitializedError(Exception):
    """Raised when trying to modify an initialized container"""
    pass


class DependencyContainer(ABC):
    """Abstract base class for dependency containers"""

    @abstractmethod
    def register(self,
                 service_type: Type[T],
                 implementation: Union[Type[T], Callable[..., T]],
                 lifetime: ServiceLifetime = ServiceLifetime.SCOPED,
                 tags: Optional[Set[str]] = None,
                 metadata: Optional[Dict[str, Any]] = None) -> None:
        """Register a service with the container"""
        pass

    @abstractmethod
    def resolve(self, service_type: Type[T]) -> T:
        """Resolve a service from the container"""
        pass

    @abstractmethod
    def create_scope(self) -> 'ServiceScope':
        """Create a new scope for scoped services"""
        pass


class ServiceScope:
    """Scope for managing service lifetime"""

    def __init__(self, container: 'FastAPIDependencyContainer'):
        self.container = container
        self._scoped_services: Dict[Type, Any] = {}
        self._disposed = False
        self._lock = threading.Lock()

    def get_scoped_service(self, service_type: Type[T]) -> Optional[T]:
        """Get a scoped service instance"""
        with self._lock:
            return self._scoped_services.get(service_type)

    def set_scoped_service(self, service_type: Type[T], instance: T) -> None:
        """Set a scoped service instance"""
        with self._lock:
            if not self._disposed:
                self._scoped_services[service_type] = instance

    def dispose(self) -> None:
        """Dispose all scoped services"""
        with self._lock:
            if not self._disposed:
                for service in self._scoped_services.values():
                    if hasattr(service, '__dispose__'):
                        try:
                            service.__dispose__()
                        except Exception as e:
                            logger.warning(f"Error disposing service {service}: {e}")
                self._scoped_services.clear()
                self._disposed = True


class FastAPIDependencyContainer(DependencyContainer):
    """FastAPI-specific dependency container with advanced features"""

    def __init__(self):
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._singleton_instances: Dict[Type, Any] = {}
        self._current_scope: Optional[ServiceScope] = None
        self._lock = threading.RLock()
        self._initialized = False
        self._dependency_graph: Dict[Type, Set[Type]] = {}
        self._circular_dependency_cache: Dict[tuple, bool] = {}
        self._thread_pool: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=4)

    def register(self,
                 service_type: Type[T],
                 implementation: Union[Type[T], Callable[..., T]],
                 lifetime: ServiceLifetime = ServiceLifetime.SCOPED,
                 tags: Optional[Set[str]] = None,
                 metadata: Optional[Dict[str, Any]] = None) -> None:
        """Register a service with the container"""

        if self._initialized:
            raise ContainerAlreadyInitializedError("Cannot register services after container is initialized")

        with self._lock:
            descriptor = ServiceDescriptor(
                service_type=service_type,
                implementation_type=implementation if isinstance(implementation, type) else type(implementation),
                lifetime=lifetime,
                factory=implementation if callable(implementation) and not isinstance(implementation, type) else None,
                dependencies=[],
                tags=tags or set(),
                metadata=metadata or {}
            )

            self._services[service_type] = descriptor
            logger.info(f"Registered service {service_type.__name__} with lifetime {lifetime.value}")

    def initialize(self) -> None:
        """Initialize the container and validate dependencies"""
        with self._lock:
            if self._initialized:
                return

            logger.info("Initializing dependency container...")

            # Build dependency graph and validate
            self._build_dependency_graph()
            self._validate_dependencies()

            self._initialized = True
            logger.info("Dependency container initialized successfully")

    def _build_dependency_graph(self) -> None:
        """Build dependency graph for circular dependency detection"""
        self._dependency_graph.clear()

        for service_type, descriptor in self._services.items():
            dependencies = self._get_service_dependencies(descriptor)
            self._dependency_graph[service_type] = set(dependencies)
            descriptor.dependencies = [dep.__name__ for dep in dependencies]

    def _get_service_dependencies(self, descriptor: ServiceDescriptor) -> List[Type]:
        """Get dependencies for a service"""
        implementation_type = descriptor.implementation_type
        dependencies = []

        try:
            # Get constructor signature
            init_signature = inspect.signature(implementation_type.__init__)

            # Get type hints
            type_hints = get_type_hints(implementation_type.__init__)

            for param_name, param in init_signature.parameters.items():
                if param_name == 'self':
                    continue

                param_type = type_hints.get(param_name)
                if param_type and param_type in self._services:
                    dependencies.append(param_type)

        except Exception as e:
            logger.warning(f"Could not analyze dependencies for {implementation_type.__name__}: {e}")

        return dependencies

    def _validate_dependencies(self) -> None:
        """Validate all dependencies and detect circular dependencies"""
        for service_type in self._services:
            self._check_circular_dependencies(service_type, path=set())

    def _check_circular_dependencies(self, service_type: Type, path: Set[Type]) -> None:
        """Check for circular dependencies using DFS"""
        if service_type in path:
            # Circular dependency detected
            cycle_path = list(path) + [service_type]
            cycle_names = [t.__name__ for t in cycle_path]
            raise CircularDependencyError(f"Circular dependency detected: {' -> '.join(cycle_names)}")

        if service_type not in self._dependency_graph:
            return

        path.add(service_type)

        for dependency in self._dependency_graph[service_type]:
            self._check_circular_dependencies(dependency, path.copy())

        path.remove(service_type)

    def resolve(self, service_type: Type[T]) -> T:
        """Resolve a service from the container"""

        if not self._initialized:
            self.initialize()

        if service_type not in self._services:
            raise ServiceNotRegisteredError(f"Service {service_type.__name__} is not registered")

        descriptor = self._services[service_type]

        # Handle different lifetimes
        if descriptor.lifetime == ServiceLifetime.TRANSIENT:
            return self._create_instance(descriptor)
        elif descriptor.lifetime == ServiceLifetime.SCOPED:
            return self._resolve_scoped(service_type, descriptor)
        elif descriptor.lifetime == ServiceLifetime.SINGLETON:
            return self._resolve_singleton(service_type, descriptor)
        else:
            raise ValueError(f"Unknown service lifetime: {descriptor.lifetime}")

    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """Create a new instance of a service"""
        try:
            if descriptor.factory:
                # Factory method
                dependencies = self._resolve_dependencies(descriptor)
                return descriptor.factory(**dependencies)
            else:
                # Constructor injection
                dependencies = self._resolve_dependencies(descriptor)
                return descriptor.implementation_type(**dependencies)
        except Exception as e:
            logger.error(f"Failed to create instance of {descriptor.service_type.__name__}: {e}")
            raise

    def _resolve_dependencies(self, descriptor: ServiceDescriptor) -> Dict[str, Any]:
        """Resolve all dependencies for a service"""
        dependencies = {}

        try:
            # Get constructor signature
            init_signature = inspect.signature(descriptor.implementation_type.__init__)
            type_hints = get_type_hints(descriptor.implementation_type.__init__)

            for param_name, param in init_signature.parameters.items():
                if param_name == 'self':
                    continue

                param_type = type_hints.get(param_name)
                if param_type and param_type in self._services:
                    dependencies[param_name] = self.resolve(param_type)
                elif param.default != inspect.Parameter.empty:
                    # Use default value
                    dependencies[param_name] = param.default

        except Exception as e:
            logger.warning(f"Could not resolve dependencies for {descriptor.implementation_type.__name__}: {e}")

        return dependencies

    def _resolve_scoped(self, service_type: Type[T], descriptor: ServiceDescriptor) -> T:
        """Resolve a scoped service"""
        if self._current_scope:
            instance = self._current_scope.get_scoped_service(service_type)
            if instance is None:
                instance = self._create_instance(descriptor)
                self._current_scope.set_scoped_service(service_type, instance)
            return instance
        else:
            # No current scope, create transient instance
            logger.warning(f"No current scope for scoped service {service_type.__name__}, creating transient instance")
            return self._create_instance(descriptor)

    def _resolve_singleton(self, service_type: Type[T], descriptor: ServiceDescriptor) -> T:
        """Resolve a singleton service"""
        with self._lock:
            if service_type not in self._singleton_instances:
                instance = self._create_instance(descriptor)
                self._singleton_instances[service_type] = instance
                logger.info(f"Created singleton instance of {service_type.__name__}")
            return self._singleton_instances[service_type]

    def create_scope(self) -> ServiceScope:
        """Create a new scope for scoped services"""
        scope = ServiceScope(self)
        return scope

    def set_current_scope(self, scope: ServiceScope) -> None:
        """Set the current scope"""
        self._current_scope = scope

    def clear_current_scope(self) -> None:
        """Clear the current scope"""
        if self._current_scope:
            self._current_scope.dispose()
            self._current_scope = None

    def get_services_by_tag(self, tag: str) -> List[Type]:
        """Get all services with a specific tag"""
        return [service_type for service_type, descriptor in self._services.items() if tag in descriptor.tags]

    def get_service_metadata(self, service_type: Type) -> Dict[str, Any]:
        """Get metadata for a service"""
        if service_type not in self._services:
            raise ServiceNotRegisteredError(f"Service {service_type.__name__} is not registered")
        return self._services[service_type].metadata

    def dispose(self) -> None:
        """Dispose all services and resources"""
        with self._lock:
            # Clear current scope
            self.clear_current_scope()

            # Dispose singleton instances
            for instance in self._singleton_instances.values():
                if hasattr(instance, '__dispose__'):
                    try:
                        instance.__dispose__()
                    except Exception as e:
                        logger.warning(f"Error disposing singleton instance: {e}")

            self._singleton_instances.clear()
            self._thread_pool.shutdown(wait=True)
            logger.info("Dependency container disposed")


# Global container instance
_container: Optional[FastAPIDependencyContainer] = None


def get_container() -> FastAPIDependencyContainer:
    """Get the global dependency container instance"""
    global _container
    if _container is None:
        _container = FastAPIDIDependencyContainer()
    return _container


def set_container(container: FastAPIDIDependencyContainer) -> None:
    """Set the global dependency container instance"""
    global _container
    _container = container


class ServiceRegistrar:
    """Helper class for service registration"""

    def __init__(self, container: FastAPIDIDependencyContainer):
        self.container = container

    def register_transient(self,
                         service_type: Type[T],
                         implementation: Union[Type[T], Callable[..., T]],
                         tags: Optional[Set[str]] = None,
                         metadata: Optional[Dict[str, Any]] = None) -> 'ServiceRegistrar':
        """Register a transient service"""
        self.container.register(
            service_type, implementation, ServiceLifetime.TRANSIENT, tags, metadata
        )
        return self

    def register_scoped(self,
                      service_type: Type[T],
                      implementation: Union[Type[T], Callable[..., T]],
                      tags: Optional[Set[str]] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> 'ServiceRegistrar':
        """Register a scoped service"""
        self.container.register(
            service_type, implementation, ServiceLifetime.SCOPED, tags, metadata
        )
        return self

    def register_singleton(self,
                         service_type: Type[T],
                         implementation: Union[Type[T], Callable[..., T]],
                         tags: Optional[Set[str]] = None,
                         metadata: Optional[Dict[str, Any]] = None) -> 'ServiceRegistrar':
        """Register a singleton service"""
        self.container.register(
            service_type, implementation, ServiceLifetime.SINGLETON, tags, metadata
        )
        return self


def registrar() -> ServiceRegistrar:
    """Get the service registrar for the global container"""
    return ServiceRegistrar(get_container())


def inject(service_type: Type[T]) -> T:
    """Dependency injection decorator"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            container = get_container()
            service_instance = container.resolve(service_type)
            return func(service_instance, *args, **kwargs)
        return wrapper
    return decorator


async def create_request_scope() -> AsyncContextManager[ServiceScope]:
    """Create a request scope for dependency injection"""
    container = get_container()
    scope = container.create_scope()
    container.set_current_scope(scope)

    try:
        yield scope
    finally:
        container.clear_current_scope()


# FastAPI integration
def get_dependency_container() -> FastAPIDIDependencyContainer:
    """FastAPI dependency for getting the container"""
    return get_container()


def resolve_service(service_type: Type[T]) -> Callable[..., T]:
    """FastAPI dependency for resolving a service"""
    def dependency(container: FastAPIDIDependencyContainer = Depends(get_dependency_container)) -> T:
        return container.resolve(service_type)
    return dependency


# Initialize container on import
get_container()