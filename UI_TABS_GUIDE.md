# Web UI Tabs Guide - What Each Tab Does

## 📊 Dashboard Tab

**Purpose**: View real-time system statistics and overall health

**What you'll see:**
- **Total Tasks**: Number of tasks submitted to this peer
- **Completed**: Number of tasks that finished successfully
- **Queue Size**: Number of tasks waiting to be executed
- **CPU Load**: Current CPU usage percentage (0-100%)
- **Memory Keys**: Number of key-value pairs stored
- **Files Stored**: Number of files uploaded to this peer

**Recent Activity**: Shows task execution statistics (total, successful, failed, success rate)

**System Information**: Shows scheduler type, algorithm, cache performance, etc.

**When to use**: Check overall system status and performance

---

## 💻 CPU Tasks Tab

**Purpose**: Execute Python programs on this peer or remote peers

**What you can do:**
1. **Write Python Code**: Enter your program in the text area
   ```python
   def main(x):
       return x * x
   ```

2. **Set Function Name**: Usually `main`

3. **Set Arguments**: JSON array like `[5]` or `["hello", 10]`

4. **Set Priority**: Higher number = executed first (default: 0)

5. **Set Retries**: How many times to retry if it fails (default: 0)

6. **Confidential Checkbox**: 
   - ✅ Checked = Runs locally only (doesn't go to other peers)
   - ❌ Unchecked = Can be sent to remote peers for execution

7. **Click "Execute Task"**: Your code runs and result appears below

**Task History**: See all previously executed tasks with results

**When to use**: 
- Run computations
- Test algorithms
- Process data
- Execute any Python code

**Example**: Calculate factorial, process lists, perform calculations

---

## 🧠 Memory Tab

**Purpose**: Store and retrieve key-value data (like a simple database)

**What you can do:**

1. **Set Memory Value**:
   - Enter a **Key** (e.g., "user_name")
   - Enter a **Value** (e.g., "Ahmed")
   - Click **Set**
   - Data is stored on this peer

2. **Get Memory Value**:
   - Enter a **Key** (e.g., "user_name")
   - Click **Get**
   - See the stored value

3. **View All Keys**: Click **Refresh** to see all stored keys

**When to use**:
- Store configuration
- Save temporary data
- Share data between tasks
- Simple key-value storage

**Example**: 
- Store: Key="temperature", Value="25"
- Get: Key="temperature" → Returns "25"

---

## 📁 Files Tab

**Purpose**: Upload and download files to/from this peer's storage

**What you can do:**

1. **Upload File**:
   - Click **Choose File**
   - Select a file from your computer
   - Click **Upload**
   - File is stored on this peer

2. **Download File**:
   - See list of stored files
   - Click **Download** next to any file
   - File downloads to your computer

**When to use**:
- Share documents
- Store data files
- Upload configuration files
- Download results

**Example**: Upload a CSV file, process it, download results

---

## 🌳 Processes Tab

**Purpose**: View process tree and manage processes (OS concept)

**What you'll see:**

1. **Process Tree**: 
   - Shows parent-child relationships
   - Visual hierarchy of processes
   - Process states (NEW, RUNNING, TERMINATED, etc.)

2. **Process Statistics**:
   - Total number of processes
   - Number of root processes
   - Process groups

**When to use**:
- Understand process hierarchy
- Monitor process creation
- See how tasks create processes
- Learn OS process management

**Note**: Processes are created when tasks execute. If you haven't run any tasks, you'll see "No processes running."

---

## ⚙️ OS Features Tab

**Purpose**: Advanced Operating System features and controls

**What you can do:**

1. **Change Scheduling Algorithm**:
   - Select from dropdown:
     - **FCFS** (First Come First Served) - Simple, fair
     - **SJF** (Shortest Job First) - Fastest tasks first
     - **Priority** - High priority tasks first
     - **Round Robin** - Time-sliced execution
   - Click **Change Algorithm**
   - System switches to new scheduler

2. **Check for Deadlocks**:
   - Click **Check for Deadlocks**
   - System checks if any processes are deadlocked
   - Shows result: Safe or Deadlock detected

3. **Memory Management**:
   - View memory allocation information
   - See fragmentation statistics
   - Monitor memory usage

4. **Resource Allocation**:
   - View resource allocation status
   - See which processes hold which resources
   - Check system safety

**When to use**:
- Experiment with different schedulers
- Learn OS concepts
- Monitor system resources
- Detect potential deadlocks

**Note**: These are advanced OS features for learning and demonstration.

---

## Quick Reference

| Tab | Purpose | Main Use Case |
|-----|---------|---------------|
| **Dashboard** | System overview | Check status, view metrics |
| **CPU Tasks** | Execute code | Run Python programs |
| **Memory** | Store data | Key-value storage |
| **Files** | File management | Upload/download files |
| **Processes** | Process tree | View process hierarchy |
| **OS Features** | OS controls | Change scheduler, check deadlocks |

---

## Common Workflows

### Workflow 1: Execute a Simple Task
1. Go to **CPU Tasks** tab
2. Enter code: `def main(x): return x * x`
3. Function: `main`
4. Args: `[5]`
5. Click **Execute Task**
6. See result: `25`

### Workflow 2: Store and Retrieve Data
1. Go to **Memory** tab
2. Set: Key="name", Value="Ahmed"
3. Click **Set**
4. Get: Key="name"
5. See: Value="Ahmed"

### Workflow 3: Upload and Process File
1. Go to **Files** tab
2. Upload a file
3. Go to **CPU Tasks** tab
4. Write code to process the file
5. Execute task
6. Download results

### Workflow 4: Monitor System
1. Go to **Dashboard** tab
2. Watch real-time statistics
3. Execute some tasks
4. See metrics update automatically

---

## Tips

1. **Dashboard updates every 2 seconds** - No need to refresh
2. **Empty sections are normal** - They populate as you use the system
3. **Check browser console** (F12) if something doesn't work
4. **Start with CPU Tasks** - Easiest way to test the system
5. **Use Memory tab** - Great for storing temporary data
6. **Try different schedulers** - See how they affect performance

---

## Troubleshooting

**Dashboard shows "-" for all values?**
- Make sure peer is running
- Check browser console for errors
- Verify peer is connected to tracker

**No data in tabs?**
- This is normal if you haven't used that feature yet
- Execute some tasks to see data
- Upload files to see them in Files tab

**Can't execute tasks?**
- Check peer is running
- Verify tracker is running
- Check browser console for error messages

---

Now you know what each tab does! Start with **CPU Tasks** to see the system in action! 🚀

