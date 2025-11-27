"""
Central tracker node for peer discovery and load balancing.
"""

import socket
import threading
import logging
import time
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta

import messages
import config

logger = logging.getLogger(__name__)


class PeerInfo:
    """Information about a registered peer."""
    
    def __init__(self, ip: str, port: int, initial_load: float = 0.0):
        self.ip = ip
        self.port = port
        self.cpu_load = initial_load
        self.last_update = datetime.now()
        self.registered_at = datetime.now()
    
    def update_load(self, load: float):
        """Update peer's CPU load and timestamp."""
        self.cpu_load = load
        self.last_update = datetime.now()
    
    def is_alive(self, timeout_seconds: float) -> bool:
        """Check if peer is still alive based on last update."""
        return (datetime.now() - self.last_update).total_seconds() < timeout_seconds
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "ip": self.ip,
            "port": self.port,
            "cpu_load": self.cpu_load,
            "last_update": self.last_update.isoformat(),
            "registered_at": self.registered_at.isoformat()
        }


class Tracker:
    """
    Central tracker that maintains peer registry and performs load balancing.
    """
    
    def __init__(self, host: str = None, port: int = None):
        """
        Initialize the tracker.
        
        Args:
            host: Host to bind to (default from config)
            port: Port to bind to (default from config)
        """
        self.host = host or config.DEFAULT_TRACKER_HOST
        self.port = port or config.DEFAULT_TRACKER_PORT
        self.peers: Dict[Tuple[str, int], PeerInfo] = {}  # (ip, port) -> PeerInfo
        self.file_registry: Dict[str, List[Tuple[str, int]]] = {}  # filename -> [(ip, port), ...]
        self.lock = threading.Lock()
        self.running = False
        self.server_socket: Optional[socket.socket] = None
        self.cleanup_thread: Optional[threading.Thread] = None
    
    def start(self):
        """Start the tracker server."""
        if self.running:
            return
        
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(10)
        self.server_socket.settimeout(1.0)  # Allow checking self.running
        
        self.running = True
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_dead_peers, daemon=True)
        self.cleanup_thread.start()
        
        logger.info(f"Tracker started on {self.host}:{self.port}")
        
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
        """Stop the tracker."""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        logger.info("Tracker stopped")
    
    def _cleanup_dead_peers(self):
        """Periodically remove peers that haven't updated in a while."""
        while self.running:
            time.sleep(config.HEARTBEAT_INTERVAL)
            
            with self.lock:
                dead_peers = []
                for peer_key, peer_info in self.peers.items():
                    if not peer_info.is_alive(config.PEER_TIMEOUT):
                        dead_peers.append(peer_key)
                
                for peer_key in dead_peers:
                    peer_info = self.peers.pop(peer_key)
                    logger.info(f"Removed dead peer: {peer_info.ip}:{peer_info.port}")
                    # Remove peer from file registry
                    for filename in list(self.file_registry.keys()):
                        if peer_key in self.file_registry[filename]:
                            self.file_registry[filename].remove(peer_key)
                        if not self.file_registry[filename]:
                            del self.file_registry[filename]
                    # Remove peer from file registry
                    for filename in list(self.file_registry.keys()):
                        if peer_key in self.file_registry[filename]:
                            self.file_registry[filename].remove(peer_key)
                        if not self.file_registry[filename]:
                            del self.file_registry[filename]
    
    def _handle_client(self, client_socket: socket.socket, address: Tuple[str, int]):
        """Handle a client connection."""
        try:
            data = self._receive_message(client_socket)
            if not data:
                return
            
            msg = messages.deserialize_message(data)
            msg_type = msg.get("type")
            
            logger.debug(f"Received {msg_type} from {address}")
            
            response = self._process_message(msg, address)
            
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
    
    def _process_message(self, msg: Dict, address: Tuple[str, int]) -> Optional[Dict]:
        """Process a message and return response."""
        msg_type = msg.get("type")
        
        if msg_type == messages.MessageType.REGISTER:
            return self._handle_register(msg, address)
        elif msg_type == messages.MessageType.UNREGISTER:
            return self._handle_unregister(msg, address)
        elif msg_type == messages.MessageType.UPDATE_LOAD:
            return self._handle_update_load(msg, address)
        elif msg_type == messages.MessageType.REQUEST_CPU:
            return self._handle_request_cpu(msg)
        elif msg_type == messages.MessageType.REGISTER_FILE:
            return self._handle_register_file(msg, address)
        elif msg_type == messages.MessageType.FIND_FILE:
            return self._handle_find_file(msg)
        elif msg_type == messages.MessageType.STATUS:
            return self._handle_status()
        else:
            return messages.create_error_message(f"Unknown message type: {msg_type}")
    
    def _handle_register(self, msg: Dict, address: Tuple[str, int]) -> Dict:
        """Handle peer registration."""
        ip = msg.get("ip", address[0])
        port = msg.get("port")
        cpu_load = msg.get("cpu_load", 0.0)
        
        if not port:
            return messages.create_error_message("Port required for registration")
        
        peer_key = (ip, port)
        
        with self.lock:
            if peer_key in self.peers:
                # Update existing peer
                self.peers[peer_key].update_load(cpu_load)
                logger.info(f"Updated peer registration: {ip}:{port} (load: {cpu_load})")
            else:
                # New peer
                self.peers[peer_key] = PeerInfo(ip, port, cpu_load)
                logger.info(f"New peer registered: {ip}:{port} (load: {cpu_load})")
        
        return messages.create_status_message("REGISTERED", {"peer_count": len(self.peers)})
    
    def _handle_unregister(self, msg: Dict, address: Tuple[str, int]) -> Dict:
        """Handle peer unregistration."""
        ip = msg.get("ip", address[0])
        port = msg.get("port")
        
        if not port:
            return messages.create_error_message("Port required for unregistration")
        
        peer_key = (ip, port)
        
        with self.lock:
            if peer_key in self.peers:
                del self.peers[peer_key]
                logger.info(f"Peer unregistered: {ip}:{port}")
                return messages.create_status_message("UNREGISTERED")
            else:
                return messages.create_error_message("Peer not found")
    
    def _handle_update_load(self, msg: Dict, address: Tuple[str, int]) -> Dict:
        """Handle peer load update."""
        ip = msg.get("ip", address[0])
        port = msg.get("port")
        cpu_load = msg.get("cpu_load", 0.0)
        
        if not port:
            return messages.create_error_message("Port required for load update")
        
        peer_key = (ip, port)
        
        with self.lock:
            if peer_key in self.peers:
                self.peers[peer_key].update_load(cpu_load)
                return messages.create_status_message("LOAD_UPDATED")
            else:
                # Auto-register if not found
                self.peers[peer_key] = PeerInfo(ip, port, cpu_load)
                logger.info(f"Auto-registered peer from load update: {ip}:{port}")
                return messages.create_status_message("LOAD_UPDATED")
    
    def _handle_request_cpu(self, msg: Dict) -> Dict:
        """Handle CPU resource request - returns least-loaded peer."""
        with self.lock:
            if not self.peers:
                return messages.create_error_message("No peers available")
            
            # Find peer with minimum CPU load
            best_peer = min(self.peers.values(), key=lambda p: p.cpu_load)
            
            logger.info(f"CPU request: selected {best_peer.ip}:{best_peer.port} (load: {best_peer.cpu_load})")
            
            return messages.create_message(
                messages.MessageType.CPU_RESPONSE,
                ip=best_peer.ip,
                port=best_peer.port,
                cpu_load=best_peer.cpu_load
            )
    
    def _handle_status(self) -> Dict:
        """Handle status request."""
        with self.lock:
            peer_list = [peer.to_dict() for peer in self.peers.values()]
            return messages.create_status_message("OK", {
                "peer_count": len(self.peers),
                "peers": peer_list
            })
    
    def _handle_register_file(self, msg: Dict, address: Tuple[str, int]) -> Dict:
        """Handle file registration (peer announces it has a file)."""
        filename = msg.get("filename")
        ip = msg.get("ip", address[0])
        port = msg.get("port")
        
        if not filename:
            return messages.create_error_message("Filename required")
        if not port:
            return messages.create_error_message("Port required")
        
        peer_key = (ip, port)
        
        with self.lock:
            if peer_key not in self.peers:
                return messages.create_error_message("Peer not registered")
            
            if filename not in self.file_registry:
                self.file_registry[filename] = []
            
            if peer_key not in self.file_registry[filename]:
                self.file_registry[filename].append(peer_key)
                logger.info(f"File registered: {filename} on {ip}:{port}")
        
        return messages.create_status_message("OK", {"filename": filename})
    
    def _handle_find_file(self, msg: Dict) -> Dict:
        """Handle file discovery request (find which peers have a file)."""
        filename = msg.get("filename")
        
        if not filename:
            return messages.create_error_message("Filename required")
        
        with self.lock:
            peers_with_file = self.file_registry.get(filename, [])
            # Filter to only alive peers
            alive_peers = []
            for peer_key in peers_with_file:
                if peer_key in self.peers and self.peers[peer_key].is_alive(config.PEER_TIMEOUT):
                    alive_peers.append({"ip": peer_key[0], "port": peer_key[1]})
        
        return messages.create_message(
            messages.MessageType.FILE_PEERS,
            filename=filename,
            peers=alive_peers,
            found=len(alive_peers) > 0
        )
    
    def _receive_message(self, sock: socket.socket) -> Optional[bytes]:
        """Receive a complete message from socket."""
        try:
            # First, receive message length (4 bytes)
            length_data = sock.recv(4)
            if len(length_data) < 4:
                return None
            
            message_length = int.from_bytes(length_data, 'big')
            
            # Receive the actual message
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
            # Send length first (4 bytes)
            length = len(data).to_bytes(4, 'big')
            sock.sendall(length + data)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise


def main():
    """Main entry point for tracker."""
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format=config.LOG_FORMAT
    )
    
    tracker = Tracker()
    
    try:
        print(f"Starting tracker on {tracker.host}:{tracker.port}")
        print("Press Ctrl+C to stop")
        tracker.start()
    except KeyboardInterrupt:
        print("\nShutting down tracker...")
        tracker.stop()


if __name__ == "__main__":
    main()




