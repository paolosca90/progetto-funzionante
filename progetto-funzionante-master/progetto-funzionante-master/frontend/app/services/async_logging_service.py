"""
Async Logging and Monitoring Service
Implements high-performance async logging with structured logging,
log aggregation, performance monitoring, and alerting.
"""

import asyncio
import logging
import json
import time
from typing import Dict, Any, Optional, List, AsyncGenerator, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import deque, defaultdict
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import traceback
import sys
from pathlib import Path

import aiofiles
from app.services.cache_service import cache_service
from app.services.async_task_scheduler import task_scheduler, TaskPriority, TaskType

logger = logging.getLogger(__name__)

class LogLevel(Enum):
    """Log levels with severity ordering"""
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50

class LogCategory(Enum):
    """Log categories for filtering and analysis"""
    HTTP_REQUEST = "http_request"
    DATABASE = "database"
    CACHE = "cache"
    FILE_OPERATION = "file_operation"
    AUTHENTICATION = "authentication"
    BUSINESS_LOGIC = "business_logic"
    EXTERNAL_API = "external_api"
    PERFORMANCE = "performance"
    SECURITY = "security"
    SYSTEM = "system"

class MetricType(Enum):
    """Types of metrics for monitoring"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"

@dataclass
class LogEntry:
    """Structured log entry"""
    timestamp: float
    level: LogLevel
    category: LogCategory
    message: str
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    traceback: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None
    execution_time: Optional[float] = None
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None

@dataclass
class Metric:
    """Performance metric"""
    name: str
    type: MetricType
    value: float
    timestamp: float
    tags: Dict[str, str] = field(default_factory=dict)
    unit: Optional[str] = None
    description: Optional[str] = None

@dataclass
class AlertRule:
    """Alert rule definition"""
    name: str
    metric_name: str
    condition: str  # e.g., "value > 100", "rate > 10"
    threshold: float
    duration: float = 300  # seconds
    severity: LogLevel = LogLevel.WARNING
    enabled: bool = True
    notification_channels: List[str] = field(default_factory=list)

@dataclass
class LoggingConfig:
    """Logging configuration"""
    log_level: LogLevel = LogLevel.INFO
    log_file: Optional[str] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    enable_structured_logging: bool = True
    enable_metrics: bool = True
    enable_alerts: bool = True
    console_output: bool = True
    buffer_size: int = 1000
    flush_interval: float = 5.0

class AsyncLogHandler:
    """Async log handler with buffering and batching"""

    def __init__(self, config: LoggingConfig):
        self.config = config
        self.log_buffer = deque(maxlen=config.buffer_size)
        self._flush_task: Optional[asyncio.Task] = None
        self._flush_lock = asyncio.Lock()
        self._stop_flushing = False

    async def handle_log(self, entry: LogEntry):
        """Handle a log entry"""
        if self.config.enable_structured_logging:
            self.log_buffer.append(entry)

            # Start flush task if not running
            if self._flush_task is None or self._flush_task.done():
                self._flush_task = asyncio.create_task(self._flush_logs())

    async def _flush_logs(self):
        """Flush buffered logs to storage"""
        while not self._stop_flushing:
            try:
                await asyncio.sleep(self.config.flush_interval)

                if not self.log_buffer:
                    continue

                async with self._flush_lock:
                    if not self.log_buffer:
                        continue

                    # Get buffered logs
                    logs_to_flush = list(self.log_buffer)
                    self.log_buffer.clear()

                    # Write logs asynchronously
                    await self._write_logs(logs_to_flush)

            except Exception as e:
                logger.error(f"Log flushing error: {e}")

    async def _write_logs(self, logs: List[LogEntry]):
        """Write logs to storage"""
        if self.config.log_file:
            await self._write_to_file(logs)

        # Write to console if enabled
        if self.config.console_output:
            for log in logs:
                self._write_to_console(log)

        # Cache recent logs for querying
        await self._cache_logs(logs)

    async def _write_to_file(self, logs: List[LogEntry]):
        """Write logs to file asynchronously"""
        try:
            log_file = Path(self.config.log_file)
            log_file.parent.mkdir(parents=True, exist_ok=True)

            async with aiofiles.open(log_file, 'a', encoding='utf-8') as f:
                for log in logs:
                    log_line = json.dumps(asdict(log)) + '\n'
                    await f.write(log_line)

            # Rotate file if needed
            if log_file.stat().st_size > self.config.max_file_size:
                await self._rotate_log_file(log_file)

        except Exception as e:
            logger.error(f"File logging error: {e}")

    async def _rotate_log_file(self, current_file: Path):
        """Rotate log file when it gets too large"""
        try:
            # Move current file to backup
            backup_file = current_file.with_suffix(f'.{int(time.time())}.log')
            current_file.rename(backup_file)

            # Keep only specified number of backup files
            log_dir = current_file.parent
            backup_files = sorted(log_dir.glob(f'{current_file.stem}.*.log'))
            if len(backup_files) > self.config.backup_count:
                for old_file in backup_files[:-self.config.backup_count]:
                    old_file.unlink()

        except Exception as e:
            logger.error(f"Log rotation error: {e}")

    def _write_to_console(self, log: LogEntry):
        """Write log to console"""
        timestamp = datetime.fromtimestamp(log.timestamp).strftime('%Y-%m-%d %H:%M:%S')
        level_name = log.level.name
        category = log.category.value

        log_message = f"[{timestamp}] [{level_name}] [{category}] {log.message}"

        if log.user_id:
            log_message += f" (user: {log.user_id})"

        if log.execution_time:
            log_message += f" (duration: {log.execution_time:.3f}s)"

        print(log_message, file=sys.stderr if log.level >= LogLevel.ERROR else sys.stdout)

    async def _cache_logs(self, logs: List[LogEntry]):
        """Cache recent logs for querying"""
        try:
            # Keep last 1000 logs in cache
            cache_key = "recent_logs"
            recent_logs = await cache_service.get(cache_key, default=[])

            # Add new logs and trim to 1000
            recent_logs.extend([asdict(log) for log in logs])
            recent_logs = recent_logs[-1000:]

            await cache_service.set(cache_key, recent_logs, ttl=3600)

        except Exception as e:
            logger.error(f"Log caching error: {e}")

    async def stop(self):
        """Stop the log handler"""
        self._stop_flushing = True
        if self._flush_task:
            await self._flush_task

class AsyncMetricsCollector:
    """Collect and manage performance metrics"""

    def __init__(self):
        self.metrics: Dict[str, List[Metric]] = defaultdict(list)
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = defaultdict(float)
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def record_metric(self, metric: Metric):
        """Record a metric value"""
        async with self._lock:
            self.metrics[metric.name].append(metric)

            # Update specific metric types
            if metric.type == MetricType.COUNTER:
                self.counters[metric.name] += metric.value
            elif metric.type == MetricType.GAUGE:
                self.gauges[metric.name] = metric.value
            elif metric.type == MetricType.HISTOGRAM:
                self.histograms[metric.name].append(metric.value)

            # Keep only recent metrics (last 1 hour)
            cutoff_time = time.time() - 3600
            self.metrics[metric.name] = [
                m for m in self.metrics[metric.name] if m.timestamp > cutoff_time
            ]

    async def increment_counter(self, name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None):
        """Increment a counter metric"""
        metric = Metric(
            name=name,
            type=MetricType.COUNTER,
            value=value,
            timestamp=time.time(),
            tags=tags or {}
        )
        await self.record_metric(metric)

    async def set_gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Set a gauge metric"""
        metric = Metric(
            name=name,
            type=MetricType.GAUGE,
            value=value,
            timestamp=time.time(),
            tags=tags or {}
        )
        await self.record_metric(metric)

    async def record_histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record a histogram metric"""
        metric = Metric(
            name=name,
            type=MetricType.HISTOGRAM,
            value=value,
            timestamp=time.time(),
            tags=tags or {}
        )
        await self.record_metric(metric)

    async def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary"""
        async with self._lock:
            summary = {
                "counters": dict(self.counters),
                "gauges": dict(self.gauges),
                "histograms": {}
            }

            # Calculate histogram statistics
            for name, values in self.histograms.items():
                if values:
                    summary["histograms"][name] = {
                        "count": len(values),
                        "min": min(values),
                        "max": max(values),
                        "avg": sum(values) / len(values),
                        "p50": sorted(values)[len(values) // 2],
                        "p95": sorted(values)[int(len(values) * 0.95)],
                        "p99": sorted(values)[int(len(values) * 0.99)]
                    }

            return summary

class AsyncAlertManager:
    """Manage alert rules and notifications"""

    def __init__(self):
        self.alert_rules: Dict[str, AlertRule] = {}
        self.alert_history: List[Dict[str, Any]] = []
        self._notification_handlers: Dict[str, Callable] = {}

    def add_alert_rule(self, rule: AlertRule):
        """Add an alert rule"""
        self.alert_rules[rule.name] = rule

    def register_notification_handler(self, channel: str, handler: Callable):
        """Register a notification handler"""
        self._notification_handlers[channel] = handler

    async def check_alerts(self, metrics_summary: Dict[str, Any]):
        """Check alert conditions against metrics"""
        for rule_name, rule in self.alert_rules.items():
            if not rule.enabled:
                continue

            try:
                triggered = await self._evaluate_alert_rule(rule, metrics_summary)
                if triggered:
                    await self._trigger_alert(rule, metrics_summary)
            except Exception as e:
                logger.error(f"Alert evaluation error for {rule_name}: {e}")

    async def _evaluate_alert_rule(self, rule: AlertRule, metrics_summary: Dict[str, Any]) -> bool:
        """Evaluate if an alert rule is triggered"""
        # Simple evaluation - can be extended with more complex conditions
        if rule.metric_name in metrics_summary["gauges"]:
            value = metrics_summary["gauges"][rule.metric_name]
            return value > rule.threshold
        elif rule.metric_name in metrics_summary["counters"]:
            value = metrics_summary["counters"][rule.metric_name]
            return value > rule.threshold

        return False

    async def _trigger_alert(self, rule: AlertRule, metrics_summary: Dict[str, Any]):
        """Trigger an alert notification"""
        alert = {
            "rule_name": rule.name,
            "severity": rule.severity.name,
            "metric_name": rule.metric_name,
            "threshold": rule.threshold,
            "current_value": metrics_summary.get("gauges", {}).get(rule.metric_name, 0),
            "timestamp": time.time(),
            "message": f"Alert triggered: {rule.name} - {rule.metric_name} exceeded threshold"
        }

        self.alert_history.append(alert)

        # Send notifications
        for channel in rule.notification_channels:
            handler = self._notification_handlers.get(channel)
            if handler:
                try:
                    await handler(alert)
                except Exception as e:
                    logger.error(f"Notification error for {channel}: {e}")

class AsyncLoggingService:
    """
    High-performance async logging service with features:
    - Structured logging with async file I/O
    - Performance metrics collection
    - Alert management and notifications
    - Log aggregation and querying
    - Real-time monitoring
    """

    def __init__(self, config: Optional[LoggingConfig] = None):
        self.config = config or LoggingConfig()
        self.log_handler = AsyncLogHandler(self.config)
        self.metrics_collector = AsyncMetricsCollector()
        self.alert_manager = AsyncAlertManager()
        self._request_context = {}
        self._monitoring_task: Optional[asyncio.Task] = None

    async def log(
        self,
        level: LogLevel,
        category: LogCategory,
        message: str,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        session_id: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None,
        execution_time: Optional[float] = None,
        include_traceback: bool = False
    ):
        """Log a structured message asynchronously"""
        try:
            # Get current context
            context = self._request_context.get(request_id, {})

            # Create log entry
            log_entry = LogEntry(
                timestamp=time.time(),
                level=level,
                category=category,
                message=message,
                user_id=user_id or context.get('user_id'),
                request_id=request_id or context.get('request_id'),
                session_id=session_id or context.get('session_id'),
                ip_address=context.get('ip_address'),
                user_agent=context.get('user_agent'),
                extra_data=extra_data,
                execution_time=execution_time,
                memory_usage=self._get_memory_usage(),
                cpu_usage=self._get_cpu_usage()
            )

            # Add traceback if requested and available
            if include_traceback and level in [LogLevel.ERROR, LogLevel.CRITICAL]:
                log_entry.traceback = traceback.format_exc()

            # Handle the log entry
            await self.log_handler.handle_log(log_entry)

            # Record metrics
            await self.metrics_collector.increment_counter(
                f"logs.{category.value}.{level.name.lower()}",
                tags={"level": level.name, "category": category.value}
            )

            if execution_time:
                await self.metrics_collector.record_histogram(
                    f"execution_time.{category.value}",
                    execution_time,
                    tags={"category": category.value}
                )

        except Exception as e:
            # Fallback to standard logging
            logger.error(f"Async logging error: {e}")
            logger.log(level.value, message, extra={'category': category.value})

    async def debug(self, category: LogCategory, message: str, **kwargs):
        """Log debug message"""
        await self.log(LogLevel.DEBUG, category, message, **kwargs)

    async def info(self, category: LogCategory, message: str, **kwargs):
        """Log info message"""
        await self.log(LogLevel.INFO, category, message, **kwargs)

    async def warning(self, category: LogCategory, message: str, **kwargs):
        """Log warning message"""
        await self.log(LogLevel.WARNING, category, message, **kwargs)

    async def error(self, category: LogCategory, message: str, **kwargs):
        """Log error message"""
        await self.log(LogLevel.ERROR, category, message, **kwargs)

    async def critical(self, category: LogCategory, message: str, **kwargs):
        """Log critical message"""
        await self.log(LogLevel.CRITICAL, category, message, **kwargs)

    @asynccontextmanager
    async def log_execution_time(self, category: LogCategory, operation: str, **log_kwargs):
        """Context manager for logging execution time"""
        start_time = time.time()
        try:
            yield
        except Exception as e:
            execution_time = time.time() - start_time
            await self.error(
                category,
                f"Operation failed: {operation}",
                execution_time=execution_time,
                extra_data={"error": str(e), "operation": operation},
                include_traceback=True,
                **log_kwargs
            )
            raise
        else:
            execution_time = time.time() - start_time
            await self.info(
                category,
                f"Operation completed: {operation}",
                execution_time=execution_time,
                extra_data={"operation": operation},
                **log_kwargs
            )

    def set_request_context(self, request_id: str, context: Dict[str, Any]):
        """Set request context for correlation"""
        self._request_context[request_id] = context

    def clear_request_context(self, request_id: str):
        """Clear request context"""
        self._request_context.pop(request_id, None)

    async def query_logs(
        self,
        category: Optional[LogCategory] = None,
        level: Optional[LogLevel] = None,
        user_id: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Query logs from cache"""
        try:
            cache_key = "recent_logs"
            recent_logs = await cache_service.get(cache_key, default=[])

            # Filter logs
            filtered_logs = []
            for log_data in recent_logs:
                log = LogEntry(**log_data)

                # Apply filters
                if category and log.category != category:
                    continue
                if level and log.level != level:
                    continue
                if user_id and log.user_id != user_id:
                    continue
                if start_time and log.timestamp < start_time:
                    continue
                if end_time and log.timestamp > end_time:
                    continue

                filtered_logs.append(log_data)

                if len(filtered_logs) >= limit:
                    break

            return filtered_logs[-limit:]  # Return most recent logs

        except Exception as e:
            logger.error(f"Log query error: {e}")
            return []

    async def get_metrics_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary"""
        return await self.metrics_collector.get_metrics_summary()

    async def start_monitoring(self):
        """Start background monitoring tasks"""
        if self._monitoring_task and not self._monitoring_task.done():
            return

        self._monitoring_task = asyncio.create_task(self._monitoring_loop())

    async def stop_monitoring(self):
        """Stop background monitoring tasks"""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

    async def _monitoring_loop(self):
        """Background monitoring loop"""
        while True:
            try:
                # Get metrics summary
                metrics_summary = await self.metrics_collector.get_metrics_summary()

                # Check alerts
                if self.config.enable_alerts:
                    await self.alert_manager.check_alerts(metrics_summary)

                # Log system metrics
                await self._log_system_metrics()

                # Sleep for monitoring interval
                await asyncio.sleep(30)  # Monitor every 30 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(5)

    async def _log_system_metrics(self):
        """Log system performance metrics"""
        try:
            memory_usage = self._get_memory_usage()
            cpu_usage = self._get_cpu_usage()

            await self.metrics_collector.set_gauge("system.memory_usage", memory_usage)
            await self.metrics_collector.set_gauge("system.cpu_usage", cpu_usage)

            # Log if metrics are high
            if memory_usage and memory_usage > 80:
                await self.warning(
                    LogCategory.SYSTEM,
                    f"High memory usage: {memory_usage:.1f}%",
                    extra_data={"memory_usage": memory_usage}
                )

            if cpu_usage and cpu_usage > 80:
                await self.warning(
                    LogCategory.SYSTEM,
                    f"High CPU usage: {cpu_usage:.1f}%",
                    extra_data={"cpu_usage": cpu_usage}
                )

        except Exception as e:
            logger.error(f"System metrics logging error: {e}")

    def _get_memory_usage(self) -> Optional[float]:
        """Get current memory usage percentage"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_percent()
        except ImportError:
            return None
        except Exception:
            return None

    def _get_cpu_usage(self) -> Optional[float]:
        """Get current CPU usage percentage"""
        try:
            import psutil
            return psutil.cpu_percent(interval=1)
        except ImportError:
            return None
        except Exception:
            return None

    async def shutdown(self):
        """Shutdown the logging service"""
        await self.stop_monitoring()
        await self.log_handler.stop()

# Global logging service instance
logging_service = AsyncLoggingService()

# Convenience functions
async def log_info(category: LogCategory, message: str, **kwargs):
    """Convenience function for info logging"""
    await logging_service.info(category, message, **kwargs)

async def log_error(category: LogCategory, message: str, **kwargs):
    """Convenience function for error logging"""
    await logging_service.error(category, message, **kwargs)

async def log_warning(category: LogCategory, message: str, **kwargs):
    """Convenience function for warning logging"""
    await logging_service.warning(category, message, **kwargs)

@asynccontextmanager
async def log_execution(category: LogCategory, operation: str, **kwargs):
    """Context manager for execution time logging"""
    async with logging_service.log_execution_time(category, operation, **kwargs):
        yield

# Initialize function
async def init_logging_service(config: Optional[LoggingConfig] = None):
    """Initialize the logging service"""
    try:
        global logging_service
        logging_service = AsyncLoggingService(config)
        await logging_service.start_monitoring()
        logger.info("Async logging service initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize logging service: {e}")
        return False

# Cleanup function
async def cleanup_logging_service():
    """Cleanup the logging service"""
    try:
        await logging_service.shutdown()
        logger.info("Async logging service cleaned up successfully")
    except Exception as e:
        logger.error(f"Failed to cleanup logging service: {e}")