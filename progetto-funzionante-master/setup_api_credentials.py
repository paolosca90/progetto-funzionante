#!/usr/bin/env python3
"""
Automated API Credentials Setup Script
This script helps configure the required API credentials for the AI Trading System.
"""

import os
import sys
from pathlib import Path
import re
from datetime import datetime

def load_env_file():
    """Load current .env file contents"""
    env_path = Path(".env")
    if env_path.exists():
        with open(env_path, 'r') as f:
            lines = f.readlines()
    else:
        lines = []
    return lines

def save_env_file(lines):
    """Save updated .env file"""
    env_path = Path(".env")
    with open(env_path, 'w') as f:
        f.writelines(lines)

def get_user_input(prompt, validation_pattern=None, help_text=None):
    """Get validated user input"""
    while True:
        if help_text:
            print(f"\n💡 {help_text}")

        user_input = input(prompt).strip()

        if not user_input:
            print("❌ This field is required. Please provide a value.")
            continue

        if validation_pattern:
            if not re.match(validation_pattern, user_input):
                print(f"❌ Invalid format. Expected format: {validation_pattern}")
                continue

        return user_input

def update_env_value(lines, key, value):
    """Update or add an environment variable"""
    pattern = f"^{key}=.*"
    updated = False

    for i, line in enumerate(lines):
        if re.match(pattern, line.strip()):
            lines[i] = f"{key}={value}\n"
            updated = True
            break

    if not updated:
        lines.append(f"{key}={value}\n")

    return lines

def validate_oanda_credentials():
    """Validate OANDA API credentials format"""
    print("\n🔑 OANDA API Configuration")
    print("=" * 50)

    api_key = get_user_input(
        "Enter your OANDA API Key: ",
        r'^[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}$',
        "Your OANDA API key should be in format: xxxx-xxxx-xxxx-xxxx"
    )

    account_id = get_user_input(
        "Enter your OANDA Account ID: ",
        r'^\d{3}-\d{3}-\d{6}-\d{3}$',
        "Your OANDA Account ID should be in format: xxx-xxx-xxxxxx-xxx"
    )

    environment = get_user_input(
        "Enter environment (demo/live): ",
        r'^(demo|live)$',
        "Use 'demo' for testing, 'live' for real trading"
    ).lower()

    return api_key, account_id, environment

def validate_gemini_credentials():
    """Validate Gemini API credentials format"""
    print("\n🤖 Google Gemini API Configuration")
    print("=" * 50)

    api_key = get_user_input(
        "Enter your Gemini API Key: ",
        r'^AIza[0-9A-Za-z\-_]{35}$',
        "Your Gemini API key should start with 'AIza' and be 39 characters long"
    )

    return api_key

def backup_existing_config():
    """Create a backup of the current .env file"""
    env_path = Path(".env")
    if env_path.exists():
        backup_path = Path(f".env.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        env_path.rename(backup_path)
        print(f"✅ Backup created: {backup_path}")

def create_validation_script():
    """Create a validation script to test the configuration"""
    script_content = '''#!/usr/bin/env python3
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
    print("🔍 Validating API Configuration")
    print("=" * 40)

    env_vars = load_env_file()

    required_vars = {
        'OANDA_API_KEY': r'^[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}$',
        'OANDA_ACCOUNT_ID': r'^\\d{3}-\\d{3}-\\d{6}-\\d{3}$',
        'OANDA_ENVIRONMENT': r'^(demo|live)$',
        'GEMINI_API_KEY': r'^AIza[0-9A-Za-z\\-_]{35}$'
    }

    all_valid = True

    for var, pattern in required_vars.items():
        value = env_vars.get(var, '')

        if not value:
            print(f"❌ {var}: Missing")
            all_valid = False
        elif var == 'OANDA_API_KEY' and value == 'test_key':
            print(f"❌ {var}: Using test value")
            all_valid = False
        elif var == 'GEMINI_API_KEY' and value == 'test_gemini_key':
            print(f"❌ {var}: Using test value")
            all_valid = False
        else:
            import re
            if re.match(pattern, value):
                print(f"✅ {var}: Valid")
            else:
                print(f"❌ {var}: Invalid format")
                all_valid = False

    print("\\n" + "=" * 40)
    if all_valid:
        print("🎉 All API credentials are properly configured!")
        print("✅ Ready for production deployment")
    else:
        print("⚠️  Some issues found. Please fix the invalid credentials.")
        print("📝 Run 'python setup_api_credentials.py' to reconfigure")

    return all_valid

if __name__ == "__main__":
    validate_configuration()
'''

    with open("validate_api_setup.py", "w") as f:
        f.write(script_content)

    # Make it executable
    if os.name != 'nt':  # Unix-like systems
        os.chmod("validate_api_setup.py", 0o755)

def main():
    """Main setup function"""
    print("🚀 AI Trading System - API Credentials Setup")
    print("=" * 50)
    print("This script will help you configure the required API credentials.")
    print("All current values will be backed up automatically.")
    print()

    try:
        # Load current configuration
        env_lines = load_env_file()

        # Show current status
        print("📊 Current Configuration Status:")
        for line in env_lines:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                if key in ['OANDA_API_KEY', 'OANDA_ACCOUNT_ID', 'OANDA_ENVIRONMENT', 'GEMINI_API_KEY']:
                    if value in ['test_key', 'test_account', 'test_gemini_key']:
                        print(f"❌ {key}: Using test value")
                    else:
                        print(f"✅ {key}: Configured")

        print()

        # Get new credentials
        oanda_key, oanda_account, oanda_env = validate_oanda_credentials()
        gemini_key = validate_gemini_credentials()

        # Confirm changes
        print("\n📋 Configuration Summary:")
        print(f"OANDA API Key: {oanda_key[:8]}...{oanda_key[-4:]}")
        print(f"OANDA Account ID: {oanda_account}")
        print(f"OANDA Environment: {oanda_env}")
        print(f"Gemini API Key: {gemini_key[:8]}...{gemini_key[-4:]}")

        confirm = input("\n✅ Proceed with these changes? (y/N): ").lower().strip()

        if confirm == 'y':
            # Backup existing configuration
            backup_existing_config()

            # Update environment file
            env_lines = update_env_value(env_lines, 'OANDA_API_KEY', oanda_key)
            env_lines = update_env_value(env_lines, 'OANDA_ACCOUNT_ID', oanda_account)
            env_lines = update_env_value(env_lines, 'OANDA_ENVIRONMENT', oanda_env)
            env_lines = update_env_value(env_lines, 'GEMINI_API_KEY', gemini_key)

            # Save changes
            save_env_file(env_lines)

            # Create validation script
            create_validation_script()

            print("\n✅ Configuration updated successfully!")
            print("📁 Backup saved to .env.backup.*")
            print("🧪 Run 'python validate_api_setup.py' to validate your configuration")

            # Offer to run validation
            run_validation = input("\n🔍 Run validation now? (Y/n): ").lower().strip()
            if run_validation != 'n':
                os.system("python validate_api_setup.py")

        else:
            print("❌ Setup cancelled. No changes made.")

    except KeyboardInterrupt:
        print("\n❌ Setup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()