"""
Dependency Injection Middleware for FastAPI

This middleware provides:
- Request-scoped dependency management
- Automatic service lifecycle management
- Performance monitoring
- Error handling and recovery
- Context propagation
- Request correlation
"""

import time
import uuid
import asyncio
from typing import Optional, Dict, Any, Callable
from fastapi import Request, Response
from fastapi.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager
import logging

from ..core.dependency_injection import (
    FastAPIDependencyContainer, ServiceScope, create_request_scope, get_container
)
from ..services.logging_service import LoggingService, LogContext, LogLevel
from ..services.config_service import ConfigService
from ..services.database_service import DatabaseService
from ..services.performance_monitoring_service import PerformanceMonitoringService

logger = logging.getLogger(__name__)


class DependencyInjectionMiddleware(BaseHTTPMiddleware):
    """Middleware for managing dependency injection per request"""

    def __init__(self, app, container: Optional[FastAPIDependencyContainer] = None):
        super().__init__(app)
        self.container = container or get_container()
        self.performance_monitor: Optional[PerformanceMonitoringService] = None

        # Try to get performance monitor from container
        try:
            self.performance_monitor = self.container.resolve(PerformanceMonitoringService)
        except Exception:
            # Performance monitor not available, continue without it
            pass

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Dispatch request with dependency injection context"""
        start_time = time.time()
        correlation_id = str(uuid.uuid4())
        request_id = str(uuid.uuid4())

        # Create request context
        context = LogContext(
            request_id=request_id,
            operation=f"{request.method} {request.url.path}",
            metadata={
                'method': request.method,
                'url': str(request.url),
                'user_agent': request.headers.get('user-agent', ''),
                'client_ip': request.client.host if request.client else 'unknown',
                'correlation_id': correlation_id
            }
        )

        # Create scope for this request
        scope = None
        response = None

        try:
            # Start request scope for dependency injection
            async with create_request_scope() as request_scope:
                scope = request_scope
                self.container.set_current_scope(scope)

                # Set correlation ID in logging service if available
                try:
                    logging_service = self.container.resolve(LoggingService)
                    logging_service.set_correlation_id(correlation_id)
                except Exception:
                    # Logging service not available, continue without it
                    pass

                # Log request start
                try:
                    logging_service = self.container.resolve(LoggingService)
                    logging_service.log_info(
                        f"Request started: {request.method} {request.url.path}",
                        context=context
                    )
                except Exception:
                    # Logging service not available, continue without it
                    pass

                # Add request scope to request state for access in route handlers
                request.state.di_scope = scope
                request.state.correlation_id = correlation_id
                request.state.request_id = request_id

                # Track performance if available
                if self.performance_monitor:
                    self.performance_monitor.start_request_tracking(request_id, request)

                # Process the request
                try:
                    response = await call_next(request)
                except Exception as e:
                    # Handle errors with proper logging
                    await self._handle_request_error(e, request, context)
                    raise

                # Add response headers
                response.headers["X-Correlation-ID"] = correlation_id
                response.headers["X-Request-ID"] = request_id

                # Log request completion
                duration = time.time() - start_time
                await self._log_request_completion(request, response, duration, context)

                # Track performance metrics
                if self.performance_monitor:
                    self.performance_monitor.end_request_tracking(
                        request_id, response, duration
                    )

                return response

        except Exception as e:
            # Handle middleware-level errors
            logger.error(f"Dependency injection middleware error: {e}")
            raise
        finally:
            # Clean up scope
            if scope:
                try:
                    scope.dispose()
                except Exception as e:
                    logger.error(f"Error disposing request scope: {e}")

            self.container.clear_current_scope()

    async def _handle_request_error(self, error: Exception, request: Request, context: LogContext) -> None:
        """Handle request errors with proper logging"""
        try:
            logging_service = self.container.resolve(LoggingService)
            logging_service.log_error(
                f"Request failed: {request.method} {request.url.path}",
                context=context,
                exception=error,
                extra={
                    'error_type': type(error).__name__,
                    'error_message': str(error)
                }
            )
        except Exception:
            # Logging service not available, use standard logger
            logger.error(f"Request failed: {request.method} {request.url.path} - {error}")

    async def _log_request_completion(self, request: Request, response: Response, duration: float, context: LogContext) -> None:
        """Log request completion with metrics"""
        try:
            logging_service = self.container.resolve(LoggingService)

            # Update context with response info
            context.metadata.update({
                'duration': duration,
                'status_code': response.status_code,
                'response_size': len(response.body) if hasattr(response, 'body') else 0
            })

            # Determine log level based on status code
            if response.status_code >= 500:
                log_level = LogLevel.ERROR
            elif response.status_code >= 400:
                log_level = LogLevel.WARNING
            else:
                log_level = LogLevel.INFO

            message = f"Request completed: {request.method} {request.url.path} - {response.status_code}"

            logging_service.log(
                level=log_level,
                message=message,
                context=context,
                extra={
                    'duration': duration,
                    'status_code': response.status_code,
                    'method': request.method,
                    'path': request.url.path
                }
            )

        except Exception as e:
            logger.error(f"Error logging request completion: {e}")


class DatabaseSessionMiddleware(BaseHTTPMiddleware):
    """Middleware for managing database sessions per request"""

    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Dispatch request with database session management"""
        # Get database service from container
        container = get_container()
        database_service = None
        session = None

        try:
            database_service = container.resolve(DatabaseService)
            session = database_service.get_session()

            # Add session to request state
            request.state.db_session = session

            # Process request
            response = await call_next(request)

            # Commit transaction if successful
            if response.status_code < 400:
                session.commit()

            return response

        except Exception as e:
            # Rollback transaction on error
            if session:
                session.rollback()
            raise
        finally:
            # Close session
            if session:
                session.close()


