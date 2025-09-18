"""
File System Security Module

Provides comprehensive file system security including:
- Secure file access controls
- Permission management
- File integrity monitoring
- Secure file operations
- Path traversal protection
- Quarantine system
- Secure file uploads
- Directory hardening
"""

import os
import stat
import shutil
import hashlib
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import aiofiles
import magic
from fastapi import HTTPException, UploadFile, File
from pydantic import BaseModel, validator

logger = logging.getLogger(__name__)

class FilePermission(Enum):
    """File permission levels"""
    NONE = 0
    READ = 1
    WRITE = 2
    EXECUTE = 3
    FULL = 4

class FileType(Enum):
    """File type classifications"""
    CONFIG = "config"
    LOG = "log"
    DATA = "data"
    UPLOAD = "upload"
    TEMP = "temp"
    BACKUP = "backup"
    CERT = "certificate"
    EXECUTABLE = "executable"
    SCRIPT = "script"
    DOCUMENT = "document"
    MEDIA = "media"
    ARCHIVE = "archive"
    UNKNOWN = "unknown"

class SecurityLevel(Enum):
    """Security levels for file operations"""
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    MINIMAL = 4

@dataclass
class FileMetadata:
    """File metadata with security information"""
    path: str
    size: int
    modified: datetime
    created: datetime
    accessed: datetime
    permissions: str
    owner: str
    group: str
    file_type: FileType
    hash_sha256: str
    hash_md5: str
    mime_type: str
    is_executable: bool
    is_writable: bool
    is_readable: bool
    security_level: SecurityLevel
    quarantine_status: bool = False
    last_integrity_check: Optional[datetime] = None
    integrity_hash: Optional[str] = None
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    risk_score: float = 0.0

@dataclass
class SecurityPolicy:
    """Security policy for file operations"""
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    allowed_extensions: Set[str] = field(default_factory=lambda: {
        '.txt', '.csv', '.json', '.xml', '.pdf', '.jpg', '.jpeg',
        '.png', '.gif', '.bmp', '.svg', '.log', '.conf', '.yaml',
        '.yml', '.ini', '.env', '.pem', '.key', '.crt', '.csr'
    })
    blocked_extensions: Set[str] = field(default_factory=lambda: {
        '.exe', '.bat', '.cmd', '.sh', '.scr', '.pif', '.com',
        '.vbs', '.js', '.jar', '.app', '.deb', '.rpm', '.dmg'
    })
    allowed_mime_types: Set[str] = field(default_factory=lambda: {
        'text/plain', 'text/csv', 'application/json', 'application/xml',
        'application/pdf', 'image/jpeg', 'image/png', 'image/gif',
        'image/svg+xml', 'text/plain', 'application/x-pem-file'
    })
    blocked_mime_types: Set[str] = field(default_factory=lambda: {
        'application/x-dosexec', 'application/x-executable',
        'application/x-sharedlib', 'application/x-object'
    })
    max_path_length: int = 4096
    require_integrity_check: bool = True
    enable_quarantine: bool = True
    scan_for_malware: bool = True
    enable_access_logging: bool = True
    restrict_file_permissions: bool = True

