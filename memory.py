"""
Distributed memory (key-value storage) handler.
"""

import threading
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class MemoryStore:
    """
    Thread-safe key-value storage for distributed memory sharing.
    """
    
    def __init__(self):
        """Initialize the memory store."""
        self.store: Dict[str, Any] = {}
        self.lock = threading.Lock()
        self.operation_count = 0
    
    def set(self, key: str, value: Any) -> bool:
        """
        Store a value with the given key.
        
        Args:
            key: Storage key
            value: Value to store
        
        Returns:
            True if successful
        """
        with self.lock:
            self.store[key] = value
            self.operation_count += 1
            logger.debug(f"Memory SET: {key} = {value}")
            return True
    
    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value by key.
        
        Args:
            key: Storage key
        
        Returns:
            Value if found, None otherwise
        """
        with self.lock:
            self.operation_count += 1
            value = self.store.get(key)
            if value is not None:
                logger.debug(f"Memory GET: {key} = {value}")
            else:
                logger.debug(f"Memory GET: {key} (not found)")
            return value
    
    def delete(self, key: str) -> bool:
        """
        Delete a key-value pair.
        
        Args:
            key: Storage key
        
        Returns:
            True if key existed and was deleted
        """
        with self.lock:
            if key in self.store:
                del self.store[key]
                self.operation_count += 1
                logger.debug(f"Memory DELETE: {key}")
                return True
            return False
    
    def list_keys(self) -> list:
        """List all stored keys."""
        with self.lock:
            return list(self.store.keys())
    
    def clear(self):
        """Clear all stored data."""
        with self.lock:
            self.store.clear()
            logger.info("Memory store cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory store statistics."""
        with self.lock:
            return {
                "key_count": len(self.store),
                "operation_count": self.operation_count
            }






