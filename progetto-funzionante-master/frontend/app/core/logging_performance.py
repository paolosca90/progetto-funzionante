"""
Advanced Performance Logging and Metrics System
Provides comprehensive performance monitoring, metrics collection,
and real-time analytics for the application.
"""

import time
import threading
import psutil
import asyncio
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, deque
import json
import statistics

from .logging_config import get_logging_config, PerformanceLoggingConfig
from .logging_structured import get_logger, get_memory_usage, get_cpu_usage
from .logging_tracing import get_tracer, trace_span


class MetricType(Enum):
    """Types of metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"
    SUMMARY = "summary"


class MetricCategory(Enum):
    """Categories of metrics"""
    HTTP = "http"
    DATABASE = "database"
    CACHE = "cache"
    EXTERNAL_API = "external_api"
    BUSINESS_LOGIC = "business_logic"
    SYSTEM = "system"
    CUSTOM = "custom"


@dataclass
class Metric:
    """Individual metric data point"""
    name: str
    type: MetricType
    value: float
    timestamp: float
    category: MetricCategory
    tags: Dict[str, str] = field(default_factory=dict)
    unit: Optional[str] = None
    description: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert metric to dictionary"""
        return {
            'name': self.name,
            'type': self.type.value,
            'value': self.value,
            'timestamp': self.timestamp,
            'category': self.category.value,
            'tags': self.tags,
            'unit': self.unit,
            'description': self.description
        }


