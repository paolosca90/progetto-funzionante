"""
Configuration System Tests

Comprehensive tests for the unified configuration system including:
- Environment validation
- Configuration loading
- Type validation
- Security checks
- Environment-specific settings
- Migration functionality
"""

import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from config.settings import (
    Settings,
    DevelopmentSettings,
    StagingSettings,
    ProductionSettings,
    TestSettings,
    Environment,
    LogLevel,
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
    FeatureFlags,
    get_settings
)
from config.config_manager import ConfigurationManager


class TestConfigurationValidation:
    """Test configuration validation functionality"""

    def test_security_settings_validation(self):
        """Test security settings validation"""
        # Valid JWT secret
        valid_secret = "a" * 64  # 64 character secret
        security = SecuritySettings(jwt_secret_key=valid_secret)
        assert security.jwt_secret_key == valid_secret

        # Invalid JWT secret (too short)
        with pytest.raises(ValueError):
            SecuritySettings(jwt_secret_key="short")

        # Default value rejection
        with pytest.raises(ValueError):
            SecuritySettings(jwt_secret_key="your-secret-key-change-this-in-production")

    def test_database_settings_validation(self):
        """Test database settings validation"""
        # Valid database URLs
        valid_urls = [
            "postgresql://user:pass@localhost:5432/db",
            "mysql://user:pass@localhost:3306/db",
            "sqlite:///./test.db"
        ]

        for url in valid_urls:
            db = DatabaseSettings(database_url=url)
            assert db.database_url == url

        # Invalid database URL
        with pytest.raises(ValueError):
            DatabaseSettings(database_url="invalid://url")

    def test_email_settings_validation(self):
        """Test email settings validation"""
        # Valid email ports
        valid_ports = [25, 465, 587, 2525]
        for port in valid_ports:
            email = EmailSettings(
                email_host="smtp.gmail.com",
                email_user="test@gmail.com",
                email_password="password",
                email_from="test@gmail.com",
                email_port=port
            )
            assert email.email_port == port

        # Invalid email port
        with pytest.raises(ValueError):
            EmailSettings(
                email_host="smtp.gmail.com",
                email_user="test@gmail.com",
                email_password="password",
                email_from="test@gmail.com",
                email_port=999
            )

    def test_oanda_settings_validation(self):
        """Test OANDA settings validation"""
        # Valid environments
        valid_environments = ["demo", "live"]
        for env in valid_environments:
            oanda = OANDASettings(
                oanda_api_key="test-key",
                oanda_account_id="test-account",
                oanda_environment=env
            )
            assert oanda.oanda_environment == env

        # Invalid environment
        with pytest.raises(ValueError):
            OANDASettings(
                oanda_api_key="test-key",
                oanda_account_id="test-account",
                oanda_environment="invalid"
            )

    def test_trading_settings_validation(self):
        """Test trading settings validation"""
        # Valid risk levels
        valid_risk_levels = ["LOW", "MEDIUM", "HIGH"]
        for risk in valid_risk_levels:
            trading = TradingSettings(default_risk_level=risk)
            assert trading.default_risk_level == risk

        # Invalid risk level
        with pytest.raises(ValueError):
            TradingSettings(default_risk_level="INVALID")


