# Audio Transcription Service

Audio transcription service using OpenAI Whisper with CUDA acceleration.

## Features

- Multiple Whisper model sizes (tiny to large)
- CUDA acceleration for fast transcription
- Support for multiple audio formats (WAV, MP3, MP4, M4A, FLAC, OGG)
- Auto language detection or manual selection
- REST API with web interface

## Setup

```bash
# Create and activate virtual environment
python3 -m venv audio-env
source audio-env/bin/activate

# Install dependencies
pip install -r requirements.txt

# For RTX 5060 Ti and newer GPUs
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

# Install system dependencies (if needed)
sudo apt update && sudo apt install ffmpeg
```

## Running the Service

```bash
# Activate environment
source audio-env/bin/activate

# Start server
python transcription_server.py
```

The service will run on http://localhost:8001

## API Endpoints

- `GET /` - Service info
- `GET /health` - Health check
- `GET /models` - Available models
- `POST /load_model` - Load specific model
- `POST /transcribe` - Transcribe audio file

## Web Interface

Access the web UI at http://localhost:8001 after starting the service.

## Model Sizes

- **tiny**: 39M parameters, fastest
- **base**: 74M parameters, balanced (default)
- **small**: 244M parameters, better accuracy
- **medium**: 769M parameters, high accuracy
- **large**: 1550M parameters, best accuracy