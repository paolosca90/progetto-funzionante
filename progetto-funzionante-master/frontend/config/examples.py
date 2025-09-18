"""
Configuration Examples and Usage Patterns

This file provides comprehensive examples of how to use the unified configuration system
in different scenarios and contexts.
"""

import os
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from config.settings import (
    settings,
    get_settings,
    Environment,
    SecuritySettings,
    DatabaseSettings,
    CacheSettings,
    EmailSettings,
    OANDASettings,
    AISettings,
    APISettings,
    ServerSettings,
    MonitoringSettings,
    TradingSettings,
    FeatureFlags
)
from config.config_manager import ConfigurationManager


def example_basic_usage():
    """Basic configuration usage examples"""
    print("=== Basic Configuration Usage ===")

    # Access configuration values
    print(f"Environment: {settings.environment.value}")
    print(f"Project Name: {settings.project_name}")
    print(f"Version: {settings.version}")
    print(f"Debug Mode: {settings.server.debug}")

    # Access nested configurations
    print(f"Database Pool Size: {settings.database.database_pool_size}")
    print(f"Redis URL: {settings.cache.redis_url}")
    print(f"JWT Algorithm: {settings.security.jwt_algorithm}")
    print(f"OANDA Environment: {settings.oanda.oanda_environment}")

    # Use environment detection
    if settings.is_development:
        print("Running in development mode")
    elif settings.is_production:
        print("Running in production mode")
    elif settings.is_staging:
        print("Running in staging mode")
    elif settings.is_testing:
        print("Running in testing mode")


def example_cache_configuration():
    """Cache configuration examples"""
    print("\n=== Cache Configuration Examples ===")

    # Access cache settings
    cache = settings.cache
    print(f"Redis URL: {cache.redis_url}")
    print(f"Cache TTL Short: {cache.cache_ttl_short} seconds")
    print(f"Cache TTL Medium: {cache.cache_ttl_medium} seconds")
    print(f"Cache TTL Long: {cache.cache_ttl_long} seconds")
    print(f"Cache Prefix: {cache.cache_prefix}")

    # Use cache prefix properties
    print(f"Signals Cache Prefix: {cache.cache_prefix_signals}")
    print(f"Users Cache Prefix: {cache.cache_prefix_users}")
    print(f"Market Data Cache Prefix: {cache.cache_prefix_market_data}")
    print(f"API Cache Prefix: {cache.cache_prefix_api}")

    # Cache warming configuration
    print(f"Cache Warming Enabled: {cache.cache_warming_enabled}")
    print(f"Cache Warming Interval: {cache.cache_warming_interval} seconds")
    print(f"Max Concurrent Warming Tasks: {cache.cache_warming_max_concurrent}")


def example_security_configuration():
    """Security configuration examples"""
    print("\n=== Security Configuration Examples ===")

    security = settings.security
    print(f"JWT Algorithm: {security.jwt_algorithm}")
    print(f"Access Token Expiration: {security.jwt_access_token_expire_minutes} minutes")
    print(f"Refresh Token Expiration: {security.jwt_refresh_token_expire_days} days")

    # Security validation
    validation = settings.validate_configuration()
    print(f"Configuration Valid: {validation['valid']}")
    if not validation['valid']:
        print("Configuration Errors:")
        for error in validation['errors']:
            print(f"  - {error}")


def example_api_configuration():
    """API configuration examples"""
    print("\n=== API Configuration Examples ===")

    api = settings.api
    print(f"API v1 Prefix: {api.api_v1_prefix}")
    print(f"Rate Limit: {api.rate_limit_requests} requests per {api.rate_limit_window} seconds")
    print(f"API Timeout: {api.api_timeout} seconds")

    # CORS configuration
    cors_origins = settings.get_cors_origins()
    print(f"CORS Origins: {cors_origins}")

    # CORS settings
    print(f"CORS Allow Credentials: {api.cors_allow_credentials}")
    print(f"CORS Allow Methods: {api.cors_allow_methods}")
    print(f"CORS Allow Headers: {api.cors_allow_headers}")


def example_trading_configuration():
    """Trading configuration examples"""
    print("\n=== Trading Configuration Examples ===")

    trading = settings.trading
    print(f"Default Symbols: {trading.default_symbols}")
    print(f"Max Daily Signals: {trading.max_daily_signals}")
    print(f"Default Risk Level: {trading.default_risk_level}")
    print(f"Default Position Size: {trading.default_position_size}")
    print(f"Max Position Size: {trading.max_position_size}")

    # Signal generation configuration
    print(f"Signal Generation Enabled: {trading.enable_signal_generation}")
    print(f"Signal Confidence Threshold: {trading.signal_confidence_threshold}")
    print(f"Signal Generation Interval: {trading.signal_generation_interval} seconds")

    # Trading hours
    print(f"Trading Hours Enabled: {trading.trading_hours_enabled}")
    print(f"Trading Session Timezone: {trading.trading_session_timezone}")


