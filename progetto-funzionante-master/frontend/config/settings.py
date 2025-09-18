"""
Unified Environment-based Configuration Settings for FastAPI Trading System
Production-ready configuration with proper validation and environment-specific overrides
"""

import os
import secrets
from typing import Optional, List, Union, Dict, Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import validator, field_validator, Field
from enum import Enum
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Environment(str, Enum):
    """Application environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class LogLevel(str, Enum):
    """Log levels for the application"""
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"


class SecuritySettings(BaseSettings):
    """Security-related configuration"""
    jwt_secret_key: str = Field(..., description="JWT secret key for token signing")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_access_token_expire_minutes: int = Field(default=30, description="JWT access token expiration in minutes")
    jwt_refresh_token_expire_days: int = Field(default=7, description="JWT refresh token expiration in days")

    @field_validator('jwt_secret_key')
    @classmethod
    def validate_jwt_secret_key(cls, v: str) -> str:
        """Validate JWT secret key is not the default"""
        if v == "your-secret-key-change-this-in-production" or len(v) < 32:
            raise ValueError("JWT secret key must be at least 32 characters and not use the default value")
        return v


class DatabaseSettings(BaseSettings):
    """Database configuration"""
    database_url: str = Field(..., description="Database connection URL")
    database_pool_size: int = Field(default=20, description="Database connection pool size")
    database_max_overflow: int = Field(default=10, description="Database max overflow connections")
    database_pool_timeout: int = Field(default=30, description="Database pool timeout in seconds")
    database_pool_recycle: int = Field(default=3600, description="Database pool recycle time in seconds")

    @field_validator('database_url')
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate database URL format"""
        if not v or not any(v.startswith(prefix) for prefix in ['postgresql://', 'mysql://', 'sqlite:///']):
            raise ValueError("Database URL must be a valid database connection string")
        return v


class CacheSettings(BaseSettings):
    """Redis caching configuration"""
    redis_url: str = Field(default="redis://localhost:6379", description="Redis connection URL")
    redis_password: Optional[str] = Field(default=None, description="Redis password")
    redis_db: int = Field(default=0, description="Redis database number")
    redis_max_connections: int = Field(default=10, description="Redis max connections")
    redis_timeout: int = Field(default=5, description="Redis timeout in seconds")
    redis_retry_on_timeout: bool = Field(default=True, description="Redis retry on timeout")

    # Cache TTL settings (in seconds)
    cache_ttl_short: int = Field(default=300, description="Short cache TTL (5 minutes)")
    cache_ttl_medium: int = Field(default=1800, description="Medium cache TTL (30 minutes)")
    cache_ttl_long: int = Field(default=3600, description="Long cache TTL (1 hour)")
    cache_ttl_very_long: int = Field(default=86400, description="Very long cache TTL (24 hours)")

    # Cache prefix settings
    cache_prefix: str = Field(default="ai_trading:", description="Cache key prefix")

    # Cache warming settings
    cache_warming_enabled: bool = Field(default=True, description="Enable cache warming")
    cache_warming_interval: int = Field(default=300, description="Cache warming interval in seconds")
    cache_warming_max_concurrent: int = Field(default=5, description="Max concurrent cache warming tasks")

    @property
    def cache_prefix_signals(self) -> str:
        """Get signals cache prefix"""
        return f"{self.cache_prefix}signals:"

    @property
    def cache_prefix_users(self) -> str:
        """Get users cache prefix"""
        return f"{self.cache_prefix}users:"

    @property
    def cache_prefix_market_data(self) -> str:
        """Get market data cache prefix"""
        return f"{self.cache_prefix}market:"

    @property
    def cache_prefix_api(self) -> str:
        """Get API cache prefix"""
        return f"{self.cache_prefix}api:"


