#!/usr/bin/env python3
import requests
import base64
import json

# Read test image  
with open('test_bank_statement.png', 'rb') as f:
    image_data = base64.b64encode(f.read()).decode('utf-8')

print(f"Image data length: {len(image_data)} chars")
print(f"First 100 chars: {image_data[:100]}")

# Test with proper image format
messages = [{
    'role': 'user', 
    'content': [
        {
            'type': 'text',
            'text': 'What do you see in this image?'
        },
        {
            'type': 'image_url',
            'image_url': {
                'url': f'data:image/png;base64,{image_data}'
            }
        }
    ]
}]

print("\nSending request with image...")
print(f"Message structure: {json.dumps(messages[0], indent=2)[:200]}...")

# Send request
response = requests.post('http://localhost:8000/api/v1/generate', json={
    'messages': messages,
    'temperature': 0.1,
    'max_tokens': 500
})

print(f"\nResponse status: {response.status_code}")
if response.ok:
    result = response.json()
    print('\nVLM Response:')
    print(result['response'])
else:
    print(f"Error: {response.text}")