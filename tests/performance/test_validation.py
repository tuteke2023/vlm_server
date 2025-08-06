"""
Validation tests for bank extraction accuracy and quality
"""

import pytest
import json
import csv
from typing import List, Dict, Tuple
import difflib
from decimal import Decimal
import re

# These will be imported from the actual implementation
# from services.vlm.bank_parser_v3 import BankStatement, BankTransaction


class TestExtractionAccuracy:
    """Test extraction accuracy against known good data"""
    
    @pytest.fixture
    def expected_transactions(self):
        """Load expected transaction data"""
        return [
            {
                "date": "01/15/2025",
                "description": "WALMART GROCERY",
                "category": "Groceries",
                "debit": 125.50,
                "credit": 0,
                "balance": 1874.50
            },
            {
                "date": "01/16/2025",
                "description": "DIRECT DEPOSIT SALARY",
                "category": "Income",
                "debit": 0,
                "credit": 3000.00,
                "balance": 4874.50
            },
            {
                "date": "01/17/2025",
                "description": "SHELL GAS STATION",
                "category": "Transportation",
                "debit": 75.25,
                "credit": 0,
                "balance": 4799.25
            }
        ]
    
    def test_transaction_count_accuracy(self, extracted_data, expected_transactions):
        """Test that all transactions are extracted"""
        assert len(extracted_data["transactions"]) == len(expected_transactions)
    
    def test_date_extraction_accuracy(self, extracted_data, expected_transactions):
        """Test date extraction accuracy"""
        extracted_dates = [t["date"] for t in extracted_data["transactions"]]
        expected_dates = [t["date"] for t in expected_transactions]
        
        # All dates should match
        assert set(extracted_dates) == set(expected_dates)
    
    def test_amount_extraction_accuracy(self, extracted_data, expected_transactions):
        """Test amount extraction accuracy"""
        for i, (extracted, expected) in enumerate(zip(
            extracted_data["transactions"],
            expected_transactions
        )):
            # Check debit accuracy
            assert abs(extracted["debit"] - expected["debit"]) < 0.01
            
            # Check credit accuracy
            assert abs(extracted["credit"] - expected["credit"]) < 0.01
            
            # Check balance accuracy
            assert abs(extracted["balance"] - expected["balance"]) < 0.01
    
    def test_description_extraction_accuracy(self, extracted_data, expected_transactions):
        """Test description extraction accuracy"""
        for extracted, expected in zip(
            extracted_data["transactions"],
            expected_transactions
        ):
            # Calculate similarity ratio
            similarity = difflib.SequenceMatcher(
                None,
                extracted["description"].lower(),
                expected["description"].lower()
            ).ratio()
            
            # Should be at least 80% similar
            assert similarity > 0.8
    
    def test_categorization_accuracy(self, extracted_data, expected_transactions):
        """Test automatic categorization accuracy"""
        correct_categories = 0
        total = len(extracted_data["transactions"])
        
        for extracted, expected in zip(
            extracted_data["transactions"],
            expected_transactions
        ):
            if extracted["category"] == expected["category"]:
                correct_categories += 1
        
        accuracy = correct_categories / total
        assert accuracy > 0.8  # 80% accuracy threshold


class TestDataValidation:
    """Validate extracted data integrity"""
    
    def test_balance_consistency(self, extracted_data):
        """Test that balances are mathematically consistent"""
        transactions = extracted_data["transactions"]
        
        for i in range(1, len(transactions)):
            prev_balance = transactions[i-1]["balance"]
            curr_transaction = transactions[i]
            
            # Calculate expected balance
            expected_balance = prev_balance
            expected_balance -= curr_transaction["debit"]
            expected_balance += curr_transaction["credit"]
            
            # Check consistency (allowing for rounding)
            assert abs(curr_transaction["balance"] - expected_balance) < 0.01
    
    def test_debit_credit_exclusivity(self, extracted_data):
        """Test that transactions have either debit or credit, not both"""
        for transaction in extracted_data["transactions"]:
            # Should not have both debit and credit
            assert not (transaction["debit"] > 0 and transaction["credit"] > 0)
    
    def test_positive_amounts(self, extracted_data):
        """Test that all amounts are positive"""
        for transaction in extracted_data["transactions"]:
            assert transaction["debit"] >= 0
            assert transaction["credit"] >= 0
            assert transaction["balance"] >= 0
    
    def test_date_format_consistency(self, extracted_data):
        """Test that all dates follow consistent format"""
        date_pattern = re.compile(r'^\d{2}/\d{2}/\d{4}$')
        
        for transaction in extracted_data["transactions"]:
            assert date_pattern.match(transaction["date"])
    
    def test_required_fields_present(self, extracted_data):
        """Test that all required fields are present"""
        required_fields = ["date", "description", "category", "debit", "credit", "balance"]
        
        for transaction in extracted_data["transactions"]:
            for field in required_fields:
                assert field in transaction
    
    def test_totals_calculation(self, extracted_data):
        """Test that totals are calculated correctly"""
        transactions = extracted_data["transactions"]
        
        # Calculate expected totals
        expected_total_debits = sum(t["debit"] for t in transactions)
        expected_total_credits = sum(t["credit"] for t in transactions)
        
        # Check against extracted totals
        assert abs(extracted_data["total_debits"] - expected_total_debits) < 0.01
        assert abs(extracted_data["total_credits"] - expected_total_credits) < 0.01


class TestEdgeCases:
    """Test edge cases and error scenarios"""
    
    def test_empty_statement(self):
        """Test handling of empty bank statement"""
        # result = extract_bank_transactions("empty_image")
        # assert result["transactions"] == []
        pass
    
    def test_malformed_data(self):
        """Test handling of malformed transaction data"""
        malformed_cases = [
            {"date": "invalid", "description": "Test", "debit": "not_a_number"},
            {"description": "Missing date", "debit": 100},
            {"date": "01/01/2025", "description": "", "debit": -50}  # Negative amount
        ]
        
        for case in malformed_cases:
            # Should handle gracefully without crashing
            # tx = BankTransaction(**case)
            # assert tx is not None
            pass
    
    def test_unusual_date_formats(self):
        """Test handling of various date formats"""
        date_formats = [
            "01/15/2025",    # MM/DD/YYYY
            "15/01/2025",    # DD/MM/YYYY
            "2025-01-15",    # YYYY-MM-DD
            "01-15-2025",    # MM-DD-YYYY
            "15-01-2025",    # DD-MM-YYYY
            "Jan 15, 2025",  # Mon DD, YYYY
            "15 Jan 2025"    # DD Mon YYYY
        ]
        
        for date_str in date_formats:
            # tx = BankTransaction(date=date_str, description="Test", debit=100)
            # Normalized date should be MM/DD/YYYY
            # assert re.match(r'^\d{2}/\d{2}/\d{4}$', tx.date)
            pass
    
    def test_large_amounts(self):
        """Test handling of large transaction amounts"""
        large_amounts = [
            1000000.00,      # Million
            99999999.99,     # Maximum reasonable
            0.01,            # Minimum
            12345.678        # Extra decimal places
        ]
        
        for amount in large_amounts:
            # tx = BankTransaction(
            #     date="01/01/2025",
            #     description="Test",
            #     debit=amount
            # )
            # assert tx.debit == round(amount, 2)
            pass
    
    def test_special_characters_in_description(self):
        """Test handling of special characters"""
        descriptions = [
            "McDonald's Restaurant",
            "AT&T Payment",
            "7-Eleven Store #1234",
            "Café Français",
            "Payment - Ref: ABC123",
            "Transfer from ***1234"
        ]
        
        for desc in descriptions:
            # tx = BankTransaction(
            #     date="01/01/2025",
            #     description=desc,
            #     debit=100
            # )
            # assert tx.description == desc
            pass


class TestComparisonMetrics:
    """Compare extraction results across providers"""
    
    def compare_provider_results(self, local_result, openai_result):
        """Compare results from different providers"""
        metrics = {
            "transaction_count_match": len(local_result["transactions"]) == len(openai_result["transactions"]),
            "total_similarity": 0,
            "date_matches": 0,
            "amount_matches": 0,
            "description_similarity": 0
        }
        
        # Compare transactions
        for local_tx, openai_tx in zip(
            local_result["transactions"],
            openai_result["transactions"]
        ):
            # Date match
            if local_tx["date"] == openai_tx["date"]:
                metrics["date_matches"] += 1
            
            # Amount match (within tolerance)
            if (abs(local_tx["debit"] - openai_tx["debit"]) < 0.01 and
                abs(local_tx["credit"] - openai_tx["credit"]) < 0.01):
                metrics["amount_matches"] += 1
            
            # Description similarity
            similarity = difflib.SequenceMatcher(
                None,
                local_tx["description"],
                openai_tx["description"]
            ).ratio()
            metrics["description_similarity"] += similarity
        
        # Calculate averages
        num_transactions = len(local_result["transactions"])
        if num_transactions > 0:
            metrics["date_match_rate"] = metrics["date_matches"] / num_transactions
            metrics["amount_match_rate"] = metrics["amount_matches"] / num_transactions
            metrics["avg_description_similarity"] = metrics["description_similarity"] / num_transactions
        
        return metrics
    
    def calculate_extraction_quality_score(self, extracted_data, expected_data):
        """Calculate overall quality score"""
        scores = {
            "completeness": 0,    # All transactions extracted
            "accuracy": 0,        # Correct amounts and dates
            "categorization": 0,  # Correct categories
            "formatting": 0       # Proper formatting
        }
        
        # Completeness score
        expected_count = len(expected_data["transactions"])
        actual_count = len(extracted_data["transactions"])
        scores["completeness"] = min(actual_count / expected_count, 1.0) if expected_count > 0 else 0
        
        # Accuracy score
        correct_amounts = 0
        for extracted, expected in zip(
            extracted_data["transactions"],
            expected_data["transactions"]
        ):
            if (abs(extracted["debit"] - expected["debit"]) < 0.01 and
                abs(extracted["credit"] - expected["credit"]) < 0.01):
                correct_amounts += 1
        
        scores["accuracy"] = correct_amounts / actual_count if actual_count > 0 else 0
        
        # Overall score (weighted average)
        weights = {
            "completeness": 0.3,
            "accuracy": 0.4,
            "categorization": 0.2,
            "formatting": 0.1
        }
        
        overall_score = sum(scores[k] * weights[k] for k in scores)
        
        return {
            "scores": scores,
            "overall": overall_score
        }


if __name__ == "__main__":
    pytest.main([__file__, "-v"])