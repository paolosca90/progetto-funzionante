from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Database URL from environment variable (Railway provides this automatically)
DATABASE_URL = os.getenv("DATABASE_URL")

# If no DATABASE_URL, use SQLite for local development
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./trading_signals.db"
    
# Fix PostgreSQL URL format for SQLAlchemy 2.x
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create engine
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency to get database session
def get_database():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Health check function
def check_database_health():
    """Check if database is accessible"""
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return True
    except Exception:
        return False