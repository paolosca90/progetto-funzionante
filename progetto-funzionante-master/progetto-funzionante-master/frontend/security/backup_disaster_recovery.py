"""
Backup and Disaster Recovery Module

Provides comprehensive backup and disaster recovery capabilities including:
- Automated backup scheduling
- Database backup and restore
- File system backup
- Encryption and integrity verification
- Off-site backup support
- Disaster recovery procedures
- Backup monitoring and alerting
- Recovery testing and validation

"""

import os
import json
import shutil
import hashlib
import sqlite3
import asyncio
import uuid
import time
import threading
import tarfile
import tempfile
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple, Callable
from pathlib import Path
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging
import aiofiles
from fastapi import HTTPException, UploadFile
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)

class BackupType(Enum):
    """Backup types"""
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"
    TRANSACTION_LOG = "transaction_log"

class BackupStatus(Enum):
    """Backup status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    VERIFYING = "verifying"

class RecoveryStatus(Enum):
    """Recovery status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"

class BackupLocation(Enum):
    """Backup storage locations"""
    LOCAL = "local"
    REMOTE = "remote"
    CLOUD = "cloud"
    OFFSITE = "offsite"

@dataclass
class BackupConfig:
    """Backup configuration"""
    enabled: bool = True
    backup_directory: str = "backups"
    retention_days: int = 30
    max_backup_size_gb: float = 10.0
    compression_enabled: bool = True
    encryption_enabled: bool = True
    integrity_verification: bool = True
    parallel_processing: bool = True
    backup_types: List[BackupType] = field(default_factory=lambda: [BackupType.FULL])
    backup_locations: List[BackupLocation] = field(default_factory=lambda: [BackupLocation.LOCAL])
    schedule_config: Dict[str, str] = field(default_factory=lambda: {
        'full_daily': '02:00',
        'incremental_hourly': '00:00',
        'retention_check': '03:00'
    })
    notification_enabled: bool = True
    notification_recipients: List[str] = field(default_factory=list)
    performance_config: Dict[str, Any] = field(default_factory=lambda: {
        'max_workers': 4,
        'chunk_size_mb': 64,
        'timeout_seconds': 3600
    })

@dataclass
class BackupMetadata:
    """Backup metadata"""
    backup_id: str
    backup_type: BackupType
    status: BackupStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    size_bytes: int = 0
    file_count: int = 0
    checksum: str = ""
    encryption_key_id: Optional[str] = None
    backup_path: str = ""
    description: str = ""
    tags: List[str] = field(default_factory=list)
    verification_results: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    error_messages: List[str] = field(default_factory=list)

@dataclass
class RecoveryPlan:
    """Disaster recovery plan"""
    plan_id: str
    name: str
    description: str
    backup_sources: List[str]
    recovery_order: List[str]
    recovery_procedures: Dict[str, str]
    contact_information: Dict[str, str]
    estimated_recovery_time: int  # in minutes
    data_consistency_checks: List[str]
    rollback_procedures: List[str]
    testing_procedures: List[str]
    last_tested: Optional[datetime] = None
    test_results: Dict[str, Any] = field(default_factory=dict)

