// P2P Resource Sharing System - Web UI JavaScript

let statusUpdateInterval;
let processUpdateInterval;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Initializing UI...');
    
    // Test connection first
    testConnection().then(connected => {
        if (connected) {
            // Load initial data
            loadStatus();
            loadHistory();
            loadMemoryKeys();
            loadFiles();
            loadProcessTree();
            
            // Set up auto-refresh for dashboard
            statusUpdateInterval = setInterval(() => {
                if (document.getElementById('dashboard').classList.contains('active')) {
                    loadStatus();
                }
            }, 2000);
            
            // Auto-refresh for process view
            processUpdateInterval = setInterval(() => {
                if (document.getElementById('processes').classList.contains('active')) {
                    loadProcessTree();
                }
            }, 3000);
        } else {
            showToast('Cannot connect to peer. Make sure peer is running with --web-ui flag.', 'error');
        }
    });
    
    // Set up form handlers
    setupFormHandlers();
    
    // Initialize task result box
    updateTaskResultBox({ status: 'info' });
    
    console.log('UI initialized');
});

// Test connection to peer
async function testConnection() {
    try {
        const response = await fetch('/api/status');
        if (response.ok) {
            const data = await response.json();
            if (data.error && data.error.includes('not initialized')) {
                console.error('Peer not initialized');
                return false;
            }
            return true;
        }
        return false;
    } catch (error) {
        console.error('Connection test failed:', error);
        return false;
    }
}

// Tab switching
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Remove active from all buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(tabName).classList.add('active');
    
    // Activate button
    event.target.classList.add('active');
    
    // Load tab-specific data
    if (tabName === 'dashboard') {
        loadStatus();
        loadHistory();
    } else if (tabName === 'cpu') {
        loadHistory();
    } else if (tabName === 'memory') {
        loadMemoryKeys();
    } else if (tabName === 'files') {
        loadFiles();
    } else if (tabName === 'processes') {
        loadProcessTree();
    } else if (tabName === 'os') {
        loadMemoryInfo();
        loadResourceInfo();
    }
}

// Load system status
async function loadStatus() {
    try {
        const response = await fetch('/api/status');
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        if (data.error) {
            console.error('Status error:', data.error);
            // Don't show toast on every refresh, just log it
            return;
        }
        
        // Update peer info
        const peerInfo = `${data.peer_ip || 'N/A'}:${data.peer_port || 'N/A'}`;
        document.getElementById('peer-info').textContent = `Peer: ${peerInfo}`;
        
        // Update status indicator
        const indicator = document.getElementById('status-indicator');
        indicator.classList.add('connected');
        indicator.classList.remove('disconnected');
        indicator.querySelector('span').textContent = 'Connected';
        
        // Update stats - handle both old and new format
        let scheduler = {};
        if (data.scheduler) {
            if (typeof data.scheduler === 'object') {
                if (data.scheduler.stats) {
                    scheduler = data.scheduler.stats;
                } else {
                    scheduler = data.scheduler;
                }
            }
        }
        
        // Get values with fallbacks
        const totalTasks = scheduler.total_tasks || scheduler.total_processes || 0;
        const completedTasks = scheduler.completed_tasks || scheduler.completed_processes || 0;
        const queueSize = scheduler.queue_size || 0;
        const load = parseFloat(scheduler.current_load) || 0;
        const memoryKeys = (data.memory && data.memory.key_count) || 0;
        const fileCount = (data.storage && data.storage.file_count) || 0;
        
        // Update DOM
        document.getElementById('total-tasks').textContent = totalTasks;
        document.getElementById('completed-tasks').textContent = completedTasks;
        document.getElementById('queue-size').textContent = queueSize;
        document.getElementById('cpu-load').textContent = (load * 100).toFixed(1) + '%';
        document.getElementById('memory-keys').textContent = memoryKeys;
        document.getElementById('file-count').textContent = fileCount;
        
        // Update system info
        updateSystemInfo(data);
        
        // Update recent activity
        updateRecentActivity(data);
        
    } catch (error) {
        console.error('Error loading status:', error);
        const indicator = document.getElementById('status-indicator');
        indicator.classList.remove('connected');
        indicator.classList.add('disconnected');
        indicator.querySelector('span').textContent = 'Disconnected';
        showToast('Failed to connect to peer. Make sure peer is running.', 'error');
    }
}

