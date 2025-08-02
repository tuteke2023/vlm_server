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
- 🏦 **Bank Transaction Extraction** - Parse statements with editable table display
- 📊 **Interactive Tables** - Edit, add, and delete transactions in real-time
- 💾 **Export Options** - Save as CSV, Excel, or JSON for AI training
- 📄 **Document Summarization** - AI-powered summaries and insights  
- 🖼️ **Image Analysis** - Object detection, OCR, and description
- 📝 **Text Extraction** - Advanced OCR with formatting preservation
- ❓ **Custom Queries** - Ask anything about uploaded documents
- 🔄 **Model Selection** - Switch between 3B/7B models for different VRAM needs

## 📁 Project Structure

```
vlm_server/
├── vlm_server.py                      # Main FastAPI server with multi-model support
├── requirements.txt                   # Dependencies
├── client_example.py                  # Python client example
├── test_vlm_server.py                 # Comprehensive test suite
├── test_chat_interface.py             # Chat interface API tests  
├── test_conversation_context.py       # Conversation memory tests
├── API_DOCUMENTATION.md               # Complete API reference
├── web_interface/                     # Dual Web UI
│   ├── index.html                    # Document processing interface
│   ├── chat.html                     # Conversational AI interface
│   ├── static/css/style.css          # Shared modern styling
│   ├── static/js/app.js              # Document processing logic
│   ├── static/js/chat.js             # Chat interface with context memory
│   ├── server.py                     # Development web server
│   └── README.md                     # Web interface docs
└── README.md                         # This file
```

## 🔧 Quick Start

### Prerequisites

- **Python 3.8+**
- **CUDA-capable GPU** (recommended: 16GB+ VRAM)
- **NVIDIA drivers** and CUDA toolkit

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
```

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

### 4. Start Web Interface

```bash
# In a new terminal
cd web_interface
python3 -m http.server 8080
```

## 🌐 **Access the Interfaces**

- **💬 Chat Interface**: `http://localhost:8080/chat.html` - Conversational AI with memory
- **🔧 Document Processing**: `http://localhost:8080/index.html` - Specialized document tools
- **🔗 Navigation**: Both interfaces have navigation links between them

## 🎯 Use Cases

### 💳 **Bank Statement Processing with Interactive Tables**
```bash
# Upload bank statement PDF or image
# AI extracts transactions into editable table format
# Features:
# - Edit any transaction field (date, description, amount, category)
# - Add new transactions with "Add Row" button
# - Delete unwanted transactions
# - Auto-categorization of transactions
# - Visual indicators for modified rows
# - Export to CSV or Excel formats
# - Save modifications as JSON for AI training
# Output: Interactive table with totals and export options
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
```bash
# Check CUDA support
python -c "import torch; print(torch.cuda.is_available())"

# Check GPU compatibility
python -c "import torch; print(torch.cuda.get_arch_list())"

# Expected: ['sm_75', 'sm_80', 'sm_86', 'sm_90', 'sm_100', 'sm_120']
```

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

### ✅ Completed Features
- [x] **Conversation Memory** - Full context awareness in chat interface
- [x] **Multi-Model Support** - Switch between 3B/7B models
- [x] **CUDA Stability** - Fixed device-side assert errors
- [x] **Interactive Bank Tables** - Editable transaction tables with CSV/Excel export
- [x] **AI Training Data Export** - Save user modifications for model improvement

### 🚧 Upcoming Features
- [ ] **Video Processing** - Support for video analysis
- [ ] **Batch API** - Process multiple files in single request  
- [ ] **WebSocket Support** - Real-time streaming responses
- [ ] **Authentication** - User management and API keys
- [ ] **Cloud Deployment** - Docker and Kubernetes support
- [ ] **Persistent Storage** - Save chat history and edited tables

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