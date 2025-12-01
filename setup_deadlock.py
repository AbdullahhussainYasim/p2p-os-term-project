#!/usr/bin/env python3
"""
Simple script to create a deadlock in your running peer.
Run this while your peer is running with Web UI.

Usage:
    1. Start your peer: python peer.py --port 9001 --web-ui --web-port 5000
    2. In another terminal, run: python setup_deadlock.py
    3. Go to Web UI and click "Check for Deadlocks"
"""

import requests
import sys

def create_deadlock(web_port=5000):
    """Create deadlock in the running peer via API."""
    print("=" * 60)
    print("Creating Deadlock Scenario")
    print("=" * 60)
    print(f"Connecting to Web UI at http://localhost:{web_port}...")
    
    try:
        # Call the API endpoint to setup deadlock
        response = requests.post(
            f"http://localhost:{web_port}/api/deadlock/setup",
            timeout=5
        )
        
        if response.status_code != 200:
            print(f"❌ Error: HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        data = response.json()
        
        if "error" in data:
            print(f"❌ Error: {data['error']}")
            return False
        
        if data.get("success"):
            print("✓ Resources and processes registered")
            print("✓ Deadlock state created:")
            print("  • P1 holds R1 (2 units), needs R2 (1 unit)")
            print("  • P2 holds R2 (2 units), needs R1 (1 unit)")
            print("  • Circular wait: P1 → P2 → P1")
            
            if data.get("deadlock"):
                print("\n✅ DEADLOCK CREATED AND DETECTED!")
                processes = data.get("deadlocked_processes", [])
                print(f"   Deadlocked processes: {sorted(set(processes))}")
                print("\n" + "=" * 60)
                print("Next Steps:")
                print(f"  1. Go to your Web UI (http://localhost:{web_port})")
                print("  2. Click on 'OS Features' tab")
                print("  3. Click 'Check for Deadlocks' button")
                print("  4. You should see: ⚠️ DEADLOCK DETECTED!")
                print("=" * 60)
                return True
            else:
                print("\n⚠️  Deadlock scenario created but not detected yet.")
                print("   Try clicking 'Check for Deadlocks' in Web UI.")
                return True
        else:
            print("❌ Failed to create deadlock scenario")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to Web UI!")
        print(f"   Make sure your peer is running with Web UI on port {web_port}")
        print("   Start it with: python peer.py --web-ui --web-port 5000")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Create deadlock in running peer")
    parser.add_argument("--port", type=int, default=5000, help="Web UI port (default: 5000)")
    
    args = parser.parse_args()
    
    success = create_deadlock(args.port)
    sys.exit(0 if success else 1)

