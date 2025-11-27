# Web UI Guide

## Overview

The P2P Resource Sharing System now includes a modern web-based user interface! Instead of using the command-line interface, you can interact with the system through a beautiful web dashboard.

## Installation

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install Flask==3.0.0
```

### Step 2: Start the System

#### Start Tracker (Terminal 1)
```bash
python tracker.py
```

#### Start Peer with Web UI (Terminal 2)
```bash
python peer.py --port 9000 --web-ui
```

The web UI will be available at: **http://127.0.0.1:5000**

### Step 3: Open in Browser

Open your web browser and navigate to:
```
http://127.0.0.1:5000
```

## Features

### Dashboard Tab
- **Real-time Statistics**: View system metrics at a glance
- **Activity Monitor**: See recent task executions
- **System Information**: Complete system status
- **Auto-refresh**: Updates every 2 seconds

### CPU Tasks Tab
- **Execute Tasks**: Run Python programs with a code editor
- **Task Configuration**: Set priority, retries, confidentiality
- **Task History**: View execution history with results
- **Real-time Results**: See task results immediately

### Memory Tab
- **Set Memory**: Store key-value pairs
- **Get Memory**: Retrieve stored values
- **View All Keys**: See all stored memory keys
- **Quick Access**: Easy memory management

### Files Tab
- **Upload Files**: Drag and drop or select files
- **Download Files**: Download stored files
- **File List**: View all stored files
- **File Management**: Easy file operations

### Processes Tab
- **Process Tree**: Visual process hierarchy
- **Process Statistics**: View process information
- **Process Management**: Monitor all processes

### OS Features Tab
- **Scheduling Algorithms**: Change scheduler (FCFS, SJF, Priority, RR)
- **Deadlock Detection**: Check for deadlocks
- **Memory Management**: View fragmentation and allocation
- **Resource Allocation**: Monitor resource usage

## Usage Examples

### Execute a CPU Task

1. Go to **CPU Tasks** tab
2. Enter Python code:
   ```python
   def main(x):
       return x * x
   ```
3. Set function name: `main`
4. Set arguments: `[5]`
5. Click **Execute Task**
6. View result in the history section

### Store Memory

1. Go to **Memory** tab
2. Enter key: `user_id`
3. Enter value: `12345`
4. Click **Set**
5. View in "All Memory Keys" section

### Upload File

1. Go to **Files** tab
2. Click **Choose File**
3. Select a file
4. Click **Upload**
5. File appears in stored files list

### Change Scheduler

1. Go to **OS Features** tab
2. Select algorithm from dropdown (FCFS, SJF, Priority, RR)
3. Click **Change Algorithm**
4. System switches to new scheduler

### Check for Deadlocks

1. Go to **OS Features** tab
2. Click **Check for Deadlocks**
3. View result (safe or deadlock detected)

## Customization

### Change Web UI Port

```bash
python peer.py --port 9000 --web-ui --web-port 8080
```

### Change Web UI Host

```bash
python peer.py --port 9000 --web-ui --web-host 0.0.0.0
```

This allows access from other machines on the network.

### Access from Another Machine

1. Start peer with `--web-host 0.0.0.0`
2. Find your machine's IP address
3. Access from another machine: `http://<YOUR_IP>:5000`

## Features Overview

### Real-time Updates
- Dashboard auto-refreshes every 2 seconds
- Task history updates automatically
- Status indicators show connection state

### Modern Design
- Beautiful gradient UI
- Responsive design (works on mobile)
- Font Awesome icons
- Smooth animations

### User-Friendly
- Intuitive tab navigation
- Clear form inputs
- Toast notifications for feedback
- Error handling with messages

## Troubleshooting

### Web UI Not Starting

**Error**: `ModuleNotFoundError: No module named 'flask'`

**Solution**: Install Flask
```bash
pip install Flask
```

### Cannot Access Web UI

**Check**:
1. Is peer running with `--web-ui` flag?
2. Is port 5000 available?
3. Check firewall settings

### Port Already in Use

**Solution**: Use different port
```bash
python peer.py --web-ui --web-port 8080
```

## Comparison: CLI vs Web UI

| Feature | CLI | Web UI |
|--------|-----|--------|
| Ease of Use | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| Visual Feedback | ⭐ | ⭐⭐⭐⭐⭐ |
| Real-time Updates | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| File Management | ⭐⭐ | ⭐⭐⭐⭐ |
| Process Visualization | ❌ | ⭐⭐⭐⭐⭐ |
| Mobile Access | ❌ | ⭐⭐⭐ |

## Tips

1. **Keep Dashboard Open**: Monitor system in real-time
2. **Use Multiple Tabs**: Open different peers in different browser tabs
3. **Check History**: Review task execution history
4. **Monitor Deadlocks**: Regularly check for deadlocks
5. **Experiment**: Try different scheduling algorithms

## Screenshots Description

The web UI includes:
- **Colorful Dashboard**: Gradient backgrounds, modern cards
- **Tab Navigation**: Easy switching between features
- **Real-time Stats**: Live system metrics
- **Code Editor**: Syntax-friendly textarea for Python code
- **File Upload**: Drag-and-drop interface
- **Process Tree**: Visual hierarchy display
- **Toast Notifications**: Success/error messages

## Next Steps

1. Start the system with `--web-ui`
2. Open browser to `http://127.0.0.1:5000`
3. Explore all tabs
4. Execute tasks
5. Monitor system status
6. Experiment with OS features

Enjoy the modern web interface! 🎉