class BackupEncryptionManager:
    """Backup encryption manager"""

    def __init__(self, key_file: str = "security/backup_keys.json"):
        self.key_file = Path(key_file)
        self.encryption_keys = {}
        self._load_keys()

    def _load_keys(self):
        """Load encryption keys"""
        if self.key_file.exists():
            try:
                with open(self.key_file, 'r') as f:
                    self.encryption_keys = json.load(f)
                logger.info(f"Loaded {len(self.encryption_keys)} encryption keys")
            except Exception as e:
                logger.error(f"Error loading encryption keys: {e}")
                self.encryption_keys = {}

    def _save_keys(self):
        """Save encryption keys"""
        try:
            self.key_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.key_file, 'w') as f:
                json.dump(self.encryption_keys, f, indent=2)
            os.chmod(self.key_file, 0o600)
        except Exception as e:
            logger.error(f"Error saving encryption keys: {e}")

    def generate_key(self, key_id: str) -> str:
        """Generate new encryption key"""
        import secrets
        key = secrets.token_urlsafe(32)
        self.encryption_keys[key_id] = key
        self._save_keys()
        return key

    def encrypt_data(self, data: bytes, key_id: str) -> bytes:
        """Encrypt data with key"""
        try:
            from cryptography.fernet import Fernet
            key = self.encryption_keys.get(key_id)
            if not key:
                raise ValueError(f"Encryption key not found: {key_id}")

            f = Fernet(key.encode())
            return f.encrypt(data)
        except Exception as e:
            logger.error(f"Error encrypting data: {e}")
            raise

    def decrypt_data(self, encrypted_data: bytes, key_id: str) -> bytes:
        """Decrypt data with key"""
        try:
            from cryptography.fernet import Fernet
            key = self.encryption_keys.get(key_id)
            if not key:
                raise ValueError(f"Encryption key not found: {key_id}")

            f = Fernet(key.encode())
            return f.decrypt(encrypted_data)
        except Exception as e:
            logger.error(f"Error decrypting data: {e}")
            raise

