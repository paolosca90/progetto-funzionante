"""
Database Service with Dependency Injection Support

This service provides enhanced database management with:
- Connection pooling and management
- Session management with proper cleanup
- Transaction management
- Database health monitoring
- Performance monitoring
- Connection resilience and retry logic
"""

import logging
import asyncio
import time
from typing import AsyncContextManager, Optional, Dict, Any, List, Callable
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass
from enum import Enum
import threading
from functools import wraps
import weakref

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import SQLAlchemyError, DBAPIError, OperationalError
from sqlalchemy.pool import QueuePool
import asyncpg

from ..core.config import Settings as CoreSettings
from ..core.dependency_injection import ServiceLifetime, inject
from ..services.logging_service import LoggingService
from ..services.config_service import ConfigService

logger = logging.getLogger(__name__)


class DatabaseHealthStatus(Enum):
    """Database health status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ConnectionPoolMetrics:
    """Connection pool metrics"""

    def __init__(self):
        self.total_connections = 0
        self.active_connections = 0
        self.idle_connections = 0
        self.failed_connections = 0
        self.average_wait_time = 0.0
        self.max_wait_time = 0.0
        self.total_wait_time = 0.0
        self.wait_count = 0


@dataclass
class DatabaseMetrics:
    """Database performance metrics"""
    query_count: int = 0
    query_time_total: float = 0.0
    query_time_avg: float = 0.0
    query_errors: int = 0
    transaction_count: int = 0
    transaction_time_total: float = 0.0
    connection_count: int = 0
    pool_metrics: Optional[ConnectionPoolMetrics] = None
    last_health_check: Optional[float] = None
    health_status: DatabaseHealthStatus = DatabaseHealthStatus.UNKNOWN


class DatabaseService:
    """Enhanced database service with dependency injection support"""

    def __init__(self, settings: CoreSettings, logging_service: LoggingService, config_service: ConfigService):
        self.settings = settings
        self.logging_service = logging_service
        self.config_service = config_service

        # Database components
        self._engine = None
        self._session_factory = None
        self._scoped_session = None
        self._base = declarative_base()

        # Connection management
        self._connection_pool_metrics = ConnectionPoolMetrics()
        self._metrics = DatabaseMetrics()
        self._lock = threading.RLock()

        # Health monitoring
        self._health_status = DatabaseHealthStatus.UNKNOWN
        self._last_health_check = 0.0
        self._health_check_interval = 30.0  # 30 seconds

        # Retry configuration
        self._max_retries = 3
        self._retry_delay = 1.0

        # Performance monitoring
        self._slow_query_threshold = 1.0  # 1 second
        self._query_callbacks: List[Callable] = []

        # Initialize database
        self._initialize_database()

    def _initialize_database(self) -> None:
        """Initialize database connection and components"""
        try:
            # Get database configuration
            db_config = self.config_service.get_database_config()
            database_url = self._get_database_url(db_config)

            # Create engine with connection pooling
            self._engine = self._create_engine(database_url, db_config)

            # Create session factory
            self._session_factory = sessionmaker(
                bind=self._engine,
                expire_on_commit=False,
                autoflush=False
            )

            # Create scoped session for thread safety
            self._scoped_session = scoped_session(self._session_factory)

            # Set up event listeners
            self._setup_event_listeners()

            # Test connection
            self._test_connection()

            logger.info("Database service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize database service: {e}")
            raise

    def _get_database_url(self, db_config: Dict[str, Any]) -> str:
        """Get database URL from configuration"""
        # Try to get from environment first
        database_url = self.settings.DATABASE_URL

        if not database_url:
            # Fall back to config service
            database_url = db_config.get('database_url')

        if not database_url:
            raise ValueError("Database URL not configured")

        return database_url

    def _create_engine(self, database_url: str, db_config: Dict[str, Any]):
        """Create database engine with connection pooling"""
        pool_size = db_config.get('pool_size', 10)
        max_overflow = db_config.get('max_overflow', 20)
        pool_timeout = db_config.get('pool_timeout', 30)
        pool_recycle = db_config.get('pool_recycle', 3600)

        # Create engine with optimized settings
        engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_recycle=pool_recycle,
            pool_pre_ping=True,  # Enable connection health checks
            pool_use_lifo=True,  # Use LIFO for better performance
            echo=False,  # Disable SQL echo in production
            isolation_level="READ COMMITTED",
            connect_args={
                'connect_timeout': 10,
                'command_timeout': 30,
                'application_name': 'ai_trading_system'
            }
        )

        return engine

    def _setup_event_listeners(self) -> None:
        """Set up SQLAlchemy event listeners for monitoring"""

        @event.listens_for(self._engine, 'before_cursor_execute')
        def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            context._query_start_time = time.time()
            context._query_statement = statement
            self._metrics.query_count += 1

        @event.listens_for(self._engine, 'after_cursor_execute')
        def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            total = time.time() - context._query_start_time
            self._metrics.query_time_total += total
            self._metrics.query_time_avg = self._metrics.query_time_total / self._metrics.query_count

            # Log slow queries
            if total > self._slow_query_threshold:
                self.logging_service.log_warning(
                    f"Slow query detected: {statement[:100]}... took {total:.2f}s",
                    extra={'query_time': total, 'statement': statement[:200]}
                )

            # Call query callbacks
            for callback in self._query_callbacks:
                try:
                    callback(statement, parameters, total)
                except Exception as e:
                    logger.error(f"Error in query callback: {e}")

        @event.listens_for(self._engine, 'handle_error')
        def receive_handle_error(exception_context):
            self._metrics.query_errors += 1
            self.logging_service.log_error(
                f"Database error: {exception_context.original_exception}",
                extra={'error': str(exception_context.original_exception)}
            )

        @event.listens_for(self._engine, 'engine_connect')
        def receive_engine_connect(connection, branch):
            if not branch:  # Only track main connections
                self._metrics.connection_count += 1
                self._connection_pool_metrics.total_connections += 1

    def _test_connection(self) -> None:
        """Test database connection"""
        try:
            with self._engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.fetchone()

            self._health_status = DatabaseHealthStatus.HEALTHY
            self._last_health_check = time.time()
            logger.info("Database connection test successful")

        except Exception as e:
            self._health_status = DatabaseHealthStatus.UNHEALTHY
            logger.error(f"Database connection test failed: {e}")
            raise

    def get_session(self) -> Session:
        """Get a new database session"""
        if self._session_factory is None:
            raise RuntimeError("Database service not initialized")

        return self._session_factory()

    def get_scoped_session(self) -> Session:
        """Get a scoped session (thread-safe)"""
        if self._scoped_session is None:
            raise RuntimeError("Database service not initialized")

        return self._scoped_session()

    @asynccontextmanager
    async def get_async_session(self) -> AsyncContextManager[Session]:
        """Get an async database session"""
        session = self.get_session()
        try:
            yield session
        finally:
            session.close()

    @contextmanager
    def get_session_context(self) -> Session:
        """Get a session with context manager for automatic cleanup"""
        session = self.get_session()
        try:
            yield session
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    @asynccontextmanager
    async def get_transaction(self) -> AsyncContextManager[Session]:
        """Get a session with transaction context"""
        session = self.get_session()
        try:
            yield session
            session.commit()
            self._metrics.transaction_count += 1
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def execute_with_retry(self, operation: Callable, *args, **kwargs) -> Any:
        """Execute database operation with retry logic"""
        last_exception = None

        for attempt in range(self._max_retries):
            try:
                return operation(*args, **kwargs)
            except (OperationalError, DBAPIError) as e:
                last_exception = e
                if attempt < self._max_retries - 1:
                    wait_time = self._retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Database operation failed, retrying in {wait_time}s... (attempt {attempt + 1}/{self._max_retries})")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Database operation failed after {self._max_retries} attempts")
                    raise
            except SQLAlchemyError as e:
                logger.error(f"Database operation failed: {e}")
                raise

        if last_exception:
            raise last_exception

    async def check_health(self) -> DatabaseHealthStatus:
        """Check database health"""
        current_time = time.time()

        # Cache health check results
        if current_time - self._last_health_check < self._health_check_interval:
            return self._health_status

        try:
            async with self.get_async_session() as session:
                # Simple health check query
                result = session.execute(text("SELECT 1"))
                result.fetchone()

            self._health_status = DatabaseHealthStatus.HEALTHY
            self._last_health_check = current_time
            self._metrics.last_health_check = current_time

        except Exception as e:
            self._health_status = DatabaseHealthStatus.UNHEALTHY
            self._last_health_check = current_time
            self._metrics.last_health_check = current_time
            logger.error(f"Database health check failed: {e}")

        return self._health_status

    def get_metrics(self) -> DatabaseMetrics:
        """Get database performance metrics"""
        self._update_pool_metrics()
        self._metrics.pool_metrics = self._connection_pool_metrics
        self._metrics.health_status = self._health_status
        self._metrics.last_health_check = self._last_health_check

        return self._metrics

    def _update_pool_metrics(self) -> None:
        """Update connection pool metrics"""
        if self._engine and hasattr(self._engine, 'pool'):
            pool = self._engine.pool
            if pool:
                self._connection_pool_metrics.total_connections = pool.size()
                self._connection_pool_metrics.active_connections = pool.checkedout()
                self._connection_pool_metrics.idle_connections = pool.checkedin()

    def add_query_callback(self, callback: Callable[[str, Any, float], None]) -> None:
        """Add a callback for query monitoring"""
        self._query_callbacks.append(callback)

    def remove_query_callback(self, callback: Callable) -> None:
        """Remove a query callback"""
        if callback in self._query_callbacks:
            self._query_callbacks.remove(callback)

    def reset_metrics(self) -> None:
        """Reset performance metrics"""
        self._metrics = DatabaseMetrics()
        self._connection_pool_metrics = ConnectionPoolMetrics()

    def get_base(self) -> Any:
        """Get SQLAlchemy declarative base"""
        return self._base

    def get_engine(self) -> Any:
        """Get SQLAlchemy engine"""
        return self._engine

    def create_all_tables(self) -> None:
        """Create all database tables"""
        if self._engine and self._base:
            self._base.metadata.create_all(bind=self._engine)
            logger.info("All database tables created")

    def drop_all_tables(self) -> None:
        """Drop all database tables"""
        if self._engine and self._base:
            self._base.metadata.drop_all(bind=self._engine)
            logger.info("All database tables dropped")

    def get_table_names(self) -> List[str]:
        """Get list of table names"""
        if self._engine:
            with self._engine.connect() as conn:
                result = conn.execute(text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))
                return [row[0] for row in result.fetchall()]
        return []

    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """Get table information"""
        if not self._engine:
            return {}

        info = {}

        try:
            with self._engine.connect() as conn:
                # Get column information
                result = conn.execute(text("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = :table_name
                    ORDER BY ordinal_position
                """), {'table_name': table_name})

                columns = []
                for row in result.fetchall():
                    columns.append({
                        'name': row[0],
                        'type': row[1],
                        'nullable': row[2] == 'YES',
                        'default': row[3]
                    })

                info['columns'] = columns

                # Get row count
                count_result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                info['row_count'] = count_result.fetchone()[0]

        except Exception as e:
            logger.error(f"Error getting table info for {table_name}: {e}")

        return info

    def backup_database(self, backup_path: str) -> bool:
        """Create database backup"""
        try:
            # This is a simplified implementation
            # In production, you'd use pg_dump or similar tools
            logger.info(f"Creating database backup to {backup_path}")

            # Execute backup command
            import subprocess
            import os

            db_config = self.config_service.get_database_config()
            db_url = self._get_database_url(db_config)

            # Parse database URL for pg_dump
            if db_url.startswith('postgresql://'):
                # Remove protocol from URL
                db_url_clean = db_url.replace('postgresql://', '')

                # Create backup command
                cmd = [
                    'pg_dump',
                    f'--dbname={db_url_clean}',
                    '--file=' + backup_path,
                    '--format=custom',
                    '--verbose'
                ]

                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode == 0:
                    logger.info("Database backup created successfully")
                    return True
                else:
                    logger.error(f"Backup failed: {result.stderr}")
                    return False
            else:
                logger.error("Backup only supported for PostgreSQL")
                return False

        except Exception as e:
            logger.error(f"Error creating database backup: {e}")
            return False

    def restore_database(self, backup_path: str) -> bool:
        """Restore database from backup"""
        try:
            logger.info(f"Restoring database from {backup_path}")

            # Execute restore command
            import subprocess

            db_config = self.config_service.get_database_config()
            db_url = self._get_database_url(db_config)

            if db_url.startswith('postgresql://'):
                # Remove protocol from URL
                db_url_clean = db_url.replace('postgresql://', '')

                # Create restore command
                cmd = [
                    'pg_restore',
                    f'--dbname={db_url_clean}',
                    '--verbose',
                    backup_path
                ]

                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode == 0:
                    logger.info("Database restore completed successfully")
                    return True
                else:
                    logger.error(f"Restore failed: {result.stderr}")
                    return False
            else:
                logger.error("Restore only supported for PostgreSQL")
                return False

        except Exception as e:
            logger.error(f"Error restoring database: {e}")
            return False

    def close_all_sessions(self) -> None:
        """Close all active sessions"""
        if self._scoped_session:
            self._scoped_session.remove()

        if self._engine:
            self._engine.dispose()

        logger.info("All database sessions closed")

    def __dispose__(self) -> None:
        """Dispose database service resources"""
        self.close_all_sessions()
        self._query_callbacks.clear()
        logger.info("Database service disposed")


# Database utility functions
def with_session(operation_func):
    """Decorator to provide database session to function"""
    @wraps(operation_func)
    def wrapper(self, *args, **kwargs):
        if hasattr(self, 'get_session_context'):
            with self.get_session_context() as session:
                return operation_func(self, session, *args, **kwargs)
        else:
            # Fallback for classes without database service
            from database import SessionLocal
            session = SessionLocal()
            try:
                return operation_func(self, session, *args, **kwargs)
            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()
    return wrapper


def with_transaction(operation_func):
    """Decorator to provide transaction session to function"""
    @wraps(operation_func)
    async def wrapper(self, *args, **kwargs):
        if hasattr(self, 'database_service'):
            async with self.database_service.get_transaction() as session:
                return await operation_func(self, session, *args, **kwargs)
        else:
            # Fallback for classes without database service
            from database import SessionLocal
            session = SessionLocal()
            try:
                result = await operation_func(self, session, *args, **kwargs)
                session.commit()
                return result
            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.close()
    return wrapper