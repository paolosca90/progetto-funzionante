# Railway Deployment Guide

This guide provides comprehensive instructions for deploying the AI Trading System to Railway with proper configuration and troubleshooting steps.

## Overview

The AI Trading System has been optimized for Railway deployment with the following key improvements:

- **Flattened project structure** - No nested subdirectories
- **Complete dependency management** - All required packages in requirements.txt
- **Fixed import structure** - Proper module imports and path resolution
- **Configuration management** - Environment-based configuration system
- **Health checks** - Railway-compatible health endpoints

## Project Structure

```
progetto-funzionante-master/
├── main.py                 # Railway entry point
├── requirements.txt        # Complete dependency list
├── nixpacks.toml          # Build configuration
├── railway.json           # Railway deployment settings
├── .env                   # Environment variables (development)
├── frontend/              # Main application code
│   ├── main.py           # FastAPI application
│   ├── config/           # Configuration system
│   ├── app/              # Application modules
│   ├── static/           # Static files
│   └── templates/        # HTML templates
└── CLAUDE.md             # Project documentation
```

## Railway Configuration Files

### nixpacks.toml

```toml
[phases.setup]
aptPkgs = ['python3-dev', 'build-essential', 'python3-setuptools', 'gcc', 'g++']

[phases.install]
cmds = [
  'python -m venv /opt/venv',
  '/opt/venv/bin/python -m pip install --upgrade pip',
  '/opt/venv/bin/python -m pip install --upgrade setuptools wheel',
  '/opt/venv/bin/python -m pip install -r requirements.txt'
]

[start]
cmd = '/opt/venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port $PORT'
```

### railway.json

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "nixpacks",
    "buildCommand": "python -m pip install -r requirements.txt"
  },
  "deploy": {
    "startCommand": "python -m uvicorn main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 300,
    "restartPolicyType": "ON_FAILURE",
    "sleepApplication": true
  },
  "environments": {
    "production": {
      "variables": {
        "SECRET_KEY": "$SECRET_KEY",
        "DATABASE_URL": "$DATABASE_URL",
        "PORT": "$PORT",
        "OANDA_API_KEY": "$OANDA_API_KEY",
        "OANDA_ACCOUNT_ID": "$OANDA_ACCOUNT_ID",
        "OANDA_ENVIRONMENT": "$OANDA_ENVIRONMENT",
        "GEMINI_API_KEY": "$GEMINI_API_KEY",
        "JWT_SECRET_KEY": "$JWT_SECRET_KEY",
        "EMAIL_HOST": "$EMAIL_HOST",
        "EMAIL_USER": "$EMAIL_USER",
        "EMAIL_PASSWORD": "$EMAIL_PASSWORD",
        "PYTHONPATH": "/app",
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

## Required Environment Variables

### Critical (Must be set for deployment)

```bash
# Database Configuration
DATABASE_URL=postgresql://user:password@host:port/database

# Security Configuration
JWT_SECRET_KEY=your_super_secret_jwt_key_here

# OANDA API Configuration
OANDA_API_KEY=your_oanda_api_key
OANDA_ACCOUNT_ID=your_oanda_account_id
OANDA_ENVIRONMENT=demo  # or 'live'

# AI Integration
GEMINI_API_KEY=your_google_gemini_api_key
```

### Optional (Have defaults)

```bash
# Application Configuration
ENVIRONMENT=production
DEBUG=false
HOST=0.0.0.0
PORT=8000
WORKERS=1

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
```

## Deployment Steps

### 1. Prepare Your Repository

Ensure your repository has the correct structure:

```bash
# Verify required files exist
ls -la
# Should show: main.py, requirements.txt, nixpacks.toml, railway.json, frontend/
```

### 2. Connect to Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize Railway project
railway init
```

### 3. Configure Environment Variables

```bash
# Add required variables
railway variables add DATABASE_URL "your_database_url"
railway variables add JWT_SECRET_KEY "your_jwt_secret"
railway variables add OANDA_API_KEY "your_oanda_key"
railway variables add OANDA_ACCOUNT_ID "your_oanda_account"
railway variables add GEMINI_API_KEY "your_gemini_key"

# Add optional variables
railway variables add ENVIRONMENT "production"
railway variables add DEBUG "false"
```

### 4. Deploy

```bash
# Deploy to Railway
railway up

# Monitor deployment status
railway logs
```

### 5. Verify Deployment

```bash
# Check health endpoint
curl https://your-app-name.railway.app/health

# Should return:
{
  "status": "healthy",
  "message": "AI Trading System is running",
  "version": "2.0.0"
}
```

## Troubleshooting

### Common Issues and Solutions

#### 1. "Nixpacks was unable to generate a build plan"

**Problem**: Railway cannot understand how to build your application.

**Solution**:
- Verify `nixpacks.toml` exists in the root directory
- Check `requirements.txt` is properly formatted
- Ensure `main.py` exists and imports correctly

#### 2. Import Errors

**Problem**: Application fails to start due to missing imports.

**Solution**:
- Check all dependencies are in `requirements.txt`
- Verify import paths are correct
- Test locally with: `python -c "import main; print('Import successful')"`

#### 3. Database Connection Issues

**Problem**: Application cannot connect to PostgreSQL.

**Solution**:
- Verify `DATABASE_URL` format is correct
- Check Railway PostgreSQL service is running
- Test connection locally with provided URL

#### 4. Missing Environment Variables

**Problem**: Application crashes due to missing configuration.

**Solution**:
- Set all required environment variables in Railway dashboard
- Verify variable names match exactly
- Check for typos in variable names

### Health Check Endpoints

The application provides several health check endpoints:

- `/health` - Basic health check
- `/api/health` - Detailed health information
- `/api/health/database` - Database connectivity check
- `/api/health/oanda` - OANDA API connectivity check

### Monitoring and Logs

```bash
# View real-time logs
railway logs

# View build logs
railway build logs

# Check application status
railway status
```

## Local Testing

Before deploying to Railway, test locally:

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set environment variables
cp .env.example .env
# Edit .env with your values

# 3. Test import
python -c "import main; print('Import successful')"

# 4. Run application
uvicorn main:app --host 0.0.0.0 --port 8000

# 5. Test health endpoint
curl http://localhost:8000/health
```

## Performance Optimization

The deployment includes several performance optimizations:

- **Static file serving** - Efficient handling of static assets
- **Database connection pooling** - Optimized database connections
- **Caching system** - Redis integration for performance
- **Async operations** - Non-blocking I/O operations
- **Health monitoring** - Continuous health checks

## Security Considerations

- **Environment variables** - All secrets stored securely
- **CORS configuration** - Proper cross-origin resource sharing
- **JWT authentication** - Secure token-based authentication
- **Input validation** - Comprehensive input sanitization
- **Rate limiting** - Protection against abuse

## Backup and Recovery

- **Database backups** - Automatic Railway PostgreSQL backups
- **Configuration backup** - Export environment variables regularly
- **Code versioning** - Use Git for version control
- **Monitoring** - Set up alerts for application health

## Support

For deployment issues:

1. Check Railway documentation: https://docs.railway.app/
2. Review this guide for troubleshooting steps
3. Check application logs for specific error messages
4. Verify all environment variables are correctly set

## Next Steps

After successful deployment:

1. Set up monitoring and alerts
2. Configure custom domain
3. Set up SSL/TLS certificates
4. Implement automated backups
5. Set up staging environment for testing

---

**Note**: This deployment has been tested and optimized for Railway's platform. All dependencies and configurations have been verified to work correctly.