def example_feature_flags():
    """Feature flags configuration examples"""
    print("\n=== Feature Flags Examples ===")

    features = settings.features
    feature_flags = [
        ('AI Analysis', features.enable_ai_analysis),
        ('Real-time Data', features.enable_real_time_data),
        ('User Authentication', features.enable_user_authentication),
        ('Email Notifications', features.enable_email_notifications),
        ('Cache Warming', features.enable_cache_warming),
        ('Performance Monitoring', features.enable_performance_monitoring),
        ('Signal Execution', features.enable_signal_execution),
        ('Paper Trading', features.enable_paper_trading),
    ]

    for name, enabled in feature_flags:
        status = "✅ Enabled" if enabled else "❌ Disabled"
        print(f"{name}: {status}")


def example_monitoring_configuration():
    """Monitoring configuration examples"""
    print("\n=== Monitoring Configuration Examples ===")

    monitoring = settings.monitoring
    print(f"Log Level: {monitoring.log_level.value}")
    print(f"Log Format: {monitoring.log_format}")
    print(f"Log File: {monitoring.log_file}")
    print(f"Enable Metrics: {monitoring.enable_metrics}")
    print(f"Metrics Port: {monitoring.metrics_port}")
    print(f"Enable Health Checks: {monitoring.enable_health_checks}")
    print(f"Enable Profiling: {monitoring.enable_profiling}")


def example_server_configuration():
    """Server configuration examples"""
    print("\n=== Server Configuration Examples ===")

    server = settings.server
    print(f"Host: {server.host}")
    print(f"Port: {server.port}")
    print(f"Debug Mode: {server.debug}")
    print(f"Auto Reload: {server.reload}")
    print(f"Max Workers: {server.max_workers}")
    print(f"Timeout: {server.timeout} seconds")

    # SSL/TLS configuration
    print(f"SSL Key File: {server.ssl_keyfile}")
    print(f"SSL Cert File: {server.ssl_certfile}")


def example_configuration_validation():
    """Configuration validation examples"""
    print("\n=== Configuration Validation Examples ===")

    # Validate current configuration
    validation = settings.validate_configuration()
    print(f"Configuration Valid: {validation['valid']}")
    print(f"Settings Count: {validation['settings_count']}")
    print(f"Environment: {validation['environment']}")

    if validation['errors']:
        print("\n❌ Configuration Errors:")
        for error in validation['errors']:
            print(f"  - {error}")

    # Get safe configuration (without sensitive data)
    safe_config = settings.get_safe_settings()
    print(f"\nSafe Configuration Keys: {list(safe_config.keys())}")


def example_environment_specific_configs():
    """Environment-specific configuration examples"""
    print("\n=== Environment-Specific Configuration Examples ===")

    # Get different environment settings
    environments = ['development', 'staging', 'production', 'testing']

    for env_name in environments:
        print(f"\n{env_name.upper()} Environment:")

        # Set environment temporarily
        original_env = os.environ.get('ENVIRONMENT')
        os.environ['ENVIRONMENT'] = env_name

        try:
            env_settings = get_settings()

            print(f"  Debug: {env_settings.server.debug}")
            print(f"  Log Level: {env_settings.monitoring.log_level.value}")
            print(f"  Max Workers: {env_settings.server.max_workers}")
            print(f"  Timeout: {env_settings.server.timeout}")
            print(f"  Email Notifications: {env_settings.features.enable_email_notifications}")
            print(f"  AI Analysis: {env_settings.features.enable_ai_analysis}")
        finally:
            # Restore original environment
            if original_env:
                os.environ['ENVIRONMENT'] = original_env
            else:
                os.environ.pop('ENVIRONMENT', None)


def example_configuration_manager():
    """Configuration manager usage examples"""
    print("\n=== Configuration Manager Examples ===")

    config_manager = ConfigurationManager()

    # Generate secure values
    jwt_secret = config_manager.generate_jwt_secret()
    print(f"Generated JWT Secret: {jwt_secret[:20]}...")

    # Generate database URL
    db_url = config_manager.generate_database_url(
        host="localhost",
        port=5432,
        database="trading",
        username="user",
        password="pass"
    )
    print(f"Generated Database URL: {db_url}")

    # Get configuration summary
    summary = config_manager.get_configuration_summary()
    print(f"\nConfiguration Summary:")
    print(f"  Environment: {summary['environment']}")
    print(f"  Valid: {summary['configuration_valid']}")
    print(f"  Settings Count: {summary['settings_count']}")

    # Generate deployment configuration
    deploy_config = config_manager.generate_deployment_config('production')
    print(f"\nProduction Deployment Config:")
    for key, value in deploy_config.items():
        print(f"  {key}: {value}")


def example_custom_configuration():
    """Custom configuration examples"""
    print("\n=== Custom Configuration Examples ===")

    # Create custom settings with overrides
    class CustomSettings(Settings):
        """Custom settings with application-specific overrides"""

        @property
        def custom_feature_enabled(self) -> bool:
            """Custom feature flag"""
            return self.environment == Environment.DEVELOPMENT

        def get_custom_database_url(self) -> str:
            """Custom database URL logic"""
            if self.is_testing:
                return "sqlite:///./custom_test.db"
            return self.database.database_url

    # Use custom settings
    custom_settings = CustomSettings()
    print(f"Custom Feature Enabled: {custom_settings.custom_feature_enabled}")
    print(f"Custom Database URL: {custom_settings.get_custom_database_url()}")


