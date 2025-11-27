# Operating System Features Documentation

This document describes all the advanced OS-related features added to the P2P system.

## 1. Multiple Scheduling Algorithms

The system now supports multiple CPU scheduling algorithms beyond Round Robin.

### Supported Algorithms

- **FCFS (First Come First Served)**: Processes executed in arrival order
- **SJF (Shortest Job First)**: Shortest tasks executed first
- **Priority**: Higher priority tasks executed first
- **Round Robin**: Time-sliced execution (original)
- **Multilevel Queue**: Multiple priority queues

### Usage

```python
# Change scheduler algorithm
peer._handle_set_scheduler({
    "algorithm": "SJF"  # or "FCFS", "PRIORITY", "RR"
})
```

### Statistics

Each algorithm tracks:
- Average waiting time
- Average turnaround time
- Throughput (processes/second)
- Queue size

## 2. Process Management

Complete process lifecycle management with process trees and groups.

### Features

- **Process Creation**: Create processes with parent-child relationships
- **Process Tree**: View hierarchical process structure
- **Process Groups**: Group related processes together
- **Process Termination**: Terminate processes and their children
- **Process States**: NEW, READY, RUNNING, WAITING, TERMINATED, ZOMBIE

### Usage

```python
# Create a process
pid = peer.process_manager.create_process(
    task_data={"program": "...", "function": "main", "args": [1]},
    parent_pid=None,  # Root process
    group_id="group1"
)

# Create child process
child_pid = peer.process_manager.create_process(
    task_data={...},
    parent_pid=pid,
    group_id="group1"
)

# Get process tree
tree = peer.process_manager.get_process_tree()

# Terminate process (and all children)
peer.process_manager.terminate_process(pid)
```

### Process Tree Example

```
P1 (root)
├── P2 (child)
│   ├── P3 (grandchild)
│   └── P4 (grandchild)
└── P5 (child)
```

## 3. Deadlock Detection

Implements Banker's Algorithm for deadlock avoidance and cycle detection for deadlock detection.

### Banker's Algorithm

Prevents deadlocks by ensuring system always remains in a safe state.

### Features

- **Resource Registration**: Register system resources (CPU, Memory, Disk)
- **Safe State Checking**: Verify system safety before allocation
- **Deadlock Detection**: Detect deadlocks using wait-for graph
- **Resource Allocation**: Allocate resources safely

### Usage

```python
# Register resources
peer.deadlock_detector.register_resource("CPU", ResourceType.CPU, 4)
peer.deadlock_detector.register_resource("MEMORY", ResourceType.MEMORY, 1000)

# Register process with max needs
peer.deadlock_detector.register_process("P1", {
    "CPU": 2,
    "MEMORY": 500
})

# Request resource (Banker's Algorithm)
safe, error = peer.deadlock_detector.request_resource("P1", "CPU", 1)
if safe:
    print("Resource allocated safely")
else:
    print(f"Allocation denied: {error}")

# Detect deadlock
deadlock, processes = peer.deadlock_detector.detect_deadlock()
if deadlock:
    print(f"Deadlock detected! Processes: {processes}")
```

### Resource Allocation Graph

The system builds a wait-for graph to detect cycles:
- Process A waits for Resource X held by Process B
- Process B waits for Resource Y held by Process A
- Cycle detected = Deadlock!

## 4. Memory Management

Advanced memory allocation with multiple algorithms and fragmentation tracking.

### Allocation Algorithms

- **First Fit**: Allocate first block that fits
- **Best Fit**: Allocate smallest block that fits
- **Worst Fit**: Allocate largest block that fits
- **Next Fit**: Similar to first fit, but starts from last allocation

### Features

- **Dynamic Allocation**: Allocate/deallocate memory for processes
- **Fragmentation Tracking**: Monitor external fragmentation
- **Coalescing**: Merge adjacent free blocks
- **Statistics**: Track allocation patterns

### Usage

```python
# Allocate memory
success, address = peer.memory_manager.allocate("P1", 1024)  # 1KB
if success:
    print(f"Memory allocated at address: {address}")

# Deallocate memory
peer.memory_manager.deallocate("P1")

# Check fragmentation
frag = peer.memory_manager.get_fragmentation()
print(f"External fragmentation: {frag['fragmentation_percentage']}%")
```

### Fragmentation Metrics

- **External Fragmentation**: Percentage of free memory that cannot be used
- **Largest Free Block**: Size of largest contiguous free block
- **Free Blocks Count**: Number of free memory blocks

