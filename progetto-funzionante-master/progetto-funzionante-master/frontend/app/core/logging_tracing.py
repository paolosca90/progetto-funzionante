"""
Advanced Log Correlation and Distributed Tracing System
Provides comprehensive request tracing, correlation IDs, and distributed tracing capabilities.
"""

import uuid
import time
import threading
import json
from typing import Dict, Any, Optional, List, Callable, ContextManager
from dataclasses import dataclass, field
from datetime import datetime
from contextlib import contextmanager
from enum import Enum
import logging

from .logging_config import get_logging_config, TracingConfig
from .logging_structured import log_context, get_logger


class TraceContext:
    """Thread-local context for distributed tracing"""

    def __init__(self):
        self._local = threading.local()

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

    def get_parent_span_id(self) -> Optional[str]:
        """Get parent span ID"""
        return getattr(self._local, 'parent_span_id', None)

    def set_parent_span_id(self, parent_span_id: str) -> None:
        """Set parent span ID"""
        self._local.parent_span_id = parent_span_id

    def get_span_stack(self) -> List[str]:
        """Get span stack"""
        return getattr(self._local, 'span_stack', [])

    def push_span(self, span_id: str) -> None:
        """Push span ID to stack"""
        if not hasattr(self._local, 'span_stack'):
            self._local.span_stack = []
        self._local.span_stack.append(span_id)

    def pop_span(self) -> Optional[str]:
        """Pop span ID from stack"""
        if hasattr(self._local, 'span_stack') and self._local.span_stack:
            return self._local.span_stack.pop()
        return None

    def get_span_context(self) -> Dict[str, Any]:
        """Get complete span context"""
        return {
            'trace_id': self.get_trace_id(),
            'span_id': self.get_span_id(),
            'parent_span_id': self.get_parent_span_id(),
            'span_stack': self.get_span_stack()
        }

    def clear(self) -> None:
        """Clear all tracing context"""
        if hasattr(self._local, '__dict__'):
            self._local.__dict__.clear()


# Global trace context instance
trace_context = TraceContext()


