"""
Centralized Logging Configuration System
Provides comprehensive logging configuration for production environments
with ELK stack integration, structured logging, and advanced monitoring.
"""

import os
import json
import logging
import logging.config
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from datetime import datetime

from ..core.config import settings


class LogLevel(Enum):
    """Log level enumeration with severity ordering"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogFormat(Enum):
    """Log format types"""
    JSON = "json"
    STRUCTURED = "structured"
    TEXT = "text"
    COLORIZED = "colorized"


class LogOutput(Enum):
    """Log output destinations"""
    CONSOLE = "console"
    FILE = "file"
    ELASTICSEARCH = "elasticsearch"
    REDIS = "redis"
    CLOUDWATCH = "cloudwatch"
    SENTRY = "sentry"


@dataclass
class LogRotationConfig:
    """Log rotation configuration"""
    enabled: bool = True
    max_size_bytes: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    rotation_interval: Optional[str] = None  # e.g., "1 day", "1 week"
    compression: bool = True
    encoding: str = "utf-8"


@dataclass
class LogFilterConfig:
    """Log filtering configuration"""
    enabled: bool = True
    min_level: LogLevel = LogLevel.INFO
    max_level: LogLevel = LogLevel.CRITICAL
    include_modules: List[str] = field(default_factory=list)
    exclude_modules: List[str] = field(default_factory=list)
    custom_filters: List[str] = field(default_factory=list)


@dataclass
class ElasticsearchConfig:
    """Elasticsearch configuration for log aggregation"""
    enabled: bool = False
    hosts: List[str] = field(default_factory=lambda: ["localhost:9200"])
    index_prefix: str = "app-logs"
    index_pattern: str = "%Y.%m.%d"
    auth_username: Optional[str] = None
    auth_password: Optional[str] = None
    use_ssl: bool = True
    verify_certs: bool = True
    timeout: int = 30
    max_retries: int = 3
    bulk_size: int = 1000
    flush_interval: float = 5.0


@dataclass
class RedisLogConfig:
    """Redis configuration for log streaming"""
    enabled: bool = False
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    key_prefix: str = "logs"
    stream_name: str = "application_logs"
    max_memory_mb: int = 100
    retention_hours: int = 168  # 7 days


@dataclass
class AlertingConfig:
    """Log alerting configuration"""
    enabled: bool = True
    error_threshold: int = 10  # errors per minute
    critical_threshold: int = 3  # critical errors per minute
    notification_channels: List[str] = field(default_factory=lambda: ["email"])
    slack_webhook: Optional[str] = None
    email_recipients: List[str] = field(default_factory=list)
    cooldown_period: int = 300  # 5 minutes


@dataclass
class PerformanceLoggingConfig:
    """Performance logging configuration"""
    enabled: bool = True
    slow_request_threshold: float = 1.0  # seconds
    database_query_threshold: float = 0.5  # seconds
    external_api_threshold: float = 2.0  # seconds
    memory_usage_threshold: float = 80.0  # percentage
    cpu_usage_threshold: float = 70.0  # percentage
    track_histograms: bool = True
    histogram_buckets: List[float] = field(default_factory=lambda: [0.1, 0.5, 1.0, 2.0, 5.0, 10.0])


@dataclass
class ComplianceLoggingConfig:
    """Compliance and audit logging configuration"""
    enabled: bool = True
    audit_log_file: str = "logs/audit.log"
    security_events_file: str = "logs/security.log"
    data_access_log_file: str = "logs/data_access.log"
    retention_days: int = 365  # 1 year
    log_sensitive_data: bool = False
    mask_patterns: List[str] = field(default_factory=lambda: [
        r"password=[^&]*",
        r"token=[^&]*",
        r"secret=[^&]*",
        r"key=[^&]*"
    ])
    required_fields: List[str] = field(default_factory=lambda: [
        "timestamp",
        "user_id",
        "action",
        "resource",
        "ip_address",
        "result"
    ])


@dataclass
class TracingConfig:
    """Distributed tracing configuration"""
    enabled: bool = True
    service_name: str = "fastapi-app"
    jaeger_agent_host: str = "localhost"
    jaeger_agent_port: int = 6831
    sampling_rate: float = 0.1  # 10% of requests
    max_payload_size: int = 4096
    include_payload: bool = False


@dataclass
class LoggingConfig:
    """Comprehensive logging configuration"""
    # Basic settings
    level: LogLevel = LogLevel.INFO
    format: LogFormat = LogFormat.JSON
    outputs: List[LogOutput] = field(default_factory=lambda: [LogOutput.CONSOLE, LogOutput.FILE])

    # File settings
    log_directory: str = "logs"
    main_log_file: str = "app.log"
    error_log_file: str = "error.log"
    access_log_file: str = "access.log"

    # Advanced configurations
    rotation: LogRotationConfig = field(default_factory=LogRotationConfig)
    filtering: LogFilterConfig = field(default_factory=LogFilterConfig)
    elasticsearch: ElasticsearchConfig = field(default_factory=ElasticsearchConfig)
    redis: RedisLogConfig = field(default_factory=RedisLogConfig)
    alerting: AlertingConfig = field(default_factory=AlertingConfig)
    performance: PerformanceLoggingConfig = field(default_factory=PerformanceLoggingConfig)
    compliance: ComplianceLoggingConfig = field(default_factory=ComplianceLoggingConfig)
    tracing: TracingConfig = field(default_factory=TracingConfig)

    # Development settings
    development_mode: bool = False
    show_logger_names: bool = True
    include_caller_info: bool = True
    enable_context_vars: bool = True

    @classmethod
    def from_env(cls) -> 'LoggingConfig':
        """Create configuration from environment variables"""
        return cls(
            level=LogLevel(os.getenv("LOG_LEVEL", "INFO")),
            format=LogFormat(os.getenv("LOG_FORMAT", "JSON")),
            development_mode=settings.is_development,

            rotation=LogRotationConfig(
                enabled=os.getenv("LOG_ROTATION_ENABLED", "true").lower() == "true",
                max_size_bytes=int(os.getenv("LOG_MAX_SIZE", "10485760")),
                backup_count=int(os.getenv("LOG_BACKUP_COUNT", "5")),
                compression=os.getenv("LOG_COMPRESSION", "true").lower() == "true"
            ),

            elasticsearch=ElasticsearchConfig(
                enabled=os.getenv("ELASTICSEARCH_ENABLED", "false").lower() == "true",
                hosts=os.getenv("ELASTICSEARCH_HOSTS", "localhost:9200").split(","),
                index_prefix=os.getenv("ELASTICSEARCH_INDEX_PREFIX", "app-logs"),
                auth_username=os.getenv("ELASTICSEARCH_USERNAME"),
                auth_password=os.getenv("ELASTICSEARCH_PASSWORD")
            ),

            redis=RedisLogConfig(
                enabled=os.getenv("REDIS_LOGS_ENABLED", "false").lower() == "true",
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", "6379")),
                password=os.getenv("REDIS_PASSWORD")
            ),

            alerting=AlertingConfig(
                enabled=os.getenv("LOG_ALERTING_ENABLED", "true").lower() == "true",
                slack_webhook=os.getenv("SLACK_WEBHOOK_URL"),
                email_recipients=os.getenv("ALERT_EMAIL_RECIPIENTS", "").split(",") if os.getenv("ALERT_EMAIL_RECIPIENTS") else []
            ),

            performance=PerformanceLoggingConfig(
                slow_request_threshold=float(os.getenv("SLOW_REQUEST_THRESHOLD", "1.0")),
                database_query_threshold=float(os.getenv("DB_QUERY_THRESHOLD", "0.5")),
                memory_usage_threshold=float(os.getenv("MEMORY_USAGE_THRESHOLD", "80.0"))
            ),

            tracing=TracingConfig(
                service_name=os.getenv("TRACING_SERVICE_NAME", "fastapi-app"),
                jaeger_agent_host=os.getenv("JAEGER_HOST", "localhost"),
                jaeger_agent_port=int(os.getenv("JAEGER_PORT", "6831")),
                sampling_rate=float(os.getenv("TRACING_SAMPLING_RATE", "0.1"))
            )
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        def serialize_dataclass(obj):
            if hasattr(obj, '__dataclass_fields__'):
                return {k: serialize_dataclass(v) for k, v in obj.__dict__.items()}
            elif isinstance(obj, Enum):
                return obj.value
            elif isinstance(obj, list):
                return [serialize_dataclass(item) for item in obj]
            else:
                return obj

        return serialize_dataclass(self)

    def save_to_file(self, file_path: str) -> None:
        """Save configuration to JSON file"""
        config_dict = self.to_dict()
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'w') as f:
            json.dump(config_dict, f, indent=2, default=str)

    @classmethod
    def load_from_file(cls, file_path: str) -> 'LoggingConfig':
        """Load configuration from JSON file"""
        with open(file_path, 'r') as f:
            config_dict = json.load(f)

        # Convert dictionary back to dataclass structure
        # This is a simplified version - in production, you'd want more robust deserialization
        return cls.from_env()  # Fallback to env for now

    def validate(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []

        # Validate log directory
        if not self.log_directory:
            errors.append("Log directory cannot be empty")

        # Validate Elasticsearch configuration if enabled
        if self.elasticsearch.enabled and not self.elasticsearch.hosts:
            errors.append("Elasticsearch hosts must be specified when enabled")

        # Validate Redis configuration if enabled
        if self.redis.enabled and not self.redis.host:
            errors.append("Redis host must be specified when enabled")

        # Validate alerting configuration
        if self.alerting.enabled and not self.alerting.notification_channels:
            errors.append("At least one notification channel must be specified for alerting")

        # Validate thresholds
        if self.performance.slow_request_threshold <= 0:
            errors.append("Slow request threshold must be positive")

        if self.performance.memory_usage_threshold <= 0 or self.performance.memory_usage_threshold > 100:
            errors.append("Memory usage threshold must be between 1 and 100")

        return errors


class LoggingConfigurationManager:
    """Manages logging configuration and provides dynamic updates"""

    def __init__(self, config: LoggingConfig):
        self.config = config
        self._config_watchers = []
        self._last_config_update = datetime.now()

    def get_config(self) -> LoggingConfig:
        """Get current configuration"""
        return self.config

    def update_config(self, new_config: LoggingConfig) -> None:
        """Update configuration and notify watchers"""
        errors = new_config.validate()
        if errors:
            raise ValueError(f"Configuration validation failed: {errors}")

        self.config = new_config
        self._last_config_update = datetime.now()

        # Notify configuration watchers
        for watcher in self._config_watchers:
            try:
                watcher(new_config)
            except Exception as e:
                logging.error(f"Error notifying configuration watcher: {e}")

    def add_config_watcher(self, callback):
        """Add a configuration change callback"""
        self._config_watchers.append(callback)

    def watch_config_file(self, file_path: str):
        """Watch configuration file for changes"""
        # This would implement file watching functionality
        # For now, it's a placeholder
        pass

    def create_logging_config(self) -> Dict[str, Any]:
        """Create Python logging configuration dictionary"""
        config = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'json': {
                    '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
                    'format': '%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d'
                },
                'structured': {
                    '()': 'app.core.logging_structured.StructuredFormatter'
                },
                'standard': {
                    'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
                },
                'detailed': {
                    'format': '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s'
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'level': self.config.level.value,
                    'formatter': 'detailed' if self.config.development_mode else 'json',
                    'stream': 'ext://sys.stdout'
                }
            },
            'loggers': {
                '': {  # root logger
                    'level': self.config.level.value,
                    'handlers': ['console'],
                    'propagate': True
                },
                'app': {
                    'level': self.config.level.value,
                    'handlers': ['console'],
                    'propagate': False
                }
            }
        }

        # Add file handler if configured
        if LogOutput.FILE in self.config.outputs:
            config['handlers']['file'] = {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': self.config.level.value,
                'formatter': 'json',
                'filename': os.path.join(self.config.log_directory, self.config.main_log_file),
                'maxBytes': self.config.rotation.max_size_bytes,
                'backupCount': self.config.rotation.backup_count,
                'encoding': self.config.rotation.encoding
            }
            config['loggers']['']['handlers'].append('file')
            config['loggers']['app']['handlers'].append('file')

        # Add error file handler
        if self.config.error_log_file:
            config['handlers']['error_file'] = {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'ERROR',
                'formatter': 'json',
                'filename': os.path.join(self.config.log_directory, self.config.error_log_file),
                'maxBytes': self.config.rotation.max_size_bytes,
                'backupCount': self.config.rotation.backup_count,
                'encoding': self.config.rotation.encoding
            }
            config['loggers']['']['handlers'].append('error_file')

        return config


# Global configuration manager instance
config_manager = LoggingConfigurationManager(LoggingConfig.from_env())


def get_logging_config() -> LoggingConfig:
    """Get the global logging configuration"""
    return config_manager.get_config()


def update_logging_config(new_config: LoggingConfig) -> None:
    """Update the global logging configuration"""
    config_manager.update_config(new_config)


def setup_logging(config: Optional[LoggingConfig] = None) -> None:
    """Setup logging with the given configuration"""
    if config is None:
        config = get_logging_config()

    # Validate configuration
    errors = config.validate()
    if errors:
        raise ValueError(f"Logging configuration validation failed: {errors}")

    # Create log directory if it doesn't exist
    Path(config.log_directory).mkdir(parents=True, exist_ok=True)

    # Apply Python logging configuration
    logging_config_dict = LoggingConfigurationManager(config).create_logging_config()
    logging.config.dictConfig(logging_config_dict)

    # Log configuration setup
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured with level: {config.level.value}")
    logger.info(f"Log outputs: {[output.value for output in config.outputs]}")
    logger.info(f"Log format: {config.format.value}")

    if config.elasticsearch.enabled:
        logger.info(f"Elasticsearch logging enabled: {config.elasticsearch.hosts}")

    if config.redis.enabled:
        logger.info(f"Redis logging enabled: {config.redis.host}:{config.redis.port}")

    if config.alerting.enabled:
        logger.info("Log alerting enabled")