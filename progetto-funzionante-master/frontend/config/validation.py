"""
Configuration Validation System
Comprehensive validation for all environment configurations with detailed error reporting
"""

import re
import ipaddress
import json
from typing import Dict, Any, List, Optional, Union, Tuple, Callable
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class ValidationLevel(str, Enum):
    """Validation severity levels"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

class ValidationCategory(str, Enum):
    """Validation categories"""
    SECURITY = "security"
    PERFORMANCE = "performance"
    FUNCTIONALITY = "functionality"
    COMPLIANCE = "compliance"
    BEST_PRACTICE = "best_practice"

@dataclass
class ValidationResult:
    """Result of a validation check"""
    field: str
    value: Any
    level: ValidationLevel
    category: ValidationCategory
    message: str
    suggestion: Optional[str] = None
    rule_id: Optional[str] = None

@dataclass
class ValidationReport:
    """Comprehensive validation report"""
    is_valid: bool
    errors: List[ValidationResult]
    warnings: List[ValidationResult]
    info: List[ValidationResult]
    total_checks: int
    passed_checks: int
    timestamp: datetime
    environment: str
    configuration_summary: Dict[str, Any]

class ConfigurationValidator:
    """Comprehensive configuration validator"""

    def __init__(self):
        self.validators: Dict[str, Callable] = {
            'security': self._validate_security_config,
            'database': self._validate_database_config,
            'api': self._validate_api_config,
            'cache': self._validate_cache_config,
            'email': self._validate_email_config,
            'oanda': self._validate_oanda_config,
            'ai': self._validate_ai_config,
            'server': self._validate_server_config,
            'monitoring': self._validate_monitoring_config,
            'trading': self._validate_trading_config,
            'feature_flags': self._validate_feature_flags,
        }

    def validate_configuration(self, config: Dict[str, Any], environment: str) -> ValidationReport:
        """Validate entire configuration"""
        errors = []
        warnings = []
        info = []

        # Validate each section
        for section, validator in self.validators.items():
            if section in config:
                section_results = validator(config[section], environment)
                for result in section_results:
                    if result.level == ValidationLevel.ERROR:
                        errors.append(result)
                    elif result.level == ValidationLevel.WARNING:
                        warnings.append(result)
                    else:
                        info.append(result)

        # Cross-section validation
        cross_section_results = self._validate_cross_section(config, environment)
        for result in cross_section_results:
            if result.level == ValidationLevel.ERROR:
                errors.append(result)
            elif result.level == ValidationLevel.WARNING:
                warnings.append(result)
            else:
                info.append(result)

        # Environment-specific validation
        env_results = self._validate_environment_specific(config, environment)
        for result in env_results:
            if result.level == ValidationLevel.ERROR:
                errors.append(result)
            elif result.level == ValidationLevel.WARNING:
                warnings.append(result)
            else:
                info.append(result)

        total_checks = len(errors) + len(warnings) + len(info)
        passed_checks = total_checks - len(errors)

        return ValidationReport(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            info=info,
            total_checks=total_checks,
            passed_checks=passed_checks,
            timestamp=datetime.utcnow(),
            environment=environment,
            configuration_summary=self._generate_summary(config)
        )

    def _validate_security_config(self, security_config: Dict[str, Any], environment: str) -> List[ValidationResult]:
        """Validate security configuration"""
        results = []

        # JWT secret key validation
        jwt_secret = security_config.get('jwt_secret_key', '')
        if not jwt_secret:
            results.append(ValidationResult(
                field='security.jwt_secret_key',
                value=jwt_secret,
                level=ValidationLevel.ERROR,
                category=ValidationCategory.SECURITY,
                message='JWT secret key is required',
                suggestion='Set a secure JWT secret key with at least 32 characters',
                rule_id='SEC001'
            ))
        elif len(jwt_secret) < 32:
            results.append(ValidationResult(
                field='security.jwt_secret_key',
                value=jwt_secret,
                level=ValidationLevel.ERROR,
                category=ValidationCategory.SECURITY,
                message='JWT secret key is too short',
                suggestion='Use a JWT secret key with at least 32 characters',
                rule_id='SEC002'
            ))
        elif jwt_secret in ['your-secret-key-change-this-in-production', 'dev-secret-key', 'test-secret-key']:
            results.append(ValidationResult(
                field='security.jwt_secret_key',
                value=jwt_secret,
                level=ValidationLevel.ERROR if environment == 'production' else ValidationLevel.WARNING,
                category=ValidationCategory.SECURITY,
                message=f'JWT secret key is using default value',
                suggestion='Change to a secure, randomly generated secret key',
                rule_id='SEC003'
            ))

        # CORS validation
        cors_origins = security_config.get('cors_origins', [])
        if environment == 'production' and '*' in cors_origins:
            results.append(ValidationResult(
                field='security.cors_origins',
                value=cors_origins,
                level=ValidationLevel.ERROR,
                category=ValidationCategory.SECURITY,
                message='CORS origins cannot be "*" in production',
                suggestion='Specify exact allowed origins for production',
                rule_id='SEC004'
            ))

        # JWT expiration validation
        access_token_expire = security_config.get('jwt_access_token_expire_minutes', 30)
        if access_token_expire > 1440:  # 24 hours
            results.append(ValidationResult(
                field='security.jwt_access_token_expire_minutes',
                value=access_token_expire,
                level=ValidationLevel.WARNING,
                category=ValidationCategory.SECURITY,
                message='Access token expiration is too long',
                suggestion='Use shorter expiration times for better security',
                rule_id='SEC005'
            ))

        return results

    def _validate_database_config(self, database_config: Dict[str, Any], environment: str) -> List[ValidationResult]:
        """Validate database configuration"""
        results = []

        # Database URL validation
        db_url = database_config.get('url', '')
        if not db_url:
            results.append(ValidationResult(
                field='database.url',
                value=db_url,
                level=ValidationLevel.ERROR,
                category=ValidationCategory.FUNCTIONALITY,
                message='Database URL is required',
                suggestion='Set a valid database connection URL',
                rule_id='DB001'
            ))
        else:
            # Validate URL format
            if not self._is_valid_database_url(db_url):
                results.append(ValidationResult(
                    field='database.url',
                    value=db_url,
                    level=ValidationLevel.ERROR,
                    category=ValidationCategory.FUNCTIONALITY,
                    message='Invalid database URL format',
                    suggestion='Use a valid database URL (postgresql://, mysql://, or sqlite://)',
                    rule_id='DB002'
                ))

            # SSL validation for production
            if environment == 'production' and 'sslmode' in db_url.lower():
                if 'require' not in db_url.lower() and 'verify-full' not in db_url.lower():
                    results.append(ValidationResult(
                        field='database.url',
                        value=db_url,
                        level=ValidationLevel.WARNING,
                        category=ValidationCategory.SECURITY,
                        message='Database SSL mode should be "require" or "verify-full" in production',
                        suggestion='Enable SSL for database connections in production',
                        rule_id='DB003'
                    ))

        # Pool size validation
        pool_size = database_config.get('pool_size', 20)
        if environment == 'production' and pool_size < 10:
            results.append(ValidationResult(
                field='database.pool_size',
                value=pool_size,
                level=ValidationLevel.WARNING,
                category=ValidationCategory.PERFORMANCE,
                message='Database pool size might be too small for production',
                suggestion='Increase pool size for better performance',
                rule_id='DB004'
            ))

        return results

    def _validate_api_config(self, api_config: Dict[str, Any], environment: str) -> List[ValidationResult]:
        """Validate API configuration"""
        results = []

        # Rate limiting validation
        rate_limit = api_config.get('rate_limit_requests', 100)
        if environment == 'production' and rate_limit > 1000:
            results.append(ValidationResult(
                field='api.rate_limit_requests',
                value=rate_limit,
                level=ValidationLevel.WARNING,
                category=ValidationCategory.PERFORMANCE,
                message='High rate limit may impact system performance',
                suggestion='Consider reducing rate limit for production',
                rule_id='API001'
            ))

        # Documentation access in production
        docs_url = api_config.get('docs_url')
        if environment == 'production' and docs_url:
            results.append(ValidationResult(
                field='api.docs_url',
                value=docs_url,
                level=ValidationLevel.WARNING,
                category=ValidationCategory.SECURITY,
                message='API documentation should be disabled in production',
                suggestion='Set docs_url to None in production',
                rule_id='API002'
            ))

        # CORS headers validation
        cors_headers = api_config.get('cors_allow_headers', [])
        if environment == 'production' and '*' in cors_headers:
            results.append(ValidationResult(
                field='api.cors_allow_headers',
                value=cors_headers,
                level=ValidationLevel.WARNING,
                category=ValidationCategory.SECURITY,
                message='CORS headers should be specific in production',
                suggestion='Specify exact allowed headers',
                rule_id='API003'
            ))

        return results

    def _validate_cache_config(self, cache_config: Dict[str, Any], environment: str) -> List[ValidationResult]:
        """Validate cache configuration"""
        results = []

        # Redis URL validation
        redis_url = cache_config.get('redis_url', '')
        if redis_url and not redis_url.startswith('redis://'):
            results.append(ValidationResult(
                field='cache.redis_url',
                value=redis_url,
                level=ValidationLevel.WARNING,
                category=ValidationCategory.FUNCTIONALITY,
                message='Redis URL should start with redis://',
                suggestion='Use proper Redis URL format',
                rule_id='CACHE001'
            ))

        # TTL validation
        ttl_short = cache_config.get('ttl_short', 300)
        ttl_long = cache_config.get('ttl_long', 3600)
        if ttl_short >= ttl_long:
            results.append(ValidationResult(
                field='cache.ttl_short',
                value=ttl_short,
                level=ValidationLevel.WARNING,
                category=ValidationCategory.PERFORMANCE,
                message='Short TTL should be less than long TTL',
                suggestion='Adjust TTL values for better caching strategy',
                rule_id='CACHE002'
            ))

        return results

    def _validate_email_config(self, email_config: Dict[str, Any], environment: str) -> List[ValidationResult]:
        """Validate email configuration"""
        results = []

        # Email validation
        email_from = email_config.get('from_address', '')
        if email_from and not self._is_valid_email(email_from):
            results.append(ValidationResult(
                field='email.from_address',
                value=email_from,
                level=ValidationLevel.WARNING,
                category=ValidationCategory.FUNCTIONALITY,
                message='Invalid email address format',
                suggestion='Use a valid email address',
                rule_id='EMAIL001'
            ))

        # Port validation
        email_port = email_config.get('port', 587)
        if email_port not in [25, 465, 587, 2525]:
            results.append(ValidationResult(
                field='email.port',
                value=email_port,
                level=ValidationLevel.WARNING,
                category=ValidationCategory.FUNCTIONALITY,
                message='Unusual email port specified',
                suggestion='Use standard email ports: 25, 465, 587, or 2525',
                rule_id='EMAIL002'
            ))

        return results

    def _validate_oanda_config(self, oanda_config: Dict[str, Any], environment: str) -> List[ValidationResult]:
        """Validate OANDA configuration"""
        results = []

        # API key validation
        api_key = oanda_config.get('api_key', '')
        if not api_key:
            results.append(ValidationResult(
                field='oanda.api_key',
                value=api_key,
                level=ValidationLevel.ERROR,
                category=ValidationCategory.FUNCTIONALITY,
                message='OANDA API key is required',
                suggestion='Set a valid OANDA API key',
                rule_id='OANDA001'
            ))
        elif len(api_key) < 10:
            results.append(ValidationResult(
                field='oanda.api_key',
                value=api_key,
                level=ValidationLevel.WARNING,
                category=ValidationCategory.SECURITY,
                message='OANDA API key seems too short',
                suggestion='Verify the API key is correct',
                rule_id='OANDA002'
            ))

        # Account ID validation
        account_id = oanda_config.get('account_id', '')
        if not account_id:
            results.append(ValidationResult(
                field='oanda.account_id',
                value=account_id,
                level=ValidationLevel.ERROR,
                category=ValidationCategory.FUNCTIONALITY,
                message='OANDA account ID is required',
                suggestion='Set a valid OANDA account ID',
                rule_id='OANDA003'
            ))

        # Environment validation
        oanda_env = oanda_config.get('environment', 'demo')
        if oanda_env not in ['demo', 'live']:
            results.append(ValidationResult(
                field='oanda.environment',
                value=oanda_env,
                level=ValidationLevel.WARNING,
                category=ValidationCategory.FUNCTIONALITY,
                message='OANDA environment should be "demo" or "live"',
                suggestion='Use "demo" for testing, "live" for production',
                rule_id='OANDA004'
            ))

        return results

    def _validate_ai_config(self, ai_config: Dict[str, Any], environment: str) -> List[ValidationResult]:
        """Validate AI configuration"""
        results = []

        # API key validation
        api_key = ai_config.get('gemini_api_key', '')
        if not api_key:
            results.append(ValidationResult(
                field='ai.gemini_api_key',
                value=api_key,
                level=ValidationLevel.ERROR,
                category=ValidationCategory.FUNCTIONALITY,
                message='Gemini API key is required',
                suggestion='Set a valid Gemini API key',
                rule_id='AI001'
            ))

        # Temperature validation
        temperature = ai_config.get('temperature', 0.7)
        if not (0.0 <= temperature <= 1.0):
            results.append(ValidationResult(
                field='ai.temperature',
                value=temperature,
                level=ValidationLevel.WARNING,
                category=ValidationCategory.FUNCTIONALITY,
                message='Temperature should be between 0.0 and 1.0',
                suggestion='Adjust temperature to valid range',
                rule_id='AI002'
            ))

        # Confidence threshold validation
        confidence_threshold = ai_config.get('confidence_threshold', 0.6)
        if not (0.0 <= confidence_threshold <= 1.0):
            results.append(ValidationResult(
                field='ai.confidence_threshold',
                value=confidence_threshold,
                level=ValidationLevel.WARNING,
                category=ValidationCategory.FUNCTIONALITY,
                message='Confidence threshold should be between 0.0 and 1.0',
                suggestion='Adjust confidence threshold to valid range',
                rule_id='AI003'
            ))

        return results

    def _validate_server_config(self, server_config: Dict[str, Any], environment: str) -> List[ValidationResult]:
        """Validate server configuration"""
        results = []

        # Host validation
        host = server_config.get('host', '127.0.0.1')
        if environment == 'production' and host == '127.0.0.1':
            results.append(ValidationResult(
                field='server.host',
                value=host,
                level=ValidationLevel.WARNING,
                category=ValidationCategory.FUNCTIONALITY,
                message='Production server should bind to 0.0.0.0',
                suggestion='Change host to "0.0.0.0" for production',
                rule_id='SRV001'
            ))

        # Port validation
        port = server_config.get('port', 8000)
        if not (1 <= port <= 65535):
            results.append(ValidationResult(
                field='server.port',
                value=port,
                level=ValidationLevel.ERROR,
                category=ValidationCategory.FUNCTIONALITY,
                message='Invalid port number',
                suggestion='Use a valid port number (1-65535)',
                rule_id='SRV002'
            ))

        # Workers validation
        workers = server_config.get('workers', 4)
        if environment == 'production' and workers < 2:
            results.append(ValidationResult(
                field='server.workers',
                value=workers,
                level=ValidationLevel.WARNING,
                category=ValidationCategory.PERFORMANCE,
                message='Production should use multiple workers',
                suggestion='Increase worker count for better performance',
                rule_id='SRV003'
            ))

        # Debug mode validation
        debug = server_config.get('debug', False)
        if environment == 'production' and debug:
            results.append(ValidationResult(
                field='server.debug',
                value=debug,
                level=ValidationLevel.ERROR,
                category=ValidationCategory.SECURITY,
                message='Debug mode should be disabled in production',
                suggestion='Set debug to False in production',
                rule_id='SRV004'
            ))

        return results

    def _validate_monitoring_config(self, monitoring_config: Dict[str, Any], environment: str) -> List[ValidationResult]:
        """Validate monitoring configuration"""
        results = []

        # Log level validation
        log_level = monitoring_config.get('log_level', 'INFO')
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if log_level not in valid_levels:
            results.append(ValidationResult(
                field='monitoring.log_level',
                value=log_level,
                level=ValidationLevel.WARNING,
                category=ValidationCategory.FUNCTIONALITY,
                message=f'Invalid log level: {log_level}',
                suggestion=f'Use one of: {valid_levels}',
                rule_id='MON001'
            ))

        # Sentry DSN validation
        sentry_dsn = monitoring_config.get('sentry_dsn', '')
        if sentry_dsn and not sentry_dsn.startswith('https://'):
            results.append(ValidationResult(
                field='monitoring.sentry_dsn',
                value=sentry_dsn,
                level=ValidationLevel.WARNING,
                category=ValidationCategory.FUNCTIONALITY,
                message='Sentry DSN should start with https://',
                suggestion='Use a valid Sentry DSN',
                rule_id='MON002'
            ))

        return results

    def _validate_trading_config(self, trading_config: Dict[str, Any], environment: str) -> List[ValidationResult]:
        """Validate trading configuration"""
        results = []

        # Position size validation
        default_position_size = trading_config.get('default_position_size', 0.01)
        if default_position_size <= 0 or default_position_size > 1:
            results.append(ValidationResult(
                field='trading.default_position_size',
                value=default_position_size,
                level=ValidationLevel.WARNING,
                category=ValidationCategory.FUNCTIONALITY,
                message='Position size should be between 0 and 1',
                suggestion='Use a reasonable position size',
                rule_id='TRD001'
            ))

        # Risk level validation
        risk_level = trading_config.get('default_risk_level', 'MEDIUM')
        if risk_level not in ['LOW', 'MEDIUM', 'HIGH']:
            results.append(ValidationResult(
                field='trading.default_risk_level',
                value=risk_level,
                level=ValidationLevel.WARNING,
                category=ValidationCategory.FUNCTIONALITY,
                message='Risk level should be LOW, MEDIUM, or HIGH',
                suggestion='Use a valid risk level',
                rule_id='TRD002'
            ))

        # Signal generation interval validation
        signal_interval = trading_config.get('signal_generation_interval', 300)
        if signal_interval < 1:
            results.append(ValidationResult(
                field='trading.signal_generation_interval',
                value=signal_interval,
                level=ValidationLevel.WARNING,
                category=ValidationCategory.PERFORMANCE,
                message='Signal generation interval should be at least 1 second',
                suggestion='Use a reasonable interval',
                rule_id='TRD003'
            ))

        return results

    def _validate_feature_flags(self, feature_flags: Dict[str, Any], environment: str) -> List[ValidationResult]:
        """Validate feature flags"""
        results = []

        # Check for invalid feature flag values
        for flag_name, flag_value in feature_flags.items():
            if not isinstance(flag_value, bool):
                results.append(ValidationResult(
                    field=f'feature_flags.{flag_name}',
                    value=flag_value,
                    level=ValidationLevel.WARNING,
                    category=ValidationCategory.FUNCTIONALITY,
                    message=f'Feature flag "{flag_name}" should be a boolean',
                    suggestion='Use true or false for feature flags',
                    rule_id='FF001'
                ))

        return results

    def _validate_cross_section(self, config: Dict[str, Any], environment: str) -> List[ValidationResult]:
        """Validate cross-section configuration dependencies"""
        results = []

        # Check if email notifications are enabled but email config is incomplete
        feature_flags = config.get('feature_flags', {})
        email_config = config.get('email', {})

        if feature_flags.get('enable_email_notifications', False):
            if not email_config.get('host') or not email_config.get('user'):
                results.append(ValidationResult(
                    field='email_notifications',
                    value=True,
                    level=ValidationLevel.ERROR,
                    category=ValidationCategory.FUNCTIONALITY,
                    message='Email notifications enabled but email configuration is incomplete',
                    suggestion='Configure email settings or disable email notifications',
                    rule_id='CROSS001'
                ))

        # Check if AI analysis is enabled but API key is missing
        ai_config = config.get('ai', {})
        if feature_flags.get('enable_ai_analysis', False) and not ai_config.get('gemini_api_key'):
            results.append(ValidationResult(
                field='ai_analysis',
                value=True,
                level=ValidationLevel.ERROR,
                category=ValidationCategory.FUNCTIONALITY,
                message='AI analysis enabled but Gemini API key is missing',
                suggestion='Configure Gemini API key or disable AI analysis',
                rule_id='CROSS002'
            ))

        # Check if real trading is enabled in development
        trading_config = config.get('trading', {})
        if (environment == 'development' and
            trading_config.get('enable_real_trading', False)):
            results.append(ValidationResult(
                field='trading.enable_real_trading',
                value=True,
                level=ValidationLevel.WARNING,
                category=ValidationCategory.SECURITY,
                message='Real trading should be disabled in development',
                suggestion='Use paper trading for development',
                rule_id='CROSS003'
            ))

        return results

    def _validate_environment_specific(self, config: Dict[str, Any], environment: str) -> List[ValidationResult]:
        """Validate environment-specific requirements"""
        results = []

        if environment == 'production':
            # Production-specific validations
            security_config = config.get('security', {})
            if security_config.get('cors_allow_credentials', True) and '*' in security_config.get('cors_origins', []):
                results.append(ValidationResult(
                    field='production_security',
                    value='insecure_cors',
                    level=ValidationLevel.ERROR,
                    category=ValidationCategory.SECURITY,
                    message='Production cannot use wildcard CORS with credentials',
                    suggestion='Specify exact CORS origins for production',
                    rule_id='ENV001'
                ))

            # Check for required production features
            monitoring_config = config.get('monitoring', {})
            if not monitoring_config.get('enable_error_tracking', False):
                results.append(ValidationResult(
                    field='monitoring.enable_error_tracking',
                    value=False,
                    level=ValidationLevel.WARNING,
                    category=ValidationCategory.COMPLIANCE,
                    message='Error tracking should be enabled in production',
                    suggestion='Enable error tracking for better monitoring',
                    rule_id='ENV002'
                ))

        elif environment == 'development':
            # Development-specific validations
            server_config = config.get('server', {})
            if not server_config.get('debug', False):
                results.append(ValidationResult(
                    field='server.debug',
                    value=False,
                    level=ValidationLevel.WARNING,
                    category=ValidationCategory.BEST_PRACTICE,
                    message='Debug mode should be enabled in development',
                    suggestion='Enable debug mode for better development experience',
                    rule_id='ENV003'
                ))

        return results

    def _generate_summary(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate configuration summary"""
        return {
            'total_sections': len(config),
            'sections': list(config.keys()),
            'environment': config.get('app', {}).get('environment', 'unknown'),
            'debug_mode': config.get('server', {}).get('debug', False),
            'has_database': 'database' in config,
            'has_cache': 'cache' in config,
            'has_email': 'email' in config,
            'has_oanda': 'oanda' in config,
            'has_ai': 'ai' in config,
        }

    def _is_valid_database_url(self, url: str) -> bool:
        """Check if database URL is valid"""
        return any(url.startswith(prefix) for prefix in [
            'postgresql://', 'mysql://', 'sqlite:///'
        ])

    def _is_valid_email(self, email: str) -> bool:
        """Check if email address is valid"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def get_validation_rules(self) -> Dict[str, str]:
        """Get all validation rules with descriptions"""
        return {
            'SEC001': 'JWT secret key is required for security',
            'SEC002': 'JWT secret key must be at least 32 characters',
            'SEC003': 'JWT secret key should not use default values',
            'SEC004': 'CORS origins cannot be wildcard in production',
            'SEC005': 'Access token expiration should be reasonable',
            'DB001': 'Database URL is required',
            'DB002': 'Database URL format must be valid',
            'DB003': 'Database SSL should be enabled in production',
            'DB004': 'Database pool size should be adequate',
            'API001': 'Rate limiting should be reasonable',
            'API002': 'API docs should be disabled in production',
            'API003': 'CORS headers should be specific in production',
            'CACHE001': 'Redis URL format should be valid',
            'CACHE002': 'Cache TTL values should be logical',
            'EMAIL001': 'Email address format should be valid',
            'EMAIL002': 'Email port should be standard',
            'OANDA001': 'OANDA API key is required',
            'OANDA002': 'OANDA API key should be valid',
            'OANDA003': 'OANDA account ID is required',
            'OANDA004': 'OANDA environment should be valid',
            'AI001': 'Gemini API key is required',
            'AI002': 'AI temperature should be valid',
            'AI003': 'AI confidence threshold should be valid',
            'SRV001': 'Production server should bind to 0.0.0.0',
            'SRV002': 'Server port should be valid',
            'SRV003': 'Production should use multiple workers',
            'SRV004': 'Debug mode should be disabled in production',
            'MON001': 'Log level should be valid',
            'MON002': 'Sentry DSN should be valid',
            'TRD001': 'Position size should be reasonable',
            'TRD002': 'Risk level should be valid',
            'TRD003': 'Signal interval should be reasonable',
            'FF001': 'Feature flags should be boolean',
            'CROSS001': 'Email notifications require email config',
            'CROSS002': 'AI analysis requires API key',
            'CROSS003': 'Real trading should not be used in development',
            'ENV001': 'Production security requirements',
            'ENV002': 'Production monitoring requirements',
            'ENV003': 'Development debug recommendations',
        }