// Update system information
function updateSystemInfo(data) {
    const infoBox = document.getElementById('system-info');
    
    let schedulerType = 'Round Robin';
    let algorithm = 'N/A';
    
    if (data.scheduler) {
        if (typeof data.scheduler === 'object') {
            if (data.scheduler.type) {
                schedulerType = data.scheduler.type;
            }
            if (data.scheduler.stats) {
                if (data.scheduler.stats.algorithm) {
                    algorithm = data.scheduler.stats.algorithm;
                }
            } else if (data.scheduler.algorithm) {
                algorithm = data.scheduler.algorithm;
            }
        }
    }
    
    const info = {
        'Scheduler Type': schedulerType,
        'Algorithm': algorithm,
        'Memory Keys': (data.memory && data.memory.key_count) || 0,
        'Files Stored': (data.storage && data.storage.file_count) || 0,
        'Cache Hit Rate': (data.cache && data.cache.hit_rate) ? (data.cache.hit_rate * 100).toFixed(1) + '%' : '0%',
        'Total Processes': (data.process_manager && data.process_manager.total_processes) || 0,
        'Process Groups': (data.process_manager && data.process_manager.total_groups) || 0,
        'Cache Size': (data.cache && data.cache.size) || 0,
        'Cache Hits': (data.cache && data.cache.hits) || 0
    };
    
    infoBox.innerHTML = '<pre>' + JSON.stringify(info, null, 2) + '</pre>';
}

// Update recent activity
function updateRecentActivity(data) {
    const activityList = document.getElementById('recent-activity');
    const history = data.task_history || {};
    
    if (history.statistics && Object.keys(history.statistics).length > 0) {
        const stats = history.statistics;
        const items = [
            { text: `Total Tasks: ${stats.total_tasks || 0}`, time: 'Total' },
            { text: `Successful: ${stats.successful || 0}`, time: 'Success' },
            { text: `Failed: ${stats.failed || 0}`, time: 'Failed' },
            { text: `Success Rate: ${(stats.success_rate * 100 || 0).toFixed(1)}%`, time: 'Rate' },
            { text: `Avg Execution Time: ${(stats.average_execution_time || 0).toFixed(3)}s`, time: 'Avg Time' }
        ];
        
        activityList.innerHTML = items.map(item => `
            <div class="activity-item">
                <span>${item.text}</span>
                <span class="time">${item.time}</span>
            </div>
        `).join('');
    } else {
        activityList.innerHTML = '<p style="padding: 20px; color: #6c757d; text-align: center;">No activity yet. Execute some tasks to see statistics here.</p>';
    }
}

