"""
Error Tracking Middleware for FastAPI with Sentry Integration
Comprehensive error capture, context enrichment, and performance monitoring
"""

import time
import json
import traceback
from datetime import datetime, UTC
from typing import Optional, Dict, Any, Callable, List
from functools import wraps
import sentry_sdk
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.sentry_config import sentry_config, ErrorSeverity, ErrorCategory
from config.settings import settings


class ErrorTrackingMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive error tracking middleware for FastAPI applications
    - Captures all exceptions with rich context
    - Performance monitoring for all requests
    - User context and breadcrumbs
    - Custom error classification
    """

    def __init__(self, app):
        super().__init__(app)
        self.request_count = 0
        self.error_count = 0
        self.last_error_time = None

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process HTTP request with comprehensive error tracking
        """
        start_time = time.time()
        request_id = self._generate_request_id()

        # Initialize Sentry for this request
        if not sentry_config.initialized:
            sentry_config.initialize()

        # Add request context to Sentry
        with sentry_sdk.configure_scope() as scope:
            scope.set_tag("request_id", request_id)
            scope.set_tag("endpoint", request.url.path)
            scope.set_tag("method", request.method)
            scope.set_extra("request_details", {
                "url": str(request.url),
                "headers": dict(request.headers),
                "query_params": dict(request.query_params),
                "client_host": request.client.host if request.client else "unknown"
            })

        # Add breadcrumb for request start
        sentry_config.add_breadcrumb(
            message=f"Started {request.method} {request.url.path}",
            category="http",
            level=ErrorSeverity.INFO,
            data={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path
            }
        )

        try:
            # Add user context if available
            await self._add_user_context(request)

            # Process the request
            response = await call_next(request)

            # Monitor response time
            duration = time.time() - start_time

            # Record performance metrics
            self._record_performance_metrics(request, duration, response.status_code)

            # Add response breadcrumb
            sentry_config.add_breadcrumb(
                message=f"Completed {request.method} {request.url.path} - {response.status_code}",
                category="http",
                level=ErrorSeverity.INFO,
                data={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "duration": duration
                }
            )

            return response

        except Exception as exc:
            # Handle exception
            duration = time.time() - start_time
            self.error_count += 1
            self.last_error_time = datetime.now(UTC)

            # Capture error in Sentry
            self._capture_error(exc, request, duration, request_id)

            # Return appropriate error response
            return await self._handle_error(exc, request)

    def _generate_request_id(self) -> str:
        """Generate unique request ID"""
        self.request_count += 1
        return f"req_{self.request_count}_{int(time.time() * 1000)}"

    async def _add_user_context(self, request: Request) -> None:
        """Add user context to Sentry scope"""
        try:
            # Try to get user from JWT token
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                # You could decode JWT here to get user info
                # For now, we'll add basic context
                user_context = {
                    "ip_address": request.client.host if request.client else "unknown",
                    "user_agent": request.headers.get("User-Agent", "unknown")
                }
                sentry_config.set_user_context(user_context)
        except Exception as e:
            # Don't let user context errors break the request
            sentry_config.add_breadcrumb(
                message="Failed to add user context",
                category="auth",
                level=ErrorSeverity.WARNING,
                data={"error": str(e)}
            )

    def _record_performance_metrics(self, request: Request, duration: float, status_code: int) -> None:
        """Record performance metrics"""
        try:
            # Record request duration
            sentry_config.metrics_aggregator.timing(
                "http.request.duration",
                duration,
                tags={
                    "endpoint": request.url.path,
                    "method": request.method,
                    "status_code": str(status_code)
                }
            )

            # Record request count
            sentry_config.metrics_aggregator.increment(
                "http.request.count",
                tags={
                    "endpoint": request.url.path,
                    "method": request.method,
                    "status_code": str(status_code)
                }
            )

            # Monitor for slow requests
            if duration > 5.0:  # 5 seconds
                sentry_config.capture_message(
                    f"Slow request detected: {request.method} {request.url.path} took {duration:.2f}s",
                    level=ErrorSeverity.WARNING,
                    category=ErrorCategory.PERFORMANCE,
                    tags={
                        "endpoint": request.url.path,
                        "method": request.method,
                        "duration_category": "slow"
                    },
                    extra_data={
                        "duration": duration,
                        "status_code": status_code
                    }
                )

        except Exception as e:
            sentry_config.add_breadcrumb(
                message="Failed to record performance metrics",
                category="monitoring",
                level=ErrorSeverity.WARNING,
                data={"error": str(e)}
            )

    def _capture_error(self, error: Exception, request: Request, duration: float, request_id: str) -> None:
        """Capture error with comprehensive context"""
        try:
            # Determine error severity and category
            severity = self._determine_error_severity(error)
            category = self._determine_error_category(error)

            # Prepare context data
            context_data = {
                "request_id": request_id,
                "request_method": request.method,
                "request_path": request.url.path,
                "request_headers": dict(request.headers),
                "request_query_params": dict(request.query_params),
                "duration": duration,
                "timestamp": datetime.now(UTC).isoformat(),
                "error_traceback": traceback.format_exc()
            }

            # Add request body if available and not too large
            try:
                if hasattr(request, 'body') and request.body:
                    body = await request.body()
                    if len(body) < 10000:  # 10KB limit
                        context_data["request_body"] = body.decode('utf-8', errors='replace')
            except Exception:
                pass

            # Capture error in Sentry
            event_id = sentry_config.capture_error(
                error=error,
                level=severity,
                category=category,
                user_context={"ip_address": request.client.host if request.client else "unknown"},
                tags={
                    "request_id": request_id,
                    "endpoint": request.url.path,
                    "method": request.method,
                    "error_type": type(error).__name__
                },
                extra_data=context_data,
                fingerprint=[
                    request.method,
                    request.url.path,
                    type(error).__name__
                ]
            )

            # Check for error rate threshold
            self._check_error_rate_threshold(request)

        except Exception as capture_error:
            # Fallback logging if Sentry capture fails
            logging.error(f"Failed to capture error in Sentry: {capture_error}")
            logging.error(f"Original error: {error}")

    def _determine_error_severity(self, error: Exception) -> ErrorSeverity:
        """Determine error severity based on exception type"""
        if isinstance(error, HTTPException):
            if error.status_code >= 500:
                return ErrorSeverity.ERROR
            elif error.status_code >= 400:
                return ErrorSeverity.WARNING
            else:
                return ErrorSeverity.INFO

        # System-level errors
        system_errors = (MemoryError, SystemExit, KeyboardInterrupt, OSError)
        if isinstance(error, system_errors):
            return ErrorSeverity.CRITICAL

        # Database errors
        if any(db_error in str(type(error)) for db_error in ["SQL", "Database", "Connection"]):
            return ErrorSeverity.ERROR

        # Business logic errors
        business_errors = (ValueError, TypeError, KeyError, AttributeError)
        if isinstance(error, business_errors):
            return ErrorSeverity.WARNING

        return ErrorSeverity.ERROR

    def _determine_error_category(self, error: Exception) -> ErrorCategory:
        """Determine error category based on exception type and message"""
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()

        # Database errors
        if any(keyword in error_type or keyword in error_str for keyword in ["sql", "database", "connection", "timeout"]):
            return ErrorCategory.DATABASE

        # Authentication errors
        if any(keyword in error_type or keyword in error_str for keyword in ["auth", "jwt", "token", "unauthorized"]):
            return ErrorCategory.AUTHENTICATION

        # Validation errors
        if any(keyword in error_type or keyword in error_str for keyword in ["validation", "value", "type", "required"]):
            return ErrorCategory.VALIDATION

        # API errors
        if any(keyword in error_type or keyword in error_str for keyword in ["http", "request", "response", "api"]):
            return ErrorCategory.API

        # External service errors
        if any(keyword in error_type or keyword in error_str for keyword in ["oanda", "external", "service", "third_party"]):
            return ErrorCategory.EXTERNAL_SERVICE

        return ErrorCategory.SYSTEM

    def _check_error_rate_threshold(self, request: Request) -> None:
        """Check if error rate exceeds threshold and send alert"""
        if not settings.sentry.alert_on_error_rate_increase:
            return

        try:
            # Simple error rate calculation (you could make this more sophisticated)
            if self.request_count > 0:
                error_rate = self.error_count / self.request_count
                if error_rate > settings.sentry.error_rate_threshold:
                    sentry_config.capture_message(
                        f"High error rate detected: {error_rate:.2%} ({self.error_count}/{self.request_count} requests)",
                        level=ErrorSeverity.WARNING,
                        category=ErrorCategory.SYSTEM,
                        tags={
                            "alert_type": "high_error_rate",
                            "error_rate": f"{error_rate:.2%}",
                            "error_count": str(self.error_count),
                            "request_count": str(self.request_count)
                        },
                        extra_data={
                            "error_rate": error_rate,
                            "error_count": self.error_count,
                            "request_count": self.request_count,
                            "threshold": settings.sentry.error_rate_threshold
                        }
                    )
        except Exception as e:
            sentry_config.add_breadcrumb(
                message="Failed to check error rate threshold",
                category="monitoring",
                level=ErrorSeverity.WARNING,
                data={"error": str(e)}
            )

    async def _handle_error(self, error: Exception, request: Request) -> Response:
        """Handle error and return appropriate response"""
        # Log the error
        logging.error(f"Error processing request {request.url.path}: {error}")

        # Return appropriate response based on error type
        if isinstance(error, HTTPException):
            return JSONResponse(
                status_code=error.status_code,
                content={
                    "error": error.detail,
                    "request_id": getattr(request.state, 'request_id', 'unknown')
                }
            )
        else:
            # Generic server error
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "request_id": getattr(request.state, 'request_id', 'unknown')
                }
            )


