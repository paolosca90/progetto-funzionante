"""
Async Error Handling and Cancellation System
Implements comprehensive error handling, cancellation patterns,
and circuit breakers for async operations.
"""

import asyncio
import traceback
from typing import Dict, Any, Optional, Callable, Type, TypeVar, Union, List
from dataclasses import dataclass, field
from enum import Enum
from contextlib import asynccontextmanager
import logging
import time
from functools import wraps
import uuid

from app.services.async_logging_service import logging_service

logger = logging.getLogger(__name__)

T = TypeVar('T')

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"              # Non-critical, log and continue
    MEDIUM = "medium"        # May affect functionality, attempt recovery
    HIGH = "high"            # Critical, requires immediate attention
    CRITICAL = "critical"    # System failure, stop operation

class ErrorCategory(Enum):
    """Error categories for better handling"""
    NETWORK = "network"
    DATABASE = "database"
    EXTERNAL_API = "external_api"
    FILE_IO = "file_io"
    VALIDATION = "validation"
    BUSINESS_LOGIC = "business_logic"
    TIMEOUT = "timeout"
    CANCELLATION = "cancellation"
    UNKNOWN = "unknown"

class RetryStrategy(Enum):
    """Retry strategies for different error types"""
    NONE = "none"                    # Don't retry
    IMMEDIATE = "immediate"          # Retry immediately
    EXPONENTIAL_BACKOFF = "exponential"  # Exponential backoff
    LINEAR_BACKOFF = "linear"        # Linear backoff
    FIXED_DELAY = "fixed"           # Fixed delay between retries

@dataclass
class ErrorContext:
    """Context information for errors"""
    operation: str
    component: str
    timestamp: float = field(default_factory=time.time)
    error_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AsyncError:
    """Enhanced error information"""
    original_error: Exception
    severity: ErrorSeverity
    category: ErrorCategory
    context: ErrorContext
    should_retry: bool = False
    retry_strategy: RetryStrategy = RetryStrategy.NONE
    max_retries: int = 0
    custom_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for serialization"""
        return {
            "error_id": self.context.error_id,
            "operation": self.context.operation,
            "component": self.context.component,
            "severity": self.severity.value,
            "category": self.category.value,
            "message": self.custom_message or str(self.original_error),
            "should_retry": self.should_retry,
            "retry_strategy": self.retry_strategy.value,
            "max_retries": self.max_retries,
            "timestamp": self.context.timestamp,
            "user_id": self.context.user_id,
            "request_id": self.context.request_id,
            "metadata": self.context.metadata,
            "traceback": traceback.format_exc()
        }

class AsyncCircuitBreaker:
    """Circuit breaker for async operations"""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        expected_exception: Type[Exception] = Exception,
        timeout: Optional[float] = None
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.timeout = timeout

        self._failure_count = 0
        self._last_failure_time = 0
        self._state = "closed"  # closed, open, half_open
        self._lock = asyncio.Lock()

    async def __aenter__(self):
        await self._acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self._record_failure()
        else:
            await self._record_success()

    async def _acquire(self):
        async with self._lock:
            if self._state == "open":
                if time.time() - self._last_failure_time > self.recovery_timeout:
                    self._state = "half_open"
                    self._failure_count = 0
                else:
                    raise RuntimeError(f"Circuit breaker is open. Failures: {self._failure_count}")

    async def _record_failure(self):
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()

            if self._failure_count >= self.failure_threshold:
                self._state = "open"

    async def _record_success(self):
        async with self._lock:
            self._failure_count = 0
            self._state = "closed"

    def get_state(self) -> Dict[str, Any]:
        """Get circuit breaker state"""
        return {
            "state": self._state,
            "failure_count": self._failure_count,
            "last_failure_time": self._last_failure_time,
            "threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout
        }

class AsyncErrorHandler:
    """Centralized error handling for async operations"""

    def __init__(self):
        self.error_handlers: Dict[ErrorCategory, List[Callable]] = {}
        self.circuit_breakers: Dict[str, AsyncCircuitBreaker] = {}
        self.error_stats: Dict[str, Dict] = {}

    def register_handler(self, category: ErrorCategory, handler: Callable):
        """Register an error handler for a specific category"""
        if category not in self.error_handlers:
            self.error_handlers[category] = []
        self.error_handlers[category].append(handler)

    def get_circuit_breaker(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0
    ) -> AsyncCircuitBreaker:
        """Get or create a circuit breaker"""
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = AsyncCircuitBreaker(
                failure_threshold=failure_threshold,
                recovery_timeout=recovery_timeout
            )
        return self.circuit_breakers[name]

    async def handle_error(self, error: AsyncError) -> Dict[str, Any]:
        """Handle an error using registered handlers"""
        # Log the error
        await logging_service.log_error(
            operation=error.context.operation,
            component=error.context.component,
            error=error.original_error,
            severity=error.severity.value,
            context=error.context.metadata
        )

        # Update statistics
        self._update_error_stats(error)

        # Execute handlers
        if error.category in self.error_handlers:
            for handler in self.error_handlers[error.category]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(error)
                    else:
                        handler(error)
                except Exception as handler_error:
                    logger.error(f"Error handler failed: {handler_error}")

        return error.to_dict()

    def _update_error_stats(self, error: AsyncError):
        """Update error statistics"""
        key = f"{error.category.value}_{error.severity.value}"
        if key not in self.error_stats:
            self.error_stats[key] = {
                "count": 0,
                "last_occurrence": 0,
                "operations": set()
            }

        self.error_stats[key]["count"] += 1
        self.error_stats[key]["last_occurrence"] = time.time()
        self.error_stats[key]["operations"].add(error.context.operation)

    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics"""
        stats = {}
        for key, value in self.error_stats.items():
            stats[key] = {
                "count": value["count"],
                "last_occurrence": value["last_occurrence"],
                "unique_operations": len(value["operations"])
            }
        return stats

