#!/usr/bin/env python3
"""Test bank extraction with patched server"""

import requests
import base64
from PIL import Image
import io

# Create a simple test image
img = Image.new('RGB', (400, 200), color='white')
img_buffer = io.BytesIO()
img.save(img_buffer, format='PNG')
img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')

# Test basic generation first
print("Testing basic generation...")
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
    response = requests.post(url, json=payload, timeout=30)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("✅ Success! Basic generation works")
        print(f"Response: {response.json()['content']}")
    else:
        print(f"❌ Error: {response.text}")
except Exception as e:
    print(f"❌ Request failed: {e}")

# Test bank extraction
print("\nTesting bank extraction...")
url = "http://localhost:8000/api/v1/bank_extract_json"
payload = {
    "model": "Qwen/Qwen2.5-VL-3B-Instruct",
    "messages": [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Extract bank transactions"},
                {"type": "image", "image": f"data:image/png;base64,{img_base64}"}
            ]
        }
    ],
    "max_new_tokens": 1000
}

try:
    response = requests.post(url, json=payload, timeout=60)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("✅ Success! Bank extraction works")
        result = response.json()
        print(f"Transactions found: {len(result.get('transactions', []))}")
    else:
        print(f"❌ Error: {response.text}")
except Exception as e:
    print(f"❌ Request failed: {e}")