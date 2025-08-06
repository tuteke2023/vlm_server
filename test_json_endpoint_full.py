#!/usr/bin/env python3
"""Test JSON endpoint with chequing statement"""

import requests
import base64

# Read the chequing statement
with open('tests/BankStatementChequing.png', 'rb') as f:
    image_data = base64.b64encode(f.read()).decode('utf-8')

messages = [{
    'role': 'user',
    'content': [
        {
            'type': 'text',
            'text': 'Extract bank transactions'
        },
        {
            'type': 'image',
            'image': f'data:image/png;base64,{image_data}'
        }
    ]
}]

# Test JSON endpoint
response = requests.post('http://localhost:8000/api/v1/bank_extract_json', json={
    'messages': messages,
    'temperature': 0.1,
    'max_new_tokens': 4096  # Fixed parameter name
})

print(f"Response status: {response.status_code}")
if response.ok:
    result = response.json()
    if result.get('status') == 'success' and 'data' in result:
        data = result['data']
        trans = data.get('transactions', [])
        
        print(f"\nExtracted {len(trans)} transactions (should be 19)")
        print(f"Total debits: ${data.get('total_debits', 0):,.2f}")
        print(f"Total credits: ${data.get('total_credits', 0):,.2f}")
        
        # Check dates
        dates = [t.get('date', '') for t in trans]
        print(f"\nTransaction dates found:")
        for date in dates:
            print(f"  {date}")
            
        # Show first and last transactions
        if trans:
            print(f"\nFirst transaction: {trans[0].get('date')} - {trans[0].get('description')}")
            print(f"Last transaction: {trans[-1].get('date')} - {trans[-1].get('description')}")