"""
Comprehensive Secrets Management System
Production-ready secrets handling with encryption, rotation, and auditing
"""

import os
import json
import base64
import hashlib
import secrets
from typing import Dict, Any, List, Optional, Union, Set
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, asdict
import logging
from abc import ABC, abstractmethod

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecretType(str, Enum):
    """Types of secrets"""
    API_KEY = "api_key"
    DATABASE_PASSWORD = "database_password"
    JWT_SECRET = "jwt_secret"
    ENCRYPTION_KEY = "encryption_key"
    CREDENTIAL = "credential"
    CERTIFICATE = "certificate"
    TOKEN = "token"
    OTHER = "other"

class SecretStatus(str, Enum):
    """Secret status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    COMPROMISED = "compromised"
    PENDING_ROTATION = "pending_rotation"
    ROTATED = "rotated"

class SecurityLevel(str, Enum):
    """Security levels for secrets"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    SECRET = "secret"
    TOP_SECRET = "top_secret"

@dataclass
class SecretMetadata:
    """Metadata for a secret"""
    key: str
    secret_type: SecretType
    security_level: SecurityLevel
    description: str
    owner: str
    created_at: datetime
    created_by: str
    expires_at: Optional[datetime] = None
    rotation_required: bool = False
    rotation_interval: Optional[timedelta] = None
    last_rotated: Optional[datetime] = None
    next_rotation: Optional[datetime] = None
    status: SecretStatus = SecretStatus.ACTIVE
    tags: List[str] = None
    access_count: int = 0
    last_accessed: Optional[datetime] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []

@dataclass
class SecretAuditLog:
    """Audit log entry for secret operations"""
    timestamp: datetime
    operation: str
    secret_key: str
    user: str
    ip_address: str
    user_agent: str
    success: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class SecretsProvider(ABC):
    """Abstract base class for secrets providers"""

    @abstractmethod
    def store_secret(self, key: str, value: Any, metadata: SecretMetadata) -> bool:
        """Store a secret"""
        pass

    @abstractmethod
    def get_secret(self, key: str) -> Optional[Any]:
        """Retrieve a secret"""
        pass

    @abstractmethod
    def delete_secret(self, key: str) -> bool:
        """Delete a secret"""
        pass

    @abstractmethod
    def list_secrets(self) -> List[str]:
        """List all secret keys"""
        pass

    @abstractmethod
    def rotate_secret(self, key: str, new_value: Any) -> bool:
        """Rotate a secret"""
        pass

