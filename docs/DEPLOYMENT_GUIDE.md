# VLM Server Deployment Guide

This guide covers deploying the VLM Server in production environments.

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Environment Setup](#environment-setup)
3. [Configuration](#configuration)
4. [Deployment Steps](#deployment-steps)
5. [Performance Tuning](#performance-tuning)
6. [Monitoring](#monitoring)
7. [Security Considerations](#security-considerations)
8. [Troubleshooting](#troubleshooting)

## System Requirements

### Hardware Requirements
- **GPU**: NVIDIA GPU with at least 8GB VRAM
  - RTX 3080 or better recommended
  - RTX 5060 Ti requires CUDA 12.8 (see GPU Compatibility section)
- **RAM**: 16GB minimum, 32GB recommended
- **Storage**: 50GB free space for models and cache
- **CPU**: 8+ cores recommended

### Software Requirements
- Ubuntu 20.04+ or similar Linux distribution
- Python 3.9+
- CUDA 11.8+ (12.8 for newer GPUs)
- Docker (optional, for containerized deployment)

## Environment Setup

### 1. Create Virtual Environment
```bash
python3 -m venv ~/vlm-env
source ~/vlm-env/bin/activate
```

### 2. Install PyTorch with GPU Support

For older GPUs (CUDA 11.8):
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

For newer GPUs (CUDA 12.8, RTX 5060 Ti+):
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
```

### 3. Install Dependencies
```bash
cd services/vlm
pip install -r requirements.txt
```

### 4. Set Up Environment Variables
Create a `.env` file in the project root:
```env
# OpenAI API (optional)
OPENAI_API_KEY=sk-...

# Server Configuration
VLM_HOST=0.0.0.0
VLM_PORT=8000
WEB_HOST=0.0.0.0
WEB_PORT=8080

# Model Configuration
DEFAULT_MODEL=Qwen/Qwen2.5-VL-3B-Instruct
MAX_VRAM_USAGE=0.85

# Cache Configuration
CACHE_SIZE=100
CACHE_TTL=900

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/vlm_server.log
```

## Configuration

### Model Selection
Edit `services/vlm/vlm_server.py` to set default model:
```python
MODEL_NAME = "Qwen/Qwen2.5-VL-3B-Instruct"  # 6.5GB VRAM
# OR
MODEL_NAME = "Qwen/Qwen2.5-VL-7B-Instruct"  # 15.5GB VRAM
```

### VRAM Management
Configure VRAM thresholds:
```python
VRAM_THRESHOLD = 0.75  # Clear cache when VRAM usage exceeds 75%
VRAM_SAFETY_LIMIT = 0.90  # Refuse processing if VRAM would exceed 90%
```

## Deployment Steps

### Option 1: Direct Deployment

1. **Start the VLM Server**:
```bash
cd services/vlm
nohup python vlm_server.py > vlm_server.log 2>&1 &
echo $! > vlm_server.pid
```

2. **Start the Web Interface**:
```bash
cd services/vlm/web_interface
nohup python server.py > web_server.log 2>&1 &
echo $! > web_server.pid
```

3. **Use systemd for Auto-restart**:
Create `/etc/systemd/system/vlm-server.service`:
```ini
[Unit]
Description=VLM Server
After=network.target

[Service]
Type=simple
User=vlm-user
WorkingDirectory=/opt/vlm_server/services/vlm
Environment="PATH=/home/vlm-user/vlm-env/bin"
ExecStart=/home/vlm-user/vlm-env/bin/python vlm_server.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable vlm-server
sudo systemctl start vlm-server
```

### Option 2: Docker Deployment

1. **Create Dockerfile**:
```dockerfile
FROM nvidia/cuda:12.8.0-runtime-ubuntu22.04

RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["python3", "services/vlm/vlm_server.py"]
```

2. **Build and Run**:
```bash
docker build -t vlm-server .
docker run --gpus all -p 8000:8000 -v $(pwd)/.env:/app/.env vlm-server
```

### Option 3: Using the Start Scripts

Use the provided scripts:
```bash
./scripts/start_all.sh  # Starts both VLM and web servers
```

## Performance Tuning

### 1. Enable Response Caching
The server includes built-in response caching. Ensure it's enabled:
```python
# In vlm_server.py, uncomment cache usage:
cache = get_cache()
cached_result = cache.get(request.messages, endpoint_name)
```

### 2. Optimize Model Loading
- Use 8-bit quantization for larger models on limited VRAM
- Adjust `max_memory` parameter for optimal VRAM usage

### 3. Batch Processing
For high-volume deployments, implement request batching:
```python
MAX_BATCH_SIZE = 4
BATCH_TIMEOUT = 100  # ms
```

### 4. Load Balancing
For multiple GPUs, use separate instances with a load balancer:
```nginx
upstream vlm_backends {
    server localhost:8000;
    server localhost:8001;
}
```

## Monitoring

### 1. Health Checks
Monitor server health:
```bash
curl http://localhost:8000/health
```

### 2. VRAM Monitoring
Check VRAM usage:
```bash
curl http://localhost:8000/vram_status
```

### 3. Prometheus Integration
Add Prometheus metrics:
```python
from prometheus_client import Counter, Histogram, Gauge

request_count = Counter('vlm_requests_total', 'Total requests')
request_duration = Histogram('vlm_request_duration_seconds', 'Request duration')
vram_usage = Gauge('vlm_vram_usage_bytes', 'VRAM usage in bytes')
```

### 4. Logging
Configure structured logging:
```python
import structlog

logger = structlog.get_logger()
logger.info("request_processed", 
    endpoint=endpoint,
    duration=duration,
    provider=provider,
    status="success"
)
```

## Security Considerations

### 1. API Authentication
Implement API key authentication:
```python
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

@app.middleware("http")
async def validate_api_key(request: Request, call_next):
    if request.url.path.startswith("/api/"):
        api_key = request.headers.get("X-API-Key")
        if api_key != os.getenv("API_KEY"):
            return JSONResponse(status_code=403, content={"error": "Invalid API key"})
    return await call_next(request)
```

### 2. Rate Limiting
Add rate limiting:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/generate")
@limiter.limit("10/minute")
async def generate(request: Request):
    ...
```

### 3. Input Validation
- Limit maximum image size
- Validate base64 image data
- Sanitize text inputs

### 4. HTTPS Configuration
Use a reverse proxy with SSL:
```nginx
server {
    listen 443 ssl;
    server_name vlm.example.com;
    
    ssl_certificate /etc/ssl/certs/vlm.crt;
    ssl_certificate_key /etc/ssl/private/vlm.key;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Troubleshooting

### Common Issues

1. **CUDA Out of Memory**
   - Reduce batch size
   - Use smaller model (3B instead of 7B)
   - Enable VRAM monitoring and auto-cleanup

2. **Slow Response Times**
   - Check if using optimized extractor
   - Enable response caching
   - Monitor CPU/GPU utilization

3. **Model Loading Failures**
   - Verify CUDA installation: `nvidia-smi`
   - Check PyTorch CUDA: `python -c "import torch; print(torch.cuda.is_available())"`
   - Ensure sufficient disk space for model download

4. **API Errors**
   - Check server logs: `tail -f vlm_server.log`
   - Verify environment variables are loaded
   - Test endpoints individually

### Debug Mode
Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Performance Profiling
Use built-in profiler:
```bash
python performance_profile.py
```

## Maintenance

### Regular Tasks
1. **Log Rotation**: Configure logrotate for log files
2. **Model Updates**: Check for model updates monthly
3. **Security Updates**: Keep dependencies updated
4. **Backup**: Regular backup of transaction corrections database

### Scaling Considerations
- Horizontal scaling: Multiple instances behind load balancer
- Vertical scaling: Upgrade to larger GPU (A100, H100)
- Hybrid approach: Use OpenAI for overflow traffic

## Conclusion

This deployment guide covers the essential steps for production deployment. Adjust configurations based on your specific requirements and workload patterns. For additional support, refer to the project documentation or raise an issue on GitHub.