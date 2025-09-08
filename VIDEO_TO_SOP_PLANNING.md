# Video-to-SOP Microservice Planning Document

## Overview
Convert short instructional/training videos into structured Standard Operating Procedures (SOPs) with automated step extraction, visual documentation, and formatting.

## Core Objectives
1. **Extract actionable steps** from video content
2. **Capture key frames** as visual references
3. **Generate structured documentation** in multiple formats
4. **Enable easy editing and refinement** of generated SOPs

## Architecture Design

### Microservice Structure
```
services/
├── video_sop/
│   ├── __init__.py
│   ├── video_sop_server.py        # FastAPI server (port 8003)
│   ├── video_processor.py         # Video analysis & frame extraction
│   ├── step_extractor.py          # Step detection & sequencing
│   ├── sop_generator.py           # SOP document generation
│   ├── template_manager.py        # SOP templates & formatting
│   ├── storage/
│   │   ├── sop_database.py        # SQLite for SOP storage
│   │   └── media_storage.py       # Frame/screenshot storage
│   ├── web_interface/
│   │   ├── index.html             # Video upload & SOP editor
│   │   └── static/
│   └── requirements.txt
```

## Technical Components

### 1. Video Processing Pipeline
```python
# Key capabilities needed:
- Video upload & validation (MP4, AVI, MOV, WEBM)
- Audio extraction → Transcription (use existing service)
- Frame extraction at key moments
- Scene change detection
- Action recognition using VLM
```

### 2. Step Extraction Logic
```python
# Approach:
1. Transcribe audio narration
2. Analyze visual frames for actions
3. Detect transitions/scene changes
4. Correlate audio instructions with visual actions
5. Generate numbered steps with timestamps
```

### 3. SOP Generation Features
```python
# Output components:
- Title & Overview
- Prerequisites/Requirements
- Step-by-step instructions
- Visual aids (screenshots)
- Warnings/Tips/Notes
- Time estimates
- Export formats: Markdown, PDF, HTML, DOCX
```

## Integration Points

### With Existing Services

1. **Transcription Service (port 8001)**
   - Extract audio from video
   - Get transcript with timestamps
   - Use speaker detection for multi-person demos

2. **VLM Server (port 8000)**
   - Analyze key frames for actions
   - Describe what's happening visually
   - Identify tools/UI elements

3. **Shared Components**
   - Authentication (if needed)
   - Storage patterns
   - Error handling

## Implementation Phases

### Phase 1: Basic Video Processing (Week 1)
- [ ] Set up FastAPI server structure
- [ ] Implement video upload endpoint
- [ ] Extract audio and send to transcription
- [ ] Basic frame extraction at intervals
- [ ] Store results in SQLite

### Phase 2: Intelligent Step Detection (Week 2)
- [ ] Implement scene change detection
- [ ] Send frames to VLM for analysis
- [ ] Correlate transcript with visual actions
- [ ] Generate basic step list
- [ ] Add timestamp markers

### Phase 3: SOP Generation (Week 3)
- [ ] Create SOP templates
- [ ] Implement step sequencing logic
- [ ] Add visual frame selection
- [ ] Generate formatted output
- [ ] Support multiple export formats

### Phase 4: Web Interface (Week 4)
- [ ] Video upload UI
- [ ] Step review/edit interface
- [ ] Frame selection tool
- [ ] SOP preview
- [ ] Export options

### Phase 5: Advanced Features (Future)
- [ ] Multi-language support
- [ ] Collaborative editing
- [ ] Version control for SOPs
- [ ] AI-powered suggestions
- [ ] Template library

## API Design

### Core Endpoints

```python
POST /upload_video
- Input: video file, metadata
- Output: job_id, status

GET /job_status/{job_id}
- Output: processing status, progress

GET /extracted_steps/{job_id}
- Output: list of steps with timestamps

POST /generate_sop
- Input: job_id, template, customizations
- Output: formatted SOP document

GET /sop/{sop_id}
- Output: saved SOP details

PUT /sop/{sop_id}
- Input: edited SOP content
- Output: updated SOP

GET /export/{sop_id}
- Query: format (md, pdf, html, docx)
- Output: formatted document
```

