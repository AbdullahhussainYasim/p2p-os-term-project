# Accessing Web UI from Multiple Devices

## Quick Setup

### Step 1: Find Your Machine's IP Address

Run this command to find your IP:
```bash
hostname -I
```

Or:
```bash
ip addr show | grep "inet " | grep -v 127.0.0.1
```

You'll get something like: `192.168.1.100` or `10.0.0.5`

### Step 2: Start Peer with Network Access

Instead of:
```bash
python3 peer.py --port 9000 --web-ui
```

Use:
```bash
python3 peer.py --port 9000 --web-ui --web-host 0.0.0.0
```

The `--web-host 0.0.0.0` makes it accessible from any device on your network.

### Step 3: Access from Other Devices

On your phone, tablet, or another computer (connected to the same WiFi/network):

Open browser and go to:
```
http://<YOUR_IP>:5000
```

For example, if your IP is `192.168.1.100`:
```
http://192.168.1.100:5000
```

## Complete Example

**On Your Main Computer:**

1. Find IP address:
   ```bash
   hostname -I
   # Output: 192.168.1.100
   ```

2. Start tracker:
   ```bash
   python3 tracker.py
   ```

3. Start peer with network access:
   ```bash
   python3 peer.py --port 9000 --web-ui --web-host 0.0.0.0
   ```

**On Your Phone/Tablet/Other Device:**

1. Make sure it's on the same WiFi network
2. Open browser
3. Go to: `http://192.168.1.100:5000`
4. You'll see the same dashboard!

## Firewall Configuration

If you can't access from other devices, you may need to allow the port through the firewall:

### Fedora/RHEL (firewalld):
```bash
sudo firewall-cmd --add-port=5000/tcp --permanent
sudo firewall-cmd --reload
```

### Ubuntu/Debian (ufw):
```bash
sudo ufw allow 5000/tcp
```

### Check if port is open:
```bash
sudo firewall-cmd --list-ports
```

## Security Note

⚠️ **Important**: Binding to `0.0.0.0` makes your web UI accessible to anyone on your network. This is fine for:
- Home networks
- Testing environments
- Academic projects

**Not recommended for**:
- Public WiFi
- Untrusted networks
- Production systems

## Troubleshooting

### Can't Access from Phone

1. **Check IP address**: Make sure you're using the correct IP
   ```bash
   hostname -I
   ```

2. **Check firewall**: Allow port 5000
   ```bash
   sudo firewall-cmd --add-port=5000/tcp
   ```

3. **Check network**: Make sure devices are on same WiFi
   - Phone and computer must be on same network
   - Check WiFi name matches

4. **Check peer is running**: Verify peer started with `--web-host 0.0.0.0`
   - Should see: `Starting web UI on http://0.0.0.0:5000`

### Connection Refused

- Make sure peer is running
- Check firewall settings
- Verify IP address is correct
- Try accessing from computer first: `http://localhost:5000`

### Can't Find IP Address

**Linux:**
```bash
hostname -I
ip addr show
ifconfig
```

**Alternative method:**
```bash
python3 -c "import socket; s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(('8.8.8.8', 80)); print(s.getsockname()[0])"
```

## Testing from Multiple Devices

1. **Computer**: `http://192.168.1.100:5000`
2. **Phone**: `http://192.168.1.100:5000`
3. **Tablet**: `http://192.168.1.100:5000`
4. **Friend's Laptop**: `http://192.168.1.100:5000` (if on same network)

All devices will see the same dashboard and can interact with the same peer!

## Advanced: Custom Port

If port 5000 is busy, use a different port:

```bash
python3 peer.py --port 9000 --web-ui --web-host 0.0.0.0 --web-port 8080
```

Then access: `http://<YOUR_IP>:8080`

## Summary

**To access from multiple devices:**

1. Find your IP: `hostname -I`
2. Start with: `--web-host 0.0.0.0`
3. Access from: `http://<YOUR_IP>:5000`
4. Allow firewall if needed

That's it! 🎉

