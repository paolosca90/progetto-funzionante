"""
Configuration Testing Framework
Provides comprehensive testing capabilities for configuration system
"""

import unittest
import pytest
import tempfile
import json
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path to import config modules
sys.path.append(str(Path(__file__).parent.parent))

from config.config_system import ConfigurationManager, FeatureFlag, ConfigVersion
from config.startup_validator import ConfigurationValidator, ConfigurationHealthReport

class TestConfigurationManager(unittest.TestCase):
    """Test cases for ConfigurationManager"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_manager = ConfigurationManager(self.temp_dir)

    def tearDown(self):
        """Clean up test environment"""
        self.config_manager.cleanup()

    def test_initialization(self):
        """Test configuration manager initialization"""
        self.assertIsNotNone(self.config_manager)
        self.assertTrue(self.temp_dir.exists())
        self.assertEqual(len(self.config_manager.config_cache), 0)

    def test_set_and_get_config(self):
        """Test setting and getting configuration values"""
        # Test setting a configuration
        result = self.config_manager.set('test_key', 'test_value')
        self.assertTrue(result)

        # Test getting the configuration
        value = self.config_manager.get('test_key')
        self.assertEqual(value, 'test_value')

        # Test getting non-existent configuration
        value = self.config_manager.get('non_existent_key', 'default_value')
        self.assertEqual(value, 'default_value')

    def test_configuration_validation(self):
        """Test configuration validation"""
        # Set some test configurations
        self.config_manager.set('database_url', 'postgresql://localhost/test')
        self.config_manager.set('jwt_secret_key', 'test_secret_key_32_characters_long')
        self.config_manager.set('oanda_api_key', 'test_api_key')

        # Validate configuration
        result = self.config_manager.validate_configuration()
        self.assertIsInstance(result, dict)
        self.assertIn('valid', result)
        self.assertIn('errors', result)
        self.assertIn('warnings', result)

    def test_feature_flags(self):
        """Test feature flag management"""
        # Test setting a feature flag
        result = self.config_manager.set_feature_flag('test_flag', True, 'Test feature flag')
        self.assertTrue(result)

        # Test getting a feature flag
        enabled = self.config_manager.get_feature_flag('test_flag')
        self.assertTrue(enabled)

        # Test feature flag with rollout percentage
        result = self.config_manager.set_feature_flag('partial_flag', True, 'Partial rollout', rollout_percentage=50)
        self.assertTrue(result)

        # Test listing feature flags
        flags = self.config_manager.list_feature_flags()
        self.assertGreaterEqual(len(flags), 2)

    def test_feature_flag_conditions(self):
        """Test feature flag with conditions"""
        # Set feature flag with conditions
        conditions = {'user_role': 'admin', 'tier': 'premium'}
        result = self.config_manager.set_feature_flag(
            'conditional_flag', True, 'Conditional feature flag',
            conditions=conditions
        )
        self.assertTrue(result)

        # Test with matching user attributes
        user_attributes = {'user_role': 'admin', 'tier': 'premium', 'other': 'value'}
        enabled = self.config_manager.get_feature_flag('conditional_flag', user_id='user123', user_attributes=user_attributes)
        self.assertTrue(enabled)

        # Test with non-matching user attributes
        user_attributes = {'user_role': 'user', 'tier': 'basic'}
        enabled = self.config_manager.get_feature_flag('conditional_flag', user_id='user456', user_attributes=user_attributes)
        self.assertFalse(enabled)

    def test_configuration_backup_and_restore(self):
        """Test configuration backup and restore"""
        # Set some configurations
        self.config_manager.set('test_key1', 'test_value1')
        self.config_manager.set('test_key2', 'test_value2')

        # Backup configuration
        backup_path = self.temp_dir / 'backup'
        result = self.config_manager.backup_configuration(backup_path)
        self.assertTrue(result)
        self.assertTrue(backup_path.exists())

        # Modify configuration
        self.config_manager.set('test_key1', 'modified_value')

        # Restore configuration
        result = self.config_manager.restore_configuration(backup_path)
        self.assertTrue(result)

        # Verify restored values
        self.assertEqual(self.config_manager.get('test_key1'), 'test_value1')
        self.assertEqual(self.config_manager.get('test_key2'), 'test_value2')

    def test_configuration_versioning(self):
        """Test configuration versioning"""
        # Create initial version
        version1 = self.config_manager.create_config_version('Initial version')
        self.assertIsNotNone(version1)

        # Modify configuration
        self.config_manager.set('test_key', 'test_value')

        # Create second version
        version2 = self.config_manager.create_config_version('Added test configuration')
        self.assertIsNotNone(version2)

        # List versions
        versions = self.config_manager.list_config_versions()
        self.assertEqual(len(versions), 2)
        self.assertEqual(versions[0].version, version2)  # Most recent first

    def test_secrets_management(self):
        """Test secrets management"""
        # Initialize secrets manager
        self.config_manager.secrets_manager.initialize('test_encryption_key')

        # Store a secret
        result = self.config_manager.secrets_manager.store_secret('test_secret', 'secret_value')
        self.assertTrue(result)

        # Retrieve the secret
        value = self.config_manager.secrets_manager.get_secret('test_secret')
        self.assertEqual(value, 'secret_value')

        # List secrets
        secrets = self.config_manager.secrets_manager.list_secrets()
        self.assertIn('test_secret', secrets)

    def test_hot_reload(self):
        """Test hot-reloading configuration"""
        # Set initial configuration
        self.config_manager.set('test_key', 'initial_value')

        # Enable hot-reload (this will fail without watchdog, but we test the setup)
        with patch('config.config_system.ConfigurationManager._setup_file_watchers'):
            self.config_manager.enable_hot_reload()
            self.assertTrue(self.config_manager.hot_reload_enabled)

    def test_configuration_summary(self):
        """Test configuration summary"""
        # Set some configurations and feature flags
        self.config_manager.set('test_key', 'test_value')
        self.config_manager.set_feature_flag('test_flag', True)

        # Get summary
        summary = self.config_manager.get_config_summary()
        self.assertIsInstance(summary, dict)
        self.assertIn('total_configs', summary)
        self.assertIn('feature_flags', summary)
        self.assertIn('config_history', summary)

class TestConfigurationValidator(unittest.TestCase):
    """Test cases for ConfigurationValidator"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_manager = ConfigurationManager(self.temp_dir)
        self.validator = ConfigurationValidator(self.config_manager)

    def tearDown(self):
        """Clean up test environment"""
        self.config_manager.cleanup()

    def test_validation_rules(self):
        """Test validation rules exist"""
        rules = self.validator.validation_rules
        self.assertIsInstance(rules, dict)
        self.assertGreater(len(rules), 0)

        # Check some essential rules
        self.assertIn('database_url', rules)
        self.assertIn('jwt_secret_key', rules)
        self.assertIn('oanda_api_key', rules)

    def test_validation_required_missing(self):
        """Test validation of required missing configuration"""
        result = self.validator.validate_configuration()

        # Should have critical issues for missing required configurations
        self.assertGreater(result.critical_issues, 0)
        self.assertEqual(result.overall_status, 'unhealthy')
        self.assertFalse(result.can_start)

    def test_validation_with_valid_config(self):
        """Test validation with valid configuration"""
        # Set valid configurations
        self.config_manager.set('database_url', 'postgresql://localhost/test')
        self.config_manager.set('jwt_secret_key', 'test_secret_key_32_characters_long')
        self.config_manager.set('oanda_api_key', 'test_api_key')
        self.config_manager.set('oanda_account_id', 'test_account_id')
        self.config_manager.set('gemini_api_key', 'test_gemini_key')

        result = self.validator.validate_configuration()

        # Should be healthy
        self.assertEqual(result.critical_issues, 0)
        self.assertEqual(result.overall_status, 'healthy')
        self.assertTrue(result.can_start)

    def test_environment_specific_validation(self):
        """Test environment-specific validation"""
        # Test production environment
        self.config_manager.set('environment', 'production')
        self.config_manager.set('debug', True)

        result = self.validator.validate_configuration()

        # Should have errors for production with debug=True
        self.assertGreater(result.error_issues, 0)

        # Fix the issue
        self.config_manager.set('debug', False)
        self.config_manager.set('security_require_https', True)
        self.config_manager.set('cors_origins', ['https://example.com'])

        result = self.validator.validate_configuration()

        # Should have fewer errors
        self.assertEqual(result.error_issues, 0)

    def test_apply_defaults(self):
        """Test applying default values"""
        # Clear any existing configurations
        self.config_manager.config_cache.clear()

        # Apply defaults
        defaults = self.validator.apply_defaults()

        # Should have applied some defaults
        self.assertIsInstance(defaults, dict)
        self.assertGreater(len(defaults), 0)

        # Check some defaults were applied
        self.assertIsNotNone(self.config_manager.get('environment'))
        self.assertIsNotNone(self.config_manager.get('debug'))
        self.assertIsNotNone(self.config_manager.get('port'))

    def test_generate_config_template(self):
        """Test generating configuration template"""
        template = self.validator.generate_config_file()

        self.assertIsInstance(template, str)
        self.assertGreater(len(template), 0)
        self.assertIn('Configuration File Template', template)

        # Should contain some expected sections
        self.assertIn('Database Configuration', template)
        self.assertIn('Security Configuration', template)
        self.assertIn('API Configuration', template)

