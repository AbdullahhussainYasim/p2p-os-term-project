#!/usr/bin/env python3
"""
Simple script to create a deadlock in a running peer.
Run this script while your peer is running, then check for deadlocks in Web UI.
"""

import socket
import json
import sys
import messages
import config

def send_message_to_peer(peer_host, peer_port, msg):
    """Send a message to the peer and get response."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(10)
    
    try:
        sock.connect((peer_host, peer_port))
        
        # Send message
        data = messages.serialize_message(msg)
        length = len(data).to_bytes(4, 'big')
        sock.send(length + data)
        
        # Receive response
        length_data = sock.recv(4)
        if len(length_data) != 4:
            return None
        length = int.from_bytes(length_data, 'big')
        response_data = sock.recv(length)
        
        if response_data:
            return messages.deserialize_message(response_data)
        return None
    except Exception as e:
        print(f"Error communicating with peer: {e}")
        return None
    finally:
        sock.close()


def create_deadlock_scenario(peer_host="127.0.0.1", peer_port=9001):
    """Create a deadlock scenario in the running peer."""
    print("=" * 60)
    print("Creating Deadlock Scenario in Running Peer")
    print("=" * 60)
    print(f"Connecting to peer at {peer_host}:{peer_port}...")
    
    # Step 1: Register processes (we'll use the existing deadlock detector)
    # Since we can't directly access the peer's deadlock detector, we need to
    # use a different approach - we'll access it via the peer's internal state
    # by using a special message or by directly manipulating if we can access it
    
    # Actually, the best way is to create a script that can be imported
    # and run in the same process, or we need to add a way to access the peer instance
    
    # For now, let's create a script that the user can run that will
    # access the peer instance if it's in the same Python environment
    
    print("\n⚠️  Note: This script needs to access the peer's deadlock detector.")
    print("   If your peer is running in a separate process, you'll need to")
    print("   run this script in a way that can access the peer instance.")
    print("\n   Alternative: Use the create_deadlock.py script which creates")
    print("   a deadlock in a standalone detector, then manually transfer")
    print("   the state to your peer.")
    
    # Try to access peer instance if available
    try:
        # Try importing web_ui to get peer_instance
        import web_ui
        if hasattr(web_ui, 'peer_instance') and web_ui.peer_instance:
            peer = web_ui.peer_instance
            detector = peer.deadlock_detector
            
            print("\n✓ Found peer instance! Creating deadlock...")
            
            from deadlock_detector import ResourceType
            
            # Register resources if not already registered
            if "R1" not in detector.resources:
                detector.register_resource("R1", ResourceType.CPU, 2)
                print("  ✓ Registered resource R1 (2 units)")
            if "R2" not in detector.resources:
                detector.register_resource("R2", ResourceType.MEMORY, 2)
                print("  ✓ Registered resource R2 (2 units)")
            
            # Register processes if not already registered
            if "P1" not in detector.processes:
                detector.register_process("P1", {"R1": 2, "R2": 1})
                print("  ✓ Registered process P1: needs {R1: 2, R2: 1}")
            if "P2" not in detector.processes:
                detector.register_process("P2", {"R1": 1, "R2": 2})
                print("  ✓ Registered process P2: needs {R1: 1, R2: 2}")
            
            # Manually create deadlock
            with detector.lock:
                # P1 gets all of R1
                detector.resources["R1"].available_units = 0
                detector.resources["R1"].allocated["P1"] = 2
                detector.processes["P1"]["allocation"]["R1"] = 2
                detector.processes["P1"]["need"]["R1"] = 0
                print("  ✓ P1 allocated R1 (2 units)")
                
                # P2 gets all of R2
                detector.resources["R2"].available_units = 0
                detector.resources["R2"].allocated["P2"] = 2
                detector.processes["P2"]["allocation"]["R2"] = 2
                detector.processes["P2"]["need"]["R2"] = 0
                print("  ✓ P2 allocated R2 (2 units)")
            
            # Check if deadlock was created
            deadlock, processes = detector.detect_deadlock()
            
            if deadlock:
                print("\n✅ DEADLOCK CREATED SUCCESSFULLY!")
                print(f"   Deadlocked processes: {sorted(set(processes))}")
                print("\n💡 Now go to Web UI and click 'Check for Deadlocks'")
                print("   You should see: ⚠️ DEADLOCK DETECTED!")
            else:
                print("\n❌ Deadlock not created. Check the scenario.")
            
            print("\n" + "=" * 60)
            return True
            
        else:
            print("\n❌ Peer instance not found in web_ui module.")
            print("   Make sure the peer is running with Web UI enabled.")
            return False
            
    except ImportError:
        print("\n❌ Could not import web_ui module.")
        print("   This script needs to access the peer instance.")
        print("\n   SOLUTION: Run this script in the same Python environment")
        print("   where your peer is running, or modify it to connect via socket.")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Create deadlock in running peer")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Peer host")
    parser.add_argument("--port", type=int, default=9001, help="Peer port")
    
    args = parser.parse_args()
    
    success = create_deadlock_scenario(args.host, args.port)
    
    if not success:
        print("\n" + "=" * 60)
        print("ALTERNATIVE METHOD:")
        print("=" * 60)
        print("If the above didn't work, you can:")
        print("1. Stop your peer")
        print("2. Run: python create_deadlock.py (creates standalone deadlock)")
        print("3. Modify the peer's deadlock detector manually")
        print("   OR use the Web UI API if you add an endpoint")
        print("=" * 60)
    
    sys.exit(0 if success else 1)

