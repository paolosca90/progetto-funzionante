#!/usr/bin/env python3
"""
API Configuration Validation Script
"""

import os
import sys
from pathlib import Path

def load_env_file():
    """Load environment variables from .env file"""
    env_path = Path(".env")
    env_vars = {}

    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    env_vars[key] = value

    return env_vars

def validate_configuration():
    """Validate the API configuration"""
    print("Validating API Configuration")
    print("=" * 40)

    env_vars = load_env_file()

    required_vars = {
        'OANDA_API_KEY': r'^[a-f0-9-]+$',
        'OANDA_ACCOUNT_ID': r'^\d{3}-\d{3}-\d{8}-\d{3}$',
        'OANDA_ENVIRONMENT': r'^(demo|live|practice)$',
        'GEMINI_API_KEY': r'^AIza[0-9A-Za-z\-_]{35}$'
    }

    all_valid = True

    for var, pattern in required_vars.items():
        value = env_vars.get(var, '')

        if not value:
            print(f"MISSING: {var}")
            all_valid = False
        elif var == 'OANDA_API_KEY' and value == 'test_key':
            print(f"TEST VALUE: {var}")
            all_valid = False
        elif var == 'GEMINI_API_KEY' and value == 'test_gemini_key':
            print(f"TEST VALUE: {var}")
            all_valid = False
        else:
            import re
            if re.match(pattern, value):
                print(f"VALID: {var}")
            else:
                print(f"INVALID FORMAT: {var}")
                all_valid = False

    print("\n" + "=" * 40)
    if all_valid:
        print("SUCCESS: All API credentials are properly configured!")
        print("Ready for production deployment")
    else:
        print("WARNING: Some issues found. Please fix the invalid credentials.")
        print("Run 'python setup_api_credentials.py' to reconfigure")

    return all_valid

if __name__ == "__main__":
    validate_configuration()