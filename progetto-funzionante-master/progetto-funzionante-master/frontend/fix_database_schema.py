#!/usr/bin/env python3
"""
Database schema fix script to add missing columns to the users table.
This fixes login/registration issues by ensuring the database matches the model.
"""

import sqlite3
import os

def fix_database_schema():
    """Add missing columns to the users table"""
    
    # Database path - adjust if different
    db_path = "trading_signals.db"
    
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found. Creating new database...")
        # If no database exists, SQLAlchemy will create it properly
        from database import engine
        from models import Base
        Base.metadata.create_all(bind=engine)
        print("New database created successfully!")
        return
    
    print(f"Fixing database schema in {db_path}...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check existing columns
        cursor.execute("PRAGMA table_info(users)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        print(f"Existing columns: {existing_columns}")
        
        # List of columns that should exist
        required_columns = {
            'id': 'INTEGER PRIMARY KEY',
            'username': 'VARCHAR(50) NOT NULL UNIQUE',
            'email': 'VARCHAR(100) NOT NULL UNIQUE', 
            'hashed_password': 'VARCHAR(128) NOT NULL',
            'full_name': 'VARCHAR(100)',
            'is_active': 'BOOLEAN DEFAULT 1',
            'is_admin': 'BOOLEAN DEFAULT 0',
            'created_at': 'DATETIME DEFAULT CURRENT_TIMESTAMP',
            'trial_end': 'DATETIME',
            'subscription_active': 'BOOLEAN DEFAULT 1',
            'last_login': 'DATETIME',
            'reset_token': 'VARCHAR(100)',
            'reset_token_expires': 'DATETIME'
        }
        
        # Add missing columns
        columns_added = 0
        for column, definition in required_columns.items():
            if column not in existing_columns:
                print(f"Adding missing column: {column}")
                try:
                    cursor.execute(f"ALTER TABLE users ADD COLUMN {column} {definition}")
                    columns_added += 1
                except sqlite3.OperationalError as e:
                    if "duplicate column name" not in str(e):
                        print(f"Warning: Could not add column {column}: {e}")
        
        conn.commit()
        print(f"Successfully added {columns_added} missing columns!")
        
        # Verify the fix
        cursor.execute("PRAGMA table_info(users)")
        final_columns = {row[1] for row in cursor.fetchall()}
        print(f"Final columns: {sorted(final_columns)}")
        
        if all(col in final_columns for col in required_columns.keys()):
            print("✅ Database schema is now correct!")
        else:
            missing = set(required_columns.keys()) - final_columns
            print(f"❌ Still missing columns: {missing}")
            
    except Exception as e:
        print(f"Error fixing database: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_database_schema()