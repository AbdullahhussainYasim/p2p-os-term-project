"""
Example usage scripts for the P2P resource sharing system.
These can be used as reference or imported for testing.
"""

import time
import json
from peer import Peer


def example_cpu_task():
    """Example: Execute a simple CPU task."""
    peer = Peer(peer_port=9000)
    
    # Start peer in background thread
    import threading
    thread = threading.Thread(target=peer.start, daemon=True)
    thread.start()
    time.sleep(2)  # Wait for peer to start
    
    # Submit a non-confidential task (will be routed to best peer)
    program = """
def main(n):
    if n <= 1:
        return 1
    return n * main(n - 1)
"""
    
    result = peer.submit_cpu_task(
        program=program,
        function="main",
        args=[5],
        confidential=False
    )
    
    print(f"Task result: {result}")
    peer.stop()


def example_confidential_task():
    """Example: Execute a confidential task (local only)."""
    peer = Peer(peer_port=9000)
    
    import threading
    thread = threading.Thread(target=peer.start, daemon=True)
    thread.start()
    time.sleep(2)
    
    # Submit confidential task (executes locally)
    program = """
def main(secret):
    # Sensitive computation - must stay local
    return hash(secret) % 1000
"""
    
    result = peer.submit_cpu_task(
        program=program,
        function="main",
        args=["my_secret_data"],
        confidential=True
    )
    
    print(f"Confidential task result: {result}")
    peer.stop()


def example_memory_operations():
    """Example: Memory storage operations."""
    peer = Peer(peer_port=9000)
    
    import threading
    thread = threading.Thread(target=peer.start, daemon=True)
    thread.start()
    time.sleep(2)
    
    # Store values
    peer.set_memory("user_id", 12345)
    peer.set_memory("username", "alice")
    peer.set_memory("data", {"key": "value"})
    
    # Retrieve values
    user_id = peer.get_memory("user_id")
    username = peer.get_memory("username")
    data = peer.get_memory("data")
    
    print(f"User ID: {user_id}")
    print(f"Username: {username}")
    print(f"Data: {data}")
    
    peer.stop()


def example_file_operations():
    """Example: File storage operations."""
    peer = Peer(peer_port=9000)
    
    import threading
    thread = threading.Thread(target=peer.start, daemon=True)
    thread.start()
    time.sleep(2)
    
    # Store a file
    test_data = b"Hello, P2P File Storage!"
    peer.put_file("test.txt", test_data)
    
    # Retrieve the file
    retrieved_data = peer.get_file("test.txt")
    
    print(f"Original: {test_data}")
    print(f"Retrieved: {retrieved_data}")
    print(f"Match: {test_data == retrieved_data}")
    
    peer.stop()


def example_complex_computation():
    """Example: More complex computation task."""
    peer = Peer(peer_port=9000)
    
    import threading
    thread = threading.Thread(target=peer.start, daemon=True)
    thread.start()
    time.sleep(2)
    
    # Compute sum of squares
    program = """
def main(n):
    return sum(i * i for i in range(1, n + 1))
"""
    
    result = peer.submit_cpu_task(
        program=program,
        function="main",
        args=[100],
        confidential=False
    )
    
    print(f"Sum of squares 1..100: {result.get('result')}")
    peer.stop()


if __name__ == "__main__":
    print("P2P Resource Sharing Examples")
    print("=" * 40)
    
    print("\n1. CPU Task Example:")
    example_cpu_task()
    
    print("\n2. Confidential Task Example:")
    example_confidential_task()
    
    print("\n3. Memory Operations Example:")
    example_memory_operations()
    
    print("\n4. File Operations Example:")
    example_file_operations()
    
    print("\n5. Complex Computation Example:")
    example_complex_computation()






