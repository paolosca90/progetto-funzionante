# Railway Deployment Guide

## Required Environment Variables

To fix the deployment issue, you need to configure the following environment variables in your Railway project dashboard:

### Security Variables
- **JWT_SECRET_KEY**: A secure JWT secret key (minimum 32 characters)
  - Generate one with: `openssl rand -hex 32`

### Database Variables
- **DATABASE_URL**: PostgreSQL connection URL (Railway provides this automatically when you add a PostgreSQL service)
  - Format: `postgresql://user:password@host:port/database`

### OANDA API Variables
- **OANDA_API_KEY**: Your OANDA API access token
  - Get from: https://www.oanda.com/demo-account/tpa/personal_token
- **OANDA_ACCOUNT_ID**: Your OANDA account ID
- **OANDA_ENVIRONMENT**: `demo` or `live`

### AI Integration Variables
- **GEMINI_API_KEY**: Google Gemini AI API key
  - Get from: https://makersuite.google.com/app/apikey

### Email Configuration Variables
- **EMAIL_HOST**: SMTP server (e.g., `smtp.gmail.com`)
- **EMAIL_USER**: Your email address
- **EMAIL_PASSWORD**: Your email password or app password
- **EMAIL_FROM**: Sender email address (usually same as EMAIL_USER)

### Optional Variables
- **REDIS_URL**: Redis connection URL for caching
- **PORT**: Application port (Railway provides this automatically)

## Step-by-Step Setup

### 1. Configure Railway Variables

1. Go to your Railway project dashboard
2. Navigate to the **Variables** tab
3. Add the following variables:

```bash
# Security
JWT_SECRET_KEY=your-generated-jwt-secret-key-min-32-chars

# Database (Railway provides this automatically when you add PostgreSQL)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# OANDA API
OANDA_API_KEY=your-oanda-api-token
OANDA_ACCOUNT_ID=your-oanda-account-id
OANDA_ENVIRONMENT=demo

# AI Integration
GEMINI_API_KEY=your-gemini-api-key

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_FROM=your-email@gmail.com

# Optional
REDIS_URL=redis://localhost:6379
PORT=${{PORT}}
```

### 2. Add PostgreSQL Service

1. In your Railway project, click **+ Add Service**
2. Select **PostgreSQL**
3. Railway will automatically provide the `DATABASE_URL` variable

### 3. Add Redis Service (Optional)

1. In your Railway project, click **+ Add Service**
2. Select **Redis**
3. Railway will automatically provide the `REDIS_URL` variable

### 4. Redeploy Application

1. After configuring all variables, click **Deploy**
2. Monitor the deployment logs for any errors

## Common Issues and Solutions

### JWT Secret Key Missing
**Error**: `pydantic_core._pydantic_core.ValidationError: 1 validation error for SecuritySettings jwt_secret_key Field required`

**Solution**: Add a JWT_SECRET_KEY variable with at least 32 characters:
```bash
JWT_SECRET_KEY=your-super-secure-jwt-secret-key-here-min-32-chars
```

### Database Connection Failed
**Error**: Database connection errors

**Solution**:
1. Ensure PostgreSQL service is added
2. Verify DATABASE_URL is properly set
3. Check if database is accepting connections

### OANDA API Authentication Failed
**Error**: OANDA API authentication errors

**Solution**:
1. Verify OANDA_API_KEY is correct
2. Check OANDA_ACCOUNT_ID is valid
3. Ensure OANDA_ENVIRONMENT matches your account type

## Testing Your Deployment

After deployment, you can test your application by:

1. **Health Check**: Visit `/health` endpoint
2. **API Test**: Visit `/api/signals/latest` for latest signals
3. **Web Interface**: Access the main dashboard

## Validation Script

Run the included validation script to check your environment variables:

```bash
python validate_env.py
```

This will show you which variables are missing or incorrectly configured.

## Production Considerations

1. **Security**: Use strong, randomly generated secrets
2. **Environment**: Set OANDA_ENVIRONMENT to "live" for production
3. **Monitoring**: Enable application monitoring and logging
4. **Backups**: Ensure database backups are configured
5. **SSL**: Railway provides automatic SSL certificates

## Support

If you encounter any issues during deployment:

1. Check Railway deployment logs
2. Run the validation script locally
3. Verify all environment variables are set correctly
4. Ensure all required services are added to your Railway project