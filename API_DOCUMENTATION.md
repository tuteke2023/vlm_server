# VLM Server API Documentation

This document describes how to connect to and use the Vision Language Model (VLM) server API.

## Overview

The VLM server provides a REST API for interacting with Qwen2.5-VL models (3B/7B-Instruct). It supports:
- Text generation with image and video inputs
- Multi-model support with hot-swapping
- Conversation context for multi-turn dialogues
- Automatic VRAM management
- Health monitoring
- Async request processing

## Server Setup

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Start the server:
```bash
python vlm_server.py
```

The server will start on `http://0.0.0.0:8000` by default.

### Configuration

You can modify the server configuration in the `Config` class in `vlm_server.py`:
- `PORT`: Server port (default: 8000)
- `HOST`: Server host (default: 0.0.0.0)
- `MAX_NEW_TOKENS`: Default max tokens to generate (default: 512)
- `VRAM_THRESHOLD`: VRAM usage threshold for automatic clearing (default: 0.85)

## API Endpoints

### 1. Health Check

**GET** `/health`

Check if the server is running and model is loaded.

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "device": "cuda"
}
```

### 2. VRAM Status

**GET** `/vram_status`

Get current VRAM usage statistics.

```bash
curl http://localhost:8000/vram_status
```

Response:
```json
{
  "allocated_gb": 12.5,
  "reserved_gb": 14.0,
  "free_gb": 11.5,
  "total_gb": 24.0,
  "usage_percentage": 52.1
}
```

### 3. Available Models

**GET** `/available_models`

Get list of available models that can be loaded.

```bash
curl http://localhost:8000/available_models
```

Response:
```json
{
  "models": {
    "Qwen/Qwen2.5-VL-7B-Instruct": {
      "name": "Qwen2.5-VL-7B-Instruct",
      "size": "7B",
      "vram_gb": 15.5,
      "description": "High quality, high VRAM usage"
    },
    "Qwen/Qwen2.5-VL-3B-Instruct": {
      "name": "Qwen2.5-VL-3B-Instruct",
      "size": "3B",
      "vram_gb": 6.5,
      "description": "Good quality, lower VRAM usage"
    }
  },
  "current_model": "Qwen/Qwen2.5-VL-3B-Instruct"
}
```

### 4. Reload Model

**POST** `/reload_model`

Switch to a different model.

```bash
curl -X POST http://localhost:8000/reload_model \
  -H "Content-Type: application/json" \
  -d '{"model_name": "Qwen/Qwen2.5-VL-7B-Instruct"}'
```

Response:
```json
{
  "message": "Model reloaded successfully",
  "model": "Qwen/Qwen2.5-VL-7B-Instruct",
  "vram_status": {
    "allocated_gb": 15.2,
    "usage_percentage": 63.3
  }
}
```

### 5. Generate Response (Main Endpoint)

**POST** `/api/v1/generate`

Generate a response from the VLM model with text, image, and/or video inputs.

#### Request Body Schema

```json
{
  "messages": [
    {
      "role": "user",
      "content": "string or array of content items"
    }
  ],
  "max_new_tokens": 512,  // optional
  "temperature": 0.7,     // optional
  "top_p": 0.9           // optional
}
```

#### Content Types

Content can be either:
1. A simple string (text only)
2. An array of content items with different types

Content item types:
- `text`: Plain text content
- `image`: Image input (supports URL, base64, or file path)
- `video`: Video input (supports URL or file path)

## Usage Examples

### Example 1: Text-only Request

```python
import requests

url = "http://localhost:8000/api/v1/generate"
data = {
    "messages": [
        {
            "role": "user",
            "content": "What is the capital of France?"
        }
    ]
}

response = requests.post(url, json=data)
print(response.json()["response"])
```

### Example 2: Image + Text Request

```python
import requests
import base64

# Method 1: Using image URL
data = {
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "image": "https://example.com/image.jpg"
                },
                {
                    "type": "text",
                    "text": "What's in this image?"
                }
            ]
        }
    ]
}

response = requests.post(url, json=data)
print(response.json()["response"])

# Method 2: Using base64 encoded image
with open("local_image.jpg", "rb") as f:
    image_base64 = base64.b64encode(f.read()).decode()

data = {
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "image": f"data:image/jpeg;base64,{image_base64}"
                },
                {
                    "type": "text",
                    "text": "Describe this image in detail"
                }
            ]
        }
    ],
    "max_new_tokens": 1024
}

response = requests.post(url, json=data)
print(response.json())
```

### Example 3: Multi-turn Conversation with Context Memory

```python
# The API maintains context across messages in the same request
data = {
    "messages": [
        {
            "role": "user",
            "content": "My name is Alice and I'm working on a data visualization project."
        },
        {
            "role": "assistant",
            "content": "Hello Alice! It's great to meet you. I'd be happy to help with your data visualization project. What kind of visualizations are you working on?"
        },
        {
            "role": "user",
            "content": "What's my name and what am I working on?"
        }
    ]
}

response = requests.post(url, json=data)
# The model will remember: "Your name is Alice and you're working on a data visualization project."

# Example with images in conversation
data = {
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "image": "https://example.com/chart1.png"
                },
                {
                    "type": "text",
                    "text": "This is my first chart attempt."
                }
            ]
        },
        {
            "role": "assistant",
            "content": "I can see your bar chart showing sales data across different regions. The visualization uses blue bars and has clear axis labels. What specific aspects would you like to improve?"
        },
        {
            "role": "user",
            "content": "Can you remind me what type of chart I showed you and what it was displaying?"
        }
    ]
}

