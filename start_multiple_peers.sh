#!/bin/bash

echo "Starting P2P System with Multiple Peers..."
echo ""

# Start tracker in background
echo "Starting Tracker..."
python3 tracker.py &
TRACKER_PID=$!
sleep 2

# Start peer 1
echo "Starting Peer 1 on port 9000 (Web UI: http://127.0.0.1:5000)..."
python3 peer.py --port 9000 --web-ui --web-port 5000 &
PEER1_PID=$!
sleep 2

# Start peer 2
echo "Starting Peer 2 on port 9001 (Web UI: http://127.0.0.1:5001)..."
python3 peer.py --port 9001 --web-ui --web-port 5001 &
PEER2_PID=$!
sleep 2

# Start peer 3
echo "Starting Peer 3 on port 9002 (Web UI: http://127.0.0.1:5002)..."
python3 peer.py --port 9002 --web-ui --web-port 5002 &
PEER3_PID=$!

echo ""
echo "=========================================="
echo "System Started Successfully!"
echo "=========================================="
echo "Tracker PID: $TRACKER_PID"
echo "Peer 1 PID: $PEER1_PID - http://127.0.0.1:5000"
echo "Peer 2 PID: $PEER2_PID - http://127.0.0.1:5001"
echo "Peer 3 PID: $PEER3_PID - http://127.0.0.1:5002"
echo ""
echo "Press Ctrl+C to stop all processes"
echo "=========================================="

# Wait for Ctrl+C
trap "echo ''; echo 'Stopping all processes...'; kill $TRACKER_PID $PEER1_PID $PEER2_PID $PEER3_PID 2>/dev/null; exit" INT

wait
