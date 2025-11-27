# P2P Operating System Resource Sharing System

A distributed Peer-to-Peer (P2P) resource-sharing system that allows peers in a network to share CPU, memory, and disk resources. This project demonstrates distributed operating system concepts including remote execution, distributed scheduling, and resource sharing.

## Features

### Core Features
- **CPU Resource Sharing**: Remote execution of Python programs across peers
- **Memory Resource Sharing**: Distributed key-value storage
- **Disk Resource Sharing**: Remote file storage and retrieval
- **Round Robin Scheduling**: Fair task scheduling on each peer
- **Load Balancing**: Central tracker selects least-loaded peer for tasks
- **Confidentiality Support**: Tasks can be marked as confidential to execute locally only

### Enhanced Features
- **Peer Heartbeat**: Automatic peer health monitoring
- **Dead Peer Detection**: Automatic removal of inactive peers
- **Task Timeout Handling**: Prevents hanging tasks
- **Comprehensive Logging**: Detailed logging for debugging
- **CLI Client**: Easy-to-use command-line interface for testing
- **Status Monitoring**: Real-time peer and system status

### Advanced Features ⭐ NEW
- **Task Prioritization**: Assign priorities to tasks (high/medium/low)
- **Task Cancellation**: Cancel tasks before execution
- **Task History & Audit Logging**: Complete execution history with statistics
- **Resource Quotas**: CPU, memory, and storage quotas per peer
- **Result Caching**: Cache task results to avoid re-execution
- **Task Retry Mechanism**: Automatic retry on failure
- **Batch Task Execution**: Execute multiple tasks in one request
- **Distributed Memory**: Share memory values across peers
- **Enhanced Statistics**: Comprehensive monitoring and metrics
- **Custom Timeouts**: Per-task timeout configuration

### Operating System Features 🖥️ NEW
- **Multiple Scheduling Algorithms**: FCFS, SJF, Priority, Round Robin
- **Process Management**: Process trees, process groups, lifecycle management
- **Deadlock Detection**: Banker's Algorithm and cycle detection
- **Memory Management**: First Fit, Best Fit, Worst Fit, Next Fit algorithms
- **Fragmentation Tracking**: Monitor external fragmentation
- **Inter-Process Communication**: Message queues and semaphores
- **Resource Allocation**: Safe resource allocation with deadlock prevention

See [ADVANCED_FEATURES.md](ADVANCED_FEATURES.md) for advanced features and [OS_FEATURES.md](OS_FEATURES.md) for OS-related features.

## System Architecture

### Components

1. **Tracker Node** (`tracker.py`)
   - Maintains registry of all active peers
   - Tracks CPU load of each peer
   - Performs load-based peer selection
   - Handles peer registration and heartbeat

2. **Peer Node** (`peer.py`)
   - Acts as both client and server
   - Provides CPU, memory, and disk services
   - Implements Round Robin scheduler
   - Handles confidential vs non-confidential tasks

3. **Scheduler** (`scheduler.py`)
   - Round Robin task scheduling
   - Queue management
   - Load calculation

4. **Executor** (`executor.py`)
   - Safe code execution (uses exec() - no sandboxing)
   - Function invocation
   - Error handling

5. **Memory Store** (`memory.py`)
   - Thread-safe key-value storage
   - Distributed memory operations

6. **File Storage** (`storage.py`)
   - Local file storage
   - File upload/download
   - Size limits

7. **CLI Client** (`client.py`)
   - Command-line interface for testing
   - Supports all operations

## Installation

### Requirements
- Python 3.7 or higher
- No external dependencies (uses only standard library)

### Setup

1. Clone or download this repository
2. Ensure Python 3.7+ is installed
3. No additional packages needed - uses only Python standard library

## Usage

### Web UI (Recommended) 🌐

The system now includes a modern web-based user interface!

**Quick Start:**
```bash
# Terminal 1: Start tracker
python tracker.py

# Terminal 2: Start peer with web UI
python peer.py --port 9000 --web-ui
```

Then open your browser to: **http://127.0.0.1:5000**

See [WEB_UI_GUIDE.md](WEB_UI_GUIDE.md) for complete web UI documentation.

