"""
Web UI for P2P Resource Sharing System.
Flask-based web interface for interacting with peers and tracker.
"""

from flask import Flask, render_template, jsonify, request
import threading
import socket
import json
import time
from typing import Dict, Optional

import messages
import config
from peer import Peer

app = Flask(__name__)

# Global peer instance (will be set when peer starts)
peer_instance: Optional[Peer] = None
tracker_host = "127.0.0.1"
tracker_port = 8888


def set_peer_instance(peer: Peer):
    """Set the peer instance for web UI."""
    global peer_instance
    peer_instance = peer


@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html')


@app.route('/api/status')
def get_status():
    """Get peer status."""
    if not peer_instance:
        return jsonify({"error": "Peer not initialized"}), 500
    
    try:
        # Get status from peer
        status = peer_instance._handle_status()
        
        # Handle different response formats
        if isinstance(status, dict):
            # Check if it's a message format with "data" key
            if "data" in status:
                return jsonify(status["data"])
            # Check if it's a message format with "status" key
            elif "status" in status:
                # Extract data from message format
                data = {k: v for k, v in status.items() if k not in ["type", "status"]}
                return jsonify(data)
            # Otherwise return as-is
            else:
                return jsonify(status)
        else:
            return jsonify({"error": "Invalid status format"}), 500
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500


