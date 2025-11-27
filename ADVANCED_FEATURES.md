# Advanced Features Documentation

This document describes all the advanced features added to the P2P Resource Sharing System.

## 1. Task Prioritization

Tasks can now be assigned priorities. Higher priority tasks are executed before lower priority tasks.

### Usage

```python
# High priority task (priority = 10)
result = peer.submit_cpu_task(
    program="def main(x): return x*2",
    function="main",
    args=[5],
    priority=10  # High priority
)

# Low priority task (priority = -5)
result = peer.submit_cpu_task(
    program="def main(x): return x*2",
    function="main",
    args=[5],
    priority=-5  # Low priority
)
```

### CLI Usage

```bash
python client.py --host 127.0.0.1 --port 9000 cpu \
  --program "def main(x): return x*2" \
  --function main \
  --args "[5]" \
  --priority 10
```

**Default Priority**: 0 (normal priority)

## 2. Task Cancellation

Tasks can be cancelled before they start executing.

### Usage

```python
# Submit a task
task_id = "T123"
result = peer.submit_cpu_task(...)

# Cancel the task
cancelled = peer.cancel_task(task_id)
```

### CLI Usage

```bash
python client.py --host 127.0.0.1 --port 9000 cancel --task-id T123
```

**Note**: Tasks that have already started executing cannot be cancelled.

## 3. Task History and Audit Logging

All task executions are logged with timestamps, execution times, and results.

### Usage

```python
# Get task history
history = peer.get_task_history(limit=100, task_type="CPU_TASK")

# Get specific task info
task_info = peer.get_task_info("T123")
```

### CLI Usage

```bash
# Get recent history
python client.py --host 127.0.0.1 --port 9000 history --limit 50

# Get history for specific task type
python client.py --host 127.0.0.1 --port 9000 history --type CPU_TASK
```

### History Statistics

The history includes:
- Total tasks executed
- Success/failure counts
- Average execution time
- Success rate

## 4. Resource Quotas

Peers now enforce resource quotas to prevent resource exhaustion.

### Quota Types

1. **CPU Task Quota**: Maximum number of CPU tasks per time window
2. **Memory Quota**: Maximum number of memory keys
3. **Storage Quota**: Maximum storage space in MB

### Configuration

Quotas are configured in `quota.py`:
- `max_cpu_tasks`: Default 100 tasks per hour
- `max_memory_keys`: Default 1000 keys
- `max_storage_mb`: Default 100 MB

### Usage

Quotas are automatically enforced. If a quota is exceeded, the operation returns an error.

```python
# Check quota usage
status = peer.get_status()
quota_info = status["quota"]
```

## 5. Task Result Caching

Identical tasks are cached to avoid re-execution.

### How It Works

- Cache key is computed from: program code + function name + arguments
- Successful results are cached
- Cache has TTL (default: 1 hour)
- Maximum cache size: 100 entries

### Usage

```python
# First execution - runs the task
result1 = peer.submit_cpu_task(program, function, args)

# Second execution with same parameters - returns cached result
result2 = peer.submit_cpu_task(program, function, args)  # Fast!
```

### Cache Statistics

```python
status = peer.get_status()
cache_stats = status["cache"]
# Shows: size, hits, misses, hit_rate
```

## 6. Task Retry Mechanism

Tasks can automatically retry on failure.

### Usage

```python
# Task with 3 retry attempts
result = peer.submit_cpu_task(
    program="def main(x): return x/0",  # Will fail
    function="main",
    args=[5],
    max_retries=3  # Will retry 3 times
)
```

### CLI Usage

```bash
python client.py --host 127.0.0.1 --port 9000 cpu \
  --program "def main(x): return x*2" \
  --function main \
  --args "[5]" \
  --retries 3
```

## 7. Batch Task Execution

Execute multiple tasks in a single request.

### Usage

```python
tasks = [
    {
        "program": "def main(x): return x*2",
        "function": "main",
        "args": [1],
        "task_id": "T1"
    },
    {
        "program": "def main(x): return x*3",
        "function": "main",
        "args": [2],
        "task_id": "T2"
    }
]

results = peer.submit_batch_tasks(tasks)
```

### CLI Usage

Create a JSON file with tasks:

```json
{
  "tasks": [
    {
      "program": "def main(x): return x*2",
      "function": "main",
      "args": [1],
      "task_id": "T1"
    }
  ]
}
```

## 8. Distributed Memory Sharing

Share memory values across different peers.

