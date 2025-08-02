#!/usr/bin/env python3
"""
Test the v3 parser with actual AI output format
"""

import logging
from bank_parser_v3 import BankStatementParser, parse_bank_statement_to_csv

# Set up logging to see what's happening
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# This is the actual format the AI returned based on the logs
test_response = """
Here is the extracted information from the bank statement in a structured table format:

| Date       | Description                                                                 | Ref. | Withdrawals | Deposits | Balance |
|------------|-----------------------------------------------------------------------------|------|-------------|----------|---------|
| 2003-10-08 | Previous balance                                                              |      |             |          | 0.55    |
| 2003-10-14 | Payroll Deposit - HOTEL                                                        |      | 694.81      |          | 695.36  |
| 2003-10-14 | Web Bill Payment - MASTERCARD                                                  | 9685 | 200.00      |          | 495.36  |
| 2003-10-16 | ATM Withdrawal - INTERAC                                                      | 3990 | 21.25       |          | 474.11  |
| 2003-10-16 | Fees - Interac                                                             |      | 1.50        |          | 472.61  |
| 2003-10-20 | Interac Purchase - ELECTRONICS                                                  | 1975 | 2.99        |          | 469.62  |
| 2003-10-21 | Web Bill Payment - AMEX                                                         | 3314 | 300.00      |          | 169.62  |
| 2003-10-22 | ATM Withdrawal - FIRST BANK                                                   | 0064 | 100.00      |          | 69.62   |
| 2003-10-23 | Interac Purchase - SUPERMARKET                                                  | 1559 | 29.08       |          | 40.54   |
| 2003-10-24 | Interac Refund - ELECTRONICS                                                  | 1975 | 2.99        |          | 43.53   |
| 2003-10-27 | Telephone Bill Payment - VISA                                                     | 2475 | 600.00      |          | -556.47 |

Total Withdrawals: $1,251.62
Total Deposits: $694.81
"""

def test_parser():
    """Test the parser with pipe-delimited format"""
    parser = BankStatementParser()
    
    print("Testing V3 Parser with Pipe-Delimited Format")
    print("="*60)
    
    try:
        # Parse the response
        bank_statement, csv_content = parse_bank_statement_to_csv(test_response)
        
        print(f"✓ Parsing successful!")
        print(f"  - Transactions found: {len(bank_statement.transactions)}")
        print(f"  - Total Debits: ${bank_statement.total_debits:.2f}")
        print(f"  - Total Credits: ${bank_statement.total_credits:.2f}")
        
        if bank_statement.transactions:
            print("\n  Transactions:")
            for i, trans in enumerate(bank_statement.transactions):
                print(f"    {i+1}. {trans.date} - {trans.description}")
                print(f"       Category: {trans.category}")
                if trans.debit > 0:
                    print(f"       Debit: ${trans.debit:.2f}")
                if trans.credit > 0:
                    print(f"       Credit: ${trans.credit:.2f}")
                print(f"       Balance: ${trans.balance:.2f}")
                print()
        
        # Save CSV for inspection
        filename = "test_parser_v3_output.csv"
        with open(filename, 'w') as f:
            f.write(csv_content)
        print(f"\n  CSV saved to: {filename}")
        
        # Display CSV content
        print("\n  CSV Content:")
        print("-"*40)
        print(csv_content[:500])
        
    except Exception as e:
        print(f"✗ Parsing failed: {e}")
        logger.exception("Detailed error:")

if __name__ == "__main__":
    test_parser()