class EmailSettings(BaseSettings):
    """Email configuration - Optional for deployment flexibility"""
    email_host: Optional[str] = Field(default=None, description="SMTP server host")
    email_port: int = Field(default=587, description="SMTP server port")
    email_user: Optional[str] = Field(default=None, description="SMTP username")
    email_password: Optional[str] = Field(default=None, description="SMTP password")
    email_from: Optional[str] = Field(default=None, description="From email address")
    email_use_tls: bool = Field(default=True, description="Use TLS for email")
    email_use_ssl: bool = Field(default=False, description="Use SSL for email")

    @field_validator('email_port')
    @classmethod
    def validate_email_port(cls, v: int) -> int:
        """Validate email port"""
        if v not in [25, 465, 587, 2525]:
            raise ValueError("Email port must be one of: 25, 465, 587, 2525")
        return v

    @property
    def is_configured(self) -> bool:
        """Check if email is properly configured"""
        return all([
            self.email_host,
            self.email_user,
            self.email_password,
            self.email_from
        ])


class OANDASettings(BaseSettings):
    """OANDA API configuration"""
    oanda_api_key: str = Field(..., description="OANDA API key")
    oanda_account_id: str = Field(..., description="OANDA account ID")
    oanda_environment: str = Field(default="demo", description="OANDA environment (demo, live, or practice)")
    oanda_base_url: str = Field(default="https://api-fxpractice.oanda.com/v3", description="OANDA base URL")
    oanda_timeout: int = Field(default=30, description="OANDA API timeout in seconds")
    oanda_retry_attempts: int = Field(default=3, description="OANDA API retry attempts")

    @field_validator('oanda_environment')
    @classmethod
    def validate_oanda_environment(cls, v: str) -> str:
        """Validate OANDA environment"""
        if v not in ["demo", "live", "practice"]:
            raise ValueError("OANDA environment must be 'demo', 'live', or 'practice'")
        return v

    @property
    def oanda_live_base_url(self) -> str:
        """Get OANDA live API URL"""
        return "https://api-fxtrade.oanda.com/v3"


class AISettings(BaseSettings):
    """AI/ML configuration"""
    gemini_api_key: str = Field(..., description="Google Gemini API key")
    gemini_model: str = Field(default="gemini-pro", description="Gemini model name")
    gemini_temperature: float = Field(default=0.7, description="Gemini temperature")
    gemini_max_tokens: int = Field(default=1000, description="Gemini max tokens")
    ai_confidence_threshold: float = Field(default=0.6, description="AI confidence threshold")


