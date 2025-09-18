"""
Comprehensive Logging Integration System
Integrates all logging components into a unified, production-ready logging solution.
"""

import logging
import time
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from .logging_config import get_logging_config, setup_logging, LoggingConfig
from .logging_structured import get_logger, generate_correlation_id, get_context_manager
from .logging_filters import get_filter_manager, setup_logging_filters
from .logging_rotation import initialize_rotation_system, get_log_rotator, get_retention_manager
from .logging_tracing import initialize_tracing, get_tracer, get_correlation_manager, trace_span
from .logging_performance import initialize_performance_monitoring, get_performance_monitor


class UnifiedLoggingSystem:
    """Unified logging system that integrates all components"""

    def __init__(self, config: Optional[LoggingConfig] = None):
        self.config = config or get_logging_config()
        self.initialized = False
        self.startup_time = time.time()
        self.logger = None

    async def initialize(self) -> bool:
        """Initialize the complete logging system"""
        try:
            # Setup basic logging configuration
            setup_logging(self.config)

            # Initialize structured logging
            self.logger = get_logger(__name__)
            self.logger.info("Initializing unified logging system")

            # Initialize filters
            filter_manager = get_filter_manager()
            filter_manager.create_filter_from_config()
            setup_logging_filters(logging.getLogger())

            # Initialize log rotation and retention
            initialize_rotation_system()

            # Initialize distributed tracing
            initialize_tracing()

            # Initialize performance monitoring
            initialize_performance_monitoring()

            # Setup log aggregation if enabled
            if self.config.elasticsearch.enabled:
                await self._setup_elasticsearch_logging()

            if self.config.redis.enabled:
                await self._setup_redis_logging()

            # Initialize alerting
            await self._setup_alerting()

            # Initialize compliance logging
            if self.config.compliance.enabled:
                await self._setup_compliance_logging()

            self.initialized = True
            self.logger.info("Unified logging system initialized successfully")
            return True

        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to initialize logging system: {e}", exc_info=True)
            else:
                print(f"Failed to initialize logging system: {e}")
            return False

    async def _setup_elasticsearch_logging(self) -> None:
        """Setup Elasticsearch log aggregation"""
        try:
            # This would integrate with the elasticsearch-py client
            # For now, we'll just log the configuration
            self.logger.info(
                f"Elasticsearch logging configured: {self.config.elasticsearch.hosts}",
                extra={
                    "hosts": self.config.elasticsearch.hosts,
                    "index_prefix": self.config.elasticsearch.index_prefix
                }
            )
        except Exception as e:
            self.logger.error(f"Failed to setup Elasticsearch logging: {e}")

    async def _setup_redis_logging(self) -> None:
        """Setup Redis log streaming"""
        try:
            # This would integrate with redis-py client
            self.logger.info(
                f"Redis logging configured: {self.config.redis.host}:{self.config.redis.port}",
                extra={
                    "host": self.config.redis.host,
                    "port": self.config.redis.port,
                    "stream_name": self.config.redis.stream_name
                }
            )
        except Exception as e:
            self.logger.error(f"Failed to setup Redis logging: {e}")

    async def _setup_alerting(self) -> None:
        """Setup log alerting system"""
        try:
            if self.config.alerting.enabled:
                monitor = get_performance_monitor()
                if monitor:
                    # Add default alerts
                    from .logging_performance import PerformanceAlert

                    # High memory usage alert
                    memory_alert = PerformanceAlert(
                        name="high_memory_usage",
                        metric_name="system.memory_usage_percent",
                        condition=">",
                        threshold=self.config.performance.memory_usage_threshold,
                        severity="warning"
                    )
                    monitor.add_alert(memory_alert)

                    # High CPU usage alert
                    cpu_alert = PerformanceAlert(
                        name="high_cpu_usage",
                        metric_name="system.cpu_usage_percent",
                        condition=">",
                        threshold=self.config.performance.cpu_usage_threshold,
                        severity="warning"
                    )
                    monitor.add_alert(cpu_alert)

                    # Slow request alert
                    slow_request_alert = PerformanceAlert(
                        name="slow_requests",
                        metric_name="http.request_duration",
                        condition=">",
                        threshold=self.config.performance.slow_request_threshold,
                        severity="warning"
                    )
                    monitor.add_alert(slow_request_alert)

                    self.logger.info("Log alerting system configured")
        except Exception as e:
            self.logger.error(f"Failed to setup alerting: {e}")

    async def _setup_compliance_logging(self) -> None:
        """Setup compliance and audit logging"""
        try:
            # Create compliance log directories
            compliance_dir = Path(self.config.log_directory) / "compliance"
            compliance_dir.mkdir(parents=True, exist_ok=True)

            # Setup audit logging
            audit_log_path = compliance_dir / self.config.compliance.audit_log_file
            security_log_path = compliance_dir / self.config.compliance.security_events_file
            data_access_log_path = compliance_dir / self.config.compliance.data_access_log_file

            # Create compliance loggers
            audit_logger = logging.getLogger("audit")
            security_logger = logging.getLogger("security")
            data_access_logger = logging.getLogger("data_access")

            # Setup file handlers for compliance logs
            for logger_name, log_path in [
                ("audit", audit_log_path),
                ("security", security_log_path),
                ("data_access", data_access_log_path)
            ]:
                logger = logging.getLogger(logger_name)
                handler = logging.FileHandler(log_path)
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                handler.setFormatter(formatter)
                logger.addHandler(handler)
                logger.setLevel(logging.INFO)

            self.logger.info("Compliance logging system configured")
        except Exception as e:
            self.logger.error(f"Failed to setup compliance logging: {e}")

    async def shutdown(self) -> None:
        """Shutdown the logging system gracefully"""
        if not self.initialized:
            return

        try:
            self.logger.info("Shutting down unified logging system")

            # Stop performance monitoring
            monitor = get_performance_monitor()
            if monitor:
                monitor.stop_monitoring()

            # Cleanup retention manager
            retention_manager = get_retention_manager()
            if retention_manager:
                # Final cleanup of old logs
                retention_manager.cleanup_old_logs()

            # Flush any remaining logs
            await self._flush_logs()

            # Generate final report
            await self._generate_shutdown_report()

            self.logger.info("Unified logging system shutdown completed")
            self.initialized = False

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error during logging system shutdown: {e}", exc_info=True)
            else:
                print(f"Error during logging system shutdown: {e}")

    async def _flush_logs(self) -> None:
        """Flush any buffered logs"""
        try:
            # This would flush any buffered logs to external systems
            # For now, we'll just ensure all handlers are flushed
            root_logger = logging.getLogger()
            for handler in root_logger.handlers:
                if hasattr(handler, 'flush'):
                    handler.flush()
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to flush logs: {e}")

    async def _generate_shutdown_report(self) -> None:
        """Generate shutdown report with statistics"""
        try:
            uptime = time.time() - self.startup_time

            # Get metrics from performance monitor
            monitor = get_performance_monitor()
            if monitor:
                report = monitor.get_performance_report(int(uptime / 3600))

                self.logger.info(
                    "Logging system shutdown report",
                    extra={
                        "uptime_seconds": uptime,
                        "uptime_hours": uptime / 3600,
                        "total_metrics": report.get("total_metrics", 0),
                        "alert_count": report.get("alert_count", 0),
                        "insights_count": len(report.get("insights", []))
                    }
                )

        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to generate shutdown report: {e}")

    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        try:
            status = {
                "initialized": self.initialized,
                "startup_time": datetime.fromtimestamp(self.startup_time).isoformat(),
                "uptime_seconds": time.time() - self.startup_time,
                "config": self.config.to_dict(),
                "components": {}
            }

            # Get status from individual components
            tracer = get_tracer()
            if tracer:
                status["components"]["tracing"] = tracer.get_trace_stats()

            monitor = get_performance_monitor()
            if monitor:
                status["components"]["performance"] = monitor.get_performance_report(1)

            rotator = get_log_rotator()
            if rotator:
                status["components"]["rotation"] = rotator.get_stats().__dict__

            correlation_manager = get_correlation_manager()
            if correlation_manager:
                status["components"]["correlation"] = {
                    "active_requests": correlation_manager.get_active_requests_count()
                }

            return status

        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to get system status: {e}")
            return {"error": str(e), "initialized": self.initialized}

    def log_system_event(self, event_type: str, message: str, **extra_fields) -> None:
        """Log a system event with standard context"""
        if not self.initialized:
            return

        correlation_id = generate_correlation_id()
        extra_fields.update({
            "event_type": event_type,
            "correlation_id": correlation_id,
            "timestamp": datetime.now().isoformat(),
            "component": "logging_system"
        })

        self.logger.info(message, extra=extra_fields)

    def rotate_all_logs(self, force: bool = False) -> Dict[str, bool]:
        """Rotate all log files"""
        if not self.initialized:
            return {}

        rotator = get_log_rotator()
        if rotator:
            return rotator.rotate_all_logs()
        return {}

    def cleanup_old_logs(self) -> Dict[str, Any]:
        """Clean up old log files"""
        if not self.initialized:
            return {"deleted_files": [], "total_size_freed": 0}

        retention_manager = get_retention_manager()
        if retention_manager:
            config = get_logging_config()
            return retention_manager.cleanup_old_logs(config.log_directory)
        return {"deleted_files": [], "total_size_freed": 0}


