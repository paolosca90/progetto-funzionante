"""
Structured Logging Formatter
Provides advanced structured logging with correlation IDs, tracing, and context awareness.
"""

import json
import logging
import time
import uuid
import threading
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import traceback
import sys

from .logging_config import get_logging_config


class LogContext:
    """Thread-local context for logging"""

    def __init__(self):
        self._local = threading.local()

    def get_correlation_id(self) -> Optional[str]:
        """Get current correlation ID"""
        return getattr(self._local, 'correlation_id', None)

    def set_correlation_id(self, correlation_id: str) -> None:
        """Set correlation ID"""
        self._local.correlation_id = correlation_id

    def get_user_id(self) -> Optional[str]:
        """Get current user ID"""
        return getattr(self._local, 'user_id', None)

    def set_user_id(self, user_id: str) -> None:
        """Set user ID"""
        self._local.user_id = user_id

    def get_request_id(self) -> Optional[str]:
        """Get current request ID"""
        return getattr(self._local, 'request_id', None)

    def set_request_id(self, request_id: str) -> None:
        """Set request ID"""
        self._local.request_id = request_id

    def get_session_id(self) -> Optional[str]:
        """Get current session ID"""
        return getattr(self._local, 'session_id', None)

    def set_session_id(self, session_id: str) -> None:
        """Set session ID"""
        self._local.session_id = session_id

    def get_trace_id(self) -> Optional[str]:
        """Get current trace ID"""
        return getattr(self._local, 'trace_id', None)

    def set_trace_id(self, trace_id: str) -> None:
        """Set trace ID"""
        self._local.trace_id = trace_id

    def get_span_id(self) -> Optional[str]:
        """Get current span ID"""
        return getattr(self._local, 'span_id', None)

    def set_span_id(self, span_id: str) -> None:
        """Set span ID"""
        self._local.span_id = span_id

    def get_extra_fields(self) -> Dict[str, Any]:
        """Get extra fields"""
        return getattr(self._local, 'extra_fields', {})

    def add_extra_field(self, key: str, value: Any) -> None:
        """Add extra field"""
        if not hasattr(self._local, 'extra_fields'):
            self._local.extra_fields = {}
        self._local.extra_fields[key] = value

    def clear(self) -> None:
        """Clear all context"""
        if hasattr(self._local, '__dict__'):
            self._local.__dict__.clear()

    def get_context_dict(self) -> Dict[str, Any]:
        """Get all context as dictionary"""
        context = {}

        for attr in ['correlation_id', 'user_id', 'request_id', 'session_id',
                    'trace_id', 'span_id']:
            value = getattr(self._local, attr, None)
            if value:
                context[attr] = value

        extra_fields = getattr(self._local, 'extra_fields', {})
        if extra_fields:
            context.update(extra_fields)

        return context


# Global context instance
log_context = LogContext()


@dataclass
class LogEntry:
    """Structured log entry"""
    timestamp: datetime
    level: str
    logger_name: str
    message: str
    module: str
    function: str
    line: int
    thread_id: int
    process_id: int
    correlation_id: Optional[str] = None
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    session_id: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    extra_fields: Dict[str, Any] = None
    exception: Optional[str] = None
    stack_trace: Optional[str] = None
    performance_metrics: Dict[str, Any] = None

    def __post_init__(self):
        if self.extra_fields is None:
            self.extra_fields = {}
        if self.performance_metrics is None:
            self.performance_metrics = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'level': self.level,
            'logger_name': self.logger_name,
            'message': self.message,
            'module': self.module,
            'function': self.function,
            'line': self.line,
            'thread_id': self.thread_id,
            'process_id': self.process_id,
            'correlation_id': self.correlation_id,
            'user_id': self.user_id,
            'request_id': self.request_id,
            'session_id': self.session_id,
            'trace_id': self.trace_id,
            'span_id': self.span_id,
            'extra_fields': self.extra_fields,
            'exception': self.exception,
            'stack_trace': self.stack_trace,
            'performance_metrics': self.performance_metrics
        }