// Setup form handlers
function setupFormHandlers() {
    // Task execution form
    document.getElementById('task-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const program = document.getElementById('program-code').value;
        const functionName = document.getElementById('function-name').value;
        const argsText = document.getElementById('task-args').value;
        const priority = parseInt(document.getElementById('task-priority').value);
        const maxRetries = parseInt(document.getElementById('task-retries').value);
        const confidential = document.getElementById('task-confidential').checked;
        
        let args;
        try {
            args = JSON.parse(argsText);
        } catch {
            args = [argsText];
        }
        
        try {
            updateTaskResultBox({ status: 'info', message: 'Executing task...' });
            const response = await fetch('/api/execute_task', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    program,
                    function: functionName,
                    args,
                    priority,
                    max_retries: maxRetries,
                    confidential
                })
            });
            
            const result = await response.json();
            
            if (result.error) {
                updateTaskResultBox({
                    status: 'error',
                    message: result.error,
                    taskId: result.task_id
                });
                showToast('Error: ' + result.error, 'error');
                loadProcessTree();
            } else {
                updateTaskResultBox({
                    status: 'success',
                    taskId: result.task_id,
                    executedBy: result.executed_by || 'Unknown',
                    value: result.result
                });
                const resultStr = result.result !== undefined
                    ? (typeof result.result === 'object' ? JSON.stringify(result.result) : String(result.result))
                    : 'No result returned';
                showToast('Task executed successfully! Result: ' + resultStr, 'success');
                loadHistory();
                loadStatus();
                loadProcessTree();
            }
        } catch (error) {
            updateTaskResultBox({ status: 'error', message: error.message });
            showToast('Error executing task: ' + error.message, 'error');
            loadProcessTree();
        }
    });
    
    // Memory set form
    document.getElementById('memory-set-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const key = document.getElementById('mem-key').value;
        const value = document.getElementById('mem-value').value;
        
        try {
            const response = await fetch('/api/memory/set', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ key, value })
            });
            
            const result = await response.json();
            
            if (result.error) {
                showToast('Error: ' + result.error, 'error');
            } else {
                showToast('Memory set successfully!', 'success');
                document.getElementById('mem-key').value = '';
                document.getElementById('mem-value').value = '';
                loadMemoryKeys();
            }
        } catch (error) {
            showToast('Error: ' + error.message, 'error');
        }
    });
    
    // Memory get form
    document.getElementById('memory-get-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const key = document.getElementById('get-mem-key').value;
        
        try {
            const response = await fetch(`/api/memory/get?key=${encodeURIComponent(key)}`);
            const result = await response.json();
            
            const resultBox = document.getElementById('memory-result');
            if (result.error) {
                resultBox.className = 'result-box error';
                resultBox.textContent = 'Error: ' + result.error;
            } else if (result.found) {
                resultBox.className = 'result-box success';
                resultBox.textContent = `Key: ${key}\nValue: ${JSON.stringify(result.value)}`;
            } else {
                resultBox.className = 'result-box';
                resultBox.textContent = `Key "${key}" not found`;
            }
        } catch (error) {
            showToast('Error: ' + error.message, 'error');
        }
    });
    
    // File upload form
    document.getElementById('file-upload-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const fileInput = document.getElementById('file-input');
        const file = fileInput.files[0];
        
        if (!file) {
            showToast('Please select a file', 'error');
            return;
        }
        
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch('/api/file/upload', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.error) {
                showToast('Error: ' + result.error, 'error');
            } else {
                showToast('File uploaded successfully!', 'success');
                fileInput.value = '';
                loadFiles();
            }
        } catch (error) {
            showToast('Error: ' + error.message, 'error');
        }
    });
    
    // File search form
    document.getElementById('file-search-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const filename = document.getElementById('search-filename').value;
        const resultsDiv = document.getElementById('file-search-results');
        
        if (!filename) {
            showToast('Please enter a filename', 'error');
            return;
        }
        
        resultsDiv.innerHTML = '<p style="color: #6c757d;">Searching network...</p>';
        
        try {
            const response = await fetch(`/api/file/find?filename=${encodeURIComponent(filename)}`);
            const result = await response.json();
            
            if (result.error) {
                resultsDiv.innerHTML = `<p style="color: #ef4444;">Error: ${result.error}</p>`;
            } else if (result.found && result.peers.length > 0) {
                resultsDiv.innerHTML = `
                    <div class="result-box success">
                        <strong>File "${filename}" found on ${result.peers.length} peer(s):</strong>
                        <ul style="margin-top: 10px; padding-left: 20px;">
                            ${result.peers.map(p => `<li>${p.ip}:${p.port}</li>`).join('')}
                        </ul>
                    </div>
                `;
            } else {
                resultsDiv.innerHTML = `<div class="result-box"><strong>File "${filename}" not found on any peer.</strong></div>`;
            }
        } catch (error) {
            resultsDiv.innerHTML = `<p style="color: #ef4444;">Error: ${error.message}</p>`;
            showToast('Error searching network: ' + error.message, 'error');
        }
    });
    
    // Download from network form
    document.getElementById('file-download-network-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const filename = document.getElementById('download-network-filename').value;
        const useMultipeer = document.getElementById('use-multipeer').checked;
        const statusDiv = document.getElementById('file-download-status');
        
        if (!filename) {
            showToast('Please enter a filename', 'error');
            return;
        }
        
        statusDiv.innerHTML = '<p style="color: #6c757d;">Downloading from network...</p>';
        
        try {
            const response = await fetch('/api/file/download-network', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filename, use_multipeer: useMultipeer })
            });
            
            const result = await response.json();
            
            if (result.error) {
                statusDiv.innerHTML = `<div class="result-box error"><strong>Error:</strong> ${result.error}</div>`;
                showToast('Error: ' + result.error, 'error');
            } else {
                const method = useMultipeer ? 'multi-peer' : 'single-peer';
                statusDiv.innerHTML = `
                    <div class="result-box success">
                        <strong>✓ File downloaded successfully!</strong><br>
                        Filename: ${result.filename}<br>
                        Size: ${(result.size / 1024).toFixed(2)} KB<br>
                        Method: ${method} download<br>
                        Peers used: ${result.peers_used || 1}
                    </div>
                `;
                showToast('File downloaded from network successfully!', 'success');
                loadFiles(); // Refresh file list
            }
        } catch (error) {
            statusDiv.innerHTML = `<div class="result-box error"><strong>Error:</strong> ${error.message}</div>`;
            showToast('Error: ' + error.message, 'error');
        }
    });
    
    // Scheduler form
    document.getElementById('scheduler-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const algorithm = document.getElementById('scheduler-algorithm').value;
        
        try {
            const response = await fetch('/api/scheduler/set', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ algorithm })
            });
            
            const result = await response.json();
            
            if (result.error) {
                showToast('Error: ' + result.error, 'error');
            } else {
                showToast(`Scheduler changed to ${algorithm}`, 'success');
                loadStatus();
            }
        } catch (error) {
            showToast('Error: ' + error.message, 'error');
        }
    });
}

