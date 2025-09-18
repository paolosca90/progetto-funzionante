# Configuration Management Guide

## Overview

This guide documents the unified configuration system for the FastAPI trading signals platform. The system uses environment-based configuration with Pydantic validation, ensuring security, flexibility, and production-readiness.

## Architecture

### Configuration Structure

```
config/
├── settings.py          # Main configuration classes
├── config_manager.py    # Configuration management utilities
└── __init__.py

Environment Files:
├── .env.example         # Example configuration
├── .env.development     # Development environment
├── .env.staging        # Staging environment
├── .env.production      # Production environment
└── .env.test          # Testing environment
```

### Key Features

- **Environment-Specific Configurations**: Separate settings for dev, staging, prod, test
- **Type Safety**: Pydantic validation with automatic type conversion
- **Secrets Management**: Secure handling of sensitive configuration
- **Validation**: Runtime configuration validation with startup checks
- **Backward Compatibility**: Legacy configuration support
- **Configuration Management**: Tools for migration, backup, and deployment

## Configuration Classes

### Main Settings Classes

#### `Settings` (Base Class)
```python
class Settings(BaseSettings):
    # Application info
    project_name: str
    version: str
    environment: Environment

    # Sub-configurations
    security: SecuritySettings
    database: DatabaseSettings
    cache: CacheSettings
    email: EmailSettings
    oanda: OANDASettings
    ai: AISettings
    api: APISettings
    server: ServerSettings
    monitoring: MonitoringSettings
    trading: TradingSettings
    features: FeatureFlags
```

#### Environment-Specific Classes

- `DevelopmentSettings`: Optimized for local development
- `StagingSettings`: Pre-production testing
- `ProductionSettings`: Optimized for production deployment
- `TestSettings`: Optimized for automated testing

## Environment Variables

### Required Variables

All environments require these core variables:

```bash
# Application
ENVIRONMENT=development|staging|production|testing

# Security
SECURITY_JWT_SECRET_KEY=your-super-secret-jwt-key-min-32-chars

# Database
DATABASE_URL=postgresql://user:pass@host:port/database

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_FROM=your-email@gmail.com

# OANDA API
OANDA_API_KEY=your-oanda-api-key
OANDA_ACCOUNT_ID=your-oanda-account-id
OANDA_ENVIRONMENT=demo|live

# AI/ML
GEMINI_API_KEY=your-gemini-api-key

# Cache
REDIS_URL=redis://localhost:6379
```

### Optional Variables

These can be customized per environment:

```bash
# Server Configuration
HOST=0.0.0.0
PORT=8000
MAX_WORKERS=4
TIMEOUT=30

# Cache Configuration
CACHE_TTL_SHORT=300
CACHE_TTL_MEDIUM=1800
CACHE_TTL_LONG=3600
CACHE_WARMING_ENABLED=true

# API Configuration
CORS_ORIGINS=["*"]
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Feature Flags
ENABLE_AI_ANALYSIS=true
ENABLE_SIGNAL_GENERATION=true
ENABLE_EMAIL_NOTIFICATIONS=true
```

## Environment Setup

### Development Environment

```bash
# Copy and configure development environment
cp .env.example .env.development

# Edit .env.development with your settings
ENVIRONMENT=development
DEBUG=true
SECURITY_JWT_SECRET_KEY=dev-secret-key-change-in-production
DATABASE_URL=postgresql://dev_user:dev_pass@localhost:5432/trading_dev
# ... other development settings
```

### Production Environment

```bash
# Copy production configuration
cp .env.example .env.production

# Set environment-specific values
ENVIRONMENT=production
DEBUG=false
SECURITY_JWT_SECRET_KEY=${RAILWAY_ENV_JWT_SECRET_KEY}
DATABASE_URL=${RAILWAY_ENV_DATABASE_URL}
REDIS_URL=${RAILWAY_ENV_REDIS_URL}
# ... use Railway secrets for sensitive values
```

### Railway Deployment

Railway automatically injects environment variables:

1. **Database**: `DATABASE_URL` provided by Railway PostgreSQL service
2. **Redis**: `REDIS_URL` provided by Railway Redis service
3. **Secrets**: Add via Railway dashboard or CLI

```bash
# Add secrets via Railway CLI
railway variables set JWT_SECRET_KEY=your-production-secret
railway variables set OANDA_API_KEY=your-production-oanda-key
railway variables set GEMINI_API_KEY=your-production-gemini-key
```

## Configuration Validation

### Startup Validation

The application validates configuration at startup:

```python
# Configuration is validated automatically
validation_result = settings.validate_configuration()
if not validation_result["valid"] and settings.is_production:
    raise RuntimeError("Configuration validation failed")
```

### Validation Checks

- **Security**: JWT secret key length and default values
- **Required Variables**: All required environment variables present
- **Environment-Specific**: Production-specific security checks
- **Format Validation**: Database URLs, email ports, etc.

### Validation Endpoints

```bash
# Check configuration health
GET /config/validate

# Get safe configuration info
GET /config/info
```

## Configuration Management

### Using the Configuration Manager

```python
from config.config_manager import config_manager

# Validate environment file
validation = config_manager.validate_environment_file('.env.production')

# Create environment file
config_manager.create_environment_file('production', '.env.local')

# Backup configuration
backup_path = config_manager.backup_configuration()

# Compare environments
comparison = config_manager.compare_environments('staging', 'production')

# Get configuration summary
summary = config_manager.get_configuration_summary()
```