class StructuredFormatter(logging.Formatter):
    """Advanced structured logging formatter"""

    def __init__(self, include_caller_info: bool = True, include_context: bool = True):
        super().__init__()
        self.include_caller_info = include_caller_info
        self.include_context = include_context
        self.config = get_logging_config()

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON"""
        # Get context information
        context_dict = log_context.get_context_dict() if self.include_context else {}

        # Create structured log entry
        log_entry = LogEntry(
            timestamp=datetime.fromtimestamp(record.created),
            level=record.levelname,
            logger_name=record.name,
            message=record.getMessage(),
            module=record.module,
            function=record.funcName,
            line=record.lineno,
            thread_id=record.thread,
            process_id=record.process,
            correlation_id=context_dict.get('correlation_id'),
            user_id=context_dict.get('user_id'),
            request_id=context_dict.get('request_id'),
            session_id=context_dict.get('session_id'),
            trace_id=context_dict.get('trace_id'),
            span_id=context_dict.get('span_id'),
            extra_fields=self._extract_extra_fields(record),
            exception=self._format_exception(record),
            stack_trace=self._format_stack_trace(record),
            performance_metrics=self._extract_performance_metrics(record)
        )

        # Apply data masking for compliance
        if self.config.compliance.enabled:
            log_entry.message = self._mask_sensitive_data(log_entry.message)
            log_entry.extra_fields = self._mask_sensitive_dict(log_entry.extra_fields)

        # Convert to JSON
        try:
            return json.dumps(log_entry.to_dict(), default=str, ensure_ascii=False)
        except (TypeError, ValueError) as e:
            # Fallback to simple format if JSON serialization fails
            return json.dumps({
                'timestamp': log_entry.timestamp.isoformat(),
                'level': log_entry.level,
                'message': f"Failed to serialize log entry: {str(e)}",
                'original_message': log_entry.message
            })

    def _extract_extra_fields(self, record: logging.LogRecord) -> Dict[str, Any]:
        """Extract extra fields from log record"""
        extra_fields = {}

        # Extract standard extra fields
        for key, value in record.__dict__.items():
            if key not in {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
                'module', 'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                'thread', 'threadName', 'processName', 'process', 'getMessage',
                'exc_info', 'exc_text', 'stack_info', 'message'
            }:
                extra_fields[key] = value

        return extra_fields

    def _format_exception(self, record: logging.LogRecord) -> Optional[str]:
        """Format exception information"""
        if record.exc_info:
            exc_type, exc_value, _ = record.exc_info
            return f"{exc_type.__name__}: {str(exc_value)}"
        return None

    def _format_stack_trace(self, record: logging.LogRecord) -> Optional[str]:
        """Format stack trace"""
        if record.exc_info:
            return traceback.format_exc()
        elif record.stack_info:
            return record.stack_info
        return None

    def _extract_performance_metrics(self, record: logging.LogRecord) -> Dict[str, Any]:
        """Extract performance metrics from record"""
        metrics = {}

        # Add timing information if available
        if hasattr(record, 'duration'):
            metrics['duration_ms'] = record.duration * 1000

        if hasattr(record, 'start_time'):
            metrics['start_time'] = record.start_time

        if hasattr(record, 'end_time'):
            metrics['end_time'] = record.end_time

        # Add memory usage if available
        if hasattr(record, 'memory_usage'):
            metrics['memory_usage_mb'] = record.memory_usage

        if hasattr(record, 'cpu_usage'):
            metrics['cpu_usage_percent'] = record.cpu_usage

        return metrics

    def _mask_sensitive_data(self, data: str) -> str:
        """Mask sensitive data in log message"""
        if not data:
            return data

        masked_data = data
        for pattern in self.config.compliance.mask_patterns:
            import re
            masked_data = re.sub(pattern, lambda m: f"{m.group(0).split('=')[0]}=***", masked_data)

        return masked_data

    def _mask_sensitive_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Mask sensitive data in dictionary"""
        if not data:
            return data

        masked_dict = {}
        sensitive_keys = {'password', 'token', 'secret', 'key', 'auth', 'credential'}

        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                masked_dict[key] = "***"
            elif isinstance(value, dict):
                masked_dict[key] = self._mask_sensitive_dict(value)
            elif isinstance(value, str):
                masked_dict[key] = self._mask_sensitive_data(value)
            else:
                masked_dict[key] = value

        return masked_dict


