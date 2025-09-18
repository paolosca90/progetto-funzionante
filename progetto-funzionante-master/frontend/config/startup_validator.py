"""
Configuration Validation System for Application Startup
Validates configuration before application starts and provides detailed error reporting
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ValidationLevel(str, Enum):
    """Validation severity levels"""
    CRITICAL = "critical"  # Application cannot start
    ERROR = "error"       # Application may start but with limitations
    WARNING = "warning"   # Application can start but should be reviewed
    INFO = "info"         # Informational messages

@dataclass
class ValidationResult:
    """Result of a configuration validation"""
    key: str
    level: ValidationLevel
    message: str
    suggestion: str = None
    required: bool = False
    default_value: Any = None

@dataclass
class ConfigurationHealthReport:
    """Comprehensive configuration health report"""
    overall_status: str  # "healthy", "degraded", "unhealthy"
    validation_results: List[ValidationResult]
    critical_issues: int
    error_issues: int
    warning_issues: int
    info_messages: int
    environment: str
    timestamp: datetime
    can_start: bool

class ConfigurationValidator:
    """Validates configuration at application startup"""

    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.validation_rules = self._get_validation_rules()

    def _get_validation_rules(self) -> Dict[str, Dict[str, Any]]:
        """Get validation rules for all configuration keys"""
        return {
            # Database configuration
            'database_url': {
                'required': True,
                'level': ValidationLevel.CRITICAL,
                'pattern': r'^(postgresql|mysql|sqlite)://.*',
                'suggestion': 'Configure DATABASE_URL environment variable',
                'default': None
            },
            'database.pool_size': {
                'required': False,
                'level': ValidationLevel.WARNING,
                'min': 1,
                'max': 50,
                'suggestion': 'Set database pool size between 1-50',
                'default': 10
            },
            'database.max_overflow': {
                'required': False,
                'level': ValidationLevel.WARNING,
                'min': 0,
                'max': 100,
                'suggestion': 'Set database max overflow between 0-100',
                'default': 20
            },

            # Security configuration
            'jwt_secret_key': {
                'required': True,
                'level': ValidationLevel.CRITICAL,
                'min_length': 32,
                'suggestion': 'Set JWT_SECRET_KEY with at least 32 characters',
                'default': None
            },
            'jwt_algorithm': {
                'required': False,
                'level': ValidationLevel.WARNING,
                'allowed_values': ['HS256', 'HS384', 'HS512', 'RS256', 'RS384', 'RS512'],
                'suggestion': 'Use HS256 for HMAC or RS256 for RSA',
                'default': 'HS256'
            },
            'jwt_access_token_expire_minutes': {
                'required': False,
                'level': ValidationLevel.WARNING,
                'min': 1,
                'max': 1440,
                'suggestion': 'Set token expiration between 1-1440 minutes',
                'default': 30
            },

            # API configuration
            'oanda_api_key': {
                'required': True,
                'level': ValidationLevel.CRITICAL,
                'min_length': 1,
                'suggestion': 'Set OANDA_API_KEY environment variable',
                'default': None
            },
            'oanda_account_id': {
                'required': True,
                'level': ValidationLevel.CRITICAL,
                'min_length': 1,
                'suggestion': 'Set OANDA_ACCOUNT_ID environment variable',
                'default': None
            },
            'oanda_environment': {
                'required': False,
                'level': ValidationLevel.WARNING,
                'allowed_values': ['demo', 'live'],
                'suggestion': 'Set OANDA environment to "demo" or "live"',
                'default': 'demo'
            },
            'gemini_api_key': {
                'required': True,
                'level': ValidationLevel.CRITICAL,
                'min_length': 1,
                'suggestion': 'Set GEMINI_API_KEY environment variable',
                'default': None
            },

            # Email configuration
            'email_host': {
                'required': False,
                'level': ValidationLevel.WARNING,
                'pattern': r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
                'suggestion': 'Configure email host for registration emails',
                'default': None
            },
            'email_user': {
                'required': False,
                'level': ValidationLevel.WARNING,
                'suggestion': 'Configure email user for authentication',
                'default': None
            },
            'email_password': {
                'required': False,
                'level': ValidationLevel.WARNING,
                'suggestion': 'Configure email password for authentication',
                'default': None
            },

            # Application configuration
            'app_name': {
                'required': False,
                'level': ValidationLevel.INFO,
                'suggestion': 'Set application name for branding',
                'default': 'Trading Signals System'
            },
            'app_version': {
                'required': False,
                'level': ValidationLevel.INFO,
                'suggestion': 'Set application version',
                'default': '1.0.0'
            },
            'environment': {
                'required': False,
                'level': ValidationLevel.WARNING,
                'allowed_values': ['development', 'staging', 'production', 'test'],
                'suggestion': 'Set environment to development, staging, production, or test',
                'default': 'development'
            },
            'debug': {
                'required': False,
                'level': ValidationLevel.WARNING,
                'suggestion': 'Set debug mode (should be False in production)',
                'default': False
            },

            # Server configuration
            'host': {
                'required': False,
                'level': ValidationLevel.WARNING,
                'pattern': r'^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$|localhost$',
                'suggestion': 'Set server host address',
                'default': '127.0.0.1'
            },
            'port': {
                'required': False,
                'level': ValidationLevel.WARNING,
                'min': 1,
                'max': 65535,
                'suggestion': 'Set server port between 1-65535',
                'default': 8000
            },
            'workers': {
                'required': False,
                'level': ValidationLevel.INFO,
                'min': 1,
                'max': 20,
                'suggestion': 'Set number of worker processes',
                'default': 1
            },

            # CORS configuration
            'cors_origins': {
                'required': False,
                'level': ValidationLevel.WARNING,
                'suggestion': 'Configure allowed CORS origins',
                'default': ['*']
            },
            'cors_allow_credentials': {
                'required': False,
                'level': ValidationLevel.INFO,
                'suggestion': 'Configure CORS credentials',
                'default': True
            },

            # Rate limiting
            'rate_limit_requests': {
                'required': False,
                'level': ValidationLevel.INFO,
                'min': 1,
                'max': 10000,
                'suggestion': 'Set rate limit requests per minute',
                'default': 100
            },
            'rate_limit_window': {
                'required': False,
                'level': ValidationLevel.INFO,
                'min': 1,
                'max': 3600,
                'suggestion': 'Set rate limit window in seconds',
                'default': 60
            },

            # Logging configuration
            'log_level': {
                'required': False,
                'level': ValidationLevel.WARNING,
                'allowed_values': ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                'suggestion': 'Set logging level',
                'default': 'INFO'
            },
            'log_file': {
                'required': False,
                'level': ValidationLevel.INFO,
                'suggestion': 'Configure log file path',
                'default': None
            },

            # Security headers
            'security_require_https': {
                'required': False,
                'level': ValidationLevel.WARNING,
                'suggestion': 'Enable HTTPS requirement in production',
                'default': False
            },
            'security_hsts_enabled': {
                'required': False,
                'level': ValidationLevel.WARNING,
                'suggestion': 'Enable HSTS for security',
                'default': False
            },
            'security_hsts_max_age': {
                'required': False,
                'level': ValidationLevel.INFO,
                'min': 0,
                'max': 31536000,
                'suggestion': 'Set HSTS max age in seconds',
                'default': 31536000
            },

            # Monitoring configuration
            'monitoring_enable_metrics': {
                'required': False,
                'level': ValidationLevel.INFO,
                'suggestion': 'Enable application metrics',
                'default': False
            },
            'monitoring_enable_error_tracking': {
                'required': False,
                'level': ValidationLevel.INFO,
                'suggestion': 'Enable error tracking',
                'default': False
            },
            'monitoring_enable_health_checks': {
                'required': False,
                'level': ValidationLevel.INFO,
                'suggestion': 'Enable health check endpoints',
                'default': True
            },

            # Railway configuration
            'railway_enable': {
                'required': False,
                'level': ValidationLevel.INFO,
                'suggestion': 'Enable Railway deployment features',
                'default': False
            },
            'railway_domain': {
                'required': False,
                'level': ValidationLevel.INFO,
                'suggestion': 'Configure Railway domain',
                'default': None
            }
        }

    def validate_configuration(self) -> ConfigurationHealthReport:
        """Validate all configuration and return health report"""
        validation_results = []

        # Validate each configuration rule
        for config_key, rule in self.validation_rules.items():
            result = self._validate_config_key(config_key, rule)
            validation_results.append(result)

        # Environment-specific validations
        environment = self.config_manager.get('environment', 'development')
        env_results = self._validate_environment_specific(environment)
        validation_results.extend(env_results)

        # Calculate overall status
        critical_count = sum(1 for r in validation_results if r.level == ValidationLevel.CRITICAL)
        error_count = sum(1 for r in validation_results if r.level == ValidationLevel.ERROR)
        warning_count = sum(1 for r in validation_results if r.level == ValidationLevel.WARNING)
        info_count = sum(1 for r in validation_results if r.level == ValidationLevel.INFO)

        if critical_count > 0:
            overall_status = "unhealthy"
            can_start = False
        elif error_count > 0:
            overall_status = "degraded"
            can_start = True
        else:
            overall_status = "healthy"
            can_start = True

        return ConfigurationHealthReport(
            overall_status=overall_status,
            validation_results=validation_results,
            critical_issues=critical_count,
            error_issues=error_count,
            warning_issues=warning_count,
            info_messages=info_count,
            environment=environment,
            timestamp=datetime.utcnow(),
            can_start=can_start
        )

    def _validate_config_key(self, config_key: str, rule: Dict[str, Any]) -> ValidationResult:
        """Validate a single configuration key"""
        value = self.config_manager.get(config_key)
        rule_level = rule['level']
        required = rule['required']

        # Check if required configuration is missing
        if required and value is None:
            return ValidationResult(
                key=config_key,
                level=rule_level,
                message=f"Required configuration '{config_key}' is missing",
                suggestion=rule['suggestion'],
                required=True,
                default_value=rule['default']
            )

        # If not required and missing, skip validation
        if value is None:
            return ValidationResult(
                key=config_key,
                level=ValidationLevel.INFO,
                message=f"Optional configuration '{config_key}' is not set",
                suggestion=rule['suggestion'],
                required=False,
                default_value=rule['default']
            )

        # Validate based on rule type
        if 'pattern' in rule:
            import re
            if not re.match(rule['pattern'], str(value)):
                return ValidationResult(
                    key=config_key,
                    level=rule_level,
                    message=f"Configuration '{config_key}' does not match required pattern: {rule['pattern']}",
                    suggestion=rule['suggestion'],
                    required=required,
                    default_value=rule['default']
                )

        if 'min_length' in rule:
            if len(str(value)) < rule['min_length']:
                return ValidationResult(
                    key=config_key,
                    level=rule_level,
                    message=f"Configuration '{config_key}' is too short (min {rule['min_length']} characters)",
                    suggestion=rule['suggestion'],
                    required=required,
                    default_value=rule['default']
                )

        if 'min' in rule:
            try:
                numeric_value = float(value)
                if numeric_value < rule['min']:
                    return ValidationResult(
                        key=config_key,
                        level=rule_level,
                        message=f"Configuration '{config_key}' is below minimum value {rule['min']}",
                        suggestion=rule['suggestion'],
                        required=required,
                        default_value=rule['default']
                    )
            except (ValueError, TypeError):
                return ValidationResult(
                    key=config_key,
                    level=rule_level,
                    message=f"Configuration '{config_key}' is not a valid number",
                    suggestion=rule['suggestion'],
                    required=required,
                    default_value=rule['default']
                )

        if 'max' in rule:
            try:
                numeric_value = float(value)
                if numeric_value > rule['max']:
                    return ValidationResult(
                        key=config_key,
                        level=rule_level,
                        message=f"Configuration '{config_key}' exceeds maximum value {rule['max']}",
                        suggestion=rule['suggestion'],
                        required=required,
                        default_value=rule['default']
                    )
            except (ValueError, TypeError):
                return ValidationResult(
                    key=config_key,
                    level=rule_level,
                    message=f"Configuration '{config_key}' is not a valid number",
                    suggestion=rule['suggestion'],
                    required=required,
                    default_value=rule['default']
                )

        if 'allowed_values' in rule:
            if value not in rule['allowed_values']:
                return ValidationResult(
                    key=config_key,
                    level=rule_level,
                    message=f"Configuration '{config_key}' has invalid value '{value}'. Allowed values: {rule['allowed_values']}",
                    suggestion=rule['suggestion'],
                    required=required,
                    default_value=rule['default']
                )

        # Configuration is valid
        return ValidationResult(
            key=config_key,
            level=ValidationLevel.INFO,
            message=f"Configuration '{config_key}' is valid",
            suggestion=None,
            required=required,
            default_value=None
        )

    def _validate_environment_specific(self, environment: str) -> List[ValidationResult]:
        """Validate environment-specific configuration"""
        results = []

        if environment == 'production':
            # Production-specific validations
            if self.config_manager.get('debug', False):
                results.append(ValidationResult(
                    key='debug',
                    level=ValidationLevel.ERROR,
                    message="Debug mode is enabled in production environment",
                    suggestion="Set debug=False in production",
                    required=False
                ))

            if not self.config_manager.get('security_require_https', False):
                results.append(ValidationResult(
                    key='security_require_https',
                    level=ValidationLevel.ERROR,
                    message="HTTPS is not required in production environment",
                    suggestion="Set security_require_https=True in production",
                    required=False
                ))

            if not self.config_manager.get('security_hsts_enabled', False):
                results.append(ValidationResult(
                    key='security_hsts_enabled',
                    level=ValidationLevel.WARNING,
                    message="HSTS is not enabled in production environment",
                    suggestion="Set security_hsts_enabled=True in production",
                    required=False
                ))

            if self.config_manager.get('cors_origins') == ['*']:
                results.append(ValidationResult(
                    key='cors_origins',
                    level=ValidationLevel.ERROR,
                    message="CORS is set to allow all origins in production",
                    suggestion="Configure specific CORS origins in production",
                    required=False
                ))

        elif environment == 'development':
            # Development-specific validations
            if not self.config_manager.get('debug', False):
                results.append(ValidationResult(
                    key='debug',
                    level=ValidationLevel.INFO,
                    message="Debug mode is disabled in development environment",
                    suggestion="Consider enabling debug mode for development",
                    required=False
                ))

        elif environment == 'staging':
            # Staging-specific validations
            if self.config_manager.get('debug', False):
                results.append(ValidationResult(
                    key='debug',
                    level=ValidationLevel.WARNING,
                    message="Debug mode is enabled in staging environment",
                    suggestion="Set debug=False in staging",
                    required=False
                ))

        return results

    def apply_defaults(self) -> Dict[str, Any]:
        """Apply default values for missing configuration"""
        applied_defaults = {}

        for config_key, rule in self.validation_rules.items():
            if self.config_manager.get(config_key) is None and 'default' in rule:
                default_value = rule['default']
                if default_value is not None:
                    self.config_manager.set(config_key, default_value)
                    applied_defaults[config_key] = default_value

        if applied_defaults:
            logger.info(f"Applied default values for {len(applied_defaults)} configuration keys")
            for key, value in applied_defaults.items():
                logger.info(f"  {key} = {value}")

        return applied_defaults

    def generate_config_file(self, template_path: Path = None) -> str:
        """Generate a configuration file template"""
        template_lines = [
            "# Configuration File Template",
            f"# Generated on {datetime.utcnow().isoformat()}",
            "# Environment: " + self.config_manager.get('environment', 'development'),
            "",
        ]

        # Group configurations by category
        categories = {
            'database': [],
            'security': [],
            'api': [],
            'email': [],
            'application': [],
            'server': [],
            'cors': [],
            'rate_limiting': [],
            'logging': [],
            'monitoring': [],
            'railway': []
        }

        for config_key, rule in self.validation_rules.items():
            category = self._get_config_category(config_key)
            if category in categories:
                categories[category].append((config_key, rule))

        # Generate configuration sections
        for category, keys in categories.items():
            if keys:
                template_lines.append(f"# {category.upper().replace('_', ' ').title()} Configuration")
                for config_key, rule in keys:
                    current_value = self.config_manager.get(config_key)
                    default_value = rule.get('default', '')

                    template_lines.append(f"# {rule['suggestion']}")
                    if rule['required']:
                        template_lines.append(f"# Required: {rule['level'].value}")
                    template_lines.append(f"{config_key}: {current_value or default_value}")
                    template_lines.append("")

        return "\n".join(template_lines)

    def _get_config_category(self, config_key: str) -> str:
        """Get configuration category"""
        if 'database' in config_key:
            return 'database'
        elif 'jwt' in config_key or 'security' in config_key:
            return 'security'
        elif 'oanda' in config_key or 'gemini' in config_key:
            return 'api'
        elif 'email' in config_key:
            return 'email'
        elif 'app' in config_key or 'environment' in config_key or 'debug' in config_key:
            return 'application'
        elif 'host' in config_key or 'port' in config_key or 'workers' in config_key:
            return 'server'
        elif 'cors' in config_key:
            return 'cors'
        elif 'rate_limit' in config_key:
            return 'rate_limiting'
        elif 'log' in config_key:
            return 'logging'
        elif 'monitoring' in config_key:
            return 'monitoring'
        elif 'railway' in config_key:
            return 'railway'
        else:
            return 'other'

def validate_application_startup(config_manager) -> ConfigurationHealthReport:
    """Validate configuration at application startup"""
    validator = ConfigurationValidator(config_manager)
    health_report = validator.validate_configuration()

    # Log validation results
    logger.info(f"Configuration validation completed")
    logger.info(f"Overall status: {health_report.overall_status}")
    logger.info(f"Critical issues: {health_report.critical_issues}")
    logger.info(f"Error issues: {health_report.error_issues}")
    logger.info(f"Warning issues: {health_report.warning_issues}")
    logger.info(f"Info messages: {health_report.info_messages}")

    # Log detailed results
    for result in health_report.validation_results:
        if result.level in [ValidationLevel.CRITICAL, ValidationLevel.ERROR]:
            logger.error(f"[{result.level.value.upper()}] {result.message}")
        elif result.level == ValidationLevel.WARNING:
            logger.warning(f"[{result.level.value.upper()}] {result.message}")
        else:
            logger.info(f"[{result.level.value.upper()}] {result.message}")

    # Apply defaults if needed
    applied_defaults = validator.apply_defaults()
    if applied_defaults:
        logger.info(f"Applied {len(applied_defaults)} default configuration values")

    # Check if application can start
    if not health_report.can_start:
        logger.error("Application cannot start due to critical configuration issues")
        logger.error("Please fix the critical issues before starting the application")
        sys.exit(1)
    elif health_report.critical_issues == 0 and health_report.error_issues > 0:
        logger.warning("Application can start but has configuration errors")
    else:
        logger.info("Application configuration is healthy")

    return health_report