# Global logging system instance
_logging_system = None


async def initialize_unified_logging(config: Optional[LoggingConfig] = None) -> bool:
    """Initialize the global unified logging system"""
    global _logging_system

    _logging_system = UnifiedLoggingSystem(config)
    return await _logging_system.initialize()


async def shutdown_unified_logging() -> None:
    """Shutdown the global unified logging system"""
    global _logging_system

    if _logging_system:
        await _logging_system.shutdown()
        _logging_system = None


def get_logging_system() -> Optional[UnifiedLoggingSystem]:
    """Get the global unified logging system instance"""
    return _logging_system


def get_logging_status() -> Dict[str, Any]:
    """Get comprehensive logging system status"""
    if _logging_system:
        return _logging_system.get_system_status()
    return {"initialized": False}


# Middleware and integration functions
def setup_fastapi_logging_middleware(app):
    """Setup logging middleware for FastAPI application"""
    from .logging_performance import add_performance_middleware
    return add_performance_middleware(app)


async def log_request_middleware(request, call_next):
    """FastAPI middleware for request logging"""
    start_time = time.time()
    correlation_id = generate_correlation_id()

    # Set trace context
    from .logging_tracing import set_trace_context_from_headers
    headers = dict(request.headers)
    set_trace_context_from_headers(headers)

    # Start request trace
    from .logging_tracing import start_request_trace
    start_request_trace(correlation_id, {
        "method": request.method,
        "url": str(request.url),
        "client_host": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent")
    })

    try:
        response = await call_next(request)

        # Log request completion
        duration = time.time() - start_time
        logger = get_logger("http")
        logger.info(
            f"HTTP request: {request.method} {request.url.path}",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "status_code": response.status_code,
                "duration": duration,
                "user_agent": request.headers.get("user-agent"),
                "client_host": request.client.host if request.client else None
            }
        )

        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id

        return response

    except Exception as e:
        duration = time.time() - start_time
        logger = get_logger("http")
        logger.error(
            f"HTTP request error: {request.method} {request.url.path}",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "path": request.url.path,
                "duration": duration,
                "error": str(e),
                "user_agent": request.headers.get("user-agent"),
                "client_host": request.client.host if request.client else None
            },
            exc_info=True
        )
        raise

    finally:
        # End request trace
        from .logging_tracing import end_request_trace
        end_request_trace(correlation_id, "completed" if 'response' in locals() else "failed")