class FileSecretsProvider(SecretsProvider):
    """File-based secrets provider with encryption"""

    def __init__(self, secrets_dir: Path = None, encryption_key: str = None):
        self.secrets_dir = secrets_dir or Path("secrets")
        self.secrets_dir.mkdir(exist_ok=True)
        self.encryption_key = encryption_key or os.getenv('SECRETS_ENCRYPTION_KEY')
        self.secrets_file = self.secrets_dir / "secrets.encrypted"
        self.metadata_file = self.secrets_dir / "metadata.json"
        self.audit_log_file = self.secrets_dir / "audit.log"

        # Initialize storage
        self._ensure_encryption_key()
        self._load_secrets()

    def _ensure_encryption_key(self):
        """Ensure encryption key is available"""
        if not self.encryption_key:
            # Generate a new encryption key
            self.encryption_key = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
            logger.warning(f"No encryption key provided, generated new key: {self.encryption_key[:16]}...")
            logger.warning("Store this key securely for future use")

    def _load_secrets(self):
        """Load secrets from storage"""
        self.secrets: Dict[str, str] = {}
        self.metadata: Dict[str, SecretMetadata] = {}

        try:
            if self.secrets_file.exists():
                with open(self.secrets_file, 'rb') as f:
                    encrypted_data = f.read()
                decrypted_data = self._decrypt(encrypted_data)
                self.secrets = json.loads(decrypted_data.decode())

            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    metadata_data = json.load(f)
                self.metadata = {
                    key: SecretMetadata(**metadata) for key, metadata in metadata_data.items()
                }
        except Exception as e:
            logger.error(f"Failed to load secrets: {e}")
            self.secrets = {}
            self.metadata = {}

    def _save_secrets(self):
        """Save secrets to storage"""
        try:
            # Save encrypted secrets
            with open(self.secrets_file, 'wb') as f:
                encrypted_data = self._encrypt(json.dumps(self.secrets).encode())
                f.write(encrypted_data)

            # Save metadata
            metadata_data = {
                key: asdict(metadata) for key, metadata in self.metadata.items()
            }
            # Convert datetime objects to strings for JSON serialization
            for key, metadata in metadata_data.items():
                for field in ['created_at', 'expires_at', 'last_rotated', 'next_rotation', 'last_accessed']:
                    if metadata.get(field):
                        metadata[field] = metadata[field].isoformat()

            with open(self.metadata_file, 'w') as f:
                json.dump(metadata_data, f, indent=2)

            # Set secure permissions
            os.chmod(self.secrets_file, 0o600)
            os.chmod(self.metadata_file, 0o600)
        except Exception as e:
            logger.error(f"Failed to save secrets: {e}")

    def _encrypt(self, data: bytes) -> bytes:
        """Encrypt data using the encryption key"""
        try:
            from cryptography.fernet import Fernet
            fernet = Fernet(self.encryption_key.encode())
            return fernet.encrypt(data)
        except ImportError:
            logger.warning("Cryptography not available, using base64 encoding")
            return base64.b64encode(data)

    def _decrypt(self, data: bytes) -> bytes:
        """Decrypt data using the encryption key"""
        try:
            from cryptography.fernet import Fernet
            fernet = Fernet(self.encryption_key.encode())
            return fernet.decrypt(data)
        except ImportError:
            logger.warning("Cryptography not available, using base64 decoding")
            return base64.b64decode(data)

    def _log_audit(self, operation: str, secret_key: str, user: str, success: bool, error_message: str = None, metadata: Dict[str, Any] = None):
        """Log audit entry"""
        try:
            audit_entry = SecretAuditLog(
                timestamp=datetime.utcnow(),
                operation=operation,
                secret_key=secret_key,
                user=user,
                ip_address="127.0.0.1",  # In production, get from request
                user_agent="SecretsManager",  # In production, get from request
                success=success,
                error_message=error_message,
                metadata=metadata or {}
            )

            with open(self.audit_log_file, 'a') as f:
                # Convert to dict and handle datetime serialization
                audit_dict = asdict(audit_entry)
                audit_dict['timestamp'] = audit_dict['timestamp'].isoformat()
                f.write(json.dumps(audit_dict) + '\n')
        except Exception as e:
            logger.error(f"Failed to log audit entry: {e}")

    def store_secret(self, key: str, value: Any, metadata: SecretMetadata) -> bool:
        """Store a secret"""
        try:
            # Convert value to string for storage
            if not isinstance(value, str):
                value = json.dumps(value)

            # Store secret
            self.secrets[key] = value
            self.metadata[key] = metadata

            # Save to storage
            self._save_secrets()

            # Log audit entry
            self._log_audit("store", key, metadata.created_by, True)

            logger.info(f"Secret '{key}' stored successfully")
            return True
        except Exception as e:
            error_msg = f"Failed to store secret '{key}': {e}"
            logger.error(error_msg)
            self._log_audit("store", key, "system", False, error_msg)
            return False

    def get_secret(self, key: str, user: str = "system") -> Optional[Any]:
        """Retrieve a secret"""
        try:
            if key not in self.secrets:
                logger.warning(f"Secret '{key}' not found")
                self._log_audit("get", key, user, False, "Secret not found")
                return None

            # Check if secret is expired
            metadata = self.metadata[key]
            if metadata.expires_at and metadata.expires_at < datetime.utcnow():
                logger.error(f"Secret '{key}' has expired")
                self._log_audit("get", key, user, False, "Secret expired")
                return None

            # Check if secret is active
            if metadata.status != SecretStatus.ACTIVE:
                logger.error(f"Secret '{key}' is not active (status: {metadata.status})")
                self._log_audit("get", key, user, False, f"Secret not active: {metadata.status}")
                return None

            # Get secret value
            value = self.secrets[key]

            # Try to parse as JSON, return as string if not
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
            finally:
                # Update access metadata
                metadata.access_count += 1
                metadata.last_accessed = datetime.utcnow()
                self._save_secrets()

        except Exception as e:
            error_msg = f"Failed to retrieve secret '{key}': {e}"
            logger.error(error_msg)
            self._log_audit("get", key, user, False, error_msg)
            return None

    def delete_secret(self, key: str, user: str = "system") -> bool:
        """Delete a secret"""
        try:
            if key not in self.secrets:
                logger.warning(f"Secret '{key}' not found")
                self._log_audit("delete", key, user, False, "Secret not found")
                return False

            # Remove secret and metadata
            del self.secrets[key]
            del self.metadata[key]

            # Save changes
            self._save_secrets()

            # Log audit entry
            self._log_audit("delete", key, user, True)

            logger.info(f"Secret '{key}' deleted successfully")
            return True
        except Exception as e:
            error_msg = f"Failed to delete secret '{key}': {e}"
            logger.error(error_msg)
            self._log_audit("delete", key, user, False, error_msg)
            return False

    def list_secrets(self) -> List[str]:
        """List all secret keys"""
        return list(self.secrets.keys())

    def rotate_secret(self, key: str, new_value: Any, user: str = "system") -> bool:
        """Rotate a secret"""
        try:
            if key not in self.secrets:
                logger.error(f"Secret '{key}' not found for rotation")
                self._log_audit("rotate", key, user, False, "Secret not found")
                return False

            # Store old value for backup
            old_value = self.secrets[key]
            old_metadata = self.metadata[key]

            # Convert new value to string
            if not isinstance(new_value, str):
                new_value = json.dumps(new_value)

            # Create new metadata
            new_metadata = SecretMetadata(
                key=key,
                secret_type=old_metadata.secret_type,
                security_level=old_metadata.security_level,
                description=f"Rotated version of {key}",
                owner=old_metadata.owner,
                created_at=datetime.utcnow(),
                created_by=user,
                expires_at=old_metadata.expires_at,
                rotation_required=old_metadata.rotation_required,
                rotation_interval=old_metadata.rotation_interval,
                last_rotated=datetime.utcnow(),
                next_rotation=self._calculate_next_rotation(old_metadata.rotation_interval),
                status=SecretStatus.ACTIVE,
                tags=old_metadata.tags.copy()
            )

            # Store new secret
            self.secrets[key] = new_value
            self.metadata[key] = new_metadata

            # Save changes
            self._save_secrets()

            # Log audit entry
            self._log_audit("rotate", key, user, True, metadata={"old_value_hash": self._hash_value(old_value)})

            logger.info(f"Secret '{key}' rotated successfully")
            return True
        except Exception as e:
            error_msg = f"Failed to rotate secret '{key}': {e}"
            logger.error(error_msg)
            self._log_audit("rotate", key, user, False, error_msg)
            return False

    def _calculate_next_rotation(self, rotation_interval: timedelta) -> Optional[datetime]:
        """Calculate next rotation date"""
        if not rotation_interval:
            return None
        return datetime.utcnow() + rotation_interval

    def _hash_value(self, value: str) -> str:
        """Generate hash of secret value for audit logging"""
        return hashlib.sha256(value.encode()).hexdigest()

    def get_secret_metadata(self, key: str) -> Optional[SecretMetadata]:
        """Get metadata for a secret"""
        return self.metadata.get(key)

    def list_secrets_by_type(self, secret_type: SecretType) -> List[str]:
        """List secrets by type"""
        return [
            key for key, metadata in self.metadata.items()
            if metadata.secret_type == secret_type
        ]

    def list_secrets_by_security_level(self, security_level: SecurityLevel) -> List[str]:
        """List secrets by security level"""
        return [
            key for key, metadata in self.metadata.items()
            if metadata.security_level == security_level
        ]

    def get_expired_secrets(self) -> List[str]:
        """Get list of expired secrets"""
        now = datetime.utcnow()
        return [
            key for key, metadata in self.metadata.items()
            if metadata.expires_at and metadata.expires_at < now
        ]

    def get_secrets_needing_rotation(self) -> List[str]:
        """Get list of secrets needing rotation"""
        now = datetime.utcnow()
        return [
            key for key, metadata in self.metadata.items()
            if metadata.next_rotation and metadata.next_rotation < now
        ]

    def get_audit_logs(self, secret_key: str = None, start_date: datetime = None, end_date: datetime = None) -> List[SecretAuditLog]:
        """Get audit logs with optional filtering"""
        try:
            logs = []
            with open(self.audit_log_file, 'r') as f:
                for line in f:
                    log_data = json.loads(line.strip())
                    audit_entry = SecretAuditLog(**log_data)

                    # Apply filters
                    if secret_key and audit_entry.secret_key != secret_key:
                        continue
                    if start_date and audit_entry.timestamp < start_date:
                        continue
                    if end_date and audit_entry.timestamp > end_date:
                        continue

                    logs.append(audit_entry)

            return sorted(logs, key=lambda x: x.timestamp, reverse=True)
        except Exception as e:
            logger.error(f"Failed to get audit logs: {e}")
            return []

    def backup_secrets(self, backup_path: Path = None) -> bool:
        """Backup secrets to a secure location"""
        try:
            if not backup_path:
                timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                backup_path = self.secrets_dir / f"backup_{timestamp}"

            backup_path.mkdir(exist_ok=True)

            # Backup secrets file
            if self.secrets_file.exists():
                shutil.copy2(self.secrets_file, backup_path / self.secrets_file.name)

            # Backup metadata file
            if self.metadata_file.exists():
                shutil.copy2(self.metadata_file, backup_path / self.metadata_file.name)

            # Backup audit log
            if self.audit_log_file.exists():
                shutil.copy2(self.audit_log_file, backup_path / self.audit_log_file.name)

            # Set secure permissions
            for file_path in backup_path.iterdir():
                os.chmod(file_path, 0o600)

            logger.info(f"Secrets backed up to: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to backup secrets: {e}")
            return False

    def restore_secrets(self, backup_path: Path) -> bool:
        """Restore secrets from backup"""
        try:
            if not backup_path.exists():
                logger.error(f"Backup path does not exist: {backup_path}")
                return False

            # Restore secrets file
            secrets_backup = backup_path / self.secrets_file.name
            if secrets_backup.exists():
                shutil.copy2(secrets_backup, self.secrets_file)

            # Restore metadata file
            metadata_backup = backup_path / self.metadata_file.name
            if metadata_backup.exists():
                shutil.copy2(metadata_backup, self.metadata_file)

            # Restore audit log
            audit_backup = backup_path / self.audit_log_file.name
            if audit_backup.exists():
                shutil.copy2(audit_backup, self.audit_log_file)

            # Reload secrets
            self._load_secrets()

            logger.info(f"Secrets restored from: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to restore secrets: {e}")
            return False

