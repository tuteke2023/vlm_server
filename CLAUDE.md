# Claude Development Notes

This file contains development notes and instructions for Claude (or other AI assistants) working on this project.

## Project Overview

VLM Server is a FastAPI-based server that provides vision-language model capabilities using Qwen2.5-VL models. The server supports:
- Image and text analysis
- Document intelligence features
- Bank statement parsing and CSV export
- Multiple model sizes (3B and 7B)
- VRAM management and optimization

## Recent Updates

### LangChain Bank Statement Parser (August 2025)
- Implemented structured bank statement parsing using LangChain
- Created `bank_parser_v3.py` with support for multiple table formats
- Added `/api/v1/bank_export` endpoint for CSV/JSON export
- Features:
  - Automatic transaction categorization
  - Proper debit/credit separation
  - Handles pipe-delimited and space-delimited tables
  - Supports "Withdrawals/Deposits" column naming

## Key Files

### Core Server
- `vlm_server.py` - Main FastAPI server with model management
- `requirements.txt` - Python dependencies including LangChain

### Bank Parser
- `bank_parser_v3.py` - Latest version with pipe-delimited table support
- `test_parser_v3.py` - Parser test suite
- `test_final_integration.py` - Integration tests

### Web Interface
- `web_interface/index.html` - Main UI
- `web_interface/static/js/app.js` - Frontend logic with CSV export
- `web_interface/static/css/style.css` - Styling

## Important Commands

### Start Server
```bash
source ~/pytorch-env/bin/activate
python vlm_server.py
```

### Start Web Interface
```bash
cd web_interface
python server.py
```

### Run Tests
```bash
python test_parser_v3.py  # Test parser directly
python test_final_integration.py  # Test full integration
```

## API Endpoints

### Bank Export
```
POST /api/v1/bank_export
{
    "messages": [...],
    "export_format": "csv" | "json"
}
```

### Generate
```
POST /api/v1/generate
{
    "messages": [...],
    "temperature": 0.1,
    "max_tokens": 1000
}
```

## Testing Bank Parser

1. Upload a bank statement image via web interface
2. Select "Bank Transactions" option
3. Process the image
4. Click "Export CSV" button
5. Verify CSV has proper columns:
   - Date, Description, Category, Debit, Credit, Balance

## Known Issues

1. LangChain direct parser expects JSON but AI returns tables
2. Parser falls back to table format parsing successfully
3. Some bank statements use "Withdrawals/Deposits" instead of "Debit/Credit"

## Development Tips

1. Always check server logs when debugging parser issues
2. The v3 parser handles most common bank statement formats
3. Categories are auto-assigned based on transaction descriptions
4. Test with various bank statement formats before deploying

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