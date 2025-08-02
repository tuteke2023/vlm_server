# VLM Server - Qwen2.5-VL-7B-Instruct API Server

A production-ready Vision Language Model (VLM) server that provides an HTTP API for the Qwen2.5-VL-7B-Instruct model with automatic VRAM management.

## Features

- 🚀 **FastAPI-based REST API** - High-performance async server
- 🖼️ **Multi-modal Support** - Process text, images, and videos
- 💾 **Automatic VRAM Management** - Prevents out-of-memory crashes
- 📊 **Real-time Monitoring** - Track VRAM usage and server health
- 🔄 **Async Processing** - Handle multiple requests efficiently
- 📝 **Comprehensive Logging** - Detailed request and error logging

## Quick Start

### Prerequisites

- Python 3.8+
- CUDA-capable GPU (recommended: 16GB+ VRAM)
- NVIDIA drivers and CUDA toolkit

### Installation

1. Clone the repository:
```bash
git clone <your-repo>
cd vlm_server
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Start the server:
```bash
python vlm_server.py
```

The server will start on `http://localhost:8000`

## Basic Usage

### Using Python

```python
import requests

# Simple text query
response = requests.post(
    "http://localhost:8000/api/v1/generate",
    json={
        "messages": [{
            "role": "user",
            "content": "What is machine learning?"
        }]
    }
)
print(response.json()["response"])

# Image analysis
response = requests.post(
    "http://localhost:8000/api/v1/generate",
    json={
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image", "image": "https://example.com/image.jpg"},
                {"type": "text", "text": "What's in this image?"}
            ]
        }]
    }
)
print(response.json()["response"])
```

### Using cURL

```bash
# Check server health
curl http://localhost:8000/health

# Generate text
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello!"}]}'
```

## API Endpoints

- `GET /` - Server info and available endpoints
- `GET /health` - Health check
- `GET /vram_status` - Current VRAM usage
- `POST /api/v1/generate` - Generate response
- `POST /clear_vram` - Manually clear VRAM

## Configuration

Modify the `Config` class in `vlm_server.py`:

```python
class Config:
    MODEL_NAME = "Qwen/Qwen2.5-VL-7B-Instruct"
    MAX_NEW_TOKENS = 512
    VRAM_THRESHOLD = 0.85  # Clear cache at 85% usage
    HOST = "0.0.0.0"
    PORT = 8000
```

## VRAM Management

The server automatically monitors VRAM usage and clears cache when usage exceeds 85% (configurable). This prevents out-of-memory errors during prolonged usage.

## Examples

See `client_example.py` for a complete example client implementation, or check `API_DOCUMENTATION.md` for detailed API usage examples.

## Documentation

- `API_DOCUMENTATION.md` - Complete API reference with examples
- `client_example.py` - Python client implementation
- `vlm_server.py` - Main server implementation

## Performance Tips

1. **GPU Memory**: The model requires ~14GB VRAM. Ensure you have at least 16GB for comfortable operation.
2. **Batch Size**: Process requests sequentially to avoid memory issues.
3. **Image Size**: Resize large images before sending to improve performance.

## Troubleshooting

### Out of Memory Errors
- Reduce `max_new_tokens`
- Enable automatic VRAM clearing
- Process smaller images

### Slow Performance
- Verify CUDA is available: `torch.cuda.is_available()`
- Check GPU usage: `nvidia-smi`
- Monitor server logs for warnings

### Connection Issues
- Check firewall settings
- Verify server is running
- Ensure correct host/port configuration

## Security Notes

- The server binds to all interfaces (0.0.0.0) by default
- No authentication is implemented
- For production use, consider:
  - Adding authentication
  - Using HTTPS
  - Implementing rate limiting
  - Running behind a reverse proxy

## License

This server implementation is provided as-is. The Qwen2.5-VL model has its own license terms - please check the model card on Hugging Face.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review server logs
3. Check API documentation
4. Open an issue with detailed error information