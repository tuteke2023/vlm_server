# JSON-First Bank Statement Processor

## Overview

The JSON-first bank statement processor is a new feature that enables efficient, multi-stage processing of bank statements. Instead of re-extracting data for each operation, it extracts once to JSON and then performs multiple operations on the saved data.

## Features

### 1. **One-Time Extraction**
- Extract bank statement data once using the VLM
- Save as structured JSON for future processing
- No need to re-process the original image

### 2. **Progressive Enhancement**
- GST/Tax coding
- Transaction classification
- Business/Personal splitting
- Custom annotations

### 3. **Multiple Export Formats**
- CSV for spreadsheets
- QuickBooks format
- Xero format
- Tax reports

## How to Use

### Access the Bank Processor

1. Navigate to `http://localhost:8080/bank_processor.html`
2. Or click "Bank Processor" in the navigation menu

### Processing Workflow

#### Step 1: Upload Statement
- Drag and drop or click to upload bank statement
- Supports PDF, PNG, JPG, JPEG formats

#### Step 2: Extract to JSON
- Choose "JSON (Recommended for processing)" format
- Click "Extract Statement"
- Review extracted data in preview

#### Step 3: Save JSON
- Click "Save JSON" to download and store locally
- Files are saved with timestamp for easy tracking

#### Step 4: Process Data
- **Add GST/Tax**: Identify taxable transactions
- **Classify**: Categorize for accounting
- **Business/Personal**: Split mixed statements
- **Add Notes**: Annotate specific transactions

#### Step 5: Export
- **CSV**: Standard spreadsheet format
- **QuickBooks**: Direct import to QuickBooks
- **Xero**: Xero accounting format
- **Tax Report**: GST/Tax summary

## API Endpoints

### Extract to JSON
```
POST /api/v1/bank_extract_json
```

Request:
```json
{
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "text", "text": "Extract bank statement"},
        {"type": "image", "image": "base64_data"}
      ]
    }
  ]
}
```

Response:
```json
{
  "status": "success",
  "data": {
    "account_number": "****1234",
    "statement_period": "October 2023",
    "transactions": [...]
  },
  "transaction_count": 17
}
```

## Benefits

1. **Efficiency**: Extract once, process many times
2. **Consistency**: Same data across all exports
3. **Flexibility**: Add new processing without re-extraction
4. **Cost Savings**: Fewer VLM API calls
5. **Audit Trail**: Complete processing history

## Technical Details

### JSON Structure
```json
{
  "account_number": "****1234",
  "statement_period": "October 2023",
  "opening_balance": 1000.00,
  "closing_balance": 1500.00,
  "transactions": [
    {
      "date": "2023-10-01",
      "description": "Purchase at Store",
      "debit": 50.00,
      "credit": 0,
      "balance": 950.00,
      "gst_applicable": true,
      "gst_amount": 5.00,
      "category": "Operating Expenses",
      "business_percentage": 100
    }
  ]
}
```

### Local Storage
- JSON files saved to browser's local storage
- Accessible across sessions
- Can be exported and shared

## Future Enhancements

1. **Batch Processing**: Process multiple statements
2. **Rules Engine**: Auto-categorization rules
3. **Integration APIs**: Direct push to accounting software
4. **Analytics Dashboard**: Spending insights
5. **Multi-Currency**: Handle foreign transactions

## Troubleshooting

### JSON Extraction Fails
- Ensure clear, readable bank statement image
- Try table format as fallback
- Check server logs for errors

### Missing Transactions
- Verify all pages are included in upload
- Check JSON preview for completeness
- Use manual editing if needed

### Export Issues
- Ensure all required fields are populated
- Check browser console for errors
- Try different export format

## Development

### Adding New Processing
1. Add UI option in `bank_processor.html`
2. Implement processing in `bank_processor.js`
3. Add server endpoint if needed
4. Update export formats

### Testing
- Test data in `test_statements/` directory
- Unit tests for JSON parsing
- Integration tests for full workflow