@app.route('/api/execute_task', methods=['POST'])
def execute_task():
    """Execute a CPU task."""
    if not peer_instance:
        return jsonify({"error": "Peer not initialized"}), 500
    
    try:
        data = request.json
        program = data.get("program", "")
        function = data.get("function", "main")
        args = data.get("args", [])
        confidential = data.get("confidential", False)
        priority = data.get("priority", 0)
        max_retries = data.get("max_retries", 0)
        timeout = data.get("timeout")
        
        if not program:
            return jsonify({"error": "Program code required"}), 400
        
        result = peer_instance.submit_cpu_task(
            program=program,
            function=function,
            args=args,
            confidential=confidential,
            priority=priority,
            max_retries=max_retries,
            timeout=timeout
        )
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/cancel_task', methods=['POST'])
def cancel_task():
    """Cancel a task."""
    if not peer_instance:
        return jsonify({"error": "Peer not initialized"}), 500
    
    try:
        data = request.json
        task_id = data.get("task_id")
        
        if not task_id:
            return jsonify({"error": "task_id required"}), 400
        
        cancelled = peer_instance.cancel_task(task_id)
        return jsonify({"success": cancelled, "task_id": task_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/memory/set', methods=['POST'])
def set_memory():
    """Set memory value."""
    if not peer_instance:
        return jsonify({"error": "Peer not initialized"}), 500
    
    try:
        data = request.json
        key = data.get("key")
        value = data.get("value")
        
        if not key:
            return jsonify({"error": "key required"}), 400
        
        success = peer_instance.set_memory(key, value)
        return jsonify({"success": success, "key": key, "value": value})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/memory/get', methods=['GET'])
def get_memory():
    """Get memory value."""
    if not peer_instance:
        return jsonify({"error": "Peer not initialized"}), 500
    
    try:
        key = request.args.get("key")
        if not key:
            return jsonify({"error": "key required"}), 400
        
        value = peer_instance.get_memory(key)
        return jsonify({"key": key, "value": value, "found": value is not None})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/memory/list', methods=['GET'])
def list_memory():
    """List all memory keys."""
    if not peer_instance:
        return jsonify({"error": "Peer not initialized"}), 500
    
    try:
        keys = peer_instance.memory_store.list_keys()
        return jsonify({"keys": keys})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/file/upload', methods=['POST'])
def upload_file():
    """Upload a file."""
    if not peer_instance:
        return jsonify({"error": "Peer not initialized"}), 500
    
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        filename = file.filename or request.form.get('filename', 'uploaded_file')
        
        data = file.read()
        success = peer_instance.put_file(filename, data)
        
        return jsonify({"success": success, "filename": filename, "size": len(data)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/file/list', methods=['GET'])
def list_files():
    """List all files."""
    if not peer_instance:
        return jsonify({"error": "Peer not initialized"}), 500
    
    try:
        files = peer_instance.file_storage.list_files()
        return jsonify({"files": files})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/file/download/<filename>', methods=['GET'])
def download_file(filename):
    """Download a file."""
    if not peer_instance:
        return jsonify({"error": "Peer not initialized"}), 500
    
    try:
        from flask import send_file
        import os
        from pathlib import Path
        
        file_path = Path(config.STORAGE_DIR) / filename
        if file_path.exists():
            return send_file(str(file_path), as_attachment=True)
        else:
            return jsonify({"error": "File not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/file/find', methods=['GET'])
def find_file():
    """Find which peers have a file."""
    if not peer_instance:
        return jsonify({"error": "Peer not initialized"}), 500
    
    try:
        filename = request.args.get("filename")
        if not filename:
            return jsonify({"error": "filename required"}), 400
        
        peers = peer_instance.find_file_on_network(filename)
        return jsonify({
            "filename": filename,
            "peers": [{"ip": ip, "port": port} for ip, port in peers],
            "found": len(peers) > 0
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/file/download-network', methods=['POST'])
def download_from_network():
    """Download a file from network using multiple peers."""
    if not peer_instance:
        return jsonify({"error": "Peer not initialized"}), 500
    
    try:
        data = request.json
        filename = data.get("filename")
        use_multipeer = data.get("use_multipeer", True)
        
        if not filename:
            return jsonify({"error": "filename required"}), 400
        
        # Download file
        file_data = peer_instance.download_file_from_network(
            filename, 
            save_path=None,  # Don't save automatically, we'll return it
            use_multipeer=use_multipeer
        )
        
        if file_data is None:
            return jsonify({"error": "File not found on network"}), 404
        
        # Save to local storage
        success = peer_instance.put_file(filename, file_data)
        
        if success:
            return jsonify({
                "success": True,
                "filename": filename,
                "size": len(file_data),
                "peers_used": len(peer_instance.find_file_on_network(filename))
            })
        else:
            return jsonify({"error": "Failed to save file"}), 500
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/file/upload-remote', methods=['POST'])
def upload_file_to_remote():
    """Upload a file to a remote peer (owned file storage)."""
    if not peer_instance:
        return jsonify({"error": "Peer not initialized"}), 500
    
    try:
        data = request.json
        filename = data.get("filename")
        target_peer_ip = data.get("target_peer_ip")
        target_peer_port = data.get("target_peer_port")
        replication_count = data.get("replication_count", 1)
        
        if not filename:
            return jsonify({"error": "filename required"}), 400
        if not target_peer_ip or not target_peer_port:
            return jsonify({"error": "target_peer_ip and target_peer_port required"}), 400
        
        # Get file from local storage
        file_data = peer_instance.file_storage.get_file(filename)
        if file_data is None:
            return jsonify({"error": f"File {filename} not found locally"}), 404
        
        # Upload to remote peer
        result = peer_instance.upload_file_to_peer(
            target_peer_ip, 
            int(target_peer_port), 
            filename, 
            file_data=file_data,
            replication_count=replication_count
        )
        
        if result.get("success"):
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/file/download-owned', methods=['POST'])
def download_owned_file():
    """Download an owned file from remote storage."""
    if not peer_instance:
        return jsonify({"error": "Peer not initialized"}), 500
    
    try:
        data = request.json
        filename = data.get("filename")
        
        if not filename:
            return jsonify({"error": "filename required"}), 400
        
        # Download owned file
        file_data = peer_instance.download_owned_file(filename)
        
        if file_data is None:
            return jsonify({"error": "File not found or failed to download"}), 404
        
        # Save to local storage
        success = peer_instance.put_file(filename, file_data)
        
        if success:
            return jsonify({
                "success": True,
                "filename": filename,
                "size": len(file_data)
            })
        else:
            return jsonify({"error": "Failed to save file"}), 500
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/file/list-owned', methods=['GET'])
def list_owned_files():
    """List files owned by this peer."""
    if not peer_instance:
        return jsonify({"error": "Peer not initialized"}), 500
    
    try:
        with peer_instance.ownership_lock:
            owned_files = list(peer_instance.owned_files.keys())
        
        return jsonify({
            "success": True,
            "owned_files": owned_files,
            "count": len(owned_files)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/peers/list', methods=['GET'])
def list_peers():
    """Get list of available peers from tracker."""
    if not peer_instance:
        return jsonify({"error": "Peer not initialized"}), 500
    
    try:
        # Query tracker for peer list
        msg = messages.create_message(messages.MessageType.STATUS)
        response = peer_instance._send_to_tracker(msg)
        
        if not response:
            return jsonify({
                "error": "No response from tracker. Make sure tracker is running.",
                "success": False
            }), 500
        
        if response.get("status") == "OK":
            peers_data = response.get("data", {})
            peer_list = peers_data.get("peers", [])
            
            # Format peer list and exclude current peer
            peers = []
            # Ensure port is int for comparison
            current_peer_ip = str(peer_instance.peer_ip)
            current_peer_port = int(peer_instance.peer_port)
            
            # Debug info
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"Current peer: {current_peer_ip}:{current_peer_port}")
            logger.debug(f"Peers from tracker: {peer_list}")
            
            for peer_info in peer_list:
                peer_ip = str(peer_info.get("ip", ""))
                # Handle both int and string ports
                peer_port_raw = peer_info.get("port", 0)
                try:
                    peer_port = int(peer_port_raw)
                except (ValueError, TypeError):
                    peer_port = 0
                
                # Skip current peer (don't show yourself in the list)
                # Compare as strings to avoid type issues
                if str(peer_ip) == str(current_peer_ip) and int(peer_port) == int(current_peer_port):
                    logger.debug(f"Skipping self: {peer_ip}:{peer_port} (current: {current_peer_ip}:{current_peer_port})")
                    continue
                
                peers.append({
                    "ip": peer_ip,
                    "port": peer_port,
                    "cpu_load": float(peer_info.get("cpu_load", 0.0)),
                    "last_update": peer_info.get("last_update")
                })
            
            return jsonify({
                "success": True,
                "peers": peers,
                "count": len(peers),
                "total_peers_on_tracker": len(peer_list),
                "current_peer": f"{current_peer_ip}:{current_peer_port}",
                "debug_info": {
                    "current_peer_ip": current_peer_ip,
                    "current_peer_port": current_peer_port,
                    "all_peers_from_tracker": [
                        {"ip": str(p.get("ip", "")), "port": int(p.get("port", 0))} 
                        for p in peer_list
                    ]
                }
            })
        else:
            error_msg = response.get("error", "Unknown error")
            return jsonify({
                "error": f"Tracker returned error: {error_msg}",
                "success": False
            }), 500
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": f"Exception: {str(e)}",
            "success": False
        }), 500


@app.route('/api/history', methods=['GET'])
def get_history():
    """Get task history."""
    if not peer_instance:
        return jsonify({"error": "Peer not initialized"}), 500
    
    try:
        limit = int(request.args.get("limit", 100))
        task_type = request.args.get("type")
        
        history = peer_instance.get_task_history(limit, task_type)
        # Ensure we return the expected format
        if isinstance(history, dict):
            return jsonify(history)
        else:
            return jsonify({"history": [], "statistics": {}})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/processes', methods=['GET'])
def get_processes():
    """Get process tree."""
    if not peer_instance:
        return jsonify({"error": "Peer not initialized"}), 500
    
    try:
        root_pid = request.args.get("root_pid")
        tree = peer_instance.process_manager.get_process_tree(root_pid)
        # Ensure we return a valid format
        if isinstance(tree, dict):
            return jsonify(tree)
        else:
            return jsonify({"total_processes": 0, "roots": []})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/deadlock/check', methods=['GET'])
def check_deadlock():
    """Check for deadlocks."""
    if not peer_instance:
        return jsonify({"error": "Peer not initialized"}), 500
    
    try:
        deadlock, processes = peer_instance.deadlock_detector.detect_deadlock()
        return jsonify({"deadlock": deadlock, "deadlocked_processes": processes})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/scheduler/set', methods=['POST'])
def set_scheduler():
    """Change scheduling algorithm."""
    if not peer_instance:
        return jsonify({"error": "Peer not initialized"}), 500
    
    try:
        data = request.json
        algorithm = data.get("algorithm")
        
        if not algorithm:
            return jsonify({"error": "algorithm required"}), 400
        
        result = peer_instance._handle_set_scheduler({"algorithm": algorithm})
        
        # Handle response format
        if isinstance(result, dict):
            if "error" in result:
                return jsonify(result), 400
            elif "data" in result:
                return jsonify(result["data"])
            else:
                return jsonify(result)
        else:
            return jsonify({"status": "OK", "algorithm": algorithm})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/memory/delete', methods=['POST'])
def delete_memory():
    """Delete a memory key."""
    if not peer_instance:
        return jsonify({"error": "Peer not initialized"}), 500
    
    try:
        data = request.json
        key = data.get("key")
        
        if not key:
            return jsonify({"error": "key required"}), 400
        
        deleted = peer_instance.memory_store.delete(key)
        return jsonify({"success": deleted, "key": key})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/file/delete', methods=['POST'])
def delete_file():
    """Delete a file."""
    if not peer_instance:
        return jsonify({"error": "Peer not initialized"}), 500
    
    try:
        data = request.json
        filename = data.get("filename")
        
        if not filename:
            return jsonify({"error": "filename required"}), 400
        
        deleted = peer_instance.file_storage.delete_file(filename)
        return jsonify({"success": deleted, "filename": filename})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/os/memory-info', methods=['GET'])
def get_memory_info():
    """Get memory management information."""
    if not peer_instance:
        return jsonify({"error": "Peer not initialized"}), 500
    
    try:
        stats = peer_instance.memory_manager.get_statistics()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/os/resource-info', methods=['GET'])
def get_resource_info():
    """Get resource allocation information."""
    if not peer_instance:
        return jsonify({"error": "Peer not initialized"}), 500
    
    try:
        status = peer_instance.deadlock_detector.get_resource_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def run_web_ui(peer: Peer, host='127.0.0.1', port=5000, debug=False):
    """
    Run the web UI server.
    
    Args:
        peer: Peer instance
        host: Host to bind to
        port: Port to bind to
        debug: Enable debug mode
    """
    set_peer_instance(peer)
    print(f"Starting web UI on http://{host}:{port}")
    print(f"Peer instance set: {peer_instance is not None}")
    print(f"Press Ctrl+D in browser for debug panel")
    app.run(host=host, port=port, debug=debug, threaded=True, use_reloader=False)


if __name__ == '__main__':
    # For testing
    from peer import Peer
    peer = Peer(peer_port=9000)
    threading.Thread(target=peer.start, daemon=True).start()
    time.sleep(2)
    run_web_ui(peer, port=5000)