### Command Line Interface

#### Starting the Tracker

The tracker must be started first. It coordinates peer discovery and load balancing.

```bash
python tracker.py
```

Or specify custom host/port:
```bash
TRACKER_HOST=0.0.0.0 TRACKER_PORT=8888 python tracker.py
```

Default: Listens on `0.0.0.0:8888`

### Starting a Peer

Start one or more peer nodes. Each peer can act as both client and server.

```bash
python peer.py
```

Or with custom settings:
```bash
python peer.py --port 9000 --tracker-host 192.168.1.100 --tracker-port 8888
```

**For testing across multiple machines:**
- On Machine 1 (Tracker): `python tracker.py`
- On Machine 2 (Peer 1): `python peer.py --port 9000 --tracker-host <MACHINE1_IP>`
- On Machine 3 (Peer 2): `python peer.py --port 9001 --tracker-host <MACHINE1_IP>`

### Using the CLI Client

The CLI client allows you to interact with peers easily.

#### Execute CPU Task (Non-Confidential)

```bash
python client.py --host 127.0.0.1 --port 9000 cpu \
  --program "def main(x): return x * x" \
  --function main \
  --args "[5]"
```

#### Execute Confidential Task (Local Only)

```bash
python client.py --host 127.0.0.1 --port 9000 cpu \
  --program "def main(x): return x * x" \
  --function main \
  --args "[5]" \
  --confidential
```

#### Memory Operations

Set memory:
```bash
python client.py --host 127.0.0.1 --port 9000 set-mem --key "mykey" --value "myvalue"
```

Get memory:
```bash
python client.py --host 127.0.0.1 --port 9000 get-mem --key "mykey"
```

#### File Operations

Upload file:
```bash
python client.py --host 127.0.0.1 --port 9000 put-file --filename "test.txt" --filepath "/path/to/file.txt"
```

Download file:
```bash
python client.py --host 127.0.0.1 --port 9000 get-file --filename "test.txt" --save "/path/to/save.txt"
```

#### Get Peer Status

```bash
python client.py --host 127.0.0.1 --port 9000 status
```

## Example Scenarios

### Scenario 1: Remote CPU Execution

1. Start tracker: `python tracker.py`
2. Start Peer 1: `python peer.py --port 9000`
3. Start Peer 2: `python peer.py --port 9001`
4. Submit task from Peer 1 (will be executed on least-loaded peer):
   ```bash
   python client.py --host 127.0.0.1 --port 9000 cpu \
     --program "def main(n): return sum(range(1, n+1))" \
     --function main \
     --args "[100]"
   ```

### Scenario 2: Confidential Task

Execute a sensitive computation locally only:
```bash
python client.py --host 127.0.0.1 --port 9000 cpu \
  --program "def main(secret): return hash(secret)" \
  --function main \
  --args '["mysecret"]' \
  --confidential
```

### Scenario 3: Distributed Memory

1. Set value on Peer 1:
   ```bash
   python client.py --host 127.0.0.1 --port 9000 set-mem --key "shared_data" --value "42"
   ```

2. Get value from Peer 1:
   ```bash
   python client.py --host 127.0.0.1 --port 9000 get-mem --key "shared_data"
   ```

### Scenario 4: File Sharing

1. Upload file to Peer 1:
   ```bash
   python client.py --host 127.0.0.1 --port 9000 put-file --filename "document.pdf" --filepath "./document.pdf"
   ```

2. Download file from Peer 1:
   ```bash
   python client.py --host 127.0.0.1 --port 9000 get-file --filename "document.pdf" --save "./downloaded.pdf"
   ```

## Testing Across Multiple Machines

### Setup Instructions

1. **Find your machine's IP address:**
   - Linux/Mac: `ip addr show` or `ifconfig`
   - Windows: `ipconfig`

2. **Start Tracker on Machine 1:**
   ```bash
   python tracker.py
   ```
   Note the IP address (e.g., `192.168.1.100`)

3. **Start Peer on Machine 2:**
   ```bash
   python peer.py --port 9000 --tracker-host 192.168.1.100 --tracker-port 8888
   ```

