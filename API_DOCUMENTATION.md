# VLM Server API Documentation

This document describes how to connect to and use the Vision Language Model (VLM) server API.

## Overview

The VLM server provides a REST API for interacting with the Qwen2.5-VL-7B-Instruct model. It supports:
- Text generation with image and video inputs
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

### 3. Generate Response (Main Endpoint)

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

### Example 3: Multi-turn Conversation

```python
data = {
    "messages": [
        {
            "role": "user",
            "content": "Hello, can you help me analyze some images?"
        },
        {
            "role": "assistant",
            "content": "Of course! I'd be happy to help you analyze images. Please share the images you'd like me to look at."
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "image": "https://example.com/chart.png"
                },
                {
                    "type": "text",
                    "text": "What kind of chart is this and what does it show?"
                }
            ]
        }
    ]
}

response = requests.post(url, json=data)
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