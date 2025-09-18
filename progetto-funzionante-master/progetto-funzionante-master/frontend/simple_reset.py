#!/usr/bin/env python3
"""
Simple, bulletproof database reset for Railway
"""

import os
from sqlalchemy import create_engine, text, MetaData
from models import Base, User
from jwt_auth import hash_password
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def simple_reset():
    """Simple database reset - drop all, create all, add admin"""
    try:
        # Get database URL
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            logger.error("No DATABASE_URL found")
            return False
            
        # Create engine
        engine = create_engine(database_url)
        
        logger.info("🚨 Starting complete database reset...")
        
        # Step 1: Drop all tables
        with engine.connect() as conn:
            logger.info("Dropping all tables...")
            
            # Disable foreign key checks
            conn.execute(text("SET session_replication_role = replica;"))
            
            # Get table names and drop them
            result = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))
            tables = [row[0] for row in result]
            
            for table in tables:
                logger.info(f"Dropping table: {table}")
                conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                
            conn.execute(text("SET session_replication_role = DEFAULT;"))
            conn.commit()
            logger.info("All tables dropped!")
        
        # Step 2: Create all tables from models
        logger.info("Creating all tables from SQLAlchemy models...")
        Base.metadata.create_all(bind=engine)
        logger.info("All tables created!")
        
        # Step 3: Add admin user
        logger.info("Creating admin user...")
        from sqlalchemy.orm import sessionmaker
        
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
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
            
            session.add(admin_user)
            session.commit()
            logger.info("Admin user created: admin@ai-cash-revolution.com / admin123!")
            
        finally:
            session.close()
        
        logger.info("✅ Database reset completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Database reset failed: {e}")
        return False

if __name__ == "__main__":
    success = simple_reset()
    if success:
        print("✅ Database reset successful!")
    else:
        print("❌ Database reset failed!")
