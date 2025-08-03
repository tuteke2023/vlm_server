#!/usr/bin/env python3
"""
Post-processor for bank statement extraction to ensure completeness
"""

def validate_and_fix_bank_extraction(extracted_data, original_text=None):
    """
    Validate bank extraction and fix common issues
    """
    issues = []
    fixes_applied = []
    
    transactions = extracted_data.get('transactions', [])
    
    # 1. Remove opening balance if included
    if transactions and 'opening balance' in transactions[0].get('description', '').lower():
        opening_balance = transactions.pop(0)
        fixes_applied.append("Removed opening balance from transactions")
    
    # 2. Check for missing end transactions
    if transactions:
        last_date = transactions[-1].get('date', '')
        # Check if we're missing December transactions (common issue)
        if '31 DEC' not in str([t.get('date') for t in transactions]) and any(m in last_date for m in ['NOV', 'OCT', 'SEP']):
            issues.append("Possible missing end-of-year transactions")
    
    # 3. Validate balance continuity
    prev_balance = None
    for i, trans in enumerate(transactions):
        balance = trans.get('balance', 0)
        debit = trans.get('debit', 0)
        credit = trans.get('credit', 0)
        
        if prev_balance is not None:
            # Check if balance calculation makes sense
            expected_balance = prev_balance - debit + credit
            if abs(expected_balance - balance) > 0.01:  # Allow for rounding
                issues.append(f"Balance discontinuity at transaction {i+1}")
        
        prev_balance = balance
    
    # 4. Fix common description issues
    for trans in transactions:
        desc = trans.get('description', '')
        # Fix concatenated descriptions
        if 'blank' in desc.lower():
            trans['description'] = desc.replace('blank', '').strip()
        
        # Fix reference numbers in descriptions
        if '{' in desc and '}' in desc:
            # Extract reference number
            import re
            ref_match = re.search(r'\{(\d+)\}', desc)
            if ref_match:
                trans['reference'] = ref_match.group(1)
                trans['description'] = re.sub(r'\s*\{\d+\}', '', desc).strip()
    
    return {
        'transactions': transactions,
        'issues': issues,
        'fixes_applied': fixes_applied,
        'transaction_count': len(transactions)
    }

# Enhanced prompt for better extraction
ENHANCED_BANK_PROMPT = """Extract ALL transactions from this bank statement.

CRITICAL INSTRUCTIONS:
1. Start from the FIRST REAL TRANSACTION (not opening balance)
2. Continue extracting until you reach the VERY LAST transaction
3. Check the bottom of EVERY page - transactions often continue to the last line
4. Common last transactions include:
   - End of month interest payments
   - December 31st closing entries
   - Final transfers or fees

IMPORTANT:
- If you see dates like "31 DEC" or end-of-period entries, INCLUDE THEM
- Do NOT stop early - check the entire document
- The last transaction often has the final balance

Format each transaction as:
| Date | Description | Ref. | Withdrawals | Deposits | Balance |

Begin extraction now and continue to the absolute end:"""