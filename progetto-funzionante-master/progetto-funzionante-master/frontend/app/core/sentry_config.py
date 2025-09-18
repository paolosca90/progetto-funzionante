"""
Comprehensive Sentry Error Tracking Configuration
Production-ready error monitoring with custom contexts, breadcrumbs, and performance tracking
"""

import os
import logging
import json
import threading
import time
from datetime import datetime, UTC
from typing import Optional, Dict, Any, List, Union, Callable
from enum import Enum
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.httpx import HttpxIntegration
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
from sentry_sdk.integrations.logging import LoggingIntegration, ignore_logger
from sentry_sdk.integrations.starlette import StarletteIntegration
from sentry_sdk.integrations.threading import ThreadingIntegration
from sentry_sdk import capture_message, capture_exception, configure_scope
from sentry_sdk.tracing import Transaction
from sentry_sdk.metrics import Metrics

from config.settings import settings


class ErrorSeverity(Enum):
    """Error severity levels for Sentry classification"""
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"


class ErrorCategory(Enum):
    """Error categories for better organization and filtering"""
    DATABASE = "database"
    API = "api"
    AUTHENTICATION = "authentication"
    VALIDATION = "validation"
    BUSINESS_LOGIC = "business_logic"
    EXTERNAL_SERVICE = "external_service"
    SYSTEM = "system"
    PERFORMANCE = "performance"


