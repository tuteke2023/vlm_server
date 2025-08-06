#!/usr/bin/env python3
"""Test bank extraction with the actual PDF"""

import requests
import base64
import json

# Read the actual PDF
pdf_path = "tests/ApriltoJune2025_BankStatement.pdf"
with open(pdf_path, "rb") as f:
    pdf_data = base64.b64encode(f.read()).decode()

# Create the request with the actual PDF
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

# First, let's test what the raw VLM sees
print("Testing raw VLM output...")
response = requests.post(
    "http://localhost:8000/api/v1/generate",
    json={
        "messages": messages,
        "temperature": 0.1,
        "max_tokens": 2000
    }
)

if response.status_code == 200:
    result = response.json()
    print("VLM Raw Response:")
    print(result['response'][:1000])  # First 1000 chars
    print("\n...")
    
# Now test the JSON extraction endpoint
print("\n\nTesting JSON extraction endpoint...")
response = requests.post(
    "http://localhost:8000/api/v1/bank_extract_json",
    json={"messages": messages}
)

if response.status_code == 200:
    result = response.json()
    data = result.get('data', {})
    transactions = data.get('transactions', [])
    
    print(f"Extracted {len(transactions)} transactions")
    print("\nFirst 5 transactions:")
    for i, tx in enumerate(transactions[:5]):
        print(f"{i+1}. {tx['date']} | {tx['description'][:40]:40} | D: ${tx['debit']:>10.2f} | C: ${tx['credit']:>10.2f}")
        
    # Check specific transactions
    print("\n\nChecking specific transactions:")
    for tx in transactions:
        if "DB RESULTS" in tx['description'] and "APR" in tx['date']:
            actual = 17765.00
            extracted = tx['credit']
            print(f"✗ DB RESULTS DBMAR25: Expected ${actual}, Got ${extracted}")
            
        if "Transfer to xx5330" in tx['description'] and "05 Apr" in tx['date']:
            actual = 8000.00
            extracted = tx['debit']
            print(f"✗ Loan transfer: Expected ${actual}, Got ${extracted}")
else:
    print(f"Error: {response.status_code}")
    print(response.text)