# File Download - Quick Summary

## ✅ How to Download Files from Other Peers

### Method 1: Direct Download (Current - Works Now)

**Using Web UI:**
1. Open the peer's web UI that has the file: `http://<PEER_IP>:5000`
2. Go to **Files** tab
3. Find the file in the list
4. Click **Download**

**Using CLI:**
```bash
python3 client.py --host <PEER_IP> --port <PORT> get-file --filename "file.txt" --save "file.txt"
```

**Example:**
```bash
# Download from peer at 172.16.18.70:9000
python3 client.py --host 172.16.18.70 --port 9000 get-file --filename "report.pdf" --save "report.pdf"
```

---

### Method 2: File Discovery (New Feature - Implemented)

**Find which peer has a file:**

**Using Python API:**
```python
from peer import Peer

peer = Peer()
peers_with_file = peer.find_file_on_network("document.pdf")
# Returns: [("172.16.18.70", 9000), ("172.16.18.71", 9001)]

# Download from first peer
from client import P2PClient
client = P2PClient("172.16.18.70", 9000)
result = client.get_file("document.pdf", "downloaded.pdf")
```

**How it works:**
- When a peer uploads a file, it automatically registers with the tracker
- You can query the tracker to find which peers have a specific file
- Then download from any of those peers

---

### Method 3: Multi-Peer Download (New Feature - Implemented)

**Download from multiple peers simultaneously:**

**Using Python API:**
```python
from peer import Peer

peer = Peer()
# Automatically finds peers with file and downloads chunks in parallel
file_data = peer.download_file_from_network("large_file.zip", save_path="large_file.zip", use_multipeer=True)
```

**How it works:**
1. Queries tracker to find all peers with the file
2. Splits file into chunks (1MB each)
3. Downloads chunks in parallel from different peers
4. Reassembles chunks into complete file

**Benefits:**
- ✅ Faster downloads (parallel chunks)
- ✅ Load balancing across peers
- ✅ Redundancy (if one peer fails, others continue)

---

## Complete Workflow Example

### Scenario: Peer 1 uploaded a file, Peer 2 wants to download it

**Step 1: Peer 1 uploads file**
```bash
# Peer 1: Upload via web UI or CLI
python3 client.py --host 127.0.0.1 --port 9000 put-file --filename "report.pdf" --filepath "report.pdf"
```
- File stored in Peer 1's `peer_storage/`
- Automatically registered with tracker

**Step 2: Peer 2 finds the file**
```python
# Peer 2: Find which peers have the file
from peer import Peer
peer = Peer()
peers = peer.find_file_on_network("report.pdf")
print(peers)  # [("172.16.18.70", 9000)]
```

**Step 3: Peer 2 downloads**
```python
# Option A: Single-peer download
from client import P2PClient
client = P2PClient("172.16.18.70", 9000)
result = client.get_file("report.pdf", "downloaded.pdf")

# Option B: Multi-peer download (if file exists on multiple peers)
file_data = peer.download_file_from_network("report.pdf", save_path="report.pdf", use_multipeer=True)
```

**Step 4: Peer 2 saves to storage (optional)**
```python
# Upload to Peer 2's own storage
peer.put_file("report.pdf", file_data)
```

---

## Web UI Integration (Coming Soon)

The web UI will have:
- **Search Network** button to find files
- **Download from Network** button for multi-peer download
- Automatic file discovery

---

## Technical Details

### File Registration
When a peer uploads a file:
```python
peer.put_file("file.txt", data)
# Automatically calls: _register_file_with_tracker("file.txt")
```

### File Discovery
Query tracker for peers with file:
```python
peers = peer.find_file_on_network("file.txt")
# Sends FIND_FILE message to tracker
# Tracker returns list of peers with that file
```

### Multi-Peer Download
1. Find all peers with file
2. Split file into chunks (1MB each)
3. Download chunks in parallel
4. Reassemble chunks

---

## Current Status

| Feature | Status | Notes |
|---------|--------|-------|
| **Direct download** | ✅ Working | Download from specific peer |
| **File discovery** | ✅ Implemented | Find which peer has file |
| **Multi-peer download** | ✅ Implemented | Parallel chunk download |
| **Web UI integration** | ⏳ Pending | UI buttons for discovery |

---

## Quick Reference

### Download from specific peer:
```bash
python3 client.py --host <PEER_IP> --port <PORT> get-file --filename "file.txt" --save "file.txt"
```

### Find file on network (Python):
```python
peers = peer.find_file_on_network("file.txt")
```

### Multi-peer download (Python):
```python
file_data = peer.download_file_from_network("file.txt", save_path="file.txt", use_multipeer=True)
```

---

## Answer to Your Questions

### Q1: How can a client peer download a file that was uploaded by another peer?

**Answer:** 
1. **Direct method**: Connect to the peer that has the file and download it
   ```bash
   python3 client.py --host <PEER_IP> --port <PORT> get-file --filename "file.txt" --save "file.txt"
   ```

2. **Discovery method**: Use file discovery to find which peer has it, then download
   ```python
   peers = peer.find_file_on_network("file.txt")
   client = P2PClient(peers[0][0], peers[0][1])
   client.get_file("file.txt", "file.txt")
   ```

### Q2: Can a client peer download a file using multiple peers?

**Answer:** 
**Yes!** Multi-peer download is now implemented:
```python
# Automatically uses multiple peers if available
file_data = peer.download_file_from_network("large_file.zip", save_path="large_file.zip", use_multipeer=True)
```

**How it works:**
- Finds all peers with the file
- Splits file into chunks
- Downloads chunks in parallel from different peers
- Reassembles into complete file

**Benefits:**
- Faster downloads
- Load balancing
- Redundancy

---

## Summary

✅ **Direct download**: Works now - connect to peer and download
✅ **File discovery**: Implemented - find which peer has a file  
✅ **Multi-peer download**: Implemented - download chunks from multiple peers in parallel

All features are ready to use! 🎉



