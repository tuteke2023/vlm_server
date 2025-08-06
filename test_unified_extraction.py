#!/usr/bin/env python3
import requests
import base64
import json

# Read test image  
with open('test_bank_statement.png', 'rb') as f:
    image_data = base64.b64encode(f.read()).decode('utf-8')

# Test unified endpoint with both formats
for export_format in ['json', 'table']:
    print(f"\n{'='*60}")
    print(f"Testing unified extraction with {export_format.upper()} format")
    print('='*60)
    
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

    # Test unified endpoint
    response = requests.post('http://localhost:8000/api/v1/bank_extract_unified', json={
        'messages': messages,
        'export_format': export_format,
        'temperature': 0.1,
        'max_tokens': 2000
    })

    print(f'\nResponse status: {response.status_code}')
    
    if response.ok:
        result = response.json()
        print(f"Status: {result.get('status')}")
        print(f"Format: {result.get('format', export_format)}")
        
        if result.get('validation_errors'):
            print(f"\nValidation errors detected: {len(result['validation_errors'])}")
            for error in result['validation_errors'][:3]:
                print(f"  - {error}")
        
        if result.get('confidence'):
            print(f"Confidence: {result['confidence'] * 100:.0f}%")
        
        if export_format == 'json':
            if result.get('data') and isinstance(result['data'], dict):
                data = result['data']
                print(f"\nExtracted {len(data.get('transactions', []))} transactions")
                print(f"Total debits: ${data.get('total_debits', 0):,.2f}")
                print(f"Total credits: ${data.get('total_credits', 0):,.2f}")
                
                # Show first 3 transactions
                for i, trans in enumerate(data.get('transactions', [])[:3]):
                    print(f"\nTransaction {i+1}:")
                    print(f"  Date: {trans.get('date')}")
                    print(f"  Description: {trans.get('description')}")
                    print(f"  Debit: ${trans.get('debit', 0):,.2f}")
                    print(f"  Credit: ${trans.get('credit', 0):,.2f}")
                    print(f"  Balance: ${trans.get('balance', 0):,.2f}")
        else:
            # Table format
            if result.get('data'):
                print("\nTable output (first 500 chars):")
                print(result['data'][:500])
    else:
        print(f"Error: {response.text}")