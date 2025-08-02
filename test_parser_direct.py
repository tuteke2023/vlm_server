#!/usr/bin/env python3
"""
Direct test of the bank parser to debug parsing issues
"""

import logging
from bank_parser_v2 import BankStatementParser, parse_bank_statement_to_csv

# Set up logging to see what's happening
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Test different AI response formats
test_responses = [
    # Format 1: Clean table format
    """
    Here's the bank statement information:

    BANK STATEMENT
    Account: ****1234
    Period: January 1-31, 2024

    Date        Description                     Debit       Credit      Balance
    ------------------------------------------------------------------------
    01/01/2024  Opening Balance                                         $5,000.00
    01/03/2024  Walmart Grocery Store          $125.43                 $4,874.57
    01/05/2024  Direct Deposit - Salary                    $3,500.00  $8,374.57
    01/07/2024  Shell Gas Station              $65.00                  $8,309.57
    01/10/2024  Transfer to Savings            $1,000.00               $7,309.57
    01/12/2024  Amazon Online Purchase         $89.99                  $7,219.58
    01/15/2024  Utility Bill Payment           $150.00                 $7,069.58
    01/18/2024  Restaurant - Pizza Palace      $45.00                  $7,024.58
    01/20/2024  ATM Withdrawal                 $200.00                 $6,824.58
    01/25/2024  Netflix Subscription           $15.99                  $6,808.59
    01/28/2024  Pharmacy - CVS                 $35.00                  $6,773.59
    01/31/2024  Bank Service Fee               $12.00                  $6,761.59

    Total Debits: $1,738.41
    Total Credits: $3,500.00
    Closing Balance: $6,761.59
    """,
    
    # Format 2: JSON-like response
    """
    I've analyzed the bank statement and here are the transactions:

    {
      "account_number": "****1234",
      "statement_period": "January 2024",
      "transactions": [
        {
          "date": "01/03/2024",
          "description": "Walmart Grocery Store",
          "debit": 125.43,
          "credit": 0,
          "balance": 4874.57
        },
        {
          "date": "01/05/2024",
          "description": "Direct Deposit - Salary",
          "debit": 0,
          "credit": 3500.00,
          "balance": 8374.57
        },
        {
          "date": "01/07/2024",
          "description": "Shell Gas Station",
          "debit": 65.00,
          "credit": 0,
          "balance": 8309.57
        }
      ],
      "total_debits": 190.43,
      "total_credits": 3500.00
    }
    """,
    
    # Format 3: Mixed narrative and table
    """
    I found the following transactions in your bank statement for account ending in 1234:

    The statement covers January 2024 and shows these transactions:

    | Date | Description | Amount | Type | Balance |
    |------|-------------|--------|------|---------|
    | 01/03/2024 | Walmart Grocery Store | $125.43 | Debit | $4,874.57 |
    | 01/05/2024 | Direct Deposit - Salary | $3,500.00 | Credit | $8,374.57 |
    | 01/07/2024 | Shell Gas Station | $65.00 | Debit | $8,309.57 |
    | 01/10/2024 | Transfer to Savings | $1,000.00 | Debit | $7,309.57 |

    Summary: Total debits of $1,190.43 and total credits of $3,500.00.
    """
]

def test_parser():
    """Test the parser with different formats"""
    parser = BankStatementParser()
    
    for i, response in enumerate(test_responses):
        print(f"\n{'='*60}")
        print(f"Testing Format {i+1}")
        print(f"{'='*60}")
        
        try:
            # Parse the response
            bank_statement, csv_content = parse_bank_statement_to_csv(response)
            
            print(f"✓ Parsing successful!")
            print(f"  - Transactions found: {len(bank_statement.transactions)}")
            print(f"  - Total Debits: ${bank_statement.total_debits:.2f}")
            print(f"  - Total Credits: ${bank_statement.total_credits:.2f}")
            
            if bank_statement.transactions:
                print("\n  First 3 transactions:")
                for j, trans in enumerate(bank_statement.transactions[:3]):
                    print(f"    {j+1}. {trans.date} - {trans.description}")
                    print(f"       Category: {trans.category}")
                    if trans.debit > 0:
                        print(f"       Debit: ${trans.debit:.2f}")
                    if trans.credit > 0:
                        print(f"       Credit: ${trans.credit:.2f}")
                    print(f"       Balance: ${trans.balance:.2f}")
            else:
                print("  ⚠️  No transactions extracted!")
                
            # Save CSV for inspection
            filename = f"test_parser_output_{i+1}.csv"
            with open(filename, 'w') as f:
                f.write(csv_content)
            print(f"\n  CSV saved to: {filename}")
            
        except Exception as e:
            print(f"✗ Parsing failed: {e}")
            logger.exception("Detailed error:")

if __name__ == "__main__":
    print("Direct Bank Parser Test")
    print("Testing parser with different AI response formats...")
    test_parser()