class FileSystemSecurityManager:
    """
    Comprehensive file system security manager

    Features:
    - Secure file access controls
    - Permission management
    - File integrity monitoring
    - Path traversal protection
    - Quarantine system
    - Secure file uploads
    """

    def __init__(self, security_policy: Optional[SecurityPolicy] = None):
        self.security_policy = security_policy or SecurityPolicy()
        self.file_metadata_cache: Dict[str, FileMetadata] = {}
        self.quarantine_directory = Path("security/quarantine")
        self.secure_temp_directory = Path("security/temp")
        self.audit_log = []
        self.integrity_database = {}
        self.access_patterns = {}
        self.suspicious_patterns = {}
        self.magic_detector = magic.Magic(mime=True)

        # Initialize directories
        self._initialize_directories()

        # Load integrity database
        self._load_integrity_database()

        logger.info("FileSystemSecurityManager initialized with security policy")

    def _initialize_directories(self):
        """Initialize security directories with proper permissions"""
        try:
            # Create quarantine directory with restricted permissions
            self.quarantine_directory.mkdir(parents=True, exist_ok=True)
            os.chmod(self.quarantine_directory, 0o700)

            # Create secure temp directory
            self.secure_temp_directory.mkdir(parents=True, exist_ok=True)
            os.chmod(self.secure_temp_directory, 0o700)

            # Secure existing directories
            self._secure_application_directories()

        except Exception as e:
            logger.error(f"Failed to initialize security directories: {e}")
            raise

    def _secure_application_directories(self):
        """Secure application directories with proper permissions"""
        secure_dirs = [
            "security",
            "logs",
            "data",
            "config",
            "uploads",
            "backups"
        ]

        for dir_name in secure_dirs:
            dir_path = Path(dir_name)
            if dir_path.exists():
                # Set secure permissions
                if dir_name == "security":
                    os.chmod(dir_path, 0o700)  # Owner only
                elif dir_name in ["config", "data"]:
                    os.chmod(dir_path, 0o750)  # Owner and group
                else:
                    os.chmod(dir_path, 0o755)  # Standard permissions

                logger.info(f"Secured directory: {dir_path}")

    def _load_integrity_database(self):
        """Load file integrity database"""
        integrity_file = Path("security/integrity_database.json")
        if integrity_file.exists():
            try:
                with open(integrity_file, 'r') as f:
                    self.integrity_database = json.load(f)
                logger.info(f"Loaded integrity database with {len(self.integrity_database)} entries")
            except Exception as e:
                logger.error(f"Failed to load integrity database: {e}")
                self.integrity_database = {}

    def _save_integrity_database(self):
        """Save file integrity database"""
        try:
            integrity_file = Path("security/integrity_database.json")
            integrity_file.parent.mkdir(parents=True, exist_ok=True)
            with open(integrity_file, 'w') as f:
                json.dump(self.integrity_database, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save integrity database: {e}")

    def _is_path_traversal(self, path: str) -> bool:
        """Check for path traversal attempts"""
        try:
            # Normalize path
            normalized = os.path.normpath(path)

            # Check for traversal patterns
            if ".." in normalized or normalized.startswith("/") or normalized[1:3] == ":\\":
                return True

            # Check if path is within allowed directories
            abs_path = Path(normalized).resolve()
            current_dir = Path.cwd()

            if not str(abs_path).startswith(str(current_dir)):
                return True

            return False
        except Exception:
            return True

    def _get_file_type(self, path: str) -> FileType:
        """Determine file type based on path and content"""
        path_lower = path.lower()

        if any(keyword in path_lower for keyword in ['config', '.conf', '.yaml', '.yml', '.ini', '.env']):
            return FileType.CONFIG
        elif any(keyword in path_lower for keyword in ['log', '.log']):
            return FileType.LOG
        elif any(keyword in path_lower for keyword in ['data', '.db', '.sqlite']):
            return FileType.DATA
        elif any(keyword in path_lower for keyword in ['upload', 'uploads']):
            return FileType.UPLOAD
        elif any(keyword in path_lower for keyword in ['temp', 'tmp']):
            return FileType.TEMP
        elif any(keyword in path_lower for keyword in ['backup', 'bak']):
            return FileType.BACKUP
        elif any(keyword in path_lower for keyword in ['.pem', '.key', '.crt', '.csr', '.cert']):
            return FileType.CERT
        elif any(keyword in path_lower for keyword in ['.py', '.sh', '.bat', '.exe']):
            return FileType.SCRIPT
        elif any(keyword in path_lower for keyword in ['.doc', '.docx', '.pdf', '.txt']):
            return FileType.DOCUMENT
        elif any(keyword in path_lower for keyword in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']):
            return FileType.MEDIA
        elif any(keyword in path_lower for keyword in ['.zip', '.tar', '.gz', '.rar']):
            return FileType.ARCHIVE

        return FileType.UNKNOWN

    def _calculate_security_level(self, file_meta: FileMetadata) -> SecurityLevel:
        """Calculate security level based on file metadata"""
        score = 0

        # File type weighting
        if file_meta.file_type == FileType.CONFIG:
            score += 4
        elif file_meta.file_type == FileType.CERT:
            score += 4
        elif file_meta.file_type == FileType.DATA:
            score += 3
        elif file_meta.file_type == FileType.SCRIPT:
            score += 3
        elif file_meta.file_type == FileType.EXECUTABLE:
            score += 4

        # Permission weighting
        if file_meta.is_executable:
            score += 2
        if file_meta.is_writable:
            score += 1

        # Size weighting
        if file_meta.size > 10 * 1024 * 1024:  # > 10MB
            score += 1
        if file_meta.size > 100 * 1024 * 1024:  # > 100MB
            score += 2

        # Risk score weighting
        score += int(file_meta.risk_score)

        # Map score to security level
        if score >= 8:
            return SecurityLevel.CRITICAL
        elif score >= 6:
            return SecurityLevel.HIGH
        elif score >= 4:
            return SecurityLevel.MEDIUM
        elif score >= 2:
            return SecurityLevel.LOW
        else:
            return SecurityLevel.MINIMAL

    def _calculate_risk_score(self, path: str, file_meta: Optional[FileMetadata] = None) -> float:
        """Calculate risk score for a file"""
        risk_score = 0.0

        # Path-based risk factors
        if any(keyword in path.lower() for keyword in ['temp', 'tmp', 'cache']):
            risk_score += 1.0

        if any(keyword in path.lower() for keyword in ['config', 'secret', 'key', 'password']):
            risk_score += 2.0

        if any(keyword in path.lower() for keyword in ['exec', 'run', 'script']):
            risk_score += 1.5

        # Extension-based risk
        ext = Path(path).suffix.lower()
        if ext in ['.exe', '.bat', '.cmd', '.sh', '.scr']:
            risk_score += 3.0
        elif ext in ['.js', '.jar', '.app']:
            risk_score += 2.0
        elif ext in ['.dll', '.so', '.dylib']:
            risk_score += 2.5

        # Size-based risk
        if file_meta and file_meta.size > 50 * 1024 * 1024:  # > 50MB
            risk_score += 1.0

        return min(risk_score, 10.0)

    def _get_file_metadata(self, path: str) -> Optional[FileMetadata]:
        """Get comprehensive file metadata"""
        try:
            if not os.path.exists(path):
                return None

            stat_info = os.stat(path)

            # Calculate file hashes
            hash_sha256 = hashlib.sha256()
            hash_md5 = hashlib.md5()

            with open(path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
                    hash_md5.update(chunk)

            # Detect MIME type
            try:
                mime_type = self.magic_detector.from_file(path)
            except:
                mime_type = "application/octet-stream"

            # Determine file type
            file_type = self._get_file_type(path)

            # Calculate risk score
            risk_score = self._calculate_risk_score(path)

            # Create metadata object
            metadata = FileMetadata(
                path=path,
                size=stat_info.st_size,
                modified=datetime.fromtimestamp(stat_info.st_mtime),
                created=datetime.fromtimestamp(stat_info.st_ctime),
                accessed=datetime.fromtimestamp(stat_info.st_atime),
                permissions=oct(stat_info.st_mode)[-3:],
                owner=str(stat_info.st_uid),
                group=str(stat_info.st_gid),
                file_type=file_type,
                hash_sha256=hash_sha256.hexdigest(),
                hash_md5=hash_md5.hexdigest(),
                mime_type=mime_type,
                is_executable=bool(stat_info.st_mode & stat.S_IEXEC),
                is_writable=bool(stat_info.st_mode & stat.S_IWRITE),
                is_readable=bool(stat_info.st_mode & stat.S_IREAD),
                security_level=SecurityLevel.MINIMAL,  # Will be calculated
                risk_score=risk_score
            )

            # Calculate security level
            metadata.security_level = self._calculate_security_level(metadata)

            return metadata

        except Exception as e:
            logger.error(f"Failed to get metadata for {path}: {e}")
            return None

    def validate_file_access(self, path: str, required_permission: FilePermission) -> bool:
        """
        Validate file access with security checks

        Args:
            path: File path to access
            required_permission: Required permission level

        Returns:
            bool: True if access is allowed
        """
        try:
            # Check for path traversal
            if self._is_path_traversal(path):
                logger.warning(f"Path traversal attempt detected: {path}")
                return False

            # Check if file exists
            if not os.path.exists(path):
                logger.warning(f"File not found: {path}")
                return False

            # Check quarantine status
            if path in self.file_metadata_cache:
                metadata = self.file_metadata_cache[path]
                if metadata.quarantine_status:
                    logger.warning(f"Attempt to access quarantined file: {path}")
                    return False

            # Check permissions
            if required_permission == FilePermission.READ:
                if not os.access(path, os.R_OK):
                    return False
            elif required_permission == FilePermission.WRITE:
                if not os.access(path, os.W_OK):
                    return False
            elif required_permission == FilePermission.EXECUTE:
                if not os.access(path, os.X_OK):
                    return False

            # Log access
            if self.security_policy.enable_access_logging:
                self._log_access_attempt(path, required_permission, True)

            return True

        except Exception as e:
            logger.error(f"Error validating file access for {path}: {e}")
            return False

    def _log_access_attempt(self, path: str, permission: FilePermission, success: bool):
        """Log file access attempt"""
        access_log = {
            'timestamp': datetime.utcnow().isoformat(),
            'path': path,
            'permission': permission.name,
            'success': success,
            'ip_address': getattr(self, 'current_ip', 'unknown'),
            'user_agent': getattr(self, 'current_user_agent', 'unknown')
        }

        self.audit_log.append(access_log)

        # Update access patterns
        if path not in self.access_patterns:
            self.access_patterns[path] = []
        self.access_patterns[path].append(access_log)

        # Check for suspicious patterns
        self._check_suspicious_patterns(path, access_log)

    def _check_suspicious_patterns(self, path: str, access_log: Dict):
        """Check for suspicious access patterns"""
        path_accesses = self.access_patterns.get(path, [])

        # Check for rapid access
        recent_accesses = [
            a for a in path_accesses
            if (datetime.utcnow() - datetime.fromisoformat(a['timestamp'])).seconds < 60
        ]

        if len(recent_accesses) > 100:  # More than 100 accesses in a minute
            self.suspicious_patterns[path] = {
                'type': 'rapid_access',
                'count': len(recent_accesses),
                'timestamp': datetime.utcnow().isoformat()
            }
            logger.warning(f"Suspicious rapid access pattern detected for {path}")

    async def secure_file_upload(self, file: UploadFile, destination_dir: str) -> str:
        """
        Securely handle file upload

        Args:
            file: UploadFile object
            destination_dir: Destination directory

        Returns:
            str: Path to uploaded file
        """
        try:
            # Validate file size
            if file.size and file.size > self.security_policy.max_file_size:
                raise HTTPException(status_code=413, detail="File too large")

            # Get file extension
            file_extension = Path(file.filename).suffix.lower()

            # Check blocked extensions
            if file_extension in self.security_policy.blocked_extensions:
                raise HTTPException(status_code=415, detail="File type not allowed")

            # Create secure filename
            secure_filename = self._create_secure_filename(file.filename)
            file_path = Path(destination_dir) / secure_filename

            # Ensure destination directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Validate file content
            content = await file.read()

            # Check MIME type
            mime_type = magic.from_buffer(content, mime=True)
            if mime_type in self.security_policy.blocked_mime_types:
                raise HTTPException(status_code=415, detail="File content type not allowed")

            # Scan for malware if enabled
            if self.security_policy.scan_for_malware:
                if self._scan_for_malware(content):
                    raise HTTPException(status_code=400, detail="Malware detected")

            # Write file securely
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)

            # Set secure permissions
            os.chmod(file_path, 0o600)

            # Get metadata and cache
            metadata = self._get_file_metadata(str(file_path))
            if metadata:
                self.file_metadata_cache[str(file_path)] = metadata

            logger.info(f"File uploaded securely: {file_path}")
            return str(file_path)

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in secure file upload: {e}")
            raise HTTPException(status_code=500, detail="File upload failed")

    def _create_secure_filename(self, filename: str) -> str:
        """Create secure filename"""
        # Remove path traversal attempts
        filename = os.path.basename(filename)

        # Remove special characters
        import re
        filename = re.sub(r'[^\w\-_\.]', '_', filename)

        # Add timestamp for uniqueness
        timestamp = int(time.time())
        name, ext = os.path.splitext(filename)

        return f"{name}_{timestamp}{ext}"

    def _scan_for_malware(self, content: bytes) -> bool:
        """Basic malware scanning (placeholder for real AV integration)"""
        # Simple pattern matching for suspicious content
        suspicious_patterns = [
            b'<script',
            b'javascript:',
            b'eval(',
            b'document.write',
            b'exec(',
            b'system(',
            b'shell_exec',
            b'passthru'
        ]

        for pattern in suspicious_patterns:
            if pattern.lower() in content.lower():
                return True

        return False

    def quarantine_file(self, path: str, reason: str) -> bool:
        """
        Quarantine a suspicious file

        Args:
            path: File path to quarantine
            reason: Reason for quarantine

        Returns:
            bool: True if successful
        """
        try:
            if not os.path.exists(path):
                logger.warning(f"Cannot quarantine non-existent file: {path}")
                return False

            # Create quarantine filename
            quarantine_path = self.quarantine_directory / f"{Path(path).name}_{int(time.time())}"

            # Move file to quarantine
            shutil.move(path, quarantine_path)

            # Set restrictive permissions
            os.chmod(quarantine_path, 0o000)

            # Update metadata
            if path in self.file_metadata_cache:
                self.file_metadata_cache[path].quarantine_status = True

            # Log quarantine event
            quarantine_log = {
                'timestamp': datetime.utcnow().isoformat(),
                'original_path': path,
                'quarantine_path': str(quarantine_path),
                'reason': reason,
                'action': 'quarantine'
            }

            self.audit_log.append(quarantine_log)

            logger.warning(f"File quarantined: {path} -> {quarantine_path}")
            return True

        except Exception as e:
            logger.error(f"Error quarantining file {path}: {e}")
            return False

    def restore_from_quarantine(self, quarantine_path: str, restore_path: str) -> bool:
        """
        Restore file from quarantine

        Args:
            quarantine_path: Quarantined file path
            restore_path: Path to restore to

        Returns:
            bool: True if successful
        """
        try:
            if not os.path.exists(quarantine_path):
                logger.warning(f"Quarantined file not found: {quarantine_path}")
                return False

            # Move file back
            shutil.move(quarantine_path, restore_path)

            # Restore appropriate permissions
            os.chmod(restore_path, 0o600)

            # Update metadata
            if restore_path in self.file_metadata_cache:
                self.file_metadata_cache[restore_path].quarantine_status = False

            # Log restoration event
            restore_log = {
                'timestamp': datetime.utcnow().isoformat(),
                'quarantine_path': quarantine_path,
                'restore_path': restore_path,
                'action': 'restore'
            }

            self.audit_log.append(restore_log)

            logger.info(f"File restored from quarantine: {quarantine_path} -> {restore_path}")
            return True

        except Exception as e:
            logger.error(f"Error restoring file {quarantine_path}: {e}")
            return False

    def check_file_integrity(self, path: str) -> bool:
        """
        Check file integrity against stored hash

        Args:
            path: File path to check

        Returns:
            bool: True if integrity is intact
        """
        try:
            if not os.path.exists(path):
                return False

            # Get current hash
            current_hash = self._calculate_file_hash(path)

            # Get stored hash
            stored_hash = self.integrity_database.get(path)

            if stored_hash is None:
                # First time checking, store hash
                self.integrity_database[path] = {
                    'hash': current_hash,
                    'timestamp': datetime.utcnow().isoformat(),
                    'algorithm': 'sha256'
                }
                self._save_integrity_database()
                return True

            # Compare hashes
            if current_hash != stored_hash['hash']:
                logger.warning(f"File integrity violation detected: {path}")

                # Log integrity event
                integrity_log = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'path': path,
                    'stored_hash': stored_hash['hash'],
                    'current_hash': current_hash,
                    'action': 'integrity_violation'
                }

                self.audit_log.append(integrity_log)

                # Quarantine file if enabled
                if self.security_policy.enable_quarantine:
                    self.quarantine_file(path, "Integrity violation detected")

                return False

            # Update metadata
            if path in self.file_metadata_cache:
                self.file_metadata_cache[path].last_integrity_check = datetime.utcnow()
                self.file_metadata_cache[path].integrity_hash = current_hash

            return True

        except Exception as e:
            logger.error(f"Error checking file integrity for {path}: {e}")
            return False

    def _calculate_file_hash(self, path: str) -> str:
        """Calculate SHA256 hash of file"""
        hash_sha256 = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def secure_file_operation(self, operation: str, path: str, **kwargs) -> bool:
        """
        Perform secure file operation with logging

        Args:
            operation: Operation type (read, write, delete, etc.)
            path: File path
            **kwargs: Additional operation parameters

        Returns:
            bool: True if successful
        """
        try:
            # Validate access
            if operation == 'read':
                if not self.validate_file_access(path, FilePermission.READ):
                    return False
            elif operation in ['write', 'append']:
                if not self.validate_file_access(path, FilePermission.WRITE):
                    return False
            elif operation == 'delete':
                if not self.validate_file_access(path, FilePermission.WRITE):
                    return False

            # Perform operation
            success = False
            if operation == 'read':
                with open(path, 'r') as f:
                    content = f.read()
                success = True
            elif operation == 'write':
                content = kwargs.get('content', '')
                with open(path, 'w') as f:
                    f.write(content)
                success = True
            elif operation == 'append':
                content = kwargs.get('content', '')
                with open(path, 'a') as f:
                    f.write(content)
                success = True
            elif operation == 'delete':
                os.remove(path)
                success = True

            # Log operation
            operation_log = {
                'timestamp': datetime.utcnow().isoformat(),
                'operation': operation,
                'path': path,
                'success': success,
                'kwargs': {k: v for k, v in kwargs.items() if k != 'content'}
            }

            self.audit_log.append(operation_log)

            if success:
                logger.info(f"Secure file operation completed: {operation} {path}")
            else:
                logger.error(f"Secure file operation failed: {operation} {path}")

            return success

        except Exception as e:
            logger.error(f"Error in secure file operation {operation} {path}: {e}")
            return False

    def cleanup_temp_files(self, max_age_hours: int = 24) -> int:
        """
        Clean up temporary files older than specified age

        Args:
            max_age_hours: Maximum age in hours

        Returns:
            int: Number of files cleaned up
        """
        try:
            cleaned_count = 0
            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)

            # Clean temp directory
            for file_path in self.secure_temp_directory.rglob('*'):
                if file_path.is_file():
                    stat_info = file_path.stat()
                    file_time = datetime.fromtimestamp(stat_info.st_mtime)

                    if file_time < cutoff_time:
                        file_path.unlink()
                        cleaned_count += 1
                        logger.info(f"Cleaned up temporary file: {file_path}")

            logger.info(f"Cleaned up {cleaned_count} temporary files")
            return cleaned_count

        except Exception as e:
            logger.error(f"Error cleaning up temporary files: {e}")
            return 0

    def get_security_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive security report

        Returns:
            Dict: Security report data
        """
        try:
            # Count files by security level
            security_levels = {}
            for metadata in self.file_metadata_cache.values():
                level = metadata.security_level.name
                security_levels[level] = security_levels.get(level, 0) + 1

            # Count quarantined files
            quarantined_count = sum(1 for m in self.file_metadata_cache.values() if m.quarantine_status)

            # Get recent security events
            recent_events = [
                event for event in self.audit_log[-100:]
                if datetime.fromisoformat(event['timestamp']) > datetime.utcnow() - timedelta(hours=24)
            ]

            # Calculate risk metrics
            total_files = len(self.file_metadata_cache)
            high_risk_files = sum(1 for m in self.file_metadata_cache.values() if m.risk_score > 5.0)

            report = {
                'timestamp': datetime.utcnow().isoformat(),
                'total_files_monitored': total_files,
                'security_levels': security_levels,
                'quarantined_files': quarantined_count,
                'high_risk_files': high_risk_files,
                'recent_security_events': len(recent_events),
                'suspicious_patterns': len(self.suspicious_patterns),
                'integrity_checks': len(self.integrity_database),
                'policy_configuration': {
                    'max_file_size': self.security_policy.max_file_size,
                    'allowed_extensions': len(self.security_policy.allowed_extensions),
                    'blocked_extensions': len(self.security_policy.blocked_extensions),
                    'require_integrity_check': self.security_policy.require_integrity_check,
                    'enable_quarantine': self.security_policy.enable_quarantine,
                    'scan_for_malware': self.security_policy.scan_for_malware
                },
                'recommendations': self._generate_security_recommendations()
            }

            return report

        except Exception as e:
            logger.error(f"Error generating security report: {e}")
            return {}

    def _generate_security_recommendations(self) -> List[str]:
        """Generate security recommendations based on current state"""
        recommendations = []

        # Check for high-risk files
        high_risk_files = [m for m in self.file_metadata_cache.values() if m.risk_score > 5.0]
        if high_risk_files:
            recommendations.append(f"Found {len(high_risk_files)} high-risk files that should be reviewed")

        # Check for suspicious patterns
        if self.suspicious_patterns:
            recommendations.append(f"Detected {len(self.suspicious_patterns)} suspicious access patterns")

        # Check for quarantined files
        quarantined_count = sum(1 for m in self.file_metadata_cache.values() if m.quarantine_status)
        if quarantined_count > 0:
            recommendations.append(f"Review {quarantined_count} quarantined files")

        # Check for missing integrity checks
        unchecked_files = [m for m in self.file_metadata_cache.values() if m.last_integrity_check is None]
        if unchecked_files:
            recommendations.append(f"Run integrity checks on {len(unchecked_files)} unchecked files")

        # Check for excessive permissions
        writable_critical_files = [
            m for m in self.file_metadata_cache.values()
            if m.security_level in [SecurityLevel.CRITICAL, SecurityLevel.HIGH] and m.is_writable
        ]
        if writable_critical_files:
            recommendations.append(f"Consider restricting write permissions on {len(writable_critical_files)} critical files")

        return recommendations

    def monitor_file_system(self, interval_seconds: int = 60):
        """
        Monitor file system for security events

        Args:
            interval_seconds: Monitoring interval
        """
        import threading
        import time

        def monitor_loop():
            while True:
                try:
                    # Check for new files
                    self._scan_for_new_files()

                    # Check file integrity if enabled
                    if self.security_policy.require_integrity_check:
                        self._check_critical_files_integrity()

                    # Clean up old temp files
                    self.cleanup_temp_files()

                    # Sleep for interval
                    time.sleep(interval_seconds)

                except Exception as e:
                    logger.error(f"Error in file system monitoring: {e}")
                    time.sleep(interval_seconds)

        # Start monitoring thread
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()

        logger.info(f"File system monitoring started with {interval_seconds}s interval")

    def _scan_for_new_files(self):
        """Scan for new files in monitored directories"""
        monitored_dirs = ['config', 'data', 'security', 'logs']

        for dir_name in monitored_dirs:
            dir_path = Path(dir_name)
            if dir_path.exists():
                for file_path in dir_path.rglob('*'):
                    if file_path.is_file():
                        file_str = str(file_path)
                        if file_str not in self.file_metadata_cache:
                            # New file detected
                            metadata = self._get_file_metadata(file_str)
                            if metadata:
                                self.file_metadata_cache[file_str] = metadata

                                # Log new file
                                new_file_log = {
                                    'timestamp': datetime.utcnow().isoformat(),
                                    'path': file_str,
                                    'action': 'new_file_detected',
                                    'file_type': metadata.file_type.name,
                                    'risk_score': metadata.risk_score
                                }

                                self.audit_log.append(new_file_log)
                                logger.info(f"New file detected: {file_str}")

    def _check_critical_files_integrity(self):
        """Check integrity of critical files"""
        critical_files = [
            m for m in self.file_metadata_cache.values()
            if m.security_level in [SecurityLevel.CRITICAL, SecurityLevel.HIGH]
        ]

        for metadata in critical_files:
            self.check_file_integrity(metadata.path)

class FileSecurityMiddleware:
    """
    FastAPI middleware for file system security
    """

    def __init__(self, app, security_manager: FileSystemSecurityManager):
        self.app = app
        self.security_manager = security_manager

        # Add middleware to FastAPI app
        self.app.middleware("http")(self.file_security_middleware)

    async def file_security_middleware(self, request, call_next):
        """File system security middleware"""
        # Set current request context
        self.security_manager.current_ip = request.client.host
        self.security_manager.current_user_agent = request.headers.get("user-agent", "unknown")

        try:
            # Process request
            response = await call_next(request)

            # Add security headers
            response.headers["X-File-Security-Enabled"] = "true"
            response.headers["X-Security-Timestamp"] = datetime.utcnow().isoformat()

            return response

        except Exception as e:
            logger.error(f"Error in file security middleware: {e}")
            raise

# Security models for FastAPI
class FileUploadRequest(BaseModel):
    """File upload request model"""
    destination_directory: str
    allowed_extensions: Optional[List[str]] = None
    max_file_size: Optional[int] = None

    @validator('destination_directory')
    def validate_destination(cls, v):
        if any(keyword in v.lower() for keyword in ['..', '/', '\\', ':', '*']):
            raise ValueError("Invalid destination directory")
        return v

class FileOperationRequest(BaseModel):
    """File operation request model"""
    operation: str
    path: str
    content: Optional[str] = None

    @validator('operation')
    def validate_operation(cls, v):
        allowed_ops = ['read', 'write', 'append', 'delete']
        if v not in allowed_ops:
            raise ValueError(f"Operation must be one of {allowed_ops}")
        return v

    @validator('path')
    def validate_path(cls, v):
        if any(keyword in v.lower() for keyword in ['..', '~', '$']):
            raise ValueError("Invalid file path")
        return v

class FileSecurityResponse(BaseModel):
    """File security response model"""
    success: bool
    message: str
    file_path: Optional[str] = None
    file_metadata: Optional[Dict] = None
    security_events: Optional[List[Dict]] = None

# Initialize security manager
file_security_manager = FileSystemSecurityManager()

# Example usage
if __name__ == "__main__":
    # Create security policy
    policy = SecurityPolicy(
        max_file_size=50 * 1024 * 1024,  # 50MB
        require_integrity_check=True,
        enable_quarantine=True,
        scan_for_malware=True
    )

    # Initialize security manager
    manager = FileSystemSecurityManager(policy)

    # Test file operations
    test_file = "test_security.txt"

    # Test file upload simulation
    print("File System Security Manager initialized")
    print(f"Security policy: {policy}")
    print(f"Monitoring {len(manager.file_metadata_cache)} files")

    # Generate security report
    report = manager.get_security_report()
    print(f"Security report: {report}")

    # Start monitoring
    manager.monitor_file_system(interval_seconds=30)

    print("File system security monitoring started")