class ConfigurationMiddleware(BaseHTTPMiddleware):
    """Middleware for configuration validation and management"""

    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> None:
        """Dispatch request with configuration validation"""
        try:
            # Get configuration service
            container = get_container()
            config_service = container.resolve(ConfigService)

            # Validate configuration (can be cached)
            if not hasattr(config_service, '_validation_cache'):
                config_service._validation_cache = True
                # Validate critical configurations
                db_config = config_service.get_database_config()
                auth_config = config_service.get_auth_config()

                # Add validation results to request state
                request.state.config_validation = {
                    'database': bool(db_config.get('database_url')),
                    'auth': bool(auth_config.get('jwt_secret_key')),
                    'valid': True
                }

        except Exception as e:
            logger.warning(f"Configuration validation failed: {e}")
            request.state.config_validation = {
                'database': False,
                'auth': False,
                'valid': False,
                'error': str(e)
            }

        # Process request
        return await call_next(request)


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """Middleware for performance monitoring and metrics collection"""

    def __init__(self, app):
        super().__init__(app)
        self.performance_monitor = None

        # Try to get performance monitor from container
        try:
            container = get_container()
            self.performance_monitor = container.resolve(PerformanceMonitoringService)
        except Exception:
            # Performance monitor not available, continue without it
            pass

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Dispatch request with performance monitoring"""
        start_time = time.time()
        request_id = str(uuid.uuid4())

        # Add request ID to state
        request.state.request_id = request_id

        try:
            # Start tracking if performance monitor is available
            if self.performance_monitor:
                self.performance_monitor.start_request_tracking(request_id, request)

            # Process request
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Track performance metrics
            if self.performance_monitor:
                self.performance_monitor.end_request_tracking(request_id, response, duration)

            # Add performance headers
            response.headers["X-Response-Time"] = f"{duration:.3f}s"
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            # Track error metrics
            duration = time.time() - start_time
            if self.performance_monitor:
                self.performance_monitor.track_error(request_id, e, duration)
            raise


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for centralized error handling"""

    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Dispatch request with error handling"""
        try:
            return await call_next(request)
        except Exception as e:
            return await self._handle_error(e, request)

    async def _handle_error(self, error: Exception, request: Request) -> Response:
        """Handle errors with proper logging and response"""
        error_id = str(uuid.uuid4())
        correlation_id = getattr(request.state, 'correlation_id', 'unknown')

        # Log error with context
        try:
            container = get_container()
            logging_service = container.resolve(LoggingService)

            context = LogContext(
                request_id=getattr(request.state, 'request_id', 'unknown'),
                operation=f"Error: {request.method} {request.url.path}",
                metadata={
                    'error_id': error_id,
                    'correlation_id': correlation_id,
                    'error_type': type(error).__name__,
                    'error_message': str(error)
                }
            )

            logging_service.log_error(
                f"Unhandled error: {str(error)}",
                context=context,
                exception=error
            )

        except Exception as log_error:
            logger.error(f"Error logging failed: {log_error}")
            logger.error(f"Original error: {error}")

        # Return error response
        from fastapi import HTTPException
        if isinstance(error, HTTPException):
            return error

        # Generic error response
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "error_id": error_id,
                "correlation_id": correlation_id,
                "message": "An unexpected error occurred"
            }
        )


class RequestTracingMiddleware(BaseHTTPMiddleware):
    """Middleware for request tracing and correlation"""

    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Dispatch request with tracing"""
        # Extract or generate correlation ID
        correlation_id = request.headers.get('X-Correlation-ID') or str(uuid.uuid4())
        trace_id = request.headers.get('X-Trace-ID') or str(uuid.uuid4())
        span_id = str(uuid.uuid4())

        # Add to request state
        request.state.correlation_id = correlation_id
        request.state.trace_id = trace_id
        request.state.span_id = span_id

        # Add tracing headers to response
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Trace-ID"] = trace_id
        response.headers["X-Span-ID"] = span_id

        return response


