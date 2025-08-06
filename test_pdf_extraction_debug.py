#!/usr/bin/env python3
"""Debug PDF extraction to see what VLM is actually extracting"""

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
        mat = fitz.Matrix(2, 2)  # 2x scaling
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")
        pdf_document.close()
        return base64.b64encode(img_data).decode('utf-8')
    except Exception as e:
        print(f"Error converting PDF: {e}")
        return None

# Test the PDF
pdf_path = "/home/teke/projects/vlm_server/tests/ApriltoJune2025_BankStatement.pdf"
print(f"Testing PDF: {pdf_path}")

image_data = convert_pdf_to_image(pdf_path)
if not image_data:
    print("Failed to convert PDF")
    exit(1)

# Ask VLM to extract in table format with explicit instructions
messages = [{
    'role': 'user',
    'content': [
        {
            'type': 'text',
            'text': """Extract the first 5 transactions from this bank statement.
For each transaction, tell me:
1. The exact date
2. The exact description
3. The exact debit amount (if any)
4. The exact credit amount (if any)
5. The exact balance shown

Be very careful with the balance column - read the exact number shown."""
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
    'max_tokens': 1000
})

if response.ok:
    result = response.json()
    print("\nVLM Response:")
    print(result['response'])
else:
    print(f"Error: {response.status_code}")