#!/usr/bin/env python3
"""
Simple script to create and detect an actual deadlock.
Perfect for demonstrating to your instructor!
"""

from deadlock_detector import DeadlockDetector, ResourceType

def main():
    print("=" * 70)
    print("CREATING ACTUAL DEADLOCK - DEMONSTRATION")
    print("=" * 70)
    
    detector = DeadlockDetector()
    
    # Step 1: Setup
    print("\n📋 STEP 1: Setting up resources and processes")
    print("-" * 70)
    
    detector.register_resource("R1", ResourceType.CPU, 2)  # Only 2 units
    detector.register_resource("R2", ResourceType.MEMORY, 2)  # Only 2 units
    print("✓ Resources registered:")
    print("  • R1 (CPU): 2 units")
    print("  • R2 (MEMORY): 2 units")
    
    detector.register_process("P1", {"R1": 2, "R2": 1})  # Needs all R1 + 1 R2
    detector.register_process("P2", {"R1": 1, "R2": 2})  # Needs 1 R1 + all R2
    print("\n✓ Processes registered:")
    print("  • P1: needs {R1: 2, R2: 1}")
    print("  • P2: needs {R1: 1, R2: 2}")
    
    # Step 2: Create deadlock manually
    print("\n🔧 STEP 2: Manually creating deadlock state")
    print("-" * 70)
    print("(Bypassing safety checks to demonstrate detection)")
    
    with detector.lock:
        # P1 gets all of R1
        detector.resources["R1"].available_units = 0
        detector.resources["R1"].allocated["P1"] = 2
        detector.processes["P1"]["allocation"]["R1"] = 2
        detector.processes["P1"]["need"]["R1"] = 0
        print("✓ P1 allocated R1 (2 units)")
        
        # P2 gets all of R2
        detector.resources["R2"].available_units = 0
        detector.resources["R2"].allocated["P2"] = 2
        detector.processes["P2"]["allocation"]["R2"] = 2
        detector.processes["P2"]["need"]["R2"] = 0
        print("✓ P2 allocated R2 (2 units)")
    
    # Step 3: Show the deadlock
    print("\n🔴 STEP 3: Deadlock condition created!")
    print("-" * 70)
    
    status = detector.get_resource_status()
    
    print("\nCurrent Resource Allocation:")
    for rid, res_info in status['resources'].items():
        print(f"  {rid}:")
        print(f"    Available: {res_info['available']}")
        print(f"    Allocated: {res_info['allocated']}")
    
    print("\nProcess Status:")
    for pid, proc_info in status['processes'].items():
        print(f"  {pid}:")
        print(f"    Has: {proc_info['allocation']}")
        print(f"    Needs: {proc_info['need']}")
    
    print("\n🔴 DEADLOCK EXPLANATION:")
    print("  • P1 needs R2 (1 unit) → but P2 holds ALL R2 (2 units)")
    print("  • P2 needs R1 (1 unit) → but P1 holds ALL R1 (2 units)")
    print("  • P1 waits for P2 → P2 waits for P1 → CIRCULAR WAIT!")
    print("  • ⚠️  DEADLOCK EXISTS!")
    
    # Step 4: Detect it
    print("\n🔍 STEP 4: Detecting the deadlock")
    print("-" * 70)
    
    deadlock, processes = detector.detect_deadlock()
    
    if deadlock:
        print("\n✅ SUCCESS! Deadlock detected!")
        print(f"   Deadlocked processes: {sorted(set(processes))}")
        print("\n💡 The system successfully detected the deadlock using:")
        print("   • Cycle detection in wait-for graph")
        print("   • DFS (Depth-First Search) algorithm")
    else:
        print("\n❌ ERROR: Deadlock not detected (this shouldn't happen!)")
    
    # Step 5: Show safe state
    print("\n📊 STEP 5: System state analysis")
    print("-" * 70)
    safe = detector._is_safe_state()
    print(f"Safe state: {'✅ YES' if safe else '❌ NO'}")
    if not safe:
        print("⚠️  System is in UNSAFE state")
        print("   (This is why deadlock occurred)")
    
    print("\n" + "=" * 70)
    print("✅ DEMONSTRATION COMPLETE!")
    print("=" * 70)
    print("\n📝 Key Points for Your Instructor:")
    print("   1. Deadlock was created by manual state manipulation")
    print("   2. System detected it using cycle detection algorithm")
    print("   3. In normal operation, Banker's Algorithm prevents this")
    print("   4. Detection proves the system can identify deadlocks")
    print("=" * 70)


if __name__ == "__main__":
    main()

