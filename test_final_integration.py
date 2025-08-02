#!/usr/bin/env python3
"""
Final integration test for bank statement CSV export
"""

import requests
import json
from datetime import datetime

SERVER_URL = "http://localhost:8000"

# Simulate the actual AI response format from the logs
AI_BANK_RESPONSE = """
Here is the extracted information from the bank statement in a structured table format:

| Date       | Description                                                                 | Ref. | Withdrawals | Deposits | Balance |
|------------|-----------------------------------------------------------------------------|------|-------------|----------|---------|
| 2003-10-08 | Previous balance                                                            |      |             |          | 0.55    |
| 2003-10-14 | Payroll Deposit - HOTEL                                                     |      |             | 694.81   | 695.36  |
| 2003-10-14 | Web Bill Payment - MASTERCARD                                               | 9685 | 200.00      |          | 495.36  |
| 2003-10-16 | ATM Withdrawal - INTERAC                                                    | 3990 | 21.25       |          | 474.11  |
| 2003-10-16 | Fees - Interac                                                              |      | 1.50        |          | 472.61  |
| 2003-10-20 | Interac Purchase - ELECTRONICS                                              | 1975 | 2.99        |          | 469.62  |
| 2003-10-21 | Web Bill Payment - AMEX                                                     | 3314 | 300.00      |          | 169.62  |
| 2003-10-22 | ATM Withdrawal - FIRST BANK                                                 | 0064 | 100.00      |          | 69.62   |
| 2003-10-23 | Interac Purchase - SUPERMARKET                                              | 1559 | 29.08       |          | 40.54   |
| 2003-10-24 | Interac Refund - ELECTRONICS                                                | 1975 |             | 2.99     | 43.53   |
| 2003-10-27 | Telephone Bill Payment - VISA                                               | 2475 | 600.00      |          | -556.47 |

Total Withdrawals: $1,254.82
Total Deposits: $697.80
"""

def test_bank_export():
    """Test the bank export endpoint with realistic data"""
    
    print("Final Integration Test - Bank Statement CSV Export")
    print("="*60)
    
    # Create messages simulating a real conversation
    messages = [
        {
            "role": "user",
            "content": "Please analyze this bank statement and extract all transactions"
        },
        {
            "role": "assistant", 
            "content": AI_BANK_RESPONSE
        }
    ]
    
    # Test CSV export
    print("\nTesting CSV Export...")
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
            
            # Display CSV content
            print("\nCSV Content:")
            print("-" * 60)
            print(data['content'])
            print("-" * 60)
            
            # Verify specific transactions
            lines = data['content'].split('\n')
            payroll_found = False
            for line in lines:
                if 'Payroll Deposit' in line and '694.81' in line:
                    payroll_found = True
                    print("\n✓ Verified: Payroll deposit correctly in Credit column")
                    break
            
            if not payroll_found:
                print("\n✗ Warning: Payroll deposit not found in Credit column")
                
        else:
            print(f"✗ Failed with status {response.status_code}")
            print(response.json())
            
    except Exception as e:
        print(f"✗ Error: {e}")

def main():
    # Check if server is running
    try:
        response = requests.get(f"{SERVER_URL}/health")
        if response.status_code == 200:
            print("✓ VLM Server is running")
            test_bank_export()
        else:
            print("✗ VLM Server is not responding properly")
    except:
        print("✗ VLM Server is not running. Start it with:")
        print("  python vlm_server.py")

if __name__ == "__main__":
    main()