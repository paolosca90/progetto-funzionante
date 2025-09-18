"""
Comprehensive Error Handling System for Enhanced OpenAPI Documentation

This module provides structured error handling with:
- Detailed error response models
- HTTP status code management
- Error categorization and logging
- User-friendly error messages
- Debugging information
- Rate limiting awareness
- Security-focused error responses
"""

from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import logging
import traceback
import uuid
from enum import Enum

logger = logging.getLogger(__name__)

class ErrorCategory(str, Enum):
    """Error categories for better error organization"""
    VALIDATION = "ValidationError"
    AUTHENTICATION = "AuthenticationError"
    AUTHORIZATION = "AuthorizationError"
    NOT_FOUND = "NotFoundError"
    RATE_LIMIT = "RateLimitError"
    BUSINESS_LOGIC = "BusinessLogicError"
    EXTERNAL_SERVICE = "ExternalServiceError"
    DATABASE = "DatabaseError"
    NETWORK = "NetworkError"
    CONFIGURATION = "ConfigurationError"
    SECURITY = "SecurityError"
    INTERNAL = "InternalError"

class ErrorSeverity(str, Enum):
    """Error severity levels for prioritization"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorResponse:
    """Comprehensive error response structure"""

    @staticmethod
    def create_error_response(
        error_type: str,
        message: str,
        status_code: int,
        category: ErrorCategory = ErrorCategory.INTERNAL,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        details: Optional[Dict[str, Any]] = None,
        field_errors: Optional[List[Dict[str, str]]] = None,
        request_id: Optional[str] = None,
        help_url: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized error response

        Args:
            error_type: Type/class of error
            message: Human-readable error message
            status_code: HTTP status code
            category: Error category for organization
            severity: Error severity level
            details: Additional error details
            field_errors: Field-specific validation errors
            request_id: Unique request identifier
            help_url: URL to help documentation
            timestamp: Error timestamp

        Returns:
            Dict[str, Any]: Formatted error response
        """
        return {
            "error": error_type,
            "message": message,
            "status_code": status_code,
            "category": category.value,
            "severity": severity.value,
            "details": details or {},
            "field_errors": field_errors or [],
            "request_id": request_id or str(uuid.uuid4()),
            "timestamp": (timestamp or datetime.utcnow()).isoformat(),
            "help_url": help_url
        }

