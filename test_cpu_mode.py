#!/usr/bin/env python3
"""Test bank extraction in CPU mode"""

import requests
import base64
from PIL import Image
import io

# Create a simple test image with text
img = Image.new('RGB', (400, 200), color='white')
from PIL import ImageDraw, ImageFont
draw = ImageDraw.Draw(img)

# Try to use a default font
try:
    # Try to get a larger font
    font = ImageFont.load_default()
except:
    font = None

# Draw some bank-like text
text = "Bank Statement\nDate: 2025-01-01\nDebit: $100.00\nCredit: $500.00"
draw.multiline_text((10, 10), text, fill='black', font=font)

# Convert to base64
img_buffer = io.BytesIO()
img.save(img_buffer, format='PNG')
img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')

# Test the bank extraction API
url = "http://localhost:8000/api/v1/bank_extract_json"
payload = {
    "image": f"data:image/png;base64,{img_base64}"
}

print("Testing bank extraction in CPU mode...")
try:
    response = requests.post(url, json=payload, timeout=60)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("Success! Response:")
        print(response.json())
    else:
        print("Error:", response.text)
except Exception as e:
    print(f"Request failed: {e}")

# Also test basic generation
print("\nTesting basic generation...")
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
    response = requests.post(url, json=payload, timeout=60)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("Success! Response:")
        print(response.json()['content'])
    else:
        print("Error:", response.text)
except Exception as e:
    print(f"Request failed: {e}")