def example_configuration_in_context():
    """Configuration usage in different contexts"""
    print("\n=== Configuration in Context Examples ===")

    # Example: Database connection configuration
    def get_database_config() -> Dict[str, Any]:
        """Get database configuration for connection"""
        return {
            'url': settings.database.database_url,
            'pool_size': settings.database.database_pool_size,
            'max_overflow': settings.database.database_max_overflow,
            'pool_timeout': settings.database.database_pool_timeout,
            'pool_recycle': settings.database.database_pool_recycle,
        }

    # Example: Email service configuration
    def get_email_config() -> Dict[str, Any]:
        """Get email configuration for service"""
        return {
            'host': settings.email.email_host,
            'port': settings.email.email_port,
            'username': settings.email.email_user,
            'password': settings.email.email_password,
            'use_tls': settings.email.email_use_tls,
            'from_email': settings.email.email_from,
        }

    # Example: API client configuration
    def get_api_client_config() -> Dict[str, Any]:
        """Get API client configuration"""
        return {
            'base_url': settings.oanda.oanda_base_url,
            'api_key': settings.oanda.oanda_api_key,
            'timeout': settings.oanda.oanda_timeout,
            'retry_attempts': settings.oanda.oanda_retry_attempts,
            'environment': settings.oanda.oanda_environment,
        }

    print("Database Config:", get_database_config())
    print("Email Config:", {k: v for k, v in get_email_config().items() if k != 'password'})
    print("API Client Config:", {k: v for k, v in get_api_client_config().items() if k != 'api_key'})


def example_configuration_testing():
    """Configuration testing examples"""
    print("\n=== Configuration Testing Examples ===")

    # Test configuration validation
    def test_production_security():
        """Test production security requirements"""
        if settings.is_production:
            assert not settings.server.debug, "Debug mode should be disabled in production"
            assert len(settings.security.jwt_secret_key) >= 32, "JWT secret must be at least 32 characters"
            assert settings.security.jwt_secret_key != "your-secret-key-change-this-in-production", "Default JWT secret not allowed in production"
            print("✅ Production security checks passed")

    # Test feature flags
    def test_feature_flags():
        """Test feature flag configuration"""
        if settings.is_testing:
            assert not settings.features.enable_ai_analysis, "AI analysis should be disabled in testing"
            assert not settings.features.enable_signal_generation, "Signal generation should be disabled in testing"
            print("✅ Testing feature flags correct")

    # Test CORS configuration
    def test_cors_configuration():
        """Test CORS configuration"""
        cors_origins = settings.get_cors_origins()
        assert len(cors_origins) > 0, "CORS origins should be configured"

        if settings.is_development:
            assert "*" in cors_origins, "Development should allow all origins"
        elif settings.is_production:
            assert "*" not in cors_origins, "Production should not allow all origins"
        print("✅ CORS configuration correct")

    # Run tests
    test_production_security()
    test_feature_flags()
    test_cors_configuration()


def example_error_handling():
    """Configuration error handling examples"""
    print("\n=== Error Handling Examples ===")

    def safe_get_configuration():
        """Safely get configuration with error handling"""
        try:
            # Validate configuration
            validation = settings.validate_configuration()
            if not validation['valid']:
                print(f"❌ Configuration errors: {validation['errors']}")
                return None

            # Get safe configuration
            safe_config = settings.get_safe_settings()
            return safe_config

        except Exception as e:
            print(f"❌ Configuration error: {e}")
            return None

    def handle_missing_configuration():
        """Handle missing configuration gracefully"""
        required_vars = [
            'DATABASE_URL',
            'OANDA_API_KEY',
            'GEMINI_API_KEY',
        ]

        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        if missing_vars:
            print(f"⚠️  Missing required environment variables: {missing_vars}")
            print("Please set these variables in your environment file")
            return False

        return True

    # Test error handling
    config = safe_get_configuration()
    if config:
        print("✅ Configuration loaded successfully")

    is_configured = handle_missing_configuration()
    if is_configured:
        print("✅ All required variables are configured")


def run_all_examples():
    """Run all configuration examples"""
    print("🚀 Configuration System Examples")
    print("=" * 50)

    try:
        example_basic_usage()
        example_cache_configuration()
        example_security_configuration()
        example_api_configuration()
        example_trading_configuration()
        example_feature_flags()
        example_monitoring_configuration()
        example_server_configuration()
        example_configuration_validation()
        example_environment_specific_configs()
        example_configuration_manager()
        example_custom_configuration()
        example_configuration_in_context()
        example_configuration_testing()
        example_error_handling()

        print("\n🎉 All examples completed successfully!")

    except Exception as e:
        print(f"\n❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_examples()