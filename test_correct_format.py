#!/usr/bin/env python3
import requests
import base64

# Read test image  
with open('test_bank_statement.png', 'rb') as f:
    image_data = base64.b64encode(f.read()).decode('utf-8')

# Use correct format matching VLM server expectations
messages = [{
    'role': 'user', 
    'content': [
        {
            'type': 'text',
            'text': 'What do you see in this image? Describe the first few transactions.'
        },
        {
            'type': 'image',
            'image': f'data:image/png;base64,{image_data}'
        }
    ]
}]

# Send request
response = requests.post('http://localhost:8000/api/v1/generate', json={
    'messages': messages,
    'temperature': 0.1,
    'max_tokens': 500
})

print(f"Response status: {response.status_code}")
if response.ok:
    result = response.json()
    print('\nVLM Response:')
    print(result['response'])
else:
    print(f"Error: {response.text}")