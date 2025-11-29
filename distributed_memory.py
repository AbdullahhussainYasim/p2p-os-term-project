"""
Distributed memory sharing across peers.
"""

import socket
import logging
from typing import Any, Optional, Tuple, Dict
import messages
import config

logger = logging.getLogger(__name__)


class DistributedMemory:
    """
    Provides distributed memory operations across peers.
    """
    
    def __init__(self, tracker_host: str, tracker_port: int):
        """
        Initialize distributed memory.
        
        Args:
            tracker_host: Tracker host address
            tracker_port: Tracker port
        """
        self.tracker_host = tracker_host
        self.tracker_port = tracker_port
    
    def set_remote(self, peer_address: Tuple[str, int], key: str, value: Any) -> bool:
        """
        Set a value in a remote peer's memory.
        
        Args:
            peer_address: (ip, port) of target peer
            key: Memory key
            value: Value to store
        
        Returns:
            True if successful
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(config.SOCKET_TIMEOUT)
        
        try:
            sock.connect(peer_address)
            msg = messages.create_message(
                messages.MessageType.SET_MEM_REMOTE,
                key=key,
                value=value
            )
            self._send_message(sock, messages.serialize_message(msg))
            
            response_data = self._receive_message(sock)
            if response_data:
                response = messages.deserialize_message(response_data)
                return response.get("status") == "OK"
            return False
        except Exception as e:
            logger.error(f"Error setting remote memory: {e}")
            return False
        finally:
            sock.close()
    
    def get_remote(self, peer_address: Tuple[str, int], key: str) -> Optional[Any]:
        """
        Get a value from a remote peer's memory.
        
        Args:
            peer_address: (ip, port) of target peer
            key: Memory key
        
        Returns:
            Value if found, None otherwise
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(config.SOCKET_TIMEOUT)
        
        try:
            sock.connect(peer_address)
            msg = messages.create_message(
                messages.MessageType.GET_MEM_REMOTE,
                key=key
            )
            self._send_message(sock, messages.serialize_message(msg))
            
            response_data = self._receive_message(sock)
            if response_data:
                response = messages.deserialize_message(response_data)
                if response.get("found"):
                    return response.get("value")
            return None
        except Exception as e:
            logger.error(f"Error getting remote memory: {e}")
            return None
        finally:
            sock.close()
    
    def _receive_message(self, sock: socket.socket) -> bytes:
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






