"""
Process Management System - Process tree, process groups, and process lifecycle.
"""

import threading
import time
import logging
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ProcessState(Enum):
    """Process states."""
    NEW = "NEW"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    TERMINATED = "TERMINATED"
    ZOMBIE = "ZOMBIE"


@dataclass
class ProcessInfo:
    """Process information structure."""
    pid: str
    ppid: Optional[str] = None  # Parent process ID
    state: ProcessState = ProcessState.NEW
    priority: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    cpu_time: float = 0.0
    memory_usage: int = 0
    children: List[str] = field(default_factory=list)
    group_id: Optional[str] = None
    task_data: Dict = field(default_factory=dict)


class ProcessManager:
    """
    Manages process tree, process groups, and process lifecycle.
    """
    
    def __init__(self):
        """Initialize process manager."""
        self.processes: Dict[str, ProcessInfo] = {}
        self.process_groups: Dict[str, Set[str]] = {}  # group_id -> set of pids
        self.lock = threading.Lock()
        self.next_pid = 1
    
    def create_process(self, task_data: Dict, parent_pid: Optional[str] = None,
                      group_id: Optional[str] = None) -> str:
        """
        Create a new process.
        
        Args:
            task_data: Task data
            parent_pid: Parent process ID
            group_id: Process group ID
        
        Returns:
            Process ID
        """
        pid = f"P{self.next_pid}"
        self.next_pid += 1
        
        process = ProcessInfo(
            pid=pid,
            ppid=parent_pid,
            state=ProcessState.NEW,
            priority=task_data.get("priority", 0),
            task_data=task_data,
            group_id=group_id
        )
        
        with self.lock:
            self.processes[pid] = process
            
            # Add to parent's children
            if parent_pid and parent_pid in self.processes:
                self.processes[parent_pid].children.append(pid)
            
            # Add to process group
            if group_id:
                if group_id not in self.process_groups:
                    self.process_groups[group_id] = set()
                self.process_groups[group_id].add(pid)
                process.group_id = group_id
        
        logger.info(f"Process {pid} created (parent: {parent_pid}, group: {group_id})")
        return pid
    
    def get_process(self, pid: str) -> Optional[ProcessInfo]:
        """Get process information."""
        with self.lock:
            return self.processes.get(pid)
    
    def set_state(self, pid: str, state: ProcessState):
        """Set process state."""
        with self.lock:
            if pid in self.processes:
                self.processes[pid].state = state
                logger.debug(f"Process {pid} state changed to {state.value}")
    
    def terminate_process(self, pid: str) -> bool:
        """
        Terminate a process and its children.
        
        Args:
            pid: Process ID
        
        Returns:
            True if process was terminated
        """
        with self.lock:
            if pid not in self.processes:
                return False
            
            process = self.processes[pid]
            
            # Terminate all children first
            for child_pid in process.children[:]:
                self.terminate_process(child_pid)
            
            # Mark as terminated
            process.state = ProcessState.TERMINATED
            
            # Remove from parent's children
            if process.ppid and process.ppid in self.processes:
                if pid in self.processes[process.ppid].children:
                    self.processes[process.ppid].children.remove(pid)
            
            # Remove from process group
            if process.group_id:
                group = self.process_groups.get(process.group_id)
                if group and pid in group:
                    group.remove(pid)
            
            # Remove process
            del self.processes[pid]
            
            logger.info(f"Process {pid} terminated")
            return True

    def add_cpu_time(self, pid: str, seconds: float):
        """Accumulate CPU time for a process."""
        with self.lock:
            if pid in self.processes:
                self.processes[pid].cpu_time += seconds
    
    def get_process_tree(self, root_pid: Optional[str] = None) -> Dict:
        """
        Get process tree starting from root.
        
        Args:
            root_pid: Root process ID (None for all root processes)
        
        Returns:
            Process tree structure
        """
        with self.lock:
            if root_pid:
                return self._build_tree(root_pid)
            else:
                # Find all root processes (no parent)
                roots = [pid for pid, proc in self.processes.items() if proc.ppid is None]
                return {
                    "roots": [self._build_tree(pid) for pid in roots],
                    "total_processes": len(self.processes)
                }
    
    def _build_tree(self, pid: str) -> Dict:
        """Build process tree recursively."""
        if pid not in self.processes:
            return None
        
        process = self.processes[pid]
        tree = {
            "pid": pid,
            "ppid": process.ppid,
            "state": process.state.value,
            "priority": process.priority,
            "children": []
        }
        
        for child_pid in process.children:
            child_tree = self._build_tree(child_pid)
            if child_tree:
                tree["children"].append(child_tree)
        
        return tree
    
    def create_process_group(self, group_id: str, pids: List[str]) -> bool:
        """
        Create a process group.
        
        Args:
            group_id: Group identifier
            pids: List of process IDs to add to group
        
        Returns:
            True if successful
        """
        with self.lock:
            if group_id not in self.process_groups:
                self.process_groups[group_id] = set()
            
            for pid in pids:
                if pid in self.processes:
                    self.process_groups[group_id].add(pid)
                    self.processes[pid].group_id = group_id
            
            logger.info(f"Process group {group_id} created with {len(pids)} processes")
            return True
    
    def get_group_processes(self, group_id: str) -> List[str]:
        """Get all processes in a group."""
        with self.lock:
            return list(self.process_groups.get(group_id, set()))
    
    def kill_group(self, group_id: str) -> int:
        """
        Terminate all processes in a group.
        
        Args:
            group_id: Group identifier
        
        Returns:
            Number of processes terminated
        """
        with self.lock:
            if group_id not in self.process_groups:
                return 0
            
            pids = list(self.process_groups[group_id])
            count = 0
            
            for pid in pids:
                if self.terminate_process(pid):
                    count += 1
            
            del self.process_groups[group_id]
            logger.info(f"Process group {group_id} terminated ({count} processes)")
            return count
    
    def get_statistics(self) -> Dict:
        """Get process management statistics."""
        with self.lock:
            states = {}
            for process in self.processes.values():
                state = process.state.value
                states[state] = states.get(state, 0) + 1
            
            return {
                "total_processes": len(self.processes),
                "process_groups": len(self.process_groups),
                "processes_by_state": states,
                "total_groups": len(self.process_groups)
            }






