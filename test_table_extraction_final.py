#!/usr/bin/env python3
import requests
import base64

# Read test image  
with open('test_bank_statement.png', 'rb') as f:
    image_data = base64.b64encode(f.read()).decode('utf-8')

# Exact prompt from bank_processor.js
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
    'max_tokens': 2000
})

print(f"Response status: {response.status_code}")
if response.ok:
    result = response.json()
    print('\nVLM Table Output:')
    print(result['response'])