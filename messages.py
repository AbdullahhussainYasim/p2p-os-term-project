"""
Message protocol definitions for P2P resource sharing system.
All messages are JSON-encoded and sent over TCP sockets.
"""

import json
from typing import Any, Dict, Optional


class MessageType:
    """Message type constants."""
    # Tracker messages
    REGISTER = "REGISTER"
    UNREGISTER = "UNREGISTER"
    UPDATE_LOAD = "UPDATE_LOAD"
    REQUEST_CPU = "REQUEST_CPU"
    CPU_RESPONSE = "CPU_RESPONSE"
    
    # CPU execution messages
    CPU_TASK = "CPU_TASK"
    CPU_RESULT = "CPU_RESULT"
    
    # Memory messages
    SET_MEM = "SET_MEM"
    GET_MEM = "GET_MEM"
    MEM_RESPONSE = "MEM_RESPONSE"
    
    # File messages
    PUT_FILE = "PUT_FILE"
    GET_FILE = "GET_FILE"
    FILE_RESPONSE = "FILE_RESPONSE"
    FIND_FILE = "FIND_FILE"
    FILE_PEERS = "FILE_PEERS"
    REGISTER_FILE = "REGISTER_FILE"
    GET_FILE_CHUNK = "GET_FILE_CHUNK"
    
    # Owned file messages (for remote storage with ownership)
    UPLOAD_TO_PEER = "UPLOAD_TO_PEER"
    GET_OWNED_FILE = "GET_OWNED_FILE"
    REGISTER_OWNED_FILE = "REGISTER_OWNED_FILE"
    FIND_OWNED_FILE = "FIND_OWNED_FILE"
    OWNED_FILE_RESPONSE = "OWNED_FILE_RESPONSE"
    DELETE_OWNED_FILE = "DELETE_OWNED_FILE"
    
    # Status messages
    STATUS = "STATUS"
    ERROR = "ERROR"
    PING = "PING"
    PONG = "PONG"
    
    # Advanced features
    CANCEL_TASK = "CANCEL_TASK"
    BATCH_TASK = "BATCH_TASK"
    BATCH_RESULT = "BATCH_RESULT"
    TASK_HISTORY = "TASK_HISTORY"
    SET_MEM_REMOTE = "SET_MEM_REMOTE"
    GET_MEM_REMOTE = "GET_MEM_REMOTE"
    RETRY_TASK = "RETRY_TASK"
    PEER_GROUP = "PEER_GROUP"
    QUOTA_CHECK = "QUOTA_CHECK"
    
    # OS Features
    CREATE_PROCESS = "CREATE_PROCESS"
    TERMINATE_PROCESS = "TERMINATE_PROCESS"
    PROCESS_TREE = "PROCESS_TREE"
    CREATE_GROUP = "CREATE_GROUP"
    KILL_GROUP = "KILL_GROUP"
    REQUEST_RESOURCE = "REQUEST_RESOURCE"
    RELEASE_RESOURCE = "RELEASE_RESOURCE"
    DEADLOCK_CHECK = "DEADLOCK_CHECK"
    ALLOCATE_MEMORY = "ALLOCATE_MEMORY"
    DEALLOCATE_MEMORY = "DEALLOCATE_MEMORY"
    CREATE_QUEUE = "CREATE_QUEUE"
    SEND_MESSAGE = "SEND_MESSAGE"
    RECEIVE_MESSAGE = "RECEIVE_MESSAGE"
    CREATE_SEMAPHORE = "CREATE_SEMAPHORE"
    SEMAPHORE_WAIT = "SEMAPHORE_WAIT"
    SEMAPHORE_SIGNAL = "SEMAPHORE_SIGNAL"
    SET_SCHEDULER = "SET_SCHEDULER"


def create_message(msg_type: str, **kwargs) -> Dict[str, Any]:
    """Create a message dictionary."""
    message = {"type": msg_type}
    message.update(kwargs)
    return message


def serialize_message(message: Dict[str, Any]) -> bytes:
    """Serialize a message to JSON bytes."""
    return json.dumps(message).encode('utf-8')


def deserialize_message(data: bytes) -> Dict[str, Any]:
    """Deserialize JSON bytes to a message dictionary."""
    try:
        return json.loads(data.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise ValueError(f"Invalid message format: {e}")


def create_cpu_task(task_id: str, program: str, function: str, args: list, 
                    confidential: bool = False, priority: int = 0,
                    max_retries: int = 0, timeout: int = None) -> Dict[str, Any]:
    """
    Create a CPU task message.
    
    Args:
        task_id: Unique task identifier
        program: Python code string
        function: Function name to call
        args: Function arguments
        confidential: If True, execute locally only
        priority: Task priority (higher = more important, default: 0)
        max_retries: Maximum retry attempts on failure (default: 0)
        timeout: Task timeout in seconds (None = use default)
    """
    msg = create_message(
        MessageType.CPU_TASK,
        task_id=task_id,
        program=program,
        function=function,
        args=args,
        confidential=confidential,
        priority=priority,
        max_retries=max_retries
    )
    if timeout is not None:
        msg["timeout"] = timeout
    return msg


def create_cpu_result(task_id: str, result: Any = None, error: Optional[str] = None,
                      executed_by: Optional[str] = None) -> Dict[str, Any]:
    """Create a CPU result message."""
    msg = create_message(
        MessageType.CPU_RESULT,
        task_id=task_id,
        result=result,
        error=error
    )
    if executed_by:
        msg["executed_by"] = executed_by
    return msg


def create_error_message(error_msg: str) -> Dict[str, Any]:
    """Create an error message."""
    return create_message(MessageType.ERROR, error=error_msg)


def create_status_message(status: str, data: Optional[Dict] = None) -> Dict[str, Any]:
    """Create a status message."""
    msg = create_message(MessageType.STATUS, status=status)
    if data:
        msg.update(data)
    return msg

