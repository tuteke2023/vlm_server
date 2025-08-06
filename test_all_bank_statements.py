#!/usr/bin/env python3
"""Test unified bank extraction with all available test statements"""

import requests
import base64
import json
from pathlib import Path

def convert_pdf_to_image(pdf_path):
    """Convert first page of PDF to image for testing"""
    try:
        import fitz  # PyMuPDF
        pdf_document = fitz.open(pdf_path)
        page = pdf_document[0]
        mat = fitz.Matrix(2, 2)  # 2x scaling for better quality
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        pdf_document.close()
        return base64.b64encode(img_data).decode('utf-8')
    except ImportError:
        print("PyMuPDF not installed, skipping PDF test")
        return None

def test_bank_statement(file_path, description):
    """Test a single bank statement with both JSON and table formats"""
    print(f"\n{'='*80}")
    print(f"Testing: {description}")
    print(f"File: {file_path}")
    print('='*80)
    
    # Load the file
    if file_path.endswith('.pdf'):
        image_data = convert_pdf_to_image(file_path)
        if not image_data:
            print("Skipping PDF - PyMuPDF not available")
            return
    else:
        with open(file_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
    
    # Test both formats
    for format_type in ['json', 'table']:
        print(f"\n--- Testing {format_type.upper()} format ---")
        
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
        
        # First test the existing endpoint
        if format_type == 'json':
            endpoint = 'http://localhost:8000/api/v1/bank_extract_json'
        else:
            endpoint = 'http://localhost:8000/api/v1/generate'
            
        try:
            response = requests.post(endpoint, json={
                'messages': messages,
                'temperature': 0.1,
                'max_tokens': 2000
            })
            
            if response.ok:
                result = response.json()
                
                if format_type == 'json' and 'data' in result:
                    data = result['data']
                    if isinstance(data, dict):
                        trans = data.get('transactions', [])
                        print(f"✓ Extracted {len(trans)} transactions")
                        print(f"  Total debits: ${data.get('total_debits', 0):,.2f}")
                        print(f"  Total credits: ${data.get('total_credits', 0):,.2f}")
                        
                        # Show first 3 transactions
                        for i, t in enumerate(trans[:3]):
                            print(f"\n  Transaction {i+1}:")
                            print(f"    {t.get('date')} - {t.get('description')[:40]}...")
                            print(f"    Debit: ${t.get('debit', 0):,.2f} | Credit: ${t.get('credit', 0):,.2f} | Balance: ${t.get('balance', 0):,.2f}")
                            
                        # Check for balance validation
                        errors = []
                        for i in range(1, len(trans)):
                            prev_bal = trans[i-1].get('balance', 0)
                            curr = trans[i]
                            expected = prev_bal + curr.get('credit', 0) - curr.get('debit', 0)
                            actual = curr.get('balance', 0)
                            
                            if abs(expected - actual) > 0.01:
                                errors.append(f"Transaction {i+1}: Expected {expected:.2f}, got {actual:.2f}")
                        
                        if errors:
                            print(f"\n⚠️  Balance validation errors: {len(errors)}")
                            for e in errors[:3]:
                                print(f"    {e}")
                        else:
                            print("\n✓ All balances validated correctly")
                            
                elif format_type == 'table':
                    output = result.get('response', '')
                    lines = output.split('\n')
                    table_lines = [l for l in lines if '|' in l and not '---' in l]
                    trans_count = len([l for l in table_lines if any(c.isdigit() for c in l)])
                    print(f"✓ Extracted approximately {trans_count} transactions in table format")
                    print("\nFirst few lines:")
                    for line in table_lines[:5]:
                        print(f"  {line[:100]}...")
                        
            else:
                print(f"✗ Error: {response.status_code} - {response.text[:200]}")
                
        except Exception as e:
            print(f"✗ Exception: {str(e)}")

# Test all available statements
test_files = [
    ("test_bank_statement.png", "Test Bank Statement (PNG)"),
    ("tests/ApriltoJune2025_BankStatement.pdf", "April to June 2025 Statement (PDF)"),
]

print("="*80)
print("TESTING BANK STATEMENT EXTRACTION")
print("="*80)

for file_path, description in test_files:
    full_path = Path(file_path)
    if not full_path.is_absolute():
        full_path = Path("/home/teke/projects/vlm_server") / full_path
    
    if full_path.exists():
        test_bank_statement(str(full_path), description)
    else:
        print(f"\n✗ File not found: {full_path}")

print("\n" + "="*80)
print("TEST SUMMARY")
print("="*80)
print("Testing complete. Check above for any validation errors or issues.")