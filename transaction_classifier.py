#!/usr/bin/env python3
"""
Transaction classifier with VLM and correction database
Includes post-processing validation and learning
"""

import json
import re
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class TransactionClassifier:
    def __init__(self, corrections_db_path: str = "transaction_corrections_db.json"):
        """Initialize with corrections database"""
        self.corrections_db = self._load_corrections_db(corrections_db_path)
        self.pattern_cache = self._compile_patterns()
    
    def _load_corrections_db(self, path: str) -> Dict:
        """Load corrections database"""
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Corrections database not found at {path}")
            return {"gst_rules": {}, "transaction_corrections": [], "learning_examples": []}
    
    def _compile_patterns(self) -> List[tuple]:
        """Compile regex patterns for faster matching"""
        patterns = []
        for correction in self.corrections_db.get('transaction_corrections', []):
            pattern = re.compile(correction['pattern'], re.IGNORECASE)
            patterns.append((pattern, correction['corrections']))
        return patterns
    
    def apply_corrections(self, transaction: Dict, vlm_classification: Dict) -> Dict:
        """Apply corrections based on pattern matching and rules"""
        description = transaction.get('description', '').lower()
        amount = transaction.get('debit', 0) or transaction.get('credit', 0)
        is_credit = transaction.get('credit', 0) > 0
        
        # Start with VLM classification
        result = vlm_classification.copy()
        
        # Apply pattern-based corrections
        for pattern, corrections in self.pattern_cache:
            if pattern.search(description):
                logger.info(f"Applying correction for pattern: {pattern.pattern}")
                result.update(corrections)
                break
        
        # Apply GST calculation rules
        if result.get('gst_applicable', False) and amount > 0:
            # Calculate GST as amount ÷ 11 for GST-inclusive amounts
            result['gst_amount'] = round(amount / 11, 2)
        else:
            result['gst_amount'] = 0
        
        # Validate and fix common errors
        
        # 1. Payroll/wages should never have GST
        if any(word in description for word in ['payroll', 'salary', 'wages']):
            result['gst_applicable'] = False
            result['gst_amount'] = 0
            result['gst_category'] = 'GST-free supply'
            if is_credit:
                result['category'] = 'Income/Revenue'
                result['subcategory'] = 'Wages & Salaries'
        
        # 2. Income transactions (credits) should be categorized correctly
        if is_credit and result.get('category') != 'Income/Revenue':
            result['category'] = 'Income/Revenue'
        
        # 3. Expense transactions (debits) should not be Income/Revenue
        if not is_credit and result.get('category') == 'Income/Revenue':
            # Fix miscategorized expenses
            if 'supermarket' in description or 'coles' in description:
                result['category'] = 'Personal/Non-business'
                result['subcategory'] = 'Groceries'
            elif 'tax' in description and 'ato' in description:
                result['category'] = 'Taxes & Licenses'
                result['subcategory'] = 'Tax Payments'
            else:
                result['category'] = 'Operating Expenses'
        
        # 4. Basic groceries are GST-free
        if any(word in description for word in ['coles', 'woolworths', 'aldi', 'supermarket']):
            result['gst_applicable'] = False
            result['gst_amount'] = 0
            result['gst_category'] = 'GST-free supply'
            result['business_percentage'] = 0
            result['tax_deductible'] = False
        
        # Add transaction details to result
        result['original_amount'] = amount
        result['transaction_type'] = 'credit' if is_credit else 'debit'
        
        return result
    
    def create_enhanced_prompt(self, transactions: List[Dict]) -> str:
        """Create prompt with corrections database"""
        prompt = f"""You are an Australian tax and accounting expert. Analyze these bank transactions using the provided GST rules and examples.

**IMPORTANT GST RULES:**
{json.dumps(self.corrections_db.get('gst_rules', {}), indent=2)}

**EXAMPLES TO FOLLOW:**
"""
        
        # Add learning examples
        for example in self.corrections_db.get('learning_examples', [])[:3]:
            prompt += f"""
Example: {example['description']} - ${example['amount']} ({example['type']})
Correct classification: {json.dumps(example['correct_classification'], indent=2)}
"""
        
        prompt += """

Now classify these transactions following the same rules:

For each transaction, provide:
- gst_applicable: boolean
- gst_amount: number (GST = total ÷ 11 for GST-inclusive)
- gst_category: string
- business_percentage: number (0-100)
- category: string
- subcategory: string
- tax_deductible: boolean
- reasoning: string

Return ONLY a JSON array. No other text.

Transactions:
""" + json.dumps(transactions, indent=2)
        
        return prompt
    
    def classify_transactions(self, transactions: List[Dict], vlm_response: str) -> List[Dict]:
        """Classify transactions using VLM response and corrections"""
        # Parse VLM response
        try:
            # Extract JSON from response
            start = vlm_response.find('[')
            end = vlm_response.rfind(']') + 1
            if start >= 0 and end > start:
                vlm_classifications = json.loads(vlm_response[start:end])
            else:
                logger.error("No JSON array found in VLM response")
                vlm_classifications = [{}] * len(transactions)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse VLM response: {e}")
            vlm_classifications = [{}] * len(transactions)
        
        # Apply corrections to each transaction
        results = []
        for i, transaction in enumerate(transactions):
            vlm_class = vlm_classifications[i] if i < len(vlm_classifications) else {}
            corrected = self.apply_corrections(transaction, vlm_class)
            
            # Merge with original transaction data
            result = transaction.copy()
            result.update(corrected)
            results.append(result)
        
        return results
    
    def save_feedback(self, transaction: Dict, user_correction: Dict):
        """Save user feedback for future learning"""
        # This would append to a feedback file for model fine-tuning
        feedback = {
            "transaction": transaction,
            "user_correction": user_correction,
            "timestamp": datetime.now().isoformat()
        }
        
        # In production, save to database or feedback file
        logger.info(f"Feedback saved: {feedback}")

# Example usage
if __name__ == "__main__":
    classifier = TransactionClassifier()
    
    # Test transaction
    test_trans = [{
        "date": "Oct 14",
        "description": "Payroll Deposit - HOTEL",
        "debit": 0,
        "credit": 694.81,
        "balance": 695.36
    }]
    
    # Simulate VLM response
    vlm_response = """[{
        "gst_applicable": true,
        "gst_amount": 63.16,
        "category": "Income/Revenue",
        "business_percentage": 100
    }]"""
    
    results = classifier.classify_transactions(test_trans, vlm_response)
    print(json.dumps(results[0], indent=2))