class ErrorHandler:
    """Centralized error handling for the application"""

    def __init__(self):
        self.error_mappings = {
            # Authentication errors
            401: {
                "category": ErrorCategory.AUTHENTICATION,
                "severity": ErrorSeverity.HIGH,
                "help_url": "https://docs.cash-revolution.com/errors/authentication"
            },
            # Authorization errors
            403: {
                "category": ErrorCategory.AUTHORIZATION,
                "severity": ErrorSeverity.HIGH,
                "help_url": "https://docs.cash-revolution.com/errors/authorization"
            },
            # Not found errors
            404: {
                "category": ErrorCategory.NOT_FOUND,
                "severity": ErrorSeverity.LOW,
                "help_url": "https://docs.cash-revolution.com/errors/not-found"
            },
            # Rate limit errors
            429: {
                "category": ErrorCategory.RATE_LIMIT,
                "severity": ErrorSeverity.MEDIUM,
                "help_url": "https://docs.cash-revolution.com/errors/rate-limit"
            },
            # Validation errors
            422: {
                "category": ErrorCategory.VALIDATION,
                "severity": ErrorSeverity.LOW,
                "help_url": "https://docs.cash-revolution.com/errors/validation"
            },
            # Server errors
            500: {
                "category": ErrorCategory.INTERNAL,
                "severity": ErrorSeverity.CRITICAL,
                "help_url": "https://docs.cash-revolution.com/errors/internal"
            },
            # Bad request errors
            400: {
                "category": ErrorCategory.VALIDATION,
                "severity": ErrorSeverity.LOW,
                "help_url": "https://docs.cash-revolution.com/errors/validation"
            }
        }

    def handle_http_exception(self, request: Request, exc: HTTPException) -> JSONResponse:
        """Handle HTTP exceptions with enhanced error information"""
        error_info = self.error_mappings.get(exc.status_code, {
            "category": ErrorCategory.INTERNAL,
            "severity": ErrorSeverity.MEDIUM,
            "help_url": "https://docs.cash-revolution.com/errors"
        })

        error_response = ErrorResponse.create_error_response(
            error_type=type(exc).__name__,
            message=exc.detail or "An error occurred",
            status_code=exc.status_code,
            category=error_info["category"],
            severity=error_info["severity"],
            details={"headers": dict(exc.headers)} if exc.headers else {},
            request_id=self._get_request_id(request),
            help_url=error_info["help_url"]
        )

        # Log the error
        self._log_error(request, exc, error_response)

        return JSONResponse(
            status_code=exc.status_code,
            content=error_response,
            headers=self._get_security_headers()
        )

    def handle_validation_error(self, request: Request, exc: RequestValidationError) -> JSONResponse:
        """Handle request validation errors with detailed field information"""
        field_errors = []
        for error in exc.errors():
            field_errors.append({
                "field": " -> ".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            })

        error_response = ErrorResponse.create_error_response(
            error_type="ValidationError",
            message="Request validation failed",
            status_code=422,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            details={
                "body": exc.body,
                "errors_count": len(field_errors)
            },
            field_errors=field_errors,
            request_id=self._get_request_id(request),
            help_url="https://docs.cash-revolution.com/errors/validation"
        )

        # Log validation errors
        self._log_error(request, exc, error_response)

        return JSONResponse(
            status_code=422,
            content=error_response,
            headers=self._get_security_headers()
        )

    def handle_general_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """Handle general exceptions with security-focused responses"""
        # Log the full exception for debugging
        logger.error(f"Unhandled exception: {exc}", exc_info=True)

        error_response = ErrorResponse.create_error_response(
            error_type="InternalError",
            message="An unexpected error occurred",
            status_code=500,
            category=ErrorCategory.INTERNAL,
            severity=ErrorSeverity.CRITICAL,
            details={
                "error_type": type(exc).__name__,
                "stack_trace": traceback.format_exc() if logger.isEnabledFor(logging.DEBUG) else None
            },
            request_id=self._get_request_id(request),
            help_url="https://docs.cash-revolution.com/errors/internal"
        )

        return JSONResponse(
            status_code=500,
            content=error_response,
            headers=self._get_security_headers()
        )

    def _get_request_id(self, request: Request) -> str:
        """Extract or generate request ID"""
        return getattr(request.state, 'request_id', str(uuid.uuid4()))

    def _log_error(self, request: Request, exc: Exception, error_response: Dict[str, Any]):
        """Log error with contextual information"""
        log_data = {
            "request_id": error_response["request_id"],
            "error_type": error_response["error"],
            "message": error_response["message"],
            "status_code": error_response["status_code"],
            "category": error_response["category"],
            "severity": error_response["severity"],
            "path": request.url.path,
            "method": request.method,
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown")
        }

        if error_response["severity"] == ErrorSeverity.CRITICAL:
            logger.critical(f"Critical error: {log_data}")
        elif error_response["severity"] == ErrorSeverity.HIGH:
            logger.error(f"High severity error: {log_data}")
        elif error_response["severity"] == ErrorSeverity.MEDIUM:
            logger.warning(f"Medium severity error: {log_data}")
        else:
            logger.info(f"Low severity error: {log_data}")

    def _get_security_headers(self) -> Dict[str, str]:
        """Get security headers for error responses"""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Content-Security-Policy": "default-src 'self'",
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }

class CustomExceptions:
    """Custom exception classes for specific error scenarios"""

    class AuthenticationError(Exception):
        """Base authentication error"""
        def __init__(self, message: str, details: Optional[Dict] = None):
            self.message = message
            self.details = details or {}
            super().__init__(self.message)

    class AuthorizationError(Exception):
        """Base authorization error"""
        def __init__(self, message: str, required_role: Optional[str] = None):
            self.message = message
            self.required_role = required_role
            super().__init__(self.message)

    class RateLimitError(Exception):
        """Rate limiting error"""
        def __init__(self, message: str, retry_after: Optional[int] = None):
            self.message = message
            self.retry_after = retry_after
            super().__init__(self.message)

    class ValidationError(Exception):
        """Validation error"""
        def __init__(self, message: str, field_errors: Optional[List[Dict]] = None):
            self.message = message
            self.field_errors = field_errors or []
            super().__init__(self.message)

    class BusinessLogicError(Exception):
        """Business logic error"""
        def __init__(self, message: str, error_code: Optional[str] = None):
            self.message = message
            self.error_code = error_code
            super().__init__(self.message)

    class ExternalServiceError(Exception):
        """External service error"""
        def __init__(self, message: str, service: str, status_code: Optional[int] = None):
            self.message = message
            self.service = service
            self.status_code = status_code
            super().__init__(self.message)

    class SecurityError(Exception):
        """Security-related error"""
        def __init__(self, message: str, security_event: Optional[str] = None):
            self.message = message
            self.security_event = security_event
            super().__init__(self.message)

# Global error handler instance
error_handler = ErrorHandler()