class AsyncRetryHandler:
    """Retry handler for async operations with various strategies"""

    def __init__(self):
        self.retry_configs: Dict[str, Dict] = {}

    def configure_retry(
        self,
        operation: str,
        strategy: RetryStrategy,
        max_retries: int,
        delay: float = 1.0,
        backoff_factor: float = 2.0,
        exceptions: List[Type[Exception]] = None
    ):
        """Configure retry settings for an operation"""
        self.retry_configs[operation] = {
            "strategy": strategy,
            "max_retries": max_retries,
            "delay": delay,
            "backoff_factor": backoff_factor,
            "exceptions": exceptions or [Exception]
        }

    async def execute_with_retry(
        self,
        operation: str,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute a function with retry logic"""
        if operation not in self.retry_configs:
            # Default behavior - no retry
            return await func(*args, **kwargs)

        config = self.retry_configs[operation]
        last_exception = None

        for attempt in range(config["max_retries"] + 1):
            try:
                return await func(*args, **kwargs)
            except tuple(config["exceptions"]) as e:
                last_exception = e

                if attempt == config["max_retries"]:
                    raise e

                # Calculate delay based on strategy
                delay = self._calculate_delay(config, attempt)

                logger.warning(
                    f"Operation {operation} failed (attempt {attempt + 1}), "
                    f"retrying in {delay}s: {str(e)}"
                )

                await asyncio.sleep(delay)

        raise last_exception

    def _calculate_delay(self, config: Dict, attempt: int) -> float:
        """Calculate delay based on retry strategy"""
        strategy = config["strategy"]
        base_delay = config["delay"]
        backoff_factor = config["backoff_factor"]

        if strategy == RetryStrategy.IMMEDIATE:
            return 0
        elif strategy == RetryStrategy.FIXED_DELAY:
            return base_delay
        elif strategy == RetryStrategy.LINEAR_BACKOFF:
            return base_delay * (attempt + 1)
        elif strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            return base_delay * (backoff_factor ** attempt)
        else:
            return base_delay

class AsyncCancellationManager:
    """Manage async operation cancellation"""

    def __init__(self):
        self.active_operations: Dict[str, asyncio.Task] = {}
        self.cancellation_tokens: Dict[str, asyncio.Event] = {}

    def create_cancellation_token(self, operation_id: str) -> asyncio.Event:
        """Create a cancellation token for an operation"""
        token = asyncio.Event()
        self.cancellation_tokens[operation_id] = token
        return token

    def cancel_operation(self, operation_id: str):
        """Cancel an operation"""
        if operation_id in self.cancellation_tokens:
            self.cancellation_tokens[operation_id].set()

        if operation_id in self.active_operations:
            self.active_operations[operation_id].cancel()

    async def wait_for_cancellation(self, operation_id: str, timeout: float = None):
        """Wait for cancellation or timeout"""
        if operation_id not in self.cancellation_tokens:
            return False

        try:
            await asyncio.wait_for(
                self.cancellation_tokens[operation_id].wait(),
                timeout=timeout
            )
            return True
        except asyncio.TimeoutError:
            return False

    def is_cancelled(self, operation_id: str) -> bool:
        """Check if an operation is cancelled"""
        if operation_id in self.cancellation_tokens:
            return self.cancellation_tokens[operation_id].is_set()
        return False

    def cleanup_operation(self, operation_id: str):
        """Clean up operation resources"""
        self.active_operations.pop(operation_id, None)
        self.cancellation_tokens.pop(operation_id, None)

# Global instances
error_handler = AsyncErrorHandler()
retry_handler = AsyncRetryHandler()
cancellation_manager = AsyncCancellationManager()

# Decorators
def async_error_handler(
    operation: str,
    component: str,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    category: ErrorCategory = ErrorCategory.UNKNOWN,
    should_retry: bool = False,
    retry_strategy: RetryStrategy = RetryStrategy.NONE,
    max_retries: int = 0
):
    """Decorator for async error handling"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            operation_id = str(uuid.uuid4())
            context = ErrorContext(
                operation=operation,
                component=component,
                metadata={"args": str(args), "kwargs": str(kwargs)}
            )

            try:
                # Add cancellation support
                cancellation_token = cancellation_manager.create_cancellation_token(operation_id)

                # Execute with retry if configured
                if should_retry:
                    result = await retry_handler.execute_with_retry(operation, func, *args, **kwargs)
                else:
                    result = await func(*args, **kwargs)

                return result

            except asyncio.CancelledError:
                error = AsyncError(
                    original_error=asyncio.CancelledError("Operation cancelled"),
                    severity=ErrorSeverity.LOW,
                    category=ErrorCategory.CANCELLATION,
                    context=ErrorContext(
                        operation=operation,
                        component=component
                    )
                )
                await error_handler.handle_error(error)
                raise

            except Exception as e:
                error = AsyncError(
                    original_error=e,
                    severity=severity,
                    category=category,
                    context=context,
                    should_retry=should_retry,
                    retry_strategy=retry_strategy,
                    max_retries=max_retries
                )

                error_info = await error_handler.handle_error(error)

                # Re-raise based on severity
                if severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
                    raise
                else:
                    return {"error": error_info}

            finally:
                cancellation_manager.cleanup_operation(operation_id)

        return wrapper
    return decorator

def async_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 30.0,
    expected_exception: Type[Exception] = Exception
):
    """Decorator for circuit breaker pattern"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            breaker = error_handler.get_circuit_breaker(
                name, failure_threshold, recovery_timeout
            )

            async with breaker:
                return await func(*args, **kwargs)

        return wrapper
    return decorator

def async_timeout(timeout: float):
    """Decorator for async operation timeout"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
            except asyncio.TimeoutError:
                raise TimeoutError(f"Operation timed out after {timeout} seconds")
        return wrapper
    return decorator

