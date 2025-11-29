"""
File storage handler for distributed disk sharing.
"""

import os
import threading
import logging
import base64
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class FileStorage:
    """
    Thread-safe file storage for distributed disk sharing.
    Files are stored in a local directory.
    """
    
    def __init__(self, storage_dir: str = "peer_storage"):
        """
        Initialize file storage.
        
        Args:
            storage_dir: Directory to store files
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.lock = threading.Lock()
        self.operation_count = 0
        logger.info(f"File storage initialized at: {self.storage_dir.absolute()}")
    
    def put_file(self, filename: str, data: bytes) -> bool:
        """
        Store a file.
        
        Args:
            filename: Name of the file
            data: File contents as bytes
        
        Returns:
            True if successful
        """
        # Sanitize filename to prevent directory traversal
        safe_filename = os.path.basename(filename)
        if not safe_filename or safe_filename in ('.', '..'):
            raise ValueError(f"Invalid filename: {filename}")
        
        file_path = self.storage_dir / safe_filename
        
        with self.lock:
            try:
                with open(file_path, 'wb') as f:
                    f.write(data)
                self.operation_count += 1
                logger.info(f"File PUT: {safe_filename} ({len(data)} bytes)")
                return True
            except Exception as e:
                logger.error(f"Failed to store file {safe_filename}: {e}")
                raise
    
    def get_file(self, filename: str) -> Optional[bytes]:
        """
        Retrieve a file.
        
        Args:
            filename: Name of the file
        
        Returns:
            File contents as bytes, or None if not found
        """
        safe_filename = os.path.basename(filename)
        file_path = self.storage_dir / safe_filename
        
        with self.lock:
            try:
                if not file_path.exists():
                    logger.debug(f"File GET: {safe_filename} (not found)")
                    return None
                
                with open(file_path, 'rb') as f:
                    data = f.read()
                self.operation_count += 1
                logger.info(f"File GET: {safe_filename} ({len(data)} bytes)")
                return data
            except Exception as e:
                logger.error(f"Failed to retrieve file {safe_filename}: {e}")
                return None
    
    def delete_file(self, filename: str) -> bool:
        """
        Delete a file.
        
        Args:
            filename: Name of the file
        
        Returns:
            True if file existed and was deleted
        """
        safe_filename = os.path.basename(filename)
        file_path = self.storage_dir / safe_filename
        
        with self.lock:
            try:
                if file_path.exists():
                    file_path.unlink()
                    self.operation_count += 1
                    logger.info(f"File DELETE: {safe_filename}")
                    return True
                return False
            except Exception as e:
                logger.error(f"Failed to delete file {safe_filename}: {e}")
                return False
    
    def list_files(self) -> list:
        """List all stored files."""
        with self.lock:
            try:
                return [f.name for f in self.storage_dir.iterdir() if f.is_file()]
            except Exception as e:
                logger.error(f"Failed to list files: {e}")
                return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get file storage statistics."""
        with self.lock:
            try:
                files = list(self.storage_dir.iterdir())
                total_size = sum(f.stat().st_size for f in files if f.is_file())
                return {
                    "file_count": len([f for f in files if f.is_file()]),
                    "total_size": total_size,
                    "operation_count": self.operation_count,
                    "storage_dir": str(self.storage_dir.absolute())
                }
            except Exception as e:
                logger.error(f"Failed to get storage stats: {e}")
                return {
                    "file_count": 0,
                    "total_size": 0,
                    "operation_count": self.operation_count,
                    "storage_dir": str(self.storage_dir.absolute())
                }






