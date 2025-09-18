"""
Advanced Log Rotation and Retention System
Provides sophisticated log rotation with compression, retention policies,
and intelligent storage management.
"""

import os
import gzip
import shutil
import logging
import threading
import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
import json
import tarfile
import tempfile
import asyncio
from concurrent.futures import ThreadPoolExecutor

from .logging_config import get_logging_config, LogRotationConfig


@dataclass
class RotationStats:
    """Statistics for log rotation"""
    total_files_rotated: int = 0
    total_bytes_saved: int = 0
    total_files_deleted: int = 0
    last_rotation_time: Optional[datetime] = None
    rotation_count: int = 0
    compression_stats: Dict[str, int] = None

    def __post_init__(self):
        if self.compression_stats is None:
            self.compression_stats = {}


class LogRotator:
    """Advanced log rotator with compression and retention"""

    def __init__(self, rotation_config: LogRotationConfig):
        self.config = rotation_config
        self.stats = RotationStats()
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="log_rotator")
        self._active_rotations = {}

    def should_rotate(self, file_path: str) -> bool:
        """Check if file should be rotated"""
        if not self.config.enabled:
            return False

        try:
            stat = os.stat(file_path)

            # Check file size
            if stat.st_size >= self.config.max_size_bytes:
                return True

            # Check rotation interval
            if self.config.rotation_interval:
                file_age = time.time() - stat.st_mtime
                interval_seconds = self._parse_interval(self.config.rotation_interval)
                if file_age >= interval_seconds:
                    return True

            return False

        except (OSError, ValueError):
            return False

    def _parse_interval(self, interval_str: str) -> int:
        """Parse rotation interval string to seconds"""
        interval_str = interval_str.lower().strip()

        if interval_str.endswith('s'):
            return int(interval_str[:-1])
        elif interval_str.endswith('m'):
            return int(interval_str[:-1]) * 60
        elif interval_str.endswith('h'):
            return int(interval_str[:-1]) * 3600
        elif interval_str.endswith('d'):
            return int(interval_str[:-1]) * 86400
        elif interval_str.endswith('w'):
            return int(interval_str[:-1]) * 604800
        else:
            # Assume seconds if no unit specified
            return int(interval_str)

    def rotate_file(self, file_path: str, force: bool = False) -> bool:
        """Rotate a log file"""
        if not force and not self.should_rotate(file_path):
            return False

        # Check if rotation is already in progress
        with self._lock:
            if file_path in self._active_rotations:
                return False
            self._active_rotations[file_path] = True

        try:
            # Create backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self._get_backup_path(file_path, timestamp)

            # Perform rotation
            success = self._perform_rotation(file_path, backup_path)

            if success:
                with self._lock:
                    self.stats.rotation_count += 1
                    self.stats.last_rotation_time = datetime.now()

            return success

        except Exception as e:
            logging.error(f"Failed to rotate log file {file_path}: {e}")
            return False
        finally:
            with self._lock:
                self._active_rotations.pop(file_path, None)

    def _get_backup_path(self, file_path: str, timestamp: str) -> str:
        """Generate backup file path"""
        path = Path(file_path)
        backup_name = f"{path.stem}_{timestamp}{path.suffix}"
        return str(path.parent / backup_name)

    def _perform_rotation(self, file_path: str, backup_path: str) -> bool:
        """Perform the actual file rotation"""
        try:
            # Move current file to backup
            shutil.move(file_path, backup_path)

            # Compress if enabled
            if self.config.compression:
                compressed_path = self._compress_file(backup_path)
                if compressed_path and compressed_path != backup_path:
                    # Remove uncompressed backup if compression succeeded
                    try:
                        os.remove(backup_path)
                    except OSError:
                        pass
                    backup_path = compressed_path

            # Apply retention policy
            self._apply_retention_policy(file_path)

            return True

        except Exception as e:
            logging.error(f"Rotation failed for {file_path}: {e}")
            return False

    def _compress_file(self, file_path: str) -> Optional[str]:
        """Compress a file using gzip"""
        try:
            compressed_path = f"{file_path}.gz"

            # Get original size
            original_size = os.path.getsize(file_path)

            # Compress the file
            with open(file_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

            # Get compressed size
            compressed_size = os.path.getsize(compressed_path)
            saved_bytes = original_size - compressed_size

            # Update statistics
            with self._lock:
                self.stats.total_files_rotated += 1
                self.stats.total_bytes_saved += saved_bytes
                self.stats.compression_stats[file_path] = saved_bytes

            logging.info(f"Compressed {file_path}: {original_size} -> {compressed_size} bytes")
            return compressed_path

        except Exception as e:
            logging.error(f"Failed to compress {file_path}: {e}")
            return None

    def _apply_retention_policy(self, file_path: str) -> None:
        """Apply retention policy to log files"""
        try:
            path = Path(file_path)
            log_dir = path.parent

            # Get all backup files
            backup_files = []
            for file_pattern in [
                f"{path.stem}_*{path.suffix}",
                f"{path.stem}_*{path.suffix}.gz"
            ]:
                backup_files.extend(log_dir.glob(file_pattern))

            # Sort by modification time
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            # Remove old files beyond backup count
            if len(backup_files) > self.config.backup_count:
                files_to_delete = backup_files[self.config.backup_count:]
                for old_file in files_to_delete:
                    try:
                        file_size = old_file.stat().st_size
                        old_file.unlink()
                        with self._lock:
                            self.stats.total_files_deleted += 1
                        logging.info(f"Deleted old log file: {old_file}")
                    except OSError as e:
                        logging.error(f"Failed to delete old log file {old_file}: {e}")

        except Exception as e:
            logging.error(f"Failed to apply retention policy: {e}")

    def get_stats(self) -> RotationStats:
        """Get rotation statistics"""
        with self._lock:
            return RotationStats(
                total_files_rotated=self.stats.total_files_rotated,
                total_bytes_saved=self.stats.total_bytes_saved,
                total_files_deleted=self.stats.total_files_deleted,
                last_rotation_time=self.stats.last_rotation_time,
                rotation_count=self.stats.rotation_count,
                compression_stats=self.stats.compression_stats.copy()
            )

    def rotate_all_logs(self) -> Dict[str, bool]:
        """Rotate all configured log files"""
        results = {}

        # Get all log files to rotate
        log_files = self._get_log_files_to_rotate()

        # Rotate each file
        for log_file in log_files:
            results[log_file] = self.rotate_file(log_file)

        return results

    def _get_log_files_to_rotate(self) -> List[str]:
        """Get list of log files to rotate"""
        config = get_logging_config()
        log_files = []

        # Add main log files
        if config.main_log_file:
            log_files.append(os.path.join(config.log_directory, config.main_log_file))

        if config.error_log_file:
            log_files.append(os.path.join(config.log_directory, config.error_log_file))

        if config.access_log_file:
            log_files.append(os.path.join(config.log_directory, config.access_log_file))

        # Add compliance log files
        if config.compliance.enabled:
            if config.compliance.audit_log_file:
                log_files.append(os.path.join(config.log_directory, config.compliance.audit_log_file))
            if config.compliance.security_events_file:
                log_files.append(os.path.join(config.log_directory, config.compliance.security_events_file))
            if config.compliance.data_access_log_file:
                log_files.append(os.path.join(config.log_directory, config.compliance.data_access_log_file))

        return [f for f in log_files if os.path.exists(f)]

    def start_monitoring(self, check_interval: int = 60) -> None:
        """Start monitoring log files for rotation"""
        def monitor_loop():
            while True:
                try:
                    time.sleep(check_interval)
                    self.check_and_rotate()
                except Exception as e:
                    logging.error(f"Log rotation monitoring error: {e}")

        # Start monitoring in background thread
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True, name="log_rotation_monitor")
        monitor_thread.start()

    def check_and_rotate(self) -> None:
        """Check and rotate files if needed"""
        log_files = self._get_log_files_to_rotate()

        for log_file in log_files:
            if self.should_rotate(log_file):
                self.rotate_file(log_file)

    def cleanup(self) -> None:
        """Cleanup resources"""
        self._executor.shutdown(wait=True)


