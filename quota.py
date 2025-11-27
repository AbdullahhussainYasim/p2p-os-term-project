"""
Resource quota management system.
"""

import threading
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ResourceQuota:
    """
    Manages resource quotas and limits for peers.
    """
    
    def __init__(self, max_cpu_tasks: int = 100, max_memory_keys: int = 1000,
                 max_storage_mb: int = 100, window_seconds: int = 3600):
        """
        Initialize resource quotas.
        
        Args:
            max_cpu_tasks: Maximum CPU tasks per time window
            max_memory_keys: Maximum memory keys
            max_storage_mb: Maximum storage in MB
            window_seconds: Time window for rate limiting
        """
        self.max_cpu_tasks = max_cpu_tasks
        self.max_memory_keys = max_memory_keys
        self.max_storage_mb = max_storage_mb
        self.window = timedelta(seconds=window_seconds)
        
        self.lock = threading.Lock()
        self.cpu_task_times: list = []  # Timestamps of CPU tasks
        self.memory_key_count = 0
        self.storage_bytes = 0
    
    def check_cpu_quota(self) -> tuple[bool, Optional[str]]:
        """
        Check if CPU task quota allows new task.
        
        Returns:
            (allowed, error_message)
        """
        now = datetime.now()
        
        with self.lock:
            # Remove old entries outside window
            self.cpu_task_times = [
                t for t in self.cpu_task_times 
                if now - t < self.window
            ]
            
            if len(self.cpu_task_times) >= self.max_cpu_tasks:
                return False, f"CPU task quota exceeded ({self.max_cpu_tasks} per {self.window.total_seconds()}s)"
            
            self.cpu_task_times.append(now)
            return True, None
    
    def check_memory_quota(self, current_keys: int) -> tuple[bool, Optional[str]]:
        """
        Check if memory quota allows new key.
        
        Args:
            current_keys: Current number of memory keys
        
        Returns:
            (allowed, error_message)
        """
        with self.lock:
            if current_keys >= self.max_memory_keys:
                return False, f"Memory quota exceeded (max {self.max_memory_keys} keys)"
            return True, None
    
    def check_storage_quota(self, additional_bytes: int) -> tuple[bool, Optional[str]]:
        """
        Check if storage quota allows file upload.
        
        Args:
            additional_bytes: Bytes to be added
        
        Returns:
            (allowed, error_message)
        """
        with self.lock:
            new_total = self.storage_bytes + additional_bytes
            max_bytes = self.max_storage_mb * 1024 * 1024
            
            if new_total > max_bytes:
                return False, f"Storage quota exceeded (max {self.max_storage_mb} MB)"
            
            self.storage_bytes = new_total
            return True, None
    
    def release_storage(self, bytes_released: int):
        """Release storage quota when file is deleted."""
        with self.lock:
            self.storage_bytes = max(0, self.storage_bytes - bytes_released)
    
    def get_usage(self) -> Dict:
        """Get current quota usage."""
        now = datetime.now()
        
        with self.lock:
            # Count tasks in current window
            recent_tasks = sum(1 for t in self.cpu_task_times 
                             if now - t < self.window)
            
            max_storage_bytes = self.max_storage_mb * 1024 * 1024
            
            return {
                "cpu_tasks": {
                    "used": recent_tasks,
                    "limit": self.max_cpu_tasks,
                    "window_seconds": self.window.total_seconds()
                },
                "memory_keys": {
                    "limit": self.max_memory_keys
                },
                "storage": {
                    "used_mb": self.storage_bytes / (1024 * 1024),
                    "limit_mb": self.max_storage_mb,
                    "used_bytes": self.storage_bytes,
                    "limit_bytes": max_storage_bytes
                }
            }






