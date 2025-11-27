# Quick Fix: Multi-Machine Connection

## Your Error

You used:
```bash
python3 peer.py --port 9000 -tracker-host 172.16.23.255 --tracker-port 8888 --web-ui --web-host 0.0.0.0
```

**Problems:**
1. ❌ `-tracker-host` → Should be `--tracker-host` (double dash!)
2. ❌ `172.16.23.255` → This is broadcast address, not tracker IP!

## Correct Command

### Machine 1 (Tracker - IP: 172.16.18.70)

**Terminal 1:**
```bash
python3 tracker.py
```

**Terminal 2:**
```bash
python3 peer.py --port 9000 --web-ui --web-host 0.0.0.0
```

### Machine 2 (Other Machine - Kali Linux)

**Correct command:**
```bash
python3 peer.py --port 9001 --tracker-host 172.16.18.70 --tracker-port 8888 --web-ui --web-host 0.0.0.0 --web-port 5001
```

**Key changes:**
- ✅ `--tracker-host` (double dash, not `-tracker-host`)
- ✅ `172.16.18.70` (actual tracker IP, not broadcast `172.16.23.255`)
- ✅ `--port 9001` (different port to avoid conflicts)
- ✅ `--web-port 5001` (different web port)

## All Available Flags

```bash
python3 peer.py \
  --port <port>                    # Peer port
  --tracker-host <ip>              # Tracker IP (use 172.16.18.70)
  --tracker-port <port>            # Tracker port (default: 8888)
  --web-ui                         # Enable web UI
  --web-host <ip>                  # Web UI host (use 0.0.0.0)
  --web-port <port>                # Web UI port
```

## Testing

### On Machine 1 (Tracker terminal):
You should see:
```
Peer registered: 172.16.18.70:9000
Peer registered: <machine2-ip>:9001
```

### On Machine 2:
You should see:
```
Starting peer on port 9001
Connecting to tracker at 172.16.18.70:8888
Registered with tracker at 172.16.18.70:8888
Starting web UI on http://0.0.0.0:5001
```

## Access Web UIs

- **Machine 1:** `http://172.16.18.70:5000`
- **Machine 2:** `http://<machine2-ip>:5001`

## Still Not Working?

1. **Check tracker is running** on Machine 1
2. **Test connection:**
   ```bash
   # From Machine 2
   ping 172.16.18.70
   telnet 172.16.18.70 8888
   ```
3. **Check firewall** (if needed):
   ```bash
   sudo ufw allow 8888/tcp
   sudo ufw allow 5001/tcp
   ```



