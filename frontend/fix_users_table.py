#!/usr/bin/env python3
"""
Script to add missing columns to users table.
This fixes login/registration issues by ensuring the database matches the model.
"""

from database import engine
from sqlalchemy import text, inspect
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_missing_users_columns():
    """Check which columns are missing from users table"""
    inspector = inspect(engine)

    # Get existing columns in users table
    existing_columns = [col['name'] for col in inspector.get_columns('users')]

    logger.info(f"Existing columns in users table: {existing_columns}")

    # Define the required user columns
    required_columns = {
        'username': ("VARCHAR(50) NOT NULL UNIQUE", "Username"),
        'email': ("VARCHAR(100) NOT NULL UNIQUE", "Email address"),
        'hashed_password': ("VARCHAR(128) NOT NULL", "Hashed password"),
        'full_name': ("VARCHAR(100)", "Full name"),
        'is_active': ("BOOLEAN DEFAULT TRUE", "Active user flag"),
        'is_admin': ("BOOLEAN DEFAULT FALSE", "Admin user flag"),
        'created_at': ("TIMESTAMP DEFAULT NOW()", "Account creation timestamp"),
        'trial_end': ("TIMESTAMP", "Trial end date"),
        'subscription_active': ("BOOLEAN DEFAULT TRUE", "Subscription status"),
        'last_login': ("TIMESTAMP", "Last login timestamp"),
        'reset_token': ("VARCHAR(100)", "Password reset token"),
        'reset_token_expires': ("TIMESTAMP", "Reset token expiration")
    }

    missing_columns = {}
    for col_name, (col_definition, description) in required_columns.items():
        if col_name not in existing_columns:
            missing_columns[col_name] = (col_definition, description)

    return missing_columns

def add_missing_users_columns():
    """Add missing columns to users table"""
    try:
        missing_columns = check_missing_users_columns()

        if not missing_columns:
            logger.info("All required columns are already present!")
            return True

        logger.info(f"Found {len(missing_columns)} missing columns: {list(missing_columns.keys())}")

        with engine.connect() as conn:
            # Add each missing column
            for col_name, (col_type, description) in missing_columns.items():
                if 'PASSWORD' in col_name.upper():
                    col_type = "VARCHAR(128) NOT NULL"
                elif 'TOKEN' in col_name.upper():
                    col_type = "VARCHAR(100)"
                elif 'TIMESTAMP' in col_name.upper() or 'LOGIN' in col_name.upper() or 'END' in col_name.upper():
                    col_type = "TIMESTAMP"
                elif 'BOOLEAN' in col_name.upper():
                    col_type = "BOOLEAN"

                alter_sql = f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col_name} {col_type}"
                logger.info(f"Executing: {alter_sql}")
                conn.execute(text(alter_sql))
                conn.commit()

                logger.info(f"Added column '{col_name}' ({description})")

        logger.info("Successfully added all missing columns!")
        return True

    except Exception as e:
        logger.error(f"Failed to add missing columns: {e}")
        return False

def verify_migration():
    """Verify that all columns were added correctly"""
    try:
        inspector = inspect(engine)
        new_columns = [col['name'] for col in inspector.get_columns('users')]
        logger.info(f"Final columns in users table after migration: {new_columns}")

        # Check for critical user columns
        critical_cols = [
            'username', 'email', 'hashed_password', 'is_active', 'is_admin',
            'created_at', 'last_login', 'reset_token', 'reset_token_expires'
        ]

        missing_after_migration = [
            col for col in critical_cols
            if col not in new_columns
        ]

        if missing_after_migration:
            logger.warning(f"Still missing critical columns: {missing_after_migration}")
            return False
        else:
            logger.info("All required user columns are now present!")
            return True

    except Exception as e:
        logger.error(f"Failed to verify migration: {e}")
        return False

if __name__ == "__main__":
    print("User Table Migration")
    print("=" * 30)

    print("Checking for missing columns...")
    successful = add_missing_users_columns()

    if successful:
        print("\nVerifying migration...")
        successful = verify_migration()

    if successful:
        print("\nMigration completed successfully!")
        print("The users table now has all required columns.")
        print("Login and registration should work properly.")
    else:
        print("\nMigration encountered issues.")
        print("Please check the logs above for details.")

    print("\nRestart your application for changes to take effect.\n")