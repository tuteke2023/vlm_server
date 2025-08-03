# Migration Checklist - Monorepo Structure

## Phase 1 Migration Checklist

### Prerequisites
- [ ] Ensure VLM server is working correctly
- [ ] Backup current working state
- [ ] Document current virtual environment setup

### Step 1: Create New Directory Structure
```bash
# Create service directories
mkdir -p services/vlm
mkdir -p services/audio
mkdir -p scripts
```

### Step 2: Move VLM Service
- [ ] Move `vlm_server.py` → `services/vlm/vlm_server.py`
- [ ] Move `bank_parser_v3.py` → `services/vlm/bank_parser_v3.py`
- [ ] Move other VLM-related files → `services/vlm/`
- [ ] Move `web_interface/` → `services/vlm/web_interface/`
- [ ] Copy `requirements.txt` → `services/vlm/requirements.txt`
- [ ] Create `services/vlm/README.md`

### Step 3: Create Audio Service
- [ ] Create `services/audio/transcription_server.py`
- [ ] Create `services/audio/requirements.txt` with Whisper dependencies
- [ ] Create `services/audio/web_interface/`
- [ ] Create `services/audio/README.md`

### Step 4: Create Docker Configuration
- [ ] Create `services/vlm/Dockerfile`
- [ ] Create `services/audio/Dockerfile`
- [ ] Create root `docker-compose.yml`

### Step 5: Create Helper Scripts
- [ ] Create `scripts/start_all.sh`
- [ ] Create `scripts/start_vlm.sh`
- [ ] Create `scripts/start_audio.sh`
- [ ] Make scripts executable

### Step 6: Update Documentation
- [ ] Update root `README.md` with new structure
- [ ] Update `CLAUDE.md` with new paths
- [ ] Create service-specific READMEs

### Step 7: Test Migration
- [ ] Test VLM service in new location
- [ ] Test audio service
- [ ] Test both services together
- [ ] Test Docker setup

### Step 8: Update Git
- [ ] Commit new structure
- [ ] Tag release (e.g., v2.0.0-monorepo)
- [ ] Push to GitHub

## Rollback Plan
If issues occur:
1. `git checkout 6c83b05` (last known good commit)
2. Restore virtual environment
3. Restart VLM server with original structure

## Virtual Environment Setup
```bash
# VLM Service
cd services/vlm
python3 -m venv vlm-env
source vlm-env/bin/activate
pip install -r requirements.txt
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu128

# Audio Service  
cd services/audio
python3 -m venv audio-env
source audio-env/bin/activate
pip install -r requirements.txt
```

## Port Assignments
- VLM API: 8000
- Audio API: 8001
- Web UI: 8080

## Testing Commands
```bash
# Test VLM
curl http://localhost:8000/health

# Test Audio
curl http://localhost:8001/health

# Test Web UI
curl http://localhost:8080
```

---
*Created: 2025-08-03*