4. **Start Peer on Machine 3:**
   ```bash
   python peer.py --port 9000 --tracker-host 192.168.1.100 --tracker-port 8888
   ```

5. **Test from any machine:**
   ```bash
   python client.py --host <PEER_IP> --port 9000 cpu \
     --program "def main(x): return x * 2" \
     --function main \
     --args "[10]"
   ```

### Firewall Configuration

If testing across machines, ensure:
- Tracker port (default 8888) is open
- Peer ports (default 9000+) are open
- TCP connections are allowed

## Message Protocol

All communication uses JSON messages over TCP with length-prefixed encoding.

### CPU Task Message
```json
{
  "type": "CPU_TASK",
  "task_id": "T123",
  "program": "def main(x): return x*x",
  "function": "main",
  "args": [5],
  "confidential": false
}
```

### CPU Result Message
```json
{
  "type": "CPU_RESULT",
  "task_id": "T123",
  "result": 25,
  "error": null
}
```

### Memory Operations
```json
{"type": "SET_MEM", "key": "x", "value": 42}
{"type": "GET_MEM", "key": "x"}
```

### File Operations
```json
{"type": "PUT_FILE", "filename": "a.txt", "data": "<base64>"}
{"type": "GET_FILE", "filename": "a.txt"}
```

## Configuration

Configuration can be modified in `config.py` or via environment variables:

- `TRACKER_HOST`: Tracker host (default: `0.0.0.0`)
- `TRACKER_PORT`: Tracker port (default: `8888`)
- `PEER_PORT`: Peer port (default: `9000`)
- `SOCKET_TIMEOUT`: Socket timeout in seconds (default: `30`)
- `TASK_TIMEOUT`: Task execution timeout (default: `60`)
- `HEARTBEAT_INTERVAL`: Peer heartbeat interval (default: `10`)
- `PEER_TIMEOUT`: Peer timeout for dead peer detection (default: `30`)

## Project Structure

```
termprojectos/
├── tracker.py          # Central tracker node
├── peer.py             # Peer node implementation
├── scheduler.py        # Round Robin scheduler
├── executor.py         # Code executor
├── memory.py           # Memory storage
├── storage.py          # File storage
├── messages.py         # Message protocol
├── config.py           # Configuration
├── client.py           # CLI client
├── README.md           # This file
└── peer_storage/       # File storage directory (created automatically)
```

## Limitations

**IMPORTANT**: This is an academic project for demonstration purposes.

### Security Limitations
- ⚠️ **No sandboxing**: Uses `exec()` without isolation
- ⚠️ **No encryption**: All communication is unencrypted
- ⚠️ **No authentication**: No peer authentication mechanism
- ⚠️ **No access control**: Any peer can access any resource

### Functional Limitations
- Round Robin scheduling is simulated (not preemptive)
- No distributed consensus mechanism
- No fault tolerance for tracker failure
- No replication of data
- Limited error recovery

### Academic Use Only
This system is designed for educational purposes to demonstrate:
- Distributed systems concepts
- P2P networking
- Resource sharing
- Scheduling algorithms
- Socket programming

**Do not use in production environments without proper security measures.**

## Future Enhancements

Potential improvements for a production system:
- Sandboxed code execution (Docker, VMs, or restricted Python environments)
- Encryption for all communications (TLS/SSL)
- Peer authentication and authorization
- Distributed hash table (DHT) for peer discovery
- Data replication and fault tolerance
- Consensus algorithms for distributed coordination
- Preemptive scheduling
- Resource quotas and limits
- Monitoring and metrics dashboard

## Troubleshooting

### Peer cannot connect to tracker
- Check tracker is running
- Verify IP address and port
- Check firewall settings
- Ensure both machines are on same network

### Tasks timeout
- Increase `TASK_TIMEOUT` in config.py
- Check network connectivity
- Verify peer is still running

### Files not found
- Check `peer_storage/` directory exists
- Verify filename spelling
- Check file permissions

### Port already in use
- Change port using `--port` argument
- Kill process using the port: `lsof -i :PORT` (Linux/Mac) or `netstat -ano | findstr :PORT` (Windows)

## License

This project is for academic/educational purposes only.

## Author

Term Project - Operating Systems Course

