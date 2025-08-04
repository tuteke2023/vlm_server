#!/bin/bash
# Start VLM Service

echo "🚀 Starting VLM Service..."

# Navigate to VLM service directory
cd "$(dirname "$0")/../services/vlm" || exit

# Use existing pytorch-env if available, otherwise create new one
if [ -d "$HOME/pytorch-env" ]; then
    echo "Using existing pytorch-env..."
    source "$HOME/pytorch-env/bin/activate"
else
    echo "Creating new virtual environment..."
    python3 -m venv vlm-env
    source vlm-env/bin/activate
    pip install -r requirements.txt
    pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
fi

# Start the server
echo "Starting VLM server on port 8000..."
MODEL_NAME="Qwen/Qwen2.5-VL-3B-Instruct" python vlm_server.py