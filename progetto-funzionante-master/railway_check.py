#!/usr/bin/env python
"""
Railway Build-time Environment Check
This script validates environment variables during Railway build process.
"""

import os
import sys
from dotenv import load_dotenv

def check_railway_environment():
    """Check if Railway environment is properly configured"""
    print("Railway Environment Check")
    print("=" * 40)

    required_vars = [
        "JWT_SECRET_KEY",
        "DATABASE_URL",
        "OANDA_API_KEY",
        "OANDA_ACCOUNT_ID",
        "OANDA_ENVIRONMENT",
        "GEMINI_API_KEY"
    ]

    missing_vars = []

    for var in required_vars:
        value = os.getenv(var)
        if not value or value in ["", "your-api-key", "your-secret-key"]:
            missing_vars.append(var)

    if missing_vars:
        print("ERROR: Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nPlease configure these variables in Railway Variables tab.")
        print("See RAILWAY_DEPLOYMENT.md for instructions.")
        return False

    # Validate JWT secret key length
    jwt_key = os.getenv("JWT_SECRET_KEY")
    if len(jwt_key) < 32:
        print(f"ERROR: JWT_SECRET_KEY must be at least 32 characters (current: {len(jwt_key)})")
        return False

    # Validate OANDA environment
    oanda_env = os.getenv("OANDA_ENVIRONMENT")
    if oanda_env not in ["demo", "live"]:
        print(f"ERROR: OANDA_ENVIRONMENT must be 'demo' or 'live' (current: {oanda_env})")
        return False

    # Validate database URL format
    db_url = os.getenv("DATABASE_URL")
    if not db_url.startswith("postgresql://"):
        print(f"ERROR: DATABASE_URL must start with 'postgresql://' (current: {db_url[:20]}...)")
        return False

    print("SUCCESS: All required environment variables are configured!")
    return True

if __name__ == "__main__":
    load_dotenv()

    if not check_railway_environment():
        sys.exit(1)
    else:
        sys.exit(0)