# Claude Development Notes

This file contains development notes and instructions for Claude (or other AI assistants) working on this project.

## Project Overview

VLM Server is a FastAPI-based server that provides vision-language model capabilities using Qwen2.5-VL models. The server supports:
- Image and text analysis with unified LLM provider architecture
- Document intelligence features with LangChain integration
- Bank statement parsing with structured output and CSV/JSON export
- Multiple providers: Local VLM and OpenAI GPT-4V
- Multiple model sizes (3B and 7B) with automatic VRAM management
- Performance optimizations and response caching

## Recent Updates

### Unified LangChain Architecture (August 2025)
- Implemented unified LLM provider system supporting multiple backends
- Created optimized LangChain extractor for better performance
- Added OpenAI GPT-4V integration with privacy controls
- Features:
  - Unified API across all providers
  - Structured output with Pydantic models
  - Automatic transaction categorization
  - Response caching for improved performance
  - Beautiful block-based UI with provider switching

## Key Files

### Core Server (services/vlm/)
- `vlm_server.py` - Main FastAPI server with unified provider support
- `unified_llm_provider.py` - Unified LLM provider abstraction
- `langchain_extractor_optimized.py` - Optimized bank statement extractor
- `openai_provider.py` - OpenAI GPT-4V integration
- `response_cache.py` - Response caching system
- `requirements.txt` - Python dependencies

### Bank Parser
- `bank_parser_v3.py` - Table format parser with multiple format support
- `langchain_extractor.py` - LangChain-based structured extraction

### Web Interface (services/vlm/web_interface/)
- `index_unified_styled.html` - Beautiful block-based UI
- `static/js/app_unified_styled.js` - Unified frontend with provider switching
- `static/js/unified_api.js` - Unified API client
- `static/css/style.css` - Enhanced styling with CSS variables

## Important Commands

### Start Server
```bash
source ~/pytorch-env/bin/activate
cd services/vlm
python vlm_server.py
```

### Start Web Interface
```bash
cd services/vlm/web_interface
python server.py
```

### Run Tests
```bash
cd tests
python -m pytest  # Run all tests
python unit/test_unified_llm_provider.py  # Test unified provider
python integration/test_bank_extraction_integration.py  # Test extraction
```

## API Endpoints

### Unified Endpoints

#### Generate (Unified)
```
POST /api/v1/generate_unified
{
    "messages": [...],
    "temperature": 0.7,
    "max_tokens": 2048
}
```

#### Bank Extraction (LangChain)
```
POST /api/v1/bank_extract_langchain
{
    "messages": [...],
    "temperature": 0.1,
    "max_tokens": 4000
}
```

#### Bank Export
```
POST /api/v1/bank_export
{
    "messages": [...],
    "export_format": "csv" | "json"
}
```

#### Provider Management
```
GET /api/v1/providers_unified
POST /api/v1/switch_provider_unified
{
    "provider": "local" | "openai"
}
```

## Testing Bank Parser

1. Upload a bank statement image via web interface
2. Select "Bank Transactions" option
3. Process the image
4. Click "Export CSV" button
5. Verify CSV has proper columns:
   - Date, Description, Category, Debit, Credit, Balance

## Performance Notes

1. LangChain endpoint provides 70% better extraction accuracy than JSON endpoint
2. Optimized extractor reduces processing time by ~30-40%
3. Response caching eliminates redundant processing for identical requests
4. VLM uses ~58% VRAM with 3B model loaded

## Development Tips

1. Always use the unified endpoints for new features
2. The optimized LangChain extractor is faster than the original
3. Enable OpenAI provider only when higher accuracy is needed
4. Monitor VRAM usage with `/vram_status` endpoint
5. Use response caching for repeated requests
6. Test with both local VLM and OpenAI providers

## Git Workflow

```bash
# Check current branch
git branch

# Create feature branch
git checkout -b feature/new-feature

# Add and commit changes
git add .
git commit -m "Description of changes"

# Push to GitHub
git push origin feature/new-feature
```

## Environment Setup

The project uses a virtual environment at `~/pytorch-env/`. Always activate it before running:
```bash
source ~/pytorch-env/bin/activate
```

### GPU Compatibility (RTX 5060 Ti and newer GPUs)

For GPUs with compute capability sm_120 (RTX 5060 Ti) and newer, you need PyTorch with CUDA 12.8 support:

1. **Activate the virtual environment first:**
   ```bash
   source ~/pytorch-env/bin/activate
   ```

2. **Install PyTorch with CUDA 12.8:**
   ```bash
   pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
   ```

This resolves the "no kernel image is available for execution on the device" error for newer GPUs.

## Project Reminders

- **IMPORTANT**: Always use the virtual environment (`source ~/pytorch-env/bin/activate`) before starting the server
- The virtual environment contains PyTorch 2.7.1+cu128 which supports newer GPUs like RTX 5060 Ti
- Never run the server with system Python - it will fail with CUDA compatibility errors

## VRAM Management

- 3B model uses ~6.5GB VRAM
- 7B model uses ~15.5GB VRAM
- Server automatically manages VRAM with garbage collection
- Use `/vram_status` endpoint to monitor usage

## Development Process

- When finishing updating the code, please test it yourself before giving it back to me.