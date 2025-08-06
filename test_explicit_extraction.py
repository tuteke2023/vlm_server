#!/usr/bin/env python3
import requests
import base64
import json

# Read test image  
with open('test_bank_statement.png', 'rb') as f:
    image_data = base64.b64encode(f.read()).decode('utf-8')

# Ultra-specific prompt
prompt = """This is a bank statement showing transactions. I can see:

First transaction: 04-Apr-25, Direct Credit 400937 DB RESULTS, Credit: 1,750.00, Balance: 1,750.00
Second transaction: 05-Apr-25, Transfer to xx5330 CommBank app Loan850.00, Debit: 850.00, Balance: 900.00
Third transaction: 05-Apr-25, Transfer to CBA A/c CommBank app, Debit: 900.00, Balance: 0.00

Please extract ALL transactions from this statement in a table format.
Use | as delimiter. Include Date | Description | Debit | Credit | Balance

Rules:
- Direct Credit = amount goes in Credit column (leave Debit empty)
- Transfer to = amount goes in Debit column (leave Credit empty) 
- Transfer from = amount goes in Credit column (leave Debit empty)
- Copy exact amounts including decimals"""

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
    table_output = result['response']
    print('\nVLM Response:')
    print(table_output)
    
    # Now let's check if it actually read the statement
    if "17,765" in table_output or "17765" in table_output:
        print("\n✓ VLM correctly read the first credit amount of 17,765.00")
    else:
        print("\n✗ VLM did not extract the correct amount (should be 17,765.00)")
        
    if "8,000" in table_output or "8000" in table_output:
        print("✓ VLM correctly read the first debit amount of 8,000.00")
    else:
        print("✗ VLM did not extract the correct debit amount (should be 8,000.00)")