#!/bin/bash
# Start Audio Transcription Service

echo "🎤 Starting Audio Transcription Service..."

# Navigate to audio service directory
cd "$(dirname "$0")/../services/audio" || exit

# Create/activate virtual environment
if [ ! -d "audio-env" ]; then
    echo "Creating virtual environment..."
    python3 -m venv audio-env
fi

source audio-env/bin/activate

# Install dependencies if needed
if [ ! -f "audio-env/.installed" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
    pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
    touch audio-env/.installed
fi

# Start the server
echo "Starting audio server on port 8001..."
python transcription_server.py