class TestEnvironmentSpecificSettings:
    """Test environment-specific configuration"""

    def test_development_settings(self):
        """Test development environment settings"""
        dev_settings = DevelopmentSettings()

        assert dev_settings.environment == Environment.DEVELOPMENT
        assert dev_settings.server.debug is True
        assert dev_settings.server.reload is True
        assert dev_settings.server.host == "127.0.0.1"
        assert dev_settings.monitoring.log_level == LogLevel.DEBUG
        assert dev_settings.features.enable_email_notifications is False

    def test_staging_settings(self):
        """Test staging environment settings"""
        staging_settings = StagingSettings()

        assert staging_settings.environment == Environment.STAGING
        assert staging_settings.server.debug is False
        assert staging_settings.server.reload is False
        assert staging_settings.server.max_workers == 4
        assert staging_settings.monitoring.log_level == LogLevel.INFO

    def test_production_settings(self):
        """Test production environment settings"""
        prod_settings = ProductionSettings()

        assert prod_settings.environment == Environment.PRODUCTION
        assert prod_settings.server.debug is False
        assert prod_settings.server.reload is False
        assert prod_settings.server.max_workers == 8
        assert prod_settings.monitoring.log_level == LogLevel.WARNING
        assert prod_settings.api.rate_limit_requests == 50

    def test_test_settings(self):
        """Test testing environment settings"""
        test_settings = TestSettings()

        assert test_settings.environment == Environment.TESTING
        assert test_settings.server.debug is True
        assert test_settings.server.max_workers == 1
        assert test_settings.monitoring.log_level == LogLevel.CRITICAL
        assert test_settings.features.enable_ai_analysis is False
        assert test_settings.features.enable_signal_generation is False
        assert test_settings.database.database_url == "sqlite:///./test.db"

    def test_environment_detection(self):
        """Test environment detection and settings selection"""
        # Test development
        with patch.dict(os.environ, {'ENVIRONMENT': 'development'}):
            settings = get_settings()
            assert isinstance(settings, DevelopmentSettings)

        # Test staging
        with patch.dict(os.environ, {'ENVIRONMENT': 'staging'}):
            settings = get_settings()
            assert isinstance(settings, StagingSettings)

        # Test production
        with patch.dict(os.environ, {'ENVIRONMENT': 'production'}):
            settings = get_settings()
            assert isinstance(settings, ProductionSettings)

        # Test testing
        with patch.dict(os.environ, {'ENVIRONMENT': 'testing'}):
            settings = get_settings()
            assert isinstance(settings, TestSettings)

        # Test default (production)
        with patch.dict(os.environ, {}, clear=True):
            settings = get_settings()
            assert isinstance(settings, ProductionSettings)


class TestConfigurationProperties:
    """Test configuration properties and methods"""

    def test_environment_properties(self):
        """Test environment detection properties"""
        dev_settings = DevelopmentSettings()
        prod_settings = ProductionSettings()

        assert dev_settings.is_development is True
        assert dev_settings.is_production is False
        assert dev_settings.is_staging is False
        assert dev_settings.is_testing is False

        assert prod_settings.is_production is True
        assert prod_settings.is_development is False
        assert prod_settings.is_staging is False
        assert prod_settings.is_testing is False

    def test_cors_origins(self):
        """Test CORS origins configuration"""
        dev_settings = DevelopmentSettings()
        staging_settings = StagingSettings()
        prod_settings = ProductionSettings()

        dev_cors = dev_settings.get_cors_origins()
        staging_cors = staging_settings.get_cors_origins()
        prod_cors = prod_settings.get_cors_origins()

        assert "*" in dev_cors
        assert "https://staging.trading-system.com" in staging_cors
        assert "https://*.railway.app" in staging_cors
        assert "https://trading-system.com" in prod_cors

    def test_cache_prefixes(self):
        """Test cache prefix properties"""
        cache = CacheSettings(cache_prefix="test:")
        assert cache.cache_prefix_signals == "test:signals:"
        assert cache.cache_prefix_users == "test:users:"
        assert cache.cache_prefix_market_data == "test:market:"
        assert cache.cache_prefix_api == "test:api:"

    def test_oanda_urls(self):
        """Test OANDA URL properties"""
        oanda = OANDASettings(oanda_environment="demo")
        assert oanda.oanda_base_url == "https://api-fxpractice.oanda.com/v3"
        assert oanda.oanda_live_base_url == "https://api-fxtrade.oanda.com/v3"

    def test_configuration_validation(self):
        """Test configuration validation method"""
        # Valid configuration
        with patch.dict(os.environ, {
            'SECURITY_JWT_SECRET_KEY': 'a' * 64,
            'DATABASE_URL': 'postgresql://user:pass@localhost:5432/db',
            'EMAIL_HOST': 'smtp.gmail.com',
            'EMAIL_USER': 'test@gmail.com',
            'EMAIL_PASSWORD': 'password',
            'EMAIL_FROM': 'test@gmail.com',
            'OANDA_API_KEY': 'test-key',
            'OANDA_ACCOUNT_ID': 'test-account',
            'GEMINI_API_KEY': 'test-gemini-key',
            'ENVIRONMENT': 'development'
        }):
            settings = get_settings()
            validation = settings.validate_configuration()
            assert validation["valid"] is True
            assert len(validation["errors"]) == 0

        # Invalid configuration (missing required fields)
        with patch.dict(os.environ, {}, clear=True):
            settings = get_settings()
            validation = settings.validate_configuration()
            assert validation["valid"] is False
            assert len(validation["errors"]) > 0

    def test_safe_settings(self):
        """Test safe settings method (no sensitive data)"""
        settings = get_settings()
        safe_settings = settings.get_safe_settings()

        # Check that sensitive fields are redacted
        assert '***REDACTED***' in str(safe_settings)

        # Check that non-sensitive fields are present
        assert 'project_name' in str(safe_settings)
        assert 'version' in str(safe_settings)
        assert 'environment' in str(safe_settings)


