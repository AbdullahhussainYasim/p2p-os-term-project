# Multi-Machine Setup Guide (Fixed)

## Important Notes

1. **Use double dashes (`--`) not single dash (`-`)** for all flags
2. **Use the tracker machine's actual IP**, not the broadcast address
3. **Make sure all machines are on the same WiFi network**

## Step-by-Step Setup

### Machine 1 (Tracker + Peer 1)
**IP Address: `172.16.18.70`** (from your `ip addr` output)

#### Terminal 1: Start Tracker
```bash
python3 tracker.py
```

**Expected output:**
```
Tracker listening on 0.0.0.0:8888
Waiting for peer registrations...
```

#### Terminal 2: Start Peer 1 with Web UI
```bash
python3 peer.py --port 9000 --web-ui --web-host 0.0.0.0
```

**Expected output:**
```
Starting peer on port 9000
Connecting to tracker at 127.0.0.1:8888
Starting web UI on http://0.0.0.0:5000
```

**Access Web UI:** `http://172.16.18.70:5000` (from any machine on network)

---

### Machine 2 (Peer 2)
**On the other machine (Kali Linux)**

#### Start Peer 2 with Web UI
```bash
python3 peer.py --port 9001 --tracker-host 172.16.18.70 --tracker-port 8888 --web-ui --web-host 0.0.0.0 --web-port 5001
```

**Important:**
- Use `--tracker-host` (double dash!)
- Use the tracker machine's IP: `172.16.18.70` (NOT `172.16.23.255`)
- Use different port for peer: `--port 9001` (not 9000)
- Use different web port: `--web-port 5001` (not 5000)

**Expected output:**
```
Starting peer on port 9001
Connecting to tracker at 172.16.18.70:8888
Starting web UI on http://0.0.0.0:5001
```

**Access Web UI:** `http://<machine2-ip>:5001`

---

## Correct Command Format

### ❌ WRONG (what you used):
```bash
python3 peer.py --port 9000 -tracker-host 172.16.23.255 --tracker-port 8888 --web-ui --web-host 0.0.0.0
```

**Problems:**
1. `-tracker-host` should be `--tracker-host` (double dash)
2. `172.16.23.255` is broadcast address, not tracker IP
3. Port 9000 might conflict if another peer uses it

### ✅ CORRECT:
```bash
python3 peer.py --port 9001 --tracker-host 172.16.18.70 --tracker-port 8888 --web-ui --web-host 0.0.0.0 --web-port 5001
```

---

## Finding Your IP Address

### On Machine 1 (Tracker):
```bash
ip addr | grep "inet " | grep -v "127.0.0.1"
```

Look for the IP on `wlo1` interface: `172.16.18.70`

### On Machine 2:
```bash
ip addr | grep "inet " | grep -v "127.0.0.1"
```

Note this IP for accessing the web UI.

---

## Complete Example Setup

### Machine 1 (172.16.18.70):
```bash
# Terminal 1
python3 tracker.py

# Terminal 2
python3 peer.py --port 9000 --web-ui --web-host 0.0.0.0
```

### Machine 2 (e.g., 172.16.18.71):
```bash
python3 peer.py --port 9001 --tracker-host 172.16.18.70 --tracker-port 8888 --web-ui --web-host 0.0.0.0 --web-port 5001
```

### Machine 3 (e.g., 172.16.18.72):
```bash
python3 peer.py --port 9002 --tracker-host 172.16.18.70 --tracker-port 8888 --web-ui --web-host 0.0.0.0 --web-port 5002
```

---

## Testing Connection

### On Machine 1 (Tracker):
You should see in tracker terminal:
```
Peer registered: 172.16.18.70:9000
Peer registered: <machine2-ip>:9001
Peer registered: <machine3-ip>:9002
```

### On Machine 2:
You should see:
```
Registered with tracker at 172.16.18.70:8888
```

### Test from Machine 2's Web UI:
1. Open `http://<machine2-ip>:5001`
2. Go to CPU Tasks tab
3. Execute a task
4. Check if it can use Machine 1's resources

---

## Troubleshooting

### Error: "unrecognized arguments: -tracker-host"
**Fix:** Use `--tracker-host` (double dash)

### Error: "Connection refused"
**Possible causes:**
1. Tracker not running on Machine 1
2. Wrong IP address (using broadcast instead of actual IP)
3. Firewall blocking connection

**Fix:**
```bash
# On Machine 1, check if tracker is listening
netstat -tuln | grep 8888

# On Machine 2, test connection
telnet 172.16.18.70 8888
# or
nc -zv 172.16.18.70 8888
```

### Error: "Address already in use"
**Fix:** Use different ports:
- Peer 1: `--port 9000 --web-port 5000`
- Peer 2: `--port 9001 --web-port 5001`
- Peer 3: `--port 9002 --web-port 5002`

### Can't access web UI from other machine
**Fix:**
1. Make sure you used `--web-host 0.0.0.0` (not `127.0.0.1`)
2. Check firewall:
   ```bash
   sudo ufw allow 5000/tcp
   sudo ufw allow 5001/tcp
   ```
3. Use the machine's actual IP, not `127.0.0.1`

---

## Quick Reference

### All Available Flags:
```bash
python3 peer.py \
  --port <port>                    # Peer port (default: auto)
  --tracker-host <ip>              # Tracker IP (default: 127.0.0.1)
  --tracker-port <port>            # Tracker port (default: 8888)
  --web-ui                         # Enable web UI
  --web-host <ip>                  # Web UI host (default: 127.0.0.1)
  --web-port <port>                # Web UI port (default: 5000)
```

### Example for Machine 2:
```bash
python3 peer.py \
  --port 9001 \
  --tracker-host 172.16.18.70 \
  --tracker-port 8888 \
  --web-ui \
  --web-host 0.0.0.0 \
  --web-port 5001
```

---

## Summary

1. ✅ Use `--tracker-host` (double dash)
2. ✅ Use tracker's actual IP: `172.16.18.70` (not broadcast)
3. ✅ Use different ports for each peer
4. ✅ Use `--web-host 0.0.0.0` to allow access from other machines
5. ✅ Make sure all machines are on same WiFi network

