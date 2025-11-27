# Quick Start Guide

## Fastest Way to Test the System

### Step 1: Start the Tracker

Open Terminal 1:
```bash
cd /path/to/termprojectos
python tracker.py
```

You should see:
```
Starting tracker on 0.0.0.0:8888
Press Ctrl+C to stop
```

### Step 2: Start a Peer

Open Terminal 2:
```bash
cd /path/to/termprojectos
python peer.py --port 9000
```

You should see:
```
Starting peer on port 9000
Connecting to tracker at 127.0.0.1:8888
Press Ctrl+C to stop
```

### Step 3: Test the System

Open Terminal 3:
```bash
cd /path/to/termprojectos
python test_system.py --host 127.0.0.1 --port 9000
```

Or test manually:
```bash
# Test CPU task
python client.py --host 127.0.0.1 --port 9000 cpu \
  --program "def main(x): return x * x" \
  --function main \
  --args "[5]"

# Test memory
python client.py --host 127.0.0.1 --port 9000 set-mem --key "test" --value "hello"
python client.py --host 127.0.0.1 --port 9000 get-mem --key "test"

# Check status
python client.py --host 127.0.0.1 --port 9000 status
```

## Testing Across Two Machines

### Machine 1 (Tracker + Peer)

Terminal 1 - Tracker:
```bash
python tracker.py
```

Terminal 2 - Peer:
```bash
python peer.py --port 9000
```

Find Machine 1's IP:
```bash
# Linux/Mac
ip addr show | grep "inet " | grep -v 127.0.0.1

# Windows
ipconfig
```

### Machine 2 (Peer)

```bash
python peer.py --port 9000 --tracker-host <MACHINE1_IP> --tracker-port 8888
```

### Test from Machine 2

```bash
# This task will be executed on the least-loaded peer (could be Machine 1 or 2)
python client.py --host 127.0.0.1 --port 9000 cpu \
  --program "def main(n): return sum(range(1, n+1))" \
  --function main \
  --args "[100]"
```

## Common Issues

**"Connection refused"**
- Make sure tracker is running first
- Check firewall settings
- Verify IP address is correct

**"Port already in use"**
- Use a different port: `python peer.py --port 9001`
- Kill the process using the port

**"No peers available"**
- Make sure at least one peer is running
- Check that peer successfully registered with tracker (check logs)

## Next Steps

- Read the full README.md for detailed documentation
- Try the examples in examples.py
- Experiment with confidential vs non-confidential tasks
- Test file sharing between peers






