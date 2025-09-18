#!/usr/bin/env python3
"""
Railway PostgreSQL database migration script.
This script adds missing columns to the users table in the Railway PostgreSQL database.
"""

import os
import sys
import psycopg2
from urllib.parse import urlparse

def migrate_railway_database():
    """Add missing columns to the Railway PostgreSQL users table"""
    
    # Get DATABASE_URL from environment (Railway sets this)
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL environment variable not found")
        print("This script must be run on Railway where DATABASE_URL is set")
        return False
    
    print(f"🔗 Connecting to Railway PostgreSQL database...")
    
    try:
        # Parse the DATABASE_URL
        url = urlparse(database_url)
        
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host=url.hostname,
            port=url.port,
            user=url.username,
            password=url.password,
            database=url.path[1:]  # Remove leading slash
        )
        
        cursor = conn.cursor()
        
        print("✅ Connected to PostgreSQL database")
        
        # Check existing columns
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND table_schema = 'public'
        """)
        
        existing_columns = {row[0] for row in cursor.fetchall()}
        print(f"📋 Existing columns: {existing_columns}")
        
        # List of columns that should exist
        required_columns = {
            'last_login': 'TIMESTAMP',
            'reset_token': 'VARCHAR(100)',
            'reset_token_expires': 'TIMESTAMP'
        }
        
        # Add missing columns
        columns_added = 0
        for column, column_type in required_columns.items():
            if column not in existing_columns:
                print(f"➕ Adding missing column: {column}")
                try:
                    cursor.execute(f"ALTER TABLE users ADD COLUMN {column} {column_type}")
                    columns_added += 1
                    print(f"✅ Added column: {column}")
                except psycopg2.Error as e:
                    if "already exists" in str(e):
                        print(f"⚠️  Column {column} already exists, skipping")
                    else:
                        print(f"❌ Error adding column {column}: {e}")
                        return False
        
        # Commit changes
        conn.commit()
        print(f"✅ Successfully added {columns_added} missing columns!")
        
        # Verify the migration
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND table_schema = 'public'
            ORDER BY column_name
        """)
        
        final_columns = {row[0] for row in cursor.fetchall()}
        print(f"📋 Final columns: {sorted(final_columns)}")
        
        if all(col in final_columns for col in required_columns.keys()):
            print("✅ Railway database schema migration completed successfully!")
            return True
        else:
            missing = set(required_columns.keys()) - final_columns
            print(f"❌ Still missing columns: {missing}")
            return False
            
    except psycopg2.Error as e:
        print(f"❌ PostgreSQL error: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    finally:
        if 'conn' in locals():
            cursor.close()
            conn.close()
            print("🔌 Database connection closed")

if __name__ == "__main__":
    success = migrate_railway_database()
    sys.exit(0 if success else 1)
