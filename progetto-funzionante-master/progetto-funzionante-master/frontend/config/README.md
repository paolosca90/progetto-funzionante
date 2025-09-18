# Configuration System Documentation

## Overview

The configuration system provides a comprehensive, production-ready environment configuration management solution for the FastAPI trading application. It supports multiple environments, hot-reloading, secrets management, feature flags, and robust validation.

## Architecture

### Core Components

1. **ConfigurationManager** (`config_system.py`)
   - Main configuration management class
   - Handles loading, validation, and persistence
   - Supports hot-reloading and environment-specific configs

2. **ConfigurationValidator** (`startup_validator.py`)
   - Validates configuration at application startup
   - Provides detailed error reporting and health checks
   - Supports environment-specific validation rules

3. **SecretsManager** (`config_system.py`)
   - Manages sensitive configuration data
   - Supports encryption and key rotation
   - Handles different secret types and providers

4. **Feature Flags** (`config_system.py`)
   - Comprehensive feature flag system
   - Supports rollout percentages and conditional logic
   - Environment-specific flag management

5. **CLI Tools** (`scripts/config_manager.py`)
   - Command-line interface for configuration management
   - Supports validation, backup/restore, and secret management

## Configuration Files

### Environment-Specific Configuration

The system supports four environments:

- **Development** (`config/config.development.yaml`)
- **Staging** (`config/config.staging.yaml`)
- **Production** (`config/config.production.yaml`)
- **Test** (`config/config.test.yaml`)

#### Configuration Structure

```yaml
# Application settings
app:
  name: "Trading Signals System"
  version: "2.0.1"
  environment: "development"
  debug: true

# Database configuration
database:
  url: "postgresql://localhost/trading_signals"
  pool_size: 10
  max_overflow: 20
  auto_create_tables: true

# Security settings
security:
  jwt_secret_key: "your-secret-key-min-32-characters"
  jwt_algorithm: "HS256"
  jwt_access_token_expire_minutes: 30
  require_https: false
  hsts_enabled: false
  hsts_max_age: 31536000

# API configuration
api:
  oanda_api_key: "your-oanda-api-key"
  oanda_account_id: "your-account-id"
  oanda_environment: "demo"
  gemini_api_key: "your-gemini-api-key"

# Server configuration
server:
  host: "127.0.0.1"
  port: 8000
  workers: 1
  timeout: 30
  max_requests: 1000

# CORS configuration
cors:
  origins: ["*"]
  allow_credentials: true
  allow_methods: ["*"]
  allow_headers: ["*"]

# Rate limiting
rate_limiting:
  requests_per_minute: 100
  window_seconds: 60

# Logging
logging:
  level: "INFO"
  file: null
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Monitoring
monitoring:
  enable_metrics: false
  enable_error_tracking: false
  enable_health_checks: true

# Railway deployment
railway:
  enable: false
  domain: null
```

### Feature Flags Configuration

Feature flags are stored in `config/feature_flags.yaml`:

```yaml
flags:
  new_ui:
    enabled: true
    description: "New user interface"
    environment: "development"
    rollout_percentage: 100
    conditions: {}
    created_at: "2024-01-01T00:00:00Z"
    modified_at: "2024-01-01T00:00:00Z"
    created_by: "system"
    tags: ["ui", "frontend"]

  beta_features:
    enabled: false
    description: "Beta features for testing"
    environment: "development"
    rollout_percentage: 10
    conditions:
      user_role: "beta_tester"
    tags: ["beta", "testing"]
```

## Usage

### Basic Configuration

```python
from config.config_system import ConfigurationManager

# Initialize configuration manager
config_manager = ConfigurationManager()

# Get configuration values
database_url = config_manager.get('database_url')
debug_mode = config_manager.get('debug', False)

# Set configuration values
config_manager.set('app_name', 'My Trading App')

# Validate configuration
validation_result = config_manager.validate_configuration()
```

### Feature Flags

```python
# Set feature flag
config_manager.set_feature_flag(
    'new_feature',
    enabled=True,
    description='New feature for testing',
    environment='development',
    rollout_percentage=50,
    tags=['beta']
)

# Check feature flag (simple)
if config_manager.get_feature_flag('new_feature'):
    # Feature is enabled
    pass

# Check feature flag with user context
user_attributes = {'user_role': 'premium', 'tier': 'gold'}
if config_manager.get_feature_flag('new_feature', user_id='user123', user_attributes=user_attributes):
    # Feature is enabled for this user
    pass

# List feature flags
flags = config_manager.list_feature_flags(environment='development')
```

### Secrets Management

```python
# Initialize secrets manager
config_manager.secrets_manager.initialize('your-encryption-key')

# Store secret
config_manager.secrets_manager.store_secret('api_key', 'secret-key')

# Retrieve secret
api_key = config_manager.secrets_manager.get_secret('api_key')

# Rotate secret
config_manager.secrets_manager.rotate_secret('api_key', 'new-secret-key')

# List secrets
secrets = config_manager.secrets_manager.list_secrets()
```

### Configuration Validation

```python
from config.startup_validator import validate_application_startup

# Validate configuration at startup
health_report = validate_application_startup(config_manager)

if health_report.can_start:
    print("Application can start")
else:
    print("Application cannot start due to configuration issues")
    for issue in health_report.validation_results:
        if issue.level == 'critical':
            print(f"CRITICAL: {issue.message}")
```