class TestFeatureFlag(unittest.TestCase):
    """Test cases for FeatureFlag"""

    def test_feature_flag_creation(self):
        """Test feature flag creation"""
        flag = FeatureFlag(
            name='test_flag',
            enabled=True,
            description='Test feature flag',
            environment='development'
        )

        self.assertEqual(flag.name, 'test_flag')
        self.assertTrue(flag.enabled)
        self.assertEqual(flag.description, 'Test feature flag')
        self.assertEqual(flag.environment, 'development')
        self.assertEqual(flag.rollout_percentage, 100)
        self.assertEqual(flag.conditions, {})
        self.assertEqual(flag.tags, [])

    def test_feature_flag_with_conditions(self):
        """Test feature flag with conditions"""
        conditions = {'user_role': 'admin', 'tier': 'premium'}
        tags = ['security', 'admin']

        flag = FeatureFlag(
            name='admin_flag',
            enabled=True,
            description='Admin feature flag',
            environment='production',
            conditions=conditions,
            tags=tags,
            rollout_percentage=100
        )

        self.assertEqual(flag.conditions, conditions)
        self.assertEqual(flag.tags, tags)
        self.assertEqual(flag.rollout_percentage, 100)

class TestConfigurationIntegration(unittest.TestCase):
    """Integration tests for configuration system"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.config_manager = ConfigurationManager(self.temp_dir)

    def tearDown(self):
        """Clean up test environment"""
        self.config_manager.cleanup()

    def test_complete_configuration_workflow(self):
        """Test complete configuration workflow"""
        # 1. Set initial configuration
        self.config_manager.set('database_url', 'postgresql://localhost/test')
        self.config_manager.set('jwt_secret_key', 'test_secret_key_32_characters_long')
        self.config_manager.set('oanda_api_key', 'test_api_key')
        self.config_manager.set('environment', 'development')

        # 2. Create feature flags
        self.config_manager.set_feature_flag('new_ui', True, 'New user interface')
        self.config_manager.set_feature_flag('beta_feature', False, 'Beta features', tags=['beta'])

        # 3. Create configuration version
        version = self.config_manager.create_config_version('Initial setup')
        self.assertIsNotNone(version)

        # 4. Validate configuration
        validator = ConfigurationValidator(self.config_manager)
        health_report = validator.validate_configuration()

        self.assertEqual(health_report.critical_issues, 0)
        self.assertEqual(health_report.overall_status, 'healthy')
        self.assertTrue(health_report.can_start)

        # 5. Backup configuration
        backup_path = self.temp_dir / 'backup'
        result = self.config_manager.backup_configuration(backup_path)
        self.assertTrue(result)

        # 6. Modify configuration
        self.config_manager.set('environment', 'production')
        self.config_manager.set_feature_flag('new_ui', False)

        # 7. Restore configuration
        result = self.config_manager.restore_configuration(backup_path)
        self.assertTrue(result)

        # 8. Verify restored configuration
        self.assertEqual(self.config_manager.get('environment'), 'development')
        self.assertTrue(self.config_manager.get_feature_flag('new_ui'))

    def test_environment_switching(self):
        """Test switching between environments"""
        # Set up development configuration
        self.config_manager.set('environment', 'development')
        self.config_manager.set('debug', True)
        self.config_manager.set_feature_flag('dev_feature', True, 'Development feature', environment='development')

        # Switch to production
        self.config_manager.set('environment', 'production')
        self.config_manager.set('debug', False)
        self.config_manager.set_feature_flag('prod_feature', True, 'Production feature', environment='production')

        # Test feature flag evaluation
        self.assertTrue(self.config_manager.get_feature_flag('prod_feature'))
        self.assertFalse(self.config_manager.get_feature_flag('dev_feature'))

        # Switch back to development
        self.config_manager.set('environment', 'development')
        self.assertTrue(self.config_manager.get_feature_flag('dev_feature'))
        self.assertFalse(self.config_manager.get_feature_flag('prod_feature'))

    def test_secrets_integration(self):
        """Test secrets integration with configuration"""
        # Initialize secrets
        self.config_manager.secrets_manager.initialize('test_encryption_key')

        # Store some secrets
        self.config_manager.secrets_manager.store_secret('api_key', 'secret_api_key')
        self.config_manager.secrets_manager.store_secret('db_password', 'secret_password')

        # Retrieve secrets
        api_key = self.config_manager.secrets_manager.get_secret('api_key')
        db_password = self.config_manager.secrets_manager.get_secret('db_password')

        self.assertEqual(api_key, 'secret_api_key')
        self.assertEqual(db_password, 'secret_password')

        # Test secrets rotation
        result = self.config_manager.secrets_manager.rotate_secret('api_key', 'new_api_key')
        self.assertTrue(result)

        new_api_key = self.config_manager.secrets_manager.get_secret('api_key')
        self.assertEqual(new_api_key, 'new_api_key')

if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)