def create_dependency_injection_middleware(container: Optional[FastAPIDependencyContainer] = None) -> Middleware:
    """Create dependency injection middleware"""
    return Middleware(DependencyInjectionMiddleware, container=container)


def create_database_session_middleware() -> Middleware:
    """Create database session middleware"""
    return Middleware(DatabaseSessionMiddleware)


def create_configuration_middleware() -> Middleware:
    """Create configuration middleware"""
    return Middleware(ConfigurationMiddleware)


def create_performance_monitoring_middleware() -> Middleware:
    """Create performance monitoring middleware"""
    return Middleware(PerformanceMonitoringMiddleware)


def create_error_handling_middleware() -> Middleware:
    """Create error handling middleware"""
    return Middleware(ErrorHandlingMiddleware)


def create_request_tracing_middleware() -> Middleware:
    """Create request tracing middleware"""
    return Middleware(RequestTracingMiddleware)


def add_all_di_middleware(app, container: Optional[FastAPIDependencyContainer] = None) -> None:
    """Add all dependency injection middleware to the app"""
    # Add middleware in order
    app.add_middleware(RequestTracingMiddleware)
    app.add_middleware(ConfigurationMiddleware)
    app.add_middleware(DependencyInjectionMiddleware, container=container)
    app.add_middleware(DatabaseSessionMiddleware)
    app.add_middleware(PerformanceMonitoringMiddleware)
    app.add_middleware(ErrorHandlingMiddleware)

    logger.info("All dependency injection middleware added successfully")


# Utility functions for middleware integration
def get_request_correlation_id(request: Request) -> str:
    """Get correlation ID from request"""
    return getattr(request.state, 'correlation_id', 'unknown')


def get_request_scope(request: Request) -> Optional[ServiceScope]:
    """Get dependency injection scope from request"""
    return getattr(request.state, 'di_scope', None)


def get_database_session(request: Request) -> Optional[Any]:
    """Get database session from request"""
    return getattr(request.state, 'db_session', None)


def get_config_validation(request: Request) -> Dict[str, Any]:
    """Get configuration validation from request"""
    return getattr(request.state, 'config_validation', {'valid': False})