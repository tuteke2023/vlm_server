# VLM Server - Vision Language Model with Conversational AI

A comprehensive Vision Language Model (VLM) server with dual web interfaces for document processing and conversational AI. Built with Qwen2.5-VL models (3B/7B) featuring GPU acceleration, conversation memory, and automatic VRAM management.

## 🚀 Features

### **Core VLM Server**
- 🔥 **GPU Accelerated** - RTX 5060 Ti with sm_120 CUDA support
- 🧠 **Multi-Model Support** - Qwen2.5-VL-3B/7B-Instruct models with hot-swapping
- 💾 **Smart VRAM Management** - Automatic memory monitoring and safety limits
- 🔄 **Multi-modal Processing** - Text, images, and video support
- 🛡️ **Production Ready** - Error handling, logging, health monitoring
- 📊 **Real-time Monitoring** - VRAM usage, performance metrics
- 🔧 **CUDA Stability** - Fixed device-side assert errors with official HF patterns

### **💬 Chat Interface** (`/chat.html`)
- 🗣️ **Conversational AI** - Natural chat with vision-language model
- 🧠 **Conversation Memory** - Remembers entire chat history for context
- 📱 **WhatsApp-style UI** - Modern chat bubbles with timestamps
- 🖼️ **Image Chat** - Upload and discuss images in conversation
- 📤 **Drag & Drop** - Easy image sharing in chat
- 💾 **Export Conversations** - Save chat history as JSON
- 📊 **Context Indicators** - Visual feedback on conversation memory

### **🔧 Document Processing Interface** (`/index.html`)
- 🌐 **Modern UI** - Responsive design with drag & drop
- 🏦 **Bank Transaction Extraction** - Parse statements and receipts
- 📊 **CSV Export** - Export bank transactions to CSV/JSON with LangChain
- 📄 **Document Summarization** - AI-powered summaries and insights  
- 🖼️ **Image Analysis** - Object detection, OCR, and description
- 📝 **Text Extraction** - Advanced OCR with formatting preservation
- ❓ **Custom Queries** - Ask anything about uploaded documents
- 🔄 **Model Selection** - Switch between 3B/7B models for different VRAM needs

### **🎙️ Audio Transcription & Vector Search** (NEW!)
- 🎯 **GPU-Accelerated Transcription** - OpenAI Whisper on CUDA for fast processing
- 📂 **Batch Processing** - Transcribe hundreds of audio files automatically
- ✂️ **Automatic Truncation** - Handle recordings >1 hour with ffmpeg truncation
- 🔍 **Vector Database Search** - ChromaDB-powered semantic search across transcripts
- 🤖 **RAG Q&A System** - Ask questions and extract action items from transcripts
- 💾 **Hybrid Storage** - SQLite for metadata + ChromaDB for vector embeddings
- 🎨 **Search Interface** - Material Design UI at `http://localhost:8002/search.html`
- 📊 **Smart Chunking** - Automatic text segmentation for optimal retrieval

## 📁 Project Structure

```
vlm_server/
├── vlm_server.py                      # Main FastAPI server with multi-model support
├── bank_parser_v3.py                  # LangChain bank statement parser
├── requirements.txt                   # Dependencies with LangChain
├── client_example.py                  # Python client example
├── test_vlm_server.py                 # Comprehensive test suite
├── test_chat_interface.py             # Chat interface API tests  
├── test_conversation_context.py       # Conversation memory tests
├── test_parser_v3.py                  # Bank parser tests
├── API_DOCUMENTATION.md               # Complete API reference
├── CLAUDE.md                          # Development notes for AI assistants
├── BATCH_TRANSCRIPTION_GUIDE.md      # Audio batch processing guide
├── AUDIO_VECTOR_FEATURES.md          # Vector database feature docs
├── batch_transcribe_filtered.py      # Batch transcription with filtering
├── transcribe_truncated.py           # Truncate and transcribe long files
├── analyze_large_files.py            # Analyze skipped audio files
├── services/audio/                   # Audio transcription service
│   ├── transcription_server.py       # Whisper API server
│   ├── vector_storage.py            # ChromaDB vector storage
│   ├── transcript_storage.py        # SQLite transcript database
│   └── web_interface/               # Audio search interface
│       └── search.html              # Vector search UI
├── web_interface/                     # Dual Web UI
│   ├── index.html                    # Document processing interface
│   ├── chat.html                     # Conversational AI interface
│   ├── static/css/style.css          # Shared modern styling
│   ├── static/js/app.js              # Document processing logic with CSV export
│   ├── static/js/chat.js             # Chat interface with context memory
│   ├── server.py                     # Development web server
│   └── README.md                     # Web interface docs
└── README.md                         # This file
```

