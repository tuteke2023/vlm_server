#!/usr/bin/env python3
"""LangChain-based transaction classifier with structured output and corrections"""

from typing import List, Dict, Optional, Tuple
from pydantic import BaseModel, Field, validator
import json
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for structured output
class TransactionClassification(BaseModel):
    """Structured classification result for a single transaction"""
    gst_applicable: bool = Field(description="Whether GST applies to this transaction")
    gst_amount: float = Field(description="GST amount in dollars", ge=0)
    gst_category: str = Field(description="GST category (GST on purchases, GST on sales, GST-free supply, etc.)")
    category: str = Field(description="Main expense/income category")
    subcategory: str = Field(description="Detailed subcategory")
    business_percentage: int = Field(description="Percentage of transaction that is business-related", ge=0, le=100)
    tax_deductible: bool = Field(description="Whether the expense is tax deductible")
    notes: str = Field(description="Additional notes or reasoning")
    
    @validator('gst_amount')
    def validate_gst_amount(cls, v, values):
        """Ensure GST amount is 0 if GST not applicable"""
        if 'gst_applicable' in values and not values['gst_applicable']:
            return 0.0
        return v

class TransactionBatch(BaseModel):
    """Batch of classified transactions"""
    transactions: List[TransactionClassification]

class LangChainTransactionClassifier:
    """Enhanced transaction classifier using LangChain for better structured output"""
    
    def __init__(self, corrections_db_path: str = "web_interface/transaction_corrections_db.json"):
        """Initialize with corrections database"""
        self.corrections_db = self._load_corrections_db(corrections_db_path)
        self.few_shot_examples = self._prepare_few_shot_examples()
        
    def _load_corrections_db(self, path: str) -> Dict:
        """Load the corrections database"""
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load corrections database: {e}")
            return {"gst_rules": {}, "transaction_corrections": [], "learning_examples": []}
    
    def _prepare_few_shot_examples(self) -> List[Dict]:
        """Prepare few-shot examples from the corrections database"""
        examples = []
        
        # Convert learning examples to few-shot format
        for example in self.corrections_db.get("learning_examples", []):
            input_text = f"Transaction: {example['description']}, Amount: ${example['amount']}, Type: {example['type']}"
            output = example['correct_classification']
            
            examples.append({
                "input": input_text,
                "output": json.dumps(output, indent=2)
            })
        
        return examples
    
    def create_classification_prompt(self, transactions: List[Dict]) -> str:
        """Create a detailed prompt for transaction classification"""
        
        # GST rules summary
        gst_rules = self.corrections_db.get("gst_rules", {})
        rules_text = "\n".join([f"- {rule['rule']}" for rule in gst_rules.get("rules", [])])
        
        # Few-shot examples
        examples_text = ""
        for example in self.few_shot_examples[:3]:  # Use top 3 examples
            examples_text += f"\nExample:\nInput: {example['input']}\nOutput: {example['output']}\n"
        
        # Transaction list
        transaction_text = ""
        for i, txn in enumerate(transactions):
            amount = txn.get('debit', 0) or txn.get('credit', 0)
            txn_type = 'debit' if txn.get('debit', 0) > 0 else 'credit'
            transaction_text += f"\n{i+1}. Date: {txn['date']}, Description: {txn['description']}, "
            transaction_text += f"Amount: ${amount}, Type: {txn_type}, Balance: ${txn['balance']}"
        
        prompt = f"""You are an expert Australian tax accountant classifying bank transactions.

GST RULES:
{rules_text}

IMPORTANT CORRECTIONS:
- Payroll/wages are always GST-free (no GST applicable)
- GST amount = Total amount ÷ 11 (for GST-inclusive prices)
- Income transactions (credits) for goods/services include GST to be paid to ATO
- Expense transactions (debits) for business purchases include GST that can be claimed
- Groceries from supermarkets are mostly GST-free and personal expenses

{examples_text}

Please classify these transactions:
{transaction_text}

For each transaction, provide:
1. gst_applicable: true/false
2. gst_amount: calculated GST amount (0 if not applicable)
3. gst_category: "GST on purchases", "GST on sales", "GST-free supply", or "Input-taxed"
4. category: main category (e.g., "Office Expenses", "Income/Revenue", "Personal/Non-business")
5. subcategory: specific subcategory
6. business_percentage: 0-100
7. tax_deductible: true/false
8. notes: brief explanation

Return the classifications as a JSON array with one object per transaction."""
        
        return prompt
    
    def parse_vlm_response(self, response: str) -> List[Dict]:
        """Parse VLM response with multiple fallback strategies"""
        classifications = []
        
        # Strategy 1: Try to find JSON array
        json_match = re.search(r'\[[\s\S]*\]', response)
        if json_match:
            try:
                data = json.loads(json_match.group(0))
                if isinstance(data, list):
                    return data
            except json.JSONDecodeError:
                pass
        
        # Strategy 2: Try to find individual JSON objects
        object_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        matches = re.findall(object_pattern, response)
        
        for match in matches:
            try:
                obj = json.loads(match)
                if 'gst_applicable' in obj:  # Verify it's a classification object
                    classifications.append(obj)
            except json.JSONDecodeError:
                continue
        
        return classifications
    
    def apply_corrections(self, transaction: Dict, classification: Dict) -> Dict:
        """Apply pattern-based corrections to a classification"""
        description = transaction.get('description', '').lower()
        
        # Check each correction pattern
        for correction in self.corrections_db.get('transaction_corrections', []):
            pattern = correction['pattern'].lower()
            if re.search(pattern, description):
                # Apply corrections
                for key, value in correction['corrections'].items():
                    classification[key] = value
                logger.info(f"Applied correction for pattern '{pattern}' to '{transaction['description']}'")
                break
        
        # Ensure GST calculations are correct
        if classification.get('gst_applicable'):
            amount = transaction.get('debit', 0) or transaction.get('credit', 0)
            # GST = Total ÷ 11 for GST-inclusive prices
            classification['gst_amount'] = round(amount / 11, 2)
        else:
            classification['gst_amount'] = 0
        
        # Add transaction details
        classification['original_amount'] = transaction.get('debit', 0) or transaction.get('credit', 0)
        classification['transaction_type'] = 'debit' if transaction.get('debit', 0) > 0 else 'credit'
        
        return classification
    
    def validate_classification(self, classification: Dict) -> Tuple[bool, List[str]]:
        """Validate a classification and return (is_valid, errors)"""
        errors = []
        
        # Check required fields
        required_fields = ['gst_applicable', 'gst_amount', 'category', 'business_percentage']
        for field in required_fields:
            if field not in classification:
                errors.append(f"Missing required field: {field}")
        
        # Validate GST logic
        if classification.get('gst_applicable', False) and classification.get('gst_amount', 0) == 0:
            errors.append("GST is applicable but amount is 0")
        
        if not classification.get('gst_applicable', False) and classification.get('gst_amount', 0) > 0:
            errors.append("GST is not applicable but amount is greater than 0")
        
        # Validate business percentage
        business_pct = classification.get('business_percentage', 0)
        if not (0 <= business_pct <= 100):
            errors.append(f"Invalid business percentage: {business_pct}")
        
        return len(errors) == 0, errors
    
    def classify_transactions(self, transactions: List[Dict], vlm_response: Optional[str] = None) -> List[Dict]:
        """
        Classify transactions with VLM response and corrections
        
        Args:
            transactions: List of transaction dictionaries
            vlm_response: Optional VLM classification response
            
        Returns:
            List of classified transactions with corrections applied
        """
        results = []
        
        # Parse VLM response if provided
        vlm_classifications = []
        if vlm_response:
            vlm_classifications = self.parse_vlm_response(vlm_response)
        
        # Process each transaction
        for i, transaction in enumerate(transactions):
            # Start with VLM classification if available
            if i < len(vlm_classifications):
                classification = vlm_classifications[i].copy()
            else:
                # Default classification if VLM didn't provide one
                classification = {
                    "gst_applicable": False,
                    "gst_amount": 0,
                    "gst_category": "Unknown",
                    "category": "Uncategorized",
                    "subcategory": "Other",
                    "business_percentage": 0,
                    "tax_deductible": False,
                    "notes": "No classification available"
                }
            
            # Apply corrections
            classification = self.apply_corrections(transaction, classification)
            
            # Validate and log any issues
            is_valid, errors = self.validate_classification(classification)
            if not is_valid:
                logger.warning(f"Classification validation errors for {transaction['description']}: {errors}")
            
            # Merge with original transaction
            result = transaction.copy()
            result.update(classification)
            results.append(result)
        
        return results
    
    def create_validation_chain(self, classifications: List[Dict]) -> Dict:
        """Create a validation summary for the classifications"""
        summary = {
            "total_transactions": len(classifications),
            "total_gst": sum(c.get('gst_amount', 0) for c in classifications),
            "business_expenses": sum(
                c.get('original_amount', 0) * c.get('business_percentage', 0) / 100
                for c in classifications if c.get('transaction_type') == 'debit'
            ),
            "tax_deductible_total": sum(
                c.get('original_amount', 0) 
                for c in classifications 
                if c.get('tax_deductible', False) and c.get('transaction_type') == 'debit'
            ),
            "categories": {}
        }
        
        # Count by category
        for c in classifications:
            cat = c.get('category', 'Unknown')
            if cat not in summary['categories']:
                summary['categories'][cat] = {"count": 0, "total": 0}
            summary['categories'][cat]['count'] += 1
            summary['categories'][cat]['total'] += c.get('original_amount', 0)
        
        return summary

# Example usage for testing
if __name__ == "__main__":
    # Test transactions
    test_transactions = [
        {
            "date": "Oct 14",
            "description": "Payroll Deposit - HOTEL",
            "debit": 0,
            "credit": 694.81,
            "balance": 695.36
        },
        {
            "date": "Oct 17",
            "description": "Officeworks - Office Supplies",
            "debit": 89.50,
            "credit": 0,
            "balance": 605.86
        }
    ]
    
    # Initialize classifier
    classifier = LangChainTransactionClassifier()
    
    # Create prompt (for demonstration)
    prompt = classifier.create_classification_prompt(test_transactions)
    print("Generated Prompt:")
    print("=" * 80)
    print(prompt)
    print("=" * 80)
    
    # Simulate VLM response
    mock_vlm_response = """
    [
        {
            "gst_applicable": true,
            "gst_amount": 63.16,
            "gst_category": "GST on sales",
            "category": "Income/Revenue",
            "subcategory": "Wages",
            "business_percentage": 100,
            "tax_deductible": false,
            "notes": "Payroll income"
        },
        {
            "gst_applicable": true,
            "gst_amount": 8.14,
            "gst_category": "GST on purchases",
            "category": "Office Expenses",
            "subcategory": "Supplies",
            "business_percentage": 100,
            "tax_deductible": true,
            "notes": "Office supplies purchase"
        }
    ]
    """
    
    # Classify with corrections
    results = classifier.classify_transactions(test_transactions, mock_vlm_response)
    
    print("\nClassification Results with Corrections:")
    for r in results:
        print(f"\n{r['description']}:")
        print(f"  GST: ${r.get('gst_amount', 0):.2f} ({r.get('gst_category', 'N/A')})")
        print(f"  Category: {r.get('category', 'N/A')} - {r.get('subcategory', 'N/A')}")
        print(f"  Notes: {r.get('notes', 'N/A')}")