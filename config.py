"""
Configuration settings for the P2P system.
"""

import os
from typing import Tuple

# Default network settings
DEFAULT_TRACKER_HOST = "0.0.0.0"  # Listen on all interfaces
DEFAULT_TRACKER_PORT = 8888
DEFAULT_PEER_PORT_START = 9000

# Timeout settings (in seconds)
SOCKET_TIMEOUT = 30
TASK_TIMEOUT = 60
HEARTBEAT_INTERVAL = 10  # How often peers update their load
PEER_TIMEOUT = 30  # Consider peer dead if no update for this long

# Storage settings
STORAGE_DIR = "peer_storage"
OWNED_STORAGE_DIR = "owned_storage"  # Separate directory for owned files
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB max file size

# Scheduler settings
ROUND_ROBIN_QUANTUM = 1  # Not used for preemption, but for logging

# Network buffer size
BUFFER_SIZE = 1024 * 1024  # 1 MB buffer

# Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

def get_tracker_address() -> Tuple[str, int]:
    """Get tracker address from environment or use defaults."""
    host = os.getenv("TRACKER_HOST", DEFAULT_TRACKER_HOST)
    port = int(os.getenv("TRACKER_PORT", DEFAULT_TRACKER_PORT))
    return (host, port)

def get_peer_port() -> int:
    """Get peer port from environment or use default start."""
    return int(os.getenv("PEER_PORT", DEFAULT_PEER_PORT_START))