class APISettings(BaseSettings):
    """API configuration"""
    api_v1_prefix: str = Field(default="/api/v1", description="API v1 prefix")
    cors_origins: List[str] = Field(default=["*"], description="CORS allowed origins")
    cors_allow_credentials: bool = Field(default=True, description="CORS allow credentials")
    cors_allow_methods: List[str] = Field(default=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"], description="CORS allowed methods")
    cors_allow_headers: List[str] = Field(default=["*"], description="CORS allowed headers")

    # Rate limiting
    rate_limit_requests: int = Field(default=100, description="Rate limit requests per window")
    rate_limit_window: int = Field(default=60, description="Rate limit window in seconds")

    # API timeouts
    api_timeout: int = Field(default=30, description="API timeout in seconds")
    api_max_retries: int = Field(default=3, description="API max retries")


class ServerSettings(BaseSettings):
    """Server configuration"""
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    debug: bool = Field(default=False, description="Debug mode")
    reload: bool = Field(default=False, description="Auto-reload on code changes")

    # SSL/TLS settings
    ssl_keyfile: Optional[str] = Field(default=None, description="SSL key file path")
    ssl_certfile: Optional[str] = Field(default=None, description="SSL cert file path")

    # Worker settings
    max_workers: int = Field(default=4, description="Max worker processes")
    timeout: int = Field(default=30, description="Worker timeout in seconds")


class SentrySettings(BaseSettings):
    """Sentry error tracking configuration"""
    sentry_dsn: Optional[str] = Field(default=None, description="Sentry DSN for error tracking")
    sentry_traces_sample_rate: float = Field(default=0.2, description="Sentry traces sample rate (0.0-1.0)")
    sentry_profiles_sample_rate: float = Field(default=0.1, description="Sentry profiles sample rate (0.0-1.0)")
    enable_performance_monitoring: bool = Field(default=True, description="Enable Sentry performance monitoring")
    enable_session_replay: bool = Field(default=False, description="Enable Sentry session replay")
    sentry_environment: Optional[str] = Field(default=None, description="Override Sentry environment")

    # Error classification and alerting
    enable_error_classification: bool = Field(default=True, description="Enable automatic error classification")
    alert_on_critical_errors: bool = Field(default=True, description="Send alerts for critical errors")
    alert_on_error_rate_increase: bool = Field(default=True, description="Send alerts for error rate increases")
    error_rate_threshold: float = Field(default=0.1, description="Error rate threshold for alerts (0.0-1.0)")

    # Custom metrics
    enable_custom_metrics: bool = Field(default=True, description="Enable custom Sentry metrics")
    metrics_flush_interval: int = Field(default=60, description="Metrics flush interval in seconds")

    @field_validator('sentry_traces_sample_rate', 'sentry_profiles_sample_rate')
    @classmethod
    def validate_sample_rate(cls, v: float) -> float:
        """Validate sample rate is between 0 and 1"""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Sample rate must be between 0.0 and 1.0")
        return v

    @field_validator('error_rate_threshold')
    @classmethod
    def validate_error_rate_threshold(cls, v: float) -> float:
        """Validate error rate threshold is between 0 and 1"""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Error rate threshold must be between 0.0 and 1.0")
        return v


class MonitoringSettings(BaseSettings):
    """Monitoring and metrics configuration"""
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")
    metrics_port: int = Field(default=8080, description="Metrics server port")
    enable_health_checks: bool = Field(default=True, description="Enable health checks")
    enable_profiling: bool = Field(default=False, description="Enable profiling")

    # Logging settings
    log_level: LogLevel = Field(default=LogLevel.INFO, description="Log level")
    log_format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s", description="Log format")
    log_file: Optional[str] = Field(default=None, description="Log file path")
    log_max_size: int = Field(default=10485760, description="Log file max size (10MB)")
    log_backup_count: int = Field(default=5, description="Log backup count")

    # Error tracking
    enable_error_tracking: bool = Field(default=False, description="Enable error tracking")
    error_tracking_dsn: Optional[str] = Field(default=None, description="Error tracking DSN")

    # Performance monitoring
    enable_apm: bool = Field(default=True, description="Enable Application Performance Monitoring")
    apm_server_url: Optional[str] = Field(default=None, description="APM server URL")
    apm_service_name: str = Field(default="trading-system", description="APM service name")


class TradingSettings(BaseSettings):
    """Trading system configuration"""
    # Default trading symbols
    default_symbols: List[str] = Field(
        default=["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD",
                "NZDUSD", "EURGBP", "EURJPY", "GBPJPY", "GOLD"],
        description="Default trading symbols"
    )

    # Risk management
    max_daily_signals: int = Field(default=100, description="Max daily signals")
    default_risk_level: str = Field(default="MEDIUM", description="Default risk level")
    default_position_size: float = Field(default=0.01, description="Default position size")
    max_position_size: float = Field(default=0.05, description="Maximum position size")

    # Trading hours
    trading_hours_enabled: bool = Field(default=True, description="Enable trading hours restriction")
    trading_session_timezone: str = Field(default="UTC", description="Trading session timezone")

    # Signal generation
    enable_signal_generation: bool = Field(default=True, description="Enable signal generation")
    signal_confidence_threshold: float = Field(default=0.6, description="Signal confidence threshold")
    signal_generation_interval: int = Field(default=300, description="Signal generation interval in seconds")

    @field_validator('default_risk_level')
    @classmethod
    def validate_risk_level(cls, v: str) -> str:
        """Validate risk level"""
        if v.upper() not in ["LOW", "MEDIUM", "HIGH"]:
            raise ValueError("Risk level must be LOW, MEDIUM, or HIGH")
        return v.upper()


class FeatureFlags(BaseSettings):
    """Feature flags configuration"""
    enable_ai_analysis: bool = Field(default=True, description="Enable AI analysis")
    enable_real_time_data: bool = Field(default=True, description="Enable real-time data")
    enable_user_authentication: bool = Field(default=True, description="Enable user authentication")
    enable_email_notifications: bool = Field(default=True, description="Enable email notifications")
    enable_cache_warming: bool = Field(default=True, description="Enable cache warming")
    enable_performance_monitoring: bool = Field(default=True, description="Enable performance monitoring")
    enable_signal_execution: bool = Field(default=False, description="Enable signal execution")
    enable_paper_trading: bool = Field(default=True, description="Enable paper trading")


class Settings(BaseSettings):
    """Main application settings"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"
    )

    # Application info
    project_name: str = Field(default="Trading Signals System", description="Application name")
    version: str = Field(default="2.0.1", description="Application version")
    description: str = Field(default="Professional Trading Signals Platform with AI and OANDA Integration", description="Application description")

    # Environment
    environment: Environment = Field(default=Environment.PRODUCTION, description="Application environment")

    # Sub-settings groups
    security: SecuritySettings = Field(default_factory=SecuritySettings, description="Security settings")
    database: DatabaseSettings = Field(default_factory=DatabaseSettings, description="Database settings")
    cache: CacheSettings = Field(default_factory=CacheSettings, description="Cache settings")
    email: EmailSettings = Field(default_factory=EmailSettings, description="Email settings")
    oanda: OANDASettings = Field(default_factory=OANDASettings, description="OANDA settings")
    ai: AISettings = Field(default_factory=AISettings, description="AI settings")
    api: APISettings = Field(default_factory=APISettings, description="API settings")
    server: ServerSettings = Field(default_factory=ServerSettings, description="Server settings")
    monitoring: MonitoringSettings = Field(default_factory=MonitoringSettings, description="Monitoring settings")
    sentry: SentrySettings = Field(default_factory=SentrySettings, description="Sentry settings")
    trading: TradingSettings = Field(default_factory=TradingSettings, description="Trading settings")
    features: FeatureFlags = Field(default_factory=FeatureFlags, description="Feature flags")

    @field_validator('environment')
    @classmethod
    def validate_environment(cls, v: Environment) -> Environment:
        """Validate environment"""
        return v

    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment == Environment.DEVELOPMENT

    @property
    def is_staging(self) -> bool:
        """Check if running in staging"""
        return self.environment == Environment.STAGING

    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == Environment.PRODUCTION

    @property
    def is_testing(self) -> bool:
        """Check if running in testing"""
        return self.environment == Environment.TESTING

    def get_cors_origins(self) -> List[str]:
        """Get CORS origins based on environment"""
        if self.is_development:
            return ["*"]
        elif self.is_staging:
            return [
                "https://staging.trading-system.com",
                "https://*.railway.app",
            ]
        elif self.is_production:
            return [
                "https://trading-system.com",
                "https://www.trading-system.com",
            ]
        else:
            return ["*"]

    def validate_configuration(self) -> Dict[str, Any]:
        """Validate all configuration settings"""
        errors = []

        # Validate security settings in production
        if self.is_production:
            if self.security.jwt_secret_key == "your-secret-key-change-this-in-production":
                errors.append("JWT secret key must be changed in production")

            if self.server.debug:
                errors.append("Debug mode should be disabled in production")

        # Validate required settings
        required_settings = [
            ('security.jwt_secret_key', self.security.jwt_secret_key),
            ('database.database_url', self.database.database_url),
            ('oanda.oanda_api_key', self.oanda.oanda_api_key),
            ('oanda.oanda_account_id', self.oanda.oanda_account_id),
            ('ai.gemini_api_key', self.ai.gemini_api_key),
        ]

        for setting_name, value in required_settings:
            if not value or value in ["", "your-secret-key", "your-oanda-api-key", "your-gemini-api-key"]:
                errors.append(f"Required setting '{setting_name}' is not configured")

        # Check if email is configured (optional)
        if not self.email.is_configured:
            # Email is optional, so just add a warning, not an error
            print(f"[WARNING] Email configuration is incomplete. Email functionality will be disabled.")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "environment": self.environment.value,
            "settings_count": len(self.model_dump()),
        }

    def get_safe_settings(self) -> Dict[str, Any]:
        """Get settings without sensitive information"""
        settings_dict = self.model_dump()

        # Remove sensitive fields
        sensitive_fields = [
            'security.jwt_secret_key',
            'database.database_url',
            'email.email_password',
            'oanda.oanda_api_key',
            'ai.gemini_api_key',
            'cache.redis_password',
        ]

        for field in sensitive_fields:
            keys = field.split('.')
            current = settings_dict
            for key in keys[:-1]:
                if key in current:
                    current = current[key]
            if keys[-1] in current:
                current[keys[-1]] = "***REDACTED***"

        return settings_dict


# Environment-specific settings
class DevelopmentSettings(Settings):
    """Development environment settings"""
    environment: Environment = Environment.DEVELOPMENT
    # Override security settings for development with defaults
    security: SecuritySettings = Field(default_factory=lambda: SecuritySettings(
        jwt_secret_key="development_jwt_secret_key_change_this_in_production_abcdefghijk"
    ))
    # Override database settings for development
    database: DatabaseSettings = Field(default_factory=lambda: DatabaseSettings(
        database_url="sqlite:///./test.db"
    ))
    # Override email settings for development (optional)
    email: EmailSettings = Field(default_factory=lambda: EmailSettings(
        email_host=None,
        email_user=None,
        email_password=None,
        email_from=None
    ))
    # Override OANDA settings for development
    oanda: OANDASettings = Field(default_factory=lambda: OANDASettings(
        oanda_api_key="demo_api_key",
        oanda_account_id="demo_account_id",
        oanda_environment="demo"
    ))
    # Override AI settings for development
    ai: AISettings = Field(default_factory=lambda: AISettings(
        gemini_api_key="demo_gemini_key"
    ))
    server: ServerSettings = Field(default_factory=lambda: ServerSettings(
        debug=True,
        reload=True,
        host="127.0.0.1",
        port=8000
    ))
    monitoring: MonitoringSettings = Field(default_factory=lambda: MonitoringSettings(
        log_level=LogLevel.DEBUG,
        enable_metrics=False,
        enable_profiling=True
    ))
    features: FeatureFlags = Field(default_factory=lambda: FeatureFlags(
        enable_email_notifications=False
    ))


class StagingSettings(Settings):
    """Staging environment settings"""
    environment: Environment = Environment.STAGING
    server: ServerSettings = Field(default_factory=lambda: ServerSettings(
        debug=False,
        reload=False,
        max_workers=4,
        timeout=30
    ))
    monitoring: MonitoringSettings = Field(default_factory=lambda: MonitoringSettings(
        log_level=LogLevel.INFO,
        enable_metrics=True
    ))


class ProductionSettings(Settings):
    """Production environment settings"""
    environment: Environment = Environment.PRODUCTION
    server: ServerSettings = Field(default_factory=lambda: ServerSettings(
        debug=False,
        reload=False,
        max_workers=8,
        timeout=20
    ))
    monitoring: MonitoringSettings = Field(default_factory=lambda: MonitoringSettings(
        log_level=LogLevel.WARNING,
        enable_metrics=True
    ))
    api: APISettings = Field(default_factory=lambda: APISettings(
        rate_limit_requests=50,
        rate_limit_window=60
    ))


class TestSettings(Settings):
    """Testing environment settings"""
    environment: Environment = Environment.TESTING
    server: ServerSettings = Field(default_factory=lambda: ServerSettings(
        debug=True,
        reload=False,
        max_workers=1,
        timeout=10
    ))
    monitoring: MonitoringSettings = Field(default_factory=lambda: MonitoringSettings(
        log_level=LogLevel.CRITICAL,
        enable_metrics=False
    ))
    features: FeatureFlags = Field(default_factory=lambda: FeatureFlags(
        enable_ai_analysis=False,
        enable_signal_generation=False,
        enable_real_time_data=False,
        enable_email_notifications=False
    ))
    database: DatabaseSettings = Field(default_factory=lambda: DatabaseSettings(
        database_url="sqlite:///./test.db"
    ))
    cache: CacheSettings = Field(default_factory=lambda: CacheSettings(
        redis_url="redis://localhost:6379/1"
    ))


def get_settings() -> Settings:
    """Get settings based on environment"""
    env = os.getenv("ENVIRONMENT", "production").lower()

    if env == "development":
        return DevelopmentSettings()
    elif env == "staging":
        return StagingSettings()
    elif env == "testing":
        return TestSettings()
    else:
        return ProductionSettings()


# Global settings instance
settings = get_settings()