### Backup and Restore

```python
from pathlib import Path

# Backup configuration
backup_path = Path('./backup')
config_manager.backup_configuration(backup_path)

# Restore configuration
config_manager.restore_configuration(backup_path)
```

### Version Management

```python
# Create manual version
version = config_manager.create_config_version('Before deploying new feature')

# List versions
versions = config_manager.list_config_versions(limit=10)

# Rollback to version
success = config_manager.rollback_to_version('v5')
```

## CLI Usage

The configuration system includes a comprehensive CLI tool:

```bash
# Validate configuration
python scripts/config_manager.py validate

# List configuration values
python scripts/config_manager.py list

# Get specific configuration
python scripts/config_manager.py get database_url

# Set configuration value
python scripts/config_manager.py set app_name "My App"

# Backup configuration
python scripts/config_manager.py backup

# Restore configuration
python scripts/config_manager.py restore ./backup

# Feature flag operations
python scripts/config_manager.py feature-flag list
python scripts/config_manager.py feature-flag enable new_ui
python scripts/config_manager.py feature-flag disable beta_features

# Secrets management
python scripts/config_manager.py secrets store api_key
python scripts/config_manager.py secrets get api_key
python scripts/config_manager.py secrets rotate api_key
```

## Environment Variables

The system supports environment variable overrides:

```bash
# Override configuration
export DATABASE_URL="postgresql://localhost/mydb"
export JWT_SECRET_KEY="my-secret-key"
export OANDA_API_KEY="my-oanda-key"
export ENVIRONMENT="production"
```

## Hot-Reloading

The configuration system supports hot-reloading of configuration files:

```python
# Enable hot-reloading
config_manager.enable_hot_reload([
    "config/*.yaml",
    ".env"
])

# Configuration will automatically reload when files change
```

## Testing

The configuration system includes comprehensive tests:

```bash
# Run all tests
python -m pytest config/config_testing.py -v

# Run specific test
python -m pytest config/config_testing.py::TestConfigurationManager::test_initialization -v

# Run with coverage
python -m pytest config/config_testing.py --cov=config --cov-report=html
```

## Security Best Practices

### Secrets Management

1. **Never commit secrets to version control**
2. **Use environment variables for sensitive data**
3. **Enable encryption for stored secrets**
4. **Rotate secrets regularly**
5. **Use different secrets for different environments**

### Configuration Security

1. **Validate all configuration at startup**
2. **Use environment-specific configurations**
3. **Implement proper CORS settings**
4. **Enable HTTPS in production**
5. **Use proper logging levels**

### Feature Flag Security

1. **Implement proper rollout percentages**
2. **Use conditional logic for sensitive features**
3. **Audit feature flag changes**
4. **Clean up unused feature flags**

## Troubleshooting

### Common Issues

1. **Configuration not loading**
   - Check file permissions
   - Verify YAML syntax
   - Check environment variable names

2. **Validation errors**
   - Review error messages
   - Check required configurations
   - Verify data types and formats

3. **Feature flags not working**
   - Check environment settings
   - Verify rollout percentages
   - Review condition logic

4. **Secrets not accessible**
   - Verify encryption key
   - Check secret storage permissions
   - Review secret rotation logs

### Debug Mode

Enable debug mode for detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable debug logging for configuration system
config_manager.set('debug', True)
```

## Migration Guide

### From Basic Configuration

1. **Replace environment variables with YAML files**
2. **Add validation rules**
3. **Implement feature flags**
4. **Add secrets management**
5. **Enable hot-reloading**

### From Legacy System

1. **Use the migration script**
2. **Test validation rules**
3. **Backup existing configuration**
4. **Gradually enable new features**
5. **Monitor for issues**

## Performance Considerations

### Configuration Loading

- Configuration is cached in memory
- Hot-reloading uses file system watchers
- Secrets are encrypted/decrypted on access

### Memory Usage

- Configuration cache is optimized for size
- Feature flags use efficient data structures
- Secrets are stored encrypted when not in use

### Startup Time

- Configuration loads in parallel
- Validation is optimized for speed
- Hot-reloading doesn't impact startup performance

## Monitoring and Observability

### Metrics

The configuration system provides various metrics:

- Configuration validation time
- Feature flag evaluation count
- Secret access patterns
- Hot-reload events

### Logging

The system logs important events:

- Configuration changes
- Validation results
- Feature flag modifications
- Secret operations

### Health Checks

The system includes health checks for:

- Configuration validation
- Secret accessibility
- Feature flag consistency
- File system permissions

## Contributing

### Adding New Configuration

1. **Add validation rules** in `startup_validator.py`
2. **Update documentation** in this README
3. **Add tests** in `config_testing.py`
4. **Update CLI commands** if needed

### Adding New Features

1. **Follow the existing patterns**
2. **Add comprehensive tests**
3. **Update documentation**
4. **Consider backward compatibility**

## License

This configuration system is part of the Trading Signals System and is subject to the same license terms.

## Support

For issues and questions:

1. **Check the troubleshooting section**
2. **Review the test cases**
3. **Check the logs**
4. **Consult the validation results**