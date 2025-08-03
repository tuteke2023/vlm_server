# Comparison Analysis: Original vs New Bank Processor

## Original Working Flow (Main App)

### 1. **Initial Extraction**
```javascript
// From app.js - generateBankTransactionPrompt()
const prompt = `Analyze this bank statement or transaction document and extract the following information in a structured format: ${options.join(', ')}. 
                Present the data in a clear table format with proper headers. 
                If you find multiple transactions, list each one separately. 
                Also provide a summary of total debits, credits, and account balance if available.`;
```

**Key points:**
- Uses `/api/v1/generate` endpoint
- Asks for "structured format" and "clear table format"
- VLM returns text in table format
- No JSON requested from VLM

### 2. **CSV Export Flow**
```javascript
// app.js - exportBankStatementCsv()
// Sends to /api/v1/bank_export endpoint
```

```python
# vlm_server.py - export_bank_statement()
# Uses the ALREADY EXTRACTED text from VLM
ai_response_text = msg.content  # From previous extraction

# Parse using bank_parser_v4.py
bank_statement, csv_content = parse_bank_statement_to_csv(ai_response_text)
```

**Key insight:** The VLM has ALREADY extracted the data as a table. The export just parses the existing text.

### 3. **Parser Logic (bank_parser_v4.py)**
- Handles pipe-delimited tables
- Has robust error handling
- Identifies deposits vs withdrawals based on keywords
- Correctly handles the VLM's tendency to put all amounts in one column

## New Bank Processor Issues

### 1. **Initial Problem: Forced JSON**
```python
# Original attempt - FORCING JSON from VLM
json_prompt = """
Extract ALL transactions from this bank statement in JSON format.
Return ONLY valid JSON with this exact structure:
{...}
"""
```

**Problems:**
- VLM struggles with strict JSON format
- Loses transactions
- Incorrect debit/credit placement

### 2. **Current Solution**
```python
# Now using table format (like original)
table_prompt = """
Extract ALL transactions from this bank statement in a structured table format.
Use this format:
| Date | Description | Ref. | Withdrawals | Deposits | Balance |
"""
```

**This matches the original approach!**

## Key Differences Identified

### 1. **Prompt Differences**

**Original (works):**
- "structured format" + "clear table format"
- Flexible, allows VLM to choose format
- Natural language instructions

**New (had issues):**
- Initially forced strict JSON
- Too prescriptive
- VLM performs worse with rigid structure requirements

### 2. **Processing Flow**

**Original:**
1. Extract once with flexible prompt → Table text
2. Parse table text when needed → CSV/JSON

**New (initial attempt):**
1. Try to extract directly to JSON → Failed/incomplete

**New (fixed):**
1. Extract to table (like original) → Table text
2. Parse table → JSON

### 3. **VLM Behavior Observed**

The VLM consistently:
- Puts ALL amounts in the "Withdrawals" column (even deposits)
- Works better with table format than JSON
- May miss transactions when forced into strict formats

## Why Original Works Better

1. **Flexible Prompting**: Lets VLM work in its preferred format (tables)
2. **Two-Stage Process**: Extract first, parse later
3. **Robust Parsing**: bank_parser_v4.py handles VLM quirks:
   - All amounts in one column
   - Keyword-based debit/credit detection
   - Error handling for malformed entries

## Conclusion

**The key difference is NOT about returning JSON vs text.**

The real differences are:
1. **Prompt flexibility** - Original uses natural language, new tried strict JSON
2. **VLM comfort zone** - Tables work better than forced JSON
3. **Parsing robustness** - Original parser handles VLM quirks better

The fix was to:
1. Return to table extraction (like original)
2. Parse table to JSON (similar to original CSV parsing)
3. Handle VLM's column placement quirks

**Bottom line**: The VLM works best when allowed to output tables naturally, then we parse that output into whatever format we need.