# Context managers
@asynccontextmanager
async def async_error_context(operation: str, component: str, **metadata):
    """Context manager for error handling"""
    context = ErrorContext(
        operation=operation,
        component=component,
        metadata=metadata
    )

    try:
        yield context
    except Exception as e:
        error = AsyncError(
            original_error=e,
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.UNKNOWN,
            context=context
        )
        await error_handler.handle_error(error)
        raise

@asynccontextmanager
async def async_circuit_breaker_context(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 30.0
):
    """Context manager for circuit breaker"""
    breaker = error_handler.get_circuit_breaker(
        name, failure_threshold, recovery_timeout
    )

    async with breaker:
        yield

# Utility functions
def classify_error(error: Exception) -> tuple[ErrorSeverity, ErrorCategory]:
    """Classify an error by severity and category"""
    error_type = type(error)
    error_str = str(error).lower()

    # Network errors
    if any(keyword in error_str for keyword in [
        "connection", "timeout", "network", "resolve", "refused"
    ]) or error_type in [
        ConnectionError, TimeoutError, OSError
    ]:
        return ErrorSeverity.HIGH, ErrorCategory.NETWORK

    # Database errors
    elif any(keyword in error_str for keyword in [
        "database", "sql", "query", "connection", "constraint"
    ]) or "database" in error_type.__name__.lower():
        return ErrorSeverity.HIGH, ErrorCategory.DATABASE

    # External API errors
    elif any(keyword in error_str for keyword in [
        "api", "http", "status", "response", "external"
    ]):
        return ErrorSeverity.MEDIUM, ErrorCategory.EXTERNAL_API

    # File I/O errors
    elif any(keyword in error_str for keyword in [
        "file", "directory", "permission", "not found"
    ]) or error_type in [FileNotFoundError, PermissionError]:
        return ErrorSeverity.MEDIUM, ErrorCategory.FILE_IO

    # Validation errors
    elif any(keyword in error_str for keyword in [
        "validation", "invalid", "required", "format"
    ]) or "validation" in error_type.__name__.lower():
        return ErrorSeverity.LOW, ErrorCategory.VALIDATION

    # Timeout errors
    elif "timeout" in error_str or error_type == TimeoutError:
        return ErrorSeverity.MEDIUM, ErrorCategory.TIMEOUT

    # Default classification
    else:
        return ErrorSeverity.MEDIUM, ErrorCategory.UNKNOWN