@dataclass
class Histogram:
    """Histogram metric with percentiles"""
    name: str
    values: List[float] = field(default_factory=list)
    sum_: float = 0.0
    count: int = 0
    min_: float = float('inf')
    max_: float = float('-inf')

    def add_value(self, value: float) -> None:
        """Add a value to the histogram"""
        self.values.append(value)
        self.sum_ += value
        self.count += 1
        self.min_ = min(self.min_, value)
        self.max_ = max(self.max_, value)

        # Keep only recent values (last 1000)
        if len(self.values) > 1000:
            self.values = self.values[-1000:]

    def get_percentiles(self) -> Dict[str, float]:
        """Calculate percentiles"""
        if not self.values:
            return {}

        sorted_values = sorted(self.values)
        count = len(sorted_values)

        return {
            'p50': sorted_values[count // 2],
            'p75': sorted_values[int(count * 0.75)],
            'p90': sorted_values[int(count * 0.90)],
            'p95': sorted_values[int(count * 0.95)],
            'p99': sorted_values[int(count * 0.99)],
            'p999': sorted_values[int(count * 0.999)] if count > 1000 else sorted_values[-1]
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get histogram statistics"""
        if not self.values:
            return {}

        percentiles = self.get_percentiles()
        return {
            'count': self.count,
            'sum': self.sum_,
            'min': self.min_,
            'max': self.max_,
            'mean': self.sum_ / self.count if self.count > 0 else 0,
            **percentiles
        }


@dataclass
class PerformanceAlert:
    """Performance alert definition"""
    name: str
    metric_name: str
    condition: str  # e.g., "value > threshold", "rate > limit"
    threshold: float
    duration: int = 300  # seconds
    severity: str = "warning"
    enabled: bool = True
    callback: Optional[Callable] = None


class PerformanceMetricsCollector:
    """Collects and manages performance metrics"""

    def __init__(self, config: PerformanceLoggingConfig):
        self.config = config
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, Histogram] = defaultdict(Histogram)
        self.timers: Dict[str, List[float]] = defaultdict(list)
        self.raw_metrics: List[Metric] = []
        self._lock = threading.Lock()
        self._max_metrics = 10000
        self.logger = get_logger(__name__)

    def record_counter(self, name: str, value: float = 1.0, category: MetricCategory = MetricCategory.CUSTOM,
                     tags: Dict[str, str] = None) -> None:
        """Record a counter metric"""
        with self._lock:
            self.counters[name] += value
            metric = Metric(
                name=name,
                type=MetricType.COUNTER,
                value=self.counters[name],
                timestamp=time.time(),
                category=category,
                tags=tags or {}
            )
            self._add_metric(metric)

    def set_gauge(self, name: str, value: float, category: MetricCategory = MetricCategory.CUSTOM,
                 tags: Dict[str, str] = None) -> None:
        """Set a gauge metric"""
        with self._lock:
            self.gauges[name] = value
            metric = Metric(
                name=name,
                type=MetricType.GAUGE,
                value=value,
                timestamp=time.time(),
                category=category,
                tags=tags or {}
            )
            self._add_metric(metric)

    def record_histogram(self, name: str, value: float, category: MetricCategory = MetricCategory.CUSTOM,
                       tags: Dict[str, str] = None) -> None:
        """Record a histogram value"""
        with self._lock:
            self.histograms[name].add_value(value)
            metric = Metric(
                name=name,
                type=MetricType.HISTOGRAM,
                value=value,
                timestamp=time.time(),
                category=category,
                tags=tags or {}
            )
            self._add_metric(metric)

    def start_timer(self, name: str, category: MetricCategory = MetricCategory.CUSTOM,
                   tags: Dict[str, str] = None) -> float:
        """Start a timer"""
        return time.time()

    def stop_timer(self, name: str, start_time: float, category: MetricCategory = MetricCategory.CUSTOM,
                  tags: Dict[str, str] = None) -> None:
        """Stop a timer and record duration"""
        duration = time.time() - start_time
        with self._lock:
            self.timers[name].append(duration)
            # Keep only recent timer values
            if len(self.timers[name]) > 1000:
                self.timers[name] = self.timers[name][-1000:]

            metric = Metric(
                name=name,
                type=MetricType.TIMER,
                value=duration,
                timestamp=time.time(),
                category=category,
                tags=tags or {},
                unit="seconds"
            )
            self._add_metric(metric)

    def _add_metric(self, metric: Metric) -> None:
        """Add a metric to the collector"""
        self.raw_metrics.append(metric)

        # Keep only recent metrics
        if len(self.raw_metrics) > self._max_metrics:
            self.raw_metrics = self.raw_metrics[-self._max_metrics:]

        # Log slow operations
        if (metric.type == MetricType.TIMER and
            metric.value > self.config.slow_request_threshold):
            self.logger.warning(
                f"Slow operation detected: {metric.name}",
                extra={
                    'metric_name': metric.name,
                    'duration': metric.value,
                    'threshold': self.config.slow_request_threshold,
                    'category': metric.category.value
                }
            )

    def get_metric_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary"""
        with self._lock:
            summary = {
                'counters': dict(self.counters),
                'gauges': dict(self.gauges),
                'histograms': {name: hist.get_stats() for name, hist in self.histograms.items()},
                'timers': {},
                'system_metrics': self._get_system_metrics()
            }

            # Calculate timer statistics
            for name, values in self.timers.items():
                if values:
                    summary['timers'][name] = {
                        'count': len(values),
                        'min': min(values),
                        'max': max(values),
                        'mean': statistics.mean(values),
                        'p50': statistics.median(values),
                        'p95': statistics.quantiles(values, n=20)[18] if len(values) > 20 else max(values)
                    }

            return summary

    def _get_system_metrics(self) -> Dict[str, float]:
        """Get system performance metrics"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            cpu_percent = process.cpu_percent(interval=0.1)

            return {
                'memory_usage_mb': memory_info.rss / 1024 / 1024,
                'memory_usage_percent': process.memory_percent(),
                'cpu_usage_percent': cpu_percent,
                'thread_count': process.num_threads(),
                'handle_count': process.num_handles() if hasattr(process, 'num_handles') else 0,
                'open_files': len(process.open_files()) if hasattr(process, 'open_files') else 0
            }
        except Exception as e:
            self.logger.error(f"Failed to get system metrics: {e}")
            return {}

    def get_metrics_by_category(self, category: MetricCategory) -> List[Metric]:
        """Get metrics by category"""
        with self._lock:
            return [m for m in self.raw_metrics if m.category == category]

    def get_metrics_by_time_range(self, start_time: float, end_time: float) -> List[Metric]:
        """Get metrics within time range"""
        with self._lock:
            return [m for m in self.raw_metrics if start_time <= m.timestamp <= end_time]

    def clear_old_metrics(self, max_age_seconds: int = 3600) -> None:
        """Clear old metrics"""
        cutoff_time = time.time() - max_age_seconds

        with self._lock:
            self.raw_metrics = [m for m in self.raw_metrics if m.timestamp > cutoff_time]


class PerformanceMonitor:
    """High-level performance monitoring system"""

    def __init__(self, config: PerformanceLoggingConfig):
        self.config = config
        self.collector = PerformanceMetricsCollector(config)
        self.alerts: List[PerformanceAlert] = []
        self.alert_history: List[Dict[str, Any]] = []
        self._monitoring_task: Optional[asyncio.Task] = None
        self._lock = threading.Lock()
        self.logger = get_logger(__name__)

    def start_monitoring(self) -> None:
        """Start performance monitoring"""
        if self._monitoring_task and not self._monitoring_task.done():
            return

        self._monitoring_task = asyncio.create_task(self._monitoring_loop())

    def stop_monitoring(self) -> None:
        """Stop performance monitoring"""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                asyncio.get_event_loop().run_until_complete(self._monitoring_task)
            except (asyncio.CancelledError, RuntimeError):
                pass

    async def _monitoring_loop(self) -> None:
        """Background monitoring loop"""
        while True:
            try:
                # Collect system metrics
                await self._collect_system_metrics()

                # Check alerts
                await self._check_alerts()

                # Cleanup old data
                self.collector.clear_old_metrics()

                # Sleep for monitoring interval
                await asyncio.sleep(30)  # Monitor every 30 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Performance monitoring error: {e}")
                await asyncio.sleep(5)

    async def _collect_system_metrics(self) -> None:
        """Collect system performance metrics"""
        try:
            # Memory metrics
            memory_usage = get_memory_usage()
            if memory_usage:
                self.collector.set_gauge(
                    "system.memory_usage_mb",
                    memory_usage,
                    MetricCategory.SYSTEM,
                    {"type": "memory"}
                )

                if memory_usage > self.config.memory_usage_threshold:
                    self.logger.warning(
                        f"High memory usage: {memory_usage:.1f}MB",
                        extra={'memory_usage_mb': memory_usage, 'threshold': self.config.memory_usage_threshold}
                    )

            # CPU metrics
            cpu_usage = get_cpu_usage()
            if cpu_usage:
                self.collector.set_gauge(
                    "system.cpu_usage_percent",
                    cpu_usage,
                    MetricCategory.SYSTEM,
                    {"type": "cpu"}
                )

                if cpu_usage > self.config.cpu_usage_threshold:
                    self.logger.warning(
                        f"High CPU usage: {cpu_usage:.1f}%",
                        extra={'cpu_usage_percent': cpu_usage, 'threshold': self.config.cpu_usage_threshold}
                    )

            # Disk metrics
            disk_usage = psutil.disk_usage('/')
            self.collector.set_gauge(
                "system.disk_usage_percent",
                disk_usage.percent,
                MetricCategory.SYSTEM,
                {"type": "disk", "path": "/"}
            )

            # Network metrics
            net_io = psutil.net_io_counters()
            self.collector.set_gauge(
                "system.network_bytes_sent",
                net_io.bytes_sent,
                MetricCategory.SYSTEM,
                {"type": "network", "direction": "sent"}
            )
            self.collector.set_gauge(
                "system.network_bytes_recv",
                net_io.bytes_recv,
                MetricCategory.SYSTEM,
                {"type": "network", "direction": "received"}
            )

        except Exception as e:
            self.logger.error(f"Failed to collect system metrics: {e}")

    async def _check_alerts(self) -> None:
        """Check performance alerts"""
        metrics_summary = self.collector.get_metric_summary()

        for alert in self.alerts:
            if not alert.enabled:
                continue

            try:
                triggered = await self._evaluate_alert(alert, metrics_summary)
                if triggered:
                    await self._trigger_alert(alert, metrics_summary)
            except Exception as e:
                self.logger.error(f"Alert evaluation error for {alert.name}: {e}")

    async def _evaluate_alert(self, alert: PerformanceAlert, metrics_summary: Dict[str, Any]) -> bool:
        """Evaluate if an alert should be triggered"""
        # Simple evaluation logic - can be extended
        if alert.metric_name in metrics_summary['gauges']:
            value = metrics_summary['gauges'][alert.metric_name]
            return value > alert.threshold
        elif alert.metric_name in metrics_summary['counters']:
            value = metrics_summary['counters'][alert.metric_name]
            return value > alert.threshold
        elif alert.metric_name in metrics_summary['timers']:
            timer_stats = metrics_summary['timers'][alert.metric_name]
            if 'mean' in timer_stats:
                return timer_stats['mean'] > alert.threshold

        return False

    async def _trigger_alert(self, alert: PerformanceAlert, metrics_summary: Dict[str, Any]) -> None:
        """Trigger a performance alert"""
        alert_data = {
            "name": alert.name,
            "metric_name": alert.metric_name,
            "threshold": alert.threshold,
            "current_value": metrics_summary.get("gauges", {}).get(alert.metric_name, 0),
            "severity": alert.severity,
            "timestamp": datetime.now().isoformat(),
            "message": f"Performance alert triggered: {alert.name}"
        }

        self.alert_history.append(alert_data)
        self.logger.warning(
            f"Performance alert triggered: {alert.name}",
            extra=alert_data
        )

        # Call custom callback if provided
        if alert.callback:
            try:
                if asyncio.iscoroutinefunction(alert.callback):
                    await alert.callback(alert_data)
                else:
                    alert.callback(alert_data)
            except Exception as e:
                self.logger.error(f"Error in alert callback: {e}")

    def add_alert(self, alert: PerformanceAlert) -> None:
        """Add a performance alert"""
        with self._lock:
            self.alerts.append(alert)

    def remove_alert(self, alert_name: str) -> None:
        """Remove a performance alert"""
        with self._lock:
            self.alerts = [a for a in self.alerts if a.name != alert_name]

    def get_alert_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get alert history"""
        with self._lock:
            return self.alert_history[-limit:]

    def get_performance_report(self, time_range_hours: int = 24) -> Dict[str, Any]:
        """Generate performance report"""
        start_time = time.time() - (time_range_hours * 3600)
        end_time = time.time()

        metrics = self.collector.get_metrics_by_time_range(start_time, end_time)
        metrics_summary = self.collector.get_metric_summary()

        # Calculate performance insights
        insights = self._calculate_performance_insights(metrics, metrics_summary)

        return {
            "time_range_hours": time_range_hours,
            "generated_at": datetime.now().isoformat(),
            "metrics_summary": metrics_summary,
            "insights": insights,
            "alert_count": len([a for a in self.alert_history if a['timestamp'] > start_time]),
            "total_metrics": len(metrics)
        }

    def _calculate_performance_insights(self, metrics: List[Metric], summary: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Calculate performance insights"""
        insights = []

        # Slow operations analysis
        slow_ops = [m for m in metrics if m.type == MetricType.TIMER and m.value > self.config.slow_request_threshold]
        if slow_ops:
            insights.append({
                "type": "slow_operations",
                "count": len(slow_ops),
                "average_duration": statistics.mean([m.value for m in slow_ops]),
                "slowest_operation": max(slow_ops, key=lambda m: m.value).name,
                "severity": "warning" if len(slow_ops) < 10 else "critical"
            })

        # Error rate analysis
        error_metrics = [m for m in metrics if 'error' in m.name.lower() or 'exception' in m.name.lower()]
        if error_metrics:
            insights.append({
                "type": "error_analysis",
                "count": len(error_metrics),
                "error_rate": len(error_metrics) / len(metrics) * 100 if metrics else 0,
                "most_common_error": max(set(m.name for m in error_metrics), key=lambda x: sum(1 for m in error_metrics if m.name == x)),
                "severity": "info"
            })

        # Resource usage trends
        if 'system_metrics' in summary:
            memory_usage = summary['system_metrics'].get('memory_usage_percent', 0)
            cpu_usage = summary['system_metrics'].get('cpu_usage_percent', 0)

            if memory_usage > 80:
                insights.append({
                    "type": "high_memory_usage",
                    "usage_percent": memory_usage,
                    "severity": "warning" if memory_usage < 90 else "critical"
                })

            if cpu_usage > 70:
                insights.append({
                    "type": "high_cpu_usage",
                    "usage_percent": cpu_usage,
                    "severity": "warning" if cpu_usage < 85 else "critical"
                })

        return insights


class PerformanceMiddleware:
    """FastAPI middleware for performance monitoring"""

    def __init__(self, app, monitor: PerformanceMonitor):
        self.app = app
        self.monitor = monitor
        self.logger = get_logger(__name__)

    async def __call__(self, scope, receive, send):
        """ASGI middleware implementation"""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        start_time = time.time()
        correlation_id = f"req_{int(time.time() * 1000000)}"

        # Add performance tracking
        path = scope.get("path", "")
        method = scope.get("method", "")

        # Record request start
        self.monitor.collector.record_counter(
            "http.requests_total",
            1.0,
            MetricCategory.HTTP,
            {"method": method, "path": path}
        )

        try:
            # Process request
            response_sent = False

            async def send_wrapper(message):
                nonlocal response_sent
                if message["type"] == "http.response.start":
                    response_sent = True
                    status_code = message["status"]

                    # Record response metrics
                    duration = time.time() - start_time
                    self.monitor.collector.stop_timer(
                        "http.request_duration",
                        start_time,
                        MetricCategory.HTTP,
                        {"method": method, "path": path, "status_code": str(status_code)}
                    )

                    # Record status code metrics
                    self.monitor.collector.record_counter(
                        f"http.responses_{status_code // 100}xx_total",
                        1.0,
                        MetricCategory.HTTP,
                        {"method": method, "path": path}
                    )

                    # Log slow requests
                    if duration > self.monitor.config.slow_request_threshold:
                        self.logger.warning(
                            f"Slow HTTP request: {method} {path}",
                            extra={
                                'duration': duration,
                                'method': method,
                                'path': path,
                                'status_code': status_code,
                                'correlation_id': correlation_id
                            }
                        )

                await send(message)

            await self.app(scope, receive, send_wrapper)

        except Exception as e:
            # Record error metrics
            duration = time.time() - start_time
            self.monitor.collector.record_counter(
                "http.errors_total",
                1.0,
                MetricCategory.HTTP,
                {"method": method, "path": path, "error_type": type(e).__name__}
            )

            self.logger.error(
                f"HTTP request error: {method} {path}",
                extra={
                    'duration': duration,
                    'method': method,
                    'path': path,
                    'error': str(e),
                    'correlation_id': correlation_id
                },
                exc_info=True
            )

            raise


# Global instances
_performance_monitor = None


def initialize_performance_monitoring() -> None:
    """Initialize performance monitoring system"""
    global _performance_monitor

    config = get_logging_config()
    _performance_monitor = PerformanceMonitor(config.performance)
    _performance_monitor.start_monitoring()

    logging.info("Performance monitoring system initialized")


def get_performance_monitor() -> Optional[PerformanceMonitor]:
    """Get the global performance monitor instance"""
    return _performance_monitor


def add_performance_middleware(app) -> PerformanceMiddleware:
    """Add performance monitoring middleware to FastAPI app"""
    monitor = get_performance_monitor()
    if monitor:
        middleware = PerformanceMiddleware(app, monitor)
        return middleware
    return app


# Convenience functions
def record_counter(name: str, value: float = 1.0, category: MetricCategory = MetricCategory.CUSTOM, **tags):
    """Record a counter metric"""
    if _performance_monitor:
        _performance_monitor.collector.record_counter(name, value, category, tags)


def set_gauge(name: str, value: float, category: MetricCategory = MetricCategory.CUSTOM, **tags):
    """Set a gauge metric"""
    if _performance_monitor:
        _performance_monitor.collector.set_gauge(name, value, category, tags)


def record_histogram(name: str, value: float, category: MetricCategory = MetricCategory.CUSTOM, **tags):
    """Record a histogram value"""
    if _performance_monitor:
        _performance_monitor.collector.record_histogram(name, value, category, tags)


def time_function(operation_name: str = None):
    """Decorator to time function execution"""
    def decorator(func):
        name = operation_name or f"{func.__module__}.{func.__name__}"

        async def async_wrapper(*args, **kwargs):
            start_time = _performance_monitor.collector.start_timer(name, MetricCategory.BUSINESS_LOGIC)
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                _performance_monitor.collector.stop_timer(name, start_time, MetricCategory.BUSINESS_LOGIC)

        def sync_wrapper(*args, **kwargs):
            start_time = _performance_monitor.collector.start_timer(name, MetricCategory.BUSINESS_LOGIC)
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                _performance_monitor.collector.stop_timer(name, start_time, MetricCategory.BUSINESS_LOGIC)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator