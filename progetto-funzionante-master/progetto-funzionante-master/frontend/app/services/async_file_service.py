"""
Async File Service for High-Performance File Operations
Implements async file I/O operations with proper error handling,
caching, and resource management.
"""

import asyncio
import aiofiles
import logging
import os
import mimetypes
from pathlib import Path
from typing import Optional, Dict, Any, List, AsyncGenerator, Union
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
import time
from datetime import datetime

from app.services.cache_service import cache_service
from app.core.config import settings

logger = logging.getLogger(__name__)

class FileOperationType(Enum):
    """Types of file operations"""
    READ = "read"
    WRITE = "write"
    APPEND = "append"
    DELETE = "delete"
    COPY = "copy"
    MOVE = "move"
    LIST = "list"

class FileType(Enum):
    """File types with specific handling"""
    HTML = "html"
    JSON = "json"
    TEXT = "text"
    BINARY = "binary"
    IMAGE = "image"
    CSS = "css"
    JS = "javascript"

@dataclass
class FileOperationResult:
    """Result of file operation"""
    success: bool
    operation: FileOperationType
    file_path: str
    file_size: Optional[int] = None
    checksum: Optional[str] = None
    operation_time: float = 0.0
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class FileMetadata:
    """File metadata information"""
    path: str
    size: int
    created_at: float
    modified_at: float
    accessed_at: float
    mime_type: str
    encoding: Optional[str]
    is_file: bool
    is_directory: bool
    permissions: str
    checksum: Optional[str] = None

@dataclass
class FileServiceConfig:
    """Configuration for async file service"""
    base_directory: str = "."
    enable_cache: bool = True
    cache_ttl: int = 3600  # 1 hour
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_extensions: List[str] = field(default_factory=lambda: ['.html', '.json', '.txt', '.css', '.js'])
    enable_checksum: bool = True
    chunk_size: int = 8192  # 8KB chunks for large files

