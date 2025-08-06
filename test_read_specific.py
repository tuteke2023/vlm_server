#!/usr/bin/env python3
import requests
import base64

# Read test image  
with open('test_bank_statement.png', 'rb') as f:
    image_data = base64.b64encode(f.read()).decode('utf-8')

# Very specific question
prompt = """Look at the first transaction dated 04-Apr-25 in this bank statement.
What is the EXACT credit amount shown? 
Read it very carefully - is it 1,750.00 or 17,765.00 or something else?
Tell me exactly what number you see in the Credit column for that transaction."""

messages = [{
    'role': 'user', 
    'content': [
        {
            'type': 'text',
            'text': prompt
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
    'max_tokens': 200
})

print(f"Response status: {response.status_code}")
if response.ok:
    result = response.json()
    print('\nVLM Response:')
    print(result['response'])