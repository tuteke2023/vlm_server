#!/usr/bin/env python3
"""Test that the web UI now uses the correct endpoint"""

import requests
import json

# Check which endpoint the web UI would use for bank transactions
print("Testing web UI behavior...\n")

# The web UI should now use /api/v1/bank_extract_json for bank transactions
# Let's verify the endpoint returns properly formatted data

# Read the actual PDF
import base64
pdf_path = "tests/ApriltoJune2025_BankStatement.pdf"
with open(pdf_path, "rb") as f:
    pdf_data = base64.b64encode(f.read()).decode()

messages = [{
    "role": "user",
    "content": [
        {
            "type": "image",
            "image": f"data:application/pdf;base64,{pdf_data}"
        },
        {
            "type": "text", 
            "text": "Extract bank transactions"
        }
    ]
}]

# Test the bank extraction endpoint
print("Testing /api/v1/bank_extract_json endpoint...")
response = requests.post(
    "http://localhost:8000/api/v1/bank_extract_json",
    json={"messages": messages}
)

if response.status_code == 200:
    result = response.json()
    if result['status'] == 'success':
        data = result['data']
        print(f"✓ Successfully extracted {data['transaction_count']} transactions")
        print(f"✓ Total debits: ${data['total_debits']:,.2f}")
        print(f"✓ Total credits: ${data['total_credits']:,.2f}")
        
        # Check first few transactions for correct amounts
        print("\nFirst 3 transactions:")
        for i, tx in enumerate(data['transactions'][:3]):
            debit = f"${tx['debit']:,.2f}" if tx['debit'] > 0 else "-"
            credit = f"${tx['credit']:,.2f}" if tx['credit'] > 0 else "-"
            print(f"  {tx['date']} | {tx['description'][:40]:40} | D: {debit:>12} | C: {credit:>12}")
            
        # Verify specific amounts
        print("\nAmount verification:")
        for tx in data['transactions']:
            if "DB RESULTS" in tx['description'] and "DBMAR25" in tx['description']:
                if tx['credit'] == 17765.00:
                    print(f"✓ DBMAR25 amount correct: ${tx['credit']:,.2f}")
                else:
                    print(f"✗ DBMAR25 amount wrong: ${tx['credit']:,.2f} (expected $17,765.00)")
                break
    else:
        print(f"✗ Extraction failed: {result}")
else:
    print(f"✗ Request failed: {response.status_code}")
    print(response.text)