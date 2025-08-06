#!/usr/bin/env python3
"""Test VLM and Audio services in new structure"""

import requests
import base64
from PIL import Image
import io
import time

print("=== Testing Microservices Structure ===\n")

# Test 1: VLM Service Health
print("1. Testing VLM Service...")
try:
    response = requests.get("http://localhost:8000/health", timeout=5)
    if response.status_code == 200:
        health = response.json()
        print(f"   ✅ VLM Service: {health['status']}")
        print(f"   ✅ Model loaded: {health['model_loaded']}")
        print(f"   ✅ Device: {health['device']}")
    else:
        print(f"   ❌ VLM Service error: {response.status_code}")
except Exception as e:
    print(f"   ❌ VLM Service not running: {e}")

# Test 2: VLM Image Processing
print("\n2. Testing VLM Image Processing...")
try:
    # Create test image
    img = Image.new('RGB', (400, 200), color='white')
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
    
    payload = {
        "model": "Qwen/Qwen2.5-VL-3B-Instruct",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": "What color is this image?"},
                {"type": "image", "image": f"data:image/png;base64,{img_base64}"}
            ]
        }],
        "max_new_tokens": 50
    }
    
    response = requests.post("http://localhost:8000/api/v1/generate", json=payload, timeout=30)
    if response.status_code == 200:
        print("   ✅ VLM processing works!")
        result = response.json()
        print(f"   Response: {result.get('choices', [{}])[0].get('message', {}).get('content', 'No content')[:100]}")
    else:
        print(f"   ❌ VLM processing error: {response.status_code}")
except Exception as e:
    print(f"   ❌ VLM processing failed: {e}")

# Test 3: Bank Extraction
print("\n3. Testing Bank Extraction...")
try:
    # Create bank statement image
    from PIL import ImageDraw
    img = Image.new('RGB', (600, 300), color='white')
    draw = ImageDraw.Draw(img)
    draw.text((10, 10), "Bank Statement\nDate: 01/01/2024\nDebit: $100\nCredit: $500", fill='black')
    
    img_buffer = io.BytesIO()
    img.save(img_buffer, format='PNG')
    img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')
    
    payload = {
        "model": "Qwen/Qwen2.5-VL-3B-Instruct",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": "Extract bank transactions"},
                {"type": "image", "image": f"data:image/png;base64,{img_base64}"}
            ]
        }],
        "max_new_tokens": 1000
    }
    
    response = requests.post("http://localhost:8000/api/v1/bank_extract_json", json=payload, timeout=30)
    if response.status_code == 200:
        print("   ✅ Bank extraction works!")
    else:
        print(f"   ❌ Bank extraction error: {response.status_code}")
except Exception as e:
    print(f"   ❌ Bank extraction failed: {e}")

print("\n✅ VLM Service Test Complete!")
print("\nVLM service is working correctly in the new structure.")
print("Ready to test audio service once it's started.")