## 🔧 Quick Start

### Prerequisites

- **Python 3.8+**
- **CUDA-capable GPU** (recommended: 16GB+ VRAM for VLM, 8GB+ for Whisper)
- **NVIDIA drivers** and CUDA toolkit
- **ffmpeg** (for audio processing and truncation)

### 1. Clone Repository

```bash
git clone https://github.com/tuteke2023/vlm_server.git
cd vlm_server
```

### 2. Setup Environment

```bash
# Create virtual environment
python3 -m venv ~/pytorch-env
source ~/pytorch-env/bin/activate

# Install dependencies
pip install -r requirements.txt

# For RTX 5060 Ti and newer GPUs (sm_120+), install PyTorch with CUDA 12.8:
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

# Install ffmpeg for audio processing (required for transcription)
sudo apt update && sudo apt install -y ffmpeg

# Install additional audio dependencies
pip install openai-whisper chromadb
```

**Important**: Always activate the virtual environment before running the server!

### 3. Start VLM Server

```bash
source ~/pytorch-env/bin/activate
python vlm_server.py
```

The server will start on `http://localhost:8000` with:
- ✅ **Model Loading**: Qwen2.5-VL-3B-Instruct (default for safe VRAM usage)
- ✅ **Health Endpoint**: `/health` - Server status
- ✅ **VRAM Monitoring**: `/vram_status` - Memory usage
- ✅ **Model Management**: `/available_models`, `/reload_model` - Multi-model support
- ✅ **Generation API**: `/api/v1/generate` - Main processing endpoint

### 4. Start Audio Transcription Service (Optional)

```bash
# In a new terminal
source ~/pytorch-env/bin/activate
cd services/audio
python transcription_server.py
```

The transcription server will start on `http://localhost:8001` with:
- ✅ **Whisper Model**: GPU-accelerated transcription (base model by default)
- ✅ **Vector Database**: ChromaDB for semantic search
- ✅ **RAG System**: Q&A and action items extraction
- ✅ **Web Search UI**: Available at `http://localhost:8002/search.html`

### 5. Start Web Interface

```bash
# In a new terminal
cd web_interface
python3 -m http.server 8080
```

## 🌐 **Access the Interfaces**

### Web Interfaces
- **🔧 Main Web UI**: `http://localhost:8080/` - Document processing tools
- **💬 Chat Interface**: `http://localhost:8080/chat.html` - Conversational AI with memory
- **💳 Bank Processor**: `http://localhost:8080/bank_processor.html` - Bank statement extraction
- **🎤 Audio Transcription**: `http://localhost:8002/` - Audio to text conversion (Whisper)
- **🔍 Vector Search**: `http://localhost:8002/search.html` - Semantic search across all transcripts

### API Endpoints
- **VLM API**: `http://localhost:8000` - Vision Language Model API
- **Audio API**: `http://localhost:8001` - Whisper transcription API

## 🎯 Use Cases

### 💳 **Bank Statement Processing**
```bash
# Upload bank statement PDF or image
# Extract: dates, amounts, descriptions, merchants
# Output: Structured transaction table with totals
# Export: Download as CSV or JSON with automatic categorization
# Features: LangChain-powered parsing with debit/credit separation
```

### 📊 **Document Analysis**
```bash
# Upload contracts, reports, invoices
# Get: Summaries, key points, entities, insights
# Formats: Executive summary, bullet points, technical
```

### 🖼️ **Image Intelligence**
```bash
# Upload photos, screenshots, diagrams
# Extract: Text (OCR), objects, colors, descriptions
# Use cases: Receipt processing, form analysis
```

### 📝 **Custom Queries**
```bash
# Ask specific questions about documents
# Examples:
# - "What are the main financial metrics?"
# - "Extract all phone numbers and emails"
# - "Summarize the contract terms"
```

