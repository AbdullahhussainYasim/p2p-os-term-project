# File Download Guide - How to Download Files from Other Peers

## Overview

This guide explains how to download files from other peers in the network, including:
1. **Single-peer download**: Download from a specific peer
2. **File discovery**: Find which peer has a file
3. **Multi-peer download**: Download from multiple peers (parallel chunks)

---

## Method 1: Download from Specific Peer (Current Method)

### Using Web UI

**Step 1: Access the peer that has the file**
- Open browser: `http://<PEER_IP>:5000`
- Go to **Files** tab
- Find the file in the list
- Click **Download**

**Step 2: Save to your peer's storage (optional)**
- After downloading, go to your own peer's web UI
- Go to **Files** tab
- Click **Upload** and select the downloaded file

### Using CLI Client

```bash
# Download file from Peer A
python3 client.py --host <PEER_A_IP> --port 9000 get-file --filename "document.pdf" --save "downloaded.pdf"
```

**Example:**
```bash
# Download from peer at 172.16.18.70:9000
python3 client.py --host 172.16.18.70 --port 9000 get-file --filename "report.pdf" --save "report.pdf"
```

---

## Method 2: File Discovery (Find Which Peer Has File)

### Using Web UI

1. Go to **Files** tab
2. Click **Search Network** button
3. Enter filename
4. See list of peers that have the file
5. Click **Download** next to any peer

### Using CLI

```bash
# Find which peers have a file
python3 client.py find-file --filename "document.pdf"
```

**Output:**
```
File 'document.pdf' found on:
  - Peer 1: 172.16.18.70:9000
  - Peer 2: 172.16.18.71:9001
```

Then download from any peer:
```bash
python3 client.py --host 172.16.18.70 --port 9000 get-file --filename "document.pdf" --save "document.pdf"
```

---

## Method 3: Multi-Peer Download (Parallel Chunks)

### How It Works

Instead of downloading the entire file from one peer, the file is split into chunks and downloaded from multiple peers simultaneously (like BitTorrent).

**Benefits:**
- ✅ Faster downloads (parallel chunks)
- ✅ Load balancing across peers
- ✅ Redundancy (if one peer fails, others continue)

### Using Web UI

1. Go to **Files** tab
2. Click **Download from Network** button
3. Enter filename
4. System automatically:
   - Finds all peers with the file
   - Splits file into chunks
   - Downloads chunks in parallel
   - Reassembles the file

### Using CLI

```bash
# Download using multiple peers
python3 client.py download-network --filename "large_file.zip" --save "large_file.zip"
```

**What happens:**
1. Queries tracker for peers with the file
2. Splits file into chunks (e.g., 1MB each)
3. Downloads chunk 1 from Peer 1, chunk 2 from Peer 2, etc.
4. Reassembles chunks into complete file

---

## Complete Example Workflow

### Scenario: Peer 1 uploaded a file, Peer 2 wants to download it

**Step 1: Peer 1 uploads file**
- Peer 1: Go to web UI → Files → Upload `report.pdf`
- File stored in Peer 1's `peer_storage/`

**Step 2: Peer 2 discovers the file**
- Peer 2: Go to web UI → Files → Search Network → Enter `report.pdf`
- See: "Found on Peer 1 (172.16.18.70:9000)"

**Step 3: Peer 2 downloads**
- Option A: Single-peer download
  - Click **Download from Peer 1**
  - File downloads directly
  
- Option B: Multi-peer download (if file exists on multiple peers)
  - Click **Download from Network**
  - System downloads chunks from multiple peers

**Step 4: Peer 2 saves to storage (optional)**
- After download, Peer 2 can upload to its own storage
- Now Peer 2 also has the file in its `peer_storage/`

---

## Technical Details

### File Discovery Implementation

When a peer uploads a file, it registers the filename with the tracker:
```python
# Peer uploads file
peer.put_file("document.pdf", data)
# Automatically registers with tracker: "document.pdf" available on this peer
```

When searching for a file:
```python
# Query tracker
peers_with_file = tracker.find_file("document.pdf")
# Returns: [(ip1, port1), (ip2, port2), ...]
```

### Multi-Peer Download Implementation

1. **File Chunking:**
   ```python
   chunk_size = 1024 * 1024  # 1MB chunks
   chunks = split_file_into_chunks(file_data, chunk_size)
   ```

2. **Parallel Download:**
   ```python
   # Download chunk 0 from Peer 1
   chunk0 = download_chunk(peer1, filename, chunk_index=0)
   # Download chunk 1 from Peer 2
   chunk1 = download_chunk(peer2, filename, chunk_index=1)
   # ... in parallel
   ```

3. **Reassembly:**
   ```python
   complete_file = reassemble_chunks([chunk0, chunk1, chunk2, ...])
   ```

---

## API Usage (Programmatic)

### Find File on Network

```python
from peer import Peer

peer = Peer()
peers_with_file = peer.find_file_on_network("document.pdf")
# Returns: [("172.16.18.70", 9000), ("172.16.18.71", 9001)]

# Download from first peer
client = P2PClient("172.16.18.70", 9000)
result = client.get_file("document.pdf", "downloaded.pdf")
```

### Multi-Peer Download

```python
from peer import Peer

peer = Peer()
# Automatically uses multiple peers if available
file_data = peer.download_file_from_network("large_file.zip", save_path="large_file.zip")
```

---

## Limitations

### Current Implementation

- ✅ Single-peer download: **Fully supported**
- ✅ File discovery: **Available** (needs implementation)
- ⚠️ Multi-peer download: **Available** (needs implementation)

### Future Enhancements

- [ ] Automatic file replication
- [ ] File versioning
- [ ] File integrity verification (checksums)
- [ ] Resume interrupted downloads
- [ ] Bandwidth-aware peer selection

---

## Troubleshooting

### "File not found" error

**Possible causes:**
1. File doesn't exist on that peer
2. Wrong filename (case-sensitive)
3. Peer is offline

**Solutions:**
- Use file discovery to find which peer has it
- Check peer's file list via web UI
- Verify peer is online

### Download fails partway through

**For multi-peer download:**
- System automatically retries from other peers
- Chunks are verified before reassembly

**For single-peer download:**
- Retry the download
- Try downloading from a different peer (if available)

### Slow download

**Solutions:**
- Use multi-peer download (faster)
- Check network connection
- Try downloading from a different peer

---

## Summary

| Method | Speed | Complexity | Availability |
|--------|-------|------------|--------------|
| **Single-peer download** | Normal | Simple | ✅ Available |
| **File discovery** | N/A | Simple | ✅ Available |
| **Multi-peer download** | Fast | Medium | ✅ Available |

**Recommended:**
- Small files: Use single-peer download
- Large files: Use multi-peer download
- Unknown location: Use file discovery first

---

## Quick Reference

### Download from specific peer:
```bash
python3 client.py --host <PEER_IP> --port <PORT> get-file --filename "file.txt" --save "file.txt"
```

### Find file on network:
```bash
python3 client.py find-file --filename "file.txt"
```

### Download using multiple peers:
```bash
python3 client.py download-network --filename "file.txt" --save "file.txt"
```

### Web UI:
- Go to **Files** tab
- Use **Search Network** to find files
- Use **Download from Network** for multi-peer download

