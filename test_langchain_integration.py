#!/usr/bin/env python3
"""
Test the LangChain bank export integration
"""

import requests
import base64
import json
import time
import asyncio
import aiohttp
from datetime import datetime

SERVER_URL = "http://localhost:8000"

def test_bank_export_endpoint():
    """Test the new bank export endpoint"""
    
    # Sample bank statement text
    bank_statement = """
    BANK STATEMENT
    Account: ****1234
    Period: January 2024
    
    Date        Description                     Amount      Balance
    01/05/2024  Opening Balance                            $5,000.00
    01/07/2024  Grocery Store Purchase         -$125.50    $4,874.50
    01/10/2024  Direct Deposit Salary          +$3,500.00  $8,374.50
    01/15/2024  Electric Bill Payment          -$185.00    $8,189.50
    01/18/2024  Restaurant - Olive Garden      -$67.25     $8,122.25
    01/20/2024  ATM Withdrawal                 -$200.00    $7,922.25
    01/25/2024  Amazon Online Purchase         -$342.75    $7,579.50
    01/28/2024  Shell Gas Station              -$45.00     $7,534.50
    01/31/2024  Monthly Service Fee            -$15.00     $7,519.50
    
    Ending Balance: $7,519.50
    """
    
    # Create request
    messages = [{
        "role": "user",
        "content": f"""Analyze this bank statement and extract transaction data.
        
        Bank Statement:
        {bank_statement}
        """
    }]
    
    print("Testing Bank Export Endpoint")
    print("=" * 60)
    
    # Test CSV export
    print("\n1. Testing CSV Export...")
    try:
        response = requests.post(
            f"{SERVER_URL}/api/v1/bank_export",
            json={
                "messages": messages,
                "export_format": "csv"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ CSV export successful!")
            print(f"  - Transactions: {data['transaction_count']}")
            print(f"  - Total Debits: ${data['total_debits']:.2f}")
            print(f"  - Total Credits: ${data['total_credits']:.2f}")
            print(f"  - Filename: {data['filename']}")
            
            # Save CSV
            with open(data['filename'], 'w') as f:
                f.write(data['content'])
            print(f"  - Saved to: {data['filename']}")
            
            # Display first few lines
            print("\nCSV Preview:")
            print("-" * 40)
            lines = data['content'].split('\n')[:10]
            for line in lines:
                print(line)
            
        else:
            print(f"✗ Failed with status {response.status_code}")
            print(response.json())
            
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # Test JSON export
    print("\n\n2. Testing JSON Export...")
    try:
        response = requests.post(
            f"{SERVER_URL}/api/v1/bank_export",
            json={
                "messages": messages,
                "export_format": "json"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ JSON export successful!")
            print(f"  - Transactions: {data['transaction_count']}")
            print(f"  - Filename: {data['filename']}")
            
            # Save JSON
            with open(data['filename'], 'w') as f:
                f.write(data['content'])
            print(f"  - Saved to: {data['filename']}")
            
            # Display structure
            print("\nJSON Structure Preview:")
            print("-" * 40)
            json_data = json.loads(data['content'])
            print(f"Account Number: {json_data.get('account_number', 'N/A')}")
            print(f"Statement Period: {json_data.get('statement_period', 'N/A')}")
            print(f"Number of Transactions: {len(json_data.get('transactions', []))}")
            
            if json_data.get('transactions'):
                print("\nFirst Transaction:")
                print(json.dumps(json_data['transactions'][0], indent=2))
                
        else:
            print(f"✗ Failed with status {response.status_code}")
            print(response.json())
            
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\n" + "=" * 60)
    print("Test complete! Check the generated files.")

def test_web_interface():
    """Instructions for testing the web interface"""
    print("\n\nWeb Interface Testing Instructions")
    print("=" * 60)
    print("1. Open http://localhost:8080 in your browser")
    print("2. Select 'Bank Transactions' from the left menu")
    print("3. Upload a bank statement image or PDF")
    print("4. Check all the extraction options")
    print("5. Click 'Start Processing'")
    print("6. Once processing is complete, you should see:")
    print("   - The extracted text in the results area")
    print("   - An 'Export CSV' button in the results header")
    print("7. Click 'Export CSV' to download the structured data")
    print("\nThe CSV will have proper columns for:")
    print("- Date")
    print("- Description") 
    print("- Category (auto-categorized)")
    print("- Debit")
    print("- Credit")
    print("- Balance")
    print("\nVerify that:")
    print("- Amounts are correctly separated into debit/credit columns")
    print("- Categories are automatically assigned")
    print("- Totals are calculated correctly")

if __name__ == "__main__":
    # Check if server is running
    try:
        response = requests.get(f"{SERVER_URL}/health")
        if response.status_code == 200:
            print("✓ VLM Server is running")
            test_bank_export_endpoint()
            test_web_interface()
        else:
            print("✗ VLM Server is not responding properly")
    except:
        print("✗ VLM Server is not running. Start it with:")
        print("  python vlm_server.py")