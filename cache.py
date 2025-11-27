"""
Task result caching system.
"""

import hashlib
import threading
import time
import logging
from typing import Dict, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ResultCache:
    """
    Caches task results to avoid re-executing identical tasks.
    """
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        """
        Initialize result cache.
        
        Args:
            max_size: Maximum number of cached results
            ttl_seconds: Time-to-live for cached results in seconds
        """
        self.cache: Dict[str, Dict] = {}
        self.lock = threading.Lock()
        self.max_size = max_size
        self.ttl = timedelta(seconds=ttl_seconds)
        self.hits = 0
        self.misses = 0
    
    def _compute_key(self, program: str, function: str, args: list) -> str:
        """Compute cache key from task parameters."""
        key_data = f"{program}:{function}:{str(args)}"
        return hashlib.sha256(key_data.encode()).hexdigest()
    
    def get(self, program: str, function: str, args: list) -> Optional[Any]:
        """
        Get cached result if available.
        
        Args:
            program: Program code
            function: Function name
            args: Function arguments
        
        Returns:
            Cached result or None if not found/expired
        """
        key = self._compute_key(program, function, args)
        
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]
                # Check if expired
                if datetime.now() - entry["timestamp"] < self.ttl:
                    self.hits += 1
                    logger.debug(f"Cache hit for task {key[:8]}")
                    return entry["result"]
                else:
                    # Expired, remove it
                    del self.cache[key]
                    logger.debug(f"Cache entry expired for {key[:8]}")
            
            self.misses += 1
            return None
    
    def put(self, program: str, function: str, args: list, result: Any):
        """
        Cache a task result.
        
        Args:
            program: Program code
            function: Function name
            args: Function arguments
            result: Task result
        """
        key = self._compute_key(program, function, args)
        
        with self.lock:
            # Remove oldest entry if cache is full
            if len(self.cache) >= self.max_size and key not in self.cache:
                # Remove oldest entry
                oldest_key = min(self.cache.keys(), 
                               key=lambda k: self.cache[k]["timestamp"])
                del self.cache[oldest_key]
            
            self.cache[key] = {
                "result": result,
                "timestamp": datetime.now()
            }
            logger.debug(f"Cached result for task {key[:8]}")
    
    def clear(self):
        """Clear all cached results."""
        with self.lock:
            self.cache.clear()
            logger.info("Result cache cleared")
    
    def get_stats(self) -> Dict:
        """Get cache statistics."""
        with self.lock:
            total = self.hits + self.misses
            hit_rate = self.hits / total if total > 0 else 0.0
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": hit_rate
            }






