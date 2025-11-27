"""
CLI client for testing the P2P resource sharing system.
"""

import argparse
import socket
import sys
import time
import base64
import json
from typing import Any, Dict

import messages
import config


class P2PClient:
    """Simple client for interacting with peers."""
    
    def __init__(self, peer_host: str, peer_port: int):
        """
        Initialize client.
        
        Args:
            peer_host: Peer host address
            peer_port: Peer port
        """
        self.peer_host = peer_host
        self.peer_port = peer_port
    
    def _send_request(self, msg: Dict) -> Dict:
        """Send a request to peer and return response."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(config.SOCKET_TIMEOUT)
        
        try:
            sock.connect((self.peer_host, self.peer_port))
            self._send_message(sock, messages.serialize_message(msg))
            
            data = self._receive_message(sock)
            if data:
                return messages.deserialize_message(data)
            else:
                return messages.create_error_message("No response from peer")
        finally:
            sock.close()
    
    def _receive_message(self, sock: socket.socket) -> bytes:
        """Receive a complete message from socket."""
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
    
    def _send_message(self, sock: socket.socket, data: bytes):
        """Send a message with length prefix."""
        length = len(data).to_bytes(4, 'big')
        sock.sendall(length + data)
    
    def execute_cpu_task(self, program: str, function: str, args: list, 
                        confidential: bool = False, priority: int = 0,
                        max_retries: int = 0, timeout: int = None) -> Dict:
        """Execute a CPU task."""
        task_id = f"CLIENT_{int(time.time() * 1000)}"
        task = messages.create_cpu_task(
            task_id, program, function, args, 
            confidential, priority, max_retries, timeout
        )
        return self._send_request(task)
    
    def cancel_task(self, task_id: str) -> Dict:
        """Cancel a task."""
        msg = messages.create_message(messages.MessageType.CANCEL_TASK, task_id=task_id)
        return self._send_request(msg)
    
    def get_task_history(self, limit: int = 100, task_type: str = None) -> Dict:
        """Get task history."""
        msg = messages.create_message(
            messages.MessageType.TASK_HISTORY,
            limit=limit,
            task_type=task_type
        )
        return self._send_request(msg)
    
    def batch_execute(self, tasks: list) -> Dict:
        """Execute multiple tasks in batch."""
        msg = messages.create_message(
            messages.MessageType.BATCH_TASK,
            tasks=tasks
        )
        return self._send_request(msg)
    
    def set_memory(self, key: str, value: Any) -> Dict:
        """Set memory value."""
        msg = messages.create_message(messages.MessageType.SET_MEM, key=key, value=value)
        return self._send_request(msg)
    
    def get_memory(self, key: str) -> Dict:
        """Get memory value."""
        msg = messages.create_message(messages.MessageType.GET_MEM, key=key)
        return self._send_request(msg)
    
    def put_file(self, filename: str, filepath: str) -> Dict:
        """Upload a file."""
        try:
            with open(filepath, 'rb') as f:
                data = f.read()
            
            data_b64 = base64.b64encode(data).decode('utf-8')
            msg = messages.create_message(
                messages.MessageType.PUT_FILE,
                filename=filename,
                data=data_b64
            )
            return self._send_request(msg)
        except Exception as e:
            return messages.create_error_message(f"Failed to read file: {e}")
    
    def get_file(self, filename: str, save_path: str = None) -> Dict:
        """Download a file."""
        msg = messages.create_message(messages.MessageType.GET_FILE, filename=filename)
        response = self._send_request(msg)
        
        if response.get("found") and save_path:
            try:
                data_b64 = response.get("data")
                if data_b64:
                    data = base64.b64decode(data_b64)
                    with open(save_path, 'wb') as f:
                        f.write(data)
                    print(f"File saved to {save_path}")
            except Exception as e:
                return messages.create_error_message(f"Failed to save file: {e}")
        
        return response
    
    def get_status(self) -> Dict:
        """Get peer status."""
        msg = messages.create_message(messages.MessageType.STATUS)
        return self._send_request(msg)


def main():
    """CLI interface."""
    parser = argparse.ArgumentParser(description="P2P Resource Sharing Client")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Peer host")
    parser.add_argument("--port", type=int, default=9000, help="Peer port")
    
    subparsers = parser.add_subparsers(dest="command", help="Command")
    
    # CPU task command
    cpu_parser = subparsers.add_parser("cpu", help="Execute CPU task")
    cpu_parser.add_argument("--program", type=str, required=True, help="Python program code")
    cpu_parser.add_argument("--function", type=str, default="main", help="Function name")
    cpu_parser.add_argument("--args", type=str, default="[]", help="Arguments as JSON list")
    cpu_parser.add_argument("--confidential", action="store_true", help="Execute locally only")
    cpu_parser.add_argument("--priority", type=int, default=0, help="Task priority (higher = more important)")
    cpu_parser.add_argument("--retries", type=int, default=0, help="Max retry attempts on failure")
    cpu_parser.add_argument("--timeout", type=int, default=None, help="Task timeout in seconds")
    
    # Cancel task command
    cancel_parser = subparsers.add_parser("cancel", help="Cancel a task")
    cancel_parser.add_argument("--task-id", type=str, required=True, help="Task ID to cancel")
    
    # Task history command
    history_parser = subparsers.add_parser("history", help="Get task history")
    history_parser.add_argument("--limit", type=int, default=100, help="Number of records to return")
    history_parser.add_argument("--type", type=str, default=None, help="Filter by task type")
    
    # Memory commands
    mem_set_parser = subparsers.add_parser("set-mem", help="Set memory value")
    mem_set_parser.add_argument("--key", type=str, required=True)
    mem_set_parser.add_argument("--value", type=str, required=True)
    
    mem_get_parser = subparsers.add_parser("get-mem", help="Get memory value")
    mem_get_parser.add_argument("--key", type=str, required=True)
    
    # File commands
    file_put_parser = subparsers.add_parser("put-file", help="Upload file")
    file_put_parser.add_argument("--filename", type=str, required=True)
    file_put_parser.add_argument("--filepath", type=str, required=True)
    
    file_get_parser = subparsers.add_parser("get-file", help="Download file")
    file_get_parser.add_argument("--filename", type=str, required=True)
    file_get_parser.add_argument("--save", type=str, help="Save path")
    
    # Status command
    subparsers.add_parser("status", help="Get peer status")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    client = P2PClient(args.host, args.port)
    
    try:
        if args.command == "cpu":
            try:
                task_args = json.loads(args.args)
            except:
                task_args = [args.args]
            
            result = client.execute_cpu_task(
                args.program,
                args.function,
                task_args,
                args.confidential,
                args.priority,
                args.retries,
                args.timeout
            )
            
            if result.get("error"):
                print(f"Error: {result['error']}")
            else:
                print(f"Result: {result.get('result')}")
        
        elif args.command == "set-mem":
            result = client.set_memory(args.key, args.value)
            if result.get("error"):
                print(f"Error: {result['error']}")
            else:
                print(f"Memory set: {args.key} = {args.value}")
        
        elif args.command == "get-mem":
            result = client.get_memory(args.key)
            if result.get("error"):
                print(f"Error: {result['error']}")
            elif result.get("found"):
                print(f"Memory value: {result['value']}")
            else:
                print(f"Key '{args.key}' not found")
        
        elif args.command == "put-file":
            result = client.put_file(args.filename, args.filepath)
            if result.get("error"):
                print(f"Error: {result['error']}")
            else:
                print(f"File uploaded: {args.filename}")
        
        elif args.command == "get-file":
            result = client.get_file(args.filename, args.save)
            if result.get("error"):
                print(f"Error: {result['error']}")
            elif result.get("found"):
                if not args.save:
                    print(f"File retrieved: {args.filename} ({result.get('size', 0)} bytes)")
            else:
                print(f"File '{args.filename}' not found")
        
        elif args.command == "cancel":
            result = client.cancel_task(args.task_id)
            if result.get("error"):
                print(f"Error: {result['error']}")
            else:
                print(f"Task {args.task_id} cancelled successfully")
        
        elif args.command == "history":
            result = client.get_task_history(args.limit, args.type)
            if result.get("error"):
                print(f"Error: {result['error']}")
            else:
                # Handle both response formats
                if "data" in result:
                    data = result.get("data", {})
                else:
                    data = result
                
                history = data.get("history", [])
                stats = data.get("statistics", {})
                
                print("Task History Statistics:")
                print(json.dumps(stats, indent=2))
                print(f"\nRecent Tasks ({len(history)}):")
                for task in history[-10:]:  # Show last 10
                    print(f"  {task.get('task_id')}: {task.get('status')} - {task.get('task_type')}")
        
        elif args.command == "status":
            result = client.get_status()
            if result.get("error"):
                print(f"Error: {result['error']}")
            else:
                print(json.dumps(result, indent=2))
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

