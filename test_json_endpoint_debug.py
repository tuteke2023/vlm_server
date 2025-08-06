#!/usr/bin/env python3
import requests
import base64
import json

# Read test image  
with open('test_bank_statement.png', 'rb') as f:
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

print("Testing JSON endpoint...")
# Test the JSON endpoint
response = requests.post('http://localhost:8000/api/v1/bank_extract_json', json={
    'messages': messages,
    'temperature': 0.1,
    'max_tokens': 2000
})

print(f'\nResponse status: {response.status_code}')
if response.ok:
    result = response.json()
    print('\nJSON endpoint response:')
    print(f"Status: {result.get('status')}")
    print(f"Transaction count: {result.get('transaction_count')}")
    
    # Get the raw response that was generated
    print('\nFirst few transactions from data:')
    print(f"\nFull result keys: {list(result.keys())}")
    
    if 'data' in result:
        # Check what type data is
        print(f"Data type: {type(result['data'])}")
        
        if isinstance(result['data'], dict):
            # It's a dict, might have transactions key
            print(f"Data keys: {list(result['data'].keys())}")
            transactions = result['data'].get('transactions', [])
        elif isinstance(result['data'], list):
            transactions = result['data']
        elif isinstance(result['data'], str):
            transactions = json.loads(result['data'])
        else:
            transactions = []
            
        print(f"Number of transactions: {len(transactions)}")
        
        for i, t in enumerate(transactions[:3]):
            print(f"\n  Transaction {i+1}:")
            print(f"    Date: {t.get('date')}")
            print(f"    Description: {t.get('description')}")
            credit = t.get('credit', 0)
            debit = t.get('debit', 0)
            balance = t.get('balance', 0)
            print(f"    Credit: ${credit:,.2f}")
            print(f"    Debit: ${debit:,.2f}")
            print(f"    Balance: ${balance:,.2f}")

print("\n\nNow testing direct generate endpoint with table prompt...")

# Now test direct with table prompt  
table_messages = [{
    'role': 'user',
    'content': [
        {
            'type': 'text', 
            'text': """Extract ALL transactions from this bank statement in a structured table format.

IMPORTANT RULES:
1. The OPENING BALANCE is NOT a transaction - it's just the starting balance, skip it
2. Start with the FIRST ACTUAL TRANSACTION (payment, transfer, withdrawal, deposit, fee, etc.)
3. Include EVERY transaction from ALL pages - check carefully for transactions at page boundaries
4. Continue until you reach the final transaction or closing balance

Use this format:
| Date | Description | Ref. | Withdrawals | Deposits | Balance |

CRITICAL RULES FOR AMOUNTS:
- Extract the COMPLETE amount including dollars AND cents (e.g., 1,750.00 not just 17 or 1)
- Include ALL digits shown in the original (e.g., 850.00 not 8 or 85)
- Use commas for thousands (e.g., 2,200.00)
- Always include .00 for whole dollar amounts
- If amount is shown as 1750, write it as 1,750.00"""
        },
        {
            'type': 'image',
            'image': f'data:image/png;base64,{image_data}'
        }
    ]
}]

response2 = requests.post('http://localhost:8000/api/v1/generate', json={
    'messages': table_messages,
    'temperature': 0.1,
    'max_tokens': 2000
})

if response2.ok:
    result2 = response2.json()
    output = result2['response']
    print('\nDirect table format output (first 800 chars):')
    print(output[:800])
    
    if '17,765' in output or '17765' in output:
        print('\n✓ Direct table format correctly shows 17,765!')
    else:
        print('\n✗ Direct table format still missing digits')