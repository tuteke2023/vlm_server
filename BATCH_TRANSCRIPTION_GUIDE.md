# Batch Audio Transcription Guide

This guide explains how to efficiently transcribe large collections of audio files with the VLM Server's audio transcription service.

## Overview

The batch transcription system provides several tools for processing audio files at scale:
- **Automatic duration filtering** - Skip files over a specified duration
- **Truncation for long recordings** - Process only the first hour of lengthy files
- **Vector database integration** - All transcripts are automatically searchable
- **Duplicate detection** - Avoid re-processing already transcribed files
- **Multi-language support** - Automatic language detection

## Quick Start

### 1. Start the Audio Service
```bash
cd services/audio
source audio-env/bin/activate
python transcription_server.py
```

### 2. Basic Batch Transcription

**Process all audio files under 30 minutes:**
```bash
python3 batch_transcribe_filtered.py "/path/to/audio/folder" --model base
```

**Process with different duration limit:**
```bash
python3 batch_transcribe_filtered.py "/path/to/audio/folder" --max-duration 45
```

### 3. Handle Large Files with Truncation

**Truncate and transcribe large files (first 60 minutes):**
```bash
python3 transcribe_truncated.py --batch --duration 60
```

**Process a single large file:**
```bash
python3 transcribe_truncated.py --file "Recording.mp3" --duration 60
```

## Available Tools

### batch_transcribe_filtered.py
Processes folders of audio files with size/duration filtering.

**Features:**
- Skips files estimated to be over specified duration (default: 30 min)
- Estimates duration based on file size and format
- Shows progress with time estimates
- Saves results to JSON file

**Usage:**
```bash
python3 batch_transcribe_filtered.py [folder] [options]

Options:
  --model {tiny,base,small,medium,large}  Whisper model (default: base)
  --max-duration MINUTES                   Max duration in minutes (default: 30)
  --no-skip                                Process already transcribed files
```

### transcribe_truncated.py
Handles large files by truncating to a specified duration before transcribing.

**Features:**
- Uses FFmpeg to truncate audio files
- Processes only first N minutes of recording
- Adds truncation note to transcript
- Perfect for recordings that ran too long

**Usage:**
```bash
# Process single file
python3 transcribe_truncated.py --file "path/to/file.mp3" --duration 60

# Batch process all previously skipped large files
python3 transcribe_truncated.py --batch --duration 60

# Keep truncated files for review
python3 transcribe_truncated.py --file "file.mp3" --keep
```

### transcribe_single.py
Transcribes individual files without duration limits.

**Usage:**
```bash
python3 transcribe_single.py "path/to/audio.mp3" --model base
```

### estimate_transcription.py
Estimates processing time before starting batch transcription.

**Usage:**
```bash
python3 estimate_transcription.py
```

## Workflow Examples

### Process a Large Audio Collection

1. **Estimate time required:**
```bash
python3 estimate_transcription.py
```

2. **Process files under 30 minutes:**
```bash
python3 batch_transcribe_filtered.py "/mnt/c/Users/username/Documents/Audio" --model base
```

3. **Review skipped large files:**
```bash
python3 analyze_large_files.py
```

4. **Process important large files with truncation:**
```bash
python3 transcribe_truncated.py --batch --duration 60
```

### Process Meeting Recordings

For folders with meeting recordings that may have run long:

```bash
# First pass: Process normal-length recordings
python3 batch_transcribe_filtered.py "/path/to/meetings" --max-duration 90

# Second pass: Truncate and process long recordings
python3 transcribe_truncated.py --batch --duration 60
```

## Vector Database Search

All transcribed audio is automatically added to the vector database for semantic search.

**Access the search interface:**
```
http://localhost:8002/search.html
```

**Features:**
- Semantic search across all transcripts
- Multi-language support (English, Chinese, etc.)
- RAG (Retrieval-Augmented Generation) context
- Export search results

## Performance Tips

1. **Model Selection:**
   - `tiny`: Fastest, lower accuracy
   - `base`: Good balance (recommended)
   - `small/medium`: Better accuracy, slower
   - `large`: Best accuracy, very slow

2. **Duration Limits:**
   - 30 minutes: Good for quick processing
   - 60 minutes: Captures most meetings
   - 90+ minutes: Only for critical content

3. **Batch Processing:**
   - Process overnight for large collections
   - Use `--no-skip` carefully (re-processes everything)
   - Monitor with `tail -f batch_transcribe.log`

## File Format Support

Supported audio formats:
- MP3, M4A, WAV, FLAC
- OGG, OPUS, WEBM
- AAC, WMA, MP4

## Monitoring Progress

**Check running processes:**
```bash
ps aux | grep transcribe
```

**Monitor logs:**
```bash
tail -f batch_transcribe.log
tail -f batch_transcribe_dji.log
```

**Check vector database status:**
```bash
curl http://localhost:8001/vector/stats | python3 -m json.tool
```

## Troubleshooting

### Audio Service Not Running
```bash
cd services/audio
source audio-env/bin/activate
python transcription_server.py
```

### FFmpeg Not Installed (for truncation)
```bash
sudo apt-get update
sudo apt-get install -y ffmpeg
```

### Out of Memory
- Use smaller Whisper model (`tiny` or `base`)
- Process fewer files at once
- Increase system swap space

### Timeout Errors
- Large files may timeout with default settings
- Use truncation for files over 2 hours
- Consider splitting very long recordings

## Output Files

Batch processing creates several output files:
- `transcription_results_[timestamp].json` - Full results with metadata
- `truncated_transcripts_[timestamp].json` - Results from truncated files
- Individual `.txt` files for each transcription (optional)

## Best Practices

1. **Start with estimation** to understand processing time
2. **Use filtering** to skip unnecessarily long files
3. **Truncate recordings** that likely ran too long
4. **Monitor progress** with log files
5. **Search immediately** - transcripts are instantly searchable
6. **Keep backups** of important audio files before processing