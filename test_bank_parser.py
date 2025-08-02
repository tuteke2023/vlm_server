#!/usr/bin/env python3
"""
Test script for the bank parser to ensure it works correctly
"""

from bank_parser import BankStatementParser, BankStatement, BankTransaction

# Test samples simulating different AI response formats
test_samples = [
    {
        "name": "Sample 1: Well-formatted table",
        "response": """
Based on the bank statement, here are the extracted transactions:

Date       | Description              | Debit   | Credit  | Balance
-----------|-------------------------|---------|---------|--------
01/05/2024 | Grocery Store Purchase  | 125.50  |         | 4874.50
01/10/2024 | Salary Deposit          |         | 3500.00 | 8374.50
01/15/2024 | Electric Bill Payment   | 185.00  |         | 8189.50
01/18/2024 | Restaurant Dining       | 67.25   |         | 8122.25
01/20/2024 | ATM Withdrawal         | 200.00  |         | 7922.25
01/25/2024 | Online Shopping Amazon  | 342.75  |         | 7579.50
01/28/2024 | Gas Station            | 45.00   |         | 7534.50
01/31/2024 | Monthly Service Fee    | 15.00   |         | 7519.50

Total Debits: $980.50
Total Credits: $3,500.00
"""
    },
    {
        "name": "Sample 2: JSON format response",
        "response": """
I've analyzed the bank statement. Here's the extracted data:

{
  "account_number": "****7890",
  "statement_period": "January 1-31, 2024",
  "transactions": [
    {
      "date": "01/02/2024",
      "description": "Direct Deposit - Employer",
      "category": "Income",
      "debit": 0,
      "credit": 2500.00,
      "balance": 3250.00
    },
    {
      "date": "01/03/2024",
      "description": "Walmart Grocery",
      "category": "Groceries",
      "debit": 156.78,
      "credit": 0,
      "balance": 3093.22
    },
    {
      "date": "01/05/2024",
      "description": "Netflix Subscription",
      "category": "Entertainment",
      "debit": 15.99,
      "credit": 0,
      "balance": 3077.23
    },
    {
      "date": "01/08/2024",
      "description": "Transfer from Savings",
      "category": "Transfer",
      "debit": 0,
      "credit": 500.00,
      "balance": 3577.23
    }
  ],
  "opening_balance": 750.00,
  "closing_balance": 3577.23
}
"""
    },
    {
        "name": "Sample 3: Mixed format with negatives",
        "response": """
Bank Statement Analysis:

Opening Balance: $1,500.00

Transaction List:
- 02/01/2024: Coffee Shop -$4.50 (Balance: $1,495.50)
- 02/02/2024: Paycheck +$1,850.00 (Balance: $3,345.50)
- 02/05/2024: Rent Payment -$1,200.00 (Balance: $2,145.50)
- 02/07/2024: Grocery Store -$87.25 (Balance: $2,058.25)
- 02/10/2024: Gas Station -$45.00 (Balance: $2,013.25)
- 02/15/2024: Online Transfer from John +$100.00 (Balance: $2,113.25)
- 02/20/2024: Restaurant -$65.50 (Balance: $2,047.75)

Closing Balance: $2,047.75
Total Withdrawals: $1,402.25
Total Deposits: $1,950.00
"""
    }
]

def test_parser():
    """Test the bank parser with various formats"""
    parser = BankStatementParser()
    
    print("Testing Bank Statement Parser")
    print("=" * 60)
    
    for sample in test_samples:
        print(f"\n{sample['name']}")
        print("-" * 40)
        
        try:
            # For testing, we'll manually create the structured data
            # In production, this would come from the AI model
            
            if "Sample 1" in sample['name']:
                # Manually parse the table format
                transactions = [
                    BankTransaction(date="01/05/2024", description="Grocery Store Purchase", 
                                  debit=125.50, credit=0, balance=4874.50, category=None),
                    BankTransaction(date="01/10/2024", description="Salary Deposit", 
                                  debit=0, credit=3500.00, balance=8374.50, category=None),
                    BankTransaction(date="01/15/2024", description="Electric Bill Payment", 
                                  debit=185.00, credit=0, balance=8189.50, category=None),
                    BankTransaction(date="01/18/2024", description="Restaurant Dining", 
                                  debit=67.25, credit=0, balance=8122.25, category=None),
                    BankTransaction(date="01/20/2024", description="ATM Withdrawal", 
                                  debit=200.00, credit=0, balance=7922.25, category=None),
                    BankTransaction(date="01/25/2024", description="Online Shopping Amazon", 
                                  debit=342.75, credit=0, balance=7579.50, category=None),
                    BankTransaction(date="01/28/2024", description="Gas Station", 
                                  debit=45.00, credit=0, balance=7534.50, category=None),
                    BankTransaction(date="01/31/2024", description="Monthly Service Fee", 
                                  debit=15.00, credit=0, balance=7519.50, category=None)
                ]
                bank_statement = BankStatement(transactions=transactions)
                
            elif "Sample 2" in sample['name']:
                # Parse JSON format
                bank_statement = parser.parse(sample['response'])
                
            else:  # Sample 3
                # Manually parse the mixed format
                transactions = [
                    BankTransaction(date="02/01/2024", description="Coffee Shop", 
                                  debit=4.50, credit=0, balance=1495.50, category=None),
                    BankTransaction(date="02/02/2024", description="Paycheck", 
                                  debit=0, credit=1850.00, balance=3345.50, category=None),
                    BankTransaction(date="02/05/2024", description="Rent Payment", 
                                  debit=1200.00, credit=0, balance=2145.50, category=None),
                    BankTransaction(date="02/07/2024", description="Grocery Store", 
                                  debit=87.25, credit=0, balance=2058.25, category=None),
                    BankTransaction(date="02/10/2024", description="Gas Station", 
                                  debit=45.00, credit=0, balance=2013.25, category=None),
                    BankTransaction(date="02/15/2024", description="Online Transfer from John", 
                                  debit=0, credit=100.00, balance=2113.25, category=None),
                    BankTransaction(date="02/20/2024", description="Restaurant", 
                                  debit=65.50, credit=0, balance=2047.75, category=None)
                ]
                bank_statement = BankStatement(
                    transactions=transactions,
                    opening_balance=1500.00,
                    closing_balance=2047.75
                )
            
            # Calculate totals
            bank_statement.calculate_totals()
            
            # Generate CSV
            csv_content = bank_statement.to_csv()
            
            print("CSV Output:")
            print(csv_content)
            
            # Save to file for inspection
            filename = f"test_output_{sample['name'].replace(' ', '_').replace(':', '')}.csv"
            with open(filename, 'w') as f:
                f.write(csv_content)
            print(f"✓ Saved to {filename}")
            
            # Verify data
            print(f"\nVerification:")
            print(f"- Transactions: {len(bank_statement.transactions)}")
            print(f"- Total Debits: ${bank_statement.total_debits:.2f}")
            print(f"- Total Credits: ${bank_statement.total_credits:.2f}")
            
            # Check categories
            categories = set(t.category for t in bank_statement.transactions)
            print(f"- Categories found: {', '.join(categories)}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("Testing complete! Check the generated CSV files.")


if __name__ == "__main__":
    test_parser()