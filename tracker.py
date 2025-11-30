#!/usr/bin/env python3
"""
Central tracker node for peer discovery and load balancing.
"""

import socket
import threading
import logging
import time
import json
from pathlib import Path
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
        
        # Owned file tracking: filename -> (owner_peer, [(storage_peer_ip, storage_peer_port), ...])
        # owner_peer is (ip, port) tuple
        # storage_peers is list of (ip, port) tuples where file is stored
        self.owned_file_registry: Dict[str, Tuple[Tuple[str, int], List[Tuple[str, int]]]] = {}
        
        # Persistence
        self.state_dir = Path("tracker_state")
        self.state_dir.mkdir(exist_ok=True)
        self.ownership_state_file = self.state_dir / "owned_files.json"
        
        # Load persisted ownership records
        self._load_ownership_state()
        
        self.lock = threading.RLock()  # Use reentrant lock to allow nested locking
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
            # Set socket timeout
            client_socket.settimeout(config.SOCKET_TIMEOUT)
            
            data = self._receive_message(client_socket)
            if not data:
                logger.debug(f"No data received from {address}")
                return
            
            msg = messages.deserialize_message(data)
            msg_type = msg.get("type")
            
            logger.info(f"Received {msg_type} from {address}")
            
            # Process message and get response
            logger.debug(f"Processing {msg_type} from {address}...")
            response = self._process_message(msg, address)
            logger.debug(f"Processed {msg_type} from {address}, response type: {response.get('type') if response else None}")
            
            if response:
                logger.info(f"Sending response for {msg_type} to {address}, response type: {response.get('type')}")
                try:
                    serialized = messages.serialize_message(response)
                    logger.debug(f"Serialized response size: {len(serialized)} bytes")
                    self._send_message(client_socket, serialized)
                    logger.info(f"Response sent successfully for {msg_type} to {address}")
                except socket.error as e:
                    logger.error(f"Socket error sending response for {msg_type} to {address}: {e}")
                except Exception as e:
                    logger.error(f"Error sending response for {msg_type} to {address}: {e}", exc_info=True)
            else:
                logger.warning(f"No response generated for {msg_type} from {address}")
                # Send error response if no response was generated
                try:
                    error_response = messages.create_error_message(f"No response generated for {msg_type}")
                    serialized = messages.serialize_message(error_response)
                    self._send_message(client_socket, serialized)
                    logger.info(f"Sent error response to {address}")
                except Exception as e:
                    logger.error(f"Failed to send error response: {e}")
        
        except Exception as e:
            logger.error(f"Error handling client {address}: {e}", exc_info=True)
            try:
                error_msg = messages.create_error_message(str(e))
                self._send_message(client_socket, messages.serialize_message(error_msg))
                logger.info(f"Sent error response to {address}")
            except Exception as send_err:
                logger.error(f"Failed to send error response to {address}: {send_err}")
        finally:
            try:
                client_socket.close()
            except:
                pass
    
    def _process_message(self, msg: Dict, address: Tuple[str, int]) -> Optional[Dict]:
        """Process a message and return response."""
        msg_type = msg.get("type")
        
        try:
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
            elif msg_type == messages.MessageType.REGISTER_OWNED_FILE:
                return self._handle_register_owned_file(msg, address)
            elif msg_type == messages.MessageType.FIND_OWNED_FILE:
                logger.info(f"Processing FIND_OWNED_FILE for {msg.get('filename')}")
                try:
                    response = self._handle_find_owned_file(msg, address)
                    if response:
                        logger.info(f"_handle_find_owned_file returned response: type={response.get('type')}, found={response.get('found')}")
                    else:
                        logger.error("_handle_find_owned_file returned None!")
                    return response
                except Exception as e:
                    logger.error(f"Exception in FIND_OWNED_FILE handler: {e}", exc_info=True)
                    return messages.create_error_message(f"Error processing FIND_OWNED_FILE: {e}")
            elif msg_type == messages.MessageType.REPORT_OWNED_FILES:
                return self._handle_report_owned_files(msg, address)
            elif msg_type == messages.MessageType.STATUS:
                return self._handle_status()
            else:
                return messages.create_error_message(f"Unknown message type: {msg_type}")
        except Exception as e:
            logger.error(f"Exception in _process_message for {msg_type}: {e}", exc_info=True)
            return messages.create_error_message(f"Error processing {msg_type}: {e}")
    
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
    
    def _handle_register_owned_file(self, msg: Dict, address: Tuple[str, int]) -> Dict:
        """Handle owned file registration."""
        filename = msg.get("filename")
        owner_ip = msg.get("owner_ip")
        owner_port = msg.get("owner_port")
        storage_ip = msg.get("storage_ip", address[0])
        storage_port = msg.get("storage_port")
        
        if not filename or not owner_ip or not owner_port or not storage_port:
            return messages.create_error_message("Missing required fields")
        
        owner_key = (owner_ip, owner_port)
        storage_key = (storage_ip, storage_port)
        
        with self.lock:
            if filename in self.owned_file_registry:
                # Add storage peer to existing entry
                existing_owner, existing_storage = self.owned_file_registry[filename]
                if existing_owner == owner_key and storage_key not in existing_storage:
                    existing_storage.append(storage_key)
            else:
                # New owned file
                self.owned_file_registry[filename] = (owner_key, [storage_key])
            
            logger.info(f"Owned file registered: {filename} owned by {owner_ip}:{owner_port}, stored on {storage_ip}:{storage_port}")
            
            # Persist to disk
            self._save_ownership_state()
        
        return messages.create_status_message("OK", {"filename": filename})
    
    def _handle_find_owned_file(self, msg: Dict, address: Tuple[str, int]) -> Dict:
        """Handle request to find storage locations for an owned file."""
        filename = msg.get("filename")
        requester_ip = msg.get("requester_ip", address[0])
        requester_port = msg.get("requester_port")
        
        logger.info(f"FIND_OWNED_FILE request for {filename} from {requester_ip}:{requester_port}")
        
        if not filename:
            logger.warning("FIND_OWNED_FILE: filename missing")
            return messages.create_error_message("Filename required")
        if not requester_port:
            logger.warning("FIND_OWNED_FILE: requester_port missing")
            return messages.create_error_message("Requester port required")
        
        try:
            alive_storage_peers = []
            owner_key = None
            
            logger.info(f"Acquiring lock for FIND_OWNED_FILE: {filename}")
            with self.lock:
                logger.info(f"Lock acquired for FIND_OWNED_FILE: {filename}")
                logger.debug(f"Checking registry for {filename}. Total files in registry: {len(self.owned_file_registry)}")
                logger.debug(f"Files in registry: {list(self.owned_file_registry.keys())}")
                
                if filename not in self.owned_file_registry:
                    logger.warning(f"FIND_OWNED_FILE: File {filename} not found in registry (total files: {len(self.owned_file_registry)})")
                    response = messages.create_message(
                        messages.MessageType.OWNED_FILE_RESPONSE,
                        filename=filename,
                        found=False,
                        error="File not found"
                    )
                    logger.info(f"Returning response: file not found")
                    return response
                
                logger.info(f"File {filename} found in registry, extracting owner and storage peers...")
                owner_key, storage_peers = self.owned_file_registry[filename]
                logger.info(f"Found file {filename}: owner={owner_key}, storage_peers={storage_peers}")
                
                # Verify ownership - use port as primary identifier (handles IP changes)
                logger.info(f"Verifying ownership: owner port {owner_key[1]} vs requester port {requester_port}")
                if owner_key[1] != requester_port:
                    logger.warning(f"Ownership mismatch: owner port {owner_key[1]} != requester port {requester_port}")
                    response = messages.create_message(
                        messages.MessageType.OWNED_FILE_RESPONSE,
                        filename=filename,
                        found=False,
                        error="Not authorized: You are not the owner of this file"
                    )
                    logger.info(f"Returning response: not authorized")
                    return response
                
                # If IP changed but port matches, update the ownership record
                if owner_key[0] != requester_ip:
                    logger.info(f"IP changed for owner: {owner_key[0]}:{owner_key[1]} -> {requester_ip}:{requester_port}")
                    new_owner_key = (requester_ip, requester_port)
                    self.owned_file_registry[filename] = (new_owner_key, storage_peers)
                    owner_key = new_owner_key
                    # Don't save state here - do it after response is sent to avoid blocking
                
                # Filter to only alive storage peers
                logger.info(f"Filtering {len(storage_peers)} storage peers for {filename}...")
                for storage_key in storage_peers:
                    logger.debug(f"Checking storage peer {storage_key}...")
                    if storage_key in self.peers:
                        is_alive = self.peers[storage_key].is_alive(config.PEER_TIMEOUT)
                        logger.debug(f"Storage peer {storage_key} is_alive={is_alive}")
                        if is_alive:
                            alive_storage_peers.append({"ip": storage_key[0], "port": storage_key[1]})
                    else:
                        logger.debug(f"Storage peer {storage_key} not in self.peers")
                
                logger.info(f"Found {len(alive_storage_peers)} alive storage peers for {filename}")
                
                # Update registry if some peers are dead
                if len(alive_storage_peers) < len(storage_peers):
                    logger.info(f"Updating registry: removing dead peers for {filename}")
                    self.owned_file_registry[filename] = (owner_key, [(p["ip"], p["port"]) for p in alive_storage_peers])
                    # Don't save state here - do it after response is sent to avoid blocking
                
                logger.info(f"Releasing lock for FIND_OWNED_FILE: {filename}")
            
            # Create response outside the lock (to avoid holding lock while creating response)
            if owner_key is None:
                logger.error("owner_key is None after processing!")
                return messages.create_error_message("Internal error: owner_key is None")
            
            response = messages.create_message(
                messages.MessageType.OWNED_FILE_RESPONSE,
                filename=filename,
                found=len(alive_storage_peers) > 0,
                owner_ip=owner_key[0],
                owner_port=owner_key[1],
                storage_peers=alive_storage_peers
            )
            logger.info(f"Created OWNED_FILE_RESPONSE for {filename}: found={len(alive_storage_peers) > 0}, peers={len(alive_storage_peers)}, owner={owner_key}")
            return response
        except Exception as e:
            logger.error(f"Error in _handle_find_owned_file: {e}", exc_info=True)
            return messages.create_error_message(f"Error finding owned file: {e}")
    
    def _handle_report_owned_files(self, msg: Dict, address: Tuple[str, int]) -> Dict:
        """Handle storage peer reporting what owned files it has."""
        storage_ip = msg.get("storage_ip", address[0])
        storage_port = msg.get("storage_port")
        owned_files = msg.get("owned_files", [])
        
        if not storage_port:
            return messages.create_error_message("Storage port required")
        
        storage_key = (storage_ip, storage_port)
        
        with self.lock:
            updated_count = 0
            for file_info in owned_files:
                filename = file_info.get("filename")
                owner_ip = file_info.get("owner_ip")
                owner_port = file_info.get("owner_port")
                
                if not filename or not owner_ip or not owner_port:
                    continue
                
                owner_key = (owner_ip, owner_port)
                
                if filename in self.owned_file_registry:
                    existing_owner, existing_storage = self.owned_file_registry[filename]
                    if existing_owner[1] == owner_port and storage_key not in existing_storage:
                        if existing_owner[0] != owner_ip:
                            existing_owner = (owner_ip, owner_port)
                        existing_storage.append(storage_key)
                        self.owned_file_registry[filename] = (existing_owner, existing_storage)
                        updated_count += 1
                else:
                    self.owned_file_registry[filename] = (owner_key, [storage_key])
                    updated_count += 1
                    logger.info(f"Rebuilt ownership: {filename} owned by {owner_ip}:{owner_port}, stored on {storage_ip}:{storage_port}")
            
            if updated_count > 0:
                self._save_ownership_state()
                logger.info(f"Updated {updated_count} owned file records from storage peer {storage_ip}:{storage_port}")
        
        return messages.create_status_message("OK", {"updated_count": updated_count})
    
    def _load_ownership_state(self):
        """Load persisted ownership records from disk."""
        try:
            if self.ownership_state_file.exists():
                with open(self.ownership_state_file, 'r') as f:
                    data = json.load(f)
                    for filename, entry in data.items():
                        owner_data = entry["owner"]
                        storage_data = entry["storage"]
                        owner_key = (owner_data["ip"], owner_data["port"])
                        storage_keys = [(s["ip"], s["port"]) for s in storage_data]
                        self.owned_file_registry[filename] = (owner_key, storage_keys)
                    logger.info(f"Loaded {len(self.owned_file_registry)} owned file records from disk")
        except Exception as e:
            logger.warning(f"Failed to load ownership state: {e}")
    
    def _save_ownership_state(self):
        """Save ownership records to disk.
        
        Note: This method assumes the lock is already held by the caller.
        It uses the lock to safely read the registry, then releases it before
        writing to disk to avoid blocking other operations.
        """
        try:
            # Read data while holding lock (assumed to be held by caller)
            data = {}
            for filename, (owner_key, storage_keys) in self.owned_file_registry.items():
                data[filename] = {
                    "owner": {"ip": owner_key[0], "port": owner_key[1]},
                    "storage": [{"ip": ip, "port": port} for ip, port in storage_keys]
                }
            
            # Write to disk outside the lock to avoid blocking
            temp_file = self.ownership_state_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)
            temp_file.replace(self.ownership_state_file)
            logger.debug(f"Saved {len(data)} owned file records to disk")
        except Exception as e:
            logger.error(f"Failed to save ownership state: {e}")
    
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
            logger.debug(f"Sending message: length={len(data)} bytes, total={len(length) + len(data)} bytes")
            # Use sendall to ensure all data is sent
            sock.sendall(length + data)
            logger.debug(f"Message sent successfully")
        except socket.error as e:
            logger.error(f"Socket error sending message: {e}")
            raise
        except Exception as e:
            logger.error(f"Error sending message: {e}", exc_info=True)
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




