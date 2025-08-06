#!/usr/bin/env python3
"""Test exactly what the main page would send"""

import requests
import base64

# Read the chequing statement
with open('tests/BankStatementChequing.png', 'rb') as f:
    image_data = base64.b64encode(f.read()).decode('utf-8')

# Exact prompt from main page bank-transactions tool
prompt = """Analyze this bank statement or transaction document and extract the following information in a structured format: transaction dates, merchant/payee names, transaction amounts, running balances. 
                Present the data in a clear table format with proper headers. 
                If you find multiple transactions, list each one separately. 
                Also provide a summary of total debits, credits, and account balance if available."""

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

# Call the generate endpoint like main page does
response = requests.post('http://localhost:8000/api/v1/generate', json={
    'messages': messages,
    'max_new_tokens': 3000,  # As set in getMaxTokens()
    'temperature': 0.7,
    'enable_safety_check': False
})

print(f"Response status: {response.status_code}")
if response.ok:
    result = response.json()
    output = result['response']
    
    # Count transactions
    lines = output.split('\n')
    trans_lines = []
    in_table = False
    
    for line in lines:
        if '---' in line and '|' in line:
            in_table = True
            continue
        if in_table and '|' in line and any(c.isdigit() for c in line):
            trans_lines.append(line)
        elif in_table and not line.strip():
            in_table = False
    
    print(f"\nExtracted {len(trans_lines)} transaction lines")
    print(f"Response length: {len(output)} characters")
    
    # Check if it mentions all transactions
    if '2003-11-08' in output:
        print("✓ Contains last transaction (2003-11-08)")
    else:
        print("✗ Missing last transaction (2003-11-08)")
        
    # Show last part of output
    print("\nLast 500 characters of response:")
    print(output[-500:])