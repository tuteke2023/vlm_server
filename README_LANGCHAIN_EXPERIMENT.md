# LangChain Bank Statement Parser Experiment

This branch (`feature/langchain-bank-parser`) implements a server-side CSV export feature for bank statements using LangChain's structured output parsers.

## Features Implemented

### 1. **Structured Output Parsing**
- Uses LangChain's `PydanticOutputParser` for reliable structured data extraction
- Pydantic models ensure type safety and validation
- Auto-categorization of transactions based on keywords

### 2. **Server-Side Processing**
- New API endpoint: `/api/v1/bank_export`
- Accepts bank statement in various formats (text, image)
- Returns structured CSV or JSON

### 3. **Frontend Integration**
- "Export CSV" button appears for bank transaction results
- Downloads properly formatted CSV with columns:
  - Date
  - Description
  - Category (auto-assigned)
  - Debit
  - Credit
  - Balance

## API Endpoint

```python
POST /api/v1/bank_export
{
    "messages": [{"role": "user", "content": "..."}],
    "export_format": "csv" | "json"
}

Response:
{
    "format": "csv",
    "content": "Date,Description,Category...",
    "filename": "bank_statement_20240802_123456.csv",
    "transaction_count": 10,
    "total_debits": 1500.00,
    "total_credits": 3000.00
}
```

## How to Test

1. **Start the server** (ensure you're on this branch):
   ```bash
   source ~/pytorch-env/bin/activate
   python vlm_server.py
   ```

2. **Test via Web Interface**:
   - Open http://localhost:8080
   - Select "Bank Transactions"
   - Upload a bank statement image/PDF
   - Process normally
   - Click "Export CSV" button in results

3. **Test via API**:
   ```bash
   python test_langchain_integration.py
   ```

## Implementation Details

### Parser Logic
1. First tries LangChain's structured parser
2. Falls back to JSON extraction if present
3. Finally tries manual table parsing
4. Returns empty statement if all fail

### Auto-Categorization
Categories include:
- Groceries
- Transportation
- Dining
- Shopping
- Utilities
- Housing
- Income
- Transfer
- Banking
- Healthcare
- Entertainment

## Known Issues

1. **Parser Sensitivity**: The parser may not catch all transaction formats
2. **Amount Detection**: Complex formats with multiple amounts per line can be challenging
3. **Date Formats**: Currently supports MM/DD/YYYY and DD/MM/YYYY

## Future Improvements

1. Add more robust table parsing
2. Support for more bank statement formats
3. Machine learning-based categorization
4. Multi-currency support
5. Statement reconciliation features

## Files Modified

- `vlm_server.py`: Added `/api/v1/bank_export` endpoint
- `bank_parser.py`: New file with LangChain parser implementation
- `requirements.txt`: Added langchain dependencies
- `web_interface/static/js/app.js`: Added CSV export functionality
- `web_interface/index.html`: Added Export CSV button

## Testing

Run the test suite:
```bash
python test_bank_parser.py  # Tests parser logic
python test_langchain_integration.py  # Tests API integration
```