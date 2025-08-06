#!/usr/bin/env python3
import requests
import base64

# Read test image  
with open('test_bank_statement.png', 'rb') as f:
    image_data = base64.b64encode(f.read()).decode('utf-8')

# Simple vision test
prompt = """What do you see in this image? Please describe:
1. What type of document is this?
2. What is the first transaction date you can see?
3. What is the first credit amount shown?
4. What is the account number?"""

# Send request
response = requests.post('http://localhost:8000/api/v1/generate', json={
    'messages': [{
        'role': 'user', 
        'content': [
            {
                'type': 'text',
                'text': prompt
            },
            {
                'type': 'image_url',
                'image_url': {'url': f'data:image/png;base64,{image_data}'}
            }
        ]
    }],
    'temperature': 0.1,
    'max_tokens': 500
})

print('Response status:', response.status_code)
if response.ok:
    result = response.json()
    print('\nVLM Response:')
    print(result['response'])