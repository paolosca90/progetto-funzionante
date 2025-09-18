#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migration script to add missing columns to the railway production database
This script safely adds missing technical analysis columns to the signals table
without losing existing data
"""

from database import engine
from sqlalchemy import text, inspect
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_missing_columns():
    """Check which technical analysis columns are missing"""
    inspector = inspect(engine)

    # Get existing columns in signals table
    existing_columns = [col['name'] for col in inspector.get_columns('signals')]

    logger.info(f"Existing columns in signals table: {existing_columns}")

    # Define the missing technical analysis columns that need to be added
    required_columns = {
        'timeframe': ("VARCHAR(10) DEFAULT 'H1'", "Analysis timeframe"),
        'risk_reward_ratio': ("FLOAT DEFAULT 0.0", "Risk/reward ratio"),
        'position_size_suggestion': ("FLOAT DEFAULT 0.01", "Suggested position size"),
        'spread': ("FLOAT DEFAULT 0.0", "Market spread at signal generation"),
        'volatility': ("FLOAT DEFAULT 0.0", "Market volatility (ATR-based)"),
        'technical_score': ("FLOAT DEFAULT 0.0", "Overall technical score"),
        'rsi': ("FLOAT", "RSI at signal generation"),
        'market_session': ("VARCHAR(20)", "Market session (Asian/European/US)")
    }

    missing_columns = {}
    for col_name, col_definition in required_columns.items():
        if col_name not in existing_columns:
            missing_columns[col_name] = col_definition

    return missing_columns

def add_missing_columns():
    """Add missing technical analysis columns to signals table"""
    try:
        missing_columns = check_missing_columns()

        if not missing_columns:
            logger.info("All required columns are already present!")
            return True

        logger.info(f"Found {len(missing_columns)} missing columns: {list(missing_columns.keys())}")

        with engine.connect() as conn:
            # Add each missing column
            for col_name, (col_type, description) in missing_columns.items():
                alter_sql = f"ALTER TABLE signals ADD COLUMN IF NOT EXISTS {col_name} {col_type}"
                logger.info(f"Executing: {alter_sql}")
                conn.execute(text(alter_sql))
                conn.commit()

                logger.info(f"✅ Added column '{col_name}' ({description})")

        logger.info("Successfully added all missing columns!")
        return True

    except Exception as e:
        logger.error(f"Failed to add missing columns: {e}")
        logger.error("You may need to manually add these columns using Railway's PostgreSQL console")
        return False

def verify_migration():
    """Verify that all columns were added correctly"""
    try:
        inspector = inspect(engine)
        new_columns = [col['name'] for col in inspector.get_columns('signals')]
        logger.info(f"Final columns in signals table after migration: {new_columns}")

        # Check for our technical analysis columns
        required_cols = [
            'timeframe', 'risk_reward_ratio', 'position_size_suggestion',
            'spread', 'volatility', 'technical_score', 'rsi', 'market_session'
        ]

        missing_after_migration = [
            col for col in required_cols
            if col not in new_columns
        ]

        if missing_after_migration:
            logger.warning(f"Still missing columns: {missing_after_migration}")
            return False
        else:
            logger.info("✅ All required technical analysis columns are now present!")
            return True

    except Exception as e:
        logger.error(f"Failed to verify migration: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Railway Database Column Migration")
    print("=" * 50)

    print("🔍 Checking for missing columns...")
    successful = add_missing_columns()

    if successful:
        print("\n✅ Verifying migration...")
        successful = verify_migration()

    if successful:
        print("\n🎉 Migration completed successfully!")
        print("The technical analysis columns have been added to your production database.")
        print("Signal endpoints should now work without crashes.")
    else:
        print("\n❌ Migration encountered issues.")
        print("Please check Railway logs and consider manual column addition if needed.")

    print("\n📝 You may need to restart your Railway deployment for changes to take effect.\n")