class TestConfigurationManager:
    """Test configuration management utilities"""

    def setup_method(self):
        """Setup configuration manager for tests"""
        self.config_manager = ConfigurationManager()

    def test_generate_jwt_secret(self):
        """Test JWT secret generation"""
        secret = self.config_manager.generate_jwt_secret(32)
        assert len(secret) == 32
        assert isinstance(secret, str)

        # Test different lengths
        secret_64 = self.config_manager.generate_jwt_secret(64)
        assert len(secret_64) == 64

    def test_generate_database_url(self):
        """Test database URL generation"""
        url = self.config_manager.generate_database_url(
            host="localhost",
            port=5432,
            database="testdb",
            username="user",
            password="pass"
        )

        assert url == "postgresql://user:pass@localhost:5432/testdb"

    def test_validate_environment_file(self):
        """Test environment file validation"""
        # Create temporary environment file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("ENVIRONMENT=development\n")
            f.write("SECURITY_JWT_SECRET_KEY=test-secret-key-at-least-32-chars\n")
            f.write("DATABASE_URL=postgresql://user:pass@localhost:5432/db\n")
            temp_file = f.name

        try:
            validation = self.config_manager.validate_environment_file(temp_file)
            assert validation["valid"] is True
            assert len(validation["errors"]) == 0
        finally:
            os.unlink(temp_file)

    def test_validate_environment_file_missing_vars(self):
        """Test environment file validation with missing variables"""
        # Create incomplete environment file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("ENVIRONMENT=production\n")
            f.write("DEBUG=true\n")
            temp_file = f.name

        try:
            validation = self.config_manager.validate_environment_file(temp_file)
            assert validation["valid"] is False
            assert len(validation["errors"]) > 0
            assert any("missing required variables" in error for error in validation["errors"])
        finally:
            os.unlink(temp_file)

    def test_environment_file_not_found(self):
        """Test validation with non-existent environment file"""
        validation = self.config_manager.validate_environment_file("nonexistent.env")
        assert validation["valid"] is False
        assert any("not found" in error for error in validation["errors"])

    def test_get_configuration_summary(self):
        """Test configuration summary generation"""
        summary = self.config_manager.get_configuration_summary()

        required_keys = [
            "environment", "version", "project_name", "configuration_valid",
            "features_enabled", "server_config", "database_config",
            "cache_config", "api_config", "timestamp"
        ]

        for key in required_keys:
            assert key in summary

        assert summary["environment"] in ["development", "staging", "production", "testing"]
        assert isinstance(summary["features_enabled"], dict)
        assert isinstance(summary["server_config"], dict)

    def test_backup_configuration(self):
        """Test configuration backup functionality"""
        backup_path = self.config_manager.backup_configuration()

        assert os.path.exists(backup_path)
        assert backup_path.endswith('.json')

        # Verify backup content
        import json
        with open(backup_path, 'r') as f:
            backup_data = json.load(f)

        assert "backup_timestamp" in backup_data
        assert "environment" in backup_data
        assert "configuration" in backup_data

        # Cleanup
        os.unlink(backup_path)

    def test_compare_environments(self):
        """Test environment comparison functionality"""
        # Create temporary environment files
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f1:
            f1.write("ENVIRONMENT=development\n")
            f1.write("DEBUG=true\n")
            f1.write("MAX_WORKERS=2\n")
            dev_file = f1.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f2:
            f2.write("ENVIRONMENT=production\n")
            f2.write("DEBUG=false\n")
            f2.write("MAX_WORKERS=8\n")
            prod_file = f2.name

        try:
            comparison = self.config_manager.compare_environments('development', 'production')

            assert comparison["environment1"] == "development"
            assert comparison["environment2"] == "production"
            assert "different_values" in comparison
            assert "MAX_WORKERS" in comparison["different_values"]

        finally:
            os.unlink(dev_file)
            os.unlink(prod_file)

    def test_generate_deployment_config(self):
        """Test deployment configuration generation"""
        # Test each environment
        environments = ["development", "staging", "production", "testing"]

        for env in environments:
            config = self.config_manager.generate_deployment_config(env)

            assert "ENVIRONMENT" in config
            assert config["ENVIRONMENT"] == env
            assert "DEBUG" in config
            assert "LOG_LEVEL" in config
            assert "MAX_WORKERS" in config

            # Validate environment-specific values
            if env == "production":
                assert config["DEBUG"] == "false"
                assert config["LOG_LEVEL"] == "WARNING"
                assert config["MAX_WORKERS"] == "8"
            elif env == "development":
                assert config["DEBUG"] == "true"
                assert config["LOG_LEVEL"] == "DEBUG"
                assert config["MAX_WORKERS"] == "2"

    def test_invalid_environment_deployment_config(self):
        """Test deployment config generation with invalid environment"""
        with pytest.raises(ValueError):
            self.config_manager.generate_deployment_config("invalid_env")


