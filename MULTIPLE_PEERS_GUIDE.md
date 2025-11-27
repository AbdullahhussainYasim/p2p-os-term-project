# Running Multiple Peers Guide

## Overview

You can run multiple peer nodes that all connect to the same tracker. This allows:
- Load balancing across multiple peers
- Distributed task execution
- Testing the full P2P system
- Demonstrating resource sharing

## Setup: Multiple Peers on Same Machine

### Step 1: Start Tracker

**Terminal 1:**
```bash
cd ~/Downloads/termprojectos
python3 tracker.py
```

### Step 2: Start Peer 1

**Terminal 2:**
```bash
cd ~/Downloads/termprojectos
python3 peer.py --port 9000 --web-ui --web-port 5000
```

Access Peer 1 UI: `http://127.0.0.1:5000`

### Step 3: Start Peer 2

**Terminal 3:**
```bash
cd ~/Downloads/termprojectos
python3 peer.py --port 9001 --web-ui --web-port 5001
```

Access Peer 2 UI: `http://127.0.0.1:5001`

### Step 4: Start Peer 3 (Optional)

**Terminal 4:**
```bash
cd ~/Downloads/termprojectos
python3 peer.py --port 9002 --web-ui --web-port 5002
```

Access Peer 3 UI: `http://127.0.0.1:5002`

## Setup: Multiple Peers on Different Machines

### On Machine 1 (Tracker + Peer 1)

**Terminal 1 - Tracker:**
```bash
python3 tracker.py
```

**Terminal 2 - Peer 1:**
```bash
python3 peer.py --port 9000 --web-ui --web-host 0.0.0.0
```

Find Machine 1's IP:
```bash
hostname -I
# Example: 192.168.1.100
```

### On Machine 2 (Peer 2)

```bash
python3 peer.py --port 9000 --tracker-host 192.168.1.100 --tracker-port 8888 --web-ui --web-host 0.0.0.0
```

### On Machine 3 (Peer 3)

```bash
python3 peer.py --port 9000 --tracker-host 192.168.1.100 --tracker-port 8888 --web-ui --web-host 0.0.0.0
```

## Complete Example: 3 Peers on Same Machine

**Terminal 1 (Tracker):**
```bash
python3 tracker.py
```

**Terminal 2 (Peer 1 - Port 9000, Web UI 5000):**
```bash
python3 peer.py --port 9000 --web-ui --web-port 5000
```

**Terminal 3 (Peer 2 - Port 9001, Web UI 5001):**
```bash
python3 peer.py --port 9001 --web-ui --web-port 5001
```

**Terminal 4 (Peer 3 - Port 9002, Web UI 5002):**
```bash
python3 peer.py --port 9002 --web-ui --web-port 5002
```

**Access:**
- Peer 1: `http://127.0.0.1:5000`
- Peer 2: `http://127.0.0.1:5001`
- Peer 3: `http://127.0.0.1:5002`

## Testing Multiple Peers

### Test Load Balancing

1. Open Peer 1's web UI: `http://127.0.0.1:5000`
2. Submit a task (it may execute on any peer)
3. Check which peer executed it by looking at the status

### Test from CLI

Submit task from Peer 1, but it may execute on Peer 2 or 3:

```bash
# This task will be routed to least-loaded peer
python3 client.py --host 127.0.0.1 --port 9000 cpu \
  --program "def main(x): return x * x" \
  --function main \
  --args "[5]"
```

### Check Tracker Status

The tracker will show all registered peers. You can see this in the tracker's console output.

## Multiple Peers with Web UI

### Same Machine Setup

| Peer | Port | Web UI Port | Access URL |
|------|------|-------------|------------|
| Peer 1 | 9000 | 5000 | http://127.0.0.1:5000 |
| Peer 2 | 9001 | 5001 | http://127.0.0.1:5001 |
| Peer 3 | 9002 | 5002 | http://127.0.0.1:5002 |

### Different Machines Setup

