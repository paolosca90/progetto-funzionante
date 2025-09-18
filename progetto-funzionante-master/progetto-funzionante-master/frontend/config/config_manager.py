"""
Configuration Management Utilities

This module provides utilities for managing configuration across different environments,
including validation, migration, and deployment helpers.
"""

import os
import json
import secrets
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from datetime import datetime
import logging

from config.settings import settings, Environment, Settings

logger = logging.getLogger(__name__)


class ConfigurationManager:
    """Configuration Management System"""

    def __init__(self):
        self.settings = settings
        self.config_history: List[Dict[str, Any]] = []

    def generate_jwt_secret(self, length: int = 64) -> str:
        """Generate a secure JWT secret key"""
        return secrets.token_urlsafe(length)

    def generate_database_url(self,
                            host: str,
                            port: int,
                            database: str,
                            username: str,
                            password: str,
                            driver: str = "postgresql") -> str:
        """Generate database URL from components"""
        return f"{driver}://{username}:{password}@{host}:{port}/{database}"

    def validate_environment_file(self, env_file_path: str) -> Dict[str, Any]:
        """Validate an environment file"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "info": [],
            "required_vars": [],
            "optional_vars": [],
            "deprecated_vars": []
        }

        if not os.path.exists(env_file_path):
            validation_result["valid"] = False
            validation_result["errors"].append(f"Environment file not found: {env_file_path}")
            return validation_result

        try:
            with open(env_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Parse environment variables
            env_vars = {}
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key] = value

            # Required variables for production
            required_vars = [
                'ENVIRONMENT',
                'SECURITY_JWT_SECRET_KEY',
                'DATABASE_URL',
                'EMAIL_HOST',
                'EMAIL_USER',
                'EMAIL_PASSWORD',
                'EMAIL_FROM',
                'OANDA_API_KEY',
                'OANDA_ACCOUNT_ID',
                'GEMINI_API_KEY'
            ]

            # Check required variables
            missing_vars = []
            for var in required_vars:
                if var not in env_vars or not env_vars[var] or env_vars[var].startswith('${'):
                    missing_vars.append(var)

            if missing_vars:
                validation_result["valid"] = False
                validation_result["errors"].append(f"Missing required variables: {', '.join(missing_vars)}")

            # Validate JWT secret key
            if 'SECURITY_JWT_SECRET_KEY' in env_vars:
                jwt_secret = env_vars['SECURITY_JWT_SECRET_KEY']
                if len(jwt_secret) < 32:
                    validation_result["warnings"].append("JWT secret key should be at least 32 characters")
                if jwt_secret in ['your-secret-key', 'your-super-secret-jwt-key', 'test-secret-key-for-testing-only']:
                    validation_result["warnings"].append("JWT secret key appears to be a default value")

            # Validate environment
            if 'ENVIRONMENT' in env_vars:
                env = env_vars['ENVIRONMENT'].lower()
                if env not in ['development', 'staging', 'production', 'testing']:
                    validation_result["errors"].append(f"Invalid environment: {env}")

            # Validate database URL
            if 'DATABASE_URL' in env_vars:
                db_url = env_vars['DATABASE_URL']
                if not db_url.startswith(('postgresql://', 'mysql://', 'sqlite:///')):
                    validation_result["warnings"].append("Database URL should start with postgresql://, mysql://, or sqlite:///")

            # Check for deprecated variables
            deprecated_vars = [
                'JWT_SECRET_KEY',  # Now SECURITY_JWT_SECRET_KEY
                'ACCESS_TOKEN_EXPIRE_MINUTES',  # Now SECURITY_JWT_ACCESS_TOKEN_EXPIRE_MINUTES
                'CACHE_TTL',  # Now CACHE_TTL_SHORT, CACHE_TTL_MEDIUM, etc.
            ]

            for var in deprecated_vars:
                if var in env_vars:
                    validation_result["deprecated_vars"].append(var)
                    validation_result["warnings"].append(f"Deprecated variable found: {var}")

            validation_result["required_vars"] = required_vars
            validation_result["info"].append(f"Found {len(env_vars)} environment variables")

        except Exception as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Error reading environment file: {str(e)}")

        return validation_result

    def create_environment_file(self,
                               environment: str,
                               output_path: str,
                               template_path: Optional[str] = None) -> bool:
        """Create a new environment file"""
        try:
            env_map = {
                'development': '.env.development',
                'staging': '.env.staging',
                'production': '.env.production',
                'testing': '.env.test'
            }

            if environment not in env_map:
                logger.error(f"Invalid environment: {environment}")
                return False

            # Determine template path
            if not template_path:
                template_path = f".env.{environment}" if environment != 'testing' else '.env.test'

            # Copy template if it exists
            if os.path.exists(template_path):
                import shutil
                shutil.copy2(template_path, output_path)
                logger.info(f"Created environment file from template: {output_path}")
                return True
            else:
                logger.error(f"Template not found: {template_path}")
                return False

        except Exception as e:
            logger.error(f"Error creating environment file: {str(e)}")
            return False

    def migrate_old_config(self, old_config_path: str, new_config_path: str) -> bool:
        """Migrate old configuration format to new format"""
        try:
            if not os.path.exists(old_config_path):
                logger.error(f"Old configuration file not found: {old_config_path}")
                return False

            with open(old_config_path, 'r', encoding='utf-8') as f:
                old_lines = f.readlines()

            # Mapping from old to new variable names
            variable_mapping = {
                'JWT_SECRET_KEY': 'SECURITY_JWT_SECRET_KEY',
                'ACCESS_TOKEN_EXPIRE_MINUTES': 'SECURITY_JWT_ACCESS_TOKEN_EXPIRE_MINUTES',
                'CACHE_TTL': 'CACHE_TTL_SHORT',
                'REDIS_POOL_SIZE': 'REDIS_MAX_CONNECTIONS',
                'REDIS_TIMEOUT': 'REDIS_TIMEOUT',
                'LOG_LEVEL': 'LOG_LEVEL',
                'LOG_FILE': 'LOG_FILE',
                'ENABLE_METRICS': 'ENABLE_METRICS',
                'METRICS_PORT': 'METRICS_PORT',
                'MAX_WORKERS': 'MAX_WORKERS',
                'TIMEOUT': 'TIMEOUT',
                'RATE_LIMIT_REQUESTS': 'RATE_LIMIT_REQUESTS',
                'RATE_LIMIT_WINDOW': 'RATE_LIMIT_WINDOW',
                'ENABLE_AI_ANALYSIS': 'ENABLE_AI_ANALYSIS',
                'ENABLE_SIGNAL_GENERATION': 'ENABLE_SIGNAL_GENERATION',
                'ENABLE_REAL_TIME_DATA': 'ENABLE_REAL_TIME_DATA',
                'ENABLE_USER_AUTHENTICATION': 'ENABLE_USER_AUTHENTICATION',
                'ENABLE_EMAIL_NOTIFICATIONS': 'ENABLE_EMAIL_NOTIFICATIONS',
            }

            # Migrate variables
            migrated_lines = []
            migrated_count = 0

            for line in old_lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    if line:
                        migrated_lines.append(line + '\n')
                    continue

                if '=' in line:
                    key, value = line.split('=', 1)
                    if key in variable_mapping:
                        new_key = variable_mapping[key]
                        migrated_lines.append(f"{new_key}={value}\n")
                        migrated_count += 1
                    else:
                        migrated_lines.append(f"{key}={value}\n")

            # Add new configuration sections
            if migrated_count > 0:
                migrated_lines.append("\n# Migrated from old configuration format\n")
                migrated_lines.append(f"# Migration date: {datetime.now().isoformat()}\n")

            with open(new_config_path, 'w', encoding='utf-8') as f:
                f.writelines(migrated_lines)

            logger.info(f"Migrated {migrated_count} variables to new format: {new_config_path}")
            return True

        except Exception as e:
            logger.error(f"Error migrating configuration: {str(e)}")
            return False

    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get a summary of the current configuration"""
        try:
            safe_settings = self.settings.get_safe_settings()
            validation_result = self.settings.validate_configuration()

            summary = {
                "environment": self.settings.environment.value,
                "version": self.settings.version,
                "project_name": self.settings.project_name,
                "configuration_valid": validation_result["valid"],
                "configuration_errors": validation_result["errors"],
                "settings_count": validation_result["settings_count"],
                "features_enabled": {
                    "ai_analysis": self.settings.features.enable_ai_analysis,
                    "signal_generation": self.settings.features.enable_signal_generation,
                    "real_time_data": self.settings.features.enable_real_time_data,
                    "user_authentication": self.settings.features.enable_user_authentication,
                    "email_notifications": self.settings.features.enable_email_notifications,
                    "cache_warming": self.settings.features.enable_cache_warming,
                    "performance_monitoring": self.settings.features.enable_performance_monitoring,
                    "signal_execution": self.settings.features.enable_signal_execution,
                    "paper_trading": self.settings.features.enable_paper_trading,
                },
                "server_config": {
                    "host": self.settings.server.host,
                    "port": self.settings.server.port,
                    "debug": self.settings.server.debug,
                    "max_workers": self.settings.server.max_workers,
                    "timeout": self.settings.server.timeout,
                },
                "database_config": {
                    "pool_size": self.settings.database.database_pool_size,
                    "max_overflow": self.settings.database.database_max_overflow,
                    "timeout": self.settings.database.database_pool_timeout,
                },
                "cache_config": {
                    "redis_url": "***REDACTED***" if self.settings.cache.redis_url else None,
                    "ttl_short": self.settings.cache.cache_ttl_short,
                    "ttl_medium": self.settings.cache.cache_ttl_medium,
                    "ttl_long": self.settings.cache.cache_ttl_long,
                    "warming_enabled": self.settings.cache.cache_warming_enabled,
                },
                "api_config": {
                    "cors_origins": self.settings.get_cors_origins(),
                    "rate_limit_requests": self.settings.api.rate_limit_requests,
                    "rate_limit_window": self.settings.api.rate_limit_window,
                },
                "timestamp": datetime.utcnow().isoformat(),
            }

            return summary

        except Exception as e:
            logger.error(f"Error getting configuration summary: {str(e)}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    def backup_configuration(self, backup_path: Optional[str] = None) -> str:
        """Backup current configuration"""
        try:
            if not backup_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"config_backup_{timestamp}.json"

            # Get safe configuration
            safe_settings = self.settings.get_safe_settings()

            # Create backup data
            backup_data = {
                "backup_timestamp": datetime.utcnow().isoformat(),
                "environment": self.settings.environment.value,
                "configuration": safe_settings,
                "validation_result": self.settings.validate_configuration()
            }

            # Save backup
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Configuration backup saved to: {backup_path}")
            return backup_path

        except Exception as e:
            logger.error(f"Error backing up configuration: {str(e)}")
            raise

    def restore_configuration(self, backup_path: str) -> bool:
        """Restore configuration from backup"""
        try:
            if not os.path.exists(backup_path):
                logger.error(f"Backup file not found: {backup_path}")
                return False

            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)

            # This is a complex operation that would require careful implementation
            # For now, just validate the backup structure
            required_keys = ['backup_timestamp', 'environment', 'configuration']
            for key in required_keys:
                if key not in backup_data:
                    logger.error(f"Invalid backup file: missing key {key}")
                    return False

            logger.info(f"Configuration backup validated: {backup_path}")
            logger.info("Manual restoration required - update environment variables from backup")
            return True

        except Exception as e:
            logger.error(f"Error restoring configuration: {str(e)}")
            return False

    def compare_environments(self, env1: str, env2: str) -> Dict[str, Any]:
        """Compare configuration between two environments"""
        try:
            # Load environment files
            env_files = {
                env1: f".env.{env1}" if env1 != 'testing' else '.env.test',
                env2: f".env.{env2}" if env2 != 'testing' else '.env.test'
            }

            env_configs = {}
            for env_name, env_file in env_files.items():
                if os.path.exists(env_file):
                    with open(env_file, 'r', encoding='utf-8') as f:
                        config = {}
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#') and '=' in line:
                                key, value = line.split('=', 1)
                                config[key] = value
                        env_configs[env_name] = config
                else:
                    env_configs[env_name] = {}

            # Compare configurations
            comparison = {
                "environment1": env1,
                "environment2": env2,
                "only_in_env1": {},
                "only_in_env2": {},
                "different_values": {},
                "same_values": [],
                "missing_files": []
            }

            for env_name, env_file in env_files.items():
                if not os.path.exists(env_file):
                    comparison["missing_files"].append(env_file)

            config1 = env_configs.get(env1, {})
            config2 = env_configs.get(env2, {})

            # Find differences
            all_keys = set(config1.keys()) | set(config2.keys())

            for key in all_keys:
                if key in config1 and key not in config2:
                    comparison["only_in_env1"][key] = config1[key]
                elif key in config2 and key not in config1:
                    comparison["only_in_env2"][key] = config2[key]
                elif config1[key] != config2[key]:
                    comparison["different_values"][key] = {
                        env1: config1[key],
                        env2: config2[key]
                    }
                else:
                    comparison["same_values"].append(key)

            return comparison

        except Exception as e:
            logger.error(f"Error comparing environments: {str(e)}")
            return {"error": str(e)}

    def generate_deployment_config(self, environment: str) -> Dict[str, str]:
        """Generate deployment configuration for a specific environment"""
        try:
            env_configs = {
                'development': {
                    'ENVIRONMENT': 'development',
                    'DEBUG': 'true',
                    'LOG_LEVEL': 'DEBUG',
                    'ENABLE_METRICS': 'false',
                    'ENABLE_PROFILING': 'true',
                    'MAX_WORKERS': '2',
                    'TIMEOUT': '60',
                },
                'staging': {
                    'ENVIRONMENT': 'staging',
                    'DEBUG': 'false',
                    'LOG_LEVEL': 'INFO',
                    'ENABLE_METRICS': 'true',
                    'ENABLE_PROFILING': 'false',
                    'MAX_WORKERS': '4',
                    'TIMEOUT': '30',
                },
                'production': {
                    'ENVIRONMENT': 'production',
                    'DEBUG': 'false',
                    'LOG_LEVEL': 'WARNING',
                    'ENABLE_METRICS': 'true',
                    'ENABLE_PROFILING': 'false',
                    'MAX_WORKERS': '8',
                    'TIMEOUT': '20',
                },
                'testing': {
                    'ENVIRONMENT': 'testing',
                    'DEBUG': 'true',
                    'LOG_LEVEL': 'CRITICAL',
                    'ENABLE_METRICS': 'false',
                    'ENABLE_PROFILING': 'false',
                    'MAX_WORKERS': '1',
                    'TIMEOUT': '10',
                }
            }

            if environment not in env_configs:
                raise ValueError(f"Invalid environment: {environment}")

            return env_configs[environment]

        except Exception as e:
            logger.error(f"Error generating deployment config: {str(e)}")
            raise


# Global configuration manager instance
config_manager = ConfigurationManager()