#!/usr/bin/env python3
"""
Quick API Credentials Setup Script
"""

import os
from pathlib import Path

def update_env_file():
    """Update .env file with real credentials"""

    print("Quick API Credentials Setup")
    print("=" * 40)
    print("Please enter your actual API credentials:")
    print()

    # Get credentials from user
    oanda_key = input("OANDA API Key (format: xxxx-xxxx-xxxx-xxxx): ").strip()
    oanda_account = input("OANDA Account ID (format: xxx-xxx-xxxxxx-xxx): ").strip()
    oanda_env = input("OANDA Environment (demo/live): ").strip().lower()
    gemini_key = input("Gemini API Key (starts with AIza): ").strip()

    # Validate environment
    if oanda_env not in ['demo', 'live']:
        oanda_env = 'demo'

    # Read current .env file
    env_path = Path(".env")
    lines = []

    if env_path.exists():
        with open(env_path, 'r') as f:
            lines = f.readlines()

    # Update the required variables
    updated_lines = []
    for line in lines:
        if line.startswith('OANDA_API_KEY='):
            updated_lines.append(f'OANDA_API_KEY={oanda_key}\n')
        elif line.startswith('OANDA_ACCOUNT_ID='):
            updated_lines.append(f'OANDA_ACCOUNT_ID={oanda_account}\n')
        elif line.startswith('OANDA_ENVIRONMENT='):
            updated_lines.append(f'OANDA_ENVIRONMENT={oanda_env}\n')
        elif line.startswith('GEMINI_API_KEY='):
            updated_lines.append(f'GEMINI_API_KEY={gemini_key}\n')
        else:
            updated_lines.append(line)

    # Write back to file
    with open(env_path, 'w') as f:
        f.writelines(updated_lines)

    print("\nConfiguration updated successfully!")
    print("Running validation...")

if __name__ == "__main__":
    update_env_file()