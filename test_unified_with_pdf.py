#!/usr/bin/env python3
"""Test unified extraction endpoint with the PDF bank statement"""

import requests
import base64
import json
from pathlib import Path

def convert_pdf_to_image(pdf_path):
    """Convert first page of PDF to image"""
    try:
        import fitz
        pdf_document = fitz.open(pdf_path)
        page = pdf_document[0]
        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        pdf_document.close()
        return base64.b64encode(img_data).decode('utf-8')
    except Exception as e:
        print(f"Error: {e}")
        return None

# Test the unified endpoint (if it exists)
pdf_path = "/home/teke/projects/vlm_server/tests/ApriltoJune2025_BankStatement.pdf"
print(f"Testing PDF with unified extraction: {pdf_path}\n")

image_data = convert_pdf_to_image(pdf_path)
if not image_data:
    print("Failed to convert PDF")
    exit(1)

messages = [{
    'role': 'user',
    'content': [
        {
            'type': 'text',
            'text': 'Extract bank transactions'
        },
        {
            'type': 'image',
            'image': f'data:image/png;base64,{image_data}'
        }
    ]
}]

# First check if unified endpoint exists
print("Testing if unified endpoint exists...")
try:
    response = requests.post('http://localhost:8000/api/v1/bank_extract_unified', json={
        'messages': messages,
        'export_format': 'json',
        'temperature': 0.1,
        'max_tokens': 2000
    })
    
    if response.status_code == 404:
        print("✗ Unified endpoint not found. Testing existing JSON endpoint instead...\n")
        
        # Fall back to existing endpoint
        response = requests.post('http://localhost:8000/api/v1/bank_extract_json', json={
            'messages': messages,
            'temperature': 0.1,
            'max_tokens': 2000
        })
        
    if response.ok:
        result = response.json()
        print(f"Status: {result.get('status')}")
        
        if 'data' in result and isinstance(result['data'], dict):
            data = result['data']
            trans = data.get('transactions', [])
            
            print(f"\n✓ Extracted {len(trans)} transactions")
            print(f"Total debits: ${data.get('total_debits', 0):,.2f}")
            print(f"Total credits: ${data.get('total_credits', 0):,.2f}")
            
            # Show all transactions with full details
            print("\nAll Transactions:")
            print("-" * 80)
            
            for i, t in enumerate(trans):
                print(f"\nTransaction {i+1}:")
                print(f"  Date: {t.get('date')}")
                print(f"  Description: {t.get('description')}")
                print(f"  Debit: ${t.get('debit', 0):,.2f}")
                print(f"  Credit: ${t.get('credit', 0):,.2f}")
                print(f"  Balance: ${t.get('balance', 0):,.2f}")
                
                # Check if this is correct based on description
                desc = t.get('description', '').lower()
                debit = t.get('debit', 0)
                credit = t.get('credit', 0)
                
                issues = []
                if 'direct credit' in desc and debit > 0:
                    issues.append("⚠️  Direct Credit should not have debit")
                if 'transfer to' in desc and credit > 0:
                    issues.append("⚠️  Transfer to should not have credit")
                if 'transfer from' in desc and debit > 0:
                    issues.append("⚠️  Transfer from should not have debit")
                    
                if issues:
                    for issue in issues:
                        print(f"  {issue}")
            
            # Validate balances
            print("\n" + "-" * 80)
            print("Balance Validation:")
            errors = []
            
            for i in range(1, len(trans)):
                prev_bal = trans[i-1].get('balance', 0)
                curr = trans[i]
                expected = prev_bal + curr.get('credit', 0) - curr.get('debit', 0)
                actual = curr.get('balance', 0)
                
                if abs(expected - actual) > 0.01:
                    errors.append(f"Transaction {i+1}: Expected ${expected:,.2f}, got ${actual:,.2f}")
            
            if errors:
                print(f"\n⚠️  Found {len(errors)} balance errors:")
                for e in errors:
                    print(f"  {e}")
            else:
                print("\n✓ All balances validated correctly!")
                
    else:
        print(f"Error: {response.status_code} - {response.text[:200]}")
        
except Exception as e:
    print(f"Exception: {e}")