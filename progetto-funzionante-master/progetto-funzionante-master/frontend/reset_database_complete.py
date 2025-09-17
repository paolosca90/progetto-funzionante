#!/usr/bin/env python3
"""
Complete database reset script for Railway PostgreSQL.
Drops all existing tables and recreates them from SQLAlchemy models.
"""

from database import engine
from models import Base, User
from sqlalchemy import text, inspect
from jwt_auth import hash_password
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def drop_all_tables():
    """Drop all existing tables"""
    try:
        with engine.connect() as conn:
            # Get all table names
            inspector = inspect(engine)
            table_names = inspector.get_table_names()
            
            if not table_names:
                logger.info("No tables found to drop")
                return True
                
            logger.info(f"Found {len(table_names)} tables to drop: {table_names}")
            
            # Drop all tables (disable foreign key checks temporarily)
            conn.execute(text("SET session_replication_role = replica;"))
            
            for table_name in table_names:
                logger.info(f"Dropping table: {table_name}")
                conn.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE"))
            
            conn.execute(text("SET session_replication_role = DEFAULT;"))
            conn.commit()
            
            logger.info("All tables dropped successfully!")
            return True
            
    except Exception as e:
        logger.error(f"Failed to drop tables: {e}")
        return False

def create_all_tables():
    """Create all tables from SQLAlchemy models"""
    try:
        logger.info("Creating all tables from models...")
        Base.metadata.create_all(bind=engine)
        logger.info("All tables created successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        return False

def create_admin_user():
    """Create a default admin user"""
    db = None
    try:
        from database import get_db
        db = next(get_db())
        
        # Check if admin user already exists
        existing_admin = db.query(User).filter(User.email == "admin@ai-cash-revolution.com").first()
        if existing_admin:
            logger.info("Admin user already exists")
            return True
            
        # Create admin user
        admin_user = User(
            username="admin",
            email="admin@ai-cash-revolution.com",
            hashed_password=hash_password("admin123!"),
            full_name="System Administrator",
            is_active=True,
            is_admin=True,
            created_at=datetime.now(),
            trial_end=datetime.now() + timedelta(days=365),
            subscription_active=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        logger.info("Admin user created successfully!")
        logger.info("Login: admin@ai-cash-revolution.com / admin123!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create admin user: {e}")
        return False
    finally:
        if db:
            db.close()

def verify_database():
    """Verify database structure"""
    try:
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        
        expected_tables = ['users', 'signals', 'signal_executions', 'subscriptions', 'oanda_connections']
        
        logger.info(f"Found tables: {table_names}")
        
        missing_tables = [table for table in expected_tables if table not in table_names]
        if missing_tables:
            logger.error(f"Missing tables: {missing_tables}")
            return False
            
        # Check users table structure
        user_columns = [col['name'] for col in inspector.get_columns('users')]
        required_user_cols = ['id', 'username', 'email', 'hashed_password', 'is_active', 'is_admin', 'last_login']
        
        missing_user_cols = [col for col in required_user_cols if col not in user_columns]
        if missing_user_cols:
            logger.error(f"Missing user columns: {missing_user_cols}")
            return False
            
        logger.info("Database structure verification passed!")
        return True
        
    except Exception as e:
        logger.error(f"Database verification failed: {e}")
        return False

def reset_complete_database():
    """Complete database reset workflow"""
    logger.info("🚨 STARTING COMPLETE DATABASE RESET")
    logger.info("=" * 50)
    
    # Step 1: Drop all tables
    logger.info("Step 1: Dropping all existing tables...")
    if not drop_all_tables():
        return False
        
    # Step 2: Create all tables
    logger.info("\nStep 2: Creating all tables from models...")  
    if not create_all_tables():
        return False
        
    # Step 3: Create admin user
    logger.info("\nStep 3: Creating default admin user...")
    if not create_admin_user():
        return False
        
    # Step 4: Verify database
    logger.info("\nStep 4: Verifying database structure...")
    if not verify_database():
        return False
        
    logger.info("\n✅ DATABASE RESET COMPLETED SUCCESSFULLY!")
    logger.info("=" * 50)
    logger.info("Admin Login: admin@ai-cash-revolution.com / admin123!")
    logger.info("The application should now work correctly.")
    
    return True

if __name__ == "__main__":
    success = reset_complete_database()
    
    if success:
        print("\n🎉 Database reset successful!")
        print("You can now use the application normally.")
    else:
        print("\n❌ Database reset failed!")
        print("Check the logs above for details.")