response = requests.post(url, json=data)
# The model remembers the previous image and discussion
```

### Example 4: Using cURL

```bash
# Simple text request
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": "Explain quantum computing in simple terms"
      }
    ]
  }'

# Image analysis request
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "user",
        "content": [
          {
            "type": "image",
            "image": "https://example.com/diagram.png"
          },
          {
            "type": "text",
            "text": "Explain this diagram"
          }
        ]
      }
    ],
    "max_new_tokens": 256
  }'
```

### Example 5: JavaScript/Node.js Client

```javascript
const axios = require('axios');

async function queryVLM(messages, options = {}) {
    const response = await axios.post('http://localhost:8000/api/v1/generate', {
        messages: messages,
        max_new_tokens: options.maxTokens || 512,
        temperature: options.temperature || 0.7,
        top_p: options.topP || 0.9
    });
    
    return response.data;
}

// Example usage
async function main() {
    // Text-only query
    const result1 = await queryVLM([
        {
            role: "user",
            content: "What are the benefits of renewable energy?"
        }
    ]);
    console.log(result1.response);
    
    // Image analysis
    const result2 = await queryVLM([
        {
            role: "user",
            content: [
                {
                    type: "image",
                    image: "https://example.com/solar-panel.jpg"
                },
                {
                    type: "text",
                    text: "What type of renewable energy system is shown here?"
                }
            ]
        }
    ], { maxTokens: 1024 });
    console.log(result2.response);
}

main().catch(console.error);
```

## Response Format

All successful responses from the `/api/v1/generate` endpoint follow this format:

```json
{
  "response": "The generated text response from the model",
  "usage": {
    "input_tokens": 125,
    "output_tokens": 89,
    "total_tokens": 214
  },
  "processing_time": 2.34
}
```

## Error Handling

The API returns appropriate HTTP status codes:

- `200`: Success
- `400`: Bad Request (invalid input)
- `503`: Service Unavailable (model not loaded)
- `500`: Internal Server Error

Error response format:
```json
{
  "detail": "Error description"
}
```

## VRAM Management

The server automatically monitors VRAM usage and clears the cache when usage exceeds the threshold (85% by default). You can also manually trigger VRAM clearing:

**POST** `/clear_vram`

```bash
curl -X POST http://localhost:8000/clear_vram
```

## Performance Tips

1. **Batch Processing**: For multiple independent queries, send them sequentially rather than concurrently to avoid VRAM issues.

2. **Image Optimization**: 
   - Resize large images before sending to reduce processing time
   - Use JPEG format for photos, PNG for diagrams
   - Base64 encoding increases payload size by ~33%

3. **Token Limits**: Set appropriate `max_new_tokens` based on your needs to avoid unnecessary computation.

4. **Connection Pooling**: When making multiple requests, use connection pooling to reduce overhead:

```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
retry = Retry(total=3, backoff_factor=0.3)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)

# Use session for all requests
response = session.post(url, json=data)
```

## Security Considerations

1. The server binds to `0.0.0.0` by default, making it accessible from any network interface. For production use, consider:
   - Binding to `127.0.0.1` for local-only access
   - Using a reverse proxy (nginx, Apache) with proper security headers
   - Implementing authentication/authorization

2. Input validation is performed, but consider additional measures:
   - Rate limiting
   - Request size limits
   - Input sanitization for file paths

3. HTTPS is recommended for production deployments to encrypt data in transit.

## Troubleshooting

### Common Issues

1. **Out of Memory (OOM)**
   - Reduce `max_new_tokens`
   - Process smaller images
   - Check VRAM status endpoint
   - Manually clear VRAM

2. **Slow Response Times**
   - Check if running on CPU instead of GPU
   - Monitor server logs for warnings
   - Consider upgrading to faster GPU

3. **Connection Refused**
   - Verify server is running
   - Check firewall settings
   - Ensure correct host/port

### Debug Mode

For detailed logging, modify the logging level in `vlm_server.py`:

```python
logging.basicConfig(level=logging.DEBUG)
```

## Web Interfaces

The VLM server includes two web interfaces:

### Chat Interface (`/chat.html`)
- **Purpose**: Interactive conversational AI with full context memory
- **Features**:
  - WhatsApp-style chat UI
  - Maintains conversation history throughout the session
  - Drag & drop image support
  - Real-time VRAM monitoring
  - Export conversation as JSON
  - Visual context indicators showing message count

### Document Processing Interface (`/index.html`)
- **Purpose**: Specialized tools for document analysis
- **Features**:
  - Bank transaction extraction
  - Document summarization
  - Image analysis and OCR
  - Custom queries
  - Model switching (3B/7B)

Both interfaces connect to the same API endpoints and support seamless navigation between them.

## Client Libraries

While you can use any HTTP client, here are some recommended libraries:

- **Python**: `requests`, `httpx`, `aiohttp`
- **JavaScript**: `axios`, `fetch`, `node-fetch`
- **Go**: `net/http`, `resty`
- **Java**: `OkHttp`, `Apache HttpClient`
- **C#**: `HttpClient`, `RestSharp`

## Rate Limiting

The server does not implement rate limiting by default. For production use, consider:
- Using a reverse proxy with rate limiting
- Implementing token bucket algorithm
- Adding API key authentication

## Monitoring

For production deployments, consider monitoring:
- Request latency
- VRAM usage trends
- Error rates
- Queue sizes

You can integrate with monitoring tools like Prometheus, Grafana, or DataDog using the provided endpoints.