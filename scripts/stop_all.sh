#!/bin/bash
# Stop All Services

echo "🛑 Stopping All Services..."

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Stop VLM service
if [ -f "$SCRIPT_DIR/../.vlm.pid" ]; then
    VLM_PID=$(cat "$SCRIPT_DIR/../.vlm.pid")
    if ps -p "$VLM_PID" > /dev/null 2>&1; then
        echo "Stopping VLM service (PID: $VLM_PID)..."
        kill "$VLM_PID"
        rm "$SCRIPT_DIR/../.vlm.pid"
    fi
fi

# Stop Audio service  
if [ -f "$SCRIPT_DIR/../.audio.pid" ]; then
    AUDIO_PID=$(cat "$SCRIPT_DIR/../.audio.pid")
    if ps -p "$AUDIO_PID" > /dev/null 2>&1; then
        echo "Stopping Audio service (PID: $AUDIO_PID)..."
        kill "$AUDIO_PID"
        rm "$SCRIPT_DIR/../.audio.pid"
    fi
fi

# Stop Web interface
if [ -f "$SCRIPT_DIR/../.web.pid" ]; then
    WEB_PID=$(cat "$SCRIPT_DIR/../.web.pid")
    if ps -p "$WEB_PID" > /dev/null 2>&1; then
        echo "Stopping Web interface (PID: $WEB_PID)..."
        kill "$WEB_PID"
        rm "$SCRIPT_DIR/../.web.pid"
    fi
fi

# Stop Audio Web interface
if [ -f "$SCRIPT_DIR/../.audio_web.pid" ]; then
    AUDIO_WEB_PID=$(cat "$SCRIPT_DIR/../.audio_web.pid")
    if ps -p "$AUDIO_WEB_PID" > /dev/null 2>&1; then
        echo "Stopping Audio Web interface (PID: $AUDIO_WEB_PID)..."
        kill "$AUDIO_WEB_PID"
        rm "$SCRIPT_DIR/../.audio_web.pid"
    fi
fi

# Also check for any remaining processes
pkill -f "vlm_server.py" 2>/dev/null
pkill -f "transcription_server.py" 2>/dev/null
pkill -f "python3 -m http.server 8080" 2>/dev/null
pkill -f "python3 -m http.server 8002" 2>/dev/null

echo "✅ All services stopped!"