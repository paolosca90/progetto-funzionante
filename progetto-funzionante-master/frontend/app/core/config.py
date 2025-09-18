"""
Unified Configuration System
This file provides backward compatibility with the old configuration system.
All configurations are now managed by the unified settings system in config/settings.py
"""

import os
from typing import List
from config.settings import settings, Environment, LogLevel


class Settings:
    """
    Legacy Settings Class for Backward Compatibility

    This class provides the same interface as the old Settings class
    but uses the new unified configuration system internally.

    All new code should import directly from config.settings instead.
    """

    @property
    def PROJECT_NAME(self) -> str:
        """Get project name from new configuration"""
        return settings.project_name

    @property
    def VERSION(self) -> str:
        """Get version from new configuration"""
        return settings.version

    @property
    def DESCRIPTION(self) -> str:
        """Get description from new configuration"""
        return settings.description

    @property
    def ALLOWED_ORIGINS(self) -> List[str]:
        """Get CORS origins from new configuration"""
        return settings.get_cors_origins()

    @property
    def DATABASE_URL(self) -> str:
        """Get database URL from new configuration"""
        return settings.database.database_url

    @property
    def JWT_SECRET_KEY(self) -> str:
        """Get JWT secret key from new configuration"""
        return settings.security.jwt_secret_key

    @property
    def ACCESS_TOKEN_EXPIRE_MINUTES(self) -> int:
        """Get access token expiration from new configuration"""
        return settings.security.jwt_access_token_expire_minutes

    @property
    def EMAIL_HOST(self) -> str:
        """Get email host from new configuration"""
        return settings.email.email_host

    @property
    def EMAIL_PORT(self) -> int:
        """Get email port from new configuration"""
        return settings.email.email_port

    @property
    def EMAIL_USER(self) -> str:
        """Get email user from new configuration"""
        return settings.email.email_user

    @property
    def EMAIL_PASSWORD(self) -> str:
        """Get email password from new configuration"""
        return settings.email.email_password

    @property
    def EMAIL_USE_TLS(self) -> bool:
        """Get email TLS setting from new configuration"""
        return settings.email.email_use_tls

    @property
    def OANDA_API_KEY(self) -> str:
        """Get OANDA API key from new configuration"""
        return settings.oanda.oanda_api_key

    @property
    def OANDA_ACCOUNT_ID(self) -> str:
        """Get OANDA account ID from new configuration"""
        return settings.oanda.oanda_account_id

    @property
    def OANDA_ENVIRONMENT(self) -> str:
        """Get OANDA environment from new configuration"""
        return settings.oanda.oanda_environment

    @property
    def GEMINI_API_KEY(self) -> str:
        """Get Gemini API key from new configuration"""
        return settings.ai.gemini_api_key

    @property
    def REDIS_URL(self) -> str:
        """Get Redis URL from new configuration"""
        return settings.cache.redis_url

    @property
    def REDIS_PASSWORD(self) -> str:
        """Get Redis password from new configuration"""
        return settings.cache.redis_password

    @property
    def REDIS_DB(self) -> int:
        """Get Redis DB from new configuration"""
        return settings.cache.redis_db

    @property
    def REDIS_POOL_SIZE(self) -> int:
        """Get Redis pool size from new configuration"""
        return settings.cache.redis_max_connections

    @property
    def REDIS_TIMEOUT(self) -> int:
        """Get Redis timeout from new configuration"""
        return settings.cache.redis_timeout

    @property
    def REDIS_RETRY_ON_TIMEOUT(self) -> bool:
        """Get Redis retry on timeout from new configuration"""
        return settings.cache.redis_retry_on_timeout

    @property
    def CACHE_TTL_SHORT(self) -> int:
        """Get short cache TTL from new configuration"""
        return settings.cache.cache_ttl_short

    @property
    def CACHE_TTL_MEDIUM(self) -> int:
        """Get medium cache TTL from new configuration"""
        return settings.cache.cache_ttl_medium

    @property
    def CACHE_TTL_LONG(self) -> int:
        """Get long cache TTL from new configuration"""
        return settings.cache.cache_ttl_long

    @property
    def CACHE_TTL_VERY_LONG(self) -> int:
        """Get very long cache TTL from new configuration"""
        return settings.cache.cache_ttl_very_long

    @property
    def CACHE_PREFIX(self) -> str:
        """Get cache prefix from new configuration"""
        return settings.cache.cache_prefix

    @property
    def CACHE_PREFIX_SIGNALS(self) -> str:
        """Get signals cache prefix from new configuration"""
        return settings.cache.cache_prefix_signals

    @property
    def CACHE_PREFIX_USERS(self) -> str:
        """Get users cache prefix from new configuration"""
        return settings.cache.cache_prefix_users

    @property
    def CACHE_PREFIX_MARKET_DATA(self) -> str:
        """Get market data cache prefix from new configuration"""
        return settings.cache.cache_prefix_market_data

    @property
    def CACHE_PREFIX_API(self) -> str:
        """Get API cache prefix from new configuration"""
        return settings.cache.cache_prefix_api

    @property
    def DEFAULT_SYMBOLS(self) -> List[str]:
        """Get default symbols from new configuration"""
        return settings.trading.default_symbols

    @property
    def MAX_DAILY_SIGNALS(self) -> int:
        """Get max daily signals from new configuration"""
        return settings.trading.max_daily_signals

    @property
    def DEFAULT_RISK_LEVEL(self) -> str:
        """Get default risk level from new configuration"""
        return settings.trading.default_risk_level

    @property
    def DEFAULT_POSITION_SIZE(self) -> float:
        """Get default position size from new configuration"""
        return settings.trading.default_position_size

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return settings.is_development

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return settings.is_production

    @property
    def is_staging(self) -> bool:
        """Check if running in staging mode."""
        return settings.is_staging

    @property
    def is_testing(self) -> bool:
        """Check if running in testing mode."""
        return settings.is_testing

    # Additional properties for new configuration features
    @property
    def ENVIRONMENT(self) -> str:
        """Get current environment"""
        return settings.environment.value

    @property
    def DEBUG(self) -> bool:
        """Get debug mode"""
        return settings.server.debug

    @property
    def HOST(self) -> str:
        """Get server host"""
        return settings.server.host

    @property
    def PORT(self) -> int:
        """Get server port"""
        return settings.server.port

    @property
    def LOG_LEVEL(self) -> str:
        """Get log level"""
        return settings.monitoring.log_level.value

    @property
    def LOG_FILE(self) -> str:
        """Get log file path"""
        return settings.monitoring.log_file

    @property
    def ENABLE_METRICS(self) -> bool:
        """Get metrics enabled flag"""
        return settings.monitoring.enable_metrics

    @property
    def METRICS_PORT(self) -> int:
        """Get metrics port"""
        return settings.monitoring.metrics_port

    @property
    def MAX_WORKERS(self) -> int:
        """Get max workers"""
        return settings.server.max_workers

    @property
    def TIMEOUT(self) -> int:
        """Get timeout"""
        return settings.server.timeout

    @property
    def RATE_LIMIT_REQUESTS(self) -> int:
        """Get rate limit requests"""
        return settings.api.rate_limit_requests

    @property
    def RATE_LIMIT_WINDOW(self) -> int:
        """Get rate limit window"""
        return settings.api.rate_limit_window

    @property
    def ENABLE_AI_ANALYSIS(self) -> bool:
        """Get AI analysis enabled flag"""
        return settings.features.enable_ai_analysis

    @property
    def ENABLE_SIGNAL_GENERATION(self) -> bool:
        """Get signal generation enabled flag"""
        return settings.features.enable_signal_generation

    @property
    def ENABLE_REAL_TIME_DATA(self) -> bool:
        """Get real-time data enabled flag"""
        return settings.features.enable_real_time_data

    @property
    def ENABLE_USER_AUTHENTICATION(self) -> bool:
        """Get user authentication enabled flag"""
        return settings.features.enable_user_authentication

    @property
    def ENABLE_EMAIL_NOTIFICATIONS(self) -> bool:
        """Get email notifications enabled flag"""
        return settings.features.enable_email_notifications

    @property
    def API_V1_PREFIX(self) -> str:
        """Get API v1 prefix"""
        return settings.api.api_v1_prefix

    @property
    def OANDA_BASE_URL(self) -> str:
        """Get OANDA base URL"""
        return settings.oanda.oanda_base_url

    @property
    def OANDA_TIMEOUT(self) -> int:
        """Get OANDA timeout"""
        return settings.oanda.oanda_timeout

    @property
    def GEMINI_MODEL(self) -> str:
        """Get Gemini model"""
        return settings.ai.gemini_model

    @property
    def GEMINI_TEMPERATURE(self) -> float:
        """Get Gemini temperature"""
        return settings.ai.gemini_temperature

    @property
    def GEMINI_MAX_TOKENS(self) -> int:
        """Get Gemini max tokens"""
        return settings.ai.gemini_max_tokens

    def validate_configuration(self) -> dict:
        """Validate configuration and return validation results"""
        return settings.validate_configuration()

    def get_safe_settings(self) -> dict:
        """Get settings without sensitive information"""
        return settings.get_safe_settings()


# Global settings instance
settings = Settings()