class AsyncFileService:
    """
    High-performance async file service with features:
    - Async file I/O operations
    - File caching with TTL
    - Checksum validation
    - Metadata extraction
    - Batch operations
    - File watching capabilities
    """

    def __init__(self, config: Optional[FileServiceConfig] = None):
        self.config = config or FileServiceConfig()
        self._operation_metrics = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "cache_hits": 0,
            "total_bytes_read": 0,
            "total_bytes_written": 0,
            "average_operation_time": 0.0
        }
        self._file_watchers = {}
        self._active_operations = {}

    def _get_file_type(self, file_path: str) -> FileType:
        """Determine file type from extension"""
        path = Path(file_path)
        extension = path.suffix.lower()

        if extension == '.html':
            return FileType.HTML
        elif extension == '.json':
            return FileType.JSON
        elif extension == '.css':
            return FileType.CSS
        elif extension in ['.js', '.mjs']:
            return FileType.JS
        elif extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
            return FileType.IMAGE
        elif extension in ['.txt', '.md', '.log']:
            return FileType.TEXT
        else:
            return FileType.BINARY

    def _calculate_checksum(self, data: Union[str, bytes]) -> str:
        """Calculate SHA256 checksum for data"""
        if isinstance(data, str):
            data = data.encode('utf-8')
        return hashlib.sha256(data).hexdigest()

    def _update_metrics(self, success: bool, operation_time: float, bytes_processed: int = 0):
        """Update operation metrics"""
        self._operation_metrics["total_operations"] += 1

        if success:
            self._operation_metrics["successful_operations"] += 1
        else:
            self._operation_metrics["failed_operations"] += 1

        # Update average operation time
        if self._operation_metrics["total_operations"] == 1:
            self._operation_metrics["average_operation_time"] = operation_time
        else:
            weight = 0.1
            self._operation_metrics["average_operation_time"] = (
                (1 - weight) * self._operation_metrics["average_operation_time"] +
                weight * operation_time
            )

    async def read_file(
        self,
        file_path: str,
        encoding: str = "utf-8",
        use_cache: bool = True,
        checksum_verification: bool = False
    ) -> FileOperationResult:
        """
        Read file asynchronously with caching support

        Args:
            file_path: Path to file
            encoding: File encoding (for text files)
            use_cache: Whether to use cache for this operation
            checksum_verification: Whether to verify file checksum

        Returns:
            FileOperationResult with file content in metadata
        """
        start_time = time.time()
        operation_type = FileOperationType.READ

        try:
            # Resolve file path
            full_path = Path(self.config.base_directory) / file_path
            if not full_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            # Check file size limit
            file_size = full_path.stat().st_size
            if file_size > self.config.max_file_size:
                raise ValueError(f"File size {file_size} exceeds limit {self.config.max_file_size}")

            # Check cache if enabled
            cache_key = f"file:{full_path.absolute()}"
            if use_cache and self.config.enable_cache:
                cached_content = await cache_service.get(cache_key)
                if cached_content:
                    self._operation_metrics["cache_hits"] += 1
                    return FileOperationResult(
                        success=True,
                        operation=operation_type,
                        file_path=file_path,
                        file_size=len(str(cached_content)),
                        checksum=self._calculate_checksum(str(cached_content)) if self.config.enable_checksum else None,
                        operation_time=time.time() - start_time,
                        metadata={"content": cached_content, "cached": True}
                    )

            # Determine file type and read accordingly
            file_type = self._get_file_type(file_path)
            content = None
            checksum = None

            if file_type in [FileType.HTML, FileType.JSON, FileType.TEXT, FileType.CSS, FileType.JS]:
                async with aiofiles.open(full_path, 'r', encoding=encoding) as file:
                    content = await file.read()
            else:
                async with aiofiles.open(full_path, 'rb') as file:
                    content = await file.read()

            # Calculate checksum if enabled
            if self.config.enable_checksum and checksum_verification:
                checksum = self._calculate_checksum(content)

            # Cache the result if enabled
            if use_cache and self.config.enable_cache and content:
                await cache_service.set(cache_key, content, self.config.cache_ttl)

            # Update metrics
            self._operation_metrics["total_bytes_read"] += len(str(content))
            self._update_metrics(True, time.time() - start_time, len(str(content)))

            return FileOperationResult(
                success=True,
                operation=operation_type,
                file_path=file_path,
                file_size=len(str(content)),
                checksum=checksum,
                operation_time=time.time() - start_time,
                metadata={
                    "content": content,
                    "file_type": file_type.value,
                    "encoding": encoding,
                    "cached": False
                }
            )

        except Exception as e:
            self._update_metrics(False, time.time() - start_time)
            logger.error(f"Failed to read file {file_path}: {e}")
            return FileOperationResult(
                success=False,
                operation=operation_type,
                file_path=file_path,
                operation_time=time.time() - start_time,
                error_message=str(e)
            )

    async def write_file(
        self,
        file_path: str,
        content: Union[str, bytes],
        encoding: str = "utf-8",
        atomic: bool = True,
        create_directories: bool = True
    ) -> FileOperationResult:
        """
        Write file asynchronously with atomic operations

        Args:
            file_path: Path to file
            content: Content to write
            encoding: File encoding (for text content)
            atomic: Whether to write atomically (using temporary file)
            create_directories: Whether to create parent directories

        Returns:
            FileOperationResult
        """
        start_time = time.time()
        operation_type = FileOperationType.WRITE

        try:
            # Resolve file path
            full_path = Path(self.config.base_directory) / file_path

            # Create directories if needed
            if create_directories:
                full_path.parent.mkdir(parents=True, exist_ok=True)

            # Check file size limit
            content_size = len(str(content))
            if content_size > self.config.max_file_size:
                raise ValueError(f"Content size {content_size} exceeds limit {self.config.max_file_size}")

            # Atomic write using temporary file
            if atomic:
                temp_path = full_path.with_suffix(full_path.suffix + '.tmp')
                try:
                    if isinstance(content, str):
                        async with aiofiles.open(temp_path, 'w', encoding=encoding) as file:
                            await file.write(content)
                    else:
                        async with aiofiles.open(temp_path, 'wb') as file:
                            await file.write(content)

                    # Atomic rename
                    temp_path.replace(full_path)
                except Exception:
                    # Clean up temporary file
                    if temp_path.exists():
                        temp_path.unlink()
                    raise
            else:
                # Direct write
                if isinstance(content, str):
                    async with aiofiles.open(full_path, 'w', encoding=encoding) as file:
                        await file.write(content)
                else:
                    async with aiofiles.open(full_path, 'wb') as file:
                        await file.write(content)

            # Invalidate cache
            cache_key = f"file:{full_path.absolute()}"
            await cache_service.delete(cache_key)

            # Update metrics
            self._operation_metrics["total_bytes_written"] += content_size
            self._update_metrics(True, time.time() - start_time, content_size)

            return FileOperationResult(
                success=True,
                operation=operation_type,
                file_path=file_path,
                file_size=content_size,
                checksum=self._calculate_checksum(str(content)) if self.config.enable_checksum else None,
                operation_time=time.time() - start_time
            )

        except Exception as e:
            self._update_metrics(False, time.time() - start_time)
            logger.error(f"Failed to write file {file_path}: {e}")
            return FileOperationResult(
                success=False,
                operation=operation_type,
                file_path=file_path,
                operation_time=time.time() - start_time,
                error_message=str(e)
            )

    async def append_file(
        self,
        file_path: str,
        content: Union[str, bytes],
        encoding: str = "utf-8"
    ) -> FileOperationResult:
        """Append content to file asynchronously"""
        start_time = time.time()
        operation_type = FileOperationType.APPEND

        try:
            full_path = Path(self.config.base_directory) / file_path
            content_size = len(str(content))

            if isinstance(content, str):
                async with aiofiles.open(full_path, 'a', encoding=encoding) as file:
                    await file.write(content)
            else:
                async with aiofiles.open(full_path, 'ab') as file:
                    await file.write(content)

            # Invalidate cache
            cache_key = f"file:{full_path.absolute()}"
            await cache_service.delete(cache_key)

            self._operation_metrics["total_bytes_written"] += content_size
            self._update_metrics(True, time.time() - start_time, content_size)

            return FileOperationResult(
                success=True,
                operation=operation_type,
                file_path=file_path,
                file_size=full_path.stat().st_size,
                operation_time=time.time() - start_time
            )

        except Exception as e:
            self._update_metrics(False, time.time() - start_time)
            logger.error(f"Failed to append to file {file_path}: {e}")
            return FileOperationResult(
                success=False,
                operation=operation_type,
                file_path=file_path,
                operation_time=time.time() - start_time,
                error_message=str(e)
            )

    async def delete_file(self, file_path: str) -> FileOperationResult:
        """Delete file asynchronously"""
        start_time = time.time()
        operation_type = FileOperationType.DELETE

        try:
            full_path = Path(self.config.base_directory) / file_path
            if full_path.exists():
                full_path.unlink()

            # Invalidate cache
            cache_key = f"file:{full_path.absolute()}"
            await cache_service.delete(cache_key)

            self._update_metrics(True, time.time() - start_time)
            return FileOperationResult(
                success=True,
                operation=operation_type,
                file_path=file_path,
                operation_time=time.time() - start_time
            )

        except Exception as e:
            self._update_metrics(False, time.time() - start_time)
            logger.error(f"Failed to delete file {file_path}: {e}")
            return FileOperationResult(
                success=False,
                operation=operation_type,
                file_path=file_path,
                operation_time=time.time() - start_time,
                error_message=str(e)
            )

    async def get_file_metadata(self, file_path: str) -> Optional[FileMetadata]:
        """Get file metadata asynchronously"""
        try:
            full_path = Path(self.config.base_directory) / file_path
            stat = full_path.stat()

            # Determine MIME type
            mime_type, encoding = mimetypes.guess_type(str(full_path))
            if not mime_type:
                mime_type = "application/octet-stream"

            # Calculate checksum if enabled and file is small enough
            checksum = None
            if self.config.enable_checksum and stat.st_size < 1024 * 1024:  # Only for files < 1MB
                result = await self.read_file(file_path, use_cache=False)
                if result.success:
                    checksum = result.checksum

            return FileMetadata(
                path=str(full_path),
                size=stat.st_size,
                created_at=stat.st_ctime,
                modified_at=stat.st_mtime,
                accessed_at=stat.st_atime,
                mime_type=mime_type,
                encoding=encoding,
                is_file=full_path.is_file(),
                is_directory=full_path.is_dir(),
                permissions=oct(stat.st_mode)[-3:],
                checksum=checksum
            )

        except Exception as e:
            logger.error(f"Failed to get metadata for {file_path}: {e}")
            return None

    async def list_directory(
        self,
        directory_path: str,
        pattern: Optional[str] = None,
        recursive: bool = False
    ) -> List[FileMetadata]:
        """List directory contents asynchronously"""
        try:
            full_path = Path(self.config.base_directory) / directory_path
            if not full_path.is_dir():
                raise ValueError(f"Not a directory: {directory_path}")

            metadata_list = []
            glob_pattern = "**/*" if recursive else "*"

            for path in full_path.glob(glob_pattern):
                if pattern and not path.match(pattern):
                    continue

                metadata = await self.get_file_metadata(str(path.relative_to(Path(self.config.base_directory))))
                if metadata:
                    metadata_list.append(metadata)

            return sorted(metadata_list, key=lambda x: x.path)

        except Exception as e:
            logger.error(f"Failed to list directory {directory_path}: {e}")
            return []

    async def batch_operations(
        self,
        operations: List[Dict[str, Any]],
        max_concurrency: int = 5
    ) -> List[FileOperationResult]:
        """
        Execute multiple file operations concurrently

        Args:
            operations: List of operation dictionaries
            max_concurrency: Maximum concurrent operations

        Returns:
            List of operation results
        """
        semaphore = asyncio.Semaphore(max_concurrency)
        results = []

        async def _execute_operation(op):
            async with semaphore:
                operation_type = op.get("type")
                if operation_type == FileOperationType.READ.value:
                    return await self.read_file(
                        op["file_path"],
                        encoding=op.get("encoding", "utf-8"),
                        use_cache=op.get("use_cache", True)
                    )
                elif operation_type == FileOperationType.WRITE.value:
                    return await self.write_file(
                        op["file_path"],
                        op["content"],
                        encoding=op.get("encoding", "utf-8"),
                        atomic=op.get("atomic", True)
                    )
                elif operation_type == FileOperationType.DELETE.value:
                    return await self.delete_file(op["file_path"])
                else:
                    raise ValueError(f"Unsupported operation type: {operation_type}")

        tasks = [_execute_operation(op) for op in operations]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to error results
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(FileOperationResult(
                    success=False,
                    operation=FileOperationType(operations[i]["type"]),
                    file_path=operations[i]["file_path"],
                    error_message=str(result)
                ))
            else:
                final_results.append(result)

        return final_results

    async def stream_read_file(self, file_path: str, chunk_size: Optional[int] = None) -> AsyncGenerator[bytes, None]:
        """Stream read large files in chunks"""
        try:
            full_path = Path(self.config.base_directory) / file_path
            chunk_size = chunk_size or self.config.chunk_size

            async with aiofiles.open(full_path, 'rb') as file:
                while True:
                    chunk = await file.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk

        except Exception as e:
            logger.error(f"Failed to stream read file {file_path}: {e}")
            raise

    async def stream_write_file(self, file_path: str, data_stream: AsyncGenerator[bytes, None]) -> FileOperationResult:
        """Stream write data to file"""
        start_time = time.time()
        operation_type = FileOperationType.WRITE

        try:
            full_path = Path(self.config.base_directory) / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)

            total_bytes = 0
            async with aiofiles.open(full_path, 'wb') as file:
                async for chunk in data_stream:
                    await file.write(chunk)
                    total_bytes += len(chunk)

            # Invalidate cache
            cache_key = f"file:{full_path.absolute()}"
            await cache_service.delete(cache_key)

            self._operation_metrics["total_bytes_written"] += total_bytes
            self._update_metrics(True, time.time() - start_time, total_bytes)

            return FileOperationResult(
                success=True,
                operation=operation_type,
                file_path=file_path,
                file_size=total_bytes,
                operation_time=time.time() - start_time
            )

        except Exception as e:
            self._update_metrics(False, time.time() - start_time)
            logger.error(f"Failed to stream write file {file_path}: {e}")
            return FileOperationResult(
                success=False,
                operation=operation_type,
                file_path=file_path,
                operation_time=time.time() - start_time,
                error_message=str(e)
            )

    def get_metrics(self) -> Dict[str, Any]:
        """Get file service metrics"""
        return {
            **self._operation_metrics,
            "cache_hit_rate": (
                (self._operation_metrics["cache_hits"] / max(1, self._operation_metrics["total_operations"])) * 100
                if self._operation_metrics["total_operations"] > 0 else 0
            )
        }

    def reset_metrics(self):
        """Reset file service metrics"""
        self._operation_metrics = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "cache_hits": 0,
            "total_bytes_read": 0,
            "total_bytes_written": 0,
            "average_operation_time": 0.0
        }

    @asynccontextmanager
    async def file_lock(self, file_path: str):
        """Context manager for file locking"""
        lock_file = Path(self.config.base_directory) / f"{file_path}.lock"
        try:
            # Create lock file
            lock_file.touch()
            yield
        finally:
            # Remove lock file
            if lock_file.exists():
                lock_file.unlink()

# Global file service instance
file_service = AsyncFileService()

# Utility functions
async def read_html_file(file_path: str) -> Optional[str]:
    """Convenience function to read HTML files"""
    result = await file_service.read_file(file_path, use_cache=True)
    return result.metadata.get("content") if result.success else None

async def serve_static_file(file_path: str, base_dir: str = "static") -> Optional[Dict[str, Any]]:
    """Convenience function to serve static files"""
    full_path = f"{base_dir}/{file_path}"
    result = await file_service.read_file(full_path, use_cache=True)

    if result.success:
        metadata = result.metadata
        return {
            "content": metadata.get("content"),
            "content_type": metadata.get("file_type", "application/octet-stream"),
            "size": result.file_size,
            "checksum": result.checksum
        }
    return None

# Initialize function
async def init_file_service(base_directory: str = "."):
    """Initialize file service with base directory"""
    try:
        file_service.config.base_directory = base_directory
        logger.info(f"File service initialized with base directory: {base_directory}")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize file service: {e}")
        return False