## 5. Inter-Process Communication (IPC)

Message queues and semaphores for process synchronization.

### Message Queues

FIFO message passing between processes.

```python
# Create message queue
peer.ipc_manager.create_message_queue("queue1", max_size=100)

# Send message
queue = peer.ipc_manager.get_message_queue("queue1")
message = Message(
    sender="P1",
    receiver="P2",  # or "*" for broadcast
    message_type="DATA",
    data={"key": "value"}
)
queue.send(message)

# Receive message
message = queue.receive("P2", timeout=5.0)
if message:
    print(f"Received: {message.data}")
```

### Semaphores

Classic synchronization primitive for mutual exclusion.

```python
# Create semaphore
peer.ipc_manager.create_semaphore("mutex", initial_value=1)

# Wait (P operation)
sem = peer.ipc_manager.get_semaphore("mutex")
sem.wait("P1")  # Decrements, blocks if value is 0

# Signal (V operation)
sem.signal("P1")  # Increments, wakes waiting process
```

### Semaphore Use Cases

1. **Mutual Exclusion**: Binary semaphore (value=1)
2. **Resource Counting**: Counting semaphore (value=N)
3. **Synchronization**: Coordinate process execution

## 6. Complete OS Feature Integration

All features work together:

```python
# 1. Create process
pid = peer.process_manager.create_process(task_data, group_id="group1")

# 2. Allocate memory
peer.memory_manager.allocate(pid, 1024)

# 3. Request resources
peer.deadlock_detector.register_process(pid, {"CPU": 1, "MEMORY": 512})
peer.deadlock_detector.request_resource(pid, "CPU", 1)

# 4. Use IPC
peer.ipc_manager.create_message_queue("queue1")
peer.ipc_manager.create_semaphore("mutex", 1)

# 5. Check for deadlocks
deadlock, processes = peer.deadlock_detector.detect_deadlock()

# 6. Get comprehensive status
status = peer.get_status()
```

## Statistics and Monitoring

All OS features provide detailed statistics:

```python
status = peer.get_status()

# Process statistics
print(status["process_manager"])
# Shows: total_processes, process_groups, processes_by_state

# Deadlock detector status
print(status["deadlock_detector"])
# Shows: resource allocation, safe state, process needs

# Memory manager statistics
print(status["memory_manager"])
# Shows: fragmentation, allocations, algorithm used

# IPC statistics
print(status["ipc"])
# Shows: message queues, semaphores, queue sizes
```

## Real-World OS Concepts Demonstrated

1. **Process Scheduling**: Multiple algorithms with performance metrics
2. **Process Hierarchy**: Parent-child relationships, process trees
3. **Resource Management**: Deadlock prevention and detection
4. **Memory Management**: Allocation algorithms, fragmentation
5. **Synchronization**: Semaphores for mutual exclusion
6. **Inter-Process Communication**: Message passing

## Example: Producer-Consumer Problem

```python
# Create semaphore for buffer
peer.ipc_manager.create_semaphore("empty", initial_value=10)  # Buffer size
peer.ipc_manager.create_semaphore("full", initial_value=0)
peer.ipc_manager.create_semaphore("mutex", initial_value=1)

# Producer process
def producer():
    for i in range(10):
        peer.ipc_manager.get_semaphore("empty").wait("producer")
        peer.ipc_manager.get_semaphore("mutex").wait("producer")
        # Produce item
        peer.ipc_manager.get_semaphore("mutex").signal("producer")
        peer.ipc_manager.get_semaphore("full").signal("producer")

# Consumer process
def consumer():
    for i in range(10):
        peer.ipc_manager.get_semaphore("full").wait("consumer")
        peer.ipc_manager.get_semaphore("mutex").wait("consumer")
        # Consume item
        peer.ipc_manager.get_semaphore("mutex").signal("consumer")
        peer.ipc_manager.get_semaphore("empty").signal("consumer")
```

## Performance Considerations

- **Scheduling**: SJF minimizes average waiting time
- **Memory**: Best Fit reduces fragmentation
- **Deadlock**: Banker's Algorithm prevents deadlocks but may deny valid requests
- **IPC**: Message queues are thread-safe and efficient

## Academic Value

These features demonstrate:
- ✅ Process scheduling algorithms
- ✅ Process management and hierarchy
- ✅ Deadlock detection and prevention
- ✅ Memory allocation strategies
- ✅ Inter-process communication
- ✅ Resource management
- ✅ System synchronization

Perfect for operating systems coursework and understanding real OS internals!