# HTTP Status Code Documentation
HTTP_STATUS_DOCUMENTATION = {
    400: {
        "title": "Bad Request",
        "description": "The request is malformed or contains invalid data",
        "category": "Client Error",
        "common_causes": [
            "Invalid JSON format",
            "Missing required fields",
            "Invalid field values",
            "Malformed request parameters"
        ],
        "resolution": "Review request format and validate all required fields",
        "retry": "Yes, after fixing the request"
    },
    401: {
        "title": "Unauthorized",
        "description": "Authentication is required or has failed",
        "category": "Authentication Error",
        "common_causes": [
            "Missing or invalid authentication token",
            "Expired token",
            "Invalid credentials",
            "Account locked"
        ],
        "resolution": "Provide valid authentication credentials",
        "retry": "Yes, with valid credentials"
    },
    403: {
        "title": "Forbidden",
        "description": "Authenticated user lacks sufficient permissions",
        "category": "Authorization Error",
        "common_causes": [
            "Insufficient subscription level",
            "Missing required role",
            "Resource access denied",
            "Account suspended"
        ],
        "resolution": "Upgrade subscription or contact administrator",
        "retry": "No, without permission changes"
    },
    404: {
        "title": "Not Found",
        "description": "Requested resource does not exist",
        "category": "Client Error",
        "common_causes": [
            "Invalid endpoint URL",
            "Resource ID does not exist",
            "Resource deleted",
            "Incorrect API version"
        ],
        "resolution": "Verify resource existence and URL",
        "retry": "No, resource does not exist"
    },
    422: {
        "title": "Unprocessable Entity",
        "description": "Request validation failed",
        "category": "Validation Error",
        "common_causes": [
            "Invalid data format",
            "Field validation failed",
            "Business rule violation",
            "Constraint violation"
        ],
        "resolution": "Review field-specific error messages",
        "retry": "Yes, after fixing validation issues"
    },
    429: {
        "title": "Too Many Requests",
        "description": "Rate limit exceeded",
        "category": "Rate Limit Error",
        "common_causes": [
            "Too many API requests",
            "Exceeded request quota",
            "Rate limiting triggered",
            "Service protection activated"
        ],
        "resolution": "Wait and retry later, or upgrade plan",
        "retry": "Yes, after rate limit reset"
    },
    500: {
        "title": "Internal Server Error",
        "description": "Unexpected server error occurred",
        "category": "Server Error",
        "common_causes": [
            "Database connection failed",
            "External service unavailable",
            "Configuration error",
            "System maintenance"
        ],
        "resolution": "Contact support with request ID",
        "retry": "Yes, after a short delay"
    },
    503: {
        "title": "Service Unavailable",
        "description": "Service temporarily unavailable",
        "category": "Server Error",
        "common_causes": [
            "Service maintenance",
            "External service outage",
            "Overloaded service",
            "Database maintenance"
        ],
        "resolution": "Wait and retry later",
        "retry": "Yes, after service restoration"
    }
}

# Error Response Examples for Documentation
ERROR_RESPONSE_EXAMPLES = {
    "validation_error": {
        "error": "ValidationError",
        "message": "Request validation failed",
        "status_code": 422,
        "category": "ValidationError",
        "severity": "low",
        "details": {
            "body": {"username": "ab", "email": "invalid-email"},
            "errors_count": 2
        },
        "field_errors": [
            {
                "field": "username",
                "message": "Username must be at least 3 characters long",
                "type": "value_error.any_str.min_length"
            },
            {
                "field": "email",
                "message": "Invalid email format",
                "type": "value_error.email"
            }
        ],
        "request_id": "req_123456789",
        "timestamp": "2024-01-15T10:30:00Z",
        "help_url": "https://docs.cash-revolution.com/errors/validation"
    },
    "authentication_error": {
        "error": "AuthenticationError",
        "message": "Invalid authentication credentials",
        "status_code": 401,
        "category": "AuthenticationError",
        "severity": "high",
        "details": {
            "auth_method": "JWT",
            "token_status": "invalid"
        },
        "request_id": "req_123456790",
        "timestamp": "2024-01-15T10:30:00Z",
        "help_url": "https://docs.cash-revolution.com/errors/authentication"
    },
    "rate_limit_error": {
        "error": "RateLimitError",
        "message": "API rate limit exceeded",
        "status_code": 429,
        "category": "RateLimitError",
        "severity": "medium",
        "details": {
            "limit": "100 requests per minute",
            "current_usage": 105,
            "reset_time": "2024-01-15T10:31:00Z"
        },
        "request_id": "req_123456791",
        "timestamp": "2024-01-15T10:30:00Z",
        "help_url": "https://docs.cash-revolution.com/errors/rate-limit"
    },
    "business_logic_error": {
        "error": "BusinessLogicError",
        "message": "Signal creation failed: market data unavailable",
        "status_code": 503,
        "category": "ExternalServiceError",
        "severity": "high",
        "details": {
            "service": "OANDA_API",
            "error_code": "MARKET_DATA_UNAVAILABLE",
            "retry_after": 30
        },
        "request_id": "req_123456792",
        "timestamp": "2024-01-15T10:30:00Z",
        "help_url": "https://docs.cash-revolution.com/errors/external-services"
    }
}