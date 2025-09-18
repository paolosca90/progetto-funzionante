"""
Dependency Injection Integration for Async Services

This module integrates the comprehensive dependency injection system with existing async services,
providing backward compatibility while enabling advanced DI features.
"""

import logging
from typing import Optional, Dict, Any, List
import asyncio

from ..core.dependency_injection import (
    FastAPIDependencyContainer, get_container, set_container,
    ServiceLifetime, resolve_service
)
from ..containers.service_containers import (
    ServiceContainerFactory, initialize_dependency_injection,
    dispose_dependency_injection
)
from ..middleware.dependency_injection_middleware import add_all_di_middleware

logger = logging.getLogger(__name__)

# Global factory instance
_service_factory: Optional[ServiceContainerFactory] = None


async def init_dependency_injection() -> bool:
    """Initialize dependency injection system"""
    global _service_factory

    try:
        logger.info("Initializing dependency injection system...")

        # Create service container factory
        _service_factory = ServiceContainerFactory()

        # Register all services
        await asyncio.get_event_loop().run_in_executor(
            None, _service_factory.register_all_services
        )

        logger.info("Dependency injection system initialized successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to initialize dependency injection system: {e}")
        return False


async def cleanup_dependency_injection() -> None:
    """Cleanup dependency injection system"""
    global _service_factory

    try:
        if _service_factory:
            await asyncio.get_event_loop().run_in_executor(
                None, _service_factory.dispose
            )
            _service_factory = None

        logger.info("Dependency injection system cleaned up successfully")

    except Exception as e:
        logger.error(f"Error cleaning up dependency injection system: {e}")


def add_dependency_injection_middleware(app) -> None:
    """Add dependency injection middleware to FastAPI app"""
    try:
        container = get_container()
        add_all_di_middleware(app, container)
        logger.info("Dependency injection middleware added successfully")

    except Exception as e:
        logger.error(f"Failed to add dependency injection middleware: {e}")


def get_service_metrics() -> Dict[str, Any]:
    """Get service metrics from dependency container"""
    try:
        container = get_container()

        metrics = {
            'container_initialized': container._initialized,
            'total_services': len(container._services),
            'singleton_services': len(container._singleton_instances),
            'dependency_graph': {
                service: list(dependencies)
                for service, dependencies in container._dependency_graph.items()
            }
        }

        # Add service-specific metrics if available
        try:
            from ..services.logging_service import LoggingService
            logging_service = container.resolve(LoggingService)
            metrics['logging'] = logging_service.get_metrics()
        except:
            pass

        try:
            from ..services.database_service import DatabaseService
            database_service = container.resolve(DatabaseService)
            metrics['database'] = database_service.get_metrics()
        except:
            pass

        return metrics

    except Exception as e:
        logger.error(f"Failed to get service metrics: {e}")
        return {'error': str(e)}


async def health_check_dependency_injection() -> Dict[str, Any]:
    """Perform health check on dependency injection system"""
    try:
        container = get_container()

        health_status = {
            'container_healthy': container._initialized,
            'services_count': len(container._services),
            'singleton_instances': len(container._singleton_instances),
            'services': {}
        }

        # Check individual service health
        services_to_check = [
            ('logging_service', 'LoggingService'),
            ('database_service', 'DatabaseService'),
            ('config_service', 'ConfigService'),
        ]

        healthy_services = 0

        for service_name, service_type in services_to_check:
            try:
                from importlib import import_module
                module_path, class_name = service_type.rsplit('.', 1)
                module = import_module(f'..services.{module_path}', __name__)
                service_class = getattr(module, class_name)

                service = container.resolve(service_class)

                if hasattr(service, 'health_check'):
                    service_health = await service.health_check()
                    health_status['services'][service_name] = service_health

                    if service_health.get('status') == 'healthy':
                        healthy_services += 1
                else:
                    health_status['services'][service_name] = {'status': 'healthy'}
                    healthy_services += 1

            except Exception as e:
                health_status['services'][service_name] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }

        # Overall health status
        if healthy_services == len(services_to_check):
            health_status['overall_status'] = 'healthy'
        elif healthy_services > 0:
            health_status['overall_status'] = 'degraded'
        else:
            health_status['overall_status'] = 'unhealthy'

        health_status['healthy_services_count'] = healthy_services
        health_status['total_services_checked'] = len(services_to_check)

        return health_status

    except Exception as e:
        logger.error(f"Dependency injection health check failed: {e}")
        return {
            'overall_status': 'unhealthy',
            'error': str(e)
        }


def get_service_container_factory() -> Optional[ServiceContainerFactory]:
    """Get the service container factory"""
    return _service_factory


# FastAPI dependency helpers
def get_dependency_container():
    """FastAPI dependency for getting the dependency container"""
    return get_container()


def get_config_service():
    """FastAPI dependency for getting config service"""
    from ..services.config_service import ConfigService
    return resolve_service(ConfigService)


def get_logging_service():
    """FastAPI dependency for getting logging service"""
    from ..services.logging_service import LoggingService
    return resolve_service(LoggingService)


def get_database_service():
    """FastAPI dependency for getting database service"""
    from ..services.database_service import DatabaseService
    return resolve_service(DatabaseService)


def get_oanda_service():
    """FastAPI dependency for getting OANDA service"""
    from ..services.external.oanda_service import OandaService
    return resolve_service(OandaService)


def get_redis_service():
    """FastAPI dependency for getting Redis service"""
    from ..services.external.redis_service import RedisService
    return resolve_service(RedisService)