class ContextLogger:
    """Logger with context awareness"""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.context = log_context

    def _log(self, level: int, message: str, **kwargs):
        """Log with context"""
        # Add context to extra fields
        extra = kwargs.get('extra', {})
        context_dict = self.context.get_context_dict()
        extra.update(context_dict)
        kwargs['extra'] = extra

        self.logger.log(level, message, **kwargs)

    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message"""
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log error message"""
        self._log(logging.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self._log(logging.CRITICAL, message, **kwargs)

    def exception(self, message: str, **kwargs):
        """Log exception with stack trace"""
        kwargs['exc_info'] = True
        self._log(logging.ERROR, message, **kwargs)

    # Context management
    def with_correlation_id(self, correlation_id: str):
        """Set correlation ID context"""
        self.context.set_correlation_id(correlation_id)
        return self

    def with_user_id(self, user_id: str):
        """Set user ID context"""
        self.context.set_user_id(user_id)
        return self

    def with_request_id(self, request_id: str):
        """Set request ID context"""
        self.context.set_request_id(request_id)
        return self

    def with_session_id(self, session_id: str):
        """Set session ID context"""
        self.context.set_session_id(session_id)
        return self

    def with_trace_id(self, trace_id: str):
        """Set trace ID context"""
        self.context.set_trace_id(trace_id)
        return self

    def with_span_id(self, span_id: str):
        """Set span ID context"""
        self.context.set_span_id(span_id)
        return self

    def with_extra(self, **kwargs):
        """Add extra fields"""
        for key, value in kwargs.items():
            self.context.add_extra_field(key, value)
        return self


def get_logger(name: str) -> ContextLogger:
    """Get context-aware logger"""
    return ContextLogger(name)


def generate_correlation_id() -> str:
    """Generate a new correlation ID"""
    return str(uuid.uuid4())


def generate_request_id() -> str:
    """Generate a new request ID"""
    return str(uuid.uuid4())


def generate_trace_id() -> str:
    """Generate a new trace ID"""
    return str(uuid.uuid4())


def generate_span_id() -> str:
    """Generate a new span ID"""
    return str(uuid.uuid4())[:8]


class LogContextManager:
    """Context manager for log context"""

    def __init__(self, **context):
        self.context = context
        self.previous_context = {}

    def __enter__(self):
        """Save current context and set new context"""
        # Save current context
        self.previous_context = log_context.get_context_dict()

        # Set new context
        if 'correlation_id' in self.context:
            log_context.set_correlation_id(self.context['correlation_id'])
        if 'user_id' in self.context:
            log_context.set_user_id(self.context['user_id'])
        if 'request_id' in self.context:
            log_context.set_request_id(self.context['request_id'])
        if 'session_id' in self.context:
            log_context.set_session_id(self.context['session_id'])
        if 'trace_id' in self.context:
            log_context.set_trace_id(self.context['trace_id'])
        if 'span_id' in self.context:
            log_context.set_span_id(self.context['span_id'])

        # Add extra fields
        for key, value in self.context.items():
            if key not in ['correlation_id', 'user_id', 'request_id', 'session_id', 'trace_id', 'span_id']:
                log_context.add_extra_field(key, value)

        return log_context

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Restore previous context"""
        log_context.clear()

        # Restore previous context
        for key, value in self.previous_context.items():
            log_context.add_extra_field(key, value)


def log_context(**context):
    """Decorator to add log context to function"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with LogContextManager(**context):
                return func(*args, **kwargs)
        return wrapper
    return decorator


def performance_logged(operation_name: str = None):
    """Decorator to log function performance"""
    def decorator(func):
        name = operation_name or f"{func.__module__}.{func.__name__}"

        def wrapper(*args, **kwargs):
            start_time = time.time()
            start_memory = get_memory_usage()

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                end_memory = get_memory_usage()

                # Log performance metrics
                logger = get_logger(func.__module__)
                logger.info(
                    f"Operation completed: {name}",
                    extra={
                        'operation': name,
                        'duration': duration,
                        'start_memory_mb': start_memory,
                        'end_memory_mb': end_memory,
                        'memory_delta_mb': end_memory - start_memory,
                        'success': True
                    }
                )

                return result

            except Exception as e:
                duration = time.time() - start_time
                end_memory = get_memory_usage()

                # Log error with performance metrics
                logger = get_logger(func.__module__)
                logger.error(
                    f"Operation failed: {name}",
                    extra={
                        'operation': name,
                        'duration': duration,
                        'start_memory_mb': start_memory,
                        'end_memory_mb': end_memory,
                        'memory_delta_mb': end_memory - start_memory,
                        'success': False,
                        'error': str(e)
                    },
                    exc_info=True
                )

                raise

        return wrapper
    return decorator


def get_memory_usage() -> float:
    """Get current memory usage in MB"""
    try:
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024  # Convert to MB
    except ImportError:
        return 0.0


def get_cpu_usage() -> float:
    """Get current CPU usage percentage"""
    try:
        import psutil
        return psutil.cpu_percent(interval=0.1)
    except ImportError:
        return 0.0