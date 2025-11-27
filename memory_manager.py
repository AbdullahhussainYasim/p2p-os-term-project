"""
Memory Management - Allocation algorithms and fragmentation handling.
"""

import threading
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class AllocationAlgorithm(Enum):
    """Memory allocation algorithms."""
    FIRST_FIT = "FIRST_FIT"
    BEST_FIT = "BEST_FIT"
    WORST_FIT = "WORST_FIT"
    NEXT_FIT = "NEXT_FIT"


@dataclass
class MemoryBlock:
    """Represents a memory block."""
    start: int
    size: int
    allocated: bool = False
    process_id: Optional[str] = None
    next: Optional['MemoryBlock'] = None


class MemoryManager:
    """
    Manages memory allocation using various algorithms.
    """
    
    def __init__(self, total_memory: int, algorithm: AllocationAlgorithm = AllocationAlgorithm.FIRST_FIT):
        """
        Initialize memory manager.
        
        Args:
            total_memory: Total memory size in bytes
            algorithm: Allocation algorithm to use
        """
        self.total_memory = total_memory
        self.algorithm = algorithm
        self.lock = threading.Lock()
        
        # Initialize free list with one large block
        self.free_list = MemoryBlock(start=0, size=total_memory, allocated=False)
        self.allocated_blocks: Dict[str, MemoryBlock] = {}  # process_id -> block
        self.next_fit_start = self.free_list  # For NEXT_FIT algorithm
    
    def allocate(self, process_id: str, size: int) -> Tuple[bool, Optional[int]]:
        """
        Allocate memory for a process.
        
        Args:
            process_id: Process identifier
            size: Size in bytes
        
        Returns:
            (success, start_address)
        """
        with self.lock:
            if process_id in self.allocated_blocks:
                return False, None  # Process already has allocated memory
            
            block = self._find_block(size)
            if not block:
                logger.warning(f"Memory allocation failed for {process_id} (size: {size})")
                return False, None
            
            # Allocate the block
            if block.size == size:
                # Exact fit
                block.allocated = True
                block.process_id = process_id
                self._remove_from_free_list(block)
                self.allocated_blocks[process_id] = block
            else:
                # Split block
                new_block = MemoryBlock(
                    start=block.start,
                    size=size,
                    allocated=True,
                    process_id=process_id
                )
                block.start += size
                block.size -= size
                self.allocated_blocks[process_id] = new_block
            
            logger.info(f"Memory allocated: {process_id} -> {new_block.start if 'new_block' in locals() else block.start} ({size} bytes)")
            return True, self.allocated_blocks[process_id].start
    
    def deallocate(self, process_id: str) -> bool:
        """
        Deallocate memory for a process.
        
        Args:
            process_id: Process identifier
        
        Returns:
            True if successful
        """
        with self.lock:
            if process_id not in self.allocated_blocks:
                return False
            
            block = self.allocated_blocks[process_id]
            block.allocated = False
            block.process_id = None
            
            # Add back to free list and coalesce
            self._add_to_free_list(block)
            self._coalesce_free_blocks()
            
            del self.allocated_blocks[process_id]
            logger.info(f"Memory deallocated: {process_id}")
            return True
    
    def _find_block(self, size: int) -> Optional[MemoryBlock]:
        """Find a suitable block based on allocation algorithm."""
        if self.algorithm == AllocationAlgorithm.FIRST_FIT:
            return self._first_fit(size)
        elif self.algorithm == AllocationAlgorithm.BEST_FIT:
            return self._best_fit(size)
        elif self.algorithm == AllocationAlgorithm.WORST_FIT:
            return self._worst_fit(size)
        elif self.algorithm == AllocationAlgorithm.NEXT_FIT:
            return self._next_fit(size)
        else:
            return self._first_fit(size)
    
    def _first_fit(self, size: int) -> Optional[MemoryBlock]:
        """First fit algorithm."""
        current = self.free_list
        while current:
            if not current.allocated and current.size >= size:
                return current
            current = current.next
        return None
    
    def _best_fit(self, size: int) -> Optional[MemoryBlock]:
        """Best fit algorithm."""
        best = None
        current = self.free_list
        while current:
            if not current.allocated and current.size >= size:
                if best is None or current.size < best.size:
                    best = current
            current = current.next
        return best
    
    def _worst_fit(self, size: int) -> Optional[MemoryBlock]:
        """Worst fit algorithm."""
        worst = None
        current = self.free_list
        while current:
            if not current.allocated and current.size >= size:
                if worst is None or current.size > worst.size:
                    worst = current
            current = current.next
        return worst
    
    def _next_fit(self, size: int) -> Optional[MemoryBlock]:
        """Next fit algorithm."""
        start = self.next_fit_start
        current = start
        
        # First pass from next_fit_start
        while current:
            if not current.allocated and current.size >= size:
                self.next_fit_start = current.next if current.next else self.free_list
                return current
            current = current.next
            if current == start:
                break
        
        # Second pass from beginning
        current = self.free_list
        while current and current != start:
            if not current.allocated and current.size >= size:
                self.next_fit_start = current.next if current.next else self.free_list
                return current
            current = current.next
        
        return None
    
    def _remove_from_free_list(self, block: MemoryBlock):
        """Remove block from free list."""
        # This is handled by the allocation logic
        pass
    
    def _add_to_free_list(self, block: MemoryBlock):
        """Add block to free list."""
        # Insert in sorted order by start address
        if not self.free_list or block.start < self.free_list.start:
            block.next = self.free_list
            self.free_list = block
        else:
            current = self.free_list
            while current.next and current.next.start < block.start:
                current = current.next
            block.next = current.next
            current.next = block
    
    def _coalesce_free_blocks(self):
        """Coalesce adjacent free blocks."""
        current = self.free_list
        while current and current.next:
            if not current.allocated and not current.next.allocated:
                if current.start + current.size == current.next.start:
                    # Merge blocks
                    current.size += current.next.size
                    current.next = current.next.next
                else:
                    current = current.next
            else:
                current = current.next
    
    def get_fragmentation(self) -> Dict:
        """Calculate memory fragmentation."""
        with self.lock:
            total_free = 0
            largest_free = 0
            free_blocks = 0
            
            current = self.free_list
            while current:
                if not current.allocated:
                    total_free += current.size
                    largest_free = max(largest_free, current.size)
                    free_blocks += 1
                current = current.next
            
            external_fragmentation = 0.0
            if total_free > 0:
                external_fragmentation = 1.0 - (largest_free / total_free) if total_free > 0 else 0.0
            
            return {
                "total_memory": self.total_memory,
                "allocated_memory": sum(block.size for block in self.allocated_blocks.values()),
                "free_memory": total_free,
                "largest_free_block": largest_free,
                "free_blocks_count": free_blocks,
                "external_fragmentation": external_fragmentation,
                "fragmentation_percentage": external_fragmentation * 100
            }
    
    def get_statistics(self) -> Dict:
        """Get memory management statistics."""
        fragmentation = self.get_fragmentation()
        return {
            "algorithm": self.algorithm.value,
            "fragmentation": fragmentation,
            "allocated_processes": len(self.allocated_blocks),
            "allocations": {
                pid: {"start": block.start, "size": block.size}
                for pid, block in self.allocated_blocks.items()
            }
        }






