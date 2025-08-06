#!/usr/bin/env python3
"""Test VLM server with pytorch-env"""

import requests
import base64
from PIL import Image
import io

# Check server health
print("Checking server health...")
try:
    response = requests.get("http://localhost:8000/health")
    print(f"Health check: {response.json()}")
except Exception as e:
    print(f"Health check failed: {e}")

# Create test image
img = Image.new('RGB', (400, 200), color='white')
img_buffer = io.BytesIO()
img.save(img_buffer, format='PNG')
img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')

# Test basic generation
print("\nTesting basic generation...")
url = "http://localhost:8000/api/v1/generate"
payload = {
    "model": "Qwen/Qwen2.5-VL-3B-Instruct",
    "messages": [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What color is this image?"},
                {"type": "image", "image": f"data:image/png;base64,{img_base64}"}
            ]
        }
    ],
    "max_new_tokens": 50
}

try:
    response = requests.post(url, json=payload, timeout=30)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("✅ SUCCESS! PyTorch CUDA 12.8 is working!")
        print(f"Response: {response.json()['content']}")
    else:
        print(f"❌ Error: {response.text}")
except Exception as e:
    print(f"❌ Request failed: {e}")