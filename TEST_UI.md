# Testing the Web UI - Step by Step

## Quick Test Checklist

### ✅ Step 1: Start System

**Terminal 1:**
```bash
python3 tracker.py
```

**Terminal 2:**
```bash
python3 peer.py --port 9000 --web-ui
```

**Expected Output:**
```
Starting peer on port 9000
Connecting to tracker at 127.0.0.1:8888
Starting web UI on http://127.0.0.1:5000
Peer instance set: True
```

### ✅ Step 2: Open Browser

Go to: `http://127.0.0.1:5000`

**What you should see:**
- Purple gradient header
- Navigation tabs
- Dashboard with 6 stat cards
- Connection status should show "Connected"

### ✅ Step 3: Test Dashboard

**Check:**
- [ ] Peer info shows (e.g., "Peer: 192.168.0.112:9000")
- [ ] Status shows "Connected" (green dot)
- [ ] Stat cards show numbers (not just "-")
- [ ] Recent Activity section has content
- [ ] System Information shows JSON data

**If you see "-" everywhere:**
1. Open browser console (F12)
2. Check for errors
3. Look at Network tab - is `/api/status` returning data?

### ✅ Step 4: Test CPU Tasks

1. Click **CPU Tasks** tab
2. Enter this code:
   ```python
   def main(x):
       return x * x
   ```
3. Function: `main`
4. Args: `[5]`
5. Click **Execute Task**

**Expected:**
- Toast notification: "Task executed successfully! Result: 25"
- Task appears in history below
- Dashboard updates (total tasks increases)

**If it doesn't work:**
- Check browser console for errors
- Check peer terminal for errors
- Verify tracker is running

### ✅ Step 5: Test Memory

1. Click **Memory** tab
2. Set Memory:
   - Key: `test`
   - Value: `hello`
   - Click **Set**
3. Get Memory:
   - Key: `test`
   - Click **Get**
4. Click **Refresh** to see all keys

**Expected:**
- Toast: "Memory set successfully!"
- Get shows: `Key: test\nValue: "hello"`
- Refresh shows badge with "test"

### ✅ Step 6: Test Files

1. Click **Files** tab
2. Click **Choose File**
3. Select any file
4. Click **Upload**
5. Click **Refresh**

**Expected:**
- Toast: "File uploaded successfully!"
- File appears in list
- Can download or delete

### ✅ Step 7: Test OS Features

1. Click **OS Features** tab
2. Change Scheduler:
   - Select "SJF" from dropdown
   - Click **Change Algorithm**
3. Check Deadlock:
   - Click **Check for Deadlocks**
4. Memory Info:
   - Click **Refresh Memory Info**
5. Resource Info:
   - Click **Refresh Resource Info**

**Expected:**
- Scheduler changes successfully
- Deadlock check shows result
- Memory info displays JSON
- Resource info displays JSON

## Debug Mode

**Press Ctrl+D in browser** to open debug panel.

Shows:
- API endpoint status
- Connection information
- Error details

## Common Issues and Fixes

### Issue: All values show "-"

**Cause**: API not returning data or wrong format

**Fix**:
1. Check browser console (F12)
2. Check Network tab - look at `/api/status` response
3. Check peer terminal for errors
4. Make sure peer is running with `--web-ui`

### Issue: "Peer not initialized"

**Cause**: Peer instance not set

**Fix**:
1. Make sure you started peer with `--web-ui` flag
2. Restart peer
3. Check peer terminal for errors

### Issue: Tasks not executing

**Cause**: Peer not connected to tracker

**Fix**:
1. Make sure tracker is running
2. Check peer terminal - should show "Registered with tracker"
3. Check tracker terminal - should show peer registration

### Issue: Files not uploading

**Cause**: File too large or storage issue

**Fix**:
1. Check file size (max 100MB)
2. Check `peer_storage/` directory exists
3. Check browser console for errors

### Issue: History not showing

**Cause**: No tasks executed yet

**Fix**:
1. Execute some tasks first
2. History populates as tasks complete
3. Check browser console if still empty

## Verification Commands

**Check if peer is running:**
```bash
ps aux | grep "peer.py"
```

**Check if web UI is accessible:**
```bash
curl http://127.0.0.1:5000/api/status
```

**Check peer storage:**
```bash
ls -la peer_storage/
```

## Expected Behavior

### Dashboard Tab
- ✅ Shows real numbers (0 initially)
- ✅ Updates every 2 seconds
- ✅ Shows peer IP and port
- ✅ Shows connection status

### CPU Tasks Tab
- ✅ Can execute tasks
- ✅ Shows results
- ✅ Shows history
- ✅ History updates after execution

### Memory Tab
- ✅ Can set memory
- ✅ Can get memory
- ✅ Shows all keys
- ✅ Can delete keys

### Files Tab
- ✅ Can upload files
- ✅ Shows file list
- ✅ Can download files
- ✅ Can delete files

### Processes Tab
- ✅ Shows process tree (empty initially)
- ✅ Shows process statistics
- ✅ Updates when processes created

### OS Features Tab
- ✅ Can change scheduler
- ✅ Can check deadlocks
- ✅ Shows memory info
- ✅ Shows resource info

## Still Having Issues?

1. **Check Browser Console** (F12):
   - Look for red errors
   - Check Network tab for failed requests

2. **Check Peer Terminal**:
   - Look for error messages
   - Check if peer registered with tracker

3. **Check Tracker Terminal**:
   - Should show peer registration
   - Should show peer updates

4. **Test API Directly**:
   ```bash
   curl http://127.0.0.1:5000/api/status
   ```

5. **Restart Everything**:
   - Stop tracker and peer
   - Start tracker first
   - Then start peer with `--web-ui`

## Success Indicators

✅ Dashboard shows actual numbers
✅ Can execute tasks and see results
✅ Memory operations work
✅ File upload/download works
✅ OS features display data
✅ No errors in browser console
✅ Connection status shows "Connected"

If all these work, your UI is functioning correctly! 🎉




