#!/usr/bin/env python3
"""Test bank statement extraction API"""

import requests
import base64
import json

# Read the test image
with open("test_bank_statement.png", "rb") as f:
    image_data = base64.b64encode(f.read()).decode()

# Create the request
messages = [{
    "role": "user",
    "content": [
        {
            "type": "image",
            "image": f"data:image/png;base64,{image_data}"
        },
        {
            "type": "text", 
            "text": "Extract bank transactions"
        }
    ]
}]

# Test the JSON extraction endpoint
print("Testing JSON extraction endpoint...")
response = requests.post(
    "http://localhost:8000/api/v1/bank_extract_json",
    json={"messages": messages}
)

if response.status_code == 200:
    result = response.json()
    print(f"Status: {result['status']}")
    print(f"Transaction count: {result.get('transaction_count', 0)}")
    print(f"Result keys: {list(result.keys())}")
    
    # Get transactions from the correct key
    data = result.get('data', {})
    transactions = data.get('transactions', []) if isinstance(data, dict) else []
    
    print(f"Data type: {type(data)}")
    print(f"Data content: {json.dumps(data, indent=2) if isinstance(data, dict) else str(data)[:200]}")
    
    print("\nExtracted transactions:")
    for tx in transactions[:5]:  # Show first 5
        print(f"  {tx['date']} | {tx['description'][:30]:30} | Debit: ${tx['debit']:>8.2f} | Credit: ${tx['credit']:>8.2f} | Balance: ${tx['balance']:>10.2f}")
    
    # Check for issues
    print("\nChecking for issues...")
    for i, tx in enumerate(transactions):
        # Check for truncated amounts
        if tx['debit'] > 0 and tx['debit'] < 10:
            print(f"  ⚠️  Row {i+1}: Debit amount seems truncated: ${tx['debit']}")
        if tx['credit'] > 0 and tx['credit'] < 10:
            print(f"  ⚠️  Row {i+1}: Credit amount seems truncated: ${tx['credit']}")
        
        # Check for non-transaction data
        desc_lower = tx['description'].lower()
        if any(word in desc_lower for word in ['total', 'fee', 'summary', 'transaction type']):
            print(f"  ⚠️  Row {i+1}: Possible non-transaction data: {tx['description']}")
            
else:
    print(f"Error: {response.status_code}")
    print(response.text)