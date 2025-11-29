"""
Deadlock Detection using Banker's Algorithm and Resource Allocation Graph.
"""

import threading
import logging
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ResourceType(Enum):
    """Resource types."""
    CPU = "CPU"
    MEMORY = "MEMORY"
    DISK = "DISK"
    NETWORK = "NETWORK"


@dataclass
class Resource:
    """Represents a system resource."""
    resource_id: str
    resource_type: ResourceType
    total_units: int
    available_units: int
    allocated: Dict[str, int] = None  # process_id -> units
    
    def __post_init__(self):
        if self.allocated is None:
            self.allocated = {}


class DeadlockDetector:
    """
    Deadlock detection using Banker's Algorithm and cycle detection.
    """
    
    def __init__(self):
        """Initialize deadlock detector."""
        self.resources: Dict[str, Resource] = {}
        self.processes: Dict[str, Dict] = {}  # pid -> {allocation, max_need, need}
        self.lock = threading.Lock()
    
    def register_resource(self, resource_id: str, resource_type: ResourceType, 
                         total_units: int):
        """
        Register a system resource.
        
        Args:
            resource_id: Resource identifier
            resource_type: Type of resource
            total_units: Total available units
        """
        with self.lock:
            self.resources[resource_id] = Resource(
                resource_id=resource_id,
                resource_type=resource_type,
                total_units=total_units,
                available_units=total_units
            )
            logger.info(f"Resource {resource_id} registered ({total_units} units)")
    
    def register_process(self, pid: str, max_need: Dict[str, int]):
        """
        Register a process with maximum resource needs.
        
        Args:
            pid: Process ID
            max_need: Maximum units needed for each resource (resource_id -> units)
        """
        with self.lock:
            allocation = {rid: 0 for rid in max_need.keys()}
            need = {rid: max_need[rid] for rid in max_need.keys()}
            
            self.processes[pid] = {
                "allocation": allocation,
                "max_need": max_need,
                "need": need
            }
            logger.debug(f"Process {pid} registered with max needs: {max_need}")
    
    def request_resource(self, pid: str, resource_id: str, units: int) -> Tuple[bool, Optional[str]]:
        """
        Request resource allocation (Banker's Algorithm).
        
        Args:
            pid: Process ID
            resource_id: Resource identifier
            units: Number of units requested
        
        Returns:
            (safe, error_message)
        """
        with self.lock:
            if pid not in self.processes:
                return False, f"Process {pid} not registered"
            
            if resource_id not in self.resources:
                return False, f"Resource {resource_id} not registered"
            
            resource = self.resources[resource_id]
            process = self.processes[pid]
            
            # Check if request exceeds need
            if units > process["need"].get(resource_id, 0):
                return False, f"Request exceeds need"
            
            # Check if resources are available
            if units > resource.available_units:
                return False, f"Insufficient resources available"
            
            # Try allocation
            resource.available_units -= units
            resource.allocated[pid] = resource.allocated.get(pid, 0) + units
            process["allocation"][resource_id] = process["allocation"].get(resource_id, 0) + units
            process["need"][resource_id] = process["need"].get(resource_id, 0) - units
            
            # Check if system is in safe state
            if self._is_safe_state():
                logger.info(f"Resource allocation granted: {pid} -> {resource_id} ({units} units)")
                return True, None
            else:
                # Rollback allocation
                resource.available_units += units
                resource.allocated[pid] -= units
                if resource.allocated[pid] == 0:
                    del resource.allocated[pid]
                process["allocation"][resource_id] -= units
                process["need"][resource_id] += units
                
                logger.warning(f"Resource allocation denied (unsafe state): {pid} -> {resource_id}")
                return False, "Allocation would lead to unsafe state"
    
    def release_resource(self, pid: str, resource_id: str, units: int) -> bool:
        """
        Release allocated resources.
        
        Args:
            pid: Process ID
            resource_id: Resource identifier
            units: Number of units to release
        
        Returns:
            True if successful
        """
        with self.lock:
            if pid not in self.processes:
                return False
            
            if resource_id not in self.resources:
                return False
            
            resource = self.resources[resource_id]
            process = self.processes[pid]
            
            allocated = process["allocation"].get(resource_id, 0)
            if units > allocated:
                return False
            
            # Release resources
            resource.available_units += units
            resource.allocated[pid] = resource.allocated.get(pid, 0) - units
            if resource.allocated[pid] == 0:
                del resource.allocated[pid]
            
            process["allocation"][resource_id] -= units
            process["need"][resource_id] = process["need"].get(resource_id, 0) + units
            
            logger.info(f"Resource released: {pid} -> {resource_id} ({units} units)")
            return True
    
    def _is_safe_state(self) -> bool:
        """
        Check if system is in safe state using Banker's Algorithm.
        
        Returns:
            True if system is in safe state
        """
        # Get available resources
        available = {rid: res.available_units for rid, res in self.resources.items()}
        
        # Initialize work and finish arrays
        work = available.copy()
        finish = {pid: False for pid in self.processes.keys()}
        
        # Find a process that can finish
        while True:
            found = False
            for pid, process in self.processes.items():
                if not finish[pid]:
                    # Check if need <= work for all resources
                    can_finish = True
                    for rid, need in process["need"].items():
                        if need > work.get(rid, 0):
                            can_finish = False
                            break
                    
                    if can_finish:
                        # Process can finish - release its resources
                        for rid, allocated in process["allocation"].items():
                            work[rid] = work.get(rid, 0) + allocated
                        finish[pid] = True
                        found = True
                        break
            
            if not found:
                break
        
        # Check if all processes can finish
        return all(finish.values())
    
    def detect_deadlock(self) -> Tuple[bool, List[str]]:
        """
        Detect deadlock using cycle detection in resource allocation graph.
        
        Returns:
            (deadlock_exists, list_of_deadlocked_processes)
        """
        with self.lock:
            # Build wait-for graph
            wait_for_graph: Dict[str, Set[str]] = {pid: set() for pid in self.processes.keys()}
            
            for pid, process in self.processes.items():
                # Process is waiting for resources it needs
                for rid, need in process["need"].items():
                    if need > 0:
                        # Check which processes hold these resources
                        resource = self.resources.get(rid)
                        if resource:
                            for holder_pid, allocated in resource.allocated.items():
                                if allocated > 0 and holder_pid != pid:
                                    wait_for_graph[pid].add(holder_pid)
            
            # Detect cycles using DFS
            visited = set()
            rec_stack = set()
            deadlocked = []
            
            def has_cycle(node: str) -> bool:
                visited.add(node)
                rec_stack.add(node)
                
                for neighbor in wait_for_graph.get(node, set()):
                    if neighbor not in visited:
                        if has_cycle(neighbor):
                            deadlocked.append(node)
                            return True
                    elif neighbor in rec_stack:
                        # Cycle detected
                        deadlocked.append(node)
                        deadlocked.append(neighbor)
                        return True
                
                rec_stack.remove(node)
                return False
            
            for pid in self.processes.keys():
                if pid not in visited:
                    has_cycle(pid)
            
            deadlock_exists = len(deadlocked) > 0
            if deadlock_exists:
                logger.warning(f"Deadlock detected! Processes: {deadlocked}")
            
            return deadlock_exists, list(set(deadlocked))
    
    def get_resource_status(self) -> Dict:
        """Get current resource allocation status."""
        with self.lock:
            return {
                "resources": {
                    rid: {
                        "total": res.total_units,
                        "available": res.available_units,
                        "allocated": sum(res.allocated.values()),
                        "allocations": res.allocated.copy()
                    }
                    for rid, res in self.resources.items()
                },
                "processes": {
                    pid: {
                        "allocation": proc["allocation"].copy(),
                        "need": proc["need"].copy(),
                        "max_need": proc["max_need"].copy()
                    }
                    for pid, proc in self.processes.items()
                },
                "safe_state": self._is_safe_state()
            }






