"""
Advanced Operating System Scheduling Algorithms.
Implements multiple scheduling algorithms beyond Round Robin.
"""

import threading
import queue
import time
import logging
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class SchedulingAlgorithm(Enum):
    """Scheduling algorithm types."""
    FCFS = "FCFS"  # First Come First Served
    SJF = "SJF"    # Shortest Job First
    PRIORITY = "PRIORITY"  # Priority-based
    RR = "RR"      # Round Robin
    MULTILEVEL = "MULTILEVEL"  # Multilevel Queue


@dataclass
class Process:
    """Represents a process/task in the OS scheduler."""
    pid: str
    arrival_time: float
    burst_time: float = 0.0  # Estimated execution time
    priority: int = 0
    remaining_time: float = 0.0
    start_time: Optional[float] = None
    completion_time: Optional[float] = None
    waiting_time: float = 0.0
    turnaround_time: float = 0.0
    task_data: Dict = field(default_factory=dict)
    cancelled: bool = False


class AdvancedScheduler:
    """
    Advanced scheduler supporting multiple OS scheduling algorithms.
    """
    
    def __init__(self, algorithm: SchedulingAlgorithm = SchedulingAlgorithm.FCFS,
                 executor_func: Callable = None):
        """
        Initialize the scheduler.
        
        Args:
            algorithm: Scheduling algorithm to use
            executor_func: Function to execute tasks
        """
        self.algorithm = algorithm
        self.executor_func = executor_func
        self.processes: Dict[str, Process] = {}
        self.ready_queue: queue.Queue = queue.Queue()
        self.running_process: Optional[Process] = None
        self.worker_thread: Optional[threading.Thread] = None
        self.running = False
        self.lock = threading.Lock()
        self.completed_processes: List[Process] = []
        self.result_callbacks: Dict[str, Callable] = {}
        
        # Statistics
        self.total_processes = 0
        self.total_waiting_time = 0.0
        self.total_turnaround_time = 0.0
    
    def start(self):
        """Start the scheduler."""
        if self.running:
            return
        
        self.running = True
        self.worker_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.worker_thread.start()
        logger.info(f"Advanced scheduler started with {self.algorithm.value} algorithm")
    
    def stop(self):
        """Stop the scheduler."""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        logger.info("Advanced scheduler stopped")
    
    def submit_task(self, task: Dict[str, Any], result_callback: Optional[Callable] = None):
        """
        Submit a task as a process.
        
        Args:
            task: Task dictionary
            result_callback: Callback for result
        """
        pid = task.get("task_id", f"P{self.total_processes}")
        priority = task.get("priority", 0)
        estimated_time = task.get("estimated_time", 1.0)  # Default 1 second
        
        process = Process(
            pid=pid,
            arrival_time=time.time(),
            burst_time=estimated_time,
            priority=priority,
            remaining_time=estimated_time,
            task_data=task
        )
        
        with self.lock:
            self.processes[pid] = process
            self.total_processes += 1
        
        if result_callback:
            self.result_callbacks[pid] = result_callback
        
        # Add to ready queue based on algorithm
        self._enqueue_process(process)
        logger.debug(f"Process {pid} submitted (algorithm: {self.algorithm.value})")
    
    def _enqueue_process(self, process: Process):
        """Enqueue process based on scheduling algorithm."""
        if self.algorithm == SchedulingAlgorithm.FCFS:
            self.ready_queue.put(process)
        
        elif self.algorithm == SchedulingAlgorithm.SJF:
            # Use priority queue sorted by burst time
            # For simplicity, we'll use a list and sort
            items = []
            while not self.ready_queue.empty():
                items.append(self.ready_queue.get())
            items.append(process)
            items.sort(key=lambda p: p.burst_time)
            for p in items:
                self.ready_queue.put(p)
        
        elif self.algorithm == SchedulingAlgorithm.PRIORITY:
            # Priority queue sorted by priority (higher first)
            items = []
            while not self.ready_queue.empty():
                items.append(self.ready_queue.get())
            items.append(process)
            items.sort(key=lambda p: -p.priority)  # Negative for descending
            for p in items:
                self.ready_queue.put(p)
        
        elif self.algorithm == SchedulingAlgorithm.RR:
            self.ready_queue.put(process)
        
        else:
            self.ready_queue.put(process)
    
    def _scheduler_loop(self):
        """Main scheduler loop."""
        while self.running:
            try:
                if self.running_process is None:
                    # Get next process from ready queue
                    try:
                        process = self.ready_queue.get(timeout=1.0)
                    except queue.Empty:
                        continue
                    
                    self.running_process = process
                    process.start_time = time.time()
                    logger.info(f"Process {process.pid} started execution")
                
                # Execute the process
                if self.running_process and not self.running_process.cancelled:
                    process = self.running_process
                    
                    try:
                        # Execute task
                        result = self.executor_func(process.task_data)
                        execution_time = time.time() - process.start_time
                        
                        # Update process statistics
                        process.completion_time = time.time()
                        process.turnaround_time = process.completion_time - process.arrival_time
                        process.waiting_time = process.turnaround_time - process.burst_time
                        
                        # Update global statistics
                        with self.lock:
                            self.total_waiting_time += process.waiting_time
                            self.total_turnaround_time += process.turnaround_time
                            self.completed_processes.append(process)
                            if process.pid in self.processes:
                                del self.processes[process.pid]
                        
                        # Create result message
                        result_msg = {
                            "type": "CPU_RESULT",
                            "task_id": process.pid,
                            "result": result,
                            "error": None,
                            "execution_time": execution_time,
                            "waiting_time": process.waiting_time,
                            "turnaround_time": process.turnaround_time
                        }
                        
                        # Call callback
                        if process.pid in self.result_callbacks:
                            self.result_callbacks[process.pid](result_msg)
                            del self.result_callbacks[process.pid]
                        
                        logger.info(f"Process {process.pid} completed (WT: {process.waiting_time:.2f}s, TT: {process.turnaround_time:.2f}s)")
                    
                    except Exception as e:
                        execution_time = time.time() - process.start_time
                        logger.error(f"Process {process.pid} failed: {e}")
                        
                        result_msg = {
                            "type": "CPU_RESULT",
                            "task_id": process.pid,
                            "result": None,
                            "error": str(e)
                        }
                        
                        if process.pid in self.result_callbacks:
                            self.result_callbacks[process.pid](result_msg)
                            del self.result_callbacks[process.pid]
                
                # Clear running process
                self.running_process = None
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}", exc_info=True)
    
    def cancel_process(self, pid: str) -> bool:
        """Cancel a process."""
        with self.lock:
            if pid in self.processes:
                process = self.processes[pid]
                process.cancelled = True
                if self.running_process and self.running_process.pid == pid:
                    self.running_process = None
                return True
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get scheduling statistics."""
        with self.lock:
            completed = len(self.completed_processes)
            avg_waiting = self.total_waiting_time / completed if completed > 0 else 0.0
            avg_turnaround = self.total_turnaround_time / completed if completed > 0 else 0.0
            
            return {
                "algorithm": self.algorithm.value,
                "total_processes": self.total_processes,
                "completed_processes": completed,
                "running_process": self.running_process.pid if self.running_process else None,
                "queue_size": self.ready_queue.qsize(),
                "average_waiting_time": avg_waiting,
                "average_turnaround_time": avg_turnaround,
                "throughput": completed / (time.time() - self.completed_processes[0].arrival_time) if completed > 0 and self.completed_processes else 0.0
            }
    
    def set_algorithm(self, algorithm: SchedulingAlgorithm):
        """Change scheduling algorithm."""
        with self.lock:
            self.algorithm = algorithm
            logger.info(f"Scheduling algorithm changed to {algorithm.value}")






