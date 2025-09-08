#!/usr/bin/env python3
"""
Batch transcribe audio files from Windows Sound Recordings folder
with automatic truncation for files longer than 1 hour
"""

import os
import sys
import time
import requests
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime
import json
from typing import Optional, Dict, List
import hashlib

# Configuration
AUDIO_DIR = "/mnt/c/Users/tekee/Documents/Sound Recordings"
API_URL = "http://localhost:8001"
MAX_DURATION_MINUTES = 60  # Truncate files longer than this
SUPPORTED_FORMATS = {'.mp3', '.wav', '.m4a', '.mp4', '.flac', '.ogg', '.webm', '.opus', '.aac', '.wma'}

def get_audio_duration(file_path: str) -> Optional[float]:
    """Get audio duration in minutes using ffprobe"""
    try:
        cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            str(file_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0 and result.stdout.strip():
            duration_seconds = float(result.stdout.strip())
            return duration_seconds / 60  # Return in minutes
    except Exception as e:
        print(f"Could not get duration for {file_path}: {e}")
    return None

def truncate_audio(input_path: str, output_path: str, max_minutes: int = 60) -> bool:
    """Truncate audio file to specified duration"""
    try:
        max_seconds = max_minutes * 60
        cmd = [
            'ffmpeg', '-i', str(input_path),
            '-t', str(max_seconds),
            '-acodec', 'copy',
            '-y',  # Overwrite output
            str(output_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return result.returncode == 0
    except Exception as e:
        print(f"Failed to truncate {input_path}: {e}")
        return False

def get_file_hash(file_path: str) -> str:
    """Calculate hash of file for duplicate detection"""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def check_already_transcribed(file_hash: str) -> bool:
    """Check if file already transcribed via API"""
    try:
        response = requests.get(f"{API_URL}/transcripts", timeout=5)
        if response.status_code == 200:
            transcripts = response.json()
            for transcript in transcripts:
                if transcript.get('file_hash') == file_hash:
                    return True
    except Exception:
        pass
    return False

def transcribe_file(file_path: str, metadata: Dict = None) -> Optional[Dict]:
    """Transcribe a single audio file"""
    try:
        # Check duration
        duration = get_audio_duration(file_path)
        if duration is None:
            print(f"⚠️  Could not determine duration for {file_path}")
            duration = 0
        
        file_to_transcribe = file_path
        truncated = False
        
        # Truncate if needed
        if duration > MAX_DURATION_MINUTES:
            print(f"  📂 File is {duration:.1f} minutes, truncating to {MAX_DURATION_MINUTES} minutes...")
            with tempfile.NamedTemporaryFile(suffix=Path(file_path).suffix, delete=False) as tmp_file:
                temp_path = tmp_file.name
            
            if truncate_audio(file_path, temp_path, MAX_DURATION_MINUTES):
                file_to_transcribe = temp_path
                truncated = True
                print(f"  ✂️  Truncated successfully")
            else:
                print(f"  ❌ Truncation failed, skipping file")
                return None
        
        # Prepare metadata
        if metadata is None:
            metadata = {}
        metadata['original_duration_minutes'] = duration
        metadata['truncated'] = truncated
        metadata['max_duration'] = MAX_DURATION_MINUTES if truncated else None
        metadata['source_path'] = str(file_path)
        
        # Send to API
        print(f"  📤 Sending to transcription API...")
        with open(file_to_transcribe, 'rb') as f:
            files = {'file': (Path(file_path).name, f, 'audio/m4a')}
            data = {
                'language': 'en',
                'task': 'transcribe',
                'metadata': json.dumps(metadata)
            }
            
            response = requests.post(
                f"{API_URL}/transcribe",
                files=files,
                data=data,
                timeout=600  # 10 minute timeout
            )
        
        # Clean up temp file if used
        if truncated:
            try:
                os.unlink(file_to_transcribe)
            except:
                pass
        
        if response.status_code == 200:
            result = response.json()
            print(f"  ✅ Transcribed successfully!")
            return result
        else:
            print(f"  ❌ Transcription failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"  ❌ Error transcribing {file_path}: {e}")
        return None

def main():
    """Main batch transcription function"""
    print(f"🎙️  Batch Transcription Tool")
    print(f"📂 Source: {AUDIO_DIR}")
    print(f"⏱️  Max duration: {MAX_DURATION_MINUTES} minutes")
    print(f"🌐 API: {API_URL}")
    print("-" * 50)
    
    # Check if API is available
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Transcription API is not available!")
            return
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        return
    
    # Find all audio files
    audio_files = []
    for ext in SUPPORTED_FORMATS:
        pattern = os.path.join(AUDIO_DIR, f"*{ext}")
        import glob
        files = glob.glob(pattern)
        audio_files.extend(files)
    
    audio_files = sorted(set(audio_files))  # Remove duplicates and sort
    
    if not audio_files:
        print(f"No audio files found in {AUDIO_DIR}")
        return
    
    print(f"\n📊 Found {len(audio_files)} audio files")
    
    # Process statistics
    successful = []
    failed = []
    skipped = []
    
    # Process each file
    for i, file_path in enumerate(audio_files, 1):
        file_name = Path(file_path).name
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
        
        print(f"\n[{i}/{len(audio_files)}] Processing: {file_name}")
        print(f"  📦 Size: {file_size:.1f} MB")
        
        # Check if already transcribed
        file_hash = get_file_hash(file_path)
        if check_already_transcribed(file_hash):
            print(f"  ⏭️  Already transcribed, skipping...")
            skipped.append(file_name)
            continue
        
        # Transcribe
        result = transcribe_file(file_path, {
            'batch_run': datetime.now().isoformat(),
            'file_index': i,
            'total_files': len(audio_files)
        })
        
        if result:
            successful.append(file_name)
            
            # Show preview of transcript
            if 'text' in result:
                preview = result['text'][:200] + "..." if len(result['text']) > 200 else result['text']
                print(f"  📝 Preview: {preview}")
        else:
            failed.append(file_name)
        
        # Small delay between files
        time.sleep(1)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TRANSCRIPTION SUMMARY")
    print(f"✅ Successful: {len(successful)}")
    print(f"⏭️  Skipped (already done): {len(skipped)}")
    print(f"❌ Failed: {len(failed)}")
    
    if failed:
        print("\n❌ Failed files:")
        for f in failed:
            print(f"  - {f}")
    
    # Save results
    results_file = f"transcription_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'source_dir': AUDIO_DIR,
            'total_files': len(audio_files),
            'successful': successful,
            'failed': failed,
            'skipped': skipped
        }, f, indent=2)
    
    print(f"\n📄 Results saved to: {results_file}")
    
    # Check vector database stats
    try:
        response = requests.get(f"{API_URL}/vector/stats", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print(f"\n🔍 Vector Database Stats:")
            print(f"  - Total transcripts: {stats['total_transcripts']}")
            print(f"  - Total chunks: {stats['total_chunks']}")
    except:
        pass

if __name__ == "__main__":
    main()