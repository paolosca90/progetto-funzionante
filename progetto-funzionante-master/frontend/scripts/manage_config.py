#!/usr/bin/env python3
"""
Configuration Management Script

Command-line utility for managing application configuration including:
- Environment validation
- Configuration migration
- Backup and restore
- Environment comparison
- Deployment preparation

Usage:
    python scripts/manage_config.py validate --env .env.production
    python scripts/manage_config.py create --environment staging
    python scripts/manage_config.py backup
    python scripts/manage_config.py compare env1 env2
    python scripts/manage_config.py migrate --from .env --to .env.new
"""

import argparse
import os
import sys
import json
from pathlib import Path
from typing import Optional

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config_manager import ConfigurationManager
from config.settings import Environment, get_settings


class ConfigCLI:
    """Command-line interface for configuration management"""

    def __init__(self):
        self.config_manager = ConfigurationManager()
        self.parser = self.create_parser()

    def create_parser(self) -> argparse.ArgumentParser:
        """Create command-line argument parser"""
        parser = argparse.ArgumentParser(
            description="Configuration Management Utility",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Validate environment file
  python scripts/manage_config.py validate --env .env.production

  # Create new environment file
  python scripts/manage_config.py create --environment staging --output .env.staging

  # Backup current configuration
  python scripts/manage_config.py backup --output config_backup.json

  # Compare two environments
  python scripts/manage_config.py compare development production

  # Migrate old configuration format
  python scripts/manage_config.py migrate --from .env --to .env.new

  # Get configuration summary
  python scripts/manage_config.py summary

  # Generate deployment configuration
  python scripts/manage_config.py deploy --environment production --format json
            """
        )

        subparsers = parser.add_subparsers(dest='command', help='Available commands')

        # Validate command
        validate_parser = subparsers.add_parser('validate', help='Validate environment file')
        validate_parser.add_argument('--env', required=True, help='Environment file to validate')
        validate_parser.add_argument('--json', action='store_true', help='Output as JSON')

        # Create command
        create_parser = subparsers.add_parser('create', help='Create environment file')
        create_parser.add_argument('--environment', required=True,
                                 choices=['development', 'staging', 'production', 'testing'],
                                 help='Environment to create')
        create_parser.add_argument('--output', required=True, help='Output file path')
        create_parser.add_argument('--template', help='Template file to use')

        # Backup command
        backup_parser = subparsers.add_parser('backup', help='Backup current configuration')
        backup_parser.add_argument('--output', help='Backup file path (auto-generated if not specified)')

        # Restore command
        restore_parser = subparsers.add_parser('restore', help='Restore configuration from backup')
        restore_parser.add_argument('--backup', required=True, help='Backup file to restore from')

        # Compare command
        compare_parser = subparsers.add_parser('compare', help='Compare two environments')
        compare_parser.add_argument('env1', help='First environment')
        compare_parser.add_argument('env2', help='Second environment')
        compare_parser.add_argument('--json', action='store_true', help='Output as JSON')

        # Migrate command
        migrate_parser = subparsers.add_parser('migrate', help='Migrate old configuration format')
        migrate_parser.add_argument('--from', dest='from_file', required=True, help='Source configuration file')
        migrate_parser.add_argument('--to', dest='to_file', required=True, help='Destination configuration file')

        # Summary command
        summary_parser = subparsers.add_parser('summary', help='Get configuration summary')
        summary_parser.add_argument('--json', action='store_true', help='Output as JSON')

        # Deploy command
        deploy_parser = subparsers.add_parser('deploy', help='Generate deployment configuration')
        deploy_parser.add_argument('--environment', required=True,
                                  choices=['development', 'staging', 'production', 'testing'],
                                  help='Target environment')
        deploy_parser.add_argument('--format', choices=['env', 'json'], default='env',
                                 help='Output format (env or json)')

        # Generate command
        generate_parser = subparsers.add_parser('generate', help='Generate secure values')
        generate_parser.add_argument('--type', required=True,
                                   choices=['jwt_secret', 'database_url', 'all'],
                                   help='Type of value to generate')
        generate_parser.add_argument('--length', type=int, default=64, help='Length for generated secrets')

        return parser

    def validate_command(self, args):
        """Handle validate command"""
        if not os.path.exists(args.env):
            print(f"❌ Environment file not found: {args.env}")
            return 1

        validation = self.config_manager.validate_environment_file(args.env)

        if args.json:
            print(json.dumps(validation, indent=2))
        else:
            print(f"🔍 Validating: {args.env}")
            print(f"{'✅ Valid' if validation['valid'] else '❌ Invalid'}")
            print(f"📊 Variables found: {len(validation.get('required_vars', []))}")

            if validation.get('errors'):
                print("\n❌ Errors:")
                for error in validation['errors']:
                    print(f"   • {error}")

            if validation.get('warnings'):
                print("\n⚠️  Warnings:")
                for warning in validation['warnings']:
                    print(f"   • {warning}")

            if validation.get('deprecated_vars'):
                print("\n🔄 Deprecated variables:")
                for var in validation['deprecated_vars']:
                    print(f"   • {var}")

        return 0 if validation['valid'] else 1

    def create_command(self, args):
        """Handle create command"""
        template_path = args.template
        if not template_path:
            template_map = {
                'development': '.env.development',
                'staging': '.env.staging',
                'production': '.env.production',
                'testing': '.env.test'
            }
            template_path = template_map.get(args.environment)

        success = self.config_manager.create_environment_file(
            environment=args.environment,
            output_path=args.output,
            template_path=template_path
        )

        if success:
            print(f"✅ Created environment file: {args.output}")
            print(f"📝 Environment: {args.environment}")
            if template_path:
                print(f"📋 Template: {template_path}")
        else:
            print(f"❌ Failed to create environment file")
            return 1

        return 0

    def backup_command(self, args):
        """Handle backup command"""
        try:
            backup_path = self.config_manager.backup_configuration(args.output)
            print(f"✅ Configuration backed up to: {backup_path}")
            print(f"📅 Backup time: {self.config_manager.settings.environment.value.upper()}")
        except Exception as e:
            print(f"❌ Backup failed: {str(e)}")
            return 1
        return 0

    def restore_command(self, args):
        """Handle restore command"""
        success = self.config_manager.restore_configuration(args.backup)
        if success:
            print(f"✅ Configuration backup validated: {args.backup}")
            print("⚠️  Manual restoration required - update environment variables from backup")
        else:
            print(f"❌ Failed to restore configuration")
            return 1
        return 0

    def compare_command(self, args):
        """Handle compare command"""
        comparison = self.config_manager.compare_environments(args.env1, args.env2)

        if args.json:
            print(json.dumps(comparison, indent=2))
        else:
            print(f"🔍 Comparing: {args.env1} vs {args.env2}")
            print(f"📊 Configuration differences:\n")

            if comparison.get('only_in_env1'):
                print(f"🔸 Only in {args.env1}:")
                for key, value in comparison['only_in_env1'].items():
                    print(f"   {key} = {value}")
                print()

            if comparison.get('only_in_env2'):
                print(f"🔸 Only in {args.env2}:")
                for key, value in comparison['only_in_env2'].items():
                    print(f"   {key} = {value}")
                print()

            if comparison.get('different_values'):
                print(f"🔄 Different values:")
                for key, values in comparison['different_values'].items():
                    print(f"   {key}:")
                    print(f"      {args.env1}: {values[args.env1]}")
                    print(f"      {args.env2}: {values[args.env2]}")
                print()

            same_count = len(comparison.get('same_values', []))
            if same_count > 0:
                print(f"✅ Same values: {same_count} variables")

        return 0

    def migrate_command(self, args):
        """Handle migrate command"""
        if not os.path.exists(args.from_file):
            print(f"❌ Source file not found: {args.from_file}")
            return 1

        success = self.config_manager.migrate_old_config(args.from_file, args.to_file)
        if success:
            print(f"✅ Configuration migrated: {args.from_file} → {args.to_file}")
            print("🔄 Old variables mapped to new format")
            print("⚠️  Review and update the new configuration file")
        else:
            print(f"❌ Migration failed")
            return 1
        return 0

    def summary_command(self, args):
        """Handle summary command"""
        summary = self.config_manager.get_configuration_summary()

        if args.json:
            print(json.dumps(summary, indent=2))
        else:
            print(f"📋 Configuration Summary")
            print(f"   Environment: {summary['environment'].upper()}")
            print(f"   Version: {summary['version']}")
            print(f"   Project: {summary['project_name']}")
            print(f"   Valid: {'✅' if summary['configuration_valid'] else '❌'}")

            if summary.get('configuration_errors'):
                print(f"\n❌ Configuration Errors:")
                for error in summary['configuration_errors']:
                    print(f"   • {error}")

            print(f"\n🔧 Server Configuration:")
            server_config = summary['server_config']
            print(f"   Host: {server_config['host']}")
            print(f"   Port: {server_config['port']}")
            print(f"   Debug: {server_config['debug']}")
            print(f"   Workers: {server_config['max_workers']}")

            print(f"\n🚀 Enabled Features:")
            features = summary['features_enabled']
            for feature, enabled in features.items():
                status = "✅" if enabled else "❌"
                print(f"   {status} {feature.replace('_', ' ').title()}")

        return 0

    def deploy_command(self, args):
        """Handle deploy command"""
        try:
            config = self.config_manager.generate_deployment_config(args.environment)

            if args.format == 'json':
                print(json.dumps(config, indent=2))
            else:
                print(f"# Deployment Configuration for {args.environment.upper()}")
                for key, value in config.items():
                    print(f"{key}={value}")

        except Exception as e:
            print(f"❌ Failed to generate deployment config: {str(e)}")
            return 1

        return 0

    def generate_command(self, args):
        """Handle generate command"""
        if args.type == 'jwt_secret':
            secret = self.config_manager.generate_jwt_secret(args.length)
            print(f"JWT_SECRET_KEY={secret}")
            print(f"# Generated {args.length}-character JWT secret key")

        elif args.type == 'database_url':
            print("# Database URL components:")
            print("# DATABASE_URL=postgresql://username:password@host:port/database")
            print("# Example:")
            print("DATABASE_URL=postgresql://trading_user:secure_pass@localhost:5432/trading_db")

        elif args.type == 'all':
            print("# Secure Configuration Values")
            print(f"JWT_SECRET_KEY={self.config_manager.generate_jwt_secret(args.length)}")
            print("# Database URL:")
            print("DATABASE_URL=postgresql://username:password@host:port/database")
            print("# API Keys:")
            print("OANDA_API_KEY=your-oanda-api-key")
            print("GEMINI_API_KEY=your-gemini-api-key")

        return 0

    def run(self):
        """Run the CLI application"""
        args = self.parser.parse_args()

        if not args.command:
            self.parser.print_help()
            return 1

        try:
            if args.command == 'validate':
                return self.validate_command(args)
            elif args.command == 'create':
                return self.create_command(args)
            elif args.command == 'backup':
                return self.backup_command(args)
            elif args.command == 'restore':
                return self.restore_command(args)
            elif args.command == 'compare':
                return self.compare_command(args)
            elif args.command == 'migrate':
                return self.migrate_command(args)
            elif args.command == 'summary':
                return self.summary_command(args)
            elif args.command == 'deploy':
                return self.deploy_command(args)
            elif args.command == 'generate':
                return self.generate_command(args)
            else:
                print(f"❌ Unknown command: {args.command}")
                return 1

        except KeyboardInterrupt:
            print("\n❌ Operation cancelled by user")
            return 1
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return 1


def main():
    """Main entry point"""
    cli = ConfigCLI()
    sys.exit(cli.run())


if __name__ == "__main__":
    main()