#!/usr/bin/env python3
import requests
import base64
import json

# Read test image
with open('test_bank_statement.png', 'rb') as f:
    image_data = base64.b64encode(f.read()).decode('utf-8')

# More specific prompt
prompt = """Look at this bank statement carefully. Extract the transactions that show:
- Date (e.g., 04-Apr-25)
- Description (e.g., Direct Credit 400937 DB RESULTS)
- Debit amount (if money went out)
- Credit amount (if money came in) 
- Balance (the running balance)

Output as a table with columns: Date | Description | Debit | Credit | Balance

IMPORTANT RULES:
1. Copy the EXACT amounts from the statement - don't change them
2. Direct Credit = put amount in Credit column only
3. Transfer to = put amount in Debit column only  
4. Transfer from = put amount in Credit column only
5. Include the decimal places (e.g., 1,750.00 not 1,750)

Start with the first transaction on 04-Apr-25."""

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
    'max_tokens': 2000
})

print('Response status:', response.status_code)
if response.ok:
    result = response.json()
    print('\nVLM Response:')
    print(result['response'])