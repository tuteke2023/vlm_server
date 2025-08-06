#!/usr/bin/env python3
"""Validate the JSON extraction balance calculations"""

import requests
import base64
from pathlib import Path

def convert_pdf_to_image(pdf_path):
    """Convert PDF to image"""
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

pdf_path = "/home/teke/projects/vlm_server/tests/ApriltoJune2025_BankStatement.pdf"
image_data = convert_pdf_to_image(pdf_path)

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

response = requests.post('http://localhost:8000/api/v1/bank_extract_json', json={
    'messages': messages,
    'temperature': 0.1,
    'max_tokens': 2000
})

if response.ok:
    result = response.json()
    if result.get('status') == 'success' and 'data' in result:
        data = result['data']
        trans = data.get('transactions', [])
        
        print(f"Extracted {len(trans)} transactions\n")
        print("Transaction Details with Balance Validation:")
        print("="*100)
        
        running_balance = 0  # Starting from nil
        
        for i, t in enumerate(trans):
            date = t.get('date', '')
            desc = t.get('description', '')
            debit = t.get('debit', 0)
            credit = t.get('credit', 0)
            balance = t.get('balance', 0)
            
            # Calculate expected balance
            running_balance = running_balance + credit - debit
            
            print(f"\n{i+1}. {date}")
            print(f"   {desc}")
            print(f"   Debit: ${debit:>10,.2f} | Credit: ${credit:>10,.2f} | Balance: ${balance:>10,.2f}")
            
            # Check debit/credit placement
            issues = []
            desc_lower = desc.lower()
            
            if 'direct credit' in desc_lower and debit > 0:
                issues.append("❌ Direct Credit should be in Credit column, not Debit")
            elif 'direct credit' in desc_lower and credit > 0:
                issues.append("✓ Direct Credit correctly in Credit column")
                
            if 'transfer to' in desc_lower and credit > 0:
                issues.append("❌ 'Transfer to' should be in Debit column, not Credit")
            elif 'transfer to' in desc_lower and debit > 0:
                issues.append("✓ 'Transfer to' correctly in Debit column")
                
            if 'transfer from' in desc_lower and debit > 0:
                issues.append("❌ 'Transfer from' should be in Credit column, not Debit")
            elif 'transfer from' in desc_lower and credit > 0:
                issues.append("✓ 'Transfer from' correctly in Credit column")
            
            for issue in issues:
                print(f"   {issue}")
            
            # Check balance calculation
            if abs(running_balance - balance) > 0.01:
                print(f"   ❌ Balance Error: Expected ${running_balance:,.2f}, got ${balance:,.2f}")
                # Try to understand the error
                if balance == debit or balance == credit:
                    print(f"      → Balance might be showing transaction amount instead of running balance")
            else:
                print(f"   ✓ Balance correct")
        
        print("\n" + "="*100)
        print("Summary:")
        print(f"Total Debits: ${data.get('total_debits', 0):,.2f}")
        print(f"Total Credits: ${data.get('total_credits', 0):,.2f}")
        print(f"Final Balance: ${trans[-1].get('balance', 0):,.2f} (should be $0.00)")