def track_errors(category: ErrorCategory = ErrorCategory.SYSTEM, severity: ErrorSeverity = ErrorSeverity.ERROR):
    """
    Decorator for tracking errors in functions
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Capture error with function context
                sentry_config.capture_error(
                    error=e,
                    level=severity,
                    category=category,
                    tags={
                        "function": func.__name__,
                        "module": func.__module__,
                        "decorator": "track_errors"
                    },
                    extra_data={
                        "function_args_count": len(args),
                        "function_kwargs_count": len(kwargs),
                        "function_name": func.__name__
                    }
                )
                raise
        return wrapper
    return decorator


def monitor_performance(operation_name: str, threshold_seconds: float = 1.0):
    """
    Decorator for monitoring function performance
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time

                # Record performance metrics
                sentry_config.metrics_aggregator.timing(
                    f"function.{operation_name}.duration",
                    duration,
                    tags={"function": func.__name__, "module": func.__module__}
                )

                # Alert on slow operations
                if duration > threshold_seconds:
                    sentry_config.capture_message(
                        f"Slow operation detected: {operation_name} took {duration:.2f}s",
                        level=ErrorSeverity.WARNING,
                        category=ErrorCategory.PERFORMANCE,
                        tags={
                            "operation": operation_name,
                            "duration_category": "slow"
                        },
                        extra_data={
                            "duration": duration,
                            "threshold": threshold_seconds
                        }
                    )

                return result
            except Exception as e:
                duration = time.time() - start_time
                sentry_config.capture_error(
                    error=e,
                    level=ErrorSeverity.ERROR,
                    category=ErrorCategory.PERFORMANCE,
                    tags={"operation": operation_name},
                    extra_data={
                        "duration": duration,
                        "failed": True
                    }
                )
                raise
        return wrapper
    return decorator


def add_breadcrumb(message: str, category: str = "default", level: ErrorSeverity = ErrorSeverity.INFO, data: Optional[Dict] = None):
    """
    Add breadcrumb for manual tracking
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            sentry_config.add_breadcrumb(
                message=message,
                category=category,
                level=level,
                data=data or {}
            )
            return func(*args, **kwargs)
        return wrapper
    return decorator