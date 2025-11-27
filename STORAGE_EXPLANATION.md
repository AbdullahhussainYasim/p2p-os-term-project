# File Storage Explanation

## Answer: Each Peer Has Its Own Storage (NOT Global)

**Short Answer**: Each peer has its own separate file storage. Files are **NOT** automatically shared or replicated across all peers.

---

## How It Works

### Storage Model: Local Per Peer

```
Peer 1                    Peer 2                    Peer 3
┌─────────────┐          ┌─────────────┐          ┌─────────────┐
│ peer_storage│          │ peer_storage│          │ peer_storage│
│ /           │          │ /           │          │ /           │
│  file1.txt  │          │  file2.txt  │          │  (empty)    │
│  file3.pdf  │          │             │          │             │
└─────────────┘          └─────────────┘          └─────────────┘
```

Each peer maintains its own `peer_storage/` directory. Files stored on one peer are **NOT** automatically available on other peers.

---

## Example Scenarios

### Scenario 1: Peer A Uploads a File

**What Happens:**
1. Peer A uploads `document.pdf`
2. File is stored in `Peer A's peer_storage/` directory
3. **Only Peer A has this file**
4. Peer B and Peer C do **NOT** have this file

**Result:**
- Peer A: Has `document.pdf` ✅
- Peer B: Does NOT have it ❌
- Peer C: Does NOT have it ❌

### Scenario 2: Peer B Downloads from Peer A

**What Happens:**
1. Peer B requests `document.pdf` from Peer A
2. Peer A sends the file to Peer B
3. Peer B receives the file data
4. **Peer B can save it locally** (but it's not automatically stored in Peer B's peer_storage)

**Result:**
- Peer A: Still has `document.pdf` ✅
- Peer B: Has a copy (if saved) ✅
- Peer C: Does NOT have it ❌

### Scenario 3: Peer B Uploads to Its Own Storage

**What Happens:**
1. Peer B uploads `document.pdf` to its own storage
2. File is stored in `Peer B's peer_storage/` directory
3. **Only Peer B has this file in its storage**

**Result:**
- Peer A: Has its own `document.pdf` ✅
- Peer B: Has its own `document.pdf` ✅
- Peer C: Does NOT have it ❌

---

## Key Points

### ✅ What IS Local (Per Peer)

1. **File Storage**: Each peer's `peer_storage/` directory
2. **Memory Store**: Each peer's key-value memory
3. **Task History**: Each peer's execution history
4. **Cache**: Each peer's result cache

### ❌ What is NOT Global

1. **Files are NOT replicated** across peers
2. **Memory is NOT shared** (unless using distributed memory API)
3. **Storage is NOT synchronized**
4. **No automatic file distribution**

---

## How to Share Files Between Peers

### Method 1: Download and Re-upload

1. **Peer A** uploads `file.txt` to its storage
2. **Peer B** downloads `file.txt` from Peer A
3. **Peer B** uploads `file.txt` to its own storage
4. Now both peers have the file

### Method 2: Direct File Transfer

Use the client to download from one peer and upload to another:

```bash
# Download from Peer A
python3 client.py --host <PEER_A_IP> --port 9000 get-file --filename "file.txt" --save "downloaded.txt"

# Upload to Peer B
python3 client.py --host <PEER_B_IP> --port 9000 put-file --filename "file.txt" --filepath "downloaded.txt"
```

### Method 3: Using Web UI

1. **Peer A**: Upload file via web UI
2. **Peer B**: Access Peer A's web UI, download the file
3. **Peer B**: Upload to its own storage via its web UI

---

## Storage Locations

Each peer stores files in:
```
/home/ahyasim/Downloads/termprojectos/peer_storage/
```

On different machines:
- **Machine 1**: `/path/to/project/peer_storage/`
- **Machine 2**: `/path/to/project/peer_storage/` (separate directory)
- **Machine 3**: `/path/to/project/peer_storage/` (separate directory)

These are **completely separate** directories on different machines.

---

## Memory Storage (Same Concept)

Memory storage works the same way:

- **Peer A** stores: `key="name"`, `value="Ahmed"`
- **Peer B** does **NOT** automatically have this
- **Peer B** has its own separate memory store

To share memory, use the distributed memory API:
```python
# Set on remote peer
peer.set_remote_memory(("192.168.1.100", 9000), "name", "Ahmed")

# Get from remote peer
value = peer.get_remote_memory(("192.168.1.100", 9000), "name")
```

---

## Why This Design?

### Advantages:
- ✅ **Privacy**: Each peer controls its own data
- ✅ **Independence**: Peers don't depend on each other
- ✅ **Simplicity**: No complex replication logic
- ✅ **Security**: Data doesn't automatically spread

### Disadvantages:
- ❌ **No automatic backup**: If peer goes down, files are lost
- ❌ **Manual sharing**: Must explicitly transfer files
- ❌ **No redundancy**: Files exist in only one place

---

## Summary

| Question | Answer |
|----------|--------|
| **Is storage global?** | ❌ No, each peer has its own storage |
| **If Peer A uploads, do all peers get it?** | ❌ No, only Peer A has it |
| **If Peer B downloads from Peer A, do others get it?** | ❌ No, only Peer B gets a copy |
| **Are files replicated?** | ❌ No, files are stored locally per peer |
| **Can peers share files?** | ✅ Yes, by downloading and re-uploading |

---

## Example: Real-World Scenario

**Setup:**
- Peer 1 (Machine 1): Uploads `report.pdf`
- Peer 2 (Machine 2): Wants the file
- Peer 3 (Machine 3): Also wants the file

**What Happens:**

1. **Peer 1** uploads `report.pdf` → Stored in Peer 1's `peer_storage/`
2. **Peer 2** downloads from Peer 1 → Gets file, can save locally
3. **Peer 2** uploads to its storage → Now Peer 2 has it in its `peer_storage/`
4. **Peer 3** downloads from Peer 1 or Peer 2 → Gets file, can save locally
5. **Peer 3** uploads to its storage → Now Peer 3 has it in its `peer_storage/`

**Final State:**
- Peer 1: Has `report.pdf` in its storage ✅
- Peer 2: Has `report.pdf` in its storage ✅
- Peer 3: Has `report.pdf` in its storage ✅

**But this required manual steps - files are NOT automatically replicated!**

---

## Technical Details

### Storage Implementation

```python
# Each peer creates its own FileStorage instance
self.file_storage = FileStorage()  # Creates local peer_storage/ directory

# Files are stored locally
file_path = self.storage_dir / filename  # Local path only
```

### File Operations

- **PUT_FILE**: Stores file in **this peer's** `peer_storage/`
- **GET_FILE**: Retrieves file from **this peer's** `peer_storage/`
- **No cross-peer storage**: Operations only affect the peer that receives them

---

## Conclusion

**Each peer has its own isolated storage.** Files uploaded to one peer are **NOT** automatically available on other peers. To share files, you must explicitly download from one peer and upload to another.

This is by design - it provides:
- Data privacy
- Peer independence  
- Simple implementation
- Explicit control over data sharing

If you need automatic replication, that would be a future enhancement (not currently implemented).




