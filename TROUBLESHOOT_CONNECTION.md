# Troubleshooting Connection Issues

## Your Current Problem

**Error:** `Connection refused` when trying to connect to tracker

**Cause:** Using wrong IP address (`172.16.23.255` is broadcast, not tracker IP)

## Solution

### Step 1: Use Correct Tracker IP

**From Machine 1 (where tracker runs), get the actual IP:**
```bash
ip addr | grep "inet " | grep -v "127.0.0.1"
```

You should see: `172.16.18.70` (this is the correct IP to use!)

### Step 2: Check if Machine 2 Can Reach Machine 1

**On Machine 2 (Kali Linux), test connection:**
```bash
# Test ping
ping 172.16.18.70

# Test if tracker port is open
telnet 172.16.18.70 8888
# or
nc -zv 172.16.18.70 8888
```

**If ping fails:**
- Machines might not be on same network
- Firewall blocking
- VM networking issue (see below)

### Step 3: VM Networking Issue

**I notice your peer shows IP `10.0.2.15`** - this is a VirtualBox NAT IP!

**If Machine 2 is a VM:**
- VM with NAT networking can't directly reach host network
- Need to use **Bridged** or **Host-Only** networking

**Fix VM networking:**
1. Shut down VM
2. Settings → Network → Adapter 1
3. Change from "NAT" to "Bridged Adapter"
4. Select your WiFi adapter
5. Start VM
6. Get new IP: `ip addr` (should be `172.16.x.x` now)

## Correct Commands

### Machine 1 (Tracker - IP: 172.16.18.70)

**Terminal 1:**
```bash
python3 tracker.py
```

**Terminal 2:**
```bash
python3 peer.py --port 9000 --web-ui --web-host 0.0.0.0
```

### Machine 2 (Kali - Use Correct IP!)

**If VM with Bridged networking (IP should be 172.16.x.x):**
```bash
python3 peer.py --port 9001 --tracker-host 172.16.18.70 --tracker-port 8888 --web-ui --web-host 0.0.0.0 --web-port 5001
```

**If still using NAT (10.0.2.15):**
- This won't work! You need bridged networking.

## Network Configuration Check

### Check Machine 1 IP
```bash
hostname -I
# Should show: 172.16.18.70
```

### Check Machine 2 IP
```bash
hostname -I
# If shows 10.0.2.15 → VM with NAT (won't work!)
# If shows 172.16.x.x → Good! Can connect
```

### Verify Same Network
Both machines should have IPs starting with `172.16.` (or same subnet)

## Firewall Check

### On Machine 1 (Tracker):
```bash
# Fedora/RHEL
sudo firewall-cmd --list-ports
sudo firewall-cmd --add-port=8888/tcp --permanent
sudo firewall-cmd --reload

# Ubuntu/Debian
sudo ufw status
sudo ufw allow 8888/tcp
```

### On Machine 2:
```bash
# Allow peer and web UI ports
sudo ufw allow 9001/tcp
sudo ufw allow 5001/tcp
```

## Testing Steps

### 1. Test Tracker is Running
**On Machine 1:**
```bash
netstat -tuln | grep 8888
# Should show: tcp 0 0 0.0.0.0:8888
```

### 2. Test Connection from Machine 2
```bash
# Test if can reach Machine 1
ping 172.16.18.70

# Test if tracker port is accessible
telnet 172.16.18.70 8888
# Should connect (press Ctrl+] then 'quit' to exit)
```

### 3. If Connection Works, Start Peer
```bash
python3 peer.py --port 9001 --tracker-host 172.16.18.70 --tracker-port 8888 --web-ui --web-host 0.0.0.0 --web-port 5001
```

## Expected Output

### Machine 1 (Tracker):
```
Tracker listening on 0.0.0.0:8888
Peer registered: 172.16.18.70:9000
Peer registered: <machine2-ip>:9001
```

### Machine 2 (Peer):
```
Starting peer on port 9001
Connecting to tracker at 172.16.18.70:8888
Registered with tracker at 172.16.18.70:8888  ← Should see this!
Starting web UI on http://0.0.0.0:5001
```

**If you see "Connection refused":**
- Wrong IP address
- Tracker not running
- Firewall blocking
- VM networking issue

## Quick Checklist

- [ ] Tracker running on Machine 1
- [ ] Using correct tracker IP: `172.16.18.70` (not `172.16.23.255`)
- [ ] Machine 2 can ping Machine 1
- [ ] Machine 2 can connect to port 8888
- [ ] Both machines on same network (same subnet)
- [ ] Firewall allows port 8888
- [ ] If VM, using Bridged networking (not NAT)

## Still Not Working?

1. **Check tracker is actually running:**
   ```bash
   # On Machine 1
   ps aux | grep tracker.py
   ```

2. **Check what IP tracker is listening on:**
   ```bash
   # On Machine 1
   netstat -tuln | grep 8888
   # Should show: 0.0.0.0:8888 (all interfaces)
   ```

3. **Try connecting from Machine 1 to itself:**
   ```bash
   # On Machine 1
   telnet 127.0.0.1 8888
   # Should connect if tracker is running
   ```

4. **Check VM networking:**
   - If IP is `10.0.2.x` → NAT mode (won't work)
   - Need to change to Bridged mode
   - Restart VM after changing



