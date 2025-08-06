#!/usr/bin/env python3
"""Test what happens with different format selections"""

import requests
import base64
import json

pdf_path = "tests/ApriltoJune2025_BankStatement.pdf"
with open(pdf_path, "rb") as f:
    pdf_data = base64.b64encode(f.read()).decode()

# Test JSON format (what should happen when JSON is selected)
print("Testing JSON format selection...")
print("="*60)

messages_json = [{
    "role": "user",
    "content": [
        {
            "type": "text",
            "text": "Extract all transactions from this bank statement in JSON format with fields: date, description, debit, credit, balance. IMPORTANT: Include ALL transactions including small amounts like 6.77"
        },
        {
            "type": "image",
            "image": f"data:application/pdf;base64,{pdf_data}"
        }
    ]
}]

# This is what bank_processor.js does when format='json'
response = requests.post(
    "http://localhost:8000/api/v1/bank_extract_json",
    json={"messages": messages_json}
)

print(f"Response status: {response.status_code}")
if response.status_code == 200:
    result = response.json()
    print(f"Response keys: {list(result.keys())}")
    print(f"Has 'data' field: {'data' in result}")
    print(f"Status: {result.get('status')}")
    
    if 'data' in result:
        data = result['data']
        print(f"\nExtracted {data['transaction_count']} transactions")
        if data['transactions']:
            first = data['transactions'][0]
            print(f"First transaction: {first['date']} - ${first['credit']:,.2f}")
    else:
        print("\nNo 'data' field - would fall back to table processing")
        print(f"Response preview: {str(result)[:200]}")

# Test table format 
print("\n\nTesting table format selection...")
print("="*60)

messages_table = [{
    "role": "user", 
    "content": [
        {
            "type": "text",
            "text": """Extract ALL transactions from this bank statement in a table format with columns: Date | Description | Reference | Withdrawals/Debit | Deposits/Credit | Balance.
                            
CRITICAL RULES FOR AMOUNTS:
- Extract the COMPLETE amount including dollars AND cents (e.g., 17,765.00 not just 17)
- Include ALL digits shown in the original (e.g., 8,000.00 not 8)
- Use commas for thousands (e.g., 2,200.00)
- Always include .00 for whole dollar amounts
- NEVER truncate amounts - if you see $17,765.00 write it as 17,765.00 not 17

Include EVERY transaction."""
        },
        {
            "type": "image",
            "image": f"data:application/pdf;base64,{pdf_data}"
        }
    ]
}]

response = requests.post(
    "http://localhost:8000/api/v1/generate",
    json={
        "messages": messages_table,
        "max_tokens": 2000
    }
)

if response.status_code == 200:
    result = response.json()
    output = result['response']
    print("First 500 chars of table output:")
    print(output[:500])
    
    # Check if amounts are correct
    if "17,765" in output or "17765" in output:
        print("\n✓ Table format has full amounts")
    else:
        print("\n✗ Table format has truncated amounts")