#!/usr/bin/env python3
"""Truncate and transcribe large audio files - process only first hour"""

import os
import sys
import time
import requests
import argparse
import tempfile
import subprocess
import json
from pathlib import Path
from datetime import datetime

# Supported audio formats
SUPPORTED_FORMATS = {'.mp3', '.wav', '.m4a', '.mp4', '.flac', '.ogg', '.webm', '.opus', '.aac', '.wma'}

def format_size(bytes):
    """Format bytes into human readable size"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.1f} TB"

def truncate_audio(input_path, output_path, duration_seconds=3600):
    """Truncate audio file to specified duration using ffmpeg"""
    try:
        # Use ffmpeg to truncate the file
        cmd = [
            'ffmpeg',
            '-i', str(input_path),
            '-t', str(duration_seconds),  # Duration in seconds
            '-c', 'copy',  # Copy codec (fast, no re-encoding)
            '-y',  # Overwrite output
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            return True
        else:
            # Try again with re-encoding if copy failed
            cmd[4] = 'pcm_s16le' if output_path.suffix.lower() == '.wav' else 'libmp3lame'
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
    except FileNotFoundError:
        print("❌ ffmpeg not found. Installing...")
        subprocess.run(['sudo', 'apt-get', 'update'], capture_output=True)
        subprocess.run(['sudo', 'apt-get', 'install', '-y', 'ffmpeg'], capture_output=True)
        return truncate_audio(input_path, output_path, duration_seconds)  # Retry
    except Exception as e:
        print(f"Error truncating: {e}")
        return False

def transcribe_file(file_path, model='base', api_url='http://localhost:8001'):
    """Transcribe an audio file"""
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f, 'audio/mpeg')}
            data = {
                'model': model,
                'save_transcript': 'true'
            }
            
            response = requests.post(
                f"{api_url}/transcribe",
                files=files,
                data=data,
                timeout=600  # 10 minute timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
    except Exception as e:
        print(f"Transcription error: {e}")
        return None

def process_large_file(file_path, max_duration_minutes=60, model='base', keep_truncated=False):
    """Process a single large file by truncating and transcribing"""
    
    file_path = Path(file_path)
    
    if not file_path.exists():
        return {'success': False, 'error': 'File not found'}
    
    file_size = file_path.stat().st_size
    max_duration_seconds = max_duration_minutes * 60
    
    print(f"\n📄 Processing: {file_path.name}")
    print(f"   Size: {format_size(file_size)}")
    
    # Create temporary truncated file
    temp_dir = Path(tempfile.gettempdir())
    truncated_path = temp_dir / f"truncated_{file_path.stem}{file_path.suffix}"
    
    print(f"   ✂️ Truncating to first {max_duration_minutes} minutes...")
    
    if truncate_audio(file_path, truncated_path, max_duration_seconds):
        truncated_size = truncated_path.stat().st_size
        print(f"   ✅ Truncated: {format_size(truncated_size)}")
        
        # Transcribe the truncated file
        print(f"   ⏳ Transcribing...")
        start_time = time.time()
        
        result = transcribe_file(truncated_path, model)
        elapsed = time.time() - start_time
        
        if result:
            print(f"   ✅ Success! ({elapsed:.1f}s)")
            print(f"      ID: {result.get('transcript_id')}")
            print(f"      Language: {result['transcription'].get('language', 'unknown')}")
            
            # Add note about truncation to transcript
            original_text = result['transcription']['text']
            truncation_note = f"[NOTE: This is a truncated transcript of the first {max_duration_minutes} minutes of a longer recording]"
            
            # Clean up unless keeping
            if not keep_truncated:
                truncated_path.unlink()
            else:
                print(f"   💾 Truncated file saved: {truncated_path}")
            
            return {
                'success': True,
                'file': str(file_path),
                'truncated_minutes': max_duration_minutes,
                'transcript_id': result.get('transcript_id'),
                'text': original_text,
                'language': result['transcription'].get('language'),
                'note': truncation_note
            }
        else:
            print(f"   ❌ Transcription failed")
            if not keep_truncated:
                truncated_path.unlink()
            return {'success': False, 'error': 'Transcription failed'}
    else:
        print(f"   ❌ Truncation failed")
        return {'success': False, 'error': 'Truncation failed'}

def batch_process_large_files(max_duration_minutes=60, model='base'):
    """Process all previously skipped large files"""
    
    print("=" * 70)
    print(f"BATCH TRUNCATE & TRANSCRIBE (First {max_duration_minutes} minutes)")
    print("=" * 70)
    
    # Load the list of skipped files
    results_file = 'transcription_results_20250904_031140.json'
    
    if not os.path.exists(results_file):
        print("❌ No previous results file found")
        print("Run batch_transcribe_filtered.py first")
        return
    
    with open(results_file, 'r') as f:
        data = json.load(f)
        skipped_files = data.get('skipped_large_files', [])
    
    if not skipped_files:
        print("❌ No skipped files found")
        return
    
    print(f"📊 Found {len(skipped_files)} large files to process")
    
    # Check audio service
    try:
        response = requests.get("http://localhost:8001/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            print(f"✅ Audio service running (Model: {health['current_model']})")
        else:
            raise Exception()
    except:
        print("❌ Audio service not running!")
        print("Start it with:")
        print("  cd services/audio && source audio-env/bin/activate && python transcription_server.py")
        return
    
    # Process each file
    results = []
    errors = []
    
    print(f"\n🎯 Processing {len(skipped_files)} files...")
    print("-" * 50)
    
    for i, file_path in enumerate(skipped_files, 1):
        print(f"\n[{i}/{len(skipped_files)}]")
        
        result = process_large_file(
            file_path,
            max_duration_minutes=max_duration_minutes,
            model=model
        )
        
        if result['success']:
            results.append(result)
        else:
            errors.append(result)
        
        # Small delay between files
        if i < len(skipped_files):
            time.sleep(1)
    
    # Summary
    print("\n" + "=" * 70)
    print("BATCH PROCESSING COMPLETE")
    print("=" * 70)
    print(f"✅ Successfully processed: {len(results)}")
    print(f"❌ Failed: {len(errors)}")
    
    # Save results
    output_file = f"truncated_transcripts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'max_duration_minutes': max_duration_minutes,
            'model': model,
            'processed': len(results),
            'failed': len(errors),
            'results': results,
            'errors': errors
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Results saved to: {output_file}")
    print("\n🔍 All transcripts added to vector database!")
    print("Search them at: http://localhost:8002/search.html")

def main():
    parser = argparse.ArgumentParser(
        description='Truncate and transcribe large audio files',
        epilog="""