## Data Models

### Video Job
```python
{
    "job_id": "uuid",
    "video_filename": "training_video.mp4",
    "upload_time": "2025-01-09T10:00:00",
    "status": "processing|completed|failed",
    "duration_seconds": 180,
    "transcript_id": "ref_to_transcription",
    "extracted_frames": ["frame1.jpg", "frame2.jpg"],
    "processing_metadata": {}
}
```

### Extracted Step
```python
{
    "step_number": 1,
    "timestamp_start": "00:00:10",
    "timestamp_end": "00:00:25",
    "instruction": "Click on File menu",
    "visual_description": "User clicks File menu in top toolbar",
    "key_frame": "frame_001.jpg",
    "warnings": [],
    "tips": []
}
```

### Generated SOP
```python
{
    "sop_id": "uuid",
    "title": "How to Export Data",
    "created_from": "job_id",
    "version": "1.0",
    "steps": [...],
    "prerequisites": [...],
    "tools_required": [...],
    "estimated_time": "5 minutes",
    "export_formats": ["md", "pdf"]
}
```

## Technology Stack

### Core Dependencies
```python
# Video Processing
opencv-python       # Frame extraction
moviepy            # Video/audio manipulation
ffmpeg-python      # Video format handling

# AI/ML
# (reuse existing Whisper & VLM)

# Document Generation
python-docx        # Word documents
markdown2          # Markdown processing
reportlab          # PDF generation
jinja2             # Template engine

# Web Framework
fastapi
uvicorn
python-multipart

# Database
sqlite3            # Built-in
sqlalchemy         # ORM (optional)
```

## Example Use Cases

### 1. Software Tutorial
**Input**: 3-minute screen recording showing how to use an application
**Output**: 
- 10-step SOP with screenshots
- Each step has clear instructions
- Keyboard shortcuts highlighted
- Common errors noted

### 2. Equipment Operation
**Input**: Video showing machine operation
**Output**:
- Safety warnings first
- Pre-operation checklist
- Step-by-step operation guide
- Maintenance notes
- Troubleshooting section

### 3. Process Documentation
**Input**: Employee demonstrating workflow
**Output**:
- Role-based instructions
- Decision points documented
- Forms/tools referenced
- Time estimates per step
- Compliance notes

## Success Metrics

1. **Accuracy**: 90%+ step extraction accuracy
2. **Processing Speed**: < 2x video duration
3. **Usability**: SOPs require < 20% manual editing
4. **Format Support**: 5+ video formats, 4+ export formats
5. **User Satisfaction**: Saves 70% documentation time

## Potential Challenges & Solutions

### Challenge 1: Poor Video Quality
**Solution**: Enhance frames with VLM, focus on audio narration

### Challenge 2: Complex Multi-step Processes
**Solution**: Allow manual step splitting/merging in editor

### Challenge 3: No Narration
**Solution**: Rely heavily on VLM visual analysis

### Challenge 4: Multiple Simultaneous Actions
**Solution**: Support sub-steps and parallel tracks

## Next Steps

1. **Validate Requirements**: Review with stakeholders
2. **Prototype Core Features**: Build minimal version
3. **Test with Sample Videos**: Gather feedback
4. **Iterate Design**: Refine based on results
5. **Production Implementation**: Full feature build

## Questions to Consider

1. What video formats are most common?
2. Average video length to support?
3. Should we support live video streams?
4. Multi-language requirements?
5. Integration with existing SOP systems?
6. Compliance/regulatory requirements?
7. Collaboration features needed?
8. Version control requirements?

## Resource Estimates

- **Development Time**: 4-6 weeks for MVP
- **Storage**: ~1GB per 100 videos processed
- **Compute**: GPU helpful but not required
- **Team**: 1 developer, occasional VLM/ML consultation

---

*This planning document outlines the Video-to-SOP microservice that will integrate seamlessly with the existing VLM Server ecosystem.*