### 💬 **Conversational AI with Memory**
```bash
# Natural multi-turn conversations with context
# Examples:
# - User: "My name is John"
# - AI: "Nice to meet you, John!"
# - User: "What's my name?"
# - AI: "Your name is John."
# 
# Upload images and discuss them:
# - Upload product image
# - Ask: "What product is this?"
# - Follow up: "What are its main features?"
# - Later: "Compare it to the product we discussed earlier"
```

### 🎙️ **Audio Transcription & Search**
```bash
# Batch transcribe audio files with automatic truncation
./transcribe_with_truncation.sh

# Simple transcription without truncation
./transcribe_all.sh

# Python-based batch transcription with detailed options
python batch_transcribe_windows.py

# Search transcripts via web UI
# Open: http://localhost:8002/search.html

# Extract action items via API
curl -X POST http://localhost:8001/qa/action_items \
  -F "person=John"

# Ask questions about transcripts
curl -X POST http://localhost:8001/qa/ask \
  -F "question=What were the main topics discussed?"
```

## 📊 Performance

### **GPU Acceleration Results**
- **Text Generation**: ~1.2 tokens/second (RTX 5060 Ti)
- **Image Analysis**: ~1.2 tokens/second with multi-modal processing
- **Speed Improvement**: 38x faster than CPU-only processing
- **Memory Efficiency**: Auto-managed VRAM usage (~74% typical)

### **Supported Formats**
- **Documents**: PDF, TXT
- **Images**: PNG, JPG, JPEG, GIF
- **File Size**: Up to 50MB per file
- **Batch Processing**: Multiple files simultaneously

## 🔌 API Usage

### **Simple Text Query**
```python
import requests

response = requests.post('http://localhost:8000/api/v1/generate', json={
    "messages": [{"role": "user", "content": "Hello!"}]
})
print(response.json()["response"])
```

### **Image Analysis**
```python
import base64

with open("image.jpg", "rb") as f:
    image_b64 = base64.b64encode(f.read()).decode()

response = requests.post('http://localhost:8000/api/v1/generate', json={
    "messages": [{
        "role": "user",
        "content": [
            {"type": "image", "image": f"data:image/jpeg;base64,{image_b64}"},
            {"type": "text", "text": "What's in this image?"}
        ]
    }]
})
```

### **Bank Transaction Extraction**
```python
# Upload bank statement
response = requests.post('http://localhost:8000/api/v1/generate', json={
    "messages": [{
        "role": "user", 
        "content": [
            {"type": "image", "image": "data:image/pdf;base64,<base64_data>"},
            {"type": "text", "text": "Extract all transactions with dates, amounts, and descriptions in table format"}
        ]
    }],
    "max_new_tokens": 1000
})

# Export to CSV
export_response = requests.post('http://localhost:8000/api/v1/bank_export', json={
    "messages": messages,  # Include conversation with AI response
    "export_format": "csv"  # or "json"
})
# Returns CSV with columns: Date, Description, Category, Debit, Credit, Balance
```

### **Audio Transcription API**
```python
# Transcribe a single audio file
with open("audio.m4a", "rb") as f:
    response = requests.post('http://localhost:8001/transcribe',
        files={'file': f},
        data={
            'language': 'en',
            'task': 'transcribe',
            'save_transcript': 'true'
        }
    )
    
# Search transcripts semantically
response = requests.post('http://localhost:8001/transcripts/search',
    data={
        'query': 'discussion about project timeline',
        'n_results': 5
    }
)

# Extract action items
response = requests.post('http://localhost:8001/qa/action_items',
    data={'person': 'John'}  # Optional: filter by person
)

# Ask questions using RAG
response = requests.post('http://localhost:8001/qa/ask',
    data={
        'question': 'What were the key decisions made?',
        'max_context_length': 3000
    }
)
```

## 🛠️ Development

### **Run Tests**
```bash
source ~/pytorch-env/bin/activate
python test_vlm_server.py
```

### **Monitor Server**
```bash
# Health check
curl http://localhost:8000/health

# VRAM status  
curl http://localhost:8000/vram_status

# Clear VRAM
curl -X POST http://localhost:8000/clear_vram
```

### **Client Development**
```bash
# See example client implementation
python client_example.py
```

## 📖 Documentation

- **[API Documentation](API_DOCUMENTATION.md)** - Complete API reference with examples
- **[Web Interface Guide](web_interface/README.md)** - Web UI usage and customization
- **[Client Examples](client_example.py)** - Python client implementation
- **[Test Suite](test_vlm_server.py)** - Comprehensive testing framework