### Migration from Old Configuration

```python
# Migrate old .env to new format
success = config_manager.migrate_old_config('.env', '.env.new')

# The system automatically maps old variables to new ones:
# JWT_SECRET_KEY → SECURITY_JWT_SECRET_KEY
# CACHE_TTL → CACHE_TTL_SHORT
# REDIS_POOL_SIZE → REDIS_MAX_CONNECTIONS
```

## Security Best Practices

### Secrets Management

1. **Never commit secrets to version control**
2. **Use environment variables or secret management services**
3. **Rotate secrets regularly**
4. **Use Railway's built-in secret management**

### Environment Security

```bash
# Production security requirements
SECURITY_JWT_SECRET_KEY=at-least-32-characters-long
DEBUG=false
ENVIRONMENT=production
ENABLE_PROFILING=false
```

### API Security

```python
# CORS is automatically configured per environment
- Development: ["*"] (permissive)
- Staging: ["https://staging.*", "https://*.railway.app"]
- Production: ["https://yourdomain.com"]
```

## Feature Flags

The system includes comprehensive feature flags:

```python
# Feature flags configuration
settings.features.enable_ai_analysis = True
settings.features.enable_signal_generation = True
settings.features.enable_email_notifications = False  # Disabled in development
settings.features.enable_performance_monitoring = True
```

## Performance Configuration

### Database Connection Pooling

```python
# Environment-specific database settings
settings.database.database_pool_size = 20  # Production
settings.database.database_max_overflow = 10
settings.database.database_pool_timeout = 30
```

### Cache Configuration

```python
# Cache settings optimized per environment
settings.cache.cache_ttl_short = 300      # 5 minutes
settings.cache.cache_ttl_medium = 1800    # 30 minutes
settings.cache.cache_ttl_long = 3600      # 1 hour
```

### Rate Limiting

```python
# API rate limiting
settings.api.rate_limit_requests = 100    # requests per window
settings.api.rate_limit_window = 60       # seconds
```

## Testing Configuration

### Test Environment Setup

```python
# .env.test configuration
ENVIRONMENT=testing
DEBUG=true
DATABASE_URL=sqlite:///./test.db
REDIS_URL=redis://localhost:6379/1

# Feature flags for testing
settings.features.enable_ai_analysis = False
settings.features.enable_signal_generation = False
settings.features.enable_email_notifications = False
```

### Configuration Testing

```python
# Test configuration validation
def test_configuration_validation():
    validation = settings.validate_configuration()
    assert validation["valid"]

# Test environment-specific settings
def test_production_settings():
    prod_settings = ProductionSettings()
    assert prod_settings.server.debug is False
    assert prod_settings.monitoring.log_level == "WARNING"
```

## Deployment Configuration

### Railway Deployment

1. **Environment Variables**: Set via Railway dashboard
2. **Service Configuration**: Use provided Railway vars
3. **Secrets Management**: Use Railway's secret storage

### Docker Deployment

```dockerfile
# Dockerfile with environment configuration
ENV ENVIRONMENT=production
ENV HOST=0.0.0.0
ENV PORT=8000
```

### Kubernetes Deployment

```yaml
# Kubernetes configuration
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  ENVIRONMENT: "production"
  MAX_WORKERS: "8"
  CACHE_TTL_SHORT: "300"
```

## Troubleshooting

### Common Issues

1. **Configuration validation fails**
   - Check required environment variables
   - Verify JWT secret key length
   - Ensure database URL format is correct

2. **Database connection issues**
   - Verify DATABASE_URL format
   - Check database service status
   - Validate network connectivity

3. **Cache connection issues**
   - Verify REDIS_URL format
   - Check Redis service status
   - Validate Redis authentication

### Debug Commands

```bash
# Validate configuration
curl http://localhost:8000/config/validate

# Check configuration info
curl http://localhost:8000/config/info

# Test environment file
python -c "from config.config_manager import config_manager; print(config_manager.validate_environment_file('.env'))"
```

## Migration Guide

### From Legacy Configuration

1. **Backup current configuration**
2. **Use migration utility**
3. **Update environment files**
4. **Test new configuration**

### Migration Steps

```bash
# 1. Backup current .env file
cp .env .env.backup

# 2. Use configuration manager to migrate
python -c "
from config.config_manager import config_manager
config_manager.migrate_old_config('.env.backup', '.env.new')
"

# 3. Review and update .env.new
# 4. Rename to .env
mv .env.new .env
```

## Best Practices

### Development

- Use `.env.development` for local development
- Keep secrets out of version control
- Test configuration changes in staging first
- Use feature flags for new functionality

### Production

- Always validate configuration before deployment
- Use secrets management for sensitive data
- Monitor configuration-related errors
- Regularly rotate secrets and API keys

### Testing

- Test configuration validation
- Test environment-specific settings
- Mock external services in tests
- Use test-specific configuration

## Support

For configuration-related issues:

1. Check configuration validation endpoints
2. Review environment files for missing variables
3. Consult this documentation
4. Check logs for configuration errors

---

*This configuration system ensures your trading signals platform is secure, scalable, and production-ready across all environments.*