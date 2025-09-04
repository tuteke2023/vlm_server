#!/usr/bin/env python3
"""Estimate transcription time for audio folders"""

import os
import sys
from pathlib import Path
from datetime import timedelta

# Supported audio formats
SUPPORTED_FORMATS = {'.mp3', '.wav', '.m4a', '.mp4', '.flac', '.ogg', '.webm', '.opus', '.aac', '.wma'}

def format_time(seconds):
    """Format seconds into human readable time"""
    if seconds < 60:
        return f"{seconds:.0f} seconds"
    elif seconds < 3600:
        return f"{seconds/60:.1f} minutes"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours:.0f} hours {minutes:.0f} minutes"

def format_size(bytes):
    """Format bytes into human readable size"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes < 1024.0:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.1f} PB"

def scan_folder(folder_path):
    """Scan folder for audio files and calculate statistics"""
    folder = Path(folder_path)
    
    if not folder.exists():
        return None, f"Folder does not exist: {folder_path}"
    
    audio_files = []
    total_size = 0
    file_types = {}
    
    try:
        # Scan recursively for audio files
        for file_path in folder.rglob('*'):
            if file_path.is_file():
                suffix = file_path.suffix.lower()
                if suffix in SUPPORTED_FORMATS:
                    try:
                        size = file_path.stat().st_size
                        audio_files.append({
                            'path': file_path,
                            'name': file_path.name,
                            'size': size,
                            'type': suffix
                        })
                        total_size += size
                        file_types[suffix] = file_types.get(suffix, 0) + 1
                    except:
                        pass  # Skip files we can't access
    except PermissionError:
        return None, f"Permission denied accessing folder: {folder_path}"
    
    return {
        'files': audio_files,
        'total_size': total_size,
        'file_types': file_types,
        'count': len(audio_files)
    }, None

def estimate_transcription_time(scan_result, model='base'):
    """Estimate transcription time based on file sizes and model"""
    
    # Rough estimates based on Whisper model speeds (seconds per MB)
    # These vary greatly based on hardware (GPU vs CPU) and audio content
    # Using RTX GPU estimates
    model_speeds = {
        'tiny': 0.5,    # ~0.5 seconds per MB
        'base': 1.0,    # ~1 second per MB
        'small': 2.0,   # ~2 seconds per MB
        'medium': 4.0,  # ~4 seconds per MB
        'large': 8.0    # ~8 seconds per MB
    }
    
    # CPU is roughly 10x slower
    cpu_multiplier = 10
    
    speed_gpu = model_speeds.get(model, 1.0)
    speed_cpu = speed_gpu * cpu_multiplier
    
    total_mb = scan_result['total_size'] / (1024 * 1024)
    
    # Calculate time estimates
    time_gpu = total_mb * speed_gpu
    time_cpu = total_mb * speed_cpu
    
    # Add overhead for file I/O, API calls, vectorization (20%)
    overhead = 1.2
    time_gpu *= overhead
    time_cpu *= overhead
    
    # Add time for vectorization and database operations (~0.5 sec per file)
    vector_time = scan_result['count'] * 0.5
    time_gpu += vector_time
    time_cpu += vector_time
    
    return {
        'gpu': time_gpu,
        'cpu': time_cpu,
        'total_mb': total_mb
    }

def main():
    print("=" * 70)
    print("AUDIO TRANSCRIPTION TIME ESTIMATOR")
    print("=" * 70)
    
    # Windows paths converted to WSL paths
    folders = [
        "/mnt/c/Users/tekee.DESKTOP-VMDIEU8/OneDrive/Documents/Sound recordings",
        "/mnt/e/DJI_Audio_001"
    ]
    
    total_files = 0
    total_size = 0
    all_files = []
    
    for folder_path in folders:
        print(f"\n📂 Scanning: {folder_path}")
        scan_result, error = scan_folder(folder_path)
        
        if error:
            print(f"   ❌ {error}")
            continue
        
        if scan_result['count'] == 0:
            print(f"   ⚠️  No audio files found")
            continue
        
        print(f"   ✅ Found {scan_result['count']} audio files")
        print(f"   📊 Total size: {format_size(scan_result['total_size'])}")
        
        # Show file type breakdown
        if scan_result['file_types']:
            print(f"   📁 File types:")
            for ext, count in sorted(scan_result['file_types'].items()):
                print(f"      {ext}: {count} file(s)")
        
        # Show largest files
        if scan_result['files']:
            largest = sorted(scan_result['files'], key=lambda x: x['size'], reverse=True)[:3]
            print(f"   📈 Largest files:")
            for f in largest:
                print(f"      {f['name']}: {format_size(f['size'])}")
        
        total_files += scan_result['count']
        total_size += scan_result['total_size']
        all_files.extend(scan_result['files'])
    
    if total_files == 0:
        print("\n❌ No audio files found in any folder!")
        return
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"📊 Total audio files: {total_files}")
    print(f"💾 Total size: {format_size(total_size)}")
    
    # Estimate for different models
    print("\n⏱️  TIME ESTIMATES:")
    print("-" * 40)
    
    models = ['tiny', 'base', 'small', 'medium', 'large']
    scan_data = {'count': total_files, 'total_size': total_size}
    
    print("\nWith GPU (CUDA):")
    for model in models:
        estimate = estimate_transcription_time(scan_data, model)
        print(f"  {model:7} model: ~{format_time(estimate['gpu'])}")
    
    print("\nWith CPU only:")
    for model in models:
        estimate = estimate_transcription_time(scan_data, model)
        print(f"  {model:7} model: ~{format_time(estimate['cpu'])}")
    
    # Recommendations
    print("\n" + "=" * 70)
    print("RECOMMENDATIONS")
    print("=" * 70)
    
    base_estimate = estimate_transcription_time(scan_data, 'base')
    
    print(f"\n🎯 Using 'base' model with GPU: ~{format_time(base_estimate['gpu'])}")
    print(f"   This provides good balance of speed and accuracy")
    
    if total_files > 50:
        print(f"\n💡 You have {total_files} files. Consider:")
        print("   1. Start with a subset to test")
        print("   2. Run overnight for full processing")
        print("   3. Use 'tiny' model for faster initial pass")
    
    if total_size > 1024 * 1024 * 1024:  # > 1GB
        print(f"\n⚠️  Large dataset ({format_size(total_size)}). Tips:")
        print("   • Ensure enough disk space for transcripts")
        print("   • Consider processing in batches")
        print("   • Monitor GPU memory usage")
    
    print("\n📝 To start transcription:")
    print("   python3 batch_transcribe.py '/mnt/c/Users/tekee.DESKTOP-VMDIEU8/OneDrive/Documents/Sound recordings'")
    print("   python3 batch_transcribe.py '/mnt/e/DJI_Audio_001'")
    print("\n   Or process both with a single command:")
    print("   python3 batch_transcribe.py '/mnt/c/Users/tekee.DESKTOP-VMDIEU8/OneDrive/Documents/Sound recordings' && \\")
    print("   python3 batch_transcribe.py '/mnt/e/DJI_Audio_001'")

if __name__ == "__main__":
    main()