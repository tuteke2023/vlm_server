#!/usr/bin/env python3
"""Test script to diagnose CUDA error"""

import torch
import numpy as np
import requests
import base64
from PIL import Image
import io

print("=== CUDA Diagnostics ===")
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"CUDA version: {torch.version.cuda}")
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"GPU Capability: {torch.cuda.get_device_capability(0)}")

print("\n=== Testing Basic CUDA Operations ===")
try:
    # Test basic tensor operations
    a = torch.tensor([1, 2, 3], device='cuda')
    b = torch.tensor([4, 5, 6], device='cuda')
    c = a + b
    print(f"Basic addition: {c}")
    
    # Test the specific operation that's failing
    print("\n=== Testing torch.isin ===")
    elements = torch.tensor([1, 2, 3], device='cuda')
    test_elements = torch.tensor([2, 4], device='cuda')
    result = torch.isin(elements, test_elements)
    print(f"torch.isin result: {result}")
    
except Exception as e:
    print(f"CUDA operation failed: {e}")

print("\n=== Testing VLM Server ===")
# Create a simple test image
img = Image.new('RGB', (100, 100), color='white')
img_buffer = io.BytesIO()
img.save(img_buffer, format='PNG')
img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')

# Test the API
url = "http://localhost:8000/api/v1/generate"
payload = {
    "model": "Qwen/Qwen2.5-VL-3B-Instruct",
    "messages": [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What is in this image?"},
                {"type": "image", "image": f"data:image/png;base64,{img_base64}"}
            ]
        }
    ],
    "max_new_tokens": 50
}

try:
    response = requests.post(url, json=payload)
    print(f"API Response Status: {response.status_code}")
    if response.status_code == 200:
        print(f"API Response: {response.json()}")
    else:
        print(f"API Error: {response.text}")
except Exception as e:
    print(f"API request failed: {e}")

print("\n=== Checking NumPy Version ===")
print(f"NumPy version: {np.__version__}")