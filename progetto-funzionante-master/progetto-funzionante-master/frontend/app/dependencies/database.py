from sqlalchemy.orm import Session
from database import SessionLocal


def get_db() -> Session:
    """
    Dependency to get database session.

    Yields:
        Database session that automatically closes after request
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()