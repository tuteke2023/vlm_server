# Frontend Consolidation Guide

## Overview

As part of Increment 6, we've consolidated the frontend code to create a unified interface that combines functionality from multiple existing interfaces while using the new unified API endpoints.

## What's New

### 1. Unified API Client (`unified_api.js`)
- Single API client that handles all server communication
- Automatic fallback from new endpoints to legacy endpoints
- Consistent error handling and response formatting
- Provider switching support

### 2. Consolidated Interface (`index_unified.html` + `app_unified.js`)
- Combines features from `index.html` and `bank_processor.html`
- Multiple analysis modes:
  - General Analysis
  - Bank Statement Extraction
  - Document Analysis
  - Technical Analysis
- Provider selection (Local VLM / OpenAI)
- Privacy warnings for sensitive data
- VRAM monitoring
- Export functionality (CSV/JSON)

### 3. Benefits
- **No code duplication**: Single codebase for all functionality
- **Consistent UX**: Same interface for all operations
- **Better error handling**: Automatic fallbacks and user notifications
- **Future-proof**: Uses new unified endpoints with legacy fallback

## Migration Guide

### For Users

1. **Access the new interface**:
   ```
   http://localhost:8080/index_unified.html
   ```

2. **Features mapping**:
   - Bank extraction: Select "Bank Statement" mode
   - General image analysis: Select "General Analysis" mode
   - Document processing: Select "Document Analysis" mode
   - Provider switching: Use the dropdown at the top

3. **Export functionality**:
   - Only visible in "Bank Statement" mode
   - Supports both CSV and JSON formats

### For Developers

1. **API Usage**:
   ```javascript
   // Initialize the unified API client
   const api = new UnifiedAPIClient('http://localhost:8000');
   
   // Use unified endpoints (with automatic fallback)
   const result = await api.extractBankStatement(messages);
   const response = await api.generate(messages);
   ```

2. **Key Endpoints**:
   - `/api/v1/bank_extract_langchain` - LangChain-based extraction (preferred)
   - `/api/v1/generate_unified` - Unified text generation
   - `/api/v1/providers_unified` - List available providers
   - `/api/v1/switch_provider_unified` - Switch between providers

3. **Response Format**:
   All responses now include metadata:
   ```json
   {
     "response": "...",
     "metadata": {
       "provider": "local",
       "model": "Qwen/Qwen2.5-VL-3B-Instruct",
       "processing_time": 1.23
     }
   }
   ```

## Legacy Interface Mapping

| Old Interface | Old Endpoint | New Interface | New Endpoint |
|--------------|--------------|---------------|--------------|
| index.html | `/api/v1/bank_extract_json` | Bank Statement mode | `/api/v1/bank_extract_langchain` |
| bank_processor.html | `/api/v1/bank_extract_unified` | Bank Statement mode | `/api/v1/bank_extract_langchain` |
| index.html | `/api/v1/generate` | General Analysis mode | `/api/v1/generate_unified` |

## Testing

Run the test suite to verify the consolidated frontend:

```bash
python test_unified_frontend.py
```

This will test:
- API endpoint availability
- UI functionality (requires Selenium)
- Mode switching
- Export features
- Provider selection

## Backward Compatibility

The consolidated frontend maintains backward compatibility:
- Automatically falls back to legacy endpoints if new ones fail
- Supports both old and new response formats
- Previous URLs still work (index.html, bank_processor.html)

## Next Steps

1. **For immediate use**: Start using `index_unified.html`
2. **For production**: After testing, rename `index_unified.html` to `index.html`
3. **For cleanup**: Remove duplicate code files after migration

## Troubleshooting

### Issue: Export buttons not visible
- **Solution**: Make sure you're in "Bank Statement" mode

### Issue: Provider switching fails
- **Solution**: Check that OpenAI API key is configured in `.env`

### Issue: VRAM status shows "Loading..."
- **Solution**: Ensure VLM server is running on port 8000

### Issue: Old interface still being used
- **Solution**: Clear browser cache and navigate to `/index_unified.html`