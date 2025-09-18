"""
Enhanced Logging Service with Dependency Injection Support

This service provides comprehensive logging capabilities with:
- Structured logging with correlation IDs
- Log levels and filtering
- Performance monitoring
- Error tracking and alerting
- Log aggregation support
- Context-aware logging
"""

import logging
import logging.handlers
import json
import time
import uuid
import threading
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
from functools import wraps
from contextlib import contextmanager
import traceback
import sys

from ..core.config import Settings as CoreSettings
from ..core.dependency_injection import ServiceLifetime, inject

# Set up logger for this module
logger = logging.getLogger(__name__)


class LogLevel(Enum):
    """Log level enumeration"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogContext:
    """Log context for correlation and tracking"""
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    operation: Optional[str] = None
    service: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class LogEntry:
    """Structured log entry"""
    timestamp: datetime
    level: LogLevel
    message: str
    logger_name: str
    context: LogContext
    extra: Dict[str, Any] = None
    exception: Optional[str] = None
    stack_trace: Optional[str] = None

    def __post_init__(self):
        if self.extra is None:
            self.extra = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert log entry to dictionary for JSON serialization"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'level': self.level.value,
            'message': self.message,
            'logger_name': self.logger_name,
            'context': asdict(self.context),
            'extra': self.extra,
            'exception': self.exception,
            'stack_trace': self.stack_trace
        }


class LogFormatter(logging.Formatter):
    """Custom log formatter for structured logging"""

    def __init__(self, include_context: bool = True):
        self.include_context = include_context
        super().__init__()

    def format(self, record: logging.LogRecord) -> str:
        """Format log record"""
        log_entry = LogEntry(
            timestamp=datetime.fromtimestamp(record.created),
            level=LogLevel(record.levelname),
            message=record.getMessage(),
            logger_name=record.name,
            context=getattr(record, 'context', LogContext()),
            extra=getattr(record, 'extra', {}),
            exception=record.exc_text,
            stack_trace=self._format_stack_trace(record)
        )

        return json.dumps(log_entry.to_dict(), default=str)

    def _format_stack_trace(self, record: logging.LogRecord) -> Optional[str]:
        """Format stack trace"""
        if record.exc_info:
            exc_type, exc_value, exc_traceback = record.exc_info
            return ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        return None


class LogHandler:
    """Base class for log handlers"""

    def __init__(self, level: LogLevel = LogLevel.INFO):
        self.level = level

    def handle(self, log_entry: LogEntry) -> None:
        """Handle log entry"""
        if self._should_handle(log_entry):
            self._do_handle(log_entry)

    def _should_handle(self, log_entry: LogEntry) -> bool:
        """Check if log entry should be handled"""
        level_order = {
            LogLevel.DEBUG: 0,
            LogLevel.INFO: 1,
            LogLevel.WARNING: 2,
            LogLevel.ERROR: 3,
            LogLevel.CRITICAL: 4
        }
        return level_order[log_entry.level] >= level_order[self.level]

    def _do_handle(self, log_entry: LogEntry) -> None:
        """Actually handle the log entry"""
        raise NotImplementedError


class ConsoleLogHandler(LogHandler):
    """Console log handler"""

    def __init__(self, level: LogLevel = LogLevel.INFO):
        super().__init__(level)
        self.logger = logging.getLogger('console')

    def _do_handle(self, log_entry: LogEntry) -> None:
        """Handle log entry to console"""
        log_dict = log_entry.to_dict()
        print(f"[{log_entry.timestamp}] {log_entry.level.value}: {log_entry.message}")
        if log_entry.extra:
            print(f"  Extra: {json.dumps(log_entry.extra, indent=2)}")


class FileLogHandler(LogHandler):
    """File log handler"""

    def __init__(self, file_path: str, level: LogLevel = LogLevel.INFO, max_bytes: int = 10485760, backup_count: int = 5):
        super().__init__(level)
        self.file_path = file_path
        self.handler = logging.handlers.RotatingFileHandler(
            file_path, maxBytes=max_bytes, backupCount=backup_count
        )
        self.handler.setFormatter(LogFormatter())

    def _do_handle(self, log_entry: LogEntry) -> None:
        """Handle log entry to file"""
        log_record = logging.LogRecord(
            name=log_entry.logger_name,
            level=getattr(logging, log_entry.level.value),
            pathname="",
            lineno=0,
            msg=log_entry.message,
            args=(),
            exc_info=None
        )
        log_record.context = log_entry.context
        log_record.extra = log_entry.extra
        self.handler.handle(log_record)


class MemoryLogHandler(LogHandler):
    """Memory log handler for testing and debugging"""

    def __init__(self, level: LogLevel = LogLevel.INFO, max_entries: int = 1000):
        super().__init__(level)
        self.entries: List[LogEntry] = []
        self.max_entries = max_entries

    def _do_handle(self, log_entry: LogEntry) -> None:
        """Handle log entry in memory"""
        self.entries.append(log_entry)
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries:]

    def get_entries(self, level: Optional[LogLevel] = None, limit: Optional[int] = None) -> List[LogEntry]:
        """Get log entries with optional filtering"""
        entries = self.entries
        if level:
            entries = [e for e in entries if e.level == level]
        if limit:
            entries = entries[-limit:]
        return entries

    def clear(self) -> None:
        """Clear all log entries"""
        self.entries.clear()


class LoggingService:
    """Enhanced logging service with dependency injection support"""

    def __init__(self, settings: CoreSettings):
        self.settings = settings
        self.handlers: List[LogHandler] = []
        self.context_stack: List[LogContext] = []
        self._lock = threading.RLock()
        self._performance_callbacks: List[Callable] = []
        self._error_callbacks: List[Callable] = []

        # Initialize logging
        self._initialize_logging()

    def _initialize_logging(self) -> None:
        """Initialize logging system"""
        # Set up root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.settings.LOG_LEVEL, 'INFO'))

        # Add default handlers
        self._add_default_handlers()

        # Set up performance monitoring
        self._setup_performance_monitoring()

        logger.info("Logging service initialized successfully")

    def _add_default_handlers(self) -> None:
        """Add default log handlers"""
        # Console handler
        console_handler = ConsoleLogHandler(LogLevel.INFO)
        self.add_handler(console_handler)

        # File handler
        if hasattr(self.settings, 'LOG_FILE') and self.settings.LOG_FILE:
            file_handler = FileLogHandler(self.settings.LOG_FILE, LogLevel.INFO)
            self.add_handler(file_handler)

        # Memory handler for debugging
        if self.settings.is_development:
            memory_handler = MemoryLogHandler(LogLevel.DEBUG, max_entries=500)
            self.add_handler(memory_handler)

    def _setup_performance_monitoring(self) -> None:
        """Set up performance monitoring for logging"""
        self._log_metrics = {
            'total_logs': 0,
            'logs_by_level': {},
            'logs_by_logger': {},
            'start_time': time.time()
        }

    def add_handler(self, handler: LogHandler) -> None:
        """Add a log handler"""
        with self._lock:
            self.handlers.append(handler)
            logger.info(f"Added log handler: {handler.__class__.__name__}")

    def remove_handler(self, handler: LogHandler) -> None:
        """Remove a log handler"""
        with self._lock:
            if handler in self.handlers:
                self.handlers.remove(handler)
                logger.info(f"Removed log handler: {handler.__class__.__name__}")

    def log(self, level: LogLevel, message: str, logger_name: str = __name__,
            context: Optional[LogContext] = None, extra: Optional[Dict[str, Any]] = None,
            exception: Optional[Exception] = None) -> None:
        """Log a message with the specified level"""
        with self._lock:
            # Create log entry
            log_entry = LogEntry(
                timestamp=datetime.now(),
                level=level,
                message=message,
                logger_name=logger_name,
                context=context or self._get_current_context(),
                extra=extra or {},
                exception=str(exception) if exception else None,
                stack_trace=traceback.format_exc() if exception else None
            )

            # Update metrics
            self._update_metrics(log_entry)

            # Handle the log entry
            for handler in self.handlers:
                handler.handle(log_entry)

            # Special handling for errors
            if level in [LogLevel.ERROR, LogLevel.CRITICAL]:
                self._handle_error_log(log_entry)

    def _get_current_context(self) -> LogContext:
        """Get current log context"""
        if self.context_stack:
            return self.context_stack[-1]
        return LogContext()

    def _update_metrics(self, log_entry: LogEntry) -> None:
        """Update logging metrics"""
        self._log_metrics['total_logs'] += 1

        # Count by level
        level_key = log_entry.level.value
        self._log_metrics['logs_by_level'][level_key] = self._log_metrics['logs_by_level'].get(level_key, 0) + 1

        # Count by logger
        logger_key = log_entry.logger_name
        self._log_metrics['logs_by_logger'][logger_key] = self._log_metrics['logs_by_logger'].get(logger_key, 0) + 1

    def _handle_error_log(self, log_entry: LogEntry) -> None:
        """Handle error logs with special processing"""
        for callback in self._error_callbacks:
            try:
                callback(log_entry)
            except Exception as e:
                logger.error(f"Error in error callback: {e}")

    def log_debug(self, message: str, logger_name: str = __name__, **kwargs) -> None:
        """Log debug message"""
        self.log(LogLevel.DEBUG, message, logger_name, **kwargs)

    def log_info(self, message: str, logger_name: str = __name__, **kwargs) -> None:
        """Log info message"""
        self.log(LogLevel.INFO, message, logger_name, **kwargs)

    def log_warning(self, message: str, logger_name: str = __name__, **kwargs) -> None:
        """Log warning message"""
        self.log(LogLevel.WARNING, message, logger_name, **kwargs)

    def log_error(self, message: str, logger_name: str = __name__, **kwargs) -> None:
        """Log error message"""
        self.log(LogLevel.ERROR, message, logger_name, **kwargs)

    def log_critical(self, message: str, logger_name: str = __name__, **kwargs) -> None:
        """Log critical message"""
        self.log(LogLevel.CRITICAL, message, logger_name, **kwargs)

    @contextmanager
    def context(self, context: LogContext) -> 'LoggingService':
        """Context manager for log context"""
        self.context_stack.append(context)
        try:
            yield self
        finally:
            self.context_stack.pop()

    @contextmanager
    def operation(self, operation_name: str, **metadata) -> 'LoggingService':
        """Context manager for operation logging"""
        context = LogContext(
            operation=operation_name,
            metadata=metadata,
            request_id=str(uuid.uuid4())
        )
        self.log_info(f"Starting operation: {operation_name}", extra=metadata)
        start_time = time.time()

        try:
            with self.context(context):
                yield self
        except Exception as e:
            self.log_error(f"Operation failed: {operation_name}", exception=e)
            raise
        finally:
            duration = time.time() - start_time
            self.log_info(f"Completed operation: {operation_name}", extra={'duration': duration})

    def add_performance_callback(self, callback: Callable[[LogEntry], None]) -> None:
        """Add performance monitoring callback"""
        self._performance_callbacks.append(callback)

    def add_error_callback(self, callback: Callable[[LogEntry], None]) -> None:
        """Add error monitoring callback"""
        self._error_callbacks.append(callback)

    def get_metrics(self) -> Dict[str, Any]:
        """Get logging metrics"""
        uptime = time.time() - self._log_metrics['start_time']
        logs_per_second = self._log_metrics['total_logs'] / uptime if uptime > 0 else 0

        return {
            'total_logs': self._log_metrics['total_logs'],
            'logs_by_level': self._log_metrics['logs_by_level'],
            'logs_by_logger': self._log_metrics['logs_by_logger'],
            'uptime_seconds': uptime,
            'logs_per_second': logs_per_second,
            'active_handlers': len(self.handlers),
            'context_stack_size': len(self.context_stack)
        }

    def get_recent_logs(self, limit: int = 100, level: Optional[LogLevel] = None) -> List[LogEntry]:
        """Get recent logs from memory handlers"""
        for handler in self.handlers:
            if isinstance(handler, MemoryLogHandler):
                return handler.get_entries(level=level, limit=limit)
        return []

    def clear_memory_logs(self) -> None:
        """Clear memory log entries"""
        for handler in self.handlers:
            if isinstance(handler, MemoryLogHandler):
                handler.clear()

    def set_level(self, level: LogLevel) -> None:
        """Set minimum log level"""
        for handler in self.handlers:
            handler.level = level

    def filter_logs(self, filter_func: Callable[[LogEntry], bool]) -> List[LogEntry]:
        """Filter logs based on custom function"""
        filtered_logs = []
        for handler in self.handlers:
            if isinstance(handler, MemoryLogHandler):
                filtered_logs.extend([entry for entry in handler.entries if filter_func(entry)])
        return filtered_logs

    def create_correlation_id(self) -> str:
        """Create a new correlation ID"""
        return str(uuid.uuid4())

    def get_correlation_id(self) -> Optional[str]:
        """Get current correlation ID"""
        current_context = self._get_current_context()
        return current_context.request_id

    def set_correlation_id(self, correlation_id: str) -> None:
        """Set current correlation ID"""
        if self.context_stack:
            self.context_stack[-1].request_id = correlation_id
        else:
            # Create new context with correlation ID
            context = LogContext(request_id=correlation_id)
            self.context_stack.append(context)

    def log_performance(self, operation: str, duration: float, **metadata) -> None:
        """Log performance metrics"""
        self.log_info(
            f"Performance: {operation}",
            extra={
                'operation': operation,
                'duration': duration,
                'type': 'performance',
                **metadata
            }
        )

        # Notify performance callbacks
        for callback in self._performance_callbacks:
            try:
                callback(operation, duration, metadata)
            except Exception as e:
                logger.error(f"Error in performance callback: {e}")


# Decorators for logging
def log_operation(operation_name: str, log_level: LogLevel = LogLevel.INFO):
    """Decorator to log function calls"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.log_info(
                    f"Operation {operation_name} completed successfully",
                    extra={
                        'operation': operation_name,
                        'duration': duration,
                        'success': True
                    }
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.log_error(
                    f"Operation {operation_name} failed",
                    extra={
                        'operation': operation_name,
                        'duration': duration,
                        'success': False
                    },
                    exception=e
                )
                raise
        return wrapper
    return decorator


def log_performance(operation_name: str = None):
    """Decorator to log function performance"""
    def decorator(func):
        name = operation_name or func.__name__
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.log_performance(name, duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.log_error(f"Performance monitoring failed for {name}", exception=e)
                raise
        return wrapper
    return decorator


def with_logging(context: Optional[LogContext] = None):
    """Decorator to add logging context to function"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if context:
                with logger.context(context):
                    return func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        return wrapper
    return decorator


# Global logger instance (will be injected)
logger: LoggingService = None


def set_logging_service(logging_service: LoggingService) -> None:
    """Set the global logging service instance"""
    global logger
    logger = logging_service


def get_logging_service() -> LoggingService:
    """Get the global logging service instance"""
    return logger