### Usage

```python
# Set value on remote peer
peer.set_remote_memory(
    peer_address=("192.168.1.100", 9000),
    key="shared_key",
    value="shared_value"
)

# Get value from remote peer
value = peer.get_remote_memory(
    peer_address=("192.168.1.100", 9000),
    key="shared_key"
)
```

## 9. Enhanced Statistics and Monitoring

Comprehensive statistics for all system components.

### Available Statistics

- **Scheduler**: Queue size, load, completed tasks, cancelled tasks
- **Memory**: Key count, operation count
- **Storage**: File count, total size, operation count
- **Executor**: Execution count
- **Task History**: Total tasks, success rate, average execution time
- **Cache**: Size, hits, misses, hit rate
- **Quota**: Current usage vs limits

### Usage

```python
status = peer.get_status()
print(status["scheduler"])  # Scheduler stats
print(status["cache"])      # Cache stats
print(status["quota"])       # Quota usage
```

### CLI Usage

```bash
python client.py --host 127.0.0.1 --port 9000 status
```

## 10. Task Timeout

Custom timeout for individual tasks.

### Usage

```python
# Task with 30 second timeout
result = peer.submit_cpu_task(
    program="def main(): import time; time.sleep(60); return 'done'",
    function="main",
    args=[],
    timeout=30  # Will timeout after 30 seconds
)
```

### CLI Usage

```bash
python client.py --host 127.0.0.1 --port 9000 cpu \
  --program "def main(): return 'done'" \
  --function main \
  --args "[]" \
  --timeout 30
```

## Feature Comparison

| Feature | Basic System | Advanced System |
|---------|-------------|-----------------|
| CPU Execution | ✅ | ✅ |
| Memory Storage | ✅ | ✅ |
| File Storage | ✅ | ✅ |
| Load Balancing | ✅ | ✅ |
| Confidentiality | ✅ | ✅ |
| Task Priority | ❌ | ✅ |
| Task Cancellation | ❌ | ✅ |
| Task History | ❌ | ✅ |
| Resource Quotas | ❌ | ✅ |
| Result Caching | ❌ | ✅ |
| Task Retry | ❌ | ✅ |
| Batch Execution | ❌ | ✅ |
| Distributed Memory | ❌ | ✅ |
| Enhanced Stats | ❌ | ✅ |
| Custom Timeout | ❌ | ✅ |

## Performance Improvements

1. **Caching**: Reduces redundant computations
2. **Priority Scheduling**: Important tasks execute first
3. **Batch Operations**: Reduces network overhead
4. **Quota Management**: Prevents resource exhaustion
5. **History Tracking**: Enables performance analysis

## Best Practices

1. **Use Priorities Wisely**: Don't make everything high priority
2. **Enable Caching**: For repeated computations
3. **Set Appropriate Timeouts**: Prevent hanging tasks
4. **Monitor Quotas**: Check usage regularly
5. **Use Batch Operations**: For multiple related tasks
6. **Review History**: Analyze task performance

## Example: Complete Workflow

```python
from peer import Peer

# Initialize peer
peer = Peer(peer_port=9000)
peer.start()

# Submit high-priority task with retries
result = peer.submit_cpu_task(
    program="def main(x): return x*x",
    function="main",
    args=[5],
    priority=10,
    max_retries=3,
    timeout=60
)

# Check task history
history = peer.get_task_history(limit=10)

# Get comprehensive status
status = peer.get_status()
print(f"Cache hit rate: {status['cache']['hit_rate']}")
print(f"Quota usage: {status['quota']}")

# Cancel a task if needed
peer.cancel_task("T123")

# Batch execute multiple tasks
tasks = [
    {"program": "def main(x): return x*2", "function": "main", "args": [i]}
    for i in range(10)
]
results = peer.submit_batch_tasks(tasks)
```

## Configuration

Advanced features can be configured in:
- `config.py`: Timeouts, intervals
- `quota.py`: Resource limits
- `cache.py`: Cache size and TTL
- `task_history.py`: History size limit

## Troubleshooting

### Task Not Cancelling
- Task may have already started executing
- Check task status in history

### Quota Exceeded
- Check current usage: `status["quota"]`
- Wait for quota window to reset
- Adjust quota limits in `quota.py`

### Cache Not Working
- Verify task parameters are identical
- Check cache statistics for hit rate
- Cache may have expired (check TTL)

### History Not Showing
- Check history limit
- Verify task completed (check status)
- History may have been cleared






