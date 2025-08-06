#!/usr/bin/env python3
"""Test extraction of BankStatementChequing.png"""

import requests
import base64

# Read the chequing statement
with open('tests/BankStatementChequing.png', 'rb') as f:
    image_data = base64.b64encode(f.read()).decode('utf-8')

# Test with current prompt
prompt = """Extract ALL transactions from this bank statement in a structured table format.

IMPORTANT RULES:
1. The OPENING BALANCE is NOT a transaction - it's just the starting balance, skip it
2. Start with the FIRST ACTUAL TRANSACTION (payment, transfer, withdrawal, deposit, fee, etc.)
3. Include EVERY transaction from ALL pages
4. Continue until you reach the final transaction or closing balance

Use this EXACT format with these EXACT column names:
| Date | Description | Withdrawals | Deposits | Balance |

DO NOT use "Debit" or "Credit" as column names. Use "Withdrawals" and "Deposits" only.

CRITICAL RULES FOR AMOUNTS:
- Extract the COMPLETE amount including dollars AND cents (e.g., 1,750.00 not just 17 or 1)
- Include ALL digits shown in the original (e.g., 850.00 not 8 or 85)
- Use commas for thousands (e.g., 2,200.00)
- Always include .00 for whole dollar amounts

DEBIT/CREDIT PLACEMENT:
- Withdrawals column = Money OUT (transfers to other accounts, payments, fees)
- Deposits column = Money IN (direct credits, transfers from other accounts)
- Each transaction should have EITHER withdrawal OR deposit, NOT both

Include EVERY transaction shown, including:
- All payments and withdrawals  
- All deposits and credits
- All transfers
- All fees and interest
- Small amounts (don't skip any transactions)

Make sure to capture the COMPLETE transaction list from ALL pages.

IMPORTANT: This statement has 19 transactions total. Extract ALL of them."""

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

response = requests.post('http://localhost:8000/api/v1/generate', json={
    'messages': messages,
    'temperature': 0.1,
    'max_tokens': 3000  # Increased token limit
})

print(f"Response status: {response.status_code}")
if response.ok:
    result = response.json()
    output = result['response']
    
    # Count transactions
    lines = output.split('\n')
    trans_lines = [l for l in lines if '|' in l and any(c.isdigit() for c in l) and not '---' in l and not 'Date' in l]
    
    print(f"\nExtracted {len(trans_lines)} transactions (should be 19)")
    
    # Show first and last few transactions
    print("\nFirst 5 transactions:")
    for line in trans_lines[:5]:
        print(line)
        
    print("\nLast 5 transactions:")
    for line in trans_lines[-5:]:
        print(line)
        
    # Check if we got all transactions
    if len(trans_lines) < 19:
        print(f"\n⚠️ WARNING: Missing {19 - len(trans_lines)} transactions!")
        print("\nFull output to check where it stops:")
        print(output)