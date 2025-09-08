# Video to SOP Converter

Convert any instructional video into a comprehensive Standard Operating Procedure with AI-verified visuals and professional documentation.

## Quick Start

### Step 1: Start the Required Services

Open two terminal windows and run:

**Terminal 1 - VLM Service:**
```bash
source ~/pytorch-env/bin/activate
cd services/vlm
python real_vlm_server.py
```

**Terminal 2 - Transcription Service:**
```bash
source ~/pytorch-env/bin/activate  
cd services/audio
python transcription_server.py
```

### Step 2: Convert Your Video

**Terminal 3 - Run Converter:**
```bash
source ~/pytorch-env/bin/activate
cd services/video_sop

# Simple usage:
python video_to_sop.py /path/to/your/video.mp4

# With custom output directory:
python video_to_sop.py video.mp4 --output ./my_project_sop
```

## What It Does

1. **Extracts Audio** - Gets audio track from video
2. **Transcribes Speech** - Converts speech to text with timestamps
3. **Identifies Key Actions** - Finds important steps (click, select, navigate, etc.)
4. **Verifies Visuals** - Uses AI to confirm frames match narration
5. **Generates Documentation** - Creates comprehensive SOP with:
   - Step-by-step instructions
   - Prerequisites and context
   - Tips and warnings
   - Troubleshooting guide
   - Compliance information
   - Visual screenshots

## Output

The converter creates:
```
output_directory/
├── hybrid_comprehensive_sop.md    # The complete SOP document
├── step_1_XXs.jpg                 # Verified screenshots
├── step_2_XXs.jpg
├── ...
└── transcript.json                # Full transcript for reference
```

## Requirements

- **GPU**: NVIDIA GPU with 16GB+ VRAM (for 7B model)
- **Software**: 
  - Python 3.8+
  - PyTorch with CUDA support
  - FFmpeg (for video processing)
- **Disk Space**: ~20GB for models

## Supported Video Formats

- MP4, MKV, AVI, MOV
- Any format supported by FFmpeg

## Tips for Best Results

1. **Clear Audio**: Videos with clear narration work best
2. **Action Words**: Videos where the narrator says "click here", "select this", etc.
3. **Screen Recordings**: Particularly good for software tutorials
4. **Resolution**: Higher resolution videos produce better frame captures

## Examples

### Convert a Software Tutorial:
```bash
python video_to_sop.py "Excel Tutorial.mp4" --output excel_sop
```

### Convert a Training Video:
```bash
python video_to_sop.py training_video.mkv --output training_docs
```

## Troubleshooting

**"VLM Service not running"**
- Ensure you started the VLM server (requires GPU)
- Check GPU memory: `nvidia-smi`

**"Transcription Service not running"**
- Start the transcription server
- Check port 8001 is not in use

**"No key segments found"**
- Video may not have clear action words
- Try videos with more instructional narration

## Advanced Usage

### Customize Action Keywords

Edit `video_to_sop.py` and modify the `action_keywords` list to detect specific terms relevant to your domain:

```python
action_keywords = [
    'your_custom_keyword',
    'domain_specific_term',
    # ... add more
]
```

### Adjust Visual Verification

Modify search window in `hybrid_sop_generator.py`:

```python
# Look further ahead for visual confirmation
for offset in [0, 2, 5, 10, 15, 20]:  # Seconds to look ahead
```

## System Architecture

```
Video File → Audio Extraction → Transcription → Key Segment Detection
                                                           ↓
Output SOP ← Documentation Generation ← VLM Verification ← Frame Extraction
```

## Contact & Support

For issues or questions, check the main project documentation or raise an issue in the repository.