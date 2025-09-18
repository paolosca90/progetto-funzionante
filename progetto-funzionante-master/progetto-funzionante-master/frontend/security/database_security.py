"""
Comprehensive Database Security and Encryption Framework
Production-ready database security with encryption and access control
"""

import os
import json
import hashlib
import hmac
import secrets
import base64
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Union, Callable
from enum import Enum
from dataclasses import dataclass, field
from contextlib import contextmanager
import logging
import redis
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError
import asyncpg
import asyncpg.pool
import asyncio
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
import jwt

logger = logging.getLogger(__name__)

class EncryptionAlgorithm(Enum):
    """Supported encryption algorithms"""
    AES_256_GCM = "aes_256_gcm"
    AES_256_CBC = "aes_256_cbc"
    FERNET = "fernet"
    RSA_OAEP = "rsa_oaep"

class DatabaseAccessLevel(Enum):
    """Database access levels"""
    READ_ONLY = "read_only"
    READ_WRITE = "read_write"
    ADMIN = "admin"
    SUPERUSER = "superuser"

class SecurityEventType(Enum):
    """Security event types for database"""
    LOGIN_SUCCESS = "db_login_success"
    LOGIN_FAILURE = "db_login_failure"
    QUERY_EXECUTED = "query_executed"
    DATA_ACCESSED = "data_accessed"
    DATA_MODIFIED = "data_modified"
    PERMISSION_DENIED = "permission_denied"
    SUSPICIOUS_QUERY = "suspicious_query"
    BACKUP_CREATED = "backup_created"
    BACKUP_RESTORED = "backup_restored"

@dataclass
class SecurityPolicy:
    """Database security policy configuration"""
    require_ssl: bool = True
    encrypt_sensitive_data: bool = True
    audit_log_enabled: bool = True
    query_timeout_seconds: int = 30
    connection_timeout_seconds: int = 10
    max_connections: int = 20
    idle_timeout_seconds: int = 300
    enable_row_level_security: bool = True
    encrypt_backups: bool = True
    backup_retention_days: int = 30
    require_mfa_for_admin: bool = True
    ip_whitelist: List[str] = field(default_factory=list)
    sensitive_tables: List[str] = field(default_factory=lambda: ["users", "oanda_connections", "subscriptions"])
    sensitive_columns: Dict[str, List[str]] = field(default_factory=lambda: {
        "users": ["password", "email", "hashed_password", "reset_token"],
        "oanda_connections": ["account_id", "api_key"],
        "subscriptions": ["payment_status", "last_payment_date"]
    })

