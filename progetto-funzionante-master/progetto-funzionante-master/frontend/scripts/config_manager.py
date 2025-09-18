#!/usr/bin/env python3
"""
Configuration Management CLI Tool
Comprehensive command-line interface for managing application configuration
"""

import os
import sys
import json
import yaml
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import logging

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.config_system import ConfigurationManager, ConfigType, SecurityLevel
from config.validation import ConfigurationValidator, ValidationLevel, ValidationCategory
from config.secrets_manager import SecretsManager, SecretType, SecurityLevel as SecretSecurityLevel

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ConfigCLI:
    """Command-line interface for configuration management"""

    def __init__(self):
        self.config_manager = ConfigurationManager()
        self.validator = ConfigurationValidator()
        self.secrets_manager = SecretsManager()

    def validate_config(self, environment: str = None, output_format: str = "text") -> bool:
        """Validate configuration"""
        try:
            if environment:
                config_file = Path(f"config/config.{environment}.yaml")
                if not config_file.exists():
                    print(f"Configuration file not found: {config_file}")
                    return False

                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f)
            else:
                # Use current configuration
                config = self.config_manager.config_cache
                environment = os.getenv('ENVIRONMENT', 'development')

            validation_result = self.validator.validate_configuration(config, environment)

            if output_format == "text":
                self._print_validation_result(validation_result)
            elif output_format == "json":
                print(json.dumps(self._validation_result_to_dict(validation_result), indent=2))
            elif output_format == "yaml":
                print(yaml.dump(self._validation_result_to_dict(validation_result), default_flow_style=False))

            return validation_result.is_valid

        except Exception as e:
            print(f"Validation failed: {e}")
            return False

    def _print_validation_result(self, result):
        """Print validation result in human-readable format"""
        print(f"\n{'='*60}")
        print(f"Configuration Validation Report")
        print(f"{'='*60}")
        print(f"Environment: {result.environment}")
        print(f"Status: {'✅ PASS' if result.is_valid else '❌ FAIL'}")
        print(f"Total Checks: {result.total_checks}")
        print(f"Passed: {result.passed_checks}")
        print(f"Errors: {len(result.errors)}")
        print(f"Warnings: {len(result.warnings)}")
        print(f"{'='*60}")

        if result.errors:
            print(f"\n❌ ERRORS:")
            for error in result.errors:
                print(f"  • {error.field}: {error.message}")
                if error.suggestion:
                    print(f"    💡 {error.suggestion}")

        if result.warnings:
            print(f"\n⚠️  WARNINGS:")
            for warning in result.warnings:
                print(f"  • {warning.field}: {warning.message}")
                if warning.suggestion:
                    print(f"    💡 {warning.suggestion}")

        if result.info:
            print(f"\nℹ️  INFO:")
            for info in result.info:
                print(f"  • {info.field}: {info.message}")

    def _validation_result_to_dict(self, result):
        """Convert validation result to dictionary"""
        return {
            "valid": result.is_valid,
            "environment": result.environment,
            "timestamp": result.timestamp.isoformat(),
            "summary": {
                "total_checks": result.total_checks,
                "passed_checks": result.passed_checks,
                "errors": len(result.errors),
                "warnings": len(result.warnings),
                "info": len(result.info)
            },
            "errors": [
                {
                    "field": error.field,
                    "message": error.message,
                    "category": error.category.value,
                    "suggestion": error.suggestion,
                    "rule_id": error.rule_id
                }
                for error in result.errors
            ],
            "warnings": [
                {
                    "field": warning.field,
                    "message": warning.message,
                    "category": warning.category.value,
                    "suggestion": warning.suggestion,
                    "rule_id": warning.rule_id
                }
                for warning in result.warnings
            ],
            "info": [
                {
                    "field": info.field,
                    "message": info.message,
                    "category": info.category.value,
                    "suggestion": info.suggestion,
                    "rule_id": info.rule_id
                }
                for info in result.info
            ]
        }

    def get_config_value(self, key: str, environment: str = None, default: str = None) -> str:
        """Get a configuration value"""
        try:
            if environment:
                config_file = Path(f"config/config.{environment}.yaml")
                if not config_file.exists():
                    print(f"Configuration file not found: {config_file}")
                    return None

                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f)

                # Navigate nested keys
                keys = key.split('.')
                value = config
                for k in keys:
                    if isinstance(value, dict) and k in value:
                        value = value[k]
                    else:
                        value = None
                        break

                return str(value) if value is not None else default
            else:
                value = self.config_manager.get(key)
                return str(value) if value is not None else default

        except Exception as e:
            print(f"Error getting configuration value: {e}")
            return default

    def set_config_value(self, key: str, value: str, environment: str = None, persist: bool = True) -> bool:
        """Set a configuration value"""
        try:
            if environment:
                config_file = Path(f"config/config.{environment}.yaml")
                if not config_file.exists():
                    print(f"Configuration file not found: {config_file}")
                    return False

                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f) or {}

                # Navigate nested keys
                keys = key.split('.')
                current = config
                for k in keys[:-1]:
                    if k not in current:
                        current[k] = {}
                    current = current[k]

                # Set the value
                final_key = keys[-1]
                old_value = current.get(final_key)
                current[final_key] = self._convert_value(value)

                # Save the configuration
                with open(config_file, 'w') as f:
                    yaml.safe_dump(config, f, default_flow_style=False, indent=2)

                print(f"✅ Set {key} = {value} in {environment} environment")
                if old_value is not None:
                    print(f"   Previous value: {old_value}")

                return True
            else:
                success = self.config_manager.set(key, self._convert_value(value), persist)
                if success:
                    print(f"✅ Set {key} = {value}")
                return success

        except Exception as e:
            print(f"Error setting configuration value: {e}")
            return False

    def _convert_value(self, value: str):
        """Convert string value to appropriate type"""
        # Try boolean
        if value.lower() in ['true', 'false']:
            return value.lower() == 'true'

        # Try integer
        try:
            return int(value)
        except ValueError:
            pass

        # Try float
        try:
            return float(value)
        except ValueError:
            pass

        # Try JSON
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            pass

        # Return as string
        return value

    def list_config_values(self, environment: str = None, pattern: str = None) -> bool:
        """List configuration values"""
        try:
            if environment:
                config_file = Path(f"config/config.{environment}.yaml")
                if not config_file.exists():
                    print(f"Configuration file not found: {config_file}")
                    return False

                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f) or {}
            else:
                config = self.config_manager.config_cache

            # Flatten nested configuration
            def flatten_config(d, parent_key='', sep='.'):
                items = []
                for k, v in d.items():
                    new_key = f"{parent_key}{sep}{k}" if parent_key else k
                    if isinstance(v, dict):
                        items.extend(flatten_config(v, new_key, sep=sep))
                    else:
                        items.append((new_key, v))
                return items

            flat_config = flatten_config(config)

            # Filter by pattern if provided
            if pattern:
                import re
                flat_config = [(k, v) for k, v in flat_config if re.search(pattern, k, re.IGNORECASE)]

            # Print configuration
            print(f"\n{'='*60}")
            print(f"Configuration Values")
            if environment:
                print(f"Environment: {environment}")
            if pattern:
                print(f"Pattern: {pattern}")
            print(f"{'='*60}")

            for key, value in sorted(flat_config):
                # Mask sensitive values
                display_value = self._mask_sensitive_value(key, value)
                print(f"  {key}: {display_value}")

            print(f"\nTotal: {len(flat_config)} configuration values")
            return True

        except Exception as e:
            print(f"Error listing configuration values: {e}")
            return False

    def _mask_sensitive_value(self, key: str, value: Any) -> str:
        """Mask sensitive configuration values"""
        sensitive_patterns = [
            'secret', 'password', 'key', 'token', 'dsn', 'api_key',
            'jwt_secret', 'database_url', 'redis_password'
        ]

        if any(pattern in key.lower() for pattern in sensitive_patterns):
            if isinstance(value, str) and len(value) > 8:
                return f"{'*' * (len(value) - 4)}{value[-4:]}"
            else:
                return "********"

        return str(value)

    def backup_config(self, environment: str = None, backup_path: str = None) -> bool:
        """Backup configuration"""
        try:
            if backup_path:
                backup_path = Path(backup_path)
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"config_backup_{environment}_{timestamp}" if environment else f"config_backup_{timestamp}"
                backup_path = Path("config/backups") / backup_name

            success = self.config_manager.backup_configuration(backup_path)
            if success:
                print(f"✅ Configuration backed up to: {backup_path}")
            return success

        except Exception as e:
            print(f"Error backing up configuration: {e}")
            return False

    def restore_config(self, backup_path: str, environment: str = None) -> bool:
        """Restore configuration from backup"""
        try:
            backup_path = Path(backup_path)
            if not backup_path.exists():
                print(f"Backup path does not exist: {backup_path}")
                return False

            success = self.config_manager.restore_configuration(backup_path)
            if success:
                print(f"✅ Configuration restored from: {backup_path}")
            return success

        except Exception as e:
            print(f"Error restoring configuration: {e}")
            return False

    def enable_hot_reload(self, environment: str = None) -> bool:
        """Enable hot-reloading for configuration"""
        try:
            self.config_manager.enable_hot_reload()
            print("✅ Hot-reloading enabled for configuration")
            print("   Configuration will automatically reload when files change")
            return True

        except Exception as e:
            print(f"Error enabling hot-reloading: {e}")
            return False

    def manage_feature_flags(self, action: str, flag_name: str, environment: str = None, enabled: bool = None) -> bool:
        """Manage feature flags"""
        try:
            if action == "list":
                flags = self.config_manager.feature_flags
                print(f"\n{'='*60}")
                print(f"Feature Flags")
                print(f"{'='*60}")

                for flag, is_enabled in sorted(flags.items()):
                    status = "✅ ENABLED" if is_enabled else "❌ DISABLED"
                    print(f"  {flag}: {status}")

                print(f"\nTotal: {len(flags)} feature flags")
                return True

            elif action == "get":
                is_enabled = self.config_manager.get_feature_flag(flag_name)
                status = "✅ ENABLED" if is_enabled else "❌ DISABLED"
                print(f"{flag_name}: {status}")
                return True

            elif action == "set":
                if enabled is None:
                    print("Error: --enabled flag is required for set action")
                    return False

                success = self.config_manager.set_feature_flag(flag_name, enabled)
                if success:
                    status = "✅ ENABLED" if enabled else "❌ DISABLED"
                    print(f"✅ {flag_name} set to {status}")
                return success

            elif action == "toggle":
                current_value = self.config_manager.get_feature_flag(flag_name)
                new_value = not current_value
                success = self.config_manager.set_feature_flag(flag_name, new_value)
                if success:
                    status = "✅ ENABLED" if new_value else "❌ DISABLED"
                    print(f"✅ {flag_name} toggled to {status}")
                return success

            else:
                print(f"Unknown action: {action}")
                return False

        except Exception as e:
            print(f"Error managing feature flags: {e}")
            return False

    def manage_secrets(self, action: str, key: str = None, value: str = None, secret_type: str = None, security_level: str = None) -> bool:
        """Manage secrets"""
        try:
            if action == "list":
                secrets = self.secrets_manager.list_secrets()
                print(f"\n{'='*60}")
                print(f"Secrets")
                print(f"{'='*60}")

                for secret_key in sorted(secrets):
                    metadata = self.secrets_manager.get_secret_metadata(secret_key)
                    if metadata:
                        status = "🟢 ACTIVE" if metadata.status.value == "active" else "🔴 INACTIVE"
                        print(f"  {secret_key} ({metadata.secret_type.value}) - {status}")

                print(f"\nTotal: {len(secrets)} secrets")
                return True

            elif action == "get":
                if not key:
                    print("Error: Secret key is required for get action")
                    return False

                secret_value = self.secrets_manager.get_secret(key)
                if secret_value is not None:
                    print(f"✅ {key}: {'*' * 8}")  # Don't show actual secret value
                    return True
                else:
                    print(f"❌ Secret '{key}' not found")
                    return False

            elif action == "set":
                if not key or not value:
                    print("Error: Key and value are required for set action")
                    return False

                # Parse secret type
                stype = SecretType.OTHER
                if secret_type:
                    try:
                        stype = SecretType(secret_type)
                    except ValueError:
                        print(f"Error: Invalid secret type: {secret_type}")
                        return False

                # Parse security level
                slevel = SecretSecurityLevel.SECRET
                if security_level:
                    try:
                        slevel = SecretSecurityLevel(security_level)
                    except ValueError:
                        print(f"Error: Invalid security level: {security_level}")
                        return False

                success = self.secrets_manager.store_secret(
                    key=key,
                    value=value,
                    secret_type=stype,
                    security_level=slevel,
                    description=f"Secret set via CLI at {datetime.now()}"
                )

                if success:
                    print(f"✅ Secret '{key}' stored successfully")
                return success

            elif action == "delete":
                if not key:
                    print("Error: Secret key is required for delete action")
                    return False

                success = self.secrets_manager.delete_secret(key)
                if success:
                    print(f"✅ Secret '{key}' deleted successfully")
                return success

            elif action == "rotate":
                if not key:
                    print("Error: Secret key is required for rotate action")
                    return False

                success = self.secrets_manager.rotate_secret(key, value)
                if success:
                    print(f"✅ Secret '{key}' rotated successfully")
                return success

            elif action == "health":
                health = self.secrets_manager.health_check()
                print(f"\n{'='*60}")
                print(f"Secrets Manager Health Check")
                print(f"{'='*60}")
                print(f"Status: {health['status']}")
                print(f"Total Secrets: {health['total_secrets']}")
                print(f"Expired Secrets: {health['expired_secrets']}")
                print(f"Secrets Needing Rotation: {health['secrets_needing_rotation']}")
                print(f"Cache Size: {health['cache_size']}")
                print(f"Provider: {health['provider_type']}")
                return True

            else:
                print(f"Unknown action: {action}")
                return False

        except Exception as e:
            print(f"Error managing secrets: {e}")
            return False

    def generate_config(self, environment: str, output_file: str = None, template: str = None) -> bool:
        """Generate configuration template"""
        try:
            if template:
                # Load template
                template_file = Path(f"config/templates/{template}.yaml")
                if not template_file.exists():
                    print(f"Template not found: {template_file}")
                    return False

                with open(template_file, 'r') as f:
                    config = yaml.safe_load(f)
            else:
                # Generate default configuration
                config = self._generate_default_config(environment)

            # Set environment-specific values
            if 'app' in config:
                config['app']['environment'] = environment

            # Output configuration
            if output_file:
                output_path = Path(output_file)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w') as f:
                    yaml.safe_dump(config, f, default_flow_style=False, indent=2)
                print(f"✅ Configuration generated: {output_path}")
            else:
                print(yaml.dump(config, default_flow_style=False, indent=2))

            return True

        except Exception as e:
            print(f"Error generating configuration: {e}")
            return False

    def _generate_default_config(self, environment: str) -> Dict[str, Any]:
        """Generate default configuration for environment"""
        return {
            'app': {
                'name': 'Trading Signals System',
                'version': '2.0.1',
                'environment': environment,
                'debug': environment == 'development'
            },
            'server': {
                'host': '127.0.0.1' if environment == 'development' else '0.0.0.0',
                'port': 8000,
                'reload': environment == 'development',
                'workers': 1 if environment == 'development' else 4
            },
            'security': {
                'jwt_secret_key': 'your-secret-key-change-this-in-production',
                'cors_origins': ['*'] if environment == 'development' else ['https://yourdomain.com']
            },
            'database': {
                'url': 'postgresql://user:password@localhost:5432/trading',
                'pool_size': 20
            },
            'cache': {
                'redis_url': 'redis://localhost:6379',
                'ttl_short': 300
            },
            'monitoring': {
                'log_level': 'DEBUG' if environment == 'development' else 'INFO'
            },
            'feature_flags': {
                'enable_ai_analysis': True,
                'enable_real_time_data': True,
                'enable_user_authentication': True
            }
        }

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description="Configuration Management CLI", formatter_class=argparse.RawDescriptionHelpFormatter, epilog="""
Examples:
  # Validate configuration
  python scripts/config_manager.py validate --environment production

  # Get configuration value
  python scripts/config_manager.py get server.port --environment production

  # Set configuration value
  python scripts/config_manager.py set server.debug true --environment development

  # List all configuration values
  python scripts/config_manager.py list --environment production

  # Backup configuration
  python scripts/config_manager.py backup --environment production

  # Enable hot-reloading
  python scripts/config_manager.py hot-reload

  # Manage feature flags
  python scripts/config_manager.py feature-flag list
  python scripts/config_manager.py feature-flag set enable_ai_analysis --enabled true

  # Manage secrets
  python scripts/config_manager.py secrets list
  python scripts/config_manager.py secrets set db_password mysecret --secret-type database_password --security-level secret

  # Generate configuration
  python scripts/config_manager.py generate production --output-file config/production.yaml
    """)

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate configuration')
    validate_parser.add_argument('--environment', help='Environment to validate')
    validate_parser.add_argument('--format', choices=['text', 'json', 'yaml'], default='text', help='Output format')

    # Get command
    get_parser = subparsers.add_parser('get', help='Get configuration value')
    get_parser.add_argument('key', help='Configuration key (dot-separated for nested values)')
    get_parser.add_argument('--environment', help='Environment')
    get_parser.add_argument('--default', help='Default value if not found')

    # Set command
    set_parser = subparsers.add_parser('set', help='Set configuration value')
    set_parser.add_argument('key', help='Configuration key (dot-separated for nested values)')
    set_parser.add_argument('value', help='Configuration value')
    set_parser.add_argument('--environment', help='Environment')
    set_parser.add_argument('--no-persist', action='store_true', help='Do not persist to file')

    # List command
    list_parser = subparsers.add_parser('list', help='List configuration values')
    list_parser.add_argument('--environment', help='Environment')
    list_parser.add_argument('--pattern', help='Filter by key pattern (regex)')

    # Backup command
    backup_parser = subparsers.add_parser('backup', help='Backup configuration')
    backup_parser.add_argument('--environment', help='Environment to backup')
    backup_parser.add_argument('--path', help='Backup path')

    # Restore command
    restore_parser = subparsers.add_parser('restore', help='Restore configuration from backup')
    restore_parser.add_argument('backup_path', help='Backup file/directory path')
    restore_parser.add_argument('--environment', help='Target environment')

    # Hot-reload command
    subparsers.add_parser('hot-reload', help='Enable hot-reloading')

    # Feature flag commands
    ff_parser = subparsers.add_parser('feature-flag', help='Manage feature flags')
    ff_subparsers = ff_parser.add_subparsers(dest='ff_action', help='Feature flag actions')

    ff_list_parser = ff_subparsers.add_parser('list', help='List feature flags')
    ff_get_parser = ff_subparsers.add_parser('get', help='Get feature flag value')
    ff_get_parser.add_argument('flag_name', help='Feature flag name')

    ff_set_parser = ff_subparsers.add_parser('set', help='Set feature flag value')
    ff_set_parser.add_argument('flag_name', help='Feature flag name')
    ff_set_parser.add_argument('--enabled', action='store_true', help='Enable flag')
    ff_set_parser.add_argument('--disabled', action='store_true', help='Disable flag')

    ff_toggle_parser = ff_subparsers.add_parser('toggle', help='Toggle feature flag')
    ff_toggle_parser.add_argument('flag_name', help='Feature flag name')

    # Secrets commands
    secrets_parser = subparsers.add_parser('secrets', help='Manage secrets')
    secrets_subparsers = secrets_parser.add_subparsers(dest='secrets_action', help='Secrets actions')

    secrets_list_parser = secrets_subparsers.add_parser('list', help='List secrets')

    secrets_get_parser = secrets_subparsers.add_parser('get', help='Get secret value')
    secrets_get_parser.add_argument('key', help='Secret key')

    secrets_set_parser = secrets_subparsers.add_parser('set', help='Set secret value')
    secrets_set_parser.add_argument('key', help='Secret key')
    secrets_set_parser.add_argument('value', help='Secret value')
    secrets_set_parser.add_argument('--secret-type', choices=['api_key', 'database_password', 'jwt_secret', 'encryption_key', 'credential', 'certificate', 'token', 'other'], default='other', help='Secret type')
    secrets_set_parser.add_argument('--security-level', choices=['public', 'internal', 'confidential', 'secret', 'top_secret'], default='secret', help='Security level')

    secrets_delete_parser = secrets_subparsers.add_parser('delete', help='Delete secret')
    secrets_delete_parser.add_argument('key', help='Secret key')

    secrets_rotate_parser = secrets_subparsers.add_parser('rotate', help='Rotate secret')
    secrets_rotate_parser.add_argument('key', help='Secret key')
    secrets_rotate_parser.add_argument('--value', help='New secret value (optional, will generate if not provided)')

    secrets_health_parser = secrets_subparsers.add_parser('health', help='Check secrets manager health')

    # Generate command
    generate_parser = subparsers.add_parser('generate', help='Generate configuration template')
    generate_parser.add_argument('environment', help='Environment for configuration')
    generate_parser.add_argument('--output-file', help='Output file path')
    generate_parser.add_argument('--template', help='Template name to use')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    cli = ConfigCLI()

    if args.command == 'validate':
        success = cli.validate_config(args.environment, args.format)
    elif args.command == 'get':
        success = cli.get_config_value(args.key, args.environment, args.default) is not None
    elif args.command == 'set':
        success = cli.set_config_value(args.key, args.value, args.environment, not args.no_persist)
    elif args.command == 'list':
        success = cli.list_config_values(args.environment, args.pattern)
    elif args.command == 'backup':
        success = cli.backup_config(args.environment, args.path)
    elif args.command == 'restore':
        success = cli.restore_config(args.backup_path, args.environment)
    elif args.command == 'hot-reload':
        success = cli.enable_hot_reload(args.environment)
    elif args.command == 'feature-flag':
        if args.ff_action == 'list':
            success = cli.manage_feature_flags('list')
        elif args.ff_action == 'get':
            success = cli.manage_feature_flags('get', args.flag_name)
        elif args.ff_action == 'set':
            enabled = args.enabled or not args.disabled
            success = cli.manage_feature_flags('set', args.flag_name, enabled=enabled)
        elif args.ff_action == 'toggle':
            success = cli.manage_feature_flags('toggle', args.flag_name)
        else:
            print(f"Unknown feature flag action: {args.ff_action}")
            return 1
    elif args.command == 'secrets':
        if args.secrets_action == 'list':
            success = cli.manage_secrets('list')
        elif args.secrets_action == 'get':
            success = cli.manage_secrets('get', args.key)
        elif args.secrets_action == 'set':
            success = cli.manage_secrets('set', args.key, args.value, args.secret_type, args.security_level)
        elif args.secrets_action == 'delete':
            success = cli.manage_secrets('delete', args.key)
        elif args.secrets_action == 'rotate':
            success = cli.manage_secrets('rotate', args.key, args.value)
        elif args.secrets_action == 'health':
            success = cli.manage_secrets('health')
        else:
            print(f"Unknown secrets action: {args.secrets_action}")
            return 1
    elif args.command == 'generate':
        success = cli.generate_config(args.environment, args.output_file, args.template)
    else:
        print(f"Unknown command: {args.command}")
        return 1

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())