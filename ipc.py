"""
Inter-Process Communication (IPC) mechanisms.
Implements message queues and semaphores.
"""

import threading
import queue
import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """IPC message."""
    sender: str
    receiver: str
    message_type: str
    data: Any
    timestamp: datetime = field(default_factory=datetime.now)
    message_id: str = None


class MessageQueue:
    """
    Message queue for inter-process communication.
    """
    
    def __init__(self, queue_id: str, max_size: int = 100):
        """
        Initialize message queue.
        
        Args:
            queue_id: Queue identifier
            max_size: Maximum queue size
        """
        self.queue_id = queue_id
        self.queue: queue.Queue = queue.Queue(maxsize=max_size)
        self.lock = threading.Lock()
        self.created_at = datetime.now()
        self.message_count = 0
    
    def send(self, message: Message) -> bool:
        """
        Send a message to the queue.
        
        Args:
            message: Message to send
        
        Returns:
            True if successful
        """
        try:
            if message.message_id is None:
                message.message_id = f"MSG{self.message_count}"
            self.queue.put(message, timeout=5.0)
            with self.lock:
                self.message_count += 1
            logger.debug(f"Message sent to queue {self.queue_id}: {message.message_id}")
            return True
        except queue.Full:
            logger.warning(f"Queue {self.queue_id} is full")
            return False
    
    def receive(self, receiver: str, timeout: float = None) -> Optional[Message]:
        """
        Receive a message from the queue.
        
        Args:
            receiver: Receiver process ID
            timeout: Timeout in seconds
        
        Returns:
            Message or None
        """
        try:
            message = self.queue.get(timeout=timeout)
            if message.receiver == receiver or message.receiver == "*":
                logger.debug(f"Message received from queue {self.queue_id}: {message.message_id}")
                return message
            else:
                # Put back if not for this receiver
                self.queue.put(message)
                return None
        except queue.Empty:
            return None
    
    def peek(self) -> Optional[Message]:
        """Peek at the next message without removing it."""
        try:
            message = self.queue.get_nowait()
            self.queue.put(message)  # Put it back
            return message
        except queue.Empty:
            return None
    
    def get_statistics(self) -> Dict:
        """Get queue statistics."""
        with self.lock:
            return {
                "queue_id": self.queue_id,
                "size": self.queue.qsize(),
                "max_size": self.queue.maxsize,
                "message_count": self.message_count,
                "created_at": self.created_at.isoformat()
            }


class Semaphore:
    """
    Semaphore for process synchronization.
    """
    
    def __init__(self, sem_id: str, initial_value: int = 1):
        """
        Initialize semaphore.
        
        Args:
            sem_id: Semaphore identifier
            initial_value: Initial semaphore value
        """
        self.sem_id = sem_id
        self.value = initial_value
        self.lock = threading.Lock()
        self.waiting_processes: List[str] = []
        self.created_at = datetime.now()
        self.operation_count = 0
    
    def wait(self, process_id: str) -> bool:
        """
        Wait (P) operation - decrement semaphore.
        
        Args:
            process_id: Process requesting the semaphore
        
        Returns:
            True if successful
        """
        with self.lock:
            self.operation_count += 1
            if self.value > 0:
                self.value -= 1
                logger.debug(f"Semaphore {self.sem_id}: wait() by {process_id} (value: {self.value})")
                return True
            else:
                # Block process
                if process_id not in self.waiting_processes:
                    self.waiting_processes.append(process_id)
                logger.debug(f"Semaphore {self.sem_id}: {process_id} blocked (value: {self.value})")
                return False
    
    def signal(self, process_id: str) -> bool:
        """
        Signal (V) operation - increment semaphore.
        
        Args:
            process_id: Process releasing the semaphore
        
        Returns:
            True if successful
        """
        with self.lock:
            self.operation_count += 1
            if self.waiting_processes:
                # Wake up a waiting process
                woken = self.waiting_processes.pop(0)
                logger.debug(f"Semaphore {self.sem_id}: {woken} woken up by {process_id}")
            else:
                self.value += 1
            logger.debug(f"Semaphore {self.sem_id}: signal() by {process_id} (value: {self.value})")
            return True
    
    def get_value(self) -> int:
        """Get current semaphore value."""
        with self.lock:
            return self.value
    
    def get_statistics(self) -> Dict:
        """Get semaphore statistics."""
        with self.lock:
            return {
                "sem_id": self.sem_id,
                "value": self.value,
                "waiting_processes": len(self.waiting_processes),
                "operation_count": self.operation_count,
                "created_at": self.created_at.isoformat()
            }


class IPCManager:
    """
    Manages IPC mechanisms (message queues and semaphores).
    """
    
    def __init__(self):
        """Initialize IPC manager."""
        self.message_queues: Dict[str, MessageQueue] = {}
        self.semaphores: Dict[str, Semaphore] = {}
        self.lock = threading.Lock()
    
    def create_message_queue(self, queue_id: str, max_size: int = 100) -> bool:
        """Create a message queue."""
        with self.lock:
            if queue_id in self.message_queues:
                return False
            self.message_queues[queue_id] = MessageQueue(queue_id, max_size)
            logger.info(f"Message queue created: {queue_id}")
            return True
    
    def get_message_queue(self, queue_id: str) -> Optional[MessageQueue]:
        """Get a message queue."""
        with self.lock:
            return self.message_queues.get(queue_id)
    
    def delete_message_queue(self, queue_id: str) -> bool:
        """Delete a message queue."""
        with self.lock:
            if queue_id in self.message_queues:
                del self.message_queues[queue_id]
                logger.info(f"Message queue deleted: {queue_id}")
                return True
            return False
    
    def create_semaphore(self, sem_id: str, initial_value: int = 1) -> bool:
        """Create a semaphore."""
        with self.lock:
            if sem_id in self.semaphores:
                return False
            self.semaphores[sem_id] = Semaphore(sem_id, initial_value)
            logger.info(f"Semaphore created: {sem_id} (initial: {initial_value})")
            return True
    
    def get_semaphore(self, sem_id: str) -> Optional[Semaphore]:
        """Get a semaphore."""
        with self.lock:
            return self.semaphores.get(sem_id)
    
    def delete_semaphore(self, sem_id: str) -> bool:
        """Delete a semaphore."""
        with self.lock:
            if sem_id in self.semaphores:
                del self.semaphores[sem_id]
                logger.info(f"Semaphore deleted: {sem_id}")
                return True
            return False
    
    def get_statistics(self) -> Dict:
        """Get IPC statistics."""
        with self.lock:
            return {
                "message_queues": {
                    qid: queue.get_statistics()
                    for qid, queue in self.message_queues.items()
                },
                "semaphores": {
                    sid: sem.get_statistics()
                    for sid, sem in self.semaphores.items()
                },
                "total_queues": len(self.message_queues),
                "total_semaphores": len(self.semaphores)
            }






