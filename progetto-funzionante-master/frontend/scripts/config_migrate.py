#!/usr/bin/env python3
"""
Configuration Migration Script
Handles migrations between different configuration versions and environments
"""

import os
import sys
import json
import yaml
import shutil
import hashlib
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import logging

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.config_system import ConfigurationManager, ConfigVersion
from config.validation import ConfigurationValidator, ValidationReport

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ConfigMigrator:
    """Handles configuration migrations"""

    def __init__(self, config_dir: Path = None):
        self.config_dir = config_dir or Path("config")
        self.backup_dir = self.config_dir / "backups"
        self.migration_log_file = self.config_dir / "migrations.log"
        self.config_manager = ConfigurationManager(self.config_dir)
        self.validator = ConfigurationValidator()

        # Ensure directories exist
        self.backup_dir.mkdir(exist_ok=True)
        self.config_dir.mkdir(exist_ok=True)

    def migrate_from_legacy(self, legacy_config_path: Path, target_env: str = "production") -> bool:
        """Migrate from legacy configuration format"""
        try:
            logger.info(f"Starting migration from legacy config: {legacy_config_path}")

            # Load legacy configuration
            legacy_config = self._load_legacy_config(legacy_config_path)
            if not legacy_config:
                logger.error("Failed to load legacy configuration")
                return False

            # Create backup before migration
            backup_path = self._create_backup("legacy_migration")
            logger.info(f"Created backup at: {backup_path}")

            # Transform legacy config to new format
            new_config = self._transform_legacy_config(legacy_config, target_env)

            # Validate new configuration
            validation_result = self.validator.validate_configuration(new_config, target_env)
            if not validation_result.is_valid:
                logger.error(f"Configuration validation failed: {len(validation_result.errors)} errors")
                for error in validation_result.errors:
                    logger.error(f"  {error.field}: {error.message}")
                return False

            # Save new configuration
            config_file = self.config_dir / f"config.{target_env}.yaml"
            with open(config_file, 'w') as f:
                yaml.safe_dump(new_config, f, default_flow_style=False, indent=2)

            # Log migration
            self._log_migration("legacy_migration", {
                "source": str(legacy_config_path),
                "target": str(config_file),
                "environment": target_env,
                "timestamp": datetime.utcnow().isoformat(),
                "validation": {
                    "valid": validation_result.is_valid,
                    "errors": len(validation_result.errors),
                    "warnings": len(validation_result.warnings)
                }
            })

            logger.info(f"Successfully migrated to: {config_file}")
            return True

        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return False

    def migrate_environment(self, from_env: str, to_env: str, override_values: Dict[str, Any] = None) -> bool:
        """Migrate configuration from one environment to another"""
        try:
            logger.info(f"Migrating configuration from {from_env} to {to_env}")

            # Load source configuration
            source_file = self.config_dir / f"config.{from_env}.yaml"
            if not source_file.exists():
                logger.error(f"Source configuration file not found: {source_file}")
                return False

            with open(source_file, 'r') as f:
                source_config = yaml.safe_load(f)

            # Create backup
            backup_path = self._create_backup(f"env_migration_{from_env}_to_{to_env}")

            # Transform configuration for target environment
            target_config = self._transform_environment_config(source_config, from_env, to_env, override_values)

            # Validate target configuration
            validation_result = self.validator.validate_configuration(target_config, to_env)
            if not validation_result.is_valid:
                logger.error(f"Target configuration validation failed: {len(validation_result.errors)} errors")
                for error in validation_result.errors:
                    logger.error(f"  {error.field}: {error.message}")
                return False

            # Save target configuration
            target_file = self.config_dir / f"config.{to_env}.yaml"
            with open(target_file, 'w') as f:
                yaml.safe_dump(target_config, f, default_flow_style=False, indent=2)

            # Log migration
            self._log_migration("environment_migration", {
                "source": str(source_file),
                "target": str(target_file),
                "from_environment": from_env,
                "to_environment": to_env,
                "timestamp": datetime.utcnow().isoformat(),
                "validation": {
                    "valid": validation_result.is_valid,
                    "errors": len(validation_result.errors),
                    "warnings": len(validation_result.warnings)
                }
            })

            logger.info(f"Successfully migrated configuration to: {target_file}")
            return True

        except Exception as e:
            logger.error(f"Environment migration failed: {e}")
            return False

    def upgrade_configuration(self, current_version: str, target_version: str) -> bool:
        """Upgrade configuration to a new version"""
        try:
            logger.info(f"Upgrading configuration from {current_version} to {target_version}")

            # Load current configuration for all environments
            environments = ["development", "staging", "production", "test"]
            migration_results = {}

            for env in environments:
                config_file = self.config_dir / f"config.{env}.yaml"
                if config_file.exists():
                    with open(config_file, 'r') as f:
                        current_config = yaml.safe_load(f)

                    # Apply version-specific upgrades
                    upgraded_config = self._apply_version_upgrades(current_config, current_version, target_version)

                    # Validate upgraded configuration
                    validation_result = self.validator.validate_configuration(upgraded_config, env)
                    if not validation_result.is_valid:
                        logger.warning(f"Validation failed for {env}: {len(validation_result.errors)} errors")

                    # Create backup
                    backup_path = self._create_backup(f"version_upgrade_{env}_{current_version}_to_{target_version}")

                    # Save upgraded configuration
                    with open(config_file, 'w') as f:
                        yaml.safe_dump(upgraded_config, f, default_flow_style=False, indent=2)

                    migration_results[env] = {
                        "success": True,
                        "validation": {
                            "valid": validation_result.is_valid,
                            "errors": len(validation_result.errors),
                            "warnings": len(validation_result.warnings)
                        }
                    }
                else:
                    migration_results[env] = {"success": False, "reason": "Config file not found"}

            # Log migration
            self._log_migration("version_upgrade", {
                "current_version": current_version,
                "target_version": target_version,
                "timestamp": datetime.utcnow().isoformat(),
                "results": migration_results
            })

            # Check if all migrations succeeded
            all_success = all(result.get("success", False) for result in migration_results.values())
            if all_success:
                logger.info(f"Successfully upgraded configuration to version {target_version}")
                return True
            else:
                logger.error("Some environment migrations failed")
                return False

        except Exception as e:
            logger.error(f"Version upgrade failed: {e}")
            return False

    def rollback_configuration(self, backup_path: Path, target_env: str = None) -> bool:
        """Rollback configuration to a previous backup"""
        try:
            logger.info(f"Rolling back configuration from: {backup_path}")

            if not backup_path.exists():
                logger.error(f"Backup file not found: {backup_path}")
                return False

            # Extract environment from backup filename
            if target_env is None:
                backup_name = backup_path.stem
                if "_env_" in backup_name:
                    target_env = backup_name.split("_env_")[-1].split("_")[0]
                else:
                    target_env = "production"  # Default

            # Create current backup before rollback
            current_backup = self._create_backup(f"pre_rollback_{target_env}")

            # Restore configuration from backup
            if backup_path.suffix == '.yaml':
                target_file = self.config_dir / f"config.{target_env}.yaml"
                shutil.copy2(backup_path, target_file)
            elif backup_path.is_dir():
                # Restore all configuration files
                for config_file in backup_path.glob("config.*.yaml"):
                    target_file = self.config_dir / config_file.name
                    shutil.copy2(config_file, target_file)
            else:
                logger.error(f"Unsupported backup format: {backup_path}")
                return False

            # Validate restored configuration
            config_file = self.config_dir / f"config.{target_env}.yaml"
            with open(config_file, 'r') as f:
                restored_config = yaml.safe_load(f)

            validation_result = self.validator.validate_configuration(restored_config, target_env)
            if not validation_result.is_valid:
                logger.error(f"Restored configuration validation failed: {len(validation_result.errors)} errors")

            # Log rollback
            self._log_migration("rollback", {
                "backup_path": str(backup_path),
                "target_environment": target_env,
                "pre_rollback_backup": str(current_backup),
                "timestamp": datetime.utcnow().isoformat(),
                "validation": {
                    "valid": validation_result.is_valid,
                    "errors": len(validation_result.errors),
                    "warnings": len(validation_result.warnings)
                }
            })

            logger.info(f"Successfully rolled back configuration for {target_env}")
            return True

        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False

    def _load_legacy_config(self, config_path: Path) -> Optional[Dict[str, Any]]:
        """Load legacy configuration format"""
        try:
            if config_path.suffix == '.json':
                with open(config_path, 'r') as f:
                    return json.load(f)
            elif config_path.suffix in ['.yaml', '.yml']:
                with open(config_path, 'r') as f:
                    return yaml.safe_load(f)
            elif config_path.suffix == '.env':
                return self._parse_env_file(config_path)
            else:
                logger.error(f"Unsupported configuration format: {config_path.suffix}")
                return None
        except Exception as e:
            logger.error(f"Failed to load legacy config: {e}")
            return None

    def _parse_env_file(self, env_path: Path) -> Dict[str, Any]:
        """Parse .env file into dictionary"""
        config = {}
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    config[key] = value
        return config

    def _transform_legacy_config(self, legacy_config: Dict[str, Any], target_env: str) -> Dict[str, Any]:
        """Transform legacy configuration to new format"""
        new_config = {
            'app': {
                'name': legacy_config.get('PROJECT_NAME', 'Trading Signals System'),
                'version': legacy_config.get('VERSION', '2.0.1'),
                'environment': target_env,
                'debug': target_env == 'development',
                'testing': target_env == 'testing'
            },
            'server': {
                'host': legacy_config.get('HOST', '127.0.0.1'),
                'port': int(legacy_config.get('PORT', 8000)),
                'reload': target_env == 'development',
                'workers': 1 if target_env == 'development' else 4,
                'timeout': int(legacy_config.get('TIMEOUT', 30))
            },
            'security': {
                'jwt_secret_key': legacy_config.get('SECURITY_JWT_SECRET_KEY', ''),
                'jwt_algorithm': legacy_config.get('SECURITY_JWT_ALGORITHM', 'HS256'),
                'jwt_access_token_expire_minutes': int(legacy_config.get('SECURITY_JWT_ACCESS_TOKEN_EXPIRE_MINUTES', 30)),
                'jwt_refresh_token_expire_days': int(legacy_config.get('SECURITY_JWT_REFRESH_TOKEN_EXPIRE_DAYS', 7)),
                'cors_origins': eval(legacy_config.get('CORS_ORIGINS', '["*"]')),
                'cors_allow_credentials': legacy_config.get('CORS_ALLOW_CREDENTIALS', 'true').lower() == 'true',
                'cors_allow_methods': eval(legacy_config.get('CORS_ALLOW_METHODS', '["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]')),
                'cors_allow_headers': eval(legacy_config.get('CORS_ALLOW_HEADERS', '["*"]'))
            },
            'database': {
                'url': legacy_config.get('DATABASE_URL', ''),
                'pool_size': int(legacy_config.get('DATABASE_POOL_SIZE', 20)),
                'max_overflow': int(legacy_config.get('DATABASE_MAX_OVERFLOW', 10)),
                'pool_timeout': int(legacy_config.get('DATABASE_POOL_TIMEOUT', 30)),
                'pool_recycle': int(legacy_config.get('DATABASE_POOL_RECYCLE', 3600))
            },
            'cache': {
                'redis_url': legacy_config.get('REDIS_URL', 'redis://localhost:6379'),
                'redis_password': legacy_config.get('REDIS_PASSWORD'),
                'max_connections': int(legacy_config.get('REDIS_MAX_CONNECTIONS', 10)),
                'timeout': int(legacy_config.get('REDIS_TIMEOUT', 5)),
                'ttl_short': int(legacy_config.get('CACHE_TTL_SHORT', 300)),
                'ttl_medium': int(legacy_config.get('CACHE_TTL_MEDIUM', 1800)),
                'ttl_long': int(legacy_config.get('CACHE_TTL_LONG', 3600)),
                'prefix': legacy_config.get('CACHE_PREFIX', 'ai_trading:')
            },
            'email': {
                'host': legacy_config.get('EMAIL_HOST', ''),
                'port': int(legacy_config.get('EMAIL_PORT', 587)),
                'user': legacy_config.get('EMAIL_USER', ''),
                'password': legacy_config.get('EMAIL_PASSWORD', ''),
                'from_address': legacy_config.get('EMAIL_FROM', ''),
                'use_tls': legacy_config.get('EMAIL_USE_TLS', 'true').lower() == 'true',
                'use_ssl': legacy_config.get('EMAIL_USE_SSL', 'false').lower() == 'true'
            },
            'oanda': {
                'api_key': legacy_config.get('OANDA_API_KEY', ''),
                'account_id': legacy_config.get('OANDA_ACCOUNT_ID', ''),
                'environment': legacy_config.get('OANDA_ENVIRONMENT', 'demo'),
                'base_url': legacy_config.get('OANDA_BASE_URL', 'https://api-fxpractice.oanda.com/v3'),
                'timeout': int(legacy_config.get('OANDA_TIMEOUT', 30)),
                'retry_attempts': int(legacy_config.get('OANDA_RETRY_ATTEMPTS', 3))
            },
            'ai': {
                'gemini_api_key': legacy_config.get('GEMINI_API_KEY', ''),
                'gemini_model': legacy_config.get('GEMINI_MODEL', 'gemini-pro'),
                'temperature': float(legacy_config.get('GEMINI_TEMPERATURE', 0.7)),
                'max_tokens': int(legacy_config.get('GEMINI_MAX_TOKENS', 1000)),
                'confidence_threshold': float(legacy_config.get('AI_CONFIDENCE_THRESHOLD', 0.6))
            },
            'monitoring': {
                'log_level': legacy_config.get('LOG_LEVEL', 'INFO'),
                'log_format': legacy_config.get('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
                'log_file': legacy_config.get('LOG_FILE'),
                'enable_metrics': legacy_config.get('ENABLE_METRICS', 'true').lower() == 'true',
                'enable_health_checks': legacy_config.get('ENABLE_HEALTH_CHECKS', 'true').lower() == 'true',
                'enable_profiling': legacy_config.get('ENABLE_PROFILING', 'false').lower() == 'true'
            },
            'trading': {
                'default_symbols': eval(legacy_config.get('DEFAULT_SYMBOLS', '["EURUSD", "GBPUSD", "USDJPY"]')),
                'max_daily_signals': int(legacy_config.get('MAX_DAILY_SIGNALS', 100)),
                'default_risk_level': legacy_config.get('DEFAULT_RISK_LEVEL', 'MEDIUM'),
                'default_position_size': float(legacy_config.get('DEFAULT_POSITION_SIZE', 0.01)),
                'max_position_size': float(legacy_config.get('MAX_POSITION_SIZE', 0.05)),
                'trading_hours_enabled': legacy_config.get('TRADING_HOURS_ENABLED', 'true').lower() == 'true',
                'signal_generation_interval': int(legacy_config.get('SIGNAL_GENERATION_INTERVAL', 300))
            },
            'feature_flags': {
                'enable_ai_analysis': legacy_config.get('ENABLE_AI_ANALYSIS', 'true').lower() == 'true',
                'enable_real_time_data': legacy_config.get('ENABLE_REAL_TIME_DATA', 'true').lower() == 'true',
                'enable_user_authentication': legacy_config.get('ENABLE_USER_AUTHENTICATION', 'true').lower() == 'true',
                'enable_email_notifications': legacy_config.get('ENABLE_EMAIL_NOTIFICATIONS', 'true').lower() == 'true',
                'enable_cache_warming': legacy_config.get('ENABLE_CACHE_WARMING', 'true').lower() == 'true',
                'enable_performance_monitoring': legacy_config.get('ENABLE_PERFORMANCE_MONITORING', 'true').lower() == 'true',
                'enable_signal_execution': legacy_config.get('ENABLE_SIGNAL_EXECUTION', 'false').lower() == 'true',
                'enable_paper_trading': legacy_config.get('ENABLE_PAPER_TRADING', 'true').lower() == 'true'
            }
        }

        return new_config

    def _transform_environment_config(self, source_config: Dict[str, Any], from_env: str, to_env: str, override_values: Dict[str, Any] = None) -> Dict[str, Any]:
        """Transform configuration for target environment"""
        target_config = source_config.copy()

        # Update environment-specific settings
        if 'app' in target_config:
            target_config['app']['environment'] = to_env

        if 'server' in target_config:
            server_config = target_config['server']
            if to_env == 'production':
                server_config.update({
                    'host': '0.0.0.0',
                    'reload': False,
                    'workers': 8,
                    'timeout': 20
                })
            elif to_env == 'staging':
                server_config.update({
                    'host': '0.0.0.0',
                    'reload': False,
                    'workers': 4,
                    'timeout': 30
                })
            elif to_env == 'development':
                server_config.update({
                    'host': '127.0.0.1',
                    'reload': True,
                    'workers': 1,
                    'timeout': 60
                })

        if 'monitoring' in target_config:
            monitoring_config = target_config['monitoring']
            if to_env == 'production':
                monitoring_config['log_level'] = 'WARNING'
            elif to_env == 'development':
                monitoring_config['log_level'] = 'DEBUG'
            else:
                monitoring_config['log_level'] = 'INFO'

        # Apply override values
        if override_values:
            target_config.update(override_values)

        return target_config

    def _apply_version_upgrades(self, config: Dict[str, Any], current_version: str, target_version: str) -> Dict[str, Any]:
        """Apply version-specific configuration upgrades"""
        # This is a placeholder for version-specific upgrade logic
        # In a real implementation, you would have specific upgrade paths
        return config

    def _create_backup(self, backup_name: str) -> Path:
        """Create a backup of current configuration"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"{backup_name}_{timestamp}"

        if backup_path.suffix:
            # Single file backup
            if backup_path.exists():
                shutil.copy2(backup_path, backup_path.with_suffix(f'.bak_{timestamp}'))
        else:
            # Directory backup
            backup_path.mkdir(exist_ok=True)
            for config_file in self.config_dir.glob("config.*.yaml"):
                shutil.copy2(config_file, backup_path / config_file.name)

        return backup_path

    def _log_migration(self, migration_type: str, migration_data: Dict[str, Any]):
        """Log migration details"""
        log_entry = {
            "type": migration_type,
            "data": migration_data,
            "timestamp": datetime.utcnow().isoformat()
        }

        with open(self.migration_log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

    def list_backups(self) -> List[Dict[str, Any]]:
        """List available configuration backups"""
        backups = []
        for backup_path in self.backup_dir.iterdir():
            if backup_path.is_file() or backup_path.is_dir():
                stat = backup_path.stat()
                backups.append({
                    "path": str(backup_path),
                    "name": backup_path.name,
                    "size": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_ctime),
                    "modified": datetime.fromtimestamp(stat.st_mtime)
                })

        return sorted(backups, key=lambda x: x['created'], reverse=True)

    def cleanup_old_backups(self, keep_count: int = 10):
        """Clean up old backup files"""
        backups = self.list_backups()
        if len(backups) > keep_count:
            for backup in backups[keep_count:]:
                backup_path = Path(backup['path'])
                try:
                    if backup_path.is_file():
                        backup_path.unlink()
                    elif backup_path.is_dir():
                        shutil.rmtree(backup_path)
                    logger.info(f"Cleaned up old backup: {backup_path}")
                except Exception as e:
                    logger.error(f"Failed to cleanup backup {backup_path}: {e}")

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description="Configuration Migration Tool")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Legacy migration command
    legacy_parser = subparsers.add_parser('migrate-legacy', help='Migrate from legacy configuration')
    legacy_parser.add_argument('legacy_config', help='Path to legacy configuration file')
    legacy_parser.add_argument('--env', default='production', help='Target environment')

    # Environment migration command
    env_parser = subparsers.add_parser('migrate-env', help='Migrate between environments')
    env_parser.add_argument('from_env', help='Source environment')
    env_parser.add_argument('to_env', help='Target environment')
    env_parser.add_argument('--override', help='Override values as JSON string')

    # Version upgrade command
    version_parser = subparsers.add_parser('upgrade', help='Upgrade configuration version')
    version_parser.add_argument('current_version', help='Current version')
    version_parser.add_argument('target_version', help='Target version')

    # Rollback command
    rollback_parser = subparsers.add_parser('rollback', help='Rollback to backup')
    rollback_parser.add_argument('backup_path', help='Path to backup file')
    rollback_parser.add_argument('--env', help='Target environment (optional)')

    # List backups command
    subparsers.add_parser('list-backups', help='List available backups')

    # Cleanup backups command
    cleanup_parser = subparsers.add_parser('cleanup-backups', help='Clean up old backups')
    cleanup_parser.add_argument('--keep', type=int, default=10, help='Number of backups to keep')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    migrator = ConfigMigrator()

    if args.command == 'migrate-legacy':
        success = migrator.migrate_from_legacy(Path(args.legacy_config), args.env)
    elif args.command == 'migrate-env':
        override_values = json.loads(args.override) if args.override else None
        success = migrator.migrate_environment(args.from_env, args.to_env, override_values)
    elif args.command == 'upgrade':
        success = migrator.upgrade_configuration(args.current_version, args.target_version)
    elif args.command == 'rollback':
        success = migrator.rollback_configuration(Path(args.backup_path), args.env)
    elif args.command == 'list-backups':
        backups = migrator.list_backups()
        for backup in backups:
            print(f"{backup['created']}: {backup['name']} ({backup['size']} bytes)")
        return 0
    elif args.command == 'cleanup-backups':
        migrator.cleanup_old_backups(args.keep)
        return 0
    else:
        print(f"Unknown command: {args.command}")
        return 1

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())