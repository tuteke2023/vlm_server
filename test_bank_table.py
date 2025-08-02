#!/usr/bin/env python3
"""
Test script for the enhanced bank statement table functionality
"""

import requests
import base64
import json
from pathlib import Path

# Server URL
SERVER_URL = "http://localhost:8000"

def test_bank_statement_extraction():
    """Test bank statement extraction with table display"""
    
    # Create a test bank statement text
    test_statement = """
    BANK STATEMENT
    Account Number: 1234567890
    Statement Period: January 1-31, 2024
    
    Date        Description                     Debit       Credit      Balance
    ---------------------------------------------------------------------------
    01/01/2024  Opening Balance                                         5,000.00
    01/05/2024  Grocery Store Purchase          125.50                 4,874.50
    01/10/2024  Salary Deposit                              3,500.00   8,374.50
    01/15/2024  Electric Bill Payment           185.00                 8,189.50
    01/18/2024  Restaurant Dining               67.25                  8,122.25
    01/20/2024  ATM Withdrawal                  200.00                 7,922.25
    01/25/2024  Online Shopping                 342.75                 7,579.50
    01/28/2024  Gas Station                     45.00                  7,534.50
    01/31/2024  Monthly Service Fee             15.00                  7,519.50
    
    Total Debits: $980.50
    Total Credits: $3,500.00
    Ending Balance: $7,519.50
    """
    
    # Convert to base64 for API
    statement_b64 = base64.b64encode(test_statement.encode()).decode()
    
    # Prepare request
    payload = {
        "messages": [{
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"""Analyze this bank statement and extract the following information: 
                    transaction dates, amounts (separate debit and credit), descriptions, running balances.
                    
                    IMPORTANT: Format the output as a table with these exact headers:
                    Date | Description | Debit | Credit | Balance
                    
                    Rules:
                    - Use consistent date format (MM/DD/YYYY)
                    - Debit amounts should be positive numbers in the Debit column
                    - Credit amounts should be positive numbers in the Credit column
                    - Leave empty cells blank
                    - Include all transactions found
                    
                    Bank Statement:
                    {test_statement}"""
                }
            ]
        }],
        "max_new_tokens": 1000
    }
    
    print("Testing bank statement extraction...")
    print("=" * 60)
    
    try:
        response = requests.post(f"{SERVER_URL}/api/v1/generate", json=payload)
        response.raise_for_status()
        
        result = response.json()
        print("AI Response:")
        print(result["response"])
        print("\n" + "=" * 60)
        print(f"Processing time: {result['processing_time']:.2f}s")
        print(f"Tokens used: {result['usage']['total_tokens']}")
        
        # Save response for testing the web UI
        with open("test_bank_response.json", "w") as f:
            json.dump(result, f, indent=2)
            
        print("\nResponse saved to test_bank_response.json")
        print("\nTo test the table display:")
        print("1. Open http://localhost:8080")
        print("2. Select 'Bank Transactions' tool")
        print("3. Upload a bank statement image or PDF")
        print("4. The results will display in an editable table format")
        print("5. You can:")
        print("   - Edit any cell by clicking on it")
        print("   - Change transaction categories")
        print("   - Add new rows with the 'Add Row' button")
        print("   - Delete rows with the trash icon")
        print("   - Export to CSV or Excel")
        print("   - Save modifications as JSON for AI training")
        
    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        print("\nMake sure the VLM server is running:")
        print("python vlm_server.py")

if __name__ == "__main__":
    test_bank_statement_extraction()