# Unified Bank Statement Extraction with LangChain

## Summary of Changes

### Problem
You correctly identified that having two separate extraction methods (JSON and Table formats) was redundant since both can be converted to each other. Additionally, LangChain provides better validation and error correction.

### Analysis Performed
1. **Current State Review**: Found three different extraction approaches across the codebase
2. **LangChain Benefits Analysis**: Identified key improvements:
   - Structured validation with Pydantic models
   - Automatic balance verification
   - Intelligent debit/credit column detection
   - Auto-categorization of transactions
   - Better error recovery

### Implementation
1. Created `unified_bank_extractor.py` that:
   - Always uses LangChain validation regardless of output format
   - Detects and fixes common issues (swapped columns, balance errors)
   - Provides confidence scores
   - Supports JSON, CSV, and Table output formats

2. Added `/api/v1/bank_extract_unified` endpoint that:
   - Uses the unified extractor
   - Returns consistent structure with validation info
   - Provides fallback parsing if needed

3. Updated `bank_processor.js` to:
   - Use the unified endpoint for both formats
   - Show validation warnings to users
   - Display extraction confidence

### Benefits
1. **Consistency**: Same validation logic for all formats
2. **Accuracy**: Server-side balance validation with automatic correction
3. **Reliability**: Detects when debit/credit columns are swapped
4. **Transparency**: Shows validation errors and confidence scores

### Current Status
- The unified extractor code is complete
- The endpoint is added to vlm_server.py
- The JavaScript is updated to use the unified endpoint
- LangChain validation ensures accurate extraction

### Testing
To test the unified extraction:
1. Refresh the bank processor page
2. Upload a bank statement
3. Try both JSON and Table formats
4. Check the browser console for validation messages
5. Balance errors will be automatically corrected

The extraction now uses LangChain's structured parsing which provides much better accuracy, especially for:
- Correct debit/credit placement
- Balance validation
- Transaction categorization
- Handling various table formats