@dataclass
class Span:
    """Distributed tracing span"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    operation_name: str = ""
    start_time: float = 0.0
    end_time: Optional[float] = None
    duration: Optional[float] = None
    tags: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    status_code: int = 0
    status_message: str = "OK"
    span_type: str = "internal"
    component: str = "application"

    def __post_init__(self):
        if self.start_time == 0.0:
            self.start_time = time.time()

    def finish(self) -> None:
        """Finish the span"""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time

    def add_tag(self, key: str, value: Any) -> None:
        """Add a tag to the span"""
        self.tags[key] = value

    def add_tags(self, tags: Dict[str, Any]) -> None:
        """Add multiple tags to the span"""
        self.tags.update(tags)

    def log_event(self, event: str, payload: Dict[str, Any] = None, timestamp: float = None) -> None:
        """Log an event within the span"""
        if timestamp is None:
            timestamp = time.time()

        self.logs.append({
            'timestamp': timestamp,
            'event': event,
            'payload': payload or {}
        })

    def set_status(self, code: int, message: str = "OK") -> None:
        """Set span status"""
        self.status_code = code
        self.status_message = message

    def to_dict(self) -> Dict[str, Any]:
        """Convert span to dictionary"""
        return {
            'trace_id': self.trace_id,
            'span_id': self.span_id,
            'parent_span_id': self.parent_span_id,
            'operation_name': self.operation_name,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.duration,
            'tags': self.tags,
            'logs': self.logs,
            'status_code': self.status_code,
            'status_message': self.status_message,
            'span_type': self.span_type,
            'component': self.component
        }


@dataclass
class TraceContextHeaders:
    """Headers for trace context propagation"""
    TRACE_ID_HEADER = "X-Trace-ID"
    SPAN_ID_HEADER = "X-Span-ID"
    PARENT_SPAN_ID_HEADER = "X-Parent-Span-ID"
    CORRELATION_ID_HEADER = "X-Correlation-ID"
    BAGGAGE_HEADER = "X-Baggage"

    @classmethod
    def extract_from_headers(cls, headers: Dict[str, str]) -> Dict[str, str]:
        """Extract trace context from headers"""
        context = {}

        if cls.TRACE_ID_HEADER in headers:
            context['trace_id'] = headers[cls.TRACE_ID_HEADER]
        if cls.SPAN_ID_HEADER in headers:
            context['span_id'] = headers[cls.SPAN_ID_HEADER]
        if cls.PARENT_SPAN_ID_HEADER in headers:
            context['parent_span_id'] = headers[cls.PARENT_SPAN_ID_HEADER]
        if cls.CORRELATION_ID_HEADER in headers:
            context['correlation_id'] = headers[cls.CORRELATION_ID_HEADER]
        if cls.BAGGAGE_HEADER in headers:
            context['baggage'] = headers[cls.BAGGAGE_HEADER]

        return context

    @classmethod
    def inject_to_headers(cls, context: Dict[str, str]) -> Dict[str, str]:
        """Inject trace context into headers"""
        headers = {}

        if 'trace_id' in context:
            headers[cls.TRACE_ID_HEADER] = context['trace_id']
        if 'span_id' in context:
            headers[cls.SPAN_ID_HEADER] = context['span_id']
        if 'parent_span_id' in context:
            headers[cls.PARENT_SPAN_ID_HEADER] = context['parent_span_id']
        if 'correlation_id' in context:
            headers[cls.CORRELATION_ID_HEADER] = context['correlation_id']
        if 'baggage' in context:
            headers[cls.BAGGAGE_HEADER] = context['baggage']

        return headers


class DistributedTracer:
    """Distributed tracing manager"""

    def __init__(self, config: TracingConfig):
        self.config = config
        self.spans: Dict[str, Span] = {}
        self.active_spans: Dict[str, Span] = {}
        self._lock = threading.Lock()
        self._span_counter = 0
        self.logger = get_logger(__name__)

    def start_span(self, operation_name: str, parent_span_id: Optional[str] = None,
                   trace_id: Optional[str] = None, tags: Dict[str, Any] = None) -> Span:
        """Start a new span"""
        with self._lock:
            # Generate trace ID if not provided
            if not trace_id:
                trace_id = str(uuid.uuid4())

            # Generate span ID
            span_id = self._generate_span_id()

            # Create span
            span = Span(
                trace_id=trace_id,
                span_id=span_id,
                parent_span_id=parent_span_id,
                operation_name=operation_name,
                tags=tags or {}
            )

            # Store spans
            self.spans[span_id] = span
            self.active_spans[span_id] = span

            # Update trace context
            trace_context.set_trace_id(trace_id)
            trace_context.set_span_id(span_id)
            trace_context.set_parent_span_id(parent_span_id)
            trace_context.push_span(span_id)

            # Update log context
            log_context.set_trace_id(trace_id)
            log_context.set_span_id(span_id)
            log_context.set_correlation_id(trace_id)  # Use trace ID as correlation ID

            self.logger.debug(
                f"Started span: {operation_name}",
                extra={
                    'trace_id': trace_id,
                    'span_id': span_id,
                    'parent_span_id': parent_span_id,
                    'operation': operation_name
                }
            )

            return span

    def finish_span(self, span_id: str, status_code: int = 0, status_message: str = "OK") -> None:
        """Finish a span"""
        with self._lock:
            span = self.active_spans.pop(span_id, None)
            if span:
                span.finish()
                span.set_status(status_code, status_message)

                # Update trace context
                trace_context.pop_span()
                current_span_id = trace_context.get_span_id()
                if current_span_id == span_id:
                    # Restore parent context if available
                    parent_span_id = span.parent_span_id
                    trace_context.set_span_id(parent_span_id)
                    trace_context.set_parent_span_id(None)

                self.logger.debug(
                    f"Finished span: {span.operation_name}",
                    extra={
                        'trace_id': span.trace_id,
                        'span_id': span.span_id,
                        'duration': span.duration,
                        'status_code': status_code,
                        'status_message': status_message
                    }
                )

                # Export span if configured
                if self.config.enabled:
                    self._export_span(span)

    def _generate_span_id(self) -> str:
        """Generate a unique span ID"""
        self._span_counter += 1
        timestamp = int(time.time() * 1000000)  # microseconds
        return f"{timestamp}-{self._span_counter}"

    def _export_span(self, span: Span) -> None:
        """Export span to external tracing system"""
        try:
            # This would integrate with Jaeger, Zipkin, or other tracing systems
            # For now, we'll just log the span data
            if span.duration and span.duration > self.config.max_payload_size / 1000:  # Convert to seconds
                self.logger.warning(
                    f"Slow operation detected: {span.operation_name}",
                    extra={
                        'trace_id': span.trace_id,
                        'span_id': span.span_id,
                        'duration': span.duration,
                        'threshold': self.config.max_payload_size / 1000
                    }
                )

        except Exception as e:
            self.logger.error(f"Failed to export span: {e}")

    def get_active_spans(self) -> List[Span]:
        """Get list of active spans"""
        with self._lock:
            return list(self.active_spans.values())

    def get_span(self, span_id: str) -> Optional[Span]:
        """Get a specific span"""
        with self._lock:
            return self.spans.get(span_id)

    def get_trace_spans(self, trace_id: str) -> List[Span]:
        """Get all spans for a trace"""
        with self._lock:
            return [span for span in self.spans.values() if span.trace_id == trace_id]

    def clear_old_spans(self, max_age_seconds: int = 3600) -> None:
        """Clear old spans from memory"""
        cutoff_time = time.time() - max_age_seconds

        with self._lock:
            old_span_ids = [
                span_id for span_id, span in self.spans.items()
                if span.start_time < cutoff_time
            ]

            for span_id in old_span_ids:
                self.spans.pop(span_id, None)
                self.active_spans.pop(span_id, None)

    def get_trace_stats(self) -> Dict[str, Any]:
        """Get tracing statistics"""
        with self._lock:
            active_count = len(self.active_spans)
            total_count = len(self.spans)

            # Calculate average duration for finished spans
            finished_spans = [span for span in self.spans.values() if span.duration is not None]
            avg_duration = 0.0
            if finished_spans:
                avg_duration = sum(span.duration for span in finished_spans) / len(finished_spans)

            return {
                'active_spans': active_count,
                'total_spans': total_count,
                'average_duration': avg_duration,
                'finished_spans': len(finished_spans)
            }


class CorrelationManager:
    """Manages correlation IDs and request tracking"""

    def __init__(self):
        self._lock = threading.Lock()
        self._correlation_mapping: Dict[str, Dict[str, Any]] = {}
        self.logger = get_logger(__name__)

    def generate_correlation_id(self) -> str:
        """Generate a new correlation ID"""
        return str(uuid.uuid4())

    def start_request(self, correlation_id: str, request_info: Dict[str, Any]) -> None:
        """Start tracking a request"""
        with self._lock:
            self._correlation_mapping[correlation_id] = {
                'start_time': time.time(),
                'request_info': request_info,
                'spans': [],
                'status': 'active'
            }

    def end_request(self, correlation_id: str, status: str = "completed",
                   response_info: Dict[str, Any] = None) -> None:
        """End tracking a request"""
        with self._lock:
            if correlation_id in self._correlation_mapping:
                request_data = self._correlation_mapping[correlation_id]
                request_data['end_time'] = time.time()
                request_data['duration'] = request_data['end_time'] - request_data['start_time']
                request_data['status'] = status
                if response_info:
                    request_data['response_info'] = response_info

                self.logger.info(
                    f"Request completed: {status}",
                    extra={
                        'correlation_id': correlation_id,
                        'duration': request_data['duration'],
                        'status': status,
                        'span_count': len(request_data['spans'])
                    }
                )

    def add_span_to_request(self, correlation_id: str, span_id: str) -> None:
        """Add a span to a request"""
        with self._lock:
            if correlation_id in self._correlation_mapping:
                self._correlation_mapping[correlation_id]['spans'].append(span_id)

    def get_request_info(self, correlation_id: str) -> Optional[Dict[str, Any]]:
        """Get request information"""
        with self._lock:
            return self._correlation_mapping.get(correlation_id)

    def cleanup_old_requests(self, max_age_seconds: int = 86400) -> None:
        """Clean up old request data"""
        cutoff_time = time.time() - max_age_seconds

        with self._lock:
            old_correlation_ids = [
                correlation_id for correlation_id, data in self._correlation_mapping.items()
                if data['start_time'] < cutoff_time
            ]

            for correlation_id in old_correlation_ids:
                self._correlation_mapping.pop(correlation_id, None)

    def get_active_requests_count(self) -> int:
        """Get count of active requests"""
        with self._lock:
            return sum(1 for data in self._correlation_mapping.values() if data['status'] == 'active')


@contextmanager
def trace_span(operation_name: str, tags: Dict[str, Any] = None, tracer: DistributedTracer = None):
    """Context manager for creating spans"""
    if tracer is None:
        tracer = get_tracer()

    parent_span_id = trace_context.get_span_id()
    trace_id = trace_context.get_trace_id()

    span = tracer.start_span(
        operation_name=operation_name,
        parent_span_id=parent_span_id,
        trace_id=trace_id,
        tags=tags
    )

    try:
        yield span
    except Exception as e:
        span.set_status(1, str(e))
        span.log_event("error", {"error": str(e), "type": type(e).__name__})
        raise
    finally:
        tracer.finish_span(span.span_id)


def trace_function(operation_name: str = None):
    """Decorator to trace function execution"""
    def decorator(func):
        name = operation_name or f"{func.__module__}.{func.__name__}"

        def wrapper(*args, **kwargs):
            with trace_span(name, {"function": func.__name__, "module": func.__module__}):
                return func(*args, **kwargs)
        return wrapper
    return decorator


# Global instances
_tracer = None
_correlation_manager = None


def initialize_tracing() -> None:
    """Initialize distributed tracing system"""
    global _tracer, _correlation_manager

    config = get_logging_config()
    _tracer = DistributedTracer(config.tracing)
    _correlation_manager = CorrelationManager()

    logging.info("Distributed tracing system initialized")


def get_tracer() -> Optional[DistributedTracer]:
    """Get the global tracer instance"""
    return _tracer


def get_correlation_manager() -> Optional[CorrelationManager]:
    """Get the global correlation manager instance"""
    return _correlation_manager


def get_trace_context() -> Dict[str, str]:
    """Get current trace context as dictionary"""
    return {
        'trace_id': trace_context.get_trace_id(),
        'span_id': trace_context.get_span_id(),
        'parent_span_id': trace_context.get_parent_span_id(),
        'correlation_id': log_context.get_correlation_id()
    }


def set_trace_context_from_headers(headers: Dict[str, str]) -> None:
    """Set trace context from HTTP headers"""
    context = TraceContextHeaders.extract_from_headers(headers)

    if 'trace_id' in context:
        trace_context.set_trace_id(context['trace_id'])
    if 'span_id' in context:
        trace_context.set_span_id(context['span_id'])
    if 'parent_span_id' in context:
        trace_context.set_parent_span_id(context['parent_span_id'])
    if 'correlation_id' in context:
        log_context.set_correlation_id(context['correlation_id'])


def get_trace_headers() -> Dict[str, str]:
    """Get HTTP headers for trace context propagation"""
    context = get_trace_context()
    return TraceContextHeaders.inject_to_headers(context)


def start_request_trace(correlation_id: str = None, request_info: Dict[str, Any] = None) -> str:
    """Start tracing a new request"""
    if correlation_id is None:
        correlation_id = _correlation_manager.generate_correlation_id()

    if request_info is None:
        request_info = {}

    _correlation_manager.start_request(correlation_id, request_info)
    log_context.set_correlation_id(correlation_id)

    return correlation_id


def end_request_trace(correlation_id: str, status: str = "completed", response_info: Dict[str, Any] = None) -> None:
    """End tracing a request"""
    _correlation_manager.end_request(correlation_id, status, response_info)