#!/usr/bin/env python3
"""Test different extraction approaches with the PDF"""

import requests
import base64
import json
from pathlib import Path

def convert_pdf_to_image(pdf_path):
    """Convert PDF to image"""
    try:
        import fitz
        pdf_document = fitz.open(pdf_path)
        
        # Try both pages
        images = []
        for page_num in range(min(2, len(pdf_document))):
            page = pdf_document[page_num]
            mat = fitz.Matrix(2, 2)
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.tobytes("png")
            images.append(base64.b64encode(img_data).decode('utf-8'))
        
        pdf_document.close()
        return images
    except Exception as e:
        print(f"Error: {e}")
        return []

pdf_path = "/home/teke/projects/vlm_server/tests/ApriltoJune2025_BankStatement.pdf"
print(f"Testing PDF: {pdf_path}\n")

images = convert_pdf_to_image(pdf_path)
if not images:
    print("Failed to convert PDF")
    exit(1)

print(f"Converted {len(images)} pages from PDF")

# Test with first page
image_data = images[0]

# Test 1: Direct table extraction
print("\n" + "="*60)
print("Test 1: Direct Table Extraction")
print("="*60)

messages = [{
    'role': 'user',
    'content': [
        {
            'type': 'text',
            'text': """Extract bank transactions from this statement in a table format.

IMPORTANT: This bank statement uses a specific format:
- Debit amounts have $ AFTER the number (e.g., "8,000.00 $")
- Credit amounts have $ BEFORE the number (e.g., "$17,765.00")
- Balances show "CR" for credit balances

Extract as: Date | Description | Debit | Credit | Balance"""
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
    'max_tokens': 2000
})

if response.ok:
    result = response.json()
    print("\nVLM Response (first 1000 chars):")
    print(result['response'][:1000])

# Test 2: JSON endpoint
print("\n" + "="*60)
print("Test 2: JSON Endpoint Extraction")
print("="*60)

messages2 = [{
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

response2 = requests.post('http://localhost:8000/api/v1/bank_extract_json', json={
    'messages': messages2,
    'temperature': 0.1,
    'max_tokens': 2000
})

if response2.ok:
    result2 = response2.json()
    print(f"\nStatus: {result2.get('status')}")
    
    if 'data' in result2:
        data = result2['data']
        if isinstance(data, dict):
            trans = data.get('transactions', [])
            print(f"Extracted {len(trans)} transactions")
            
            if trans:
                print("\nFirst 3 transactions:")
                for i, t in enumerate(trans[:3]):
                    print(f"\n{i+1}. {t.get('date')} - {t.get('description')[:30]}...")
                    print(f"   Debit: ${t.get('debit', 0):,.2f} | Credit: ${t.get('credit', 0):,.2f} | Balance: ${t.get('balance', 0):,.2f}")

# Test 3: Try with both pages combined
if len(images) > 1:
    print("\n" + "="*60)
    print("Test 3: Multi-page Extraction")
    print("="*60)
    
    # Note: Current VLM might not support multiple images
    # This is just to test if it helps