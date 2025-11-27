# Running Multiple Peers on Different Machines

## Overview

You can run peers on different machines (laptops, computers) that all connect to the same tracker. This demonstrates true distributed P2P networking.

## Setup Instructions

### Step 1: Find Machine 1's IP Address

**On Machine 1 (where tracker will run):**

```bash
hostname -I
```

You'll get something like: `192.168.1.100` or `192.168.0.112`

**Write this down - you'll need it for other machines!**

### Step 2: Start Tracker on Machine 1

**Machine 1 - Terminal 1:**
```bash
cd ~/Downloads/termprojectos
python3 tracker.py
```

You should see:
```
Starting tracker on 0.0.0.0:8888
Press Ctrl+C to stop
```

**Keep this terminal open!**

### Step 3: Start Peer 1 on Machine 1 (Optional)

**Machine 1 - Terminal 2:**
```bash
python3 peer.py --port 9000 --web-ui --web-host 0.0.0.0
```

Access: `http://<MACHINE1_IP>:5000`

### Step 4: Start Peer 2 on Machine 2

**On Machine 2 (your friend's laptop):**

1. **Copy the project** to Machine 2 (or clone from same source)

2. **Start Peer 2:**
```bash
cd ~/Downloads/termprojectos
python3 peer.py --port 9000 --tracker-host 192.168.1.100 --tracker-port 8888 --web-ui --web-host 0.0.0.0
```

Replace `192.168.1.100` with Machine 1's actual IP address.

Access Peer 2 UI: `http://<MACHINE2_IP>:5000`

### Step 5: Start Peer 3 on Machine 3 (Optional)

**On Machine 3 (another friend's laptop):**

```bash
cd ~/Downloads/termprojectos
python3 peer.py --port 9000 --tracker-host 192.168.1.100 --tracker-port 8888 --web-ui --web-host 0.0.0.0
```

Replace `192.168.1.100` with Machine 1's actual IP address.

Access Peer 3 UI: `http://<MACHINE3_IP>:5000`

## Complete Example

### Machine 1 (IP: 192.168.1.100)

**Terminal 1 - Tracker:**
```bash
python3 tracker.py
```

**Terminal 2 - Peer 1:**
```bash
python3 peer.py --port 9000 --web-ui --web-host 0.0.0.0
```

**Access Peer 1:** `http://192.168.1.100:5000`

### Machine 2 (IP: 192.168.1.101)

**Peer 2:**
```bash
python3 peer.py --port 9000 --tracker-host 192.168.1.100 --tracker-port 8888 --web-ui --web-host 0.0.0.0
```

**Access Peer 2:** `http://192.168.1.101:5000`

### Machine 3 (IP: 192.168.1.102)

**Peer 3:**
```bash
python3 peer.py --port 9000 --tracker-host 192.168.1.100 --tracker-port 8888 --web-ui --web-host 0.0.0.0
```

**Access Peer 3:** `http://192.168.1.102:5000`

## Testing Distributed System

### Test 1: Submit Task from Machine 2

**On Machine 2, open web UI:**
```
http://192.168.1.101:5000
```

1. Go to **CPU Tasks** tab
2. Enter program:
   ```python
   def main(x):
       return x * x
   ```
3. Set function: `main`
4. Set args: `[5]`
5. Click **Execute Task**

**What happens:**
- Task goes to tracker on Machine 1
- Tracker selects least-loaded peer (could be Machine 1, 2, or 3)
- Task executes on selected machine
- Result returns to Machine 2

### Test 2: Check Status from Any Machine

**From any machine's web UI:**
- Go to **Dashboard** tab
- See real-time statistics
- View which peer executed tasks

### Test 3: Load Balancing

1. Submit multiple tasks from different machines
2. Tasks will be distributed across all peers
3. Tracker balances load automatically

## Network Requirements

### All Machines Must:
- ✅ Be on the **same WiFi network** (or same LAN)
- ✅ Have **firewall ports open** (8888 for tracker, 9000+ for peers, 5000 for web UI)
- ✅ Have **Python 3** installed
- ✅ Have **project files** (or access to them)

### Firewall Configuration

**On each machine, allow ports:**

**Fedora/RHEL:**
```bash
sudo firewall-cmd --add-port=8888/tcp --permanent  # Tracker
sudo firewall-cmd --add-port=9000/tcp --permanent  # Peer
sudo firewall-cmd --add-port=5000/tcp --permanent  # Web UI
sudo firewall-cmd --reload
```

**Ubuntu/Debian:**
```bash
sudo ufw allow 8888/tcp  # Tracker
sudo ufw allow 9000/tcp  # Peer
sudo ufw allow 5000/tcp  # Web UI
```

## Troubleshooting

### Peer Can't Connect to Tracker

**Problem:** `Connection refused` or `No peers available`

**Solutions:**
1. **Check tracker is running** on Machine 1
2. **Verify IP address** is correct
3. **Check firewall** allows port 8888
4. **Verify same network** - all machines on same WiFi
5. **Test connectivity:**
   ```bash
   # From Machine 2, test connection to Machine 1
   ping 192.168.1.100
   telnet 192.168.1.100 8888
   ```

### Can't Access Web UI from Other Machine

**Problem:** Web UI not accessible from other machines

**Solutions:**
1. **Use `--web-host 0.0.0.0`** (not `127.0.0.1`)
2. **Check firewall** allows port 5000
3. **Use correct IP** - use machine's IP, not localhost
4. **Check network** - machines must be on same network

### Wrong IP Address

**Find correct IP:**
```bash
hostname -I
```

Or:
```bash
ip addr show | grep "inet " | grep -v 127.0.0.1
```

### Tracker Not Visible

**Make sure tracker binds to all interfaces:**
- Tracker should show: `Starting tracker on 0.0.0.0:8888`
- If it shows `127.0.0.1`, it won't accept external connections

## Step-by-Step Checklist

### Machine 1 (Tracker Host)
- [ ] Find IP address: `hostname -I`
- [ ] Start tracker: `python3 tracker.py`
- [ ] Allow firewall port 8888
- [ ] (Optional) Start Peer 1 with `--web-host 0.0.0.0`

### Machine 2 (Peer 2)
- [ ] Copy project files
- [ ] Install Python 3
- [ ] Install Flask: `pip3 install Flask`
- [ ] Start peer: `python3 peer.py --port 9000 --tracker-host <MACHINE1_IP> --web-ui --web-host 0.0.0.0`
- [ ] Allow firewall ports 9000 and 5000
- [ ] Test: Open `http://<MACHINE2_IP>:5000`

### Machine 3 (Peer 3)
- [ ] Same as Machine 2
- [ ] Use same tracker IP (Machine 1's IP)

## Example: 3 Friends Testing

**Friend 1 (Machine 1 - IP: 192.168.1.100):**
```bash
# Terminal 1
python3 tracker.py

# Terminal 2
python3 peer.py --port 9000 --web-ui --web-host 0.0.0.0
```

**Friend 2 (Machine 2 - IP: 192.168.1.101):**
```bash
python3 peer.py --port 9000 --tracker-host 192.168.1.100 --web-ui --web-host 0.0.0.0
```

**Friend 3 (Machine 3 - IP: 192.168.1.102):**
```bash
python3 peer.py --port 9000 --tracker-host 192.168.1.100 --web-ui --web-host 0.0.0.0
```

**All friends can:**
- Access their own web UI
- Submit tasks that execute on any machine
- See distributed load balancing
- Test true P2P networking

## Quick Reference

**Tracker (Machine 1):**
```bash
python3 tracker.py
```

**Peer on Another Machine:**
```bash
python3 peer.py --port 9000 --tracker-host <MACHINE1_IP> --tracker-port 8888 --web-ui --web-host 0.0.0.0
```

**Key Points:**
- Replace `<MACHINE1_IP>` with actual IP
- All machines must be on same network
- Open firewall ports
- Use `0.0.0.0` for web-host to allow external access

## Summary

✅ **Yes, you can run multiple peers on different machines!**

**Steps:**
1. Start tracker on Machine 1
2. Find Machine 1's IP address
3. Start peers on other machines with `--tracker-host <MACHINE1_IP>`
4. All peers connect to same tracker
5. Tasks distribute across all machines
6. Each machine has its own web UI

**Requirements:**
- Same WiFi/network
- Firewall ports open
- Correct IP addresses
- Python 3 + Flask installed

Enjoy distributed P2P networking! 🚀

