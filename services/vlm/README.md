# VLM Service

Vision Language Model service for document processing, bank statement extraction, and image analysis.

## Setup

```bash
# Create and activate virtual environment
python3 -m venv vlm-env
source vlm-env/bin/activate

# Install dependencies
pip install -r requirements.txt

# For RTX 5060 Ti and newer GPUs
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128
```

## Running the Service

```bash
# Activate environment
source vlm-env/bin/activate

# Start server
python vlm_server.py
```

The service will run on http://localhost:8000

## API Endpoints

- `/health` - Health check
- `/api/v1/generate` - Main generation endpoint
- `/api/v1/bank_extract_json` - Bank statement extraction
- `/api/v1/bank_export` - Export to CSV/JSON
- `/vram_status` - GPU memory status