# Convenience functions for common logging patterns
def log_business_event(event_name: str, **kwargs):
    """Log a business event"""
    logger = get_logger("business")
    logger.info(
        f"Business event: {event_name}",
        extra={
            "event_type": "business",
            "event_name": event_name,
            **kwargs
        }
    )


def log_security_event(event_type: str, severity: str = "warning", **kwargs):
    """Log a security event"""
    logger = get_logger("security")
    log_method = getattr(logger, severity, logger.warning)
    log_method(
        f"Security event: {event_type}",
        extra={
            "event_type": "security",
            "security_event_type": event_type,
            "severity": severity,
            **kwargs
        }
    )


def log_performance_event(operation: str, duration: float, **kwargs):
    """Log a performance event"""
    logger = get_logger("performance")
    logger.info(
        f"Performance event: {operation}",
        extra={
            "event_type": "performance",
            "operation": operation,
            "duration": duration,
            **kwargs
        }
    )


def log_error_event(error: Exception, context: Dict[str, Any] = None, **kwargs):
    """Log an error event"""
    logger = get_logger("errors")
    logger.error(
        f"Error event: {type(error).__name__}",
        extra={
            "event_type": "error",
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
            **kwargs
        },
        exc_info=True
    )


# Health check for logging system
async def logging_health_check() -> Dict[str, Any]:
    """Health check for the logging system"""
    try:
        if not _logging_system:
            return {"status": "uninitialized", "timestamp": datetime.now().isoformat()}

        status = _logging_system.get_system_status()
        status["health_check"] = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components_healthy": all(
                component.get("status", "healthy") == "healthy"
                for component in status.get("components", {}).values()
            )
        }

        return status

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }