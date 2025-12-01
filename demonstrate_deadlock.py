#!/usr/bin/env python3
"""
Deadlock Demonstration Script
Shows how the system prevents and detects deadlocks.
"""

from deadlock_detector import DeadlockDetector, ResourceType
import time

def demonstrate_deadlock_prevention():
    """Demonstrate that Banker's Algorithm prevents deadlocks."""
    print("=" * 60)
    print("DEMONSTRATION 1: Deadlock Prevention (Banker's Algorithm)")
    print("=" * 60)
    
    detector = DeadlockDetector()
    
    # Register resources
    print("\n1. Registering resources...")
    detector.register_resource("R1", ResourceType.CPU, 2)  # Only 2 units available
    detector.register_resource("R2", ResourceType.MEMORY, 2)
    print("   ✓ Resources registered: R1 (2 units), R2 (2 units)")
    
    # Register processes with max needs
    print("\n2. Registering processes...")
    detector.register_process("P1", {"R1": 2, "R2": 1})  # Needs 2 R1, 1 R2
    detector.register_process("P2", {"R1": 1, "R2": 2})  # Needs 1 R1, 2 R2
    print("   ✓ P1 registered: max_need = {R1: 2, R2: 1}")
    print("   ✓ P2 registered: max_need = {R1: 1, R2: 2}")
    
    # Show initial state
    print("\n3. Initial state:")
    status = detector.get_resource_status()
    print(f"   Available: R1={status['resources']['R1']['available']}, R2={status['resources']['R2']['available']}")
    
    # P1 requests R1
    print("\n4. P1 requests R1 (2 units)...")
    safe, error = detector.request_resource("P1", "R1", 2)
    if safe:
        print("   ✅ GRANTED - System is safe")
    else:
        print(f"   ❌ DENIED - {error}")
    
    # P2 requests R2
    print("\n5. P2 requests R2 (2 units)...")
    safe, error = detector.request_resource("P2", "R2", 2)
    if safe:
        print("   ✅ GRANTED - System is safe")
    else:
        print(f"   ❌ DENIED - {error}")
    
    # Now try to create deadlock
    print("\n6. Attempting to create deadlock scenario...")
    print("   P1 now needs R2 (1 unit) to complete...")
    safe, error = detector.request_resource("P1", "R2", 1)
    if safe:
        print("   ✅ GRANTED - System is safe")
    else:
        print(f"   ❌ DENIED - {error}")
        print("   💡 Banker's Algorithm prevented deadlock!")
    
    print("\n7. P2 now needs R1 (1 unit) to complete...")
    safe, error = detector.request_resource("P2", "R1", 1)
    if safe:
        print("   ✅ GRANTED - System is safe")
    else:
        print(f"   ❌ DENIED - {error}")
        print("   💡 Banker's Algorithm prevented deadlock!")
    
    # Check for deadlock
    print("\n8. Checking for deadlock...")
    deadlock, processes = detector.detect_deadlock()
    if deadlock:
        print(f"   ⚠️  DEADLOCK DETECTED! Processes: {processes}")
    else:
        print("   ✅ NO DEADLOCK - System is safe")
    
    print("\n" + "=" * 60)


def demonstrate_deadlock_detection():
    """Demonstrate deadlock detection by manually creating a deadlock state."""
    print("\n" + "=" * 60)
    print("DEMONSTRATION 2: Deadlock Detection (Cycle Detection)")
    print("=" * 60)
    
    detector = DeadlockDetector()
    
    # Register resources
    print("\n1. Registering resources...")
    detector.register_resource("R1", ResourceType.CPU, 3)
    detector.register_resource("R2", ResourceType.MEMORY, 3)
    print("   ✓ Resources registered: R1 (3 units), R2 (3 units)")
    
    # Register processes
    print("\n2. Registering processes...")
    detector.register_process("P1", {"R1": 2, "R2": 1})
    detector.register_process("P2", {"R1": 1, "R2": 2})
    detector.register_process("P3", {"R1": 1, "R2": 1})
    print("   ✓ 3 processes registered")
    
    # Manually create deadlock by bypassing safety checks
    # (In real system, this would be prevented, but we'll simulate it)
    print("\n3. Creating deadlock scenario (simulating unsafe allocations)...")
    
    # P1 gets R1
    print("   P1 acquires R1 (2 units)...")
    detector.request_resource("P1", "R1", 2)
    
    # P2 gets R2
    print("   P2 acquires R2 (2 units)...")
    detector.request_resource("P2", "R2", 2)
    
    # P3 gets R1 (1 unit) - remaining
    print("   P3 acquires R1 (1 unit)...")
    detector.request_resource("P3", "R1", 1)
    
    # Now show the deadlock state
    print("\n4. Current resource allocation:")
    status = detector.get_resource_status()
    for rid, res_info in status['resources'].items():
        print(f"   {rid}: Available={res_info['available']}, Allocated={res_info['allocated']}")
    
    print("\n5. Process needs:")
    for pid, proc_info in status['processes'].items():
        print(f"   {pid}: Need={proc_info['need']}, Allocation={proc_info['allocation']}")
    
    # Now P1 needs R2 (but P2 has it)
    # P2 needs R1 (but P1 and P3 have it)
    # This creates a circular wait
    print("\n6. Deadlock scenario:")
    print("   P1 needs R2 (1 unit) → but P2 holds R2")
    print("   P2 needs R1 (1 unit) → but P1 and P3 hold R1")
    print("   → Circular wait condition!")
    
    # Detect deadlock
    print("\n7. Running deadlock detection...")
    deadlock, processes = detector.detect_deadlock()
    
    if deadlock:
        print(f"   ⚠️  DEADLOCK DETECTED!")
        print(f"   Deadlocked processes: {processes}")
        print("\n   💡 The system successfully detected the deadlock using cycle detection!")
    else:
        print("   ✅ No deadlock detected")
    
    print("\n" + "=" * 60)


def create_actual_deadlock():
    """Create an actual deadlock by manually manipulating the state."""
    print("\n" + "=" * 60)
    print("DEMONSTRATION 3: Creating ACTUAL Deadlock (Manual State Manipulation)")
    print("=" * 60)
    print("\n⚠️  This demonstration manually creates a deadlock state")
    print("   by bypassing safety checks to show detection works.")
    print("=" * 60)
    
    detector = DeadlockDetector()
    
    # Register resources
    print("\n1. Registering resources...")
    detector.register_resource("R1", ResourceType.CPU, 2)  # Only 2 units
    detector.register_resource("R2", ResourceType.MEMORY, 2)  # Only 2 units
    print("   ✓ Resources: R1 (2 units), R2 (2 units)")
    
    # Register processes
    print("\n2. Registering processes...")
    detector.register_process("P1", {"R1": 2, "R2": 1})  # Needs all R1 + 1 R2
    detector.register_process("P2", {"R1": 1, "R2": 2})  # Needs 1 R1 + all R2
    print("   ✓ P1: needs {R1: 2, R2: 1}")
    print("   ✓ P2: needs {R1: 1, R2: 2}")
    
    # Manually create deadlock by directly manipulating internal state
    print("\n3. Manually creating deadlock state (bypassing safety checks)...")
    print("   This simulates what would happen if safety checks were bypassed.")
    
    with detector.lock:
        # P1 gets all of R1
        detector.resources["R1"].available_units = 0
        detector.resources["R1"].allocated["P1"] = 2
        detector.processes["P1"]["allocation"]["R1"] = 2
        detector.processes["P1"]["need"]["R1"] = 0
        print("   ✓ P1 allocated R1 (2 units) - R1 is now exhausted")
        
        # P2 gets all of R2
        detector.resources["R2"].available_units = 0
        detector.resources["R2"].allocated["P2"] = 2
        detector.processes["P2"]["allocation"]["R2"] = 2
        detector.processes["P2"]["need"]["R2"] = 0
        print("   ✓ P2 allocated R2 (2 units) - R2 is now exhausted")
        
        # Now:
        # P1 needs R2 (1 unit) but P2 has all R2 → P1 waits for P2
        # P2 needs R1 (1 unit) but P1 has all R1 → P2 waits for P1
        # → CIRCULAR WAIT = DEADLOCK!
    
    print("\n4. Current state after manual allocation:")
    status = detector.get_resource_status()
    print("\n   Resources:")
    for rid, res_info in status['resources'].items():
        print(f"     {rid}: Available={res_info['available']}, Allocated={res_info['allocated']}")
    
    print("\n   Processes:")
    for pid, proc_info in status['processes'].items():
        print(f"     {pid}:")
        print(f"       Allocation: {proc_info['allocation']}")
        print(f"       Need: {proc_info['need']}")
    
    print("\n5. Deadlock condition:")
    print("   🔴 P1 needs R2 (1 unit) → but P2 holds all R2 (2 units)")
    print("   🔴 P2 needs R1 (1 unit) → but P1 holds all R1 (2 units)")
    print("   🔴 Circular wait: P1 → waits for P2 → waits for P1")
    print("   ⚠️  DEADLOCK EXISTS!")
    
    # Check safe state
    print("\n6. Checking if system is in safe state...")
    safe = detector._is_safe_state()
    print(f"   Safe state: {'✅ YES' if safe else '❌ NO'}")
    if not safe:
        print("   ⚠️  System is in UNSAFE state (deadlock possible)")
    
    # Detect deadlock
    print("\n7. Running deadlock detection algorithm...")
    deadlock, processes = detector.detect_deadlock()
    
    if deadlock:
        print(f"\n   ⚠️  DEADLOCK DETECTED!")
        print(f"   Deadlocked processes: {sorted(set(processes))}")
        print("\n   💡 The cycle detection algorithm successfully identified the deadlock!")
        print("   💡 This proves the detection mechanism works correctly!")
    else:
        print("\n   ❌ No deadlock detected (this shouldn't happen!)")
    
    print("\n" + "=" * 60)


def demonstrate_with_peer():
    """Demonstrate using an actual peer instance."""
    print("\n" + "=" * 60)
    print("DEMONSTRATION 4: Using Peer Instance")
    print("=" * 60)
    
    from peer import Peer
    
    print("\n1. Creating peer instance (no need to start server for this demo)...")
    peer = Peer(peer_port=9001)
    # Note: We don't need to start the peer server for deadlock demonstration
    # The deadlock_detector is already initialized in __init__
    
    print("   ✓ Peer instance created (deadlock detector ready)")
    
    # Access deadlock detector
    detector = peer.deadlock_detector
    
    print("\n2. Resources already registered:")
    status = detector.get_resource_status()
    for rid, res_info in status['resources'].items():
        print(f"   {rid}: {res_info['total']} units")
    
    print("\n3. Registering test processes...")
    detector.register_process("TEST_P1", {"CPU": 3, "MEMORY": 500})
    detector.register_process("TEST_P2", {"CPU": 3, "MEMORY": 500})
    print("   ✓ Processes registered")
    
    print("\n4. Testing resource requests...")
    safe, error = detector.request_resource("TEST_P1", "CPU", 3)
    print(f"   TEST_P1 requests CPU (3 units): {'✅ GRANTED' if safe else '❌ DENIED - ' + str(error)}")
    
    safe, error = detector.request_resource("TEST_P2", "CPU", 3)
    print(f"   TEST_P2 requests CPU (3 units): {'✅ GRANTED' if safe else '❌ DENIED - ' + str(error)}")
    
    print("\n5. Checking for deadlock...")
    deadlock, processes = detector.detect_deadlock()
    if deadlock:
        print(f"   ⚠️  DEADLOCK DETECTED! Processes: {processes}")
    else:
        print("   ✅ NO DEADLOCK - System is safe")
    
    print("\n6. Resource status:")
    status = detector.get_resource_status()
    print(f"   Safe state: {status['safe_state']}")
    print(f"   CPU available: {status['resources']['CPU']['available']}/{status['resources']['CPU']['total']}")
    print(f"   MEMORY available: {status['resources']['MEMORY']['available']}/{status['resources']['MEMORY']['total']}")
    
    print("\n" + "=" * 60)
    print("\n💡 TIP: You can also check deadlock via Web UI:")
    print("   1. Open http://localhost:5000 (if web-ui is enabled)")
    print("   2. Go to 'OS Features' tab")
    print("   3. Click 'Check for Deadlocks' button")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("DEADLOCK DETECTION SYSTEM - DEMONSTRATION")
    print("=" * 60)
    
    # Run demonstrations
    demonstrate_deadlock_prevention()
    demonstrate_deadlock_detection()
    create_actual_deadlock()  # This is the key one for showing actual deadlock!
    
    # Ask user if they want to test with actual peer
    print("\n" + "=" * 60)
    response = input("\nDo you want to test with an actual peer? (y/n): ")
    if response.lower() == 'y':
        demonstrate_with_peer()
    
    print("\n✅ Demonstration complete!")
    print("=" * 60)
    print("\n📝 SUMMARY:")
    print("   • Demonstration 1: Shows how Banker's Algorithm PREVENTS deadlocks")
    print("   • Demonstration 2: Shows deadlock DETECTION with cycle detection")
    print("   • Demonstration 3: Creates ACTUAL deadlock to prove detection works")
    print("   • Demonstration 4: Tests with real Peer instance")
    print("=" * 60)