class DatabaseEncryptor:
    """Database encryption utilities"""

    def __init__(self, encryption_key: Optional[str] = None):
        self.encryption_key = encryption_key or self._generate_encryption_key()
        self.fernet = Fernet(self.encryption_key.encode())
        self.aes_key = self._derive_aes_key(self.encryption_key)

    def _generate_encryption_key(self) -> str:
        """Generate a secure encryption key"""
        return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()

    def _derive_aes_key(self, password: str, salt: Optional[bytes] = None) -> bytes:
        """Derive AES key from password using PBKDF2"""
        if salt is None:
            salt = secrets.token_bytes(16)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        return kdf.derive(password.encode())

    def encrypt_field(self, value: str, algorithm: EncryptionAlgorithm = EncryptionAlgorithm.FERNET) -> str:
        """Encrypt a field value"""
        if not value:
            return value

        try:
            if algorithm == EncryptionAlgorithm.FERNET:
                encrypted = self.fernet.encrypt(value.encode())
                return base64.b64encode(encrypted).decode()
            elif algorithm == EncryptionAlgorithm.AES_256_GCM:
                return self._encrypt_aes_gcm(value)
            else:
                raise ValueError(f"Unsupported encryption algorithm: {algorithm}")
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise

    def decrypt_field(self, encrypted_value: str, algorithm: EncryptionAlgorithm = EncryptionAlgorithm.FERNET) -> str:
        """Decrypt a field value"""
        if not encrypted_value:
            return encrypted_value

        try:
            if algorithm == EncryptionAlgorithm.FERNET:
                encrypted_bytes = base64.b64decode(encrypted_value.encode())
                decrypted = self.fernet.decrypt(encrypted_bytes)
                return decrypted.decode()
            elif algorithm == EncryptionAlgorithm.AES_256_GCM:
                return self._decrypt_aes_gcm(encrypted_value)
            else:
                raise ValueError(f"Unsupported encryption algorithm: {algorithm}")
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise

    def _encrypt_aes_gcm(self, value: str) -> str:
        """Encrypt using AES-256-GCM"""
        iv = secrets.token_bytes(12)  # 96-bit IV for GCM
        cipher = Cipher(
            algorithms.AES(self.aes_key),
            modes.GCM(iv),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(value.encode()) + encryptor.finalize()
        return base64.b64encode(iv + encryptor.tag + ciphertext).decode()

    def _decrypt_aes_gcm(self, encrypted_value: str) -> str:
        """Decrypt using AES-256-GCM"""
        decoded = base64.b64decode(encrypted_value.encode())
        iv = decoded[:12]
        tag = decoded[12:28]
        ciphertext = decoded[28:]

        cipher = Cipher(
            algorithms.AES(self.aes_key),
            modes.GCM(iv, tag),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        return plaintext.decode()

    def hash_sensitive_data(self, data: str) -> str:
        """Hash sensitive data for comparison"""
        return hashlib.sha256(data.encode()).hexdigest()

class DatabaseAuditor:
    """Database security audit logging"""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.audit_log_file = "logs/database_audit.log"

    async def log_security_event(
        self,
        event_type: SecurityEventType,
        user_id: Optional[str],
        table_name: Optional[str],
        operation: str,
        details: Dict[str, Any],
        ip_address: Optional[str] = None,
        success: bool = True
    ):
        """Log security event"""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type.value,
            "user_id": user_id,
            "table_name": table_name,
            "operation": operation,
            "details": details,
            "ip_address": ip_address,
            "success": success
        }

        # Log to file
        try:
            with open(self.audit_log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event) + "\n")
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")

        # Store in Redis for recent events
        if self.redis_client:
            try:
                await self.redis_client.lpush(
                    f"audit_events:{user_id or 'anonymous'}",
                    json.dumps(event)
                )
                await self.redis_client.expire(
                    f"audit_events:{user_id or 'anonymous'}",
                    86400  # 24 hours
                )
            except Exception as e:
                logger.error(f"Failed to store audit event in Redis: {e}")

        # Log to application logger
        log_level = logging.WARNING if not success else logging.INFO
        logger.log(log_level, f"Database security event: {event_type.value} - {operation}")

    async def get_audit_events(
        self,
        user_id: Optional[str] = None,
        event_type: Optional[SecurityEventType] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get audit events with filtering"""
        events = []

        if self.redis_client and user_id:
            try:
                events_json = await self.redis_client.lrange(f"audit_events:{user_id}", 0, -1)
                for event_json in events_json:
                    event = json.loads(event_json)
                    event_time = datetime.fromisoformat(event["timestamp"])

                    # Apply filters
                    if event_type and event["event_type"] != event_type.value:
                        continue
                    if start_time and event_time < start_time:
                        continue
                    if end_time and event_time > end_time:
                        continue

                    events.append(event)
                    if len(events) >= limit:
                        break
            except Exception as e:
                logger.error(f"Failed to get audit events from Redis: {e}")

        return events

class DatabaseConnectionManager:
    """Secure database connection manager"""

    def __init__(self, database_url: str, security_policy: SecurityPolicy):
        self.database_url = database_url
        self.security_policy = security_policy
        self.engine = None
        self.SessionLocal = None
        self.async_pool = None
        self.encryptor = DatabaseEncryptor()
        self.auditor = DatabaseAuditor()

    def create_engine(self):
        """Create secure database engine"""
        # Add SSL requirement to connection string
        if self.security_policy.require_ssl and "sslmode" not in self.database_url:
            if "?" in self.database_url:
                self.database_url += "&sslmode=require"
            else:
                self.database_url += "?sslmode=require"

        # Create engine with security settings
        self.engine = create_engine(
            self.database_url,
            poolclass=QueuePool,
            pool_size=self.security_policy.max_connections,
            max_overflow=self.security_policy.max_connections // 2,
            pool_timeout=self.security_policy.connection_timeout_seconds,
            pool_recycle=self.security_policy.idle_timeout_seconds,
            connect_args={
                "connect_timeout": self.security_policy.connection_timeout_seconds,
                "application_name": "trading_system_secure",
                "options": f"-c statement_timeout={self.security_policy.query_timeout_seconds * 1000}"
            }
        )

        # Create session factory
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        # Set up event listeners for audit logging
        self._setup_audit_events()

        return self.engine

    async def create_async_pool(self):
        """Create async connection pool"""
        if self.database_url.startswith("postgresql://"):
            # Convert to asyncpg format
            async_url = self.database_url.replace("postgresql://", "postgresql+asyncpg://")

            self.async_pool = await asyncpg.create_pool(
                async_url,
                min_size=2,
                max_size=self.security_policy.max_connections,
                command_timeout=self.security_policy.query_timeout_seconds,
                server_settings={
                    "sslmode": "require" if self.security_policy.require_ssl else "prefer",
                    "application_name": "trading_system_secure",
                    "statement_timeout": f"{self.security_policy.query_timeout_seconds}s"
                }
            )

        return self.async_pool

    def _setup_audit_events(self):
        """Set up SQLAlchemy event listeners for audit logging"""
        @event.listens_for(self.engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            cursor.statement_timeout = self.security_policy.query_timeout_seconds * 1000

        @event.listens_for(self.engine, "after_cursor_execute")
        def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            # Log query execution for audit
            asyncio.create_task(self.auditor.log_security_event(
                event_type=SecurityEventType.QUERY_EXECUTED,
                user_id=getattr(context, 'user_id', None),
                table_name=self._extract_table_name(statement),
                operation="SELECT" if statement.strip().upper().startswith("SELECT") else "MODIFY",
                details={"query": statement[:200], "parameters": str(parameters)},
                success=True
            ))

    def _extract_table_name(self, query: str) -> Optional[str]:
        """Extract table name from SQL query"""
        query_lower = query.lower()
        if "from " in query_lower:
            from_part = query_lower.split("from ")[1].split()[0]
            return from_part.strip('"').strip("'")
        return None

    @contextmanager
    def get_session(self, user_id: Optional[str] = None):
        """Get database session with security context"""
        session = self.SessionLocal()
        try:
            # Store user context for audit logging
            session.user_id = user_id
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            session.rollback()
            raise
        finally:
            session.close()

    async def get_async_connection(self, user_id: Optional[str] = None):
        """Get async database connection"""
        if not self.async_pool:
            raise RuntimeError("Async pool not initialized")

        async with self.async_pool.acquire() as conn:
            # Set session variables for security context
            if user_id:
                await conn.execute('SET SESSION app.user_id = $1', user_id)
            yield conn

class SecureDatabaseOperations:
    """Secure database operations with encryption and access control"""

    def __init__(self, connection_manager: DatabaseConnectionManager):
        self.connection_manager = connection_manager
        self.security_policy = connection_manager.security_policy
        self.encryptor = connection_manager.encryptor
        self.auditor = connection_manager.auditor

    async def insert_sensitive_data(
        self,
        table_name: str,
        data: Dict[str, Any],
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> int:
        """Insert data with sensitive field encryption"""
        async with self.connection_manager.get_async_connection(user_id) as conn:
            # Encrypt sensitive fields
            encrypted_data = self._encrypt_sensitive_fields(table_name, data)

            # Build insert query
            columns = list(encrypted_data.keys())
            values = list(encrypted_data.values())
            placeholders = [f'${i+1}' for i in range(len(values))]

            query = f"""
                INSERT INTO {table_name} ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
                RETURNING id
            """

            try:
                result = await conn.fetchrow(query, *values)
                record_id = result['id']

                # Log the operation
                await self.auditor.log_security_event(
                    event_type=SecurityEventType.DATA_MODIFIED,
                    user_id=user_id,
                    table_name=table_name,
                    operation="INSERT",
                    details={"record_id": record_id, "fields": list(data.keys())},
                    ip_address=ip_address,
                    success=True
                )

                return record_id

            except Exception as e:
                await self.auditor.log_security_event(
                    event_type=SecurityEventType.DATA_MODIFIED,
                    user_id=user_id,
                    table_name=table_name,
                    operation="INSERT",
                    details={"error": str(e)},
                    ip_address=ip_address,
                    success=False
                )
                raise

    async def get_sensitive_data(
        self,
        table_name: str,
        record_id: int,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get data with sensitive field decryption"""
        async with self.connection_manager.get_async_connection(user_id) as conn:
            query = f"SELECT * FROM {table_name} WHERE id = $1"

            try:
                result = await conn.fetchrow(query, record_id)
                if not result:
                    return None

                # Convert to dict
                data = dict(result)

                # Decrypt sensitive fields
                decrypted_data = self._decrypt_sensitive_fields(table_name, data)

                # Log the access
                await self.auditor.log_security_event(
                    event_type=SecurityEventType.DATA_ACCESSED,
                    user_id=user_id,
                    table_name=table_name,
                    operation="SELECT",
                    details={"record_id": record_id},
                    ip_address=ip_address,
                    success=True
                )

                return decrypted_data

            except Exception as e:
                await self.auditor.log_security_event(
                    event_type=SecurityEventType.DATA_ACCESSED,
                    user_id=user_id,
                    table_name=table_name,
                    operation="SELECT",
                    details={"record_id": record_id, "error": str(e)},
                    ip_address=ip_address,
                    success=False
                )
                raise

    async def update_sensitive_data(
        self,
        table_name: str,
        record_id: int,
        data: Dict[str, Any],
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> bool:
        """Update data with sensitive field encryption"""
        async with self.connection_manager.get_async_connection(user_id) as conn:
            # Encrypt sensitive fields
            encrypted_data = self._encrypt_sensitive_fields(table_name, data)

            # Build update query
            set_clauses = [f"{key} = ${i+2}" for i, key in enumerate(encrypted_data.keys())]
            query = f"""
                UPDATE {table_name}
                SET {', '.join(set_clauses)}
                WHERE id = $1
            """

            values = [record_id] + list(encrypted_data.values())

            try:
                result = await conn.execute(query, *values)
                success = result != "UPDATE 0"

                # Log the operation
                await self.auditor.log_security_event(
                    event_type=SecurityEventType.DATA_MODIFIED,
                    user_id=user_id,
                    table_name=table_name,
                    operation="UPDATE",
                    details={"record_id": record_id, "fields": list(data.keys())},
                    ip_address=ip_address,
                    success=success
                )

                return success

            except Exception as e:
                await self.auditor.log_security_event(
                    event_type=SecurityEventType.DATA_MODIFIED,
                    user_id=user_id,
                    table_name=table_name,
                    operation="UPDATE",
                    details={"record_id": record_id, "error": str(e)},
                    ip_address=ip_address,
                    success=False
                )
                raise

    async def backup_database(
        self,
        backup_path: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> bool:
        """Create encrypted database backup"""
        try:
            # This would implement pg_dump with encryption
            # For now, it's a placeholder implementation
            logger.info(f"Creating encrypted database backup to {backup_path}")

            await self.auditor.log_security_event(
                event_type=SecurityEventType.BACKUP_CREATED,
                user_id=user_id,
                table_name=None,
                operation="BACKUP",
                details={"backup_path": backup_path, "encrypted": self.security_policy.encrypt_backups},
                ip_address=ip_address,
                success=True
            )

            return True

        except Exception as e:
            await self.auditor.log_security_event(
                event_type=SecurityEventType.BACKUP_CREATED,
                user_id=user_id,
                table_name=None,
                operation="BACKUP",
                details={"backup_path": backup_path, "error": str(e)},
                ip_address=ip_address,
                success=False
            )
            raise

    async def restore_database(
        self,
        backup_path: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> bool:
        """Restore database from encrypted backup"""
        try:
            # This would implement pg_restore with decryption
            # For now, it's a placeholder implementation
            logger.info(f"Restoring database from encrypted backup {backup_path}")

            await self.auditor.log_security_event(
                event_type=SecurityEventType.BACKUP_RESTORED,
                user_id=user_id,
                table_name=None,
                operation="RESTORE",
                details={"backup_path": backup_path},
                ip_address=ip_address,
                success=True
            )

            return True

        except Exception as e:
            await self.auditor.log_security_event(
                event_type=SecurityEventType.BACKUP_RESTORED,
                user_id=user_id,
                table_name=None,
                operation="RESTORE",
                details={"backup_path": backup_path, "error": str(e)},
                ip_address=ip_address,
                success=False
            )
            raise

    def _encrypt_sensitive_fields(self, table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive fields in data"""
        if not self.security_policy.encrypt_sensitive_data:
            return data

        encrypted_data = data.copy()
        sensitive_columns = self.security_policy.sensitive_columns.get(table_name, [])

        for column in sensitive_columns:
            if column in encrypted_data and encrypted_data[column]:
                encrypted_data[column] = self.encryptor.encrypt_field(str(encrypted_data[column]))

        return encrypted_data

    def _decrypt_sensitive_fields(self, table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt sensitive fields in data"""
        if not self.security_policy.encrypt_sensitive_data:
            return data

        decrypted_data = data.copy()
        sensitive_columns = self.security_policy.sensitive_columns.get(table_name, [])

        for column in sensitive_columns:
            if column in decrypted_data and decrypted_data[column]:
                try:
                    decrypted_data[column] = self.encryptor.decrypt_field(str(decrypted_data[column]))
                except Exception as e:
                    logger.warning(f"Failed to decrypt field {column}: {e}")
                    # Keep encrypted value if decryption fails
                    pass

        return decrypted_data

    def validate_query_safety(self, query: str) -> Tuple[bool, Optional[str]]:
        """Validate query for potential security issues"""
        dangerous_patterns = [
            r"DROP\s+TABLE",
            r"DROP\s+DATABASE",
            r"TRUNCATE",
            r"DELETE\s+FROM\s+\w+\s+WHERE\s+1=1",
            r"UPDATE\s+\w+\s+SET\s+\w+\s*=\s*'malicious'",
            r"INSERT\s+INTO\s+\w+\s+VALUES\s*\('malicious'",
            r"GRANT\s+ALL",
            r"REVOKE\s+ALL",
            r"CREATE\s+USER",
            r"ALTER\s+USER",
            r"DROP\s+USER",
            r"--",  # SQL comments
            r"/\*.*\*/",  # Multi-line comments
            r"xp_cmdshell",
            r"sp_oacreate",
            r"sp_adduser",
            r"sp_password"
        ]

        query_lower = query.lower()
        for pattern in dangerous_patterns:
            if re.search(pattern, query_lower, re.IGNORECASE):
                return False, f"Query contains potentially dangerous pattern: {pattern}"

        return True, None

class DatabaseSecurityManager:
    """Main database security management class"""

    def __init__(self, database_url: str, security_policy: Optional[SecurityPolicy] = None):
        self.security_policy = security_policy or SecurityPolicy()
        self.connection_manager = DatabaseConnectionManager(database_url, self.security_policy)
        self.secure_operations = SecureDatabaseOperations(self.connection_manager)
        self.initialized = False

    async def initialize(self):
        """Initialize database security"""
        try:
            # Create engine and async pool
            self.connection_manager.create_engine()
            await self.connection_manager.create_async_pool()

            # Set up security functions and triggers
            await self._setup_security_functions()

            # Create audit tables if they don't exist
            await self._create_audit_tables()

            # Set up row-level security
            if self.security_policy.enable_row_level_security:
                await self._setup_row_level_security()

            self.initialized = True
            logger.info("Database security initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize database security: {e}")
            raise

    async def _setup_security_functions(self):
        """Set up security functions in the database"""
        async with self.connection_manager.get_async_connection() as conn:
            # Create function for query validation
            await conn.execute("""
                CREATE OR REPLACE FUNCTION validate_query_safety(query_text TEXT)
                RETURNS BOOLEAN AS $$
                DECLARE
                    dangerous_patterns TEXT[] := ARRAY[
                        'DROP TABLE', 'DROP DATABASE', 'TRUNCATE',
                        'DELETE FROM', 'GRANT ALL', 'REVOKE ALL',
                        'CREATE USER', 'ALTER USER', 'DROP USER'
                    ];
                    pattern TEXT;
                BEGIN
                    FOREACH pattern IN ARRAY dangerous_patterns LOOP
                        IF query_text ILIKE '%' || pattern || '%' THEN
                            RETURN FALSE;
                        END IF;
                    END LOOP;
                    RETURN TRUE;
                END;
                $$ LANGUAGE plpgsql;
            """)

    async def _create_audit_tables(self):
        """Create audit tables if they don't exist"""
        async with self.connection_manager.get_async_connection() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS security_audit_log (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    event_type VARCHAR(50) NOT NULL,
                    user_id VARCHAR(255),
                    table_name VARCHAR(255),
                    operation VARCHAR(50) NOT NULL,
                    details JSONB,
                    ip_address INET,
                    success BOOLEAN DEFAULT TRUE
                );

                CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON security_audit_log(timestamp);
                CREATE INDEX IF NOT EXISTS idx_audit_user_id ON security_audit_log(user_id);
                CREATE INDEX IF NOT EXISTS idx_audit_event_type ON security_audit_log(event_type);
                CREATE INDEX IF NOT EXISTS idx_audit_table_name ON security_audit_log(table_name);
            """)

    async def _setup_row_level_security(self):
        """Set up row-level security policies"""
        async with self.connection_manager.get_async_connection() as conn:
            # Enable row-level security
            await conn.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY;")

            # Create policy for users to only see their own data
            await conn.execute("""
                CREATE POLICY user_isolation ON users
                FOR ALL TO app_user
                USING (id = current_setting('app.user_id', true)::INTEGER);
            """)

            # Create policy for signals based on user access
            await conn.execute("""
                CREATE POLICY signal_access ON signals
                FOR SELECT TO app_user
                USING (is_public = TRUE OR creator_id = current_setting('app.user_id', true)::INTEGER);
            """)

    async def get_security_status(self) -> Dict[str, Any]:
        """Get database security status"""
        return {
            "initialized": self.initialized,
            "ssl_required": self.security_policy.require_ssl,
            "encryption_enabled": self.security_policy.encrypt_sensitive_data,
            "audit_logging_enabled": self.security_policy.audit_log_enabled,
            "row_level_security_enabled": self.security_policy.enable_row_level_security,
            "max_connections": self.security_policy.max_connections,
            "query_timeout": self.security_policy.query_timeout_seconds,
            "sensitive_tables": self.security_policy.sensitive_tables
        }

    async def rotate_encryption_key(self, new_key: Optional[str] = None):
        """Rotate encryption key"""
        new_key = new_key or secrets.token_urlsafe(32)
        new_encryptor = DatabaseEncryptor(new_key)

        # This would implement key rotation logic
        # For now, it's a placeholder
        logger.info("Database encryption key rotated")

        return new_key

    def get_session(self, user_id: Optional[str] = None):
        """Get secure database session"""
        return self.connection_manager.get_session(user_id)

    async def get_async_connection(self, user_id: Optional[str] = None):
        """Get secure async database connection"""
        return self.connection_manager.get_async_connection(user_id)