class SentryConfig:
    """Centralized Sentry configuration management"""

    def __init__(self):
        self.initialized = False
        self.metrics_aggregator = None
        self.performance_monitor = None
        self.error_classifier = None
        self.custom_handlers = {}

    def initialize(self) -> None:
        """Initialize Sentry SDK with comprehensive configuration"""
        if self.initialized:
            return

        sentry_dsn = settings.SENTRY_DSN or os.getenv("SENTRY_DSN")
        if not sentry_dsn:
            logging.warning("SENTRY_DSN not configured - error tracking disabled")
            return

        # Configure sampling rates
        traces_sample_rate = float(settings.SENTRY_TRACES_SAMPLE_RATE or os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.2"))
        profiles_sample_rate = float(settings.SENTRY_PROFILES_SAMPLE_RATE or os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.1"))

        # Performance monitoring settings
        enable_performance_monitoring = settings.ENABLE_PERFORMANCE_MONITORING or os.getenv("ENABLE_PERFORMANCE_MONITORING", "true").lower() == "true"

        # Create Sentry integrations
        integrations = self._create_integrations()

        # Initialize Sentry SDK
        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=integrations,
            traces_sample_rate=traces_sample_rate,
            profiles_sample_rate=profiles_sample_rate,
            environment=settings.ENVIRONMENT or os.getenv("ENVIRONMENT", "development"),
            release=self._get_release_version(),
            debug=settings.ENVIRONMENT == "development",
            send_default_pii=False,
            server_name=os.getenv("HOSTNAME", "unknown"),
            before_send=self._before_send,
            before_breadcrumb=self._before_breadcrumb,
            auto_enabling_integrations=False,
            _experiments={
                "profiles_sample_rate": profiles_sample_rate,
            }
        )

        # Initialize additional components
        self._initialize_metrics()
        self._initialize_performance_monitor()
        self._initialize_error_classifier()

        # Configure logging integration
        self._configure_logging()

        self.initialized = True
        logging.info(f"Sentry initialized for environment: {settings.ENVIRONMENT}")

    def _create_integrations(self) -> List:
        """Create Sentry integrations for the FastAPI application"""
        return [
            # FastAPI-specific integrations
            FastApiIntegration(),
            StarletteIntegration(),

            # Database integrations
            SqlalchemyIntegration(),
            RedisIntegration(),

            # HTTP client integrations
            HttpxIntegration(),
            AioHttpIntegration(),

            # Logging integration
            LoggingIntegration(
                level=logging.INFO,
                event_level=logging.WARNING
            ),

            # Threading support
            ThreadingIntegration(propagate_hub=True),
        ]

    def _get_release_version(self) -> str:
        """Get release version from environment or git"""
        if version := os.getenv("RELEASE_VERSION"):
            return version

        if version := os.getenv("GIT_COMMIT_SHA"):
            return f"trading-system@{version[:8]}"

        # Try to get from git if available
        try:
            import subprocess
            result = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                                 capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return f"trading-system@{result.stdout.strip()}"
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            pass

        return "trading-system@unknown"

    def _before_send(self, event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process events before sending to Sentry"""
        if not event:
            return None

        # Add custom classification
        if self.error_classifier:
            event = self.error_classifier.classify_error(event, hint)

        # Filter out sensitive data
        event = self._filter_sensitive_data(event)

        # Add environment context
        event.setdefault("contexts", {})
        event["contexts"]["app"] = {
            "environment": settings.ENVIRONMENT,
            "version": self._get_release_version(),
            "database_connected": getattr(settings, 'DATABASE_URL', False),
            "oanda_configured": bool(settings.OANDA_API_KEY),
        }

        # Add performance metrics if available
        if self.metrics_aggregator:
            event["contexts"]["metrics"] = self.metrics_aggregator.get_summary()

        return event

    def _before_breadcrumb(self, breadcrumb: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process breadcrumbs before adding to Sentry"""
        if not breadcrumb:
            return None

        # Filter sensitive data from breadcrumbs
        breadcrumb = self._filter_sensitive_data(breadcrumb)

        # Add timestamp if missing
        if "timestamp" not in breadcrumb:
            breadcrumb["timestamp"] = datetime.now(UTC).isoformat()

        return breadcrumb

    def _filter_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive data from Sentry events"""
        sensitive_keys = {
            "password", "secret", "token", "api_key", "jwt", "authorization",
            "credit_card", "ssn", "social_security", "personal_id"
        }

        if isinstance(data, dict):
            return {
                key: self._filter_sensitive_data(value)
                if not any(sensitive in key.lower() for sensitive in sensitive_keys)
                else "[FILTERED]"
                for key, value in data.items()
            }
        elif isinstance(data, list):
            return [self._filter_sensitive_data(item) for item in data]
        else:
            return data

    def _initialize_metrics(self) -> None:
        """Initialize metrics collection"""
        try:
            from sentry_sdk.metrics import Metrics
            self.metrics_aggregator = MetricsAggregator()
        except ImportError:
            logging.warning("Sentry metrics not available")

    def _initialize_performance_monitor(self) -> None:
        """Initialize performance monitoring"""
        self.performance_monitor = PerformanceMonitor()

    def _initialize_error_classifier(self) -> None:
        """Initialize error classification system"""
        self.error_classifier = ErrorClassifier()

    def _configure_logging(self) -> None:
        """Configure logging integration with Sentry"""
        # Ignore certain loggers to prevent noise
        ignore_logger("uvicorn.access")
        ignore_logger("uvicorn.error")

    def capture_error(
        self,
        error: Exception,
        level: ErrorSeverity = ErrorSeverity.ERROR,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        user_context: Optional[Dict[str, Any]] = None,
        tags: Optional[Dict[str, str]] = None,
        extra_data: Optional[Dict[str, Any]] = None,
        fingerprint: Optional[List[str]] = None
    ) -> str:
        """Capture an error with enhanced context"""
        if not self.initialized:
            self.initialize()

        with configure_scope() as scope:
            # Set user context
            if user_context:
                scope.user.update(user_context)

            # Set tags
            if tags:
                scope.set_tags(tags)

            # Set extra data
            if extra_data:
                scope.set_extra("custom_data", extra_data)

            # Set level
            scope.level = level.value

            # Set fingerprint for grouping
            if fingerprint:
                scope.fingerprint = fingerprint

        # Capture the exception
        event_id = capture_exception(error)

        # Log the error
        logging.error(f"Captured error in Sentry: {event_id} - {error}")

        return event_id

    def capture_message(
        self,
        message: str,
        level: ErrorSeverity = ErrorSeverity.INFO,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        tags: Optional[Dict[str, str]] = None,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """Capture a custom message"""
        if not self.initialized:
            self.initialize()

        with configure_scope() as scope:
            # Set tags
            if tags:
                scope.set_tags(tags)

            # Set extra data
            if extra_data:
                scope.set_extra("custom_data", extra_data)

            # Set level
            scope.level = level.value

        # Capture the message
        event_id = capture_message(message, level=level.value)

        return event_id

    def add_breadcrumb(
        self,
        message: str,
        category: str = "default",
        level: ErrorSeverity = ErrorSeverity.INFO,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add a breadcrumb for context"""
        if not self.initialized:
            return

        sentry_sdk.add_breadcrumb(
            message=message,
            category=category,
            level=level.value,
            data=data or {}
        )

    def set_user_context(self, user_data: Dict[str, Any]) -> None:
        """Set user context for all subsequent events"""
        if not self.initialized:
            return

        with configure_scope() as scope:
            scope.user.update(user_data)


class MetricsAggregator:
    """Aggregate and report custom metrics"""

    def __init__(self):
        self.metrics = {}
        self.lock = threading.Lock()

    def increment(self, metric_name: str, value: int = 1, tags: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric"""
        key = f"{metric_name}:{json.dumps(tags or {})}"
        with self.lock:
            self.metrics[key] = self.metrics.get(key, 0) + value

    def timing(self, metric_name: str, duration: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record a timing metric"""
        key = f"{metric_name}_timing:{json.dumps(tags or {})}"
        with self.lock:
            if key not in self.metrics:
                self.metrics[key] = []
            self.metrics[key].append(duration)

    def gauge(self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Set a gauge metric"""
        key = f"{metric_name}_gauge:{json.dumps(tags or {})}"
        with self.lock:
            self.metrics[key] = value

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary for reporting"""
        with self.lock:
            summary = {}
            for key, value in self.metrics.items():
                if isinstance(value, list):
                    summary[key] = {
                        "count": len(value),
                        "avg": sum(value) / len(value) if value else 0,
                        "min": min(value) if value else 0,
                        "max": max(value) if value else 0
                    }
                else:
                    summary[key] = value
            return summary


class PerformanceMonitor:
    """Monitor application performance metrics"""

    def __init__(self):
        self.request_times = []
        self.database_query_times = []
        self.api_call_times = []

    def record_request_time(self, duration: float, endpoint: str) -> None:
        """Record API request time"""
        self.request_times.append({
            "duration": duration,
            "endpoint": endpoint,
            "timestamp": datetime.now(UTC).isoformat()
        })

    def record_database_query(self, duration: float, query_type: str) -> None:
        """Record database query time"""
        self.database_query_times.append({
            "duration": duration,
            "query_type": query_type,
            "timestamp": datetime.now(UTC).isoformat()
        })

    def record_api_call(self, duration: float, service: str) -> None:
        """Record external API call time"""
        self.api_call_times.append({
            "duration": duration,
            "service": service,
            "timestamp": datetime.now(UTC).isoformat()
        })

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        return {
            "requests": self._calculate_stats(self.request_times),
            "database_queries": self._calculate_stats(self.database_query_times),
            "api_calls": self._calculate_stats(self.api_call_times)
        }

    def _calculate_stats(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate statistics for performance data"""
        if not data:
            return {"count": 0}

        durations = [item["duration"] for item in data]
        return {
            "count": len(durations),
            "avg_duration": sum(durations) / len(durations),
            "min_duration": min(durations),
            "max_duration": max(durations)
        }


class ErrorClassifier:
    """Classify errors for better organization and analysis"""

    def __init__(self):
        self.classification_rules = self._build_classification_rules()

    def _build_classification_rules(self) -> Dict:
        """Build error classification rules"""
        return {
            "database": {
                "exceptions": ["SQLAlchemyError", "DBAPIError", "ConnectionError"],
                "keywords": ["connection", "timeout", "database", "query", "sql"]
            },
            "api": {
                "exceptions": ["HTTPError", "RequestError", "ConnectionError"],
                "keywords": ["http", "request", "response", "api", "endpoint"]
            },
            "authentication": {
                "exceptions": ["JWTError", "AuthenticationError", "ValidationError"],
                "keywords": ["auth", "token", "jwt", "login", "password"]
            },
            "validation": {
                "exceptions": ["ValidationError", "ValueError", "TypeError"],
                "keywords": ["validation", "invalid", "format", "required", "schema"]
            },
            "external_service": {
                "exceptions": ["HTTPError", "TimeoutError", "ConnectionError"],
                "keywords": ["oanda", "external", "service", "third_party"]
            }
        }

    def classify_error(self, event: Dict[str, Any], hint: Dict[str, Any]) -> Dict[str, Any]:
        """Classify error and add metadata"""
        exception = hint.get("exc_info")
        if not exception:
            return event

        exc_type, exc_value, exc_traceback = exception
        exc_name = exc_type.__name__ if exc_type else "Unknown"

        # Classify based on exception type and message
        category = self._determine_category(exc_name, str(exc_value))

        # Add classification to event
        event.setdefault("tags", {})
        event["tags"]["error_category"] = category
        event["tags"]["error_type"] = exc_name

        # Add severity based on exception type
        severity = self._determine_severity(exc_name, exc_value)
        event["level"] = severity

        return event

    def _determine_category(self, exc_name: str, exc_message: str) -> str:
        """Determine error category"""
        exc_lower = exc_name.lower()
        msg_lower = exc_message.lower()

        for category, rules in self.classification_rules.items():
            # Check exception names
            for exception in rules.get("exceptions", []):
                if exception.lower() in exc_lower:
                    return category

            # Check message keywords
            for keyword in rules.get("keywords", []):
                if keyword in msg_lower:
                    return category

        return "business_logic"

    def _determine_severity(self, exc_name: str, exc_value) -> str:
        """Determine error severity"""
        critical_exceptions = ["SystemExit", "KeyboardInterrupt", "MemoryError"]
        error_exceptions = ["RuntimeError", "TypeError", "ValueError", "KeyError", "AttributeError"]

        if any(exc in exc_name for exc in critical_exceptions):
            return "critical"
        elif any(exc in exc_name for exc in error_exceptions):
            return "error"
        else:
            return "warning"


# Global Sentry instance
sentry_config = SentryConfig()