## 🔧 Configuration

### **Server Settings** (in `vlm_server.py`)
```python
class Config:
    MODEL_NAME = "Qwen/Qwen2.5-VL-7B-Instruct"
    MAX_NEW_TOKENS = 512
    VRAM_THRESHOLD = 0.85  # Clear cache at 85%
    HOST = "0.0.0.0"
    PORT = 8000
```

### **Web Interface** (in `web_interface/static/js/app.js`)
```javascript
constructor() {
    this.serverUrl = 'http://localhost:8000';  // VLM server URL
    // ... other settings
}
```

## 🚨 Troubleshooting

### **GPU Issues**

#### RTX 5060 Ti and newer GPUs (sm_120) Compatibility

If you get `CUDA error: no kernel image is available for execution on the device`:

1. **Ensure you're using the virtual environment:**
   ```bash
   source ~/pytorch-env/bin/activate
   ```

2. **Install PyTorch with CUDA 12.8 support:**
   ```bash
   pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
   ```

3. **Verify installation:**
   ```bash
   python -c "import torch; print(f'PyTorch: {torch.__version__}')"
   python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
   python -c "import torch; print(f'GPU: {torch.cuda.get_device_name(0)}')"
   ```

**Note**: The RTX 5060 Ti requires PyTorch 2.7.1+ with CUDA 12.8 for full compatibility.

### **Memory Issues**
```bash
# Monitor VRAM
nvidia-smi

# Clear VRAM manually
curl -X POST http://localhost:8000/clear_vram
```

### **Server Issues**
```bash
# Check server logs
tail -f server.log

# Test basic connectivity
curl http://localhost:8000/health
```

### **Audio Transcription Issues**

#### FFmpeg Not Found
```bash
# Install ffmpeg (required for audio processing)
sudo apt update && sudo apt install -y ffmpeg

# Verify installation
ffmpeg -version
```

#### GPU Not Being Used for Whisper
```bash
# Check CUDA availability
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"

# Monitor GPU usage during transcription
watch -n 1 nvidia-smi
```

#### Vector Database Connection Issues
```bash
# Check vector database status
curl http://localhost:8001/vector/stats

# Verify ChromaDB installation
pip show chromadb
```

#### Batch Transcription Tips
- Files >1 hour are automatically truncated to 60 minutes
- Use `transcribe_with_truncation.sh` for automatic truncation
- Check `transcription_results_*.json` for batch processing logs
- Monitor GPU usage: expect ~30% utilization, ~15GB VRAM for Whisper base model

## 🔐 Security Considerations

- **Production Deployment**: Use HTTPS and proper authentication
- **File Validation**: Only allow trusted file types and sizes
- **Rate Limiting**: Implement request rate limiting for production
- **Network Security**: Consider firewall rules and VPN access

## 🤝 Contributing

1. **Fork** the repository
2. **Create** feature branch: `git checkout -b feature/amazing-feature`
3. **Commit** changes: `git commit -m 'Add amazing feature'`
4. **Push** to branch: `git push origin feature/amazing-feature`
5. **Open** a Pull Request

## 📋 Roadmap

- [ ] **Video Processing** - Support for video analysis
- [ ] **Batch API** - Process multiple files in single request  
- [ ] **WebSocket Support** - Real-time streaming responses
- [ ] **Authentication** - User management and API keys
- [ ] **Cloud Deployment** - Docker and Kubernetes support
- [ ] **Model Management** - Hot-swapping different models

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Qwen Team** - For the excellent Qwen2.5-VL model
- **Hugging Face** - For transformers library and model hosting
- **PyTorch Team** - For the deep learning framework
- **FastAPI** - For the modern web framework

## 📞 Support

- **GitHub Issues**: Report bugs and feature requests
- **Documentation**: Check API_DOCUMENTATION.md for detailed usage
- **Examples**: See client_example.py for implementation patterns

---

**🚀 Ready to process your documents with AI? Get started now!**

```bash
git clone https://github.com/tuteke2023/vlm_server.git
cd vlm_server
source ~/pytorch-env/bin/activate
pip install -r requirements.txt
python vlm_server.py
```

Open `http://localhost:8080` for the web interface or use the API at `http://localhost:8000`