class LogArchiveManager:
    """Manages log archiving and long-term storage"""

    def __init__(self, archive_directory: str = "logs/archive"):
        self.archive_directory = Path(archive_directory)
        self.archive_directory.mkdir(parents=True, exist_ok=True)

    def create_archive(self, log_files: List[str], archive_name: str = None) -> Optional[str]:
        """Create an archive of log files"""
        try:
            if archive_name is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                archive_name = f"logs_archive_{timestamp}.tar.gz"

            archive_path = self.archive_directory / archive_name

            with tarfile.open(archive_path, "w:gz") as tar:
                for log_file in log_files:
                    if os.path.exists(log_file):
                        tar.add(log_file, arcname=os.path.basename(log_file))

            logging.info(f"Created archive: {archive_path}")
            return str(archive_path)

        except Exception as e:
            logging.error(f"Failed to create archive: {e}")
            return None

    def extract_archive(self, archive_path: str, extract_to: str = None) -> bool:
        """Extract an archive"""
        try:
            if extract_to is None:
                extract_to = tempfile.mkdtemp(prefix="log_extract_")

            with tarfile.open(archive_path, "r:gz") as tar:
                tar.extractall(extract_to)

            logging.info(f"Extracted archive to: {extract_to}")
            return True

        except Exception as e:
            logging.error(f"Failed to extract archive {archive_path}: {e}")
            return False

    def list_archives(self) -> List[Dict[str, Any]]:
        """List available archives"""
        archives = []

        try:
            for archive_file in self.archive_directory.glob("*.tar.gz"):
                stat = archive_file.stat()
                archives.append({
                    "name": archive_file.name,
                    "path": str(archive_file),
                    "size": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_ctime),
                    "modified": datetime.fromtimestamp(stat.st_mtime)
                })

            return sorted(archives, key=lambda x: x["created"], reverse=True)

        except Exception as e:
            logging.error(f"Failed to list archives: {e}")
            return []

    def delete_archive(self, archive_name: str) -> bool:
        """Delete an archive"""
        try:
            archive_path = self.archive_directory / archive_name
            if archive_path.exists():
                archive_path.unlink()
                logging.info(f"Deleted archive: {archive_name}")
                return True
            else:
                logging.warning(f"Archive not found: {archive_name}")
                return False

        except Exception as e:
            logging.error(f"Failed to delete archive {archive_name}: {e}")
            return False

    def get_archive_stats(self) -> Dict[str, Any]:
        """Get archive statistics"""
        try:
            archives = self.list_archives()
            total_size = sum(archive["size"] for archive in archives)
            oldest = min((archive["created"] for archive in archives), default=None)
            newest = max((archive["created"] for archive in archives), default=None)

            return {
                "total_archives": len(archives),
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / 1024 / 1024, 2),
                "oldest_archive": oldest.isoformat() if oldest else None,
                "newest_archive": newest.isoformat() if newest else None
            }

        except Exception as e:
            logging.error(f"Failed to get archive stats: {e}")
            return {}


