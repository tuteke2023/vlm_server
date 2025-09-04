# Setup Guide for New Computer

This guide helps you set up the complete VLM + Audio + Vector Database system on a new computer.

## Prerequisites

- Python 3.8+
- CUDA-capable GPU (16GB+ VRAM recommended for full features)
- 50GB free disk space
- Ubuntu 20.04+ or similar Linux (Windows WSL2 also works)

## Quick Setup

### 1. Clone the Repository

```bash
git clone https://github.com/tuteke2023/vlm_server.git
cd vlm_server
```

### 2. Setup Virtual Environment

```bash
# Create and activate virtual environment
python3 -m venv ~/pytorch-env
source ~/pytorch-env/bin/activate

# Install PyTorch with CUDA support
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

# Install all requirements
pip install -r requirements.txt
```

### 3. Install Audio Service Dependencies

```bash
# Install audio-specific requirements
pip install openai-whisper chromadb sentence-transformers sqlalchemy
```

### 4. Start Services

#### Terminal 1: VLM Server (if you have 16GB+ VRAM)
```bash
source ~/pytorch-env/bin/activate
python vlm_server.py
# Server runs on http://localhost:8000
```

#### Terminal 2: Audio Service with Vector Database
```bash
source ~/pytorch-env/bin/activate
cd services/audio
python transcription_server.py
# Server runs on http://localhost:8001
```

#### Terminal 3: Web Interface
```bash
cd services/audio/web_interface
python3 -m http.server 8002
# Web UI at http://localhost:8002
```

## Access Points

### Web Interfaces
- **Q&A System**: http://localhost:8002/qa_interface.html
- **Vector Search**: http://localhost:8002/search.html
- **Audio Transcription**: http://localhost:8002/index.html
- **Main VLM Interface**: http://localhost:8080/ (if running main web UI)

### API Endpoints
- **VLM API**: http://localhost:8000/api/v1/generate
- **Audio API**: http://localhost:8001/transcribe
- **Q&A API**: http://localhost:8001/qa/ask
- **Vector Search API**: http://localhost:8001/transcripts/search

## Import Existing Vector Database

If you have an exported vector database from another computer:

```bash
# 1. Copy the export file to this computer
scp user@old-computer:~/vector_db_export_*.tar.gz .

# 2. Extract it
tar -xzf vector_db_export_*.tar.gz

# 3. Copy database files to correct location
cp -r vector_db_export_*/transcript_vectors services/audio/
cp vector_db_export_*/transcripts.db services/audio/

# 4. Restart the audio service
```

## Configuration for Different Setups

### Setup A: Everything on One Computer (16GB+ VRAM)
No changes needed - everything runs locally

### Setup B: Distributed (8GB + 16GB machines)

On the 8GB machine (vector database):
```python
# In services/audio/llm_qa_system.py, change:
vlm_url = "http://192.168.1.100:8000"  # IP of 16GB machine
```

On the 16GB machine (VLM):
```bash
python vlm_server.py --host 0.0.0.0  # Allow external connections
```

### Setup C: Cloud LLM (No GPU needed for Q&A)

```python
# In services/audio/llm_qa_system.py:
# Use OpenAI instead of local VLM
import openai
openai.api_key = "your-key-here"
```

## Testing the Installation

### 1. Test VLM Server
```bash
curl http://localhost:8000/health
```

### 2. Test Audio Service
```bash
curl http://localhost:8001/health
```

### 3. Test Vector Database
```bash
curl http://localhost:8001/vector/stats
```

### 4. Test Q&A System
```bash
python test_qa_system.py
```

### 5. Test Performance
```bash
python test_performance.py
```

## Batch Processing Audio Files

### Process a folder of audio files
```bash
python batch_transcribe_filtered.py "/path/to/audio/folder" --model base
```

### Process with truncation for long files
```bash
python transcribe_truncated.py --batch --duration 60
```

## Troubleshooting

### CUDA Out of Memory
- Use smaller model: Change to `qwen2.5-vl-3b` instead of `7b`
- Reduce batch size in processing
- Close other GPU applications

### Port Already in Use
```bash
# Find and kill process using port
lsof -ti :8001 | xargs kill -9
```

### Whisper Model Download Issues
```bash
# Pre-download Whisper models
python -c "import whisper; whisper.load_model('base')"
```

### Vector Database Corruption
```bash
# Rebuild vector database from SQLite
python -c "from services.audio.vector_storage import VectorTranscriptStorage; 
v = VectorTranscriptStorage(); v.rebuild_from_sqlite()"
```

## Performance Tips

1. **For Transcription**: Use `base` model for good balance
2. **For Q&A**: Keep chunks small (500 chars) for better relevance
3. **For Search**: Use semantic search first, then filter
4. **For VLM**: Use 3B model if VRAM limited, 7B for better quality

## System Requirements Summary

### Minimum (Basic Features)
- 8GB RAM
- 8GB VRAM
- 20GB disk space

### Recommended (Full Features)
- 16GB RAM
- 16GB VRAM
- 50GB disk space

### Optimal (Best Performance)
- 32GB RAM
- 24GB VRAM
- 100GB disk space

## Getting Help

- GitHub Issues: https://github.com/tuteke2023/vlm_server/issues
- Check logs: `tail -f services/audio/audio_service.log`
- Test endpoints: `python test_qa_system.py`

## Next Steps

1. Process your audio files: `python batch_transcribe_filtered.py /path/to/audio`
2. Try Q&A: Visit http://localhost:8002/qa_interface.html
3. Search transcripts: Visit http://localhost:8002/search.html
4. Explore the API: Check API_DOCUMENTATION.md