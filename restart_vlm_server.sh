#!/bin/bash
# Restart VLM server for testing Increment 1

echo "Stopping VLM server..."
# Find and kill the VLM server process
pkill -f "vlm_server.py"
sleep 2

echo "Starting VLM server..."
cd services/vlm
source ~/pytorch-env/bin/activate
nohup python3 vlm_server.py > ../../vlm_server_test.log 2>&1 &

echo "Waiting for server to start..."
sleep 10

# Check if server is running
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✓ VLM server is running"
    echo "Log file: vlm_server_test.log"
else
    echo "✗ VLM server failed to start"
    echo "Check vlm_server_test.log for errors"
fi