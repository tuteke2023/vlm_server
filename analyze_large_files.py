#!/usr/bin/env python3
"""Analyze large skipped audio files and their estimated durations"""

import json
from pathlib import Path
import os

def format_size(bytes):
    """Format bytes into human readable size"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.1f} TB"

def estimate_duration(file_path, file_size):
    """Estimate audio duration based on file size and format"""
    ext = Path(file_path).suffix.lower()
    
    # Rough bitrate estimates for duration calculation
    bitrate_estimates = {
        '.mp3': 128,   # kbps
        '.m4a': 96,
        '.wav': 1411,  # uncompressed
        '.flac': 700,
        '.ogg': 64,
        '.mp4': 128,
        '.webm': 96,
        '.opus': 64,
        '.aac': 128,
        '.wma': 128,
    }
    
    bitrate = bitrate_estimates.get(ext, 128)  # Default 128 kbps
    
    # Calculate approximate duration in minutes
    # file_size in bytes, bitrate in kbps
    duration_minutes = (file_size * 8) / (bitrate * 1000 * 60)
    
    return duration_minutes

print("=" * 80)
print("ANALYSIS OF SKIPPED LARGE AUDIO FILES (>30 minutes)")
print("=" * 80)

# Load the skipped files from results
with open('transcription_results_20250904_031140.json', 'r') as f:
    data = json.load(f)
    skipped_files = data.get('skipped_large_files', [])

if not skipped_files:
    print("No skipped files found")
    exit()

# Analyze each file
file_info = []
total_size = 0
total_duration = 0

for file_path in skipped_files:
    try:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            duration = estimate_duration(file_path, size)
            file_info.append({
                'path': file_path,
                'name': Path(file_path).name,
                'size': size,
                'duration': duration,
                'ext': Path(file_path).suffix.lower()
            })
            total_size += size
            total_duration += duration
    except:
        pass

# Sort by duration
file_info.sort(key=lambda x: x['duration'], reverse=True)

# Group by duration ranges
short_medium = []  # 30-45 minutes
medium_long = []   # 45-90 minutes
very_long = []     # >90 minutes

for file in file_info:
    if file['duration'] <= 45:
        short_medium.append(file)
    elif file['duration'] <= 90:
        medium_long.append(file)
    else:
        very_long.append(file)

# Display summary
print(f"\nTOTAL: {len(file_info)} files")
print(f"Total size: {format_size(total_size)}")
print(f"Total duration: ~{total_duration:.0f} minutes ({total_duration/60:.1f} hours)")

print("\n" + "-" * 80)
print("BREAKDOWN BY DURATION:")
print("-" * 80)

print(f"\n📄 SHORT-MEDIUM (30-45 minutes): {len(short_medium)} files")
if short_medium:
    print("  Good candidates for individual transcription:")
    for i, file in enumerate(short_medium[:10], 1):
        print(f"  {i:2}. {file['name'][:60]:<60} ~{file['duration']:.0f} min ({format_size(file['size'])})")
    if len(short_medium) > 10:
        print(f"  ... and {len(short_medium) - 10} more")

print(f"\n📁 MEDIUM-LONG (45-90 minutes): {len(medium_long)} files")
if medium_long:
    print("  May want to transcribe selectively:")
    for i, file in enumerate(medium_long[:10], 1):
        print(f"  {i:2}. {file['name'][:60]:<60} ~{file['duration']:.0f} min ({format_size(file['size'])})")
    if len(medium_long) > 10:
        print(f"  ... and {len(medium_long) - 10} more")

print(f"\n📦 VERY LONG (>90 minutes): {len(very_long)} files")
if very_long:
    print("  Consider splitting or transcribing only if critical:")
    for i, file in enumerate(very_long[:10], 1):
        print(f"  {i:2}. {file['name'][:60]:<60} ~{file['duration']:.0f} min ({format_size(file['size'])})")
    if len(very_long) > 10:
        print(f"  ... and {len(very_long) - 10} more")

# Key files that might be important (based on naming)
print("\n" + "-" * 80)
print("POTENTIALLY IMPORTANT FILES (based on names):")
print("-" * 80)

important_keywords = ['meeting', 'call', 'interview', 'presentation', 'pitch', 'consultation']
important_files = []

for file in file_info:
    name_lower = file['name'].lower()
    if any(keyword in name_lower for keyword in important_keywords):
        important_files.append(file)

if important_files:
    for i, file in enumerate(important_files[:15], 1):
        print(f"{i:2}. {file['name'][:60]:<60} ~{file['duration']:.0f} min")

print("\n" + "=" * 80)
print("RECOMMENDATIONS:")
print("=" * 80)
print("1. For SHORT-MEDIUM files (30-45 min): Consider transcribing individually")
print("2. For MEDIUM-LONG files (45-90 min): Transcribe only if content is valuable")
print("3. For VERY LONG files (>90 min): Consider splitting or selective transcription")
print("\n📝 To transcribe a specific file, use:")
print("   python3 transcribe_single.py '<file_path>' --model base")