This tool helps process large audio files that may have been left recording.
It truncates files to a specified duration (default 60 minutes) before transcribing.

Examples:
  # Process a single file (first 60 minutes)
  python3 transcribe_truncated.py --file "Recording (9).m4a"
  
  # Process all skipped large files (first 60 minutes)
  python3 transcribe_truncated.py --batch
  
  # Use 45 minute truncation
  python3 transcribe_truncated.py --batch --duration 45
  
  # Use a different model
  python3 transcribe_truncated.py --batch --model small
        """
    )
    
    parser.add_argument('--file', help='Single file to process')
    parser.add_argument('--batch', action='store_true', 
                      help='Process all previously skipped large files')
    parser.add_argument('--duration', type=int, default=60,
                      help='Maximum duration in minutes (default: 60)')
    parser.add_argument('--model', default='base',
                      choices=['tiny', 'base', 'small', 'medium', 'large'],
                      help='Whisper model to use (default: base)')
    parser.add_argument('--keep', action='store_true',
                      help='Keep truncated audio files')
    
    args = parser.parse_args()
    
    if args.file:
        # Process single file
        result = process_large_file(
            args.file,
            max_duration_minutes=args.duration,
            model=args.model,
            keep_truncated=args.keep
        )
        
        if result['success']:
            print("\n✅ Processing complete!")
            print(f"Transcript ID: {result['transcript_id']}")
        else:
            print(f"\n❌ Processing failed: {result.get('error')}")
    
    elif args.batch:
        # Batch process all large files
        batch_process_large_files(
            max_duration_minutes=args.duration,
            model=args.model
        )
    
    else:
        parser.print_help()

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Truncate & Transcribe Tool")
        print("-" * 40)
        print("Process large audio files by truncating to first hour")
        print("\nUsage:")
        print("  Process all large files: python3 transcribe_truncated.py --batch")
        print("  Process single file:     python3 transcribe_truncated.py --file <path>")
        print("\nFor full help: python3 transcribe_truncated.py --help")
    else:
        main()