class SecretsManager:
    """Main secrets management system"""

    def __init__(self, provider: SecretsProvider = None):
        self.provider = provider or FileSecretsProvider()
        self.cache: Dict[str, Any] = {}
        self.cache_ttl = 300  # 5 minutes

    def store_secret(self, key: str, value: Any, secret_type: SecretType = SecretType.OTHER,
                    security_level: SecurityLevel = SecurityLevel.SECRET,
                    description: str = "", owner: str = "system",
                    expires_at: datetime = None, rotation_interval: timedelta = None,
                    user: str = "system", tags: List[str] = None) -> bool:
        """Store a secret with metadata"""
        metadata = SecretMetadata(
            key=key,
            secret_type=secret_type,
            security_level=security_level,
            description=description,
            owner=owner,
            created_at=datetime.utcnow(),
            created_by=user,
            expires_at=expires_at,
            rotation_required=rotation_interval is not None,
            rotation_interval=rotation_interval,
            next_rotation=self._calculate_next_rotation(rotation_interval),
            tags=tags or []
        )

        return self.provider.store_secret(key, value, metadata)

    def get_secret(self, key: str, user: str = "system", use_cache: bool = True) -> Optional[Any]:
        """Retrieve a secret with caching"""
        # Check cache first
        if use_cache and key in self.cache:
            cached_value, cache_time = self.cache[key]
            if datetime.utcnow() - cache_time < timedelta(seconds=self.cache_ttl):
                return cached_value

        # Get from provider
        value = self.provider.get_secret(key, user)

        # Cache the result
        if value is not None and use_cache:
            self.cache[key] = (value, datetime.utcnow())

        return value

    def delete_secret(self, key: str, user: str = "system") -> bool:
        """Delete a secret"""
        # Remove from cache
        self.cache.pop(key, None)
        return self.provider.delete_secret(key, user)

    def rotate_secret(self, key: str, new_value: Any = None, user: str = "system") -> bool:
        """Rotate a secret"""
        # If no new value provided, generate one based on secret type
        if new_value is None:
            new_value = self._generate_secret_value(key)

        # Clear cache
        self.cache.pop(key, None)

        return self.provider.rotate_secret(key, new_value, user)

    def _generate_secret_value(self, key: str) -> str:
        """Generate a new secret value based on the secret type"""
        metadata = self.provider.get_secret_metadata(key)
        if not metadata:
            return secrets.token_urlsafe(32)

        if metadata.secret_type == SecretType.JWT_SECRET:
            return secrets.token_urlsafe(32)
        elif metadata.secret_type == SecretType.API_KEY:
            return f"sk_{secrets.token_urlsafe(32)}"
        elif metadata.secret_type == SecretType.DATABASE_PASSWORD:
            return secrets.token_urlsafe(16)
        elif metadata.secret_type == SecretType.ENCRYPTION_KEY:
            return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
        else:
            return secrets.token_urlsafe(32)

    def _calculate_next_rotation(self, rotation_interval: timedelta) -> Optional[datetime]:
        """Calculate next rotation date"""
        if not rotation_interval:
            return None
        return datetime.utcnow() + rotation_interval

    def list_secrets(self) -> List[str]:
        """List all secrets"""
        return self.provider.list_secrets()

    def get_secret_metadata(self, key: str) -> Optional[SecretMetadata]:
        """Get metadata for a secret"""
        return self.provider.get_secret_metadata(key)

    def clear_cache(self):
        """Clear the secrets cache"""
        self.cache.clear()

    def health_check(self) -> Dict[str, Any]:
        """Perform health check on secrets manager"""
        try:
            total_secrets = len(self.provider.list_secrets())
            expired_secrets = len(self.provider.get_expired_secrets())
            needs_rotation = len(self.provider.get_secrets_needing_rotation())

            return {
                "status": "healthy",
                "total_secrets": total_secrets,
                "expired_secrets": expired_secrets,
                "secrets_needing_rotation": needs_rotation,
                "cache_size": len(self.cache),
                "cache_ttl": self.cache_ttl,
                "provider_type": type(self.provider).__name__
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    def rotate_expired_secrets(self, user: str = "system") -> Dict[str, bool]:
        """Rotate all expired secrets"""
        expired_secrets = self.provider.get_expired_secrets()
        results = {}

        for secret_key in expired_secrets:
            results[secret_key] = self.rotate_secret(secret_key, user=user)

        return results

    def backup_secrets(self, backup_path: Path = None) -> bool:
        """Backup all secrets"""
        return self.provider.backup_secrets(backup_path)

    def restore_secrets(self, backup_path: Path) -> bool:
        """Restore secrets from backup"""
        self.clear_cache()
        return self.provider.restore_secrets(backup_path)

# Global secrets manager instance
secrets_manager = SecretsManager()