// Load task history
async function loadHistory() {
    try {
        const response = await fetch('/api/history?limit=20');
        const data = await response.json();
        
        const historyList = document.getElementById('task-history');
        
        if (data.error) {
            historyList.innerHTML = '<p style="padding: 20px; color: #6c757d; text-align: center;">No task history available yet. Execute some tasks to see history here.</p>';
            return;
        }
        
        // Handle different response formats
        let history = [];
        if (Array.isArray(data)) {
            history = data;
        } else if (data.history && Array.isArray(data.history)) {
            history = data.history;
        } else if (data.data && data.data.history && Array.isArray(data.data.history)) {
            history = data.data.history;
        }
        
        if (history.length === 0) {
            historyList.innerHTML = '<p style="padding: 20px; color: #6c757d; text-align: center;">No task history yet. Execute some tasks to see history here.</p>';
            return;
        }
        
        historyList.innerHTML = history.slice(-10).reverse().map(item => {
            const status = item.status || 'UNKNOWN';
            const statusClass = status === 'SUCCESS' ? 'success' : (status === 'FAILED' ? 'error' : '');
            const role = item.role ? `<div><strong>Role:</strong> ${escapeHtml(item.role)}</div>` : '';
            const executedLine = item.peer_info ? `<div><strong>Executed On:</strong> ${escapeHtml(item.peer_info)}</div>` : '';
            const requestedLine = item.requested_by && (!item.peer_info || item.requested_by !== item.peer_info)
                ? `<div><strong>Requested By:</strong> ${escapeHtml(item.requested_by)}</div>`
                : '';
            return `
            <div class="history-item ${statusClass}">
                <div><strong>Task ID:</strong> ${item.task_id || 'N/A'}</div>
                <div><strong>Type:</strong> ${item.task_type || 'N/A'}</div>
                <div><strong>Status:</strong> ${status}</div>
                ${role}
                ${executedLine}
                ${requestedLine}
                ${item.execution_time !== undefined ? `<div><strong>Time:</strong> ${parseFloat(item.execution_time).toFixed(3)}s</div>` : ''}
                ${item.error ? `<div><strong>Error:</strong> ${item.error}</div>` : ''}
                ${item.result !== undefined ? `<div><strong>Result:</strong> ${JSON.stringify(item.result).substring(0, 100)}${JSON.stringify(item.result).length > 100 ? '...' : ''}</div>` : ''}
                <div class="time">${item.timestamp || 'N/A'}</div>
            </div>
        `;
        }).join('');
    } catch (error) {
        console.error('Error loading history:', error);
        const historyList = document.getElementById('task-history');
        historyList.innerHTML = '<p style="padding: 20px; color: #ef4444;">Error loading history: ' + error.message + '</p>';
    }
}

