"""
Peer node implementation - acts as both client and server.
Provides CPU, memory, and disk resource sharing.
"""

import socket
import threading
import logging
import time
import base64
import os
from pathlib import Path
from typing import Dict, Optional, List, Tuple, Any
from datetime import datetime

import messages
import config
from scheduler import RoundRobinScheduler
from executor import CodeExecutor
from memory import MemoryStore
from storage import FileStorage
from task_history import TaskHistory
from cache import ResultCache
from quota import ResourceQuota
from distributed_memory import DistributedMemory
from os_scheduler import AdvancedScheduler, SchedulingAlgorithm
from process_manager import ProcessManager, ProcessState
from deadlock_detector import DeadlockDetector, ResourceType
from memory_manager import MemoryManager, AllocationAlgorithm
from ipc import IPCManager, Message

logger = logging.getLogger(__name__)


class Peer:
    """
    Peer node that can execute tasks, store memory, and share files.
    """
    
    def __init__(self, peer_port: int = None, tracker_host: str = None, tracker_port: int = None):
        """
        Initialize the peer.
        
        Args:
            peer_port: Port for this peer to listen on
            tracker_host: Tracker host address
            tracker_port: Tracker port
        """
        self.peer_port = peer_port or config.get_peer_port()
        self.tracker_host = tracker_host or config.DEFAULT_TRACKER_HOST
        self.tracker_port = tracker_port or config.DEFAULT_TRACKER_PORT
        
        # Get local IP address
        self.peer_ip = self._get_local_ip()
        self.old_peer_ip = None  # Track IP changes
        
        # Services
        self.executor = CodeExecutor()
        self.memory_store = MemoryStore()
        self.file_storage = FileStorage()
        
        # Advanced features
        self.task_history = TaskHistory()
        self.result_cache = ResultCache()
        self.quota = ResourceQuota()
        self.distributed_memory = DistributedMemory(self.tracker_host, self.tracker_port)
        
        # OS Features
        self.process_manager = ProcessManager()
        self.deadlock_detector = DeadlockDetector()
        self.memory_manager = MemoryManager(total_memory=1024*1024*1024)  # 1GB
        self.ipc_manager = IPCManager()
        
        # Initialize deadlock detector with default resources
        self.deadlock_detector.register_resource("CPU", ResourceType.CPU, 4)
        self.deadlock_detector.register_resource("MEMORY", ResourceType.MEMORY, 1000)
        self.deadlock_detector.register_resource("DISK", ResourceType.DISK, 10)
        
        # Scheduler - can switch between algorithms
        self.use_advanced_scheduler = False
        self.scheduler = RoundRobinScheduler(self._execute_task)
        self.advanced_scheduler = AdvancedScheduler(
            algorithm=SchedulingAlgorithm.FCFS,
            executor_func=self._execute_task
        )
        self.scheduler.start()
        
        # Server socket
        self.server_socket: Optional[socket.socket] = None
        self.running = False
        
        # Tracker communication
        self.heartbeat_thread: Optional[threading.Thread] = None
        
        # Pending task results (task_id -> result)
        self.pending_results: Dict[str, Any] = {}
        self.result_lock = threading.Lock()
        self.task_process_map: Dict[str, str] = {}
        
        # Owned file tracking
        # Files owned by this peer: filename -> [storage_peer_addresses]
        self.owned_files: Dict[str, List[Tuple[str, int]]] = {}
        # Files stored for other peers: filename -> (owner_ip, owner_port)
        self.stored_for_others: Dict[str, Tuple[str, int]] = {}
        self.ownership_lock = threading.Lock()
    
    def _get_local_ip(self) -> str:
        """Get local IP address for external connections."""
        try:
            # Connect to tracker to determine local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect((self.tracker_host, self.tracker_port))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def start(self):
        """Start the peer server and register with tracker."""
        if self.running:
            return
        
        # Start server socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(("0.0.0.0", self.peer_port))
        self.server_socket.listen(10)
        self.server_socket.settimeout(1.0)
        
        self.running = True
        
        # Register with tracker
        self._register_with_tracker()
        self._register_existing_files()
        # Reconstruct owned file metadata from disk (in case peer restarted)
        self._reconstruct_owned_files_metadata()
        # Report owned files to tracker (helps rebuild registry after tracker restart)
        self._report_owned_files_to_tracker()
        
        # Start heartbeat thread
        self.heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self.heartbeat_thread.start()
        
        logger.info(f"Peer started on {self.peer_ip}:{self.peer_port}")
        
        # Main accept loop
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                client_socket.settimeout(config.SOCKET_TIMEOUT)
                
                # Handle client in separate thread
                thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, address),
                    daemon=True
                )
                thread.start()
                
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    logger.error(f"Error accepting connection: {e}", exc_info=True)
    
    def stop(self):
        """Stop the peer."""
        self.running = False
        
        # Unregister from tracker
        self._unregister_from_tracker()
        
        # Stop scheduler
        self.scheduler.stop()
        
        # Close server socket
        if self.server_socket:
            self.server_socket.close()
        
        logger.info("Peer stopped")
    
    def _register_with_tracker(self):
        """Register this peer with the tracker."""
        try:
            # Check if IP changed
            current_ip = self._get_local_ip()
            if self.old_peer_ip and current_ip != self.old_peer_ip:
                logger.info(f"IP changed: {self.old_peer_ip} -> {current_ip}")
            
            msg = messages.create_message(
                messages.MessageType.REGISTER,
                ip=current_ip,
                port=self.peer_port,
                cpu_load=self.scheduler.get_load(),
                old_ip=self.old_peer_ip if self.old_peer_ip else None
            )
            
            response = self._send_to_tracker(msg)
            if response and response.get("status") == "REGISTERED":
                logger.info(f"Registered with tracker at {self.tracker_host}:{self.tracker_port}")
                # Update IP tracking
                if current_ip != self.peer_ip:
                    self.old_peer_ip = self.peer_ip
                    self.peer_ip = current_ip
            else:
                logger.warning("Failed to register with tracker")
        except Exception as e:
            logger.error(f"Error registering with tracker: {e}")
    
    def _register_existing_files(self):
        """Register already stored files with the tracker."""
        try:
            files = self.file_storage.list_files()
            for filename in files:
                self._register_file_with_tracker(filename)
        except Exception as e:
            logger.debug(f"Error registering existing files: {e}")
    
    def _unregister_from_tracker(self):
        """Unregister this peer from the tracker."""
        try:
            msg = messages.create_message(
                messages.MessageType.UNREGISTER,
                ip=self.peer_ip,
                port=self.peer_port
            )
            self._send_to_tracker(msg)
        except Exception as e:
            logger.debug(f"Error unregistering from tracker: {e}")
    
    def _heartbeat_loop(self):
        """Periodically update tracker with current load."""
        while self.running:
            time.sleep(config.HEARTBEAT_INTERVAL)
            
            try:
                current_load = self.scheduler.get_load()
                msg = messages.create_message(
                    messages.MessageType.UPDATE_LOAD,
                    ip=self.peer_ip,
                    port=self.peer_port,
                    cpu_load=current_load
                )
                self._send_to_tracker(msg)
            except Exception as e:
                logger.debug(f"Error sending heartbeat: {e}")
    
    def _handle_client(self, client_socket: socket.socket, address: Tuple[str, int]):
        """Handle a client connection."""
        try:
            data = self._receive_message(client_socket)
            if not data:
                return
            
            msg = messages.deserialize_message(data)
            msg_type = msg.get("type")
            
            logger.debug(f"Received {msg_type} from {address}")
            
            response = self._process_message(msg)
            
            if response:
                self._send_message(client_socket, messages.serialize_message(response))
        
        except Exception as e:
            logger.error(f"Error handling client {address}: {e}", exc_info=True)
            try:
                error_msg = messages.create_error_message(str(e))
                self._send_message(client_socket, messages.serialize_message(error_msg))
            except:
                pass
        finally:
            client_socket.close()
    
    def _process_message(self, msg: Dict, address: Tuple[str, int] = None) -> Optional[Dict]:
        """Process a message and return response."""
        msg_type = msg.get("type")
        
        if msg_type == messages.MessageType.CPU_TASK:
            return self._handle_cpu_task(msg)
        elif msg_type == messages.MessageType.CANCEL_TASK:
            return self._handle_cancel_task(msg)
        elif msg_type == messages.MessageType.BATCH_TASK:
            return self._handle_batch_task(msg)
        elif msg_type == messages.MessageType.SET_MEM:
            return self._handle_set_mem(msg)
        elif msg_type == messages.MessageType.GET_MEM:
            return self._handle_get_mem(msg)
        elif msg_type == messages.MessageType.SET_MEM_REMOTE:
            return self._handle_set_mem(msg)  # Same handler
        elif msg_type == messages.MessageType.GET_MEM_REMOTE:
            return self._handle_get_mem(msg)  # Same handler
        elif msg_type == messages.MessageType.PUT_FILE:
            return self._handle_put_file(msg)
        elif msg_type == messages.MessageType.GET_FILE:
            return self._handle_get_file(msg)
        elif msg_type == messages.MessageType.UPLOAD_TO_PEER:
            return self._handle_upload_to_peer(msg, address or ("0.0.0.0", 0))
        elif msg_type == messages.MessageType.GET_OWNED_FILE:
            return self._handle_get_owned_file(msg, address or ("0.0.0.0", 0))
        elif msg_type == messages.MessageType.STATUS:
            return self._handle_status()
        elif msg_type == messages.MessageType.TASK_HISTORY:
            return self._handle_task_history(msg)
        else:
            return messages.create_error_message(f"Unknown message type: {msg_type}")
    
    def _handle_cpu_task(self, msg: Dict) -> Dict:
        """Handle incoming CPU task - add to scheduler queue."""
        task_id = msg.get("task_id", "unknown")
        program = msg.get("program", "")
        function = msg.get("function", "")
        args = msg.get("args", [])
        executed_by = f"{self.peer_ip}:{self.peer_port}"
        requested_by = msg.get("source_peer") or executed_by
        
        # Check cache first
        cached_result = self.result_cache.get(program, function, args)
        if cached_result is not None:
            logger.info(f"Cache hit for task {task_id}")
            self.task_history.record_task(
                task_id, "CPU_TASK", "SUCCESS", 
                cached_result, None, 0.0, executed_by,
                role="EXECUTOR",
                requested_by=requested_by
            )
            return messages.create_cpu_result(task_id, cached_result, None, executed_by=executed_by)
        
        # Check quota
        allowed, error = self.quota.check_cpu_quota()
        if not allowed:
            self.task_history.record_task(
                task_id, "CPU_TASK", "FAILED", 
                None, error, 0.0, executed_by,
                role="EXECUTOR",
                requested_by=requested_by
            )
            return messages.create_cpu_result(task_id, None, error, executed_by=executed_by)

        # Create OS process entry
        process_metadata = {
            "task_id": task_id,
            "function": function,
            "args": args,
            "priority": msg.get("priority", 0),
            "source_peer": requested_by,
            "confidential": msg.get("confidential", False)
        }
        pid = self.process_manager.create_process(process_metadata)
        self.process_manager.set_state(pid, ProcessState.READY)
        self.task_process_map[task_id] = pid
        
        # Store callback for result
        result_container = {"result": None, "ready": threading.Event()}
        start_time = time.time()
        
        def result_callback(result_msg: Dict):
            result_container["result"] = result_msg
            result_container["ready"].set()

            if "executed_by" not in result_msg or not result_msg.get("executed_by"):
                result_msg["executed_by"] = executed_by
            
            # Record in history
            execution_time = time.time() - start_time
            status = "SUCCESS" if not result_msg.get("error") else "FAILED"
            self.task_history.record_task(
                task_id, "CPU_TASK", status,
                result_msg.get("result"), result_msg.get("error"),
                execution_time, result_msg.get("executed_by", executed_by),
                role="EXECUTOR",
                requested_by=requested_by
            )

            # Update process state
            pid = self.task_process_map.pop(task_id, None)
            if pid:
                self.process_manager.set_state(pid, ProcessState.TERMINATED)
            
            # Cache successful results
            if status == "SUCCESS" and result_msg.get("result") is not None:
                self.result_cache.put(program, function, args, result_msg.get("result"))
        
        # Submit to scheduler
        self.scheduler.submit_task(msg, result_callback)
        
        # Wait for result (with timeout)
        timeout = msg.get("timeout", config.TASK_TIMEOUT)
        if result_container["ready"].wait(timeout=timeout):
            return result_container["result"]
        else:
            error_msg = "Task execution timeout"
            self.task_history.record_task(
                task_id, "CPU_TASK", "FAILED",
                None, error_msg, time.time() - start_time, executed_by,
                role="EXECUTOR",
                requested_by=requested_by
            )
            pid = self.task_process_map.pop(task_id, None)
            if pid:
                self.process_manager.set_state(pid, ProcessState.TERMINATED)
            return messages.create_cpu_result(task_id, None, error_msg, executed_by=executed_by)
    
    def _handle_cancel_task(self, msg: Dict) -> Dict:
        """Handle task cancellation request."""
        task_id = msg.get("task_id")
        if not task_id:
            return messages.create_error_message("task_id required")
        
        cancelled = self.scheduler.cancel_task(task_id)
        if cancelled:
            return messages.create_status_message("CANCELLED", {"task_id": task_id})
        else:
            return messages.create_error_message(f"Task {task_id} not found or already executing")
    
    def _handle_batch_task(self, msg: Dict) -> Dict:
        """Handle batch task execution."""
        tasks = msg.get("tasks", [])
        if not tasks:
            return messages.create_error_message("No tasks provided")
        
        results = []
        for task in tasks:
            result = self._handle_cpu_task(task)
            results.append(result)
        
        return messages.create_message(
            messages.MessageType.BATCH_RESULT,
            results=results
        )
    
    def _handle_task_history(self, msg: Dict) -> Dict:
        """Handle task history request."""
        limit = msg.get("limit", 100)
        task_type = msg.get("task_type")
        task_id = msg.get("task_id")
        
        if task_id:
            info = self.task_history.get_task_info(task_id)
            return messages.create_status_message("OK", {"task": info})
        else:
            history = self.task_history.get_history(limit, task_type)
            stats = self.task_history.get_statistics()
            return messages.create_status_message("OK", {
                "history": history,
                "statistics": stats
            })
    
    def _execute_task(self, task: Dict) -> Any:
        """Execute a task using the executor."""
        # Check for retry logic
        max_retries = task.get("max_retries", 0)
        retries = 0
        task_id = task.get("task_id")
        pid = self.task_process_map.get(task_id)
        
        while retries <= max_retries:
            try:
                if pid:
                    self.process_manager.set_state(pid, ProcessState.RUNNING)
                start_time = time.time()
                result = self.executor.execute(task)
                if pid:
                    self.process_manager.add_cpu_time(pid, time.time() - start_time)
                return result
            except Exception as e:
                if retries < max_retries:
                    retries += 1
                    logger.warning(f"Task {task.get('task_id')} failed, retrying ({retries}/{max_retries}): {e}")
                    time.sleep(0.5)  # Brief delay before retry
                else:
                    raise
    
    def _handle_set_mem(self, msg: Dict) -> Dict:
        """Handle memory set operation."""
        key = msg.get("key")
        value = msg.get("value")
        
        if key is None:
            return messages.create_error_message("Key required for SET_MEM")
        
        try:
            # Check quota
            current_keys = len(self.memory_store.list_keys())
            allowed, error = self.quota.check_memory_quota(current_keys + 1)
            if not allowed:
                return messages.create_error_message(error)
            
            self.memory_store.set(key, value)
            return messages.create_status_message("OK", {"operation": "SET_MEM", "key": key})
        except Exception as e:
            return messages.create_error_message(f"SET_MEM failed: {e}")
    
    def _handle_get_mem(self, msg: Dict) -> Dict:
        """Handle memory get operation."""
        key = msg.get("key")
        
        if key is None:
            return messages.create_error_message("Key required for GET_MEM")
        
        try:
            value = self.memory_store.get(key)
            return messages.create_message(
                messages.MessageType.MEM_RESPONSE,
                key=key,
                value=value,
                found=value is not None
            )
        except Exception as e:
            return messages.create_error_message(f"GET_MEM failed: {e}")
    
    def _handle_put_file(self, msg: Dict) -> Dict:
        """Handle file upload operation."""
        filename = msg.get("filename")
        data_b64 = msg.get("data")
        
        if not filename:
            return messages.create_error_message("Filename required for PUT_FILE")
        
        if not data_b64:
            return messages.create_error_message("Data required for PUT_FILE")
        
        try:
            # Decode base64 data
            data = base64.b64decode(data_b64)
            
            # Check file size
            if len(data) > config.MAX_FILE_SIZE:
                return messages.create_error_message(f"File too large (max {config.MAX_FILE_SIZE} bytes)")
            
            # Check quota
            allowed, error = self.quota.check_storage_quota(len(data))
            if not allowed:
                return messages.create_error_message(error)
            
            self.file_storage.put_file(filename, data)
            # Register file with tracker
            self._register_file_with_tracker(filename)
            return messages.create_status_message("OK", {
                "operation": "PUT_FILE",
                "filename": filename,
                "size": len(data)
            })
        except Exception as e:
            return messages.create_error_message(f"PUT_FILE failed: {e}")
    
    def _handle_get_file(self, msg: Dict) -> Dict:
        """Handle file download operation."""
        filename = msg.get("filename")
        
        if not filename:
            return messages.create_error_message("Filename required for GET_FILE")
        
        try:
            # Prevent access to owned files through regular GET_FILE
            # Owned files must be accessed via GET_OWNED_FILE
            with self.ownership_lock:
                if filename in self.stored_for_others:
                    return messages.create_error_message("This file is owned by another peer. Use GET_OWNED_FILE instead.")
            
            # Also check if file exists in owned_storage directory
            owned_storage_path = Path(config.OWNED_STORAGE_DIR)
            if owned_storage_path.exists():
                for owner_dir in owned_storage_path.iterdir():
                    if owner_dir.is_dir():
                        file_path = owner_dir / filename
                        if file_path.exists():
                            return messages.create_error_message("This file is owned by another peer. Use GET_OWNED_FILE instead.")
            
            data = self.file_storage.get_file(filename)
            
            if data is None:
                return messages.create_message(
                    messages.MessageType.FILE_RESPONSE,
                    filename=filename,
                    found=False
                )
            
            # Encode as base64
            data_b64 = base64.b64encode(data).decode('utf-8')
            
            return messages.create_message(
                messages.MessageType.FILE_RESPONSE,
                filename=filename,
                data=data_b64,
                found=True,
                size=len(data)
            )
        except Exception as e:
            return messages.create_error_message(f"GET_FILE failed: {e}")
    
    def _handle_status(self) -> Dict:
        """Handle status request."""
        scheduler_stats = self.scheduler.get_stats()
        memory_stats = self.memory_store.get_stats()
        storage_stats = self.file_storage.get_stats()
        executor_stats = self.executor.get_stats()
        history_stats = self.task_history.get_statistics()
        cache_stats = self.result_cache.get_stats()
        quota_usage = self.quota.get_usage()
        
        return messages.create_status_message("OK", {
            "peer_ip": self.peer_ip,
            "peer_port": self.peer_port,
            "scheduler": {
                "type": "advanced" if self.use_advanced_scheduler else "round_robin",
                "stats": self.advanced_scheduler.get_statistics() if self.use_advanced_scheduler else scheduler_stats
            },
            "memory": memory_stats,
            "storage": storage_stats,
            "executor": executor_stats,
            "task_history": history_stats,
            "cache": cache_stats,
            "quota": quota_usage,
            "process_manager": self.process_manager.get_statistics(),
            "deadlock_detector": self.deadlock_detector.get_resource_status(),
            "memory_manager": self.memory_manager.get_statistics(),
            "ipc": self.ipc_manager.get_statistics()
        })
    
    # Client-side methods for submitting tasks
    
    def submit_cpu_task(self, program: str, function: str, args: list, 
                       confidential: bool = False, task_id: str = None,
                       priority: int = 0, max_retries: int = 0, 
                       timeout: int = None) -> Dict:
        """
        Submit a CPU task for execution.
        
        Args:
            program: Python code string
            function: Function name to call
            args: Function arguments
            confidential: If True, execute locally only
            task_id: Optional task ID (auto-generated if not provided)
        
        Returns:
            Result dictionary with task_id, result, and error
        """
        if task_id is None:
            task_id = f"T{int(time.time() * 1000)}"
        
        task = messages.create_cpu_task(
            task_id, program, function, args, 
            confidential, priority, max_retries, timeout
        )
        task["source_peer"] = f"{self.peer_ip}:{self.peer_port}"
        
        if confidential:
            # Execute locally
            logger.info(f"Executing confidential task {task_id} locally")
            result_container = {"result": None, "ready": threading.Event()}
            
            def result_callback(result_msg: Dict):
                result_container["result"] = result_msg
                result_container["ready"].set()
            
            self.scheduler.submit_task(task, result_callback)
            
            # Wait for result
            if result_container["ready"].wait(timeout=config.TASK_TIMEOUT):
                return result_container["result"]
            else:
                return messages.create_cpu_result(task_id, None, "Task execution timeout")
        else:
            # Request best peer from tracker
            logger.info(f"Submitting non-confidential task {task_id} to remote peer")
            try:
                best_peer = self._request_best_peer()
                if not best_peer:
                    return messages.create_cpu_result(task_id, None, "No peers available")
                
                # Send task to remote peer
                result = self._send_task_to_peer(best_peer, task)
                status = "SUCCESS" if not result.get("error") else "FAILED"
                executed_by = result.get("executed_by") or f"{best_peer[0]}:{best_peer[1]}"
                self.task_history.record_task(
                    task_id,
                    "CPU_TASK",
                    status,
                    result.get("result"),
                    result.get("error"),
                    None,
                    executed_by,
                    role="CLIENT",
                    requested_by=f"{self.peer_ip}:{self.peer_port}"
                )
                return result
            except Exception as e:
                logger.error(f"Error submitting task to remote peer: {e}")
                return messages.create_cpu_result(task_id, None, f"Remote execution failed: {e}")
    
    def _request_best_peer(self) -> Optional[Tuple[str, int]]:
        """Request best peer from tracker."""
        msg = messages.create_message(messages.MessageType.REQUEST_CPU)
        response = self._send_to_tracker(msg)
        
        if response and response.get("type") == messages.MessageType.CPU_RESPONSE:
            ip = response.get("ip")
            port = response.get("port")
            return (ip, port)
        return None
    
    def _send_task_to_peer(self, peer_address: Tuple[str, int], task: Dict) -> Dict:
        """Send a task to a remote peer and wait for result."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(config.TASK_TIMEOUT)
        
        try:
            sock.connect(peer_address)
            self._send_message(sock, messages.serialize_message(task))
            
            # Receive result
            data = self._receive_message(sock)
            if data:
                result = messages.deserialize_message(data)
                if "executed_by" not in result or not result.get("executed_by"):
                    result["executed_by"] = f"{peer_address[0]}:{peer_address[1]}"
                return result
            else:
                task_id = task.get("task_id", "unknown")
                return messages.create_cpu_result(
                    task_id, None, "No response from peer",
                    executed_by=f"{peer_address[0]}:{peer_address[1]}"
                )
        finally:
            sock.close()
    
    def set_memory(self, key: str, value: Any) -> bool:
        """Set a value in local memory store."""
        return self.memory_store.set(key, value)
    
    def get_memory(self, key: str) -> Optional[Any]:
        """Get a value from local memory store."""
        return self.memory_store.get(key)
    
    def put_file(self, filename: str, data: bytes) -> bool:
        """Store a file locally."""
        return self.file_storage.put_file(filename, data)
    
    def get_file(self, filename: str) -> Optional[bytes]:
        """Retrieve a file locally."""
        return self.file_storage.get_file(filename)
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task by ID."""
        return self.scheduler.cancel_task(task_id)
    
    def submit_batch_tasks(self, tasks: list) -> list:
        """
        Submit multiple tasks for batch execution.
        
        Args:
            tasks: List of task dictionaries
        
        Returns:
            List of result dictionaries
        """
        results = []
        for task in tasks:
            result = self.submit_cpu_task(
                task.get("program"),
                task.get("function"),
                task.get("args", []),
                task.get("confidential", False),
                task.get("task_id"),
                task.get("priority", 0),
                task.get("max_retries", 0),
                task.get("timeout")
            )
            results.append(result)
        return results
    
    def get_task_history(self, limit: int = 100, task_type: str = None) -> Dict:
        """Get task execution history."""
        history = self.task_history.get_history(limit, task_type)
        stats = self.task_history.get_statistics()
        return {
            "history": history,
            "statistics": stats
        }
    
    def get_task_info(self, task_id: str) -> Optional[Dict]:
        """Get information about a specific task."""
        return self.task_history.get_task_info(task_id)
    
    def set_remote_memory(self, peer_address: Tuple[str, int], key: str, value: Any) -> bool:
        """Set a value in a remote peer's memory."""
        return self.distributed_memory.set_remote(peer_address, key, value)
    
    def get_remote_memory(self, peer_address: Tuple[str, int], key: str) -> Optional[Any]:
        """Get a value from a remote peer's memory."""
        return self.distributed_memory.get_remote(peer_address, key)
    
    # OS Feature Handlers
    
    def _handle_create_process(self, msg: Dict) -> Dict:
        """Handle process creation."""
        task_data = msg.get("task_data", {})
        parent_pid = msg.get("parent_pid")
        group_id = msg.get("group_id")
        
        pid = self.process_manager.create_process(task_data, parent_pid, group_id)
        return messages.create_status_message("OK", {"pid": pid})
    
    def _handle_terminate_process(self, msg: Dict) -> Dict:
        """Handle process termination."""
        pid = msg.get("pid")
        if not pid:
            return messages.create_error_message("pid required")
        
        success = self.process_manager.terminate_process(pid)
        if success:
            return messages.create_status_message("OK", {"pid": pid})
        else:
            return messages.create_error_message(f"Process {pid} not found")
    
    def _handle_process_tree(self, msg: Dict) -> Dict:
        """Handle process tree request."""
        root_pid = msg.get("root_pid")
        tree = self.process_manager.get_process_tree(root_pid)
        return messages.create_status_message("OK", {"tree": tree})
    
    def _handle_create_group(self, msg: Dict) -> Dict:
        """Handle process group creation."""
        group_id = msg.get("group_id")
        pids = msg.get("pids", [])
        
        if not group_id:
            return messages.create_error_message("group_id required")
        
        success = self.process_manager.create_process_group(group_id, pids)
        if success:
            return messages.create_status_message("OK", {"group_id": group_id})
        else:
            return messages.create_error_message("Failed to create group")
    
    def _handle_kill_group(self, msg: Dict) -> Dict:
        """Handle process group termination."""
        group_id = msg.get("group_id")
        if not group_id:
            return messages.create_error_message("group_id required")
        
        count = self.process_manager.kill_group(group_id)
        return messages.create_status_message("OK", {"group_id": group_id, "terminated": count})
    
    def _handle_request_resource(self, msg: Dict) -> Dict:
        """Handle resource request."""
        pid = msg.get("pid")
        resource_id = msg.get("resource_id")
        units = msg.get("units", 1)
        
        if not pid or not resource_id:
            return messages.create_error_message("pid and resource_id required")
        
        safe, error = self.deadlock_detector.request_resource(pid, resource_id, units)
        if safe:
            return messages.create_status_message("OK", {"pid": pid, "resource_id": resource_id, "units": units})
        else:
            return messages.create_error_message(error or "Resource request denied")
    
    def _handle_release_resource(self, msg: Dict) -> Dict:
        """Handle resource release."""
        pid = msg.get("pid")
        resource_id = msg.get("resource_id")
        units = msg.get("units", 1)
        
        if not pid or not resource_id:
            return messages.create_error_message("pid and resource_id required")
        
        success = self.deadlock_detector.release_resource(pid, resource_id, units)
        if success:
            return messages.create_status_message("OK", {"pid": pid, "resource_id": resource_id})
        else:
            return messages.create_error_message("Failed to release resource")
    
    def _handle_deadlock_check(self, msg: Dict) -> Dict:
        """Handle deadlock detection request."""
        deadlock, processes = self.deadlock_detector.detect_deadlock()
        return messages.create_status_message("OK", {
            "deadlock": deadlock,
            "deadlocked_processes": processes
        })
    
    def _handle_allocate_memory(self, msg: Dict) -> Dict:
        """Handle memory allocation."""
        pid = msg.get("pid")
        size = msg.get("size")
        
        if not pid or not size:
            return messages.create_error_message("pid and size required")
        
        success, address = self.memory_manager.allocate(pid, size)
        if success:
            return messages.create_status_message("OK", {"pid": pid, "address": address, "size": size})
        else:
            return messages.create_error_message("Memory allocation failed")
    
    def _handle_deallocate_memory(self, msg: Dict) -> Dict:
        """Handle memory deallocation."""
        pid = msg.get("pid")
        if not pid:
            return messages.create_error_message("pid required")
        
        success = self.memory_manager.deallocate(pid)
        if success:
            return messages.create_status_message("OK", {"pid": pid})
        else:
            return messages.create_error_message("Memory deallocation failed")
    
    def _handle_create_queue(self, msg: Dict) -> Dict:
        """Handle message queue creation."""
        queue_id = msg.get("queue_id")
        max_size = msg.get("max_size", 100)
        
        if not queue_id:
            return messages.create_error_message("queue_id required")
        
        success = self.ipc_manager.create_message_queue(queue_id, max_size)
        if success:
            return messages.create_status_message("OK", {"queue_id": queue_id})
        else:
            return messages.create_error_message("Queue already exists")
    
    def _handle_send_message(self, msg: Dict) -> Dict:
        """Handle message sending."""
        queue_id = msg.get("queue_id")
        sender = msg.get("sender")
        receiver = msg.get("receiver", "*")
        message_type = msg.get("message_type", "DATA")
        data = msg.get("data")
        
        if not queue_id or not sender:
            return messages.create_error_message("queue_id and sender required")
        
        queue = self.ipc_manager.get_message_queue(queue_id)
        if not queue:
            return messages.create_error_message(f"Queue {queue_id} not found")
        
        message = Message(sender=sender, receiver=receiver, message_type=message_type, data=data)
        success = queue.send(message)
        if success:
            return messages.create_status_message("OK", {"message_id": message.message_id})
        else:
            return messages.create_error_message("Failed to send message")
    
    def _handle_receive_message(self, msg: Dict) -> Dict:
        """Handle message receiving."""
        queue_id = msg.get("queue_id")
        receiver = msg.get("receiver")
        timeout = msg.get("timeout")
        
        if not queue_id or not receiver:
            return messages.create_error_message("queue_id and receiver required")
        
        queue = self.ipc_manager.get_message_queue(queue_id)
        if not queue:
            return messages.create_error_message(f"Queue {queue_id} not found")
        
        message = queue.receive(receiver, timeout)
        if message:
            return messages.create_status_message("OK", {
                "sender": message.sender,
                "message_type": message.message_type,
                "data": message.data,
                "message_id": message.message_id
            })
        else:
            return messages.create_error_message("No message received")
    
    def _handle_create_semaphore(self, msg: Dict) -> Dict:
        """Handle semaphore creation."""
        sem_id = msg.get("sem_id")
        initial_value = msg.get("initial_value", 1)
        
        if not sem_id:
            return messages.create_error_message("sem_id required")
        
        success = self.ipc_manager.create_semaphore(sem_id, initial_value)
        if success:
            return messages.create_status_message("OK", {"sem_id": sem_id})
        else:
            return messages.create_error_message("Semaphore already exists")
    
    def _handle_semaphore_wait(self, msg: Dict) -> Dict:
        """Handle semaphore wait operation."""
        sem_id = msg.get("sem_id")
        process_id = msg.get("process_id")
        
        if not sem_id or not process_id:
            return messages.create_error_message("sem_id and process_id required")
        
        sem = self.ipc_manager.get_semaphore(sem_id)
        if not sem:
            return messages.create_error_message(f"Semaphore {sem_id} not found")
        
        success = sem.wait(process_id)
        return messages.create_status_message("OK" if success else "BLOCKED", {
            "sem_id": sem_id,
            "value": sem.get_value()
        })
    
    def _handle_semaphore_signal(self, msg: Dict) -> Dict:
        """Handle semaphore signal operation."""
        sem_id = msg.get("sem_id")
        process_id = msg.get("process_id")
        
        if not sem_id or not process_id:
            return messages.create_error_message("sem_id and process_id required")
        
        sem = self.ipc_manager.get_semaphore(sem_id)
        if not sem:
            return messages.create_error_message(f"Semaphore {sem_id} not found")
        
        success = sem.signal(process_id)
        return messages.create_status_message("OK", {
            "sem_id": sem_id,
            "value": sem.get_value()
        })
    
    def _handle_set_scheduler(self, msg: Dict) -> Dict:
        """Handle scheduler algorithm change."""
        algorithm = msg.get("algorithm")
        
        if algorithm:
            try:
                algo = SchedulingAlgorithm[algorithm]
                if not self.use_advanced_scheduler:
                    self.scheduler.stop()
                    self.advanced_scheduler.set_algorithm(algo)
                    self.advanced_scheduler.start()
                    self.use_advanced_scheduler = True
                else:
                    self.advanced_scheduler.set_algorithm(algo)
                
                return messages.create_status_message("OK", {"algorithm": algorithm})
            except KeyError:
                return messages.create_error_message(f"Unknown algorithm: {algorithm}")
        else:
            return messages.create_error_message("algorithm required")
    
    # Network helper methods
    
    def _register_file_with_tracker(self, filename: str):
        """Register a file with the tracker."""
        try:
            msg = messages.create_message(
                messages.MessageType.REGISTER_FILE,
                filename=filename,
                ip=self.peer_ip,
                port=self.peer_port
            )
            self._send_to_tracker(msg)
        except Exception as e:
            logger.debug(f"Failed to register file with tracker: {e}")
    
    def find_file_on_network(self, filename: str) -> List[Tuple[str, int]]:
        """Find which peers have a file."""
        try:
            msg = messages.create_message(messages.MessageType.FIND_FILE, filename=filename)
            response = self._send_to_tracker(msg)
            
            if response and response.get("found"):
                peers = response.get("peers", [])
                return [(p["ip"], p["port"]) for p in peers]
            return []
        except Exception as e:
            logger.error(f"Error finding file on network: {e}")
            return []
    
    def download_file_from_network(self, filename: str, save_path: str = None, use_multipeer: bool = True) -> Optional[bytes]:
        """
        Download a file from the network, optionally using multiple peers.
        
        Args:
            filename: Name of file to download
            save_path: Optional path to save file
            use_multipeer: If True, download chunks from multiple peers
            
        Returns:
            File data as bytes, or None if failed
        """
        # Find peers with the file
        peers = self.find_file_on_network(filename)
        
        if not peers:
            logger.warning(f"File {filename} not found on any peer")
            return None
        
        if not use_multipeer or len(peers) == 1:
            # Single-peer download
            peer_ip, peer_port = peers[0]
            return self._download_from_peer(peer_ip, peer_port, filename, save_path)
        
        # Multi-peer download
        return self._download_multipeer(peers, filename, save_path)
    
    def _download_from_peer(self, peer_ip: str, peer_port: int, filename: str, save_path: str = None) -> Optional[bytes]:
        """Download file from a specific peer."""
        try:
            from client import P2PClient
            client = P2PClient(peer_ip, peer_port)
            response = client.get_file(filename, save_path)
            
            if response.get("found") and response.get("data"):
                data_b64 = response.get("data")
                data = base64.b64decode(data_b64)
                return data
            return None
        except Exception as e:
            logger.error(f"Error downloading from peer {peer_ip}:{peer_port}: {e}")
            return None
    
    def _download_multipeer(self, peers: List[Tuple[str, int]], filename: str, save_path: str = None) -> Optional[bytes]:
        """Download file chunks from multiple peers in parallel."""
        import threading
        
        # First, get file size from first peer
        first_peer_ip, first_peer_port = peers[0]
        try:
            from client import P2PClient
            client = P2PClient(first_peer_ip, first_peer_port)
            response = client.get_file(filename)
            if not response.get("found"):
                return None
            
            file_size = response.get("size", 0)
            if file_size == 0:
                # Fallback to single-peer download
                return self._download_from_peer(first_peer_ip, first_peer_port, filename, save_path)
        except:
            return self._download_from_peer(first_peer_ip, first_peer_port, filename, save_path)
        
        # Split into chunks (1MB each)
        chunk_size = 1024 * 1024
        num_chunks = (file_size + chunk_size - 1) // chunk_size
        
        chunks = [None] * num_chunks
        errors = []
        
        def download_chunk(chunk_idx: int, peer_idx: int):
            """Download a specific chunk from a peer."""
            peer_ip, peer_port = peers[peer_idx % len(peers)]
            try:
                # For now, download full file and extract chunk
                # In a real implementation, peers would support chunk requests
                data = self._download_from_peer(peer_ip, peer_port, filename)
                if data:
                    start = chunk_idx * chunk_size
                    end = min(start + chunk_size, len(data))
                    chunks[chunk_idx] = data[start:end]
            except Exception as e:
                errors.append(f"Chunk {chunk_idx} from {peer_ip}:{peer_port}: {e}")
        
        # Download chunks in parallel
        threads = []
        for i in range(num_chunks):
            thread = threading.Thread(target=download_chunk, args=(i, i % len(peers)), daemon=True)
            thread.start()
            threads.append(thread)
        
        # Wait for all threads
        for thread in threads:
            thread.join(timeout=30)
        
        # Check if all chunks downloaded
        if None in chunks:
            logger.warning("Some chunks failed to download, falling back to single-peer")
            return self._download_from_peer(peers[0][0], peers[0][1], filename, save_path)
        
        # Reassemble file
        file_data = b''.join(chunks)
        
        if save_path:
            with open(save_path, 'wb') as f:
                f.write(file_data)
            logger.info(f"File downloaded and saved to {save_path}")
        
        return file_data
    
    def _encrypt_file_data(self, data: bytes, owner_ip: str, owner_port: int) -> bytes:
        """
        Encrypt/obfuscate file data so storage peer cannot read it.
        Uses simple XOR encryption with a key derived from owner info.
        """
        import hashlib
        # Create a key from owner info
        key_str = f"{owner_ip}:{owner_port}:secret_salt"
        key = hashlib.sha256(key_str.encode()).digest()
        
        # XOR encrypt
        encrypted = bytearray(data)
        for i in range(len(encrypted)):
            encrypted[i] ^= key[i % len(key)]
        
        return bytes(encrypted)
    
    def _decrypt_file_data(self, encrypted_data: bytes, owner_ip: str, owner_port: int) -> bytes:
        """Decrypt file data (XOR is symmetric)."""
        return self._encrypt_file_data(encrypted_data, owner_ip, owner_port)
    
    def _handle_upload_to_peer(self, msg: Dict, address: Tuple[str, int]) -> Dict:
        """
        Handle file upload from another peer (store for them).
        Files are stored encrypted so this peer cannot read them.
        """
        filename = msg.get("filename")
        data_b64 = msg.get("data")
        owner_ip = msg.get("owner_ip")
        owner_port = msg.get("owner_port")
        
        if not filename or not data_b64 or not owner_ip or not owner_port:
            return messages.create_error_message("Missing required fields")
        
        try:
            # Decode and decrypt data
            encrypted_data = base64.b64decode(data_b64)
            # Note: We store encrypted, owner will decrypt when retrieving
            # But we need to decrypt to verify it's valid data
            # Actually, we'll store it encrypted and owner decrypts on retrieval
            
            # Check file size
            if len(encrypted_data) > config.MAX_FILE_SIZE:
                return messages.create_error_message(f"File too large (max {config.MAX_FILE_SIZE} bytes)")
            
            # Store in owned_storage directory with restricted permissions
            from pathlib import Path
            owned_storage_base = Path(config.OWNED_STORAGE_DIR)
            owned_storage_base.mkdir(exist_ok=True, mode=0o700)  # Only owner can access
            
            # Create directory for this owner: {owner_ip}_{owner_port}
            owner_dir = owned_storage_base / f"{owner_ip}_{owner_port}"
            owner_dir.mkdir(exist_ok=True, mode=0o700)
            
            # Store encrypted file
            file_path = owner_dir / filename
            with open(file_path, 'wb') as f:
                f.write(encrypted_data)
            
            # Set restrictive permissions (owner read/write only)
            os.chmod(file_path, 0o600)
            os.chmod(owner_dir, 0o700)
            
            # Track this file
            with self.ownership_lock:
                self.stored_for_others[filename] = (owner_ip, owner_port)
            
            # Register with tracker
            self._register_owned_file_with_tracker(filename, self.peer_ip, self.peer_port)
            
            logger.info(f"Stored owned file {filename} for {owner_ip}:{owner_port} (encrypted)")
            
            return messages.create_status_message("OK", {
                "filename": filename,
                "size": len(encrypted_data)
            })
        except Exception as e:
            logger.error(f"Failed to store owned file: {e}", exc_info=True)
            return messages.create_error_message(f"UPLOAD_TO_PEER failed: {e}")
    
    def _handle_get_owned_file(self, msg: Dict, address: Tuple[str, int]) -> Dict:
        """
        Handle request to retrieve an owned file.
        Only the owner can retrieve it.
        """
        filename = msg.get("filename")
        requester_ip = address[0]
        requester_port = msg.get("requester_port")
        
        if not filename or not requester_port:
            return messages.create_error_message("Missing required fields")
        
        try:
            # Check if we have this file stored
            with self.ownership_lock:
                if filename not in self.stored_for_others:
                    # Try to reconstruct from disk (in case peer restarted)
                    self._reconstruct_owned_files_metadata()
                    if filename not in self.stored_for_others:
                        return messages.create_error_message("File not found on this peer")
                
                owner_ip, owner_port = self.stored_for_others[filename]
            
            # Verify ownership - use port as primary identifier (handles IP changes)
            if owner_port != requester_port:
                return messages.create_error_message("Not authorized: You are not the owner of this file")
            
            # If IP changed but port matches, update the stored info
            if owner_ip != requester_ip:
                logger.info(f"IP changed for owner: {owner_ip} -> {requester_ip} (port {owner_port})")
                with self.ownership_lock:
                    self.stored_for_others[filename] = (requester_ip, owner_port)
                    # Rename directory if needed
                    from pathlib import Path
                    old_dir = Path(config.OWNED_STORAGE_DIR) / f"{owner_ip}_{owner_port}"
                    new_dir = Path(config.OWNED_STORAGE_DIR) / f"{requester_ip}_{owner_port}"
                    if old_dir.exists() and not new_dir.exists():
                        try:
                            old_dir.rename(new_dir)
                        except Exception as e:
                            logger.warning(f"Could not rename directory: {e}")
            
            # Read encrypted file
            from pathlib import Path
            owner_dir = Path(config.OWNED_STORAGE_DIR) / f"{requester_ip}_{requester_port}"
            file_path = owner_dir / filename
            
            if not file_path.exists():
                # Try old IP directory as fallback
                old_dir = Path(config.OWNED_STORAGE_DIR) / f"{owner_ip}_{owner_port}"
                old_file_path = old_dir / filename
                if old_file_path.exists():
                    file_path = old_file_path
                else:
                    return messages.create_error_message("File not found on disk")
            
            with open(file_path, 'rb') as f:
                encrypted_data = f.read()
            
            # Return encrypted data (owner will decrypt it)
            data_b64 = base64.b64encode(encrypted_data).decode('utf-8')
            
            return messages.create_message(
                messages.MessageType.OWNED_FILE_RESPONSE,
                filename=filename,
                found=True,
                data=data_b64,
                size=len(encrypted_data)
            )
        except Exception as e:
            logger.error(f"Failed to retrieve owned file: {e}", exc_info=True)
            return messages.create_error_message(f"GET_OWNED_FILE failed: {e}")
    
    def _reconstruct_owned_files_metadata(self):
        """Reconstruct owned files metadata from disk (after peer restart)."""
        try:
            from pathlib import Path
            owned_storage_base = Path(config.OWNED_STORAGE_DIR)
            if not owned_storage_base.exists():
                return
            
            for owner_dir in owned_storage_base.iterdir():
                if owner_dir.is_dir():
                    # Parse owner from directory name: {owner_ip}_{owner_port}
                    parts = owner_dir.name.split("_", 1)
                    if len(parts) == 2:
                        try:
                            owner_ip = parts[0]
                            owner_port = int(parts[1])
                            
                            # Scan files in this owner's directory
                            for file_path in owner_dir.iterdir():
                                if file_path.is_file():
                                    filename = file_path.name
                                    self.stored_for_others[filename] = (owner_ip, owner_port)
                                    logger.debug(f"Reconstructed: {filename} for {owner_ip}:{owner_port}")
                        except (ValueError, IndexError):
                            pass
        except Exception as e:
            logger.warning(f"Failed to reconstruct owned files metadata: {e}")
    
    def upload_file_to_peer(self, filename: str, file_data: bytes, target_peers: List[Tuple[str, int]], 
                           replication: int = 1) -> Dict:
        """
        Upload a file to remote peer(s) with ownership.
        
        Args:
            filename: Name of the file
            file_data: File contents as bytes
            target_peers: List of (ip, port) tuples to store the file
            replication: Number of replicas to create (default: 1)
        
        Returns:
            Dict with success status and storage locations
        """
        if not file_data:
            return {"success": False, "error": "No file data provided"}
        
        if len(file_data) > config.MAX_FILE_SIZE:
            return {"success": False, "error": f"File too large (max {config.MAX_FILE_SIZE} bytes)"}
        
        # Encrypt file data
        encrypted_data = self._encrypt_file_data(file_data, self.peer_ip, self.peer_port)
        data_b64 = base64.b64encode(encrypted_data).decode('utf-8')
        
        successful_peers = []
        errors = []
        
        # Upload to target peers (up to replication count)
        for target_ip, target_port in target_peers[:replication]:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(config.SOCKET_TIMEOUT)
                
                sock.connect((target_ip, target_port))
                
                msg = messages.create_message(
                    messages.MessageType.UPLOAD_TO_PEER,
                    filename=filename,
                    data=data_b64,
                    owner_ip=self.peer_ip,
                    owner_port=self.peer_port
                )
                
                self._send_message(sock, messages.serialize_message(msg))
                
                response_data = self._receive_message(sock)
                if response_data:
                    response = messages.deserialize_message(response_data)
                    if response.get("status") == "OK":
                        successful_peers.append((target_ip, target_port))
                        # Register with tracker
                        self._register_owned_file_with_tracker(filename, target_ip, target_port)
                    else:
                        errors.append(f"{target_ip}:{target_port}: {response.get('error', 'Unknown error')}")
                else:
                    errors.append(f"{target_ip}:{target_port}: No response")
                
                sock.close()
            except Exception as e:
                errors.append(f"{target_ip}:{target_port}: {str(e)}")
                logger.error(f"Failed to upload to {target_ip}:{target_port}: {e}")
        
        if successful_peers:
            # Track owned files
            with self.ownership_lock:
                self.owned_files[filename] = successful_peers
            
            return {
                "success": True,
                "filename": filename,
                "storage_peers": successful_peers,
                "errors": errors if errors else None
            }
        else:
            return {
                "success": False,
                "error": f"Failed to upload to any peer. Errors: {', '.join(errors)}"
            }
    
    def download_owned_file(self, filename: str) -> Optional[bytes]:
        """
        Download an owned file from storage peer(s).
        Handles offline peers and IP changes.
        
        Returns:
            File data as bytes, or None if not found
        """
        # First, query tracker to find storage locations
        msg = messages.create_message(
            messages.MessageType.FIND_OWNED_FILE,
            filename=filename,
            requester_ip=self.peer_ip,
            requester_port=self.peer_port
        )
        
        response = self._send_to_tracker(msg)
        if not response or response.get("type") != messages.MessageType.OWNED_FILE_RESPONSE:
            logger.error("Failed to query tracker for owned file")
            return None
        
        if not response.get("found"):
            logger.warning(f"File {filename} not found in tracker registry")
            return None
        
        storage_peers = response.get("storage_peers", [])
        if not storage_peers:
            logger.warning(f"No storage peers found for {filename}")
            return None
        
        # Try each storage peer
        for peer_info in storage_peers:
            storage_ip = peer_info.get("ip")
            storage_port = peer_info.get("port")
            
            if not storage_ip or not storage_port:
                continue
            
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(config.SOCKET_TIMEOUT)
                
                sock.connect((storage_ip, storage_port))
                
                msg = messages.create_message(
                    messages.MessageType.GET_OWNED_FILE,
                    filename=filename,
                    requester_ip=self.peer_ip,
                    requester_port=self.peer_port
                )
                
                self._send_message(sock, messages.serialize_message(msg))
                
                response_data = self._receive_message(sock)
                if response_data:
                    response = messages.deserialize_message(response_data)
                    if response.get("found"):
                        encrypted_data_b64 = response.get("data")
                        if encrypted_data_b64:
                            encrypted_data = base64.b64decode(encrypted_data_b64)
                            # Decrypt
                            file_data = self._decrypt_file_data(encrypted_data, self.peer_ip, self.peer_port)
                            sock.close()
                            logger.info(f"Downloaded owned file {filename} from {storage_ip}:{storage_port}")
                            return file_data
                
                sock.close()
            except Exception as e:
                logger.debug(f"Failed to download from {storage_ip}:{storage_port}: {e}")
                continue
        
        logger.error(f"Failed to download {filename} from any storage peer")
        return None
    
    def list_owned_files(self) -> List[str]:
        """List all files owned by this peer."""
        with self.ownership_lock:
            return list(self.owned_files.keys())
    
    def _register_owned_file_with_tracker(self, filename: str, storage_ip: str, storage_port: int):
        """Register an owned file with the tracker."""
        try:
            msg = messages.create_message(
                messages.MessageType.REGISTER_OWNED_FILE,
                filename=filename,
                owner_ip=self.peer_ip,
                owner_port=self.peer_port,
                storage_ip=storage_ip,
                storage_port=storage_port
            )
            self._send_to_tracker(msg)
        except Exception as e:
            logger.debug(f"Failed to register owned file with tracker: {e}")
    
    def _send_to_tracker(self, msg: Dict) -> Optional[Dict]:
        """Send a message to the tracker and return response."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(config.SOCKET_TIMEOUT)
        
        try:
            sock.connect((self.tracker_host, self.tracker_port))
            self._send_message(sock, messages.serialize_message(msg))
            
            data = self._receive_message(sock)
            if data:
                return messages.deserialize_message(data)
        except Exception as e:
            logger.error(f"Error communicating with tracker: {e}")
            return None
        finally:
            sock.close()
    
    def _receive_message(self, sock: socket.socket) -> Optional[bytes]:
        """Receive a complete message from socket."""
        try:
            length_data = sock.recv(4)
            if len(length_data) < 4:
                return None
            
            message_length = int.from_bytes(length_data, 'big')
            
            data = b''
            while len(data) < message_length:
                chunk = sock.recv(min(message_length - len(data), config.BUFFER_SIZE))
                if not chunk:
                    return None
                data += chunk
            
            return data
        except Exception as e:
            logger.debug(f"Error receiving message: {e}")
            return None
    
    def _send_message(self, sock: socket.socket, data: bytes):
        """Send a message with length prefix."""
        try:
            length = len(data).to_bytes(4, 'big')
            sock.sendall(length + data)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise


def main():
    """Main entry point for peer."""
    import argparse
    
    parser = argparse.ArgumentParser(description="P2P Resource Sharing Peer")
    parser.add_argument("--port", type=int, default=None, help="Peer port (default: auto)")
    parser.add_argument("--tracker-host", type=str, default=None, help="Tracker host")
    parser.add_argument("--tracker-port", type=int, default=None, help="Tracker port")
    parser.add_argument("--web-ui", action="store_true", help="Enable web UI")
    parser.add_argument("--web-port", type=int, default=5000, help="Web UI port (default: 5000)")
    parser.add_argument("--web-host", type=str, default="127.0.0.1", help="Web UI host (default: 127.0.0.1)")
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format=config.LOG_FORMAT
    )
    
    peer = Peer(
        peer_port=args.port,
        tracker_host=args.tracker_host,
        tracker_port=args.tracker_port
    )
    
    try:
        print(f"Starting peer on port {peer.peer_port}")
        print(f"Connecting to tracker at {peer.tracker_host}:{peer.tracker_port}")
        
        if args.web_ui:
            print(f"Starting web UI on http://{args.web_host}:{args.web_port}")
            from web_ui import run_web_ui
            import threading
            # Start peer in background thread
            peer_thread = threading.Thread(target=peer.start, daemon=True)
            peer_thread.start()
            time.sleep(2)  # Wait for peer to start
            # Start web UI (blocks)
            run_web_ui(peer, host=args.web_host, port=args.web_port)
        else:
            print("Press Ctrl+C to stop")
            print("Tip: Use --web-ui flag to enable web interface")
            peer.start()
    except KeyboardInterrupt:
        print("\nShutting down peer...")
        peer.stop()


if __name__ == "__main__":
    main()

