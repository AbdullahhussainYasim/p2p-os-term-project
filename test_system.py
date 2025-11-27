"""
Simple test script to verify the P2P system is working.
Run this after starting the tracker and at least one peer.
"""

import time
import sys
from client import P2PClient


def test_cpu_task(client: P2PClient):
    """Test CPU task execution."""
    print("Testing CPU task execution...")
    
    program = "def main(x): return x * x"
    result = client.execute_cpu_task(program, "main", [5], confidential=False)
    
    if result.get("error"):
        print(f"❌ CPU task failed: {result['error']}")
        return False
    
    if result.get("result") == 25:
        print("✅ CPU task passed: 5 * 5 = 25")
        return True
    else:
        print(f"❌ CPU task failed: expected 25, got {result.get('result')}")
        return False


def test_confidential_task(client: P2PClient):
    """Test confidential task execution."""
    print("Testing confidential task execution...")
    
    program = "def main(x): return x + 10"
    result = client.execute_cpu_task(program, "main", [5], confidential=True)
    
    if result.get("error"):
        print(f"❌ Confidential task failed: {result['error']}")
        return False
    
    if result.get("result") == 15:
        print("✅ Confidential task passed: 5 + 10 = 15")
        return True
    else:
        print(f"❌ Confidential task failed: expected 15, got {result.get('result')}")
        return False


def test_memory_operations(client: P2PClient):
    """Test memory operations."""
    print("Testing memory operations...")
    
    # Set memory
    result = client.set_memory("test_key", "test_value")
    if result.get("error"):
        print(f"❌ SET_MEM failed: {result['error']}")
        return False
    
    # Get memory
    result = client.get_memory("test_key")
    if result.get("error"):
        print(f"❌ GET_MEM failed: {result['error']}")
        return False
    
    if result.get("found") and result.get("value") == "test_value":
        print("✅ Memory operations passed")
        return True
    else:
        print(f"❌ Memory operations failed: {result}")
        return False


def test_file_operations(client: P2PClient):
    """Test file operations."""
    print("Testing file operations...")
    
    import tempfile
    import os
    
    # Create a test file
    test_content = b"Hello, P2P File Storage!"
    with tempfile.NamedTemporaryFile(delete=False, mode='wb') as f:
        test_file = f.name
        f.write(test_content)
    
    try:
        # Upload file
        result = client.put_file("test_file.txt", test_file)
        if result.get("error"):
            print(f"❌ PUT_FILE failed: {result['error']}")
            return False
        
        # Download file
        with tempfile.NamedTemporaryFile(delete=False, mode='wb') as f:
            download_file = f.name
        
        result = client.get_file("test_file.txt", download_file)
        if result.get("error"):
            print(f"❌ GET_FILE failed: {result['error']}")
            return False
        
        if not result.get("found"):
            print("❌ File not found after upload")
            return False
        
        # Verify content
        with open(download_file, 'rb') as f:
            downloaded_content = f.read()
        
        if downloaded_content == test_content:
            print("✅ File operations passed")
            return True
        else:
            print("❌ File content mismatch")
            return False
    
    finally:
        # Cleanup
        if os.path.exists(test_file):
            os.unlink(test_file)
        if os.path.exists(download_file):
            os.unlink(download_file)


def test_status(client: P2PClient):
    """Test status endpoint."""
    print("Testing status endpoint...")
    
    result = client.get_status()
    if result.get("error"):
        print(f"❌ Status failed: {result['error']}")
        return False
    
    if "status" in result and result["status"] == "OK":
        print("✅ Status endpoint passed")
        print(f"   Peer: {result.get('peer_ip')}:{result.get('peer_port')}")
        return True
    else:
        print(f"❌ Status failed: {result}")
        return False


def main():
    """Run all tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test P2P Resource Sharing System")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Peer host")
    parser.add_argument("--port", type=int, default=9000, help="Peer port")
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("P2P Resource Sharing System - Test Suite")
    print("=" * 50)
    print(f"Testing peer at {args.host}:{args.port}\n")
    
    client = P2PClient(args.host, args.port)
    
    tests = [
        ("Status", test_status),
        ("CPU Task", test_cpu_task),
        ("Confidential Task", test_confidential_task),
        ("Memory Operations", test_memory_operations),
        ("File Operations", test_file_operations),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func(client)
            results.append((test_name, result))
            time.sleep(0.5)  # Small delay between tests
        except Exception as e:
            print(f"❌ {test_name} raised exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("Test Results Summary")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())