class LogRetentionManager:
    """Manages log retention policies and cleanup"""

    def __init__(self, retention_days: int = 30):
        self.retention_days = retention_days
        self._lock = threading.Lock()

    def cleanup_old_logs(self, log_directory: str) -> Dict[str, Any]:
        """Clean up old log files based on retention policy"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            deleted_files = []
            total_size_freed = 0

            log_dir = Path(log_directory)
            if not log_dir.exists():
                return {"deleted_files": [], "total_size_freed": 0}

            # Find files to delete
            for log_file in log_dir.glob("*.log*"):
                try:
                    if log_file.stat().st_mtime < cutoff_date.timestamp():
                        file_size = log_file.stat().st_size
                        log_file.unlink()
                        deleted_files.append(str(log_file))
                        total_size_freed += file_size
                except OSError as e:
                    logging.error(f"Failed to delete {log_file}: {e}")

            return {
                "deleted_files": deleted_files,
                "total_size_freed": total_size_freed,
                "total_size_freed_mb": round(total_size_freed / 1024 / 1024, 2),
                "cutoff_date": cutoff_date.isoformat()
            }

        except Exception as e:
            logging.error(f"Failed to cleanup old logs: {e}")
            return {"deleted_files": [], "total_size_freed": 0}

    def get_disk_usage(self, log_directory: str) -> Dict[str, Any]:
        """Get disk usage statistics for log directory"""
        try:
            log_dir = Path(log_directory)
            if not log_dir.exists():
                return {"total_size": 0, "file_count": 0}

            total_size = 0
            file_count = 0

            for log_file in log_dir.rglob("*"):
                if log_file.is_file():
                    total_size += log_file.stat().st_size
                    file_count += 1

            return {
                "total_size": total_size,
                "total_size_mb": round(total_size / 1024 / 1024, 2),
                "file_count": file_count,
                "directory": str(log_dir)
            }

        except Exception as e:
            logging.error(f"Failed to get disk usage: {e}")
            return {"total_size": 0, "file_count": 0}

    def start_retention_scheduler(self, check_interval: int = 3600) -> None:
        """Start retention cleanup scheduler"""
        def cleanup_loop():
            while True:
                try:
                    time.sleep(check_interval)
                    config = get_logging_config()
                    if config.compliance.enabled:
                        result = self.cleanup_old_logs(config.log_directory)
                        if result["deleted_files"]:
                            logging.info(f"Retention cleanup: deleted {len(result['deleted_files'])} files, "
                                       f"freed {result['total_size_freed_mb']} MB")
                except Exception as e:
                    logging.error(f"Retention scheduler error: {e}")

        # Start scheduler in background thread
        scheduler_thread = threading.Thread(target=cleanup_loop, daemon=True, name="retention_scheduler")
        scheduler_thread.start()


# Global instances
log_rotator = None
archive_manager = None
retention_manager = None


def initialize_rotation_system() -> None:
    """Initialize the log rotation system"""
    global log_rotator, archive_manager, retention_manager

    config = get_logging_config()

    # Initialize components
    log_rotator = LogRotator(config.rotation)
    archive_manager = LogArchiveManager()
    retention_manager = LogRetentionManager(config.compliance.retention_days)

    # Start monitoring
    log_rotator.start_monitoring()
    retention_manager.start_retention_scheduler()

    logging.info("Log rotation system initialized")


def get_log_rotator() -> Optional[LogRotator]:
    """Get the global log rotator instance"""
    return log_rotator


def get_archive_manager() -> Optional[LogArchiveManager]:
    """Get the global archive manager instance"""
    return archive_manager


def get_retention_manager() -> Optional[LogRetentionManager]:
    """Get the global retention manager instance"""
    return retention_manager


def rotate_log_file(file_path: str, force: bool = False) -> bool:
    """Rotate a specific log file"""
    if log_rotator:
        return log_rotator.rotate_file(file_path, force)
    return False


def create_log_archive(log_files: List[str], archive_name: str = None) -> Optional[str]:
    """Create an archive of log files"""
    if archive_manager:
        return archive_manager.create_archive(log_files, archive_name)
    return None


def cleanup_old_logs(log_directory: str = None) -> Dict[str, Any]:
    """Clean up old log files"""
    if retention_manager:
        config = get_logging_config()
        log_dir = log_directory or config.log_directory
        return retention_manager.cleanup_old_logs(log_dir)
    return {"deleted_files": [], "total_size_freed": 0}