class TestConfigurationIntegration:
    """Integration tests for configuration system"""

    def test_full_configuration_cycle(self):
        """Test complete configuration cycle"""
        # Create temporary environment file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("ENVIRONMENT=development\n")
            f.write("SECURITY_JWT_SECRET_KEY=a" * 64 + "\n")
            f.write("DATABASE_URL=postgresql://user:pass@localhost:5432/test\n")
            f.write("EMAIL_HOST=smtp.gmail.com\n")
            f.write("EMAIL_USER=test@gmail.com\n")
            f.write("EMAIL_PASSWORD=password\n")
            f.write("EMAIL_FROM=test@gmail.com\n")
            f.write("OANDA_API_KEY=test-oanda-key\n")
            f.write("OANDA_ACCOUNT_ID=test-account\n")
            f.write("GEMINI_API_KEY=test-gemini-key\n")
            env_file = f.name

        try:
            # Load configuration
            with patch.dict(os.environ, {'ENVIRONMENT': 'development'}):
                settings = get_settings()

                # Validate configuration
                validation = settings.validate_configuration()
                assert validation["valid"] is True

                # Test configuration manager
                config_manager = ConfigurationManager()
                summary = config_manager.get_configuration_summary()

                assert summary["configuration_valid"] is True
                assert summary["environment"] == "development"

                # Test safe settings
                safe_settings = settings.get_safe_settings()
                assert '***REDACTED***' in str(safe_settings)

        finally:
            os.unlink(env_file)

    def test_production_security_checks(self):
        """Test production security validation"""
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'production',
            'SECURITY_JWT_SECRET_KEY': 'your-secret-key-change-this-in-production',  # Default value
            'DATABASE_URL': 'postgresql://user:pass@localhost:5432/test',
            'EMAIL_HOST': 'smtp.gmail.com',
            'EMAIL_USER': 'test@gmail.com',
            'EMAIL_PASSWORD': 'password',
            'EMAIL_FROM': 'test@gmail.com',
            'OANDA_API_KEY': 'test-oanda-key',
            'OANDA_ACCOUNT_ID': 'test-account',
            'GEMINI_API_KEY': 'test-gemini-key',
        }):
            settings = get_settings()
            validation = settings.validate_configuration()

            # Should fail due to default JWT secret in production
            assert validation["valid"] is False
            assert any("JWT secret key must be changed" in error for error in validation["errors"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])