"""
Unified bank statement extractor using LangChain
Provides consistent extraction regardless of output format
"""

import logging
from typing import Dict, List, Tuple
from bank_parser_v3 import BankStatement, parse_bank_statement_to_csv
from bank_table_parser_v3 import parse_bank_table_to_json

logger = logging.getLogger(__name__)

class UnifiedBankExtractor:
    """Unified extraction that always uses LangChain validation"""
    
    @staticmethod
    def extract_and_validate(vlm_response: str, output_format: str = "json") -> Dict:
        """
        Extract bank transactions with LangChain validation
        
        Args:
            vlm_response: Raw VLM output (table format)
            output_format: "json", "csv", or "table"
            
        Returns:
            Dict with extracted data and metadata
        """
        try:
            # Always parse through LangChain first for validation
            bank_statement, csv_content = parse_bank_statement_to_csv(vlm_response)
            
            # Validate balances
            validation_errors = UnifiedBankExtractor._validate_balances(bank_statement.transactions)
            
            if validation_errors:
                logger.warning(f"Balance validation errors: {validation_errors}")
                # Attempt to fix common issues
                bank_statement = UnifiedBankExtractor._fix_common_issues(bank_statement, validation_errors)
            
            # Format output based on request
            if output_format == "json":
                return {
                    "status": "success",
                    "data": bank_statement.dict(),
                    "transaction_count": len(bank_statement.transactions),
                    "validation_errors": validation_errors,
                    "confidence": 0.95 if not validation_errors else 0.80
                }
            
            elif output_format == "csv":
                return {
                    "status": "success", 
                    "data": csv_content,
                    "transaction_count": len(bank_statement.transactions),
                    "format": "csv"
                }
            
            elif output_format == "table":
                # Convert back to table format with corrections
                table = UnifiedBankExtractor._json_to_table(bank_statement)
                return {
                    "status": "success",
                    "data": table,
                    "transaction_count": len(bank_statement.transactions),
                    "format": "table"
                }
                
        except Exception as e:
            logger.error(f"Extraction failed: {str(e)}")
            # Fallback to basic parsing
            return UnifiedBankExtractor._fallback_extraction(vlm_response, output_format)
    
    @staticmethod
    def _validate_balances(transactions: List) -> List[str]:
        """Validate running balances and return errors"""
        errors = []
        
        for i in range(1, len(transactions)):
            prev = transactions[i-1]
            curr = transactions[i]
            
            expected_balance = prev.balance + curr.credit - curr.debit
            
            if abs(expected_balance - curr.balance) > 0.01:
                errors.append(
                    f"Balance mismatch at {curr.date}: "
                    f"expected {expected_balance:.2f}, got {curr.balance:.2f}"
                )
        
        return errors
    
    @staticmethod
    def _fix_common_issues(statement: BankStatement, errors: List[str]) -> BankStatement:
        """Attempt to fix common extraction issues"""
        
        # Check if debit/credit columns are swapped
        swap_indicators = 0
        for trans in statement.transactions:
            # Direct Credit should have credit, not debit
            if "direct credit" in trans.description.lower() and trans.debit > 0:
                swap_indicators += 1
            # Transfer to should have debit, not credit  
            if "transfer to" in trans.description.lower() and trans.credit > 0:
                swap_indicators += 1
        
        # If many indicators, swap the columns
        if swap_indicators > len(statement.transactions) * 0.3:
            logger.info("Detected swapped debit/credit columns, fixing...")
            for trans in statement.transactions:
                trans.debit, trans.credit = trans.credit, trans.debit
        
        # Recalculate balances if needed
        if statement.transactions:
            running_balance = statement.opening_balance
            for trans in statement.transactions:
                running_balance = running_balance + trans.credit - trans.debit
                trans.balance = running_balance
        
        return statement
    
    @staticmethod  
    def _json_to_table(statement: BankStatement) -> str:
        """Convert validated JSON back to table format"""
        lines = []
        lines.append("| Date | Description | Debit | Credit | Balance |")
        lines.append("|------|-------------|-------|--------|---------|")
        
        for trans in statement.transactions:
            debit_str = f"{trans.debit:,.2f}" if trans.debit > 0 else ""
            credit_str = f"{trans.credit:,.2f}" if trans.credit > 0 else ""
            balance_str = f"{trans.balance:,.2f}"
            
            lines.append(
                f"| {trans.date} | {trans.description} | "
                f"{debit_str} | {credit_str} | {balance_str} |"
            )
        
        return "\n".join(lines)
    
    @staticmethod
    def _fallback_extraction(vlm_response: str, output_format: str) -> Dict:
        """Basic extraction without LangChain validation"""
        try:
            # Use simple parser
            parsed = parse_bank_table_to_json(vlm_response)
            
            return {
                "status": "warning",
                "data": parsed,
                "message": "Fallback parser used - validation limited",
                "format": output_format
            }
        except:
            return {
                "status": "error",
                "message": "Failed to parse bank statement",
                "data": None
            }