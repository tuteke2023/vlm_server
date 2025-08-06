# Manual Testing Checklist for Unified LangChain Implementation

## Pre-Testing Setup

- [ ] Ensure virtual environment is activated: `source ~/pytorch-env/bin/activate`
- [ ] Start VLM server: `python services/vlm/vlm_server.py`
- [ ] Start web interface: `cd services/vlm/web_interface && python server.py`
- [ ] Verify `.env` file contains valid OpenAI API key (if testing OpenAI)
- [ ] Have test bank statements ready in `tests/` folder

## 1. Provider Management Testing

### Local VLM Provider
- [ ] Select "Local VLM" from provider dropdown
- [ ] Verify provider indicator shows green/local color
- [ ] Test basic text query (e.g., "What is 2+2?")
- [ ] Verify response comes from local model
- [ ] Check response metadata shows correct model name

### OpenAI Provider
- [ ] Select "OpenAI GPT-4V" from provider dropdown
- [ ] Verify provider indicator shows orange color (external service)
- [ ] Test basic text query
- [ ] Verify response comes from OpenAI
- [ ] Check response metadata shows "gpt-4o"

### Provider Switching
- [ ] Switch from Local to OpenAI mid-conversation
- [ ] Verify smooth transition without errors
- [ ] Switch back to Local
- [ ] Confirm provider state persists across page refresh

## 2. Bank Statement Extraction Testing

### Main Page (index.html)
- [ ] Select "Bank Transactions" tool
- [ ] Upload BankStatementChequing.png
- [ ] Process with Local VLM
- [ ] Verify all 19 transactions are extracted
- [ ] Check amounts include decimal places
- [ ] Verify categories are auto-assigned
- [ ] Test "Export CSV" button
- [ ] Verify CSV downloads with correct data

### OpenAI Extraction
- [ ] Switch to OpenAI provider
- [ ] Upload same bank statement
- [ ] Verify privacy warning modal appears
- [ ] Test "Proceed" option
- [ ] Compare results with Local VLM
- [ ] Test "Cancel" option on privacy modal

### Bank Processor Page
- [ ] Navigate to bank_processor.html
- [ ] Upload bank statement
- [ ] Test "Table" format output
- [ ] Test "JSON" format output
- [ ] Verify both use same extraction logic
- [ ] Check categorization consistency

## 3. Privacy and Security Testing

### Sensitive Content Detection
- [ ] Type message with bank account number
- [ ] Select OpenAI provider
- [ ] Verify privacy warning appears
- [ ] Test warning doesn't appear for Local VLM
- [ ] Test warning for various sensitive patterns:
  - [ ] SSN format (###-##-####)
  - [ ] Credit card numbers
  - [ ] Account numbers
  - [ ] Personal identification

### API Key Security
- [ ] Verify OpenAI API key not visible in UI
- [ ] Check browser developer tools - no API key in requests
- [ ] Test with invalid API key in .env
- [ ] Verify graceful error handling

## 4. Error Handling and Fallback Testing

### OpenAI Failure Scenarios
- [ ] Temporarily invalidate OpenAI API key
- [ ] Attempt extraction with OpenAI
- [ ] Verify fallback dialog appears
- [ ] Test "Use Local VLM" option
- [ ] Test "Cancel" option
- [ ] Restore valid API key

### Network Issues
- [ ] Disconnect internet (for OpenAI testing)
- [ ] Verify appropriate error messages
- [ ] Confirm Local VLM still works
- [ ] Test automatic fallback behavior

## 5. Performance Testing

### Response Times
- [ ] Time Local VLM extraction (note seconds)
- [ ] Time OpenAI extraction (should be faster)
- [ ] Test with different image sizes
- [ ] Monitor UI responsiveness during processing

### Token Usage
- [ ] Check token usage display for Local VLM
- [ ] Verify token limits are respected
- [ ] Test extraction with max_tokens parameter

## 6. UI/UX Testing

### Visual Feedback
- [ ] Verify loading spinners appear during processing
- [ ] Check provider status indicators update correctly
- [ ] Test progress indicators for long operations
- [ ] Verify error messages are clear and actionable

### Responsiveness
- [ ] Test on desktop browser (1920x1080)
- [ ] Test on tablet size (768x1024)
- [ ] Test on mobile size (375x667)
- [ ] Verify all buttons remain accessible

### Accessibility
- [ ] Test keyboard navigation (Tab key)
- [ ] Verify all buttons have proper labels
- [ ] Test with screen reader (if available)
- [ ] Check color contrast for readability

## 7. Data Validation Testing

### Extraction Accuracy
- [ ] Compare extracted data with source image
- [ ] Verify:
  - [ ] All dates are in MM/DD/YYYY format
  - [ ] Amounts are positive numbers
  - [ ] Debit/Credit placement is correct
  - [ ] Running balances are mathematically correct
  - [ ] Categories match transaction descriptions

### Export Functionality
- [ ] Export as CSV and verify in Excel/spreadsheet
- [ ] Export as JSON and validate structure
- [ ] Check special characters are handled properly
- [ ] Verify totals in summary section

## 8. Integration Testing

### End-to-End Workflows
- [ ] Complete bank extraction workflow:
  1. [ ] Start with Local VLM
  2. [ ] Extract statement
  3. [ ] Switch to OpenAI
  4. [ ] Extract same statement
  5. [ ] Compare results
  6. [ ] Export both as CSV
  7. [ ] Verify consistency

### Multi-Page Testing
- [ ] Test navigation between pages maintains state
- [ ] Verify shared functionality works consistently
- [ ] Check that provider selection persists

## 9. Edge Cases

- [ ] Upload non-bank statement image
- [ ] Upload corrupted/invalid image file
- [ ] Test with empty bank statement
- [ ] Test with single transaction
- [ ] Test with 100+ transactions
- [ ] Test with multiple currency symbols
- [ ] Test with special characters in descriptions

## 10. Performance Benchmarks

Record the following metrics:

| Test Case | Local VLM Time | OpenAI Time | Notes |
|-----------|----------------|-------------|-------|
| Small statement (< 10 transactions) | ___ seconds | ___ seconds | |
| Medium statement (10-30 transactions) | ___ seconds | ___ seconds | |
| Large statement (30+ transactions) | ___ seconds | ___ seconds | |
| Complex statement (mixed formats) | ___ seconds | ___ seconds | |

## Post-Testing Cleanup

- [ ] Clear browser cache
- [ ] Check for any error logs in console
- [ ] Document any issues found
- [ ] Verify no sensitive data left in test files
- [ ] Stop all running servers

## Sign-off

- [ ] All critical paths tested
- [ ] No blocking issues found
- [ ] Performance meets requirements
- [ ] Security measures working correctly

Tested by: ________________
Date: ____________________
Version: _________________

## Notes Section

Use this space to document any observations, issues, or suggestions discovered during testing:

---

### Issues Found:

### Suggestions for Improvement:

### Additional Test Cases Needed: