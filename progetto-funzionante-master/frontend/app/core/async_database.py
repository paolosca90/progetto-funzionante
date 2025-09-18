"""
Async Database Support for FastAPI
Implements async database operations using SQLAlchemy 2.0 async support
"""

import asyncio
import logging
from typing import AsyncGenerator, Optional, Dict, Any
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.exc import SQLAlchemyError
import os

from app.core.config import settings

logger = logging.getLogger(__name__)

# Async database URL conversion
def get_async_database_url(sync_url: str) -> str:
    """Convert synchronous database URL to async format"""
    if sync_url.startswith("sqlite"):
        return sync_url.replace("sqlite://", "sqlite+aiosqlite://")
    elif sync_url.startswith("postgresql://"):
        return sync_url.replace("postgresql://", "postgresql+asyncpg://")
    elif sync_url.startswith("mysql://"):
        return sync_url.replace("mysql://", "mysql+aiomysql://")
    return sync_url

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./trading_signals.db"

# Convert to async URL
ASYNC_DATABASE_URL = get_async_database_url(DATABASE_URL)

# Create async engine with optimized settings
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=settings.is_development,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600,
    future=True
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

# Import the Base from models for async compatibility
try:
    from models import Base as ModelsBase
    AsyncBase = ModelsBase
except ImportError:
    from sqlalchemy.ext.declarative import declarative_base
    AsyncBase = declarative_base()

class AsyncDatabaseManager:
    """Manager for async database operations with connection pooling and health monitoring"""

    def __init__(self):
        self.engine = async_engine
        self.session_factory = AsyncSessionLocal
        self._connection_pool = {}
        self._health_check_interval = 60  # seconds
        self._last_health_check = None
        self._is_healthy = False

    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive database health check"""
        try:
            async with AsyncSessionLocal() as session:
                # Test basic connectivity
                result = await session.execute("SELECT 1")
                await session.commit()

                # Get connection pool stats
                pool = self.engine.pool
                pool_stats = {
                    "size": pool.size(),
                    "checked_in": pool.checkedin(),
                    "checked_out": pool.checkedout(),
                    "overflow": pool.overflow(),
                    "invalidated": pool.invalidated()
                }

                self._is_healthy = True
                self._last_health_check = asyncio.get_event_loop().time()

                return {
                    "status": "healthy",
                    "connection": "connected",
                    "pool_stats": pool_stats,
                    "engine_url": str(self.engine.url),
                    "async_supported": True
                }

        except SQLAlchemyError as e:
            self._is_healthy = False
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "connection": "disconnected",
                "error": str(e),
                "async_supported": False
            }
        except Exception as e:
            self._is_healthy = False
            logger.error(f"Unexpected database health check error: {e}")
            return {
                "status": "error",
                "connection": "error",
                "error": str(e),
                "async_supported": False
            }

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get async database session with proper error handling and cleanup"""
        session = self.session_factory()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()

    @asynccontextmanager
    async def get_connection(self):
        """Get raw database connection for complex operations"""
        async with self.engine.connect() as connection:
            try:
                yield connection
            except Exception as e:
                logger.error(f"Database connection error: {e}")
                raise

    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute a raw SQL query asynchronously"""
        async with self.get_session() as session:
            try:
                result = await session.execute(query, params or {})
                await session.commit()
                return result
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"Query execution error: {e}")
                raise

    async def execute_many(self, queries: list[tuple[str, Optional[Dict[str, Any]]]]) -> list[Any]:
        """Execute multiple queries in a transaction"""
        async with self.get_session() as session:
            try:
                results = []
                for query, params in queries:
                    result = await session.execute(query, params or {})
                    results.append(result)
                await session.commit()
                return results
            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"Batch query execution error: {e}")
                raise

    async def create_tables(self):
        """Create database tables asynchronously"""
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(AsyncBase.metadata.create_all)
            logger.info("Database tables created successfully")
        except SQLAlchemyError as e:
            logger.error(f"Failed to create database tables: {e}")
            raise

    async def drop_tables(self):
        """Drop database tables asynchronously"""
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(AsyncBase.metadata.drop_all)
            logger.info("Database tables dropped successfully")
        except SQLAlchemyError as e:
            logger.error(f"Failed to drop database tables: {e}")
            raise

    async def close(self):
        """Close all database connections"""
        try:
            await self.engine.dispose()
            logger.info("Database engine disposed successfully")
        except Exception as e:
            logger.error(f"Error closing database engine: {e}")

# Global async database manager instance
async_db_manager = AsyncDatabaseManager()

# Dependency for FastAPI routes
async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for getting async database session"""
    async with async_db_manager.get_session() as session:
        yield session

# Health check function for async database
async def check_async_database_health() -> bool:
    """Check if async database is accessible"""
    try:
        health_result = await async_db_manager.health_check()
        return health_result["status"] == "healthy"
    except Exception:
        return False

# Async context manager for database operations
@asynccontextmanager
async def async_database_operation():
    """Context manager for async database operations"""
    async with async_db_manager.get_session() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Async database operation failed: {e}")
            raise

# Utility functions for common async operations
async def async_fetch_all(session: AsyncSession, query, params: Optional[Dict[str, Any]] = None) -> list:
    """Fetch all results from a query"""
    result = await session.execute(query, params or {})
    return result.fetchall()

async def async_fetch_one(session: AsyncSession, query, params: Optional[Dict[str, Any]] = None) -> Optional[Any]:
    """Fetch one result from a query"""
    result = await session.execute(query, params or {})
    return result.fetchone()

async def async_fetch_scalar(session: AsyncSession, query, params: Optional[Dict[str, Any]] = None) -> Any:
    """Fetch scalar value from a query"""
    result = await session.execute(query, params or {})
    return result.scalar()

# Transaction management
@asynccontextmanager
async def async_transaction(session: AsyncSession):
    """Context manager for managing transactions"""
    try:
        async with session.begin():
            yield session
    except Exception as e:
        await session.rollback()
        logger.error(f"Transaction failed: {e}")
        raise

# Batch operations
async def async_batch_insert(session: AsyncSession, model_class, data_list: list[Dict[str, Any]]) -> list:
    """Insert multiple records asynchronously"""
    try:
        objects = [model_class(**data) for data in data_list]
        session.add_all(objects)
        await session.commit()

        # Refresh objects to get database-generated values
        for obj in objects:
            await session.refresh(obj)

        return objects
    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Batch insert failed: {e}")
        raise

# Connection pooling utilities
async def get_pool_status() -> Dict[str, Any]:
    """Get connection pool status"""
    pool = async_db_manager.engine.pool
    return {
        "pool_size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "invalidated": pool.invalidated(),
        "timeout": pool.timeout(),
        "healthy": async_db_manager._is_healthy
    }

# Initialize function for startup
async def init_async_database():
    """Initialize async database system"""
    try:
        await async_db_manager.create_tables()
        health_status = await async_db_manager.health_check()

        if health_status["status"] == "healthy":
            logger.info("Async database system initialized successfully")
            return True
        else:
            logger.warning(f"Async database system initialized with issues: {health_status}")
            return False
    except Exception as e:
        logger.error(f"Failed to initialize async database system: {e}")
        return False

# Cleanup function for shutdown
async def cleanup_async_database():
    """Cleanup async database system"""
    try:
        await async_db_manager.close()
        logger.info("Async database system cleaned up successfully")
    except Exception as e:
        logger.error(f"Failed to cleanup async database system: {e}")