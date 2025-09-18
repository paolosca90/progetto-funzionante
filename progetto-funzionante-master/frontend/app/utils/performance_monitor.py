"""
Performance Monitoring Utilities for FastAPI with Sentry Integration
Real-time performance tracking, custom metrics, and alerts
"""

import time
import threading
import psutil
import asyncio
from datetime import datetime, UTC, timedelta
from typing import Dict, List, Optional, Any, Callable
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, asdict
import json
import logging

import sentry_sdk
from prometheus_client import Counter, Histogram, Gauge, start_http_server
from prometheus_client.exposition import generate_latest

from app.core.sentry_config import sentry_config, ErrorSeverity, ErrorCategory
from config.settings import settings


@dataclass
class PerformanceMetrics:
    """Performance metrics data structure"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_usage_mb: float
    disk_usage_percent: float
    active_requests: int
    response_time_avg: float
    error_rate: float
    database_connections: int
    cache_hit_rate: float


class PerformanceMonitor:
    """
    Comprehensive performance monitoring system
    - System metrics (CPU, memory, disk)
    - Application metrics (requests, errors, response times)
    - Custom metrics and business KPIs
    - Real-time alerts and dashboards
    """

    def __init__(self):
        self.metrics_history: List[PerformanceMetrics] = []
        self.active_requests = 0
        self.request_count = 0
        self.error_count = 0
        self.response_times: List[float] = []
        self.lock = threading.Lock()
        self.running = False
        self.collection_interval = 30  # seconds

        # Prometheus metrics
        self._setup_prometheus_metrics()

    def _setup_prometheus_metrics(self) -> None:
        """Setup Prometheus metrics"""
        # HTTP metrics
        self.http_requests_total = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status_code']
        )

        self.http_request_duration = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration',
            ['method', 'endpoint']
        )

        self.active_requests_gauge = Gauge(
            'active_requests',
            'Number of active requests'
        )

        # System metrics
        self.cpu_usage_gauge = Gauge(
            'cpu_usage_percent',
            'CPU usage percentage'
        )

        self.memory_usage_gauge = Gauge(
            'memory_usage_percent',
            'Memory usage percentage'
        )

        self.disk_usage_gauge = Gauge(
            'disk_usage_percent',
            'Disk usage percentage'
        )

        # Business metrics
        self.signals_generated_total = Counter(
            'signals_generated_total',
            'Total trading signals generated',
            ['symbol', 'confidence_level']
        )

        self.users_active_gauge = Gauge(
            'users_active',
            'Number of active users'
        )

        # Database metrics
        self.database_query_duration = Histogram(
            'database_query_duration_seconds',
            'Database query duration',
            ['operation', 'table']
        )

        self.database_connections_gauge = Gauge(
            'database_connections',
            'Number of database connections'
        )

        # Cache metrics
        self.cache_hit_ratio_gauge = Gauge(
            'cache_hit_ratio',
            'Cache hit ratio'
        )

        self.cache_operations_total = Counter(
            'cache_operations_total',
            'Total cache operations',
            ['operation', 'result']
        )

    def start_monitoring(self) -> None:
        """Start background monitoring"""
        if self.running:
            return

        self.running = True
        self._start_metrics_collection()
        self._start_prometheus_server()

        logging.info("Performance monitoring started")

    def stop_monitoring(self) -> None:
        """Stop background monitoring"""
        self.running = False
        logging.info("Performance monitoring stopped")

    def _start_metrics_collection(self) -> None:
        """Start background metrics collection"""
        def collect_metrics():
            while self.running:
                try:
                    metrics = self._collect_system_metrics()
                    with self.lock:
                        self.metrics_history.append(metrics)
                        # Keep only last 1000 metrics
                        if len(self.metrics_history) > 1000:
                            self.metrics_history.pop(0)
                except Exception as e:
                    logging.error(f"Error collecting metrics: {e}")

                time.sleep(self.collection_interval)

        thread = threading.Thread(target=collect_metrics, daemon=True)
        thread.start()

    def _start_prometheus_server(self) -> None:
        """Start Prometheus metrics server"""
        try:
            port = settings.monitoring.metrics_port
            start_http_server(port)
            logging.info(f"Prometheus metrics server started on port {port}")
        except Exception as e:
            logging.error(f"Failed to start Prometheus server: {e}")

    def _collect_system_metrics(self) -> PerformanceMetrics:
        """Collect system metrics"""
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # Calculate derived metrics
            with self.lock:
                response_time_avg = sum(self.response_times) / len(self.response_times) if self.response_times else 0
                error_rate = self.error_count / self.request_count if self.request_count > 0 else 0

            return PerformanceMetrics(
                timestamp=datetime.now(UTC).isoformat(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_usage_mb=memory.used / 1024 / 1024,
                disk_usage_percent=disk.percent,
                active_requests=self.active_requests,
                response_time_avg=response_time_avg,
                error_rate=error_rate,
                database_connections=self._get_database_connections(),
                cache_hit_rate=self._get_cache_hit_rate()
            )
        except Exception as e:
            logging.error(f"Error collecting system metrics: {e}")
            return PerformanceMetrics(
                timestamp=datetime.now(UTC).isoformat(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_usage_mb=0.0,
                disk_usage_percent=0.0,
                active_requests=0,
                response_time_avg=0.0,
                error_rate=0.0,
                database_connections=0,
                cache_hit_rate=0.0
            )

    def _get_database_connections(self) -> int:
        """Get current database connections count"""
        try:
            # This would need to be implemented based on your database setup
            # For now, return a placeholder
            return 0
        except Exception:
            return 0

    def _get_cache_hit_rate(self) -> float:
        """Get cache hit rate"""
        try:
            # This would need to be implemented based on your cache setup
            # For now, return a placeholder
            return 0.85
        except Exception:
            return 0.0

    @contextmanager
    def track_request(self, method: str, endpoint: str):
        """Context manager for tracking HTTP requests"""
        self.active_requests += 1
        self.active_requests_gauge.set(self.active_requests)
        start_time = time.time()

        try:
            yield
            status_code = 200  # Default success
        except Exception as e:
            status_code = getattr(e, 'status_code', 500)
            self.error_count += 1
            raise
        finally:
            duration = time.time() - start_time
            self.active_requests -= 1
            self.active_requests_gauge.set(self.active_requests)

            # Update metrics
            with self.lock:
                self.request_count += 1
                self.response_times.append(duration)
                # Keep only last 1000 response times
                if len(self.response_times) > 1000:
                    self.response_times.pop(0)

            # Update Prometheus metrics
            self.http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=str(status_code)
            ).inc()

            self.http_request_duration.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)

            # Check for performance issues
            self._check_performance_thresholds(duration, method, endpoint)

    @contextmanager
    def track_database_query(self, operation: str, table: str):
        """Context manager for tracking database queries"""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.database_query_duration.labels(
                operation=operation,
                table=table
            ).observe(duration)

    @contextmanager
    def track_cache_operation(self, operation: str, result: str):
        """Context manager for tracking cache operations"""
        try:
            yield
        finally:
            self.cache_operations_total.labels(
                operation=operation,
                result=result
            ).inc()

    def _check_performance_thresholds(self, duration: float, method: str, endpoint: str) -> None:
        """Check performance thresholds and send alerts"""
        # Slow request alert
        if duration > 5.0:
            sentry_config.capture_message(
                f"Slow HTTP request: {method} {endpoint} took {duration:.2f}s",
                level=ErrorSeverity.WARNING,
                category=ErrorCategory.PERFORMANCE,
                tags={
                    "alert_type": "slow_request",
                    "method": method,
                    "endpoint": endpoint
                },
                extra_data={
                    "duration": duration,
                    "threshold": 5.0
                }
            )

        # Very slow request alert
        if duration > 10.0:
            sentry_config.capture_message(
                f"Very slow HTTP request: {method} {endpoint} took {duration:.2f}s",
                level=ErrorSeverity.ERROR,
                category=ErrorCategory.PERFORMANCE,
                tags={
                    "alert_type": "very_slow_request",
                    "method": method,
                    "endpoint": endpoint
                },
                extra_data={
                    "duration": duration,
                    "threshold": 10.0
                }
            )

    def record_signal_generated(self, symbol: str, confidence_level: str) -> None:
        """Record signal generation metric"""
        self.signals_generated_total.labels(
            symbol=symbol,
            confidence_level=confidence_level
        ).inc()

    def update_active_users(self, count: int) -> None:
        """Update active users gauge"""
        self.users_active_gauge.set(count)

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for dashboard"""
        with self.lock:
            if not self.metrics_history:
                return {"error": "No metrics available"}

            latest = self.metrics_history[-1]
            return {
                "current": asdict(latest),
                "trends": self._calculate_trends(),
                "alerts": self._get_active_alerts(),
                "summary": {
                    "total_requests": self.request_count,
                    "total_errors": self.error_count,
                    "avg_response_time": sum(self.response_times) / len(self.response_times) if self.response_times else 0,
                    "error_rate": self.error_count / self.request_count if self.request_count > 0 else 0
                }
            }

    def _calculate_trends(self) -> Dict[str, Any]:
        """Calculate performance trends"""
        if len(self.metrics_history) < 2:
            return {}

        recent = self.metrics_history[-10:]  # Last 10 metrics
        older = self.metrics_history[-20:-10] if len(self.metrics_history) >= 20 else self.metrics_history[:-10]

        if not older:
            return {}

        def avg_metric(metrics: List[PerformanceMetrics], field: str) -> float:
            return sum(getattr(m, field) for m in metrics) / len(metrics)

        return {
            "cpu_trend": avg_metric(recent, "cpu_percent") - avg_metric(older, "cpu_percent"),
            "memory_trend": avg_metric(recent, "memory_percent") - avg_metric(older, "memory_percent"),
            "response_time_trend": avg_metric(recent, "response_time_avg") - avg_metric(older, "response_time_avg"),
            "error_rate_trend": avg_metric(recent, "error_rate") - avg_metric(older, "error_rate")
        }

    def _get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get active performance alerts"""
        alerts = []
        latest = self.metrics_history[-1] if self.metrics_history else None

        if not latest:
            return alerts

        # CPU alert
        if latest.cpu_percent > 80:
            alerts.append({
                "type": "high_cpu",
                "message": f"High CPU usage: {latest.cpu_percent:.1f}%",
                "severity": "warning" if latest.cpu_percent < 90 else "critical"
            })

        # Memory alert
        if latest.memory_percent > 85:
            alerts.append({
                "type": "high_memory",
                "message": f"High memory usage: {latest.memory_percent:.1f}%",
                "severity": "warning" if latest.memory_percent < 95 else "critical"
            })

        # Error rate alert
        if latest.error_rate > 0.1:
            alerts.append({
                "type": "high_error_rate",
                "message": f"High error rate: {latest.error_rate:.1%}",
                "severity": "warning" if latest.error_rate < 0.2 else "critical"
            })

        return alerts

    def get_prometheus_metrics(self) -> str:
        """Get Prometheus metrics in text format"""
        return generate_latest().decode('utf-8')

    @asynccontextmanager
    async def track_async_operation(self, operation_name: str):
        """Async context manager for tracking operations"""
        start_time = time.time()
        try:
            yield
        except Exception as e:
            duration = time.time() - start_time
            sentry_config.capture_error(
                error=e,
                level=ErrorSeverity.ERROR,
                category=ErrorCategory.PERFORMANCE,
                tags={"operation": operation_name},
                extra_data={"duration": duration, "failed": True}
            )
            raise
        else:
            duration = time.time() - start_time
            # Record successful operation metric
            sentry_config.metrics_aggregator.timing(
                f"operation.{operation_name}.duration",
                duration,
                tags={"status": "success"}
            )


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


# Decorators for easy use
def track_performance(operation_name: str, threshold: float = 1.0):
    """Decorator to track function performance"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            async with performance_monitor.track_async_operation(operation_name):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    duration = time.time() - start_time
                    if duration > threshold:
                        sentry_config.capture_message(
                            f"Slow async operation: {operation_name} took {duration:.2f}s",
                            level=ErrorSeverity.WARNING,
                            category=ErrorCategory.PERFORMANCE,
                            tags={"operation": operation_name}
                        )
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    sentry_config.capture_error(
                        error=e,
                        level=ErrorSeverity.ERROR,
                        category=ErrorCategory.PERFORMANCE,
                        tags={"operation": operation_name},
                        extra_data={"duration": duration}
                    )
                    raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            with performance_monitor.track_async_operation(operation_name):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    if duration > threshold:
                        sentry_config.capture_message(
                            f"Slow operation: {operation_name} took {duration:.2f}s",
                            level=ErrorSeverity.WARNING,
                            category=ErrorCategory.PERFORMANCE,
                            tags={"operation": operation_name}
                        )
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    sentry_config.capture_error(
                        error=e,
                        level=ErrorSeverity.ERROR,
                        category=ErrorCategory.PERFORMANCE,
                        tags={"operation": operation_name},
                        extra_data={"duration": duration}
                    )
                    raise

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator