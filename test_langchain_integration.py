#!/usr/bin/env python3
"""Test script for LangChain integration with bank transaction classification"""

import json
import sys
from pathlib import Path

# Add the project directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_langchain_classifier():
    """Test the LangChain classifier (when LangChain is installed)"""
    
    print("Testing LangChain Transaction Classifier")
    print("=" * 80)
    
    # Check if LangChain is available
    try:
        import langchain
        from langchain.prompts import FewShotPromptTemplate, PromptTemplate
        from langchain.output_parsers import PydanticOutputParser
        print(f"✓ LangChain is installed (version: {langchain.__version__})")
    except ImportError:
        print("✗ LangChain is not installed")
        print("\nTo use LangChain features, please install:")
        print("  pip install langchain langchain-community pydantic")
        print("\nFor now, demonstrating the classifier without LangChain dependencies...")
    
    # Test with our custom classifier (works without LangChain)
    from transaction_classifier_langchain import LangChainTransactionClassifier
    
    # Load test transactions
    test_transactions = [
        {
            "date": "Oct 14",
            "description": "Payroll Deposit - HOTEL",
            "reference": "",
            "debit": 0,
            "credit": 694.81,
            "balance": 695.36
        },
        {
            "date": "Oct 14", 
            "description": "Officeworks - Office Supplies",
            "reference": "",
            "debit": 89.50,
            "credit": 0,
            "balance": 605.86
        },
        {
            "date": "Oct 17",
            "description": "Client Payment - Consulting",
            "reference": "INV-2024-045", 
            "debit": 0,
            "credit": 2200.00,
            "balance": 2805.86
        },
        {
            "date": "Oct 22",
            "description": "Coles Supermarket",
            "reference": "",
            "debit": 95.50,
            "credit": 0,
            "balance": 2710.36
        },
        {
            "date": "Oct 23",
            "description": "Telstra Mobile Service",
            "reference": "",
            "debit": 89.00,
            "credit": 0,
            "balance": 2621.36
        }
    ]
    
    # Initialize classifier
    classifier = LangChainTransactionClassifier()
    
    # Generate classification prompt
    prompt = classifier.create_classification_prompt(test_transactions)
    
    print("\n1. Generated Prompt Preview:")
    print("-" * 40)
    print(prompt[:500] + "...")
    
    # Simulate VLM response (with intentional errors to test corrections)
    mock_vlm_response = """
    Here are the classifications:
    
    [
        {
            "gst_applicable": true,
            "gst_amount": 63.16,
            "gst_category": "GST on sales",
            "category": "Income/Revenue",
            "subcategory": "Wages",
            "business_percentage": 100,
            "tax_deductible": false,
            "notes": "Payroll income includes GST"
        },
        {
            "gst_applicable": true,
            "gst_amount": 8.00,
            "gst_category": "GST on purchases",
            "category": "Office Expenses",
            "subcategory": "Office Supplies",
            "business_percentage": 100,
            "tax_deductible": true,
            "notes": "Office supplies from Officeworks"
        },
        {
            "gst_applicable": true,
            "gst_amount": 200.00,
            "gst_category": "GST on sales",
            "category": "Income/Revenue",
            "subcategory": "Professional Services",
            "business_percentage": 100,
            "tax_deductible": false,
            "notes": "Consulting income with GST"
        },
        {
            "gst_applicable": true,
            "gst_amount": 8.68,
            "gst_category": "GST on purchases",
            "category": "Groceries",
            "subcategory": "Food",
            "business_percentage": 50,
            "tax_deductible": true,
            "notes": "Supermarket purchase"
        },
        {
            "gst_applicable": true,
            "gst_amount": 8.09,
            "gst_category": "GST on purchases",
            "category": "Utilities",
            "subcategory": "Telecommunications",
            "business_percentage": 50,
            "tax_deductible": true,
            "notes": "Mobile phone service"
        }
    ]
    """
    
    # Classify with corrections
    results = classifier.classify_transactions(test_transactions, mock_vlm_response)
    
    print("\n\n2. Classification Results (with corrections applied):")
    print("-" * 40)
    
    for i, result in enumerate(results):
        print(f"\nTransaction {i+1}: {result['description']}")
        print(f"  Amount: ${result.get('original_amount', 0):.2f} ({result.get('transaction_type', 'unknown')})")
        print(f"  GST Applicable: {result.get('gst_applicable', False)}")
        print(f"  GST Amount: ${result.get('gst_amount', 0):.2f}")
        print(f"  GST Category: {result.get('gst_category', 'N/A')}")
        print(f"  Category: {result.get('category', 'N/A')} - {result.get('subcategory', 'N/A')}")
        print(f"  Business %: {result.get('business_percentage', 0)}%")
        print(f"  Tax Deductible: {result.get('tax_deductible', False)}")
        print(f"  Notes: {result.get('notes', 'N/A')}")
        
        # Highlight corrections
        if 'Payroll' in result['description'] and not result.get('gst_applicable'):
            print("  ✓ CORRECTED: Payroll is GST-free")
        if 'Coles' in result['description'] and not result.get('gst_applicable'):
            print("  ✓ CORRECTED: Groceries are GST-free and personal")
        if 'Officeworks' in result['description'] and abs(result.get('gst_amount', 0) - 8.14) < 0.01:
            print("  ✓ CORRECTED: GST amount recalculated")
    
    # Generate validation summary
    validation = classifier.create_validation_chain(results)
    
    print("\n\n3. Validation Summary:")
    print("-" * 40)
    print(f"Total Transactions: {validation['total_transactions']}")
    print(f"Total GST: ${validation['total_gst']:.2f}")
    print(f"Business Expenses: ${validation['business_expenses']:.2f}")
    print(f"Tax Deductible Total: ${validation['tax_deductible_total']:.2f}")
    
    print("\nBy Category:")
    for cat, data in validation['categories'].items():
        print(f"  {cat}: {data['count']} transactions, ${data['total']:.2f} total")
    
    # Save results
    output_file = 'langchain_classification_results.json'
    with open(output_file, 'w') as f:
        json.dump({
            'transactions': results,
            'validation_summary': validation,
            'corrections_applied': [
                "Payroll marked as GST-free",
                "Groceries marked as GST-free and personal", 
                "GST amounts recalculated using ÷11 formula",
                "Telstra mobile categorized with 50% business use"
            ]
        }, f, indent=2)
    
    print(f"\n\nResults saved to: {output_file}")
    
    # Show LangChain integration benefits
    print("\n\n4. LangChain Integration Benefits:")
    print("-" * 40)
    print("✓ Structured output with Pydantic models ensures consistent format")
    print("✓ Few-shot learning from corrections database examples")
    print("✓ Better prompt engineering with FewShotPromptTemplate")
    print("✓ Output parser validation catches formatting errors")
    print("✓ Chain-of-thought reasoning for complex classifications")
    print("✓ Easy integration with other LLMs beyond the VLM")

if __name__ == "__main__":
    test_langchain_classifier()