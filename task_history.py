"""
Task history and audit logging system.
"""

import threading
import time
import logging
from typing import Dict, List, Optional
from datetime import datetime
from collections import deque

logger = logging.getLogger(__name__)


class TaskHistory:
    """
    Maintains history of all executed tasks for auditing and monitoring.
    """
    
    def __init__(self, max_history: int = 1000):
        """
        Initialize task history.
        
        Args:
            max_history: Maximum number of tasks to keep in history
        """
        self.history: deque = deque(maxlen=max_history)
        self.lock = threading.Lock()
        self.task_stats: Dict[str, Dict] = {}  # task_id -> stats
    
    def record_task(self, task_id: str, task_type: str, status: str, 
                   result: any = None, error: str = None, 
                   execution_time: float = None, peer_info: str = None,
                   role: str = None, requested_by: str = None):
        """
        Record a task execution.
        
        Args:
            task_id: Task identifier
            task_type: Type of task (CPU_TASK, SET_MEM, etc.)
            status: Task status (SUCCESS, FAILED, CANCELLED)
            result: Task result (if successful)
            error: Error message (if failed)
            execution_time: Time taken to execute
            peer_info: Information about which peer executed it
        """
        record = {
            "task_id": task_id,
            "task_type": task_type,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "execution_time": execution_time
        }
        
        if peer_info:
            record["peer_info"] = peer_info
        if requested_by:
            record["requested_by"] = requested_by
        if role:
            record["role"] = role
        
        if result is not None:
            record["result"] = str(result)[:100]  # Truncate long results
        
        if error:
            record["error"] = error
        
        with self.lock:
            self.history.append(record)
            self.task_stats[task_id] = record
        
        logger.debug(f"Recorded task {task_id}: {status}")
    
    def get_history(self, limit: int = 100, task_type: str = None) -> List[Dict]:
        """
        Get task history.
        
        Args:
            limit: Maximum number of records to return
            task_type: Filter by task type (optional)
        
        Returns:
            List of task records
        """
        with self.lock:
            history = list(self.history)
            if task_type:
                history = [h for h in history if h.get("task_type") == task_type]
            return history[-limit:]
    
    def get_task_info(self, task_id: str) -> Optional[Dict]:
        """Get information about a specific task."""
        with self.lock:
            return self.task_stats.get(task_id)
    
    def get_statistics(self) -> Dict:
        """Get overall statistics."""
        with self.lock:
            total = len(self.history)
            if total == 0:
                return {
                    "total_tasks": 0,
                    "successful": 0,
                    "failed": 0,
                    "cancelled": 0,
                    "average_execution_time": 0.0
                }
            
            successful = sum(1 for h in self.history if h.get("status") == "SUCCESS")
            failed = sum(1 for h in self.history if h.get("status") == "FAILED")
            cancelled = sum(1 for h in self.history if h.get("status") == "CANCELLED")
            
            exec_times = [h.get("execution_time", 0) for h in self.history 
                         if h.get("execution_time") is not None]
            avg_time = sum(exec_times) / len(exec_times) if exec_times else 0.0
            
            return {
                "total_tasks": total,
                "successful": successful,
                "failed": failed,
                "cancelled": cancelled,
                "success_rate": successful / total if total > 0 else 0.0,
                "average_execution_time": avg_time
            }






