#!/usr/bin/env python
"""
Environment Variable Validation Script for Railway Deployment
This script validates that all required environment variables are properly set.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def validate_environment():
    """Validate all required environment variables"""
    print("Validating Railway Environment Variables...")
    print("=" * 60)

    required_vars = {
        # Security
        "JWT_SECRET_KEY": {
            "required": True,
            "description": "JWT secret key (min 32 characters)",
            "validation": lambda x: len(x) >= 32,
            "error_message": "JWT_SECRET_KEY must be at least 32 characters long"
        },

        # Database
        "DATABASE_URL": {
            "required": True,
            "description": "PostgreSQL database connection URL",
            "validation": lambda x: x.startswith('postgresql://'),
            "error_message": "DATABASE_URL must be a valid PostgreSQL connection string"
        },

        # OANDA API
        "OANDA_API_KEY": {
            "required": True,
            "description": "OANDA API access token",
            "validation": lambda x: len(x) > 10,
            "error_message": "OANDA_API_KEY must be a valid API token"
        },
        "OANDA_ACCOUNT_ID": {
            "required": True,
            "description": "OANDA account ID",
            "validation": lambda x: len(x) > 5 and x.isdigit(),
            "error_message": "OANDA_ACCOUNT_ID must be a valid account number"
        },
        "OANDA_ENVIRONMENT": {
            "required": True,
            "description": "OANDA environment (demo or live)",
            "validation": lambda x: x in ["demo", "live"],
            "error_message": "OANDA_ENVIRONMENT must be 'demo' or 'live'"
        },

        # AI Integration
        "GEMINI_API_KEY": {
            "required": True,
            "description": "Google Gemini AI API key",
            "validation": lambda x: len(x) > 10,
            "error_message": "GEMINI_API_KEY must be a valid API key"
        },

        # Email Configuration (Optional)
        "EMAIL_HOST": {
            "required": False,
            "description": "SMTP server host",
            "validation": lambda x: not x or '.' in x,
            "error_message": "EMAIL_HOST must be a valid SMTP server if provided"
        },
        "EMAIL_USER": {
            "required": False,
            "description": "SMTP username",
            "validation": lambda x: not x or '@' in x,
            "error_message": "EMAIL_USER must be a valid email address if provided"
        },
        "EMAIL_PASSWORD": {
            "required": False,
            "description": "SMTP password",
            "validation": lambda x: True,
            "error_message": ""
        },

        # Optional but recommended
        "REDIS_URL": {
            "required": False,
            "description": "Redis connection URL for caching",
            "validation": lambda x: True,
            "error_message": ""
        },

        # Application
        "PORT": {
            "required": True,
            "description": "Application port",
            "validation": lambda x: x.isdigit(),
            "error_message": "PORT must be a valid port number"
        }
    }

    errors = []
    warnings = []
    valid_vars = []

    for var_name, config in required_vars.items():
        value = os.getenv(var_name)

        if config["required"] and not value:
            errors.append(f"[ERROR] {var_name}: {config['description']} - MISSING")
        elif value:
            try:
                if config["validation"](value):
                    valid_vars.append(f"[OK] {var_name}: {config['description']}")
                else:
                    errors.append(f"[ERROR] {var_name}: {config['error_message']}")
            except Exception as e:
                errors.append(f"[ERROR] {var_name}: Validation failed - {str(e)}")
        elif not config["required"]:
            warnings.append(f"[WARN] {var_name}: {config['description']} - Optional but recommended")

    # Print results
    print("\n[OK] VALID VARIABLES:")
    for var in valid_vars:
        print(f"  {var}")

    print("\n[WARN] WARNINGS:")
    for warning in warnings:
        print(f"  {warning}")

    print("\n[ERROR] ERRORS:")
    for error in errors:
        print(f"  {error}")

    print("\n" + "=" * 60)

    if errors:
        print(f"[ERROR] VALIDATION FAILED: {len(errors)} errors found")
        print("\n[INFO] TO FIX THESE ERRORS:")
        print("1. Go to your Railway project dashboard")
        print("2. Navigate to Variables tab")
        print("3. Add the missing environment variables with proper values")
        print("4. Redeploy your application")
        return False
    else:
        print(f"[OK] VALIDATION PASSED: {len(valid_vars)} variables configured")
        if warnings:
            print(f"[WARN] {len(warnings)} optional variables not set")
        return True

def show_env_template():
    """Show environment variable template for Railway"""
    print("\n[INFO] RAILWAY ENVIRONMENT VARIABLES TEMPLATE:")
    print("=" * 60)

    template = {
        "JWT_SECRET_KEY": "your-super-secret-jwt-key-min-32-characters-long",
        "DATABASE_URL": "postgresql://user:password@host:port/database",
        "OANDA_API_KEY": "your-oanda-api-token-here",
        "OANDA_ACCOUNT_ID": "your-oanda-account-id",
        "OANDA_ENVIRONMENT": "demo",
        "GEMINI_API_KEY": "your-gemini-api-key-here",
        "EMAIL_HOST": "smtp.gmail.com (optional)",
        "EMAIL_USER": "your-email@gmail.com (optional)",
        "EMAIL_PASSWORD": "your-app-password-here (optional)",
        "REDIS_URL": "redis://localhost:6379",
        "PORT": "8000"
    }

    for key, value in template.items():
        print(f"{key}={value}")

if __name__ == "__main__":
    success = validate_environment()

    if not success:
        show_env_template()
        print("\n[INFO] TIP: Copy this template and replace with your actual values in Railway Variables")
        sys.exit(1)
    else:
        print("\n[SUCCESS] All environment variables are properly configured!")
        print("[INFO] Your application is ready for Railway deployment!")
        sys.exit(0)