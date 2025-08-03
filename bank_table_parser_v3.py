"""
Bank table to JSON parser v3 - uses balance changes to determine debit/credit
"""

import re
import json
from typing import Dict, List, Optional

def parse_bank_table_to_json(table_text: str) -> Dict:
    """Parse VLM table output to JSON format using balance validation"""
    
    lines = table_text.strip().split('\n')
    transactions = []
    
    for i, line in enumerate(lines):
        # Skip headers, separators, and non-table content
        if not '|' in line or '---' in line or 'Date' in line.upper():
            continue
            
        # Split by pipe - DO NOT remove empty parts as they represent empty columns
        parts = [p.strip() for p in line.split('|')]
        
        # Remove only the first and last empty parts (table borders)
        if parts and parts[0] == '':
            parts = parts[1:]
        if parts and parts[-1] == '':
            parts = parts[:-1]
            
        # For VLM output format, we expect 6 columns:
        # Date | Description | Ref | Withdrawals | Deposits | Balance
        if len(parts) < 5:  # At least need date, desc, amount, balance
            continue
            
        # Extract fields
        date_str = parts[0]
        description = parts[1]
        
        # Skip if date doesn't look valid
        if not any(char.isdigit() for char in date_str):
            continue
            
        # Find the balance - it's usually the last numeric column
        balance_str = ""
        for j in range(len(parts)-1, 1, -1):
            if parts[j] and re.match(r'^-?\d+[\d,]*\.?\d*$', parts[j].replace(',', '')):
                balance_str = parts[j]
                break
                
        if not balance_str:
            continue
            
        # Find the amount - look for numeric values in middle columns
        # Skip reference column (usually index 2) if it looks like a reference number
        amount_str = ""
        ref_idx = 2  # Reference is typically the 3rd column
        
        for j in range(2, len(parts)-1):
            if parts[j] and re.match(r'^\d+[\d,]*\.?\d*$', parts[j].replace(',', '')):
                # Check if this might be a reference number (typically 4+ digits with no decimal)
                if j == ref_idx and len(parts[j]) >= 4 and '.' not in parts[j]:
                    # This is likely a reference number, skip it
                    continue
                amount_str = parts[j]
                break
        
        # Parse reference (if exists)
        ref = ""
        if len(parts) > 2:
            ref = parts[2] if not re.match(r'^\d+[\d,]*\.?\d*$', parts[2].replace(',', '')) else ""
            
        try:
            # Parse amount
            amount = 0
            if amount_str:
                amount = float(amount_str.replace(',', ''))
            
            # Parse balance
            balance = 0
            if balance_str:
                balance_clean = balance_str.replace(',', '').replace('(', '-').replace(')', '')
                balance = float(balance_clean)
            
            # Get previous balance to determine debit/credit
            prev_balance = 0
            if transactions:
                prev_balance = transactions[-1]["balance"]
            elif "previous balance" in description.lower():
                # This is the opening balance line
                transactions.append({
                    "date": date_str,
                    "description": description,
                    "reference": ref,
                    "debit": 0,
                    "credit": 0,
                    "balance": balance
                })
                continue
            
            # SMART DETECTION: Use balance change to determine debit/credit
            balance_change = balance - prev_balance
            
            # Determine debit/credit based on balance change
            debit = 0
            credit = 0
            
            if amount > 0:
                if abs(balance_change - amount) < 0.01:
                    # Balance increased by the amount -> Credit
                    credit = amount
                elif abs(balance_change + amount) < 0.01:
                    # Balance decreased by the amount -> Debit
                    debit = amount
                else:
                    # Fallback to keyword detection if balance math doesn't match
                    # This handles cases where there might be multiple transactions
                    desc_lower = description.lower()
                    credit_keywords = ['deposit', 'refund', 'transfer - from', 'from savings', 'income', 'payroll']
                    is_credit = any(keyword in desc_lower for keyword in credit_keywords)
                    
                    if is_credit:
                        credit = amount
                    else:
                        debit = amount
                        
            # Normalize date format
            if '/' in date_str:
                # Keep the format as-is for now
                date_iso = date_str
            else:
                date_iso = date_str
                
            transaction = {
                "date": date_iso,
                "description": description,
                "reference": ref,
                "debit": round(debit, 2),
                "credit": round(credit, 2),
                "balance": round(balance, 2)
            }
            
            transactions.append(transaction)
            
        except Exception as e:
            print(f"Error parsing line: {line} - {e}")
            continue
    
    # Calculate totals
    total_debits = sum(t["debit"] for t in transactions)
    total_credits = sum(t["credit"] for t in transactions)
    
    # Get opening and closing balances
    opening_balance = transactions[0]["balance"] if transactions else 0
    closing_balance = transactions[-1]["balance"] if transactions else 0
    
    return {
        "account_number": "****",
        "statement_period": "",
        "opening_balance": opening_balance,
        "closing_balance": closing_balance,
        "transaction_count": len(transactions),
        "total_debits": round(total_debits, 2),
        "total_credits": round(total_credits, 2),
        "transactions": transactions
    }

def test_parser():
    """Test with VLM output that has amounts in wrong columns"""
    
    # Example where VLM puts everything in Withdrawals column
    vlm_output = """
| Date       | Description                    | Ref. | Withdrawals | Deposits | Balance |
|------------|--------------------------------|------|-------------|----------|---------|
| Oct 14     | Previous balance               |      |             |          | 0.55    |
| Oct 14     | Payroll Deposit - HOTEL        |      | 694.81      |          | 695.36  |
| Oct 14     | Web Bill Payment - POWER       |      | 200.00      |          | 495.36  |
| Oct 27     | Telephone Bill Payment - VISA  |      | 6.77        |          | 488.59  |
| Oct 28     | Payroll Deposit - HOTEL        |      | 694.81      |          | 1183.40 |
"""
    
    result = parse_bank_table_to_json(vlm_output)
    
    print("Parsed JSON:")
    print(json.dumps(result, indent=2))
    
    # Verify results
    print("\nValidation:")
    for trans in result["transactions"]:
        if trans["description"] != "Previous balance":
            if trans["credit"] > 0:
                print(f"✓ {trans['description']}: Credit ${trans['credit']} (balance went UP)")
            elif trans["debit"] > 0:
                print(f"✓ {trans['description']}: Debit ${trans['debit']} (balance went DOWN)")

if __name__ == "__main__":
    test_parser()