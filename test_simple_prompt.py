#!/usr/bin/env python3
"""Test with simplified prompt and increased tokens"""

import requests
import base64

# Read the chequing statement
with open('tests/BankStatementChequing.png', 'rb') as f:
    image_data = base64.b64encode(f.read()).decode('utf-8')

# Simple prompt
prompt = """Extract ALL transactions from this bank statement as a table with columns: Date | Description | Debit | Credit | Balance

Include EVERY transaction - don't stop early. Extract all amounts completely with dollars and cents."""

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
    'max_new_tokens': 4096  # Increased
})

print(f"Response status: {response.status_code}")
if response.ok:
    result = response.json()
    output = result['response']
    
    # Count transactions
    lines = output.split('\n')
    trans_lines = [l for l in lines if '|' in l and any(c.isdigit() for c in l) and not '---' in l and not 'Date' in l]
    
    print(f"\nExtracted {len(trans_lines)} transactions (should be 19)")
    
    # Check if we got all transactions
    expected_dates = [
        '2003-10-08', '2003-10-14', '2003-10-16', '2003-10-20', '2003-10-21',
        '2003-10-22', '2003-10-23', '2003-10-24', '2003-10-27', '2003-10-30',
        '2003-11-03', '2003-11-06', '2003-11-07', '2003-11-08'
    ]
    
    found_dates = []
    for line in trans_lines:
        for date in expected_dates:
            if date in line:
                found_dates.append(date)
                break
    
    print(f"\nFound dates: {len(set(found_dates))} unique")
    missing = set(expected_dates) - set(found_dates)
    if missing:
        print(f"Missing dates: {sorted(missing)}")
    
    # Show last few transactions to see where it stops
    print("\nLast 5 transactions:")
    for line in trans_lines[-5:]:
        print(line[:100] + "...")