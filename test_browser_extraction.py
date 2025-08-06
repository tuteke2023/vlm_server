#!/usr/bin/env python3
import requests
import base64
import json

# Read test image
with open('test_bank_statement.png', 'rb') as f:
    image_data = base64.b64encode(f.read()).decode('utf-8')

# Exact prompt from updated bank_processor.js
prompt = """Extract ALL transactions from this bank statement in a table format with columns: Date | Description | Debit | Credit | Balance

CRITICAL RULES:
1. AMOUNTS:
   - Extract the COMPLETE amount including dollars AND cents (e.g., 17,765.00 not just 17)
   - Include ALL digits shown in the original (e.g., 8,000.00 not 8)
   - Use commas for thousands (e.g., 2,200.00)
   - Always include .00 for whole dollar amounts

2. DEBIT vs CREDIT:
   - DEBIT = Money OUT (withdrawals, transfers out, fees)
   - CREDIT = Money IN (deposits, direct credits, transfers in)
   - Each transaction should have EITHER debit OR credit, NOT both
   - "Direct Credit" = CREDIT column only (leave debit empty)
   - "Transfer to" = DEBIT column only (leave credit empty)
   - "Transfer from" = CREDIT column only (leave debit empty)
   - Look at the transaction description to determine which column to use

3. BALANCE:
   - Copy the exact running balance shown for each transaction
   - Do NOT calculate balances yourself - use the actual values from the statement

4. VALIDATION:
   - After creating the table, verify that each balance equals: previous balance + credit - debit
   - If balances don't add up, you have the debit/credit in wrong columns - fix it
   - Opening balance should be the starting point
   - Each subsequent balance should reflect the transaction correctly

Skip any summary rows, totals, or fee information. Only include actual transactions.

Include EVERY transaction."""

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
    print('\nExtracted table:')
    print(result['response'])
    
    # Parse the table like bank_processor.js does
    print('\n\nParsing table to JSON:')
    lines = result['response'].split('\n')
    transactions = []
    
    for line in lines:
        if 'Date' in line or '---' in line or line.strip() == '':
            continue
            
        if '|' in line:
            parts = line.split('|')
            parts = [p.strip() for p in parts]
            
            # Remove empty first/last elements
            if parts[0] == '':
                parts.pop(0)
            if parts and parts[-1] == '':
                parts.pop()
            
            if len(parts) >= 5:
                def parse_amount(s):
                    if not s or s == '-' or s == '':
                        return 0
                    return float(s.replace(',', ''))
                
                trans = {
                    'date': parts[0],
                    'description': parts[1],
                    'debit': parse_amount(parts[2]),
                    'credit': parse_amount(parts[3]),
                    'balance': parse_amount(parts[4])
                }
                transactions.append(trans)
                
    print(json.dumps(transactions, indent=2))
    
    # Validate balances
    print('\n\nValidating balances:')
    for i in range(1, len(transactions)):
        prev_balance = transactions[i-1]['balance']
        trans = transactions[i]
        expected = prev_balance + trans['credit'] - trans['debit']
        
        if abs(expected - trans['balance']) > 0.01:
            print(f"❌ Balance mismatch at {trans['date']} - {trans['description']}")
            print(f"   Previous: ${prev_balance:,.2f}")
            print(f"   Debit: ${trans['debit']:,.2f}, Credit: ${trans['credit']:,.2f}")
            print(f"   Expected: ${expected:,.2f}, Actual: ${trans['balance']:,.2f}")
        else:
            print(f"✓ {trans['date']} - Balance correct")