#!/bin/bash
# Start All Services

echo "🚀 Starting All Services..."

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Start VLM service in background
echo "Starting VLM service..."
nohup "$SCRIPT_DIR/start_vlm.sh" > "$SCRIPT_DIR/../vlm_service.log" 2>&1 &
VLM_PID=$!
echo "VLM service started with PID: $VLM_PID"

# Wait a bit for VLM to start
sleep 5

# Start Audio service in background
echo "Starting Audio service..."
nohup "$SCRIPT_DIR/start_audio.sh" > "$SCRIPT_DIR/../audio_service.log" 2>&1 &
AUDIO_PID=$!
echo "Audio service started with PID: $AUDIO_PID"

# Start web server (accessible from LAN)
echo "Starting web interface..."
cd "$SCRIPT_DIR/../services/vlm/web_interface" || exit
nohup python3 -m http.server 8080 --bind 0.0.0.0 > "$SCRIPT_DIR/../web_interface.log" 2>&1 &
WEB_PID=$!
echo "Web interface started with PID: $WEB_PID"

# Start audio web interface (accessible from LAN)
echo "Starting audio web interface..."
cd "$SCRIPT_DIR/../services/audio/web_interface" || exit
nohup python3 -m http.server 8002 --bind 0.0.0.0 > "$SCRIPT_DIR/../audio_web_interface.log" 2>&1 &
AUDIO_WEB_PID=$!
echo "Audio web interface started with PID: $AUDIO_WEB_PID"

# Save PIDs for stop script
echo "$VLM_PID" > "$SCRIPT_DIR/../.vlm.pid"
echo "$AUDIO_PID" > "$SCRIPT_DIR/../.audio.pid"
echo "$WEB_PID" > "$SCRIPT_DIR/../.web.pid"
echo "$AUDIO_WEB_PID" > "$SCRIPT_DIR/../.audio_web.pid"

echo "
✅ All services started!

Services running:
- VLM API: http://localhost:8000
- Audio API: http://localhost:8001
- Main Web Interface: http://localhost:8080
- Audio Web Interface: http://localhost:8002

Logs:
- VLM: vlm_service.log
- Audio: audio_service.log
- Web: web_interface.log

To stop all services, run: ./scripts/stop_all.sh
"