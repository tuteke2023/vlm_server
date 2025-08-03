# JSON-First Architecture for Bank Statement Processing

## Benefits of JSON-First Approach

### 1. **Single Source of Truth**
- JSON file serves as canonical extracted data
- No re-parsing needed for different outputs
- Consistent data across all downstream processes

### 2. **Efficient Multi-Stage Processing**
```
Image → VLM (JSON) → Local JSON File → Multiple Outputs
                           ↓
                    ┌──────┴──────┬─────────┬──────────┐
                    │             │         │          │
                   CSV       GST Coding  Analytics  Tax Reports
```

### 3. **Reduced VLM Calls**
- Extract once, process many times
- Cost-effective for expensive AI operations
- Faster subsequent operations

### 4. **Enhanced Processing Capabilities**
- Add GST/VAT coding
- Classify transactions for accounting
- Generate financial reports
- Tax categorization
- Expense tracking
- Budget analysis

## Proposed Implementation

### 1. Modified VLM Extraction Prompt
```python
BANK_STATEMENT_JSON_PROMPT = """
Analyze this bank statement and extract ALL transactions in JSON format.

Return ONLY valid JSON with this exact structure:
{
  "account_number": "****1234",
  "statement_period": "October 2023",
  "opening_balance": 0.55,
  "closing_balance": -72.47,
  "transactions": [
    {
      "date": "2023-10-14",
      "description": "Payroll Deposit - HOTEL",
      "reference": "",
      "debit": 0,
      "credit": 694.81,
      "balance": 695.36,
      "merchant_category": "",
      "gst_applicable": false,
      "gst_amount": 0
    }
  ]
}

Important:
- Use ISO date format (YYYY-MM-DD)
- Debit and credit as numbers, not strings
- Include all fields even if empty
- GST fields will be populated later
"""
```

### 2. New Endpoint for JSON Extraction
```python
@app.post("/api/v1/bank_extract_json")
async def extract_bank_statement_json(request: ExtractRequest):
    """Extract bank statement to JSON and save locally"""
    
    # Generate with JSON-specific prompt
    ai_response = await vlm_server.generate_with_prompt(
        request.messages,
        system_prompt=BANK_STATEMENT_JSON_PROMPT
    )
    
    # Parse and validate JSON
    try:
        bank_data = json.loads(ai_response.response)
        
        # Save to local file with timestamp
        filename = f"bank_statements/stmt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(bank_data, f, indent=2)
        
        return {
            "status": "success",
            "filename": filename,
            "transaction_count": len(bank_data.get("transactions", [])),
            "data": bank_data
        }
    except json.JSONDecodeError:
        # Fallback to table parser if JSON fails
        return await fallback_extraction(ai_response.response)
```

### 3. GST Processing Endpoint
```python
@app.post("/api/v1/process_gst")
async def process_gst(request: GSTRequest):
    """Add GST coding to saved JSON file"""
    
    # Load saved JSON
    with open(request.filename, 'r') as f:
        bank_data = json.load(f)
    
    # Process each transaction for GST
    for trans in bank_data["transactions"]:
        # Use AI to determine GST applicability
        gst_prompt = f"""
        Transaction: {trans['description']}
        Amount: ${trans['debit'] or trans['credit']}
        
        Determine:
        1. Is GST applicable? (yes/no)
        2. If yes, what's the GST amount?
        3. GST category code
        
        Common categories:
        - Food/Groceries: Usually no GST
        - Services: 10% GST
        - Capital items: 10% GST with input credit
        """
        
        gst_response = await vlm_server.generate(gst_prompt)
        
        # Parse and update transaction
        trans["gst_applicable"] = gst_response.get("applicable", False)
        trans["gst_amount"] = gst_response.get("amount", 0)
        trans["gst_category"] = gst_response.get("category", "")
    
    # Save updated JSON
    updated_filename = request.filename.replace('.json', '_gst.json')
    with open(updated_filename, 'w') as f:
        json.dump(bank_data, f, indent=2)
    
    return {"status": "success", "filename": updated_filename}
```

### 4. Transaction Classification Endpoint
```python
@app.post("/api/v1/classify_transactions")
async def classify_transactions(request: ClassifyRequest):
    """Enhanced classification with business rules"""
    
    with open(request.filename, 'r') as f:
        bank_data = json.load(f)
    
    # Batch process for efficiency
    transactions_text = "\n".join([
        f"{t['date']}: {t['description']} - ${t['debit'] or t['credit']}"
        for t in bank_data["transactions"]
    ])
    
    classification_prompt = f"""
    Classify these transactions for accounting:
    {transactions_text}
    
    Categories:
    - Operating Expenses
    - Capital Expenses  
    - Revenue/Income
    - Loan Payments
    - Tax Payments
    - Personal Drawings
    
    Also identify:
    - Tax deductible (yes/no)
    - Business percentage (0-100%)
    - Accounting code
    """
    
    classifications = await vlm_server.generate(classification_prompt)
    
    # Update and save
    # ... implementation
```

### 5. Multi-Format Export
```python
@app.post("/api/v1/export_from_json")
async def export_from_json(request: ExportRequest):
    """Export saved JSON to various formats"""
    
    with open(request.filename, 'r') as f:
        bank_data = json.load(f)
    
    if request.format == "csv":
        return export_to_csv(bank_data)
    elif request.format == "quickbooks":
        return export_to_quickbooks(bank_data)
    elif request.format == "xero":
        return export_to_xero(bank_data)
    elif request.format == "tax_summary":
        return generate_tax_summary(bank_data)
```

## Workflow Benefits

### Current Workflow (Inefficient)
```
Image → VLM → Table Text → Parse → CSV
         ↓
    (Reprocess)
         ↓
Image → VLM → Classification
         ↓
    (Reprocess)
         ↓  
Image → VLM → GST Coding
```

### JSON-First Workflow (Efficient)
```
Image → VLM → JSON File
                  ↓
          ┌───────┼───────┬──────────┬─────────┐
          │       │       │          │         │
         CSV   GST Code  Classify  Reports  Analytics
         (instant) (AI)    (AI)    (instant) (instant)
```

## Storage Structure
```
bank_statements/
├── stmt_20250803_142530.json          # Original extraction
├── stmt_20250803_142530_gst.json      # With GST coding
├── stmt_20250803_142530_classified.json # With classifications
├── exports/
│   ├── stmt_20250803_142530.csv
│   ├── stmt_20250803_142530_quickbooks.csv
│   └── stmt_20250803_142530_tax_summary.pdf
```

## Key Advantages

1. **Performance**: One VLM call vs multiple
2. **Consistency**: Same data across all exports
3. **Flexibility**: Easy to add new processing steps
4. **Audit Trail**: Complete history of transformations
5. **Offline Processing**: Can reprocess without original image
6. **Batch Operations**: Process multiple statements together
7. **Integration Ready**: JSON is universal format

## Implementation Priority

1. **Phase 1**: JSON extraction and storage
2. **Phase 2**: Basic CSV/JSON export from saved files
3. **Phase 3**: GST/Tax coding with AI
4. **Phase 4**: Advanced classification and reporting
5. **Phase 5**: Integration with accounting software