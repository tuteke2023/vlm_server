# LangChain Integration for Bank Statement Processing

## Overview

This document describes the LangChain integration added to the VLM Server's bank statement processor. LangChain enhances the transaction classification process with structured output parsing, validation, and pattern-based corrections.

## Key Features

### 1. Structured Output with Pydantic

```python
class TransactionClassification(BaseModel):
    gst_applicable: bool
    gst_amount: float
    gst_category: str
    category: str
    subcategory: str
    business_percentage: int
    tax_deductible: bool
    notes: str
```

- Ensures consistent output format from VLM
- Automatic validation of data types and ranges
- Clear schema for downstream processing

### 2. Few-Shot Learning

The system uses examples from the corrections database to guide the VLM:

```json
{
  "description": "Payroll Deposit - HOTEL",
  "correct_classification": {
    "gst_applicable": false,
    "gst_category": "GST-free supply",
    "reasoning": "Wages and salaries are GST-free"
  }
}
```

### 3. Pattern-Based Corrections

Automatic corrections are applied based on transaction patterns:

- **Payroll/Wages**: Always marked as GST-free
- **Supermarkets**: Marked as GST-free personal expenses
- **Office Supplies**: GST calculated as amount ÷ 11
- **Telecommunications**: Set to 50% business use by default

### 4. Validation Chains

The system validates:
- GST calculations (amount ÷ 11 for inclusive prices)
- Category consistency (credits = income, debits = expenses)
- Business percentage (0-100%)
- Required fields presence

## Architecture

### Components

1. **transaction_classifier_langchain.py**
   - Core LangChain classifier implementation
   - Handles VLM response parsing and corrections
   - Provides validation and summary generation

2. **langchain_classifier_full.py**
   - Full LangChain implementation with prompts
   - FewShotPromptTemplate for learning
   - Pydantic output parser integration

3. **vlm_langchain_endpoint.py**
   - FastAPI endpoints for LangChain classification
   - REST API for web interface integration
   - Correction database management

4. **bank_processor_langchain.js**
   - Frontend integration with LangChain endpoints
   - Enhanced UI feedback for corrections
   - Detailed transaction views with classifications

## Usage

### Python API

```python
from transaction_classifier_langchain import LangChainTransactionClassifier

# Initialize classifier
classifier = LangChainTransactionClassifier()

# Classify transactions
results = classifier.classify_transactions(
    transactions,  # List of transaction dictionaries
    vlm_response   # Optional VLM classification response
)

# Get validation summary
summary = classifier.create_validation_chain(results)
```

### REST API

```bash
# Classify transactions
POST /api/v1/langchain/classify_transactions
{
  "transactions": [...],
  "use_vlm": true
}

# Get corrections database
GET /api/v1/langchain/corrections_database
```

### Web Interface

The bank processor automatically uses LangChain when available:

1. Upload bank statement
2. Extract transactions
3. Click "Add GST Coding" or "Classify Transactions"
4. LangChain applies corrections and validations
5. Export enhanced CSV with all classifications

## Benefits

### Without LangChain
- Manual parsing of unstructured VLM responses
- No validation of output format
- Hard-coded correction rules scattered in code
- Limited error handling for malformed responses

### With LangChain
- ✅ Automatic structured output parsing
- ✅ Built-in validation with Pydantic models
- ✅ Centralized corrections database
- ✅ Robust error handling and retry logic
- ✅ Easy to extend with new LLMs
- ✅ Better prompt engineering with few-shot examples
- ✅ Observability through LangSmith (when configured)

## Corrections Applied

The system automatically fixes common VLM errors:

1. **Payroll GST Error**: VLM often incorrectly adds GST to wages
   - Correction: Mark as GST-free, set amount to 0

2. **GST Calculation**: VLM may calculate GST incorrectly
   - Correction: Recalculate as amount ÷ 11

3. **Category Misclassification**: VLM may categorize incorrectly
   - Correction: Apply pattern-based category rules

4. **Business Percentage**: VLM may not set appropriate percentages
   - Correction: Apply standard percentages by category

## Testing

Run the test suite:

```bash
# Test LangChain classifier
python test_langchain_integration.py

# Test full integration
python test_langchain_full_integration.py
```

## Installation

LangChain is optional but recommended:

```bash
pip install langchain langchain-community pydantic
```

The system gracefully falls back to standard VLM processing if LangChain is not available.

## Future Enhancements

1. **Multi-LLM Support**: Easy to add GPT-4, Claude, or other models
2. **Memory**: Add conversation memory for multi-turn classification
3. **Agents**: Use LangChain agents for complex reasoning tasks
4. **RAG**: Integrate with vector databases for historical transaction matching
5. **Streaming**: Support streaming responses for large batches

## Configuration

The corrections database is located at:
`web_interface/transaction_corrections_db.json`

To add new correction patterns:

```json
{
  "pattern": "your-pattern|alternative",
  "corrections": {
    "gst_applicable": true/false,
    "category": "Your Category",
    ...
  }
}
```

## Troubleshooting

1. **LangChain not installed**: System falls back to standard processing
2. **VLM timeout**: Increase timeout in vlm_langchain_endpoint.py
3. **Incorrect classifications**: Add patterns to corrections database
4. **Validation errors**: Check Pydantic schema requirements

## Summary

LangChain integration significantly improves the accuracy and reliability of bank statement processing by:

- Ensuring consistent structured output
- Automatically correcting common errors
- Providing detailed validation and summaries
- Making the system extensible and maintainable

The integration is designed to be optional, allowing the system to function without LangChain while providing enhanced capabilities when available.