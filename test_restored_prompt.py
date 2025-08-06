#!/usr/bin/env python3
"""Test with restored original prompt"""

import requests
import base64

# Read test image
with open('test_bank_statement.png', 'rb') as f:
    image_data = base64.b64encode(f.read()).decode('utf-8')

# Original working prompt
prompt = """Extract ALL transactions from this bank statement in a structured table format.

IMPORTANT RULES:
1. The OPENING BALANCE is NOT a transaction - it's just the starting balance, skip it
2. Start with the FIRST ACTUAL TRANSACTION (payment, transfer, withdrawal, deposit, fee, etc.)
3. Include EVERY transaction from ALL pages
4. Continue until you reach the final transaction or closing balance

Use this format:
| Date | Description | Withdrawals | Deposits | Balance |

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

Make sure to capture the COMPLETE transaction list from ALL pages."""

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
    'max_tokens': 2000
})

print(f"Response status: {response.status_code}")
if response.ok:
    result = response.json()
    output = result['response']
    print("\nVLM Output:")
    print(output)
    
    # Count transactions
    lines = output.split('\n')
    trans_lines = [l for l in lines if '|' in l and any(c.isdigit() for c in l) and not '---' in l]
    print(f"\nExtracted {len(trans_lines)} transactions")
    
    # Check if amounts are in correct columns
    for line in trans_lines[:5]:
        if 'direct credit' in line.lower():
            parts = line.split('|')
            if len(parts) >= 5:
                withdrawal = parts[2].strip()
                deposit = parts[3].strip()
                if withdrawal and withdrawal != '0.00' and withdrawal != '-':
                    print(f"⚠️ WARNING: Direct Credit has amount in Withdrawals column: {line[:80]}...")
                elif deposit:
                    print(f"✓ Direct Credit correctly in Deposits column")