def get_cache_service():
    """FastAPI dependency for getting cache service"""
    from ..services.cache_service import CacheService
    return resolve_service(CacheService)


def get_auth_service():
    """FastAPI dependency for getting auth service"""
    from ..services.auth_service import AuthService
    return resolve_service(AuthService)


def get_user_service():
    """FastAPI dependency for getting user service"""
    from ..services.user_service import UserService
    return resolve_service(UserService)


def get_signal_service():
    """FastAPI dependency for getting signal service"""
    from ..services.signal_service import SignalService
    return resolve_service(SignalService)


# Backward compatibility functions
def get_db():
    """Backward compatibility database session getter"""
    from ..services.database_service import DatabaseService
    try:
        container = get_container()
        db_service = container.resolve(DatabaseService)
        return db_service.get_session()
    except:
        # Fallback to original implementation
        from database import SessionLocal
        return SessionLocal()


def get_auth_service_legacy():
    """Backward compatibility auth service getter"""
    from ..services.auth_service import AuthService
    try:
        container = get_container()
        db_service = container.resolve(DatabaseService)
        return AuthService(db_service.get_session())
    except:
        # Fallback to original implementation
        from database import SessionLocal
        return AuthService(SessionLocal())


def get_signal_service_legacy():
    """Backward compatibility signal service getter"""
    from ..services.signal_service import SignalService
    try:
        container = get_container()
        db_service = container.resolve(DatabaseService)
        return SignalService(db_service.get_session())
    except:
        # Fallback to original implementation
        from database import SessionLocal
        return SignalService(SessionLocal())


def get_user_service_legacy():
    """Backward compatibility user service getter"""
    from ..services.user_service import UserService
    try:
        container = get_container()
        db_service = container.resolve(DatabaseService)
        return UserService(db_service.get_session())
    except:
        # Fallback to original implementation
        from database import SessionLocal
        return UserService(SessionLocal())


def get_oanda_service_legacy():
    """Backward compatibility OANDA service getter"""
    from ..services.external.oanda_service import OandaService
    try:
        container = get_container()
        return container.resolve(OandaService)
    except:
        # Fallback to original implementation
        from oanda_signal_engine import OANDAEngine
        return OANDAEngine()


# Service registration helpers
def register_custom_service(service_type, implementation, lifetime=ServiceLifetime.SCOPED, **kwargs):
    """Register a custom service with the dependency container"""
    try:
        container = get_container()
        container.register(service_type, implementation, lifetime, **kwargs)
        logger.info(f"Registered custom service: {service_type.__name__}")
        return True
    except Exception as e:
        logger.error(f"Failed to register custom service {service_type.__name__}: {e}")
        return False


def register_service_with_factory(service_type, factory_function, lifetime=ServiceLifetime.SCOPED, **kwargs):
    """Register a service with a factory function"""
    try:
        container = get_container()
        descriptor = container._services.get(service_type)
        if descriptor:
            descriptor.factory = factory_function
            logger.info(f"Registered factory for service: {service_type.__name__}")
            return True
        else:
            logger.error(f"Service {service_type.__name__} not registered")
            return False
    except Exception as e:
        logger.error(f"Failed to register factory for service {service_type.__name__}: {e}")
        return False


# Utility functions
def is_dependency_injection_enabled() -> bool:
    """Check if dependency injection is enabled"""
    try:
        container = get_container()
        return container._initialized
    except:
        return False


def get_registered_services() -> List[str]:
    """Get list of registered service names"""
    try:
        container = get_container()
        return [service_type.__name__ for service_type in container._services.keys()]
    except:
        return []


def get_service_dependencies(service_type) -> List[str]:
    """Get dependencies for a service"""
    try:
        container = get_container()
        descriptor = container._services.get(service_type)
        if descriptor:
            return descriptor.dependencies
        return []
    except:
        return []


def validate_service_dependencies() -> Dict[str, Any]:
    """Validate all service dependencies"""
    try:
        container = get_container()
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'services_validated': 0
        }

        for service_type, descriptor in container._services.items():
            validation_result['services_validated'] += 1

            # Check for missing dependencies
            for dep_name in descriptor.dependencies:
                dep_found = False
                for dep_type in container._services.keys():
                    if dep_type.__name__ == dep_name:
                        dep_found = True
                        break

                if not dep_found:
                    validation_result['valid'] = False
                    validation_result['errors'].append(
                        f"Service {service_type.__name__} depends on missing service {dep_name}"
                    )

        return validation_result

    except Exception as e:
        return {
            'valid': False,
            'errors': [f"Dependency validation failed: {e}"],
            'warnings': [],
            'services_validated': 0
        }


# Export public API
__all__ = [
    # Initialization
    'init_dependency_injection',
    'cleanup_dependency_injection',
    'add_dependency_injection_middleware',

    # Service access
    'get_dependency_container',
    'get_config_service',
    'get_logging_service',
    'get_database_service',
    'get_oanda_service',
    'get_redis_service',
    'get_cache_service',
    'get_auth_service',
    'get_user_service',
    'get_signal_service',

    # Backward compatibility
    'get_db',
    'get_auth_service_legacy',
    'get_signal_service_legacy',
    'get_user_service_legacy',
    'get_oanda_service_legacy',

    # Service registration
    'register_custom_service',
    'register_service_with_factory',

    # Utilities
    'is_dependency_injection_enabled',
    'get_registered_services',
    'get_service_dependencies',
    'validate_service_dependencies',
    'get_service_metrics',
    'health_check_dependency_injection',
    'get_service_container_factory',
]