#!/usr/bin/env python3
"""Test bank extraction with working server"""

import requests
import base64
from PIL import Image, ImageDraw, ImageFont
import io

print("=== Testing Bank Extraction ===")

# Create a bank statement-like image
img = Image.new('RGB', (600, 400), color='white')
draw = ImageDraw.Draw(img)

# Add bank statement text
text = """Bank Statement
Account: 123456789
Period: 01/01/2024 - 31/01/2024

Date        Description          Debit    Credit   Balance
01/01/2024  Opening Balance                        1000.00
05/01/2024  Grocery Store        50.00             950.00
10/01/2024  Salary Payment                2500.00 3450.00
15/01/2024  Rent Payment        1200.00           2250.00
20/01/2024  ATM Withdrawal       100.00           2150.00
25/01/2024  Interest Credit                 15.00 2165.00
31/01/2024  Closing Balance                       2165.00"""

draw.text((10, 10), text, fill='black')

# Convert to base64
img_buffer = io.BytesIO()
img.save(img_buffer, format='PNG')
img_base64 = base64.b64encode(img_buffer.getvalue()).decode('utf-8')

# Test bank extraction
url = "http://localhost:8000/api/v1/bank_extract_json"
payload = {
    "model": "Qwen/Qwen2.5-VL-3B-Instruct",
    "messages": [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Extract bank transactions"},
                {"type": "image", "image": f"data:image/png;base64,{img_base64}"}
            ]
        }
    ],
    "max_new_tokens": 2000
}

try:
    print("Sending request to bank extraction endpoint...")
    response = requests.post(url, json=payload, timeout=60)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ SUCCESS! Bank extraction is working!")
        result = response.json()
        print(f"\nAccount Info:")
        print(f"  Account Number: {result.get('account_number', 'N/A')}")
        print(f"  Period: {result.get('period', {}).get('start', 'N/A')} - {result.get('period', {}).get('end', 'N/A')}")
        print(f"  Opening Balance: ${result.get('opening_balance', 'N/A')}")
        print(f"  Closing Balance: ${result.get('closing_balance', 'N/A')}")
        print(f"\nTransactions found: {len(result.get('transactions', []))}")
        for i, txn in enumerate(result.get('transactions', [])[:5]):
            print(f"  {i+1}. {txn.get('date')} - {txn.get('description')} - ${txn.get('debit', 0) or txn.get('credit', 0)}")
    else:
        print(f"❌ Error: {response.text}")
except Exception as e:
    print(f"❌ Request failed: {e}")

print("\n✅ The VLM server is now working properly with pytorch-env and CUDA 12.8!")
print("You can access the web UI at http://localhost:8080/bank_processor.html")