# Configuration functions
def configure_retry_defaults():
    """Configure default retry settings"""
    retry_handler.configure_retry(
        "database_query",
        RetryStrategy.EXPONENTIAL_BACKOFF,
        max_retries=3,
        delay=0.1,
        exceptions=[Exception]
    )

    retry_handler.configure_retry(
        "external_api_call",
        RetryStrategy.EXPONENTIAL_BACKOFF,
        max_retries=5,
        delay=1.0,
        exceptions=[ConnectionError, TimeoutError]
    )

    retry_handler.configure_retry(
        "file_operation",
        RetryStrategy.LINEAR_BACKOFF,
        max_retries=2,
        delay=0.5,
        exceptions=[FileNotFoundError, PermissionError]
    )

def register_default_error_handlers():
    """Register default error handlers"""
    async def network_error_handler(error: AsyncError):
        logger.warning(f"Network error in {error.context.operation}: {error.original_error}")

    async def database_error_handler(error: AsyncError):
        logger.error(f"Database error in {error.context.operation}: {error.original_error}")

    async def external_api_error_handler(error: AsyncError):
        logger.warning(f"External API error in {error.context.operation}: {error.original_error}")

    error_handler.register_handler(ErrorCategory.NETWORK, network_error_handler)
    error_handler.register_handler(ErrorCategory.DATABASE, database_error_handler)
    error_handler.register_handler(ErrorCategory.EXTERNAL_API, external_api_error_handler)

# Initialize
async def init_error_handling():
    """Initialize error handling system"""
    try:
        configure_retry_defaults()
        register_default_error_handlers()
        await logging_service.log_event("error_handling_initialized", {"status": "success"})
        return True
    except Exception as e:
        logger.error(f"Failed to initialize error handling: {e}")
        return False

async def cleanup_error_handling():
    """Cleanup error handling system"""
    try:
        # Cancel all active operations
        for operation_id in list(cancellation_manager.active_operations.keys()):
            cancellation_manager.cancel_operation(operation_id)

        await logging_service.log_event("error_handling_cleanup", {"status": "success"})
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

# Health check
async def get_error_handling_health() -> Dict[str, Any]:
    """Get error handling system health"""
    return {
        "active_operations": len(cancellation_manager.active_operations),
        "circuit_breakers": {
            name: breaker.get_state()
            for name, breaker in error_handler.circuit_breakers.items()
        },
        "error_stats": error_handler.get_error_stats(),
        "retry_configs": len(retry_handler.retry_configs)
    }