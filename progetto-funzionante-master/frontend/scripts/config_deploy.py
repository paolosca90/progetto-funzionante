#!/usr/bin/env python3
"""
Configuration Deployment Script
Handles automated deployment of configuration across environments
"""

import os
import sys
import json
import yaml
import shutil
import subprocess
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import logging

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.config_system import ConfigurationManager
from config.validation import ConfigurationValidator, ValidationReport

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ConfigDeployer:
    """Handles configuration deployment and environment management"""

    def __init__(self, config_dir: Path = None):
        self.config_dir = config_dir or Path("config")
        self.deployments_dir = self.config_dir / "deployments"
        self.templates_dir = self.config_dir / "templates"
        self.config_manager = ConfigurationManager(self.config_dir)
        self.validator = ConfigurationValidator()

        # Ensure directories exist
        self.deployments_dir.mkdir(exist_ok=True)
        self.templates_dir.mkdir(exist_ok=True)

    def deploy_to_environment(self, environment: str, target_path: Path = None, dry_run: bool = False) -> bool:
        """Deploy configuration to a specific environment"""
        try:
            logger.info(f"Deploying configuration to {environment} environment")

            # Load environment configuration
            config_file = self.config_dir / f"config.{environment}.yaml"
            if not config_file.exists():
                logger.error(f"Configuration file not found: {config_file}")
                return False

            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)

            # Validate configuration
            validation_result = self.validator.validate_configuration(config, environment)
            if not validation_result.is_valid:
                logger.error(f"Configuration validation failed for {environment}:")
                for error in validation_result.errors:
                    logger.error(f"  {error.field}: {error.message}")
                return False

            # Prepare deployment package
            deployment_package = self._prepare_deployment_package(config, environment)

            if dry_run:
                logger.info("Dry run mode - would deploy:")
                logger.info(f"  Target path: {target_path or 'default'}")
                logger.info(f"  Files: {list(deployment_package.keys())}")
                return True

            # Determine target path
            if not target_path:
                target_path = self._get_default_target_path(environment)

            # Create deployment
            deployment_path = self._create_deployment(deployment_package, target_path, environment)

            # Run post-deployment checks
            if not self._run_post_deployment_checks(deployment_path, environment):
                logger.warning("Post-deployment checks failed")

            # Log deployment
            self._log_deployment(environment, deployment_path, validation_result)

            logger.info(f"Successfully deployed configuration to {environment}")
            logger.info(f"Deployment location: {deployment_path}")
            return True

        except Exception as e:
            logger.error(f"Deployment to {environment} failed: {e}")
            return False

    def rollback_deployment(self, environment: str, deployment_id: str = None) -> bool:
        """Rollback a deployment"""
        try:
            logger.info(f"Rolling back deployment for {environment}")

            # Find the deployment to rollback
            if deployment_id:
                deployment_path = self.deployments_dir / deployment_id
            else:
                # Rollback to previous deployment
                deployments = self._list_deployments(environment)
                if len(deployments) < 2:
                    logger.error("No previous deployment found for rollback")
                    return False
                deployment_path = deployments[-2]['path']

            if not deployment_path.exists():
                logger.error(f"Deployment not found: {deployment_path}")
                return False

            # Get current configuration location
            current_config_path = self._get_default_target_path(environment)

            # Backup current configuration
            backup_path = self._backup_current_config(environment)

            # Restore from deployment
            self._restore_deployment(deployment_path, current_config_path)

            # Verify rollback
            if not self._verify_configuration(current_config_path, environment):
                logger.error("Rollback verification failed")
                return False

            logger.info(f"Successfully rolled back deployment for {environment}")
            return True

        except Exception as e:
            logger.error(f"Rollback failed for {environment}: {e}")
            return False

    def promote_configuration(self, from_env: str, to_env: str, override_values: Dict[str, Any] = None) -> bool:
        """Promote configuration from one environment to another"""
        try:
            logger.info(f"Promoting configuration from {from_env} to {to_env}")

            # Load source configuration
            source_config_file = self.config_dir / f"config.{from_env}.yaml"
            if not source_config_file.exists():
                logger.error(f"Source configuration not found: {source_config_file}")
                return False

            with open(source_config_file, 'r') as f:
                source_config = yaml.safe_load(f)

            # Transform configuration for target environment
            target_config = self._transform_for_promotion(source_config, from_env, to_env, override_values)

            # Validate target configuration
            validation_result = self.validator.validate_configuration(target_config, to_env)
            if not validation_result.is_valid:
                logger.error(f"Target configuration validation failed:")
                for error in validation_result.errors:
                    logger.error(f"  {error.field}: {error.message}")
                return False

            # Backup current target configuration
            self._backup_current_config(to_env)

            # Save promoted configuration
            target_config_file = self.config_dir / f"config.{to_env}.yaml"
            with open(target_config_file, 'w') as f:
                yaml.safe_dump(target_config, f, default_flow_style=False, indent=2)

            # Deploy to target environment
            success = self.deploy_to_environment(to_env)

            # Log promotion
            self._log_promotion(from_env, to_env, validation_result)

            if success:
                logger.info(f"Successfully promoted configuration from {from_env} to {to_env}")
                return True
            else:
                logger.error(f"Failed to deploy promoted configuration to {to_env}")
                return False

        except Exception as e:
            logger.error(f"Promotion from {from_env} to {to_env} failed: {e}")
            return False

    def create_deployment_template(self, template_name: str, base_env: str = "production") -> bool:
        """Create a deployment template from an existing environment"""
        try:
            logger.info(f"Creating deployment template {template_name} from {base_env}")

            # Load base configuration
            base_config_file = self.config_dir / f"config.{base_env}.yaml"
            if not base_config_file.exists():
                logger.error(f"Base configuration not found: {base_config_file}")
                return False

            with open(base_config_file, 'r') as f:
                base_config = yaml.safe_load(f)

            # Create template with placeholders
            template_config = self._create_template_config(base_config)

            # Save template
            template_file = self.templates_dir / f"{template_name}.yaml"
            with open(template_file, 'w') as f:
                yaml.safe_dump(template_config, f, default_flow_style=False, indent=2)

            # Create template documentation
            self._create_template_documentation(template_name, template_config)

            logger.info(f"Successfully created deployment template: {template_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to create template {template_name}: {e}")
            return False

    def deploy_from_template(self, template_name: str, environment: str, variables: Dict[str, Any]) -> bool:
        """Deploy configuration from a template"""
        try:
            logger.info(f"Deploying from template {template_name} to {environment}")

            # Load template
            template_file = self.templates_dir / f"{template_name}.yaml"
            if not template_file.exists():
                logger.error(f"Template not found: {template_file}")
                return False

            with open(template_file, 'r') as f:
                template_config = yaml.safe_load(f)

            # Apply variables to template
            deployed_config = self._apply_template_variables(template_config, variables)

            # Validate deployed configuration
            validation_result = self.validator.validate_configuration(deployed_config, environment)
            if not validation_result.is_valid:
                logger.error(f"Template deployment validation failed:")
                for error in validation_result.errors:
                    logger.error(f"  {error.field}: {error.message}")
                return False

            # Save deployed configuration
            config_file = self.config_dir / f"config.{environment}.yaml"
            with open(config_file, 'w') as f:
                yaml.safe_dump(deployed_config, f, default_flow_style=False, indent=2)

            # Deploy to environment
            success = self.deploy_to_environment(environment)

            logger.info(f"Successfully deployed from template {template_name} to {environment}")
            return success

        except Exception as e:
            logger.error(f"Template deployment failed: {e}")
            return False

    def _prepare_deployment_package(self, config: Dict[str, Any], environment: str) -> Dict[str, str]:
        """Prepare deployment package with all necessary files"""
        package = {}

        # Main configuration file
        config_content = yaml.dump(config, default_flow_style=False, indent=2)
        package[f"config.{environment}.yaml"] = config_content

        # Environment file (extract sensitive values)
        env_vars = self._extract_environment_variables(config)
        env_content = "\n".join([f"{key}={value}" for key, value in env_vars.items()])
        package[f".env.{environment}"] = env_content

        # Deployment metadata
        metadata = {
            "environment": environment,
            "deployed_at": datetime.utcnow().isoformat(),
            "version": config.get('app', {}).get('version', 'unknown'),
            "checksum": self._generate_checksum(config_content)
        }
        package["deployment.json"] = json.dumps(metadata, indent=2)

        return package

    def _create_deployment(self, package: Dict[str, str], target_path: Path, environment: str) -> Path:
        """Create deployment files"""
        deployment_id = f"{environment}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        deployment_path = self.deployments_dir / deployment_id
        deployment_path.mkdir(exist_ok=True)

        # Write deployment files
        for filename, content in package.items():
            file_path = deployment_path / filename
            with open(file_path, 'w') as f:
                f.write(content)

        # Copy to target location
        for filename, content in package.items():
            if filename.startswith('config.'):
                target_file = target_path / filename
                target_file.parent.mkdir(parents=True, exist_ok=True)
                with open(target_file, 'w') as f:
                    f.write(content)

        return deployment_path

    def _run_post_deployment_checks(self, deployment_path: Path, environment: str) -> bool:
        """Run post-deployment verification checks"""
        try:
            # Check if all required files exist
            required_files = [f"config.{environment}.yaml", "deployment.json"]
            for file_name in required_files:
                file_path = deployment_path / file_name
                if not file_path.exists():
                    logger.error(f"Required deployment file missing: {file_name}")
                    return False

            # Verify deployment metadata
            metadata_file = deployment_path / "deployment.json"
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)

            required_fields = ["environment", "deployed_at", "version", "checksum"]
            for field in required_fields:
                if field not in metadata:
                    logger.error(f"Missing metadata field: {field}")
                    return False

            # Verify checksum
            config_file = deployment_path / f"config.{environment}.yaml"
            with open(config_file, 'r') as f:
                config_content = f.read()

            current_checksum = self._generate_checksum(config_content)
            if current_checksum != metadata["checksum"]:
                logger.error("Configuration checksum mismatch")
                return False

            return True

        except Exception as e:
            logger.error(f"Post-deployment checks failed: {e}")
            return False

    def _transform_for_promotion(self, config: Dict[str, Any], from_env: str, to_env: str, override_values: Dict[str, Any] = None) -> Dict[str, Any]:
        """Transform configuration for environment promotion"""
        promoted_config = config.copy()

        # Update environment-specific settings
        if 'app' in promoted_config:
            promoted_config['app']['environment'] = to_env

        # Apply environment-specific transformations
        if to_env == 'production':
            # Production-specific settings
            if 'server' in promoted_config:
                promoted_config['server'].update({
                    'debug': False,
                    'reload': False,
                    'workers': 8
                })
            if 'monitoring' in promoted_config:
                promoted_config['monitoring'].update({
                    'log_level': 'WARNING',
                    'enable_metrics': True,
                    'enable_error_tracking': True
                })
        elif to_env == 'staging':
            # Staging-specific settings
            if 'server' in promoted_config:
                promoted_config['server'].update({
                    'debug': False,
                    'reload': False,
                    'workers': 4
                })
            if 'monitoring' in promoted_config:
                promoted_config['monitoring'].update({
                    'log_level': 'INFO',
                    'enable_metrics': True
                })

        # Apply override values
        if override_values:
            promoted_config.update(override_values)

        return promoted_config

    def _create_template_config(self, base_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create template configuration with placeholders"""
        template_config = {}

        for section, section_config in base_config.items():
            template_section = {}
            for key, value in section_config.items():
                if isinstance(value, str) and self._is_sensitive_value(key, value):
                    # Replace sensitive values with placeholders
                    template_section[key] = f"{{{{{key.upper()}}}}}"
                else:
                    template_section[key] = value
            template_config[section] = template_section

        return template_config

    def _is_sensitive_value(self, key: str, value: str) -> bool:
        """Check if a value is sensitive and should be replaced with a placeholder"""
        sensitive_patterns = [
            'password', 'secret', 'key', 'token', 'api_key', 'jwt_secret',
            'dsn', 'database_url', 'redis_password'
        ]
        return any(pattern in key.lower() for pattern in sensitive_patterns)

    def _apply_template_variables(self, template_config: Dict[str, Any], variables: Dict[str, Any]) -> Dict[str, Any]:
        """Apply variables to template configuration"""
        deployed_config = {}

        for section, section_config in template_config.items():
            deployed_section = {}
            for key, value in section_config.items():
                if isinstance(value, str) and value.startswith('{{') and value.endswith('}}'):
                    # Replace placeholder with variable value
                    var_name = value[2:-2].lower()
                    deployed_section[key] = variables.get(var_name, value)
                else:
                    deployed_section[key] = value
            deployed_config[section] = deployed_section

        return deployed_config

    def _extract_environment_variables(self, config: Dict[str, Any]) -> Dict[str, str]:
        """Extract environment variables from configuration"""
        env_vars = {}

        def extract_recursive(config_dict, prefix=""):
            for key, value in config_dict.items():
                full_key = f"{prefix}_{key}" if prefix else key
                if isinstance(value, dict):
                    extract_recursive(value, full_key)
                elif isinstance(value, (str, int, float, bool)):
                    if self._is_environment_variable(full_key):
                        env_vars[full_key.upper()] = str(value)

        extract_recursive(config)
        return env_vars

    def _is_environment_variable(self, key: str) -> bool:
        """Check if a key should be exported as environment variable"""
        env_patterns = [
            'api_key', 'secret', 'password', 'database_url', 'redis_url',
            'email_host', 'email_user', 'email_password', 'host', 'port'
        ]
        return any(pattern in key.lower() for pattern in env_patterns)

    def _get_default_target_path(self, environment: str) -> Path:
        """Get default deployment target path for environment"""
        base_paths = {
            'development': Path('/opt/trading-system/dev/config'),
            'staging': Path('/opt/trading-system/staging/config'),
            'production': Path('/opt/trading-system/prod/config'),
            'test': Path('/opt/trading-system/test/config')
        }
        return base_paths.get(environment, Path('/tmp/config'))

    def _backup_current_config(self, environment: str) -> Path:
        """Backup current configuration"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_path = self.deployments_dir / f"backup_{environment}_{timestamp}"

        current_config_path = self._get_default_target_path(environment)
        if current_config_path.exists():
            shutil.copytree(current_config_path, backup_path)

        return backup_path

    def _restore_deployment(self, deployment_path: Path, target_path: Path):
        """Restore configuration from deployment"""
        if target_path.exists():
            shutil.rmtree(target_path)
        shutil.copytree(deployment_path, target_path)

    def _verify_configuration(self, config_path: Path, environment: str) -> bool:
        """Verify deployed configuration"""
        try:
            config_file = config_path / f"config.{environment}.yaml"
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)

            validation_result = self.validator.validate_configuration(config, environment)
            return validation_result.is_valid

        except Exception as e:
            logger.error(f"Configuration verification failed: {e}")
            return False

    def _generate_checksum(self, content: str) -> str:
        """Generate checksum for content"""
        import hashlib
        return hashlib.sha256(content.encode()).hexdigest()

    def _log_deployment(self, environment: str, deployment_path: Path, validation_result: ValidationReport):
        """Log deployment details"""
        log_entry = {
            "type": "deployment",
            "environment": environment,
            "deployment_path": str(deployment_path),
            "timestamp": datetime.utcnow().isoformat(),
            "validation": {
                "valid": validation_result.is_valid,
                "errors": len(validation_result.errors),
                "warnings": len(validation_result.warnings)
            }
        }

        log_file = self.deployments_dir / "deployments.log"
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

    def _log_promotion(self, from_env: str, to_env: str, validation_result: ValidationReport):
        """Log promotion details"""
        log_entry = {
            "type": "promotion",
            "from_environment": from_env,
            "to_environment": to_env,
            "timestamp": datetime.utcnow().isoformat(),
            "validation": {
                "valid": validation_result.is_valid,
                "errors": len(validation_result.errors),
                "warnings": len(validation_result.warnings)
            }
        }

        log_file = self.deployments_dir / "promotions.log"
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')

    def _create_template_documentation(self, template_name: str, template_config: Dict[str, Any]):
        """Create documentation for template"""
        doc_file = self.templates_dir / f"{template_name}.md"
        doc_content = f"""# {template_name} Configuration Template

This template provides a standardized configuration structure for deploying the Trading Signals System.

## Required Variables

The following variables must be provided when using this template:

"""

        # Extract required variables
        required_vars = set()

        def extract_vars(config_dict):
            for value in config_dict.values():
                if isinstance(value, str) and value.startswith('{{') and value.endswith('}}'):
                    var_name = value[2:-2].lower()
                    required_vars.add(var_name)
                elif isinstance(value, dict):
                    extract_vars(value)

        extract_vars(template_config)

        for var in sorted(required_vars):
            doc_content += f"- **{var.upper()}**: Description for {var}\n"

        doc_content += """

## Usage

To deploy using this template:

```bash
python scripts/config_deploy.py deploy-from-template {template_name} <environment> --variables 'KEY1=value1,KEY2=value2'
```

## Configuration Sections

"""

        # Document configuration sections
        for section, section_config in template_config.items():
            doc_content += f"### {section.title()}\n\n"
            for key, value in section_config.items():
                if isinstance(value, str) and value.startswith('{{') and value.endswith('}}'):
                    doc_content += f"- **{key}**: Template variable `{{{value}}}`\n"
                else:
                    doc_content += f"- **{key}**: `{value}`\n"
            doc_content += "\n"

        with open(doc_file, 'w') as f:
            f.write(doc_content)

    def _list_deployments(self, environment: str) -> List[Dict[str, Any]]:
        """List deployments for an environment"""
        deployments = []
        for deployment_path in self.deployments_dir.iterdir():
            if deployment_path.is_dir() and deployment_path.name.startswith(environment):
                metadata_file = deployment_path / "deployment.json"
                if metadata_file.exists():
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    deployments.append({
                        "path": deployment_path,
                        "metadata": metadata
                    })

        return sorted(deployments, key=lambda x: x["metadata"]["deployed_at"], reverse=True)

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description="Configuration Deployment Tool")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Deploy command
    deploy_parser = subparsers.add_parser('deploy', help='Deploy configuration to environment')
    deploy_parser.add_argument('environment', help='Target environment')
    deploy_parser.add_argument('--target-path', help='Target deployment path')
    deploy_parser.add_argument('--dry-run', action='store_true', help='Dry run mode')

    # Rollback command
    rollback_parser = subparsers.add_parser('rollback', help='Rollback deployment')
    rollback_parser.add_argument('environment', help='Environment to rollback')
    rollback_parser.add_argument('--deployment-id', help='Specific deployment ID to rollback to')

    # Promote command
    promote_parser = subparsers.add_parser('promote', help='Promote configuration between environments')
    promote_parser.add_argument('from_env', help='Source environment')
    promote_parser.add_argument('to_env', help='Target environment')
    promote_parser.add_argument('--override', help='Override values as JSON string')

    # Create template command
    template_parser = subparsers.add_parser('create-template', help='Create deployment template')
    template_parser.add_argument('template_name', help='Template name')
    template_parser.add_argument('--base-env', default='production', help='Base environment')

    # Deploy from template command
    template_deploy_parser = subparsers.add_parser('deploy-from-template', help='Deploy from template')
    template_deploy_parser.add_argument('template_name', help='Template name')
    template_deploy_parser.add_argument('environment', help='Target environment')
    template_deploy_parser.add_argument('--variables', required=True, help='Template variables as KEY=VALUE,KEY2=VALUE2')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    deployer = ConfigDeployer()

    if args.command == 'deploy':
        success = deployer.deploy_to_environment(args.environment, Path(args.target_path) if args.target_path else None, args.dry_run)
    elif args.command == 'rollback':
        success = deployer.rollback_deployment(args.environment, args.deployment_id)
    elif args.command == 'promote':
        override_values = json.loads(args.override) if args.override else None
        success = deployer.promote_configuration(args.from_env, args.to_env, override_values)
    elif args.command == 'create-template':
        success = deployer.create_deployment_template(args.template_name, args.base_env)
    elif args.command == 'deploy-from-template':
        variables = dict(pair.split('=', 1) for pair in args.variables.split(','))
        success = deployer.deploy_from_template(args.template_name, args.environment, variables)
    else:
        print(f"Unknown command: {args.command}")
        return 1

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())