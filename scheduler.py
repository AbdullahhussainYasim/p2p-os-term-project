"""
Round Robin (RR) scheduler for local task execution.
"""

import threading
import queue
import time
import logging
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class TaskWrapper:
    """Wrapper for tasks with priority and cancellation support."""
    task: Dict[str, Any]
    callback: Optional[Callable] = None
    priority: int = 0
    submitted_at: datetime = field(default_factory=datetime.now)
    cancelled: bool = False
    cancellation_lock: threading.Lock = field(default_factory=threading.Lock)
    
    def __lt__(self, other):
        """Compare by priority (higher priority first)."""
        return self.priority > other.priority


class RoundRobinScheduler:
    """
    Round Robin scheduler for CPU tasks.
    Tasks are executed in FIFO order (simulated RR without preemption).
    """
    
    def __init__(self, executor_func: Callable):
        """
        Initialize the scheduler.
        
        Args:
            executor_func: Function to execute tasks (task_dict) -> result
        """
        self.task_queue = queue.PriorityQueue()  # Now supports priority
        self.executor_func = executor_func
        self.worker_thread = None
        self.running = False
        self.current_load = 0.0  # Current CPU load (0.0 to 1.0)
        self.task_count = 0
        self.completed_tasks = 0
        self.cancelled_tasks = 0
        self.lock = threading.Lock()
        self.active_tasks: Dict[str, TaskWrapper] = {}  # task_id -> TaskWrapper
        
    def start(self):
        """Start the scheduler worker thread."""
        if self.running:
            return
        
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()
        logger.info("Round Robin scheduler started")
    
    def stop(self):
        """Stop the scheduler."""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        logger.info("Round Robin scheduler stopped")
    
    def submit_task(self, task: Dict[str, Any], result_callback: Optional[Callable] = None):
        """
        Submit a task to the scheduler.
        
        Args:
            task: Task dictionary with type, task_id, program, function, args, priority
            result_callback: Optional callback(result_dict) when task completes
        """
        task_id = task.get("task_id", f"T{self.task_count}")
        priority = task.get("priority", 0)
        self.task_count += 1
        
        task_wrapper = TaskWrapper(
            task=task,
            callback=result_callback,
            priority=priority
        )
        
        with self.lock:
            self.active_tasks[task_id] = task_wrapper
        
        self.task_queue.put(task_wrapper)
        logger.debug(f"Task {task_id} submitted to scheduler (priority: {priority})")
        
        # Update load based on queue size
        with self.lock:
            queue_size = self.task_queue.qsize()
            self.current_load = min(0.95, queue_size * 0.1)
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a task if it hasn't started executing.
        
        Args:
            task_id: Task identifier
        
        Returns:
            True if task was cancelled, False if not found or already executing
        """
        with self.lock:
            if task_id not in self.active_tasks:
                return False
            
            task_wrapper = self.active_tasks[task_id]
            with task_wrapper.cancellation_lock:
                if task_wrapper.cancelled:
                    return False
                task_wrapper.cancelled = True
                self.cancelled_tasks += 1
                logger.info(f"Task {task_id} cancelled")
                return True
    
    def get_load(self) -> float:
        """Get current CPU load estimate."""
        with self.lock:
            return self.current_load
    
    def _worker_loop(self):
        """Main worker loop - processes tasks in priority order."""
        while self.running:
            try:
                # Get next task (blocks with timeout to allow checking self.running)
                try:
                    task_wrapper = self.task_queue.get(timeout=1.0)
                except queue.Empty:
                    # Update load when queue is empty
                    with self.lock:
                        self.current_load = 0.0
                    continue
                
                task = task_wrapper.task
                task_id = task.get("task_id", "unknown")
                
                # Check if cancelled
                with task_wrapper.cancellation_lock:
                    if task_wrapper.cancelled:
                        logger.info(f"Task {task_id} was cancelled, skipping")
                        with self.lock:
                            if task_id in self.active_tasks:
                                del self.active_tasks[task_id]
                        self.task_queue.task_done()
                        continue
                
                logger.info(f"Processing task {task_id} (priority: {task_wrapper.priority}, queue size: {self.task_queue.qsize()})")
                
                # Execute task
                start_time = time.time()
                try:
                    result = self.executor_func(task)
                    execution_time = time.time() - start_time
                    logger.info(f"Task {task_id} completed in {execution_time:.2f}s")
                    
                    # Check if cancelled during execution
                    with task_wrapper.cancellation_lock:
                        if task_wrapper.cancelled:
                            logger.info(f"Task {task_id} was cancelled during execution")
                            self.task_queue.task_done()
                            continue
                    
                    # Create result message
                    result_msg = {
                        "type": "CPU_RESULT",
                        "task_id": task_id,
                        "result": result,
                        "error": None
                    }
                    
                    # Call callback if registered
                    if task_wrapper.callback:
                        task_wrapper.callback(result_msg)
                    
                except Exception as e:
                    execution_time = time.time() - start_time
                    logger.error(f"Task {task_id} failed after {execution_time:.2f}s: {e}")
                    
                    # Create error result
                    result_msg = {
                        "type": "CPU_RESULT",
                        "task_id": task_id,
                        "result": None,
                        "error": str(e)
                    }
                    
                    # Call callback if registered
                    if task_wrapper.callback:
                        task_wrapper.callback(result_msg)
                
                finally:
                    # Remove from active tasks
                    with self.lock:
                        if task_id in self.active_tasks:
                            del self.active_tasks[task_id]
                    
                    self.task_queue.task_done()
                    self.completed_tasks += 1
                    
                    # Update load
                    with self.lock:
                        queue_size = self.task_queue.qsize()
                        self.current_load = min(0.95, queue_size * 0.1)
                
            except Exception as e:
                logger.error(f"Error in scheduler worker loop: {e}", exc_info=True)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics."""
        with self.lock:
            return {
                "queue_size": self.task_queue.qsize(),
                "current_load": self.current_load,
                "total_tasks": self.task_count,
                "completed_tasks": self.completed_tasks,
                "cancelled_tasks": self.cancelled_tasks,
                "active_tasks": len(self.active_tasks)
            }
    
    def list_tasks(self) -> list:
        """List all active tasks."""
        with self.lock:
            return [
                {
                    "task_id": task_id,
                    "priority": wrapper.priority,
                    "submitted_at": wrapper.submitted_at.isoformat(),
                    "cancelled": wrapper.cancelled
                }
                for task_id, wrapper in self.active_tasks.items()
            ]