// Load memory keys
async function loadMemoryKeys() {
    try {
        const response = await fetch('/api/memory/list');
        const data = await response.json();
        
        if (data.error) {
            const keysList = document.getElementById('memory-keys');
            keysList.innerHTML = '<p style="padding: 20px; color: #6c757d;">No memory keys stored yet. Use the form above to store some values.</p>';
            return;
        }
        
        const keysList = document.getElementById('memory-keys');
        const keys = data.keys || [];
        
        if (keys.length === 0) {
            keysList.innerHTML = '<p style="padding: 20px; color: #6c757d;">No memory keys stored yet. Use the form above to store some values.</p>';
            return;
        }
        
        keysList.innerHTML = keys.map(key => `
            <span class="key-badge">${key}</span>
        `).join('');
    } catch (error) {
        console.error('Error loading memory keys:', error);
        const keysList = document.getElementById('memory-keys');
        keysList.innerHTML = '<p style="padding: 20px; color: #ef4444;">Error loading memory keys.</p>';
    }
}

// Load files
async function loadFiles() {
    try {
        const response = await fetch('/api/file/list');
        const data = await response.json();
        
        const filesList = document.getElementById('files-list');
        
        if (data.error) {
            filesList.innerHTML = '<p style="padding: 20px; color: #6c757d;">No files stored yet. Use the form above to upload files.</p>';
            return;
        }
        
        const files = data.files || [];
        
        if (files.length === 0) {
            filesList.innerHTML = '<p style="padding: 20px; color: #6c757d;">No files stored yet. Use the form above to upload files.</p>';
            return;
        }
        
        filesList.innerHTML = files.map(file => `
            <div class="file-item">
                <span class="file-name"><i class="fas fa-file"></i> ${file}</span>
                <div class="file-actions">
                    <a href="/api/file/download/${encodeURIComponent(file)}" class="btn btn-secondary" download>
                        <i class="fas fa-download"></i> Download
                    </a>
                    <button onclick="deleteFile('${file}')" class="btn btn-secondary" style="background: #ef4444;">
                        <i class="fas fa-trash"></i> Delete
                    </button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading files:', error);
        const filesList = document.getElementById('files-list');
        filesList.innerHTML = '<p style="padding: 20px; color: #ef4444;">Error loading files: ' + error.message + '</p>';
    }
}

// Delete file
async function deleteFile(filename) {
    if (!confirm(`Are you sure you want to delete "${filename}"?`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/file/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename })
        });
        
        const result = await response.json();
        
        if (result.error) {
            showToast('Error: ' + result.error, 'error');
        } else if (result.success) {
            showToast('File deleted successfully!', 'success');
            loadFiles();
        } else {
            showToast('File not found', 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

// Load process tree
async function loadProcessTree() {
    try {
        const response = await fetch('/api/processes');
        const data = await response.json();
        
        if (data.error) {
            const treeView = document.getElementById('process-tree');
            treeView.innerHTML = '<p style="padding: 20px; color: #6c757d;">No processes running. Processes are created when tasks are executed.</p>';
            return;
        }
        
        const treeView = document.getElementById('process-tree');
        const statsBox = document.getElementById('process-stats');
        
        // Display process tree
        if (data.tree) {
            treeView.innerHTML = renderTree(data.tree, 0);
        } else if (data.roots && data.roots.length > 0) {
            treeView.innerHTML = data.roots.map(root => renderTree(root, 0)).join('');
        } else {
            treeView.innerHTML = '<p style="padding: 20px; color: #6c757d;">No processes running. Processes are created when tasks are executed.</p>';
        }
        
        // Display statistics
        const stats = {
            'Total Processes': data.total_processes || 0,
            'Root Processes': data.roots?.length || 0,
            'Process Groups': data.process_groups || 0
        };
        statsBox.innerHTML = '<pre>' + JSON.stringify(stats, null, 2) + '</pre>';
    } catch (error) {
        console.error('Error loading process tree:', error);
        const treeView = document.getElementById('process-tree');
        treeView.innerHTML = '<p style="padding: 20px; color: #ef4444;">Error loading process tree.</p>';
    }
}

// Render process tree
function renderTree(node, depth) {
    if (!node) return '';
    
    const indent = '  '.repeat(depth);
    let html = `<div class="tree-node ${depth > 0 ? 'tree-node-child' : ''}">
        <strong>${node.pid}</strong> (${node.state}) - Priority: ${node.priority}
    </div>`;
    
    if (node.children && node.children.length > 0) {
        html += node.children.map(child => renderTree(child, depth + 1)).join('');
    }
    
    return html;
}

// Check for deadlocks
async function checkDeadlock() {
    try {
        const response = await fetch('/api/deadlock/check');
        const data = await response.json();
        
        const resultBox = document.getElementById('deadlock-result');
        
        if (data.error) {
            resultBox.className = 'result-box error';
            resultBox.innerHTML = '<strong>Error:</strong> ' + data.error;
        } else if (data.deadlock) {
            resultBox.className = 'result-box error';
            const processes = data.deadlocked_processes || [];
            resultBox.innerHTML = `<strong>⚠️ DEADLOCK DETECTED!</strong><br>Deadlocked Processes: ${processes.length > 0 ? processes.join(', ') : 'Unknown'}`;
        } else {
            resultBox.className = 'result-box success';
            resultBox.innerHTML = '<strong>✓ No deadlock detected.</strong><br>System is safe.';
        }
    } catch (error) {
        const resultBox = document.getElementById('deadlock-result');
        resultBox.className = 'result-box error';
        resultBox.innerHTML = '<strong>Error:</strong> ' + error.message;
        showToast('Error: ' + error.message, 'error');
    }
}

// Load memory management info
async function loadMemoryInfo() {
    try {
        const response = await fetch('/api/os/memory-info');
        const data = await response.json();
        
        const infoBox = document.getElementById('memory-mgmt-info');
        
        if (data.error) {
            infoBox.innerHTML = '<p style="color: #ef4444;">Error: ' + data.error + '</p>';
        } else {
            infoBox.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
        }
    } catch (error) {
        const infoBox = document.getElementById('memory-mgmt-info');
        infoBox.innerHTML = '<p style="color: #ef4444;">Error loading memory info: ' + error.message + '</p>';
    }
}

// Load resource allocation info
async function loadResourceInfo() {
    try {
        const response = await fetch('/api/os/resource-info');
        const data = await response.json();
        
        const infoBox = document.getElementById('resource-info');
        
        if (data.error) {
            infoBox.innerHTML = '<p style="color: #ef4444;">Error: ' + data.error + '</p>';
        } else {
            infoBox.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
        }
    } catch (error) {
        const infoBox = document.getElementById('resource-info');
        infoBox.innerHTML = '<p style="color: #ef4444;">Error loading resource info: ' + error.message + '</p>';
    }
}

// Delete memory key
async function deleteSelectedKey() {
    const key = prompt('Enter key to delete:');
    if (!key) return;
    
    try {
        const response = await fetch('/api/memory/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ key })
        });
        
        const result = await response.json();
        
        if (result.error) {
            showToast('Error: ' + result.error, 'error');
        } else if (result.success) {
            showToast('Memory key deleted successfully!', 'success');
            loadMemoryKeys();
        } else {
            showToast('Key not found', 'error');
        }
    } catch (error) {
        showToast('Error: ' + error.message, 'error');
    }
}

// Show toast notification
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 4000);
}

function escapeHtml(value) {
    if (value === undefined || value === null) return '';
    return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function updateTaskResultBox(info = {}) {
    const resultBox = document.getElementById('cpu-task-result');
    if (!resultBox) {
        return;
    }
    
    let className = 'info-box';
    let html = '';
    
    if (info.status === 'success') {
        className += ' success';
        const resultValue = info.value !== undefined
            ? `<pre>${escapeHtml(JSON.stringify(info.value, null, 2))}</pre>`
            : '<em>No result returned.</em>';
        html = `
            <div><strong>Task ID:</strong> ${escapeHtml(info.taskId || 'N/A')}</div>
            <div><strong>Executed On:</strong> ${escapeHtml(info.executedBy || 'Unknown')}</div>
            <div><strong>Status:</strong> SUCCESS</div>
            <div><strong>Result:</strong> ${resultValue}</div>
        `;
    } else if (info.status === 'error') {
        className += ' error';
        html = `
            <div><strong>Error${info.taskId ? ` (Task ${escapeHtml(info.taskId)})` : ''}:</strong></div>
            <p>${escapeHtml(info.message || info.error || 'Unknown error')}</p>
        `;
    } else {
        const msg = info.message || 'No task executed yet.';
        html = `<p>${escapeHtml(msg)}</p>`;
    }
    
    resultBox.className = className;
    resultBox.innerHTML = html;
}

// Add loading indicator
function showLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = '<div class="spinner"></div>';
    }
}

// Handle API errors better
function handleApiError(error, defaultMessage) {
    console.error('API Error:', error);
    const message = error.message || defaultMessage || 'An error occurred';
    showToast(message, 'error');
    return message;
}

