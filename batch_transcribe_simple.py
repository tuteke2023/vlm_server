#!/usr/bin/env python3
"""
Simple batch transcription without ffmpeg dependencies
Sends files directly to Whisper API
"""

import os
import sys
import time
import requests
from pathlib import Path
from datetime import datetime
import json
import hashlib

# Configuration
AUDIO_DIR = "/mnt/c/Users/tekee/Documents/Sound Recordings"
API_URL = "http://localhost:8001"
SUPPORTED_FORMATS = {'.mp3', '.wav', '.m4a', '.mp4', '.flac', '.ogg', '.webm', '.opus', '.aac', '.wma'}

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

def transcribe_file(file_path: str, metadata: dict = None) -> dict:
    """Transcribe a single audio file"""
    try:
        # Prepare metadata
        if metadata is None:
            metadata = {}
        
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        metadata['source_path'] = str(file_path)
        metadata['file_size_mb'] = file_size_mb
        
        # Note for large files
        if file_size_mb > 20:
            print(f"  ⚠️  Large file ({file_size_mb:.1f} MB) - may take longer to process")
            metadata['note'] = 'Large file - consider truncating if > 1 hour'
        
        # Send to API
        print(f"  📤 Sending to transcription API...")
        with open(file_path, 'rb') as f:
            files = {'file': (Path(file_path).name, f, 'audio/m4a')}
            data = {
                'language': 'en',
                'task': 'transcribe',
                'metadata': json.dumps(metadata)
            }
            
            # Longer timeout for larger files
            timeout = 600 if file_size_mb < 20 else 1200
            
            response = requests.post(
                f"{API_URL}/transcribe",
                files=files,
                data=data,
                timeout=timeout
            )
        
        if response.status_code == 200:
            result = response.json()
            print(f"  ✅ Transcribed successfully!")
            return result
        else:
            error_msg = response.text[:200] if response.text else f"Status {response.status_code}"
            print(f"  ❌ Transcription failed: {error_msg}")
            return None
            
    except requests.Timeout:
        print(f"  ⏱️  Timeout - file may be too large")
        return None
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return None

def main():
    """Main batch transcription function"""
    print(f"🎙️  Simple Batch Transcription Tool")
    print(f"📂 Source: {AUDIO_DIR}")
    print(f"🌐 API: {API_URL}")
    print("-" * 50)
    
    # Check if API is available
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Transcription API is not available!")
            return
        print("✅ API is healthy")
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
    
    # Check current vector DB status
    try:
        response = requests.get(f"{API_URL}/vector/stats", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print(f"📚 Current database: {stats['total_transcripts']} transcripts")
    except:
        pass
    
    print("\nStarting transcription...\n")
    
    # Process statistics
    successful = []
    failed = []
    skipped = []
    
    # Process each file
    for i, file_path in enumerate(audio_files, 1):
        file_name = Path(file_path).name
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
        
        print(f"[{i}/{len(audio_files)}] {file_name}")
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
            'total_files': len(audio_files),
            'original_filename': file_name
        })
        
        if result:
            successful.append(file_name)
            
            # Show preview of transcript
            if 'text' in result:
                preview = result['text'][:150] + "..." if len(result['text']) > 150 else result['text']
                print(f"  📝 Preview: {preview}")
            
            # Update vector count
            if 'vectors_added' in result:
                print(f"  🔍 Added {result['vectors_added']} vector chunks")
        else:
            failed.append(file_name)
        
        # Small delay between files
        time.sleep(2)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TRANSCRIPTION SUMMARY")
    print(f"✅ Successful: {len(successful)}")
    print(f"⏭️  Skipped (already done): {len(skipped)}")
    print(f"❌ Failed: {len(failed)}")
    
    if failed:
        print("\n❌ Failed files:")
        for f in failed[:10]:  # Show first 10
            print(f"  - {f}")
        if len(failed) > 10:
            print(f"  ... and {len(failed) - 10} more")
    
    # Check final vector database stats
    try:
        response = requests.get(f"{API_URL}/vector/stats", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print(f"\n🔍 Final Vector Database Stats:")
            print(f"  - Total transcripts: {stats['total_transcripts']}")
            print(f"  - Total chunks: {stats['total_chunks']}")
            print(f"\n✨ You can now search these transcripts at:")
            print(f"   http://localhost:8002/search.html")
    except:
        pass
    
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

if __name__ == "__main__":
    main()