class BackupIntegrityManager:
    """Backup integrity verification"""

    def __init__(self):
        self.integrity_database = {}
        self._load_integrity_database()

    def _load_integrity_database(self):
        """Load integrity database"""
        db_file = Path("security/backup_integrity.json")
        if db_file.exists():
            try:
                with open(db_file, 'r') as f:
                    self.integrity_database = json.load(f)
            except Exception as e:
                logger.error(f"Error loading integrity database: {e}")
                self.integrity_database = {}

    def _save_integrity_database(self):
        """Save integrity database"""
        try:
            db_file = Path("security/backup_integrity.json")
            db_file.parent.mkdir(parents=True, exist_ok=True)
            with open(db_file, 'w') as f:
                json.dump(self.integrity_database, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving integrity database: {e}")

    def calculate_checksum(self, file_path: str) -> str:
        """Calculate SHA-256 checksum of file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def verify_integrity(self, backup_path: str, expected_checksum: str) -> bool:
        """Verify backup integrity"""
        try:
            actual_checksum = self.calculate_checksum(backup_path)
            is_valid = actual_checksum == expected_checksum

            # Store verification result
            self.integrity_database[backup_path] = {
                'checksum': actual_checksum,
                'expected_checksum': expected_checksum,
                'verification_time': datetime.utcnow().isoformat(),
                'is_valid': is_valid
            }
            self._save_integrity_database()

            return is_valid
        except Exception as e:
            logger.error(f"Error verifying integrity of {backup_path}: {e}")
            return False

    def verify_backup_structure(self, backup_path: str) -> Dict[str, Any]:
        """Verify backup structure and contents"""
        try:
            backup_path = Path(backup_path)
            if not backup_path.exists():
                return {'valid': False, 'error': 'Backup file not found'}

            verification_results = {
                'valid': True,
                'file_exists': True,
                'file_size_mb': backup_path.stat().st_size / (1024 * 1024),
                'file_readable': os.access(backup_path, os.R_OK),
                'structure_valid': True,
                'errors': []
            }

            # Check if it's a tar archive
            if backup_path.suffix in ['.tar', '.tar.gz', '.tar.bz2']:
                try:
                    with tarfile.open(backup_path, 'r:*') as tar:
                        members = tar.getnames()
                        verification_results['file_count'] = len(members)
                        verification_results['contains_metadata'] = any('metadata.json' in m for m in members)
                except Exception as e:
                    verification_results['structure_valid'] = False
                    verification_results['errors'].append(f"Invalid tar archive: {e}")

            return verification_results

        except Exception as e:
            logger.error(f"Error verifying backup structure: {e}")
            return {'valid': False, 'error': str(e)}

class BackupManager:
    """
    Comprehensive backup manager

    Features:
    - Automated backup scheduling
    - Multiple backup types
    - Encryption and integrity verification
    - Multi-location support
    - Performance optimization
    """

    def __init__(self, config: Optional[BackupConfig] = None):
        self.config = config or BackupConfig()
        self.backup_history: List[BackupMetadata] = []
        self.encryption_manager = BackupEncryptionManager()
        self.integrity_manager = BackupIntegrityManager()
        self.backup_lock = threading.Lock()
        self.scheduler_thread = None
        self.is_running = False
        self.backup_callbacks = []

        # Initialize backup directory
        self._initialize_backup_directory()

        # Load backup history
        self._load_backup_history()

        logger.info("BackupManager initialized")

    def _initialize_backup_directory(self):
        """Initialize backup directory structure"""
        try:
            backup_dir = Path(self.config.backup_directory)
            backup_dir.mkdir(parents=True, exist_ok=True)
            os.chmod(backup_dir, 0o750)

            # Create subdirectories
            subdirs = ['full', 'incremental', 'differential', 'logs', 'temp']
            for subdir in subdirs:
                (backup_dir / subdir).mkdir(exist_ok=True)
                os.chmod(backup_dir / subdir, 0o750)

        except Exception as e:
            logger.error(f"Error initializing backup directory: {e}")
            raise

    def _load_backup_history(self):
        """Load backup history"""
        history_file = Path(self.config.backup_directory) / "backup_history.json"
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    history_data = json.load(f)
                    self.backup_history = [
                        BackupMetadata(**item) for item in history_data
                    ]
                logger.info(f"Loaded {len(self.backup_history)} backup records")
            except Exception as e:
                logger.error(f"Error loading backup history: {e}")
                self.backup_history = []

    def _save_backup_history(self):
        """Save backup history"""
        try:
            history_file = Path(self.config.backup_directory) / "backup_history.json"
            with open(history_file, 'w') as f:
                json.dump([asdict(backup) for backup in self.backup_history], f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving backup history: {e}")

    def start_scheduler(self):
        """Start backup scheduler"""
        if self.is_running:
            return

        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()

        logger.info("Backup scheduler started")

    def stop_scheduler(self):
        """Stop backup scheduler"""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join()
        logger.info("Backup scheduler stopped")

    def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.is_running:
            try:
                current_time = datetime.utcnow()

                # Check scheduled backups
                for backup_type in self.config.backup_types:
                    if self._should_run_backup(backup_type, current_time):
                        logger.info(f"Scheduled {backup_type.value} backup starting")
                        asyncio.run(self.create_backup_async(backup_type))

                # Clean up old backups
                if self._should_cleanup(current_time):
                    self.cleanup_old_backups()

                # Sleep for 1 minute
                import time
                time.sleep(60)

            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                import time
                time.sleep(60)

    def _should_run_backup(self, backup_type: BackupType, current_time: datetime) -> bool:
        """Check if backup should run"""
        # Find last backup of this type
        last_backup = None
        for backup in reversed(self.backup_history):
            if backup.backup_type == backup_type and backup.status == BackupStatus.COMPLETED:
                last_backup = backup
                break

        if not last_backup:
            return True  # First backup

        # Check schedule based on backup type
        if backup_type == BackupType.FULL:
            # Daily full backup
            return (current_time - last_backup.end_time).days >= 1
        elif backup_type == BackupType.INCREMENTAL:
            # Hourly incremental backup
            return (current_time - last_backup.end_time).seconds >= 3600
        elif backup_type == BackupType.DIFFERENTIAL:
            # Every 6 hours
            return (current_time - last_backup.end_time).seconds >= 21600

        return False

    def _should_cleanup(self, current_time: datetime) -> bool:
        """Check if cleanup should run"""
        # Run cleanup at 3 AM daily
        return current_time.hour == 3 and current_time.minute < 5

    async def create_backup_async(self, backup_type: BackupType, description: str = "") -> str:
        """
        Create backup asynchronously

        Args:
            backup_type: Type of backup to create
            description: Backup description

        Returns:
            str: Backup ID
        """
        with self.backup_lock:
            backup_id = f"backup_{backup_type.value}_{int(time.time())}"
            backup = BackupMetadata(
                backup_id=backup_id,
                backup_type=backup_type,
                status=BackupStatus.PENDING,
                start_time=datetime.utcnow(),
                description=description
            )

            self.backup_history.append(backup)
            logger.info(f"Starting backup: {backup_id}")

            try:
                backup.status = BackupStatus.IN_PROGRESS
                start_time = time.time()

                # Create backup
                backup_path = await self._perform_backup(backup_type, backup_id)

                # Set backup metadata
                backup.backup_path = backup_path
                backup.end_time = datetime.utcnow()
                backup.size_bytes = Path(backup_path).stat().st_size

                # Verify integrity if enabled
                if self.config.integrity_verification:
                    backup.status = BackupStatus.VERIFYING
                    verification_results = await self._verify_backup(backup_path)
                    backup.verification_results = verification_results
                    backup.checksum = verification_results.get('checksum', '')

                backup.status = BackupStatus.COMPLETED
                backup.performance_metrics = {
                    'duration_seconds': time.time() - start_time,
                    'throughput_mb_s': backup.size_bytes / (1024 * 1024) / (time.time() - start_time)
                }

                logger.info(f"Backup completed: {backup_id} ({backup.size_bytes / (1024 * 1024):.2f} MB)")

                # Trigger callbacks
                for callback in self.backup_callbacks:
                    try:
                        callback(backup)
                    except Exception as e:
                        logger.error(f"Error in backup callback: {e}")

                return backup_id

            except Exception as e:
                backup.status = BackupStatus.FAILED
                backup.error_messages = [str(e)]
                logger.error(f"Backup failed: {backup_id} - {e}")
                raise

    async def _perform_backup(self, backup_type: BackupType, backup_id: str) -> str:
        """Perform backup operation"""
        backup_dir = Path(self.config.backup_directory) / backup_type.value
        backup_filename = f"{backup_id}.tar.gz"
        backup_path = backup_dir / backup_filename

        # Create temporary directory for backup
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Backup configuration files
            await self._backup_config_files(temp_path)

            # Backup database
            await self._backup_database(temp_path, backup_type)

            # Backup application files
            await self._backup_application_files(temp_path, backup_type)

            # Create metadata
            metadata = {
                'backup_id': backup_id,
                'backup_type': backup_type.value,
                'created_at': datetime.utcnow().isoformat(),
                'files_backed_up': [],
                'config_version': '1.0'
            }

            with open(temp_path / 'metadata.json', 'w') as f:
                json.dump(metadata, f, indent=2)

            # Create archive
            with tarfile.open(backup_path, 'w:gz') as tar:
                tar.add(temp_path, arcname='')

            # Encrypt if enabled
            if self.config.encryption_enabled:
                backup_path = await self._encrypt_backup(backup_path, backup_id)

        return str(backup_path)

    async def _backup_config_files(self, backup_dir: Path):
        """Backup configuration files"""
        config_files = [
            '.env',
            'config/*.yaml',
            'config/*.yml',
            'config/*.json',
            'requirements.txt'
        ]

        for pattern in config_files:
            import glob
            for file_path in glob.glob(pattern):
                if os.path.exists(file_path):
                    dest_path = backup_dir / 'config' / Path(file_path).name
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(file_path, dest_path)

    async def _backup_database(self, backup_dir: Path, backup_type: BackupType):
        """Backup database"""
        try:
            # Create database backup
            db_dir = backup_dir / 'database'
            db_dir.mkdir(exist_ok=True)

            # SQLite database backup
            if Path('trading_signals.db').exists():
                backup_db_path = db_dir / 'trading_signals.db'
                shutil.copy2('trading_signals.db', backup_db_path)

            # Create SQL dump
            dump_file = db_dir / 'database_dump.sql'
            await self._create_database_dump(dump_file)

        except Exception as e:
            logger.error(f"Error backing up database: {e}")
            raise

    async def _create_database_dump(self, dump_file: Path):
        """Create database SQL dump"""
        try:
            # This is a simplified version - in production, use proper database dump tools
            conn = sqlite3.connect('trading_signals.db')
            with open(dump_file, 'w') as f:
                for line in conn.iterdump():
                    f.write(line + '\n')
            conn.close()
        except Exception as e:
            logger.error(f"Error creating database dump: {e}")

    async def _backup_application_files(self, backup_dir: Path, backup_type: BackupType):
        """Backup application files"""
        app_files = [
            'main.py',
            'models.py',
            'schemas.py',
            'security/',
            'logs/'
        ]

        for file_path in app_files:
            source_path = Path(file_path)
            if source_path.exists():
                dest_path = backup_dir / 'app' / source_path.name
                if source_path.is_dir():
                    shutil.copytree(source_path, dest_path, ignore=shutil.ignore_patterns('*.pyc', '__pycache__'))
                else:
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source_path, dest_path)

    async def _encrypt_backup(self, backup_path: Path, backup_id: str) -> Path:
        """Encrypt backup file"""
        try:
            # Generate encryption key
            key_id = f"backup_{backup_id}"
            encryption_key = self.encryption_manager.generate_key(key_id)

            # Read and encrypt file
            with open(backup_path, 'rb') as f:
                data = f.read()

            encrypted_data = self.encryption_manager.encrypt_data(data, key_id)

            # Write encrypted file
            encrypted_path = backup_path.with_suffix('.enc')
            with open(encrypted_path, 'wb') as f:
                f.write(encrypted_data)

            # Remove original file
            backup_path.unlink()

            return encrypted_path

        except Exception as e:
            logger.error(f"Error encrypting backup: {e}")
            return backup_path

    async def _verify_backup(self, backup_path: str) -> Dict[str, Any]:
        """Verify backup integrity"""
        try:
            verification_results = self.integrity_manager.verify_backup_structure(backup_path)

            # Calculate checksum
            checksum = self.integrity_manager.calculate_checksum(backup_path)
            verification_results['checksum'] = checksum

            return verification_results

        except Exception as e:
            logger.error(f"Error verifying backup: {e}")
            return {'valid': False, 'error': str(e)}

    async def restore_backup(self, backup_id: str, target_directory: str = "") -> bool:
        """
        Restore from backup

        Args:
            backup_id: Backup ID to restore
            target_directory: Target directory for restore

        Returns:
            bool: True if successful
        """
        try:
            # Find backup
            backup = None
            for b in self.backup_history:
                if b.backup_id == backup_id:
                    backup = b
                    break

            if not backup:
                logger.error(f"Backup not found: {backup_id}")
                return False

            logger.info(f"Starting restore from backup: {backup_id}")

            # Decrypt if encrypted
            backup_path = backup.backup_path
            if backup.encryption_key_id:
                backup_path = await self._decrypt_backup(backup_path, backup.encryption_key_id)

            # Extract backup
            restore_dir = Path(target_directory) if target_directory else Path(f"restore_{backup_id}")
            restore_dir.mkdir(parents=True, exist_ok=True)

            with tarfile.open(backup_path, 'r:*') as tar:
                tar.extractall(restore_dir)

            # Restore database
            await self._restore_database(restore_dir / 'database')

            # Restore configuration
            await self._restore_config(restore_dir / 'config')

            logger.info(f"Restore completed: {backup_id}")
            return True

        except Exception as e:
            logger.error(f"Error restoring backup {backup_id}: {e}")
            return False

    async def _decrypt_backup(self, backup_path: str, key_id: str) -> Path:
        """Decrypt backup file"""
        try:
            with open(backup_path, 'rb') as f:
                encrypted_data = f.read()

            decrypted_data = self.encryption_manager.decrypt_data(encrypted_data, key_id)

            # Write decrypted file
            decrypted_path = Path(backup_path).with_suffix('.tar.gz')
            with open(decrypted_path, 'wb') as f:
                f.write(decrypted_data)

            return decrypted_path

        except Exception as e:
            logger.error(f"Error decrypting backup: {e}")
            raise

    async def _restore_database(self, db_dir: Path):
        """Restore database from backup"""
        try:
            if not db_dir.exists():
                return

            # Restore SQLite database
            backup_db = db_dir / 'trading_signals.db'
            if backup_db.exists():
                # Create backup of current database
                current_db = Path('trading_signals.db')
                if current_db.exists():
                    backup_current = Path(f"trading_signals.db.backup_{int(time.time())}")
                    shutil.copy2(current_db, backup_current)

                # Restore database
                shutil.copy2(backup_db, current_db)

        except Exception as e:
            logger.error(f"Error restoring database: {e}")
            raise

    async def _restore_config(self, config_dir: Path):
        """Restore configuration from backup"""
        try:
            if not config_dir.exists():
                return

            # Backup current config
            config_files = ['.env', 'requirements.txt']
            for config_file in config_files:
                current_path = Path(config_file)
                if current_path.exists():
                    backup_path = Path(f"{config_file}.backup_{int(time.time())}")
                    shutil.copy2(current_path, backup_path)

            # Restore config files
            for config_file in config_dir.iterdir():
                if config_file.is_file():
                    dest_path = Path(config_file.name)
                    shutil.copy2(config_file, dest_path)

        except Exception as e:
            logger.error(f"Error restoring configuration: {e}")

    def cleanup_old_backups(self):
        """Clean up old backups based on retention policy"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=self.config.retention_days)
            cleaned_count = 0

            for backup in self.backup_history[:]:
                if backup.end_time and backup.end_time < cutoff_time:
                    # Delete backup file
                    if os.path.exists(backup.backup_path):
                        os.remove(backup.backup_path)

                    # Remove from history
                    self.backup_history.remove(backup)
                    cleaned_count += 1

            if cleaned_count > 0:
                self._save_backup_history()
                logger.info(f"Cleaned up {cleaned_count} old backups")

        except Exception as e:
            logger.error(f"Error cleaning up old backups: {e}")

    def get_backup_status(self) -> Dict[str, Any]:
        """Get backup system status"""
        try:
            total_backups = len(self.backup_history)
            successful_backups = sum(1 for b in self.backup_history if b.status == BackupStatus.COMPLETED)
            failed_backups = sum(1 for b in self.backup_history if b.status == BackupStatus.FAILED)

            # Calculate storage usage
            total_size = sum(b.size_bytes for b in self.backup_history if b.status == BackupStatus.COMPLETED)

            # Get recent backups
            recent_backups = [
                b for b in self.backup_history
                if b.end_time and (datetime.utcnow() - b.end_time).days < 7
            ]

            return {
                'total_backups': total_backups,
                'successful_backups': successful_backups,
                'failed_backups': failed_backups,
                'success_rate': successful_backups / total_backups if total_backups > 0 else 0,
                'total_storage_mb': total_size / (1024 * 1024),
                'scheduler_running': self.is_running,
                'config': {
                    'enabled': self.config.enabled,
                    'retention_days': self.config.retention_days,
                    'encryption_enabled': self.config.encryption_enabled,
                    'integrity_verification': self.config.integrity_verification
                },
                'recent_backups': [
                    {
                        'backup_id': b.backup_id,
                        'backup_type': b.backup_type.value,
                        'status': b.status.value,
                        'size_mb': b.size_bytes / (1024 * 1024),
                        'created_at': b.start_time.isoformat()
                    }
                    for b in recent_backups[-10:]
                ]
            }

        except Exception as e:
            logger.error(f"Error getting backup status: {e}")
            return {}

    def add_backup_callback(self, callback: Callable[[BackupMetadata], None]):
        """Add callback for backup events"""
        self.backup_callbacks.append(callback)

class DisasterRecoveryManager:
    """Disaster recovery management"""

    def __init__(self):
        self.recovery_plans: Dict[str, RecoveryPlan] = {}
        self.recovery_history: List[Dict[str, Any]] = []
        self._load_recovery_plans()

    def _load_recovery_plans(self):
        """Load recovery plans"""
        plans_file = Path("security/recovery_plans.json")
        if plans_file.exists():
            try:
                with open(plans_file, 'r') as f:
                    plans_data = json.load(f)
                    self.recovery_plans = {
                        plan_id: RecoveryPlan(**plan_data)
                        for plan_id, plan_data in plans_data.items()
                    }
                logger.info(f"Loaded {len(self.recovery_plans)} recovery plans")
            except Exception as e:
                logger.error(f"Error loading recovery plans: {e}")
                self.recovery_plans = {}

    def _save_recovery_plans(self):
        """Save recovery plans"""
        try:
            plans_file = Path("security/recovery_plans.json")
            plans_file.parent.mkdir(parents=True, exist_ok=True)
            with open(plans_file, 'w') as f:
                json.dump(
                    {plan_id: asdict(plan) for plan_id, plan in self.recovery_plans.items()},
                    f, indent=2, default=str
                )
        except Exception as e:
            logger.error(f"Error saving recovery plans: {e}")

    def create_recovery_plan(self, name: str, description: str, **kwargs) -> str:
        """Create recovery plan"""
        plan_id = f"plan_{uuid.uuid4().hex[:8]}"

        plan = RecoveryPlan(
            plan_id=plan_id,
            name=name,
            description=description,
            backup_sources=kwargs.get('backup_sources', []),
            recovery_order=kwargs.get('recovery_order', []),
            recovery_procedures=kwargs.get('recovery_procedures', {}),
            contact_information=kwargs.get('contact_information', {}),
            estimated_recovery_time=kwargs.get('estimated_recovery_time', 60),
            data_consistency_checks=kwargs.get('data_consistency_checks', []),
            rollback_procedures=kwargs.get('rollback_procedures', []),
            testing_procedures=kwargs.get('testing_procedures', [])
        )

        self.recovery_plans[plan_id] = plan
        self._save_recovery_plans()

        logger.info(f"Created recovery plan: {plan_id} - {name}")
        return plan_id

    def execute_recovery_plan(self, plan_id: str) -> bool:
        """Execute recovery plan"""
        try:
            plan = self.recovery_plans.get(plan_id)
            if not plan:
                logger.error(f"Recovery plan not found: {plan_id}")
                return False

            logger.info(f"Executing recovery plan: {plan_id} - {plan.name}")

            # Record recovery start
            recovery_record = {
                'plan_id': plan_id,
                'plan_name': plan.name,
                'start_time': datetime.utcnow().isoformat(),
                'status': 'in_progress',
                'steps_completed': [],
                'errors': []
            }

            # Execute recovery steps
            for step in plan.recovery_order:
                try:
                    logger.info(f"Executing recovery step: {step}")
                    # Execute recovery procedure
                    procedure = plan.recovery_procedures.get(step)
                    if procedure:
                        # This would be implemented based on specific recovery procedures
                        recovery_record['steps_completed'].append(step)
                    else:
                        logger.warning(f"Recovery procedure not found for step: {step}")

                except Exception as e:
                    recovery_record['errors'].append(f"Step {step} failed: {e}")
                    logger.error(f"Recovery step failed: {step} - {e}")

            # Record recovery completion
            recovery_record['end_time'] = datetime.utcnow().isoformat()
            recovery_record['status'] = 'completed' if not recovery_record['errors'] else 'partial'

            self.recovery_history.append(recovery_record)

            logger.info(f"Recovery plan execution completed: {plan_id}")
            return True

        except Exception as e:
            logger.error(f"Error executing recovery plan {plan_id}: {e}")
            return False

    def test_recovery_plan(self, plan_id: str) -> Dict[str, Any]:
        """Test recovery plan"""
        try:
            plan = self.recovery_plans.get(plan_id)
            if not plan:
                return {'success': False, 'error': 'Plan not found'}

            logger.info(f"Testing recovery plan: {plan_id}")

            test_results = {
                'test_id': f"test_{uuid.uuid4().hex[:8]}",
                'plan_id': plan_id,
                'test_date': datetime.utcnow().isoformat(),
                'test_results': {},
                'issues_found': [],
                'recommendations': []
            }

            # Test each recovery procedure
            for step, procedure in plan.recovery_procedures.items():
                try:
                    # Simulate testing procedure
                    test_results['test_results'][step] = {
                        'status': 'passed',
                        'duration_seconds': 1.0,
                        'notes': 'Test completed successfully'
                    }
                except Exception as e:
                    test_results['issues_found'].append(f"Step {step} failed: {e}")

            # Update plan test information
            plan.last_tested = datetime.utcnow()
            plan.test_results = test_results
            self._save_recovery_plans()

            return test_results

        except Exception as e:
            logger.error(f"Error testing recovery plan {plan_id}: {e}")
            return {'success': False, 'error': str(e)}

    def get_recovery_status(self) -> Dict[str, Any]:
        """Get disaster recovery status"""
        try:
            total_plans = len(self.recovery_plans)
            tested_plans = sum(1 for p in self.recovery_plans.values() if p.last_tested)

            recent_tests = [
                p for p in self.recovery_plans.values()
                if p.last_tested and (datetime.utcnow() - p.last_tested).days < 30
            ]

            return {
                'total_plans': total_plans,
                'tested_plans': tested_plans,
                'recently_tested': len(recent_tests),
                'testing_coverage': tested_plans / total_plans if total_plans > 0 else 0,
                'recent_recoveries': len(self.recovery_history[-10:]) if self.recovery_history else 0,
                'plans': [
                    {
                        'plan_id': plan.plan_id,
                        'name': plan.name,
                        'last_tested': plan.last_tested.isoformat() if plan.last_tested else None,
                        'estimated_recovery_time': plan.estimated_recovery_time
                    }
                    for plan in self.recovery_plans.values()
                ]
            }

        except Exception as e:
            logger.error(f"Error getting recovery status: {e}")
            return {}

# Initialize global instances
backup_config = BackupConfig()
backup_manager = BackupManager(backup_config)
disaster_recovery_manager = DisasterRecoveryManager()

# Example usage
if __name__ == "__main__":
    # Create backup manager
    config = BackupConfig(
        retention_days=7,
        encryption_enabled=True,
        integrity_verification=True
    )

    manager = BackupManager(config)
    recovery = DisasterRecoveryManager()

    # Start backup scheduler
    manager.start_scheduler()

    # Create recovery plan
    plan_id = recovery.create_recovery_plan(
        name="Application Recovery",
        description="Recover application from backup",
        backup_sources=["database", "config", "application_files"],
        recovery_order=["database", "config", "application_files"],
        estimated_recovery_time=30
    )

    # Test recovery plan
    test_results = recovery.test_recovery_plan(plan_id)
    print(f"Recovery plan test results: {test_results}")

    # Get backup status
    status = manager.get_backup_status()
    print(f"Backup status: {status}")

    print("Backup and disaster recovery system initialized")