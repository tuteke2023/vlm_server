#!/usr/bin/env python3
"""Debug what's happening with browser requests"""

import requests
import json
import base64

# Check the VLM output directly with the exact prompt the browser would send
pdf_path = "tests/ApriltoJune2025_BankStatement.pdf"
with open(pdf_path, "rb") as f:
    pdf_data = base64.b64encode(f.read()).decode()

# Test 1: Check raw VLM output with table prompt
print("Test 1: Raw VLM output with table extraction prompt")
print("="*60)

messages = [{
    "role": "user",
    "content": [
        {
            "type": "image",
            "image": f"data:application/pdf;base64,{pdf_data}"
        },
        {
            "type": "text", 
            "text": """Extract ALL transactions from this bank statement in a structured table format.
IMPORTANT RULES:
1. The OPENING BALANCE is NOT a transaction - it's just the starting balance, skip it
2. Start with the FIRST ACTUAL TRANSACTION (payment, transfer, withdrawal, deposit, fee, etc.)
3. Include EVERY transaction from ALL pages - check carefully for transactions at page boundaries
4. Continue until you reach the final transaction or closing balance

Use this format:
| Date | Description | Ref. | Withdrawals | Deposits | Balance |

CRITICAL RULES FOR AMOUNTS:
- Extract the COMPLETE amount including dollars AND cents (e.g., 1,750.00 not just 17 or 1)
- Include ALL digits shown in the original (e.g., 850.00 not 8 or 85)
- Use commas for thousands (e.g., 2,200.00)
- Always include .00 for whole dollar amounts
- If amount is shown as 1750, write it as 1,750.00

Include EVERY transaction shown, including:
- All payments and withdrawals  
- All deposits and credits
- All transfers
- All fees and interest
- Small amounts (don't skip any transactions)

DO NOT include:
- Opening balance
- Statement headers/footers
- Account summaries

Make sure to capture the COMPLETE transaction list from ALL pages."""
        }
    ]
}]

response = requests.post(
    "http://localhost:8000/api/v1/generate",
    json={
        "messages": messages,
        "max_tokens": 2000,
        "temperature": 0.1
    }
)

if response.status_code == 200:
    result = response.json()
    vlm_output = result['response']
    print("First 1500 chars of VLM output:")
    print(vlm_output[:1500])
    
    # Check if amounts are truncated in raw output
    if "17,765" in vlm_output or "17765" in vlm_output:
        print("\n✓ VLM is outputting full amounts correctly")
    elif " 17 " in vlm_output or "|17|" in vlm_output:
        print("\n✗ VLM is truncating amounts!")
        
    # Save full output for inspection
    with open("debug_vlm_output.txt", "w") as f:
        f.write(vlm_output)
    print("\nFull output saved to debug_vlm_output.txt")

# Test 2: Check bank_extract_json endpoint
print("\n\nTest 2: Bank extraction JSON endpoint")
print("="*60)

response = requests.post(
    "http://localhost:8000/api/v1/bank_extract_json",
    json={"messages": messages}
)

if response.status_code == 200:
    result = response.json()
    print(f"Status: {result['status']}")
    print(f"Transaction count: {result.get('transaction_count', 0)}")
    
    if result['status'] == 'success':
        data = result['data']
        # Check first transaction amount
        if data['transactions']:
            first_tx = data['transactions'][0]
            print(f"\nFirst transaction:")
            print(f"  Date: {first_tx['date']}")
            print(f"  Description: {first_tx['description']}")
            print(f"  Credit: ${first_tx['credit']:,.2f}")
            
            if first_tx['credit'] == 17765.00:
                print("  ✓ Amount is correct!")
            else:
                print(f"  ✗ Amount is wrong (expected $17,765.00)")
                
print("\n\nIf amounts are correct in these tests but wrong in browser:")
print("1. Clear browser cache (Ctrl+Shift+R or Cmd+Shift+R)")
print("2. Check browser console for errors")
print("3. Check Network tab to see actual responses")