| Machine | IP | Peer Port | Web UI Port | Access URL |
|---------|----|-----------|-------------|------------|
| Machine 1 | 192.168.1.100 | 9000 | 5000 | http://192.168.1.100:5000 |
| Machine 2 | 192.168.1.101 | 9000 | 5000 | http://192.168.1.101:5000 |
| Machine 3 | 192.168.1.102 | 9000 | 5000 | http://192.168.1.102:5000 |

## How Load Balancing Works

When you submit a task:

1. **Client** (Peer 1) requests CPU resources from **Tracker**
2. **Tracker** checks all registered peers' CPU loads
3. **Tracker** selects peer with **minimum load** (could be Peer 2 or 3)
4. **Client** sends task to selected peer
5. **Selected peer** executes task and returns result
6. **Client** receives result

## Example Workflow

### Scenario: 3 Peers, Task Distribution

1. **Start all peers:**
   - Tracker on port 8888
   - Peer 1 on port 9000
   - Peer 2 on port 9001
   - Peer 3 on port 9002

2. **Submit task from Peer 1:**
   ```bash
   python3 client.py --host 127.0.0.1 --port 9000 cpu \
     --program "def main(n): return sum(range(1, n+1))" \
     --function main \
     --args "[100]"
   ```

3. **Task execution:**
   - Tracker selects least-loaded peer (e.g., Peer 2)
   - Peer 2 executes the task
   - Result returned to Peer 1

4. **Submit another task:**
   - Now Peer 2 has higher load
   - Tracker selects Peer 3 (least loaded now)
   - Peer 3 executes the task

## Monitoring Multiple Peers

### Check Each Peer's Status

**Peer 1:**
```bash
python3 client.py --host 127.0.0.1 --port 9000 status
```

**Peer 2:**
```bash
python3 client.py --host 127.0.0.1 --port 9001 status
```

**Peer 3:**
```bash
python3 client.py --host 127.0.0.1 --port 9002 status
```

### View in Web UI

Open each peer's web UI to see:
- Current CPU load
- Queue size
- Task history
- Process information

## Quick Start Script

Create a script to start multiple peers:

**start_peers.sh:**
```bash
#!/bin/bash

# Start tracker
python3 tracker.py &
TRACKER_PID=$!

sleep 2

# Start peer 1
python3 peer.py --port 9000 --web-ui --web-port 5000 &
PEER1_PID=$!

# Start peer 2
python3 peer.py --port 9001 --web-ui --web-port 5001 &
PEER2_PID=$!

# Start peer 3
python3 peer.py --port 9002 --web-ui --web-port 5002 &
PEER3_PID=$!

echo "Tracker PID: $TRACKER_PID"
echo "Peer 1 PID: $PEER1_PID (http://127.0.0.1:5000)"
echo "Peer 2 PID: $PEER2_PID (http://127.0.0.1:5001)"
echo "Peer 3 PID: $PEER3_PID (http://127.0.0.1:5002)"
echo ""
echo "Press Ctrl+C to stop all"

wait
```

Make it executable:
```bash
chmod +x start_peers.sh
./start_peers.sh
```

## Troubleshooting

### Port Already in Use

If you get "port already in use":
- Use different ports: `--port 9001`, `--port 9002`, etc.
- Use different web ports: `--web-port 5001`, `--web-port 5002`, etc.

### Peers Not Connecting

- Make sure tracker is running first
- Check tracker host/port are correct
- Verify all peers are on same network (if different machines)

### Can't See Other Peers

- Check tracker console - it shows registered peers
- Verify all peers successfully registered
- Check network connectivity

## Summary

**To run multiple peers:**

1. **Start tracker** (one instance)
2. **Start peer 1**: `python3 peer.py --port 9000 --web-ui --web-port 5000`
3. **Start peer 2**: `python3 peer.py --port 9001 --web-ui --web-port 5001`
4. **Start peer 3**: `python3 peer.py --port 9002 --web-ui --web-port 5002`
5. **Access each**: Different URLs for each peer's web UI

**Key Points:**
- Each peer needs unique port
- Each web UI needs unique port
- All peers connect to same tracker
- Tracker balances load across all peers
- Tasks can execute on any peer

Enjoy testing with multiple peers! 🚀




