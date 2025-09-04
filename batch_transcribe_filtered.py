#!/usr/bin/env python3
"""Batch Transcribe Audio Files with Size Filtering - Skip long recordings"""

import os
import sys
import time
import requests
import argparse
from pathlib import Path
from datetime import datetime
import json

# Supported audio formats
SUPPORTED_FORMATS = {'.mp3', '.wav', '.m4a', '.mp4', '.flac', '.ogg', '.webm', '.opus', '.aac', '.wma'}

# Approximate file size limits for 30 minutes of audio
# These are rough estimates - actual size depends on bitrate
SIZE_LIMITS = {
    '.mp3': 45 * 1024 * 1024,    # 45 MB for 30 min @ 128kbps
    '.m4a': 35 * 1024 * 1024,    # 35 MB for 30 min @ 96kbps  
    '.wav': 300 * 1024 * 1024,   # 300 MB for 30 min uncompressed
    '.flac': 150 * 1024 * 1024,  # 150 MB for 30 min lossless
    '.ogg': 30 * 1024 * 1024,     # 30 MB for 30 min @ 64kbps
    '.mp4': 50 * 1024 * 1024,     # 50 MB for 30 min
    '.webm': 35 * 1024 * 1024,    # 35 MB for 30 min
    '.opus': 25 * 1024 * 1024,    # 25 MB for 30 min
    '.aac': 40 * 1024 * 1024,     # 40 MB for 30 min
    '.wma': 45 * 1024 * 1024,     # 45 MB for 30 min
}

def format_size(bytes):
    """Format bytes into human readable size"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.1f} TB"

def estimate_duration(file_path, file_size):
    """Estimate audio duration based on file size and format"""
    ext = file_path.suffix.lower()
    
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

class FilteredBatchTranscriber:
    def __init__(self, api_url="http://localhost:8001", model="base", max_duration_minutes=30):
        self.api_url = api_url
        self.model = model
        self.max_duration_minutes = max_duration_minutes
        self.results = []
        self.errors = []
        self.skipped_large = []
        
    def check_service(self):
        """Check if the audio service is running"""
        try:
            response = requests.get(f"{self.api_url}/health")
            if response.status_code == 200:
                health = response.json()
                print(f"✅ Audio service is running (Model: {health['current_model']})")
                return True
        except:
            pass
        
        print("❌ Audio service is not running!")
        print("Please start it with:")
        print("  cd services/audio && source audio-env/bin/activate && python transcription_server.py")
        return False
    
    def scan_folder(self, folder_path):
        """Scan folder for audio files and filter by size"""
        audio_files = []
        skipped_files = []
        folder = Path(folder_path)
        
        if not folder.exists():
            print(f"❌ Folder does not exist: {folder_path}")
            return [], []
        
        # Get size limit for each format
        default_limit = self.max_duration_minutes * 2 * 1024 * 1024  # Rough default: 2MB per minute
        
        # Scan recursively for audio files
        for file_path in folder.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_FORMATS:
                try:
                    file_size = file_path.stat().st_size
                    ext = file_path.suffix.lower()
                    
                    # Get size limit for this format
                    size_limit = SIZE_LIMITS.get(ext, default_limit)
                    
                    # Estimate duration
                    est_duration = estimate_duration(file_path, file_size)
                    
                    if file_size > size_limit or est_duration > self.max_duration_minutes:
                        skipped_files.append({
                            'path': file_path,
                            'size': file_size,
                            'est_duration': est_duration
                        })
                    else:
                        audio_files.append(file_path)
                except Exception as e:
                    print(f"Warning: Could not access {file_path}: {e}")
        
        return sorted(audio_files), skipped_files
    
    def transcribe_file(self, file_path):
        """Transcribe a single audio file"""
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (file_path.name, f, 'audio/mpeg')}
                data = {
                    'model': self.model,
                    'save_transcript': 'true'
                }
                
                response = requests.post(
                    f"{self.api_url}/transcribe",
                    files=files,
                    data=data,
                    timeout=300
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        'success': True,
                        'file': str(file_path),
                        'transcript_id': result.get('transcript_id'),
                        'text': result['transcription']['text'],
                        'language': result['transcription'].get('language', 'unknown')
                    }
                else:
                    return {
                        'success': False,
                        'file': str(file_path),
                        'error': f"HTTP {response.status_code}"
                    }
                    
        except Exception as e:
            return {
                'success': False,
                'file': str(file_path),
                'error': str(e)
            }
    
    def process_folder(self, folder_path, skip_existing=True):
        """Process audio files in folder, skipping large ones"""
        print("=" * 70)
        print("BATCH AUDIO TRANSCRIPTION (WITH SIZE FILTER)")
        print("=" * 70)
        print(f"⚙️  Max duration: {self.max_duration_minutes} minutes")
        
        # Check service
        if not self.check_service():
            return False
        
        # Scan for audio files
        print(f"\n📂 Scanning folder: {folder_path}")
        audio_files, skipped_large = self.scan_folder(folder_path)
        
        if skipped_large:
            print(f"⏭️  Skipping {len(skipped_large)} large file(s) (>30 minutes):")
            total_skipped_size = sum(f['size'] for f in skipped_large)
            print(f"   Total size skipped: {format_size(total_skipped_size)}")
            
            # Show first 5 skipped files
            for skip in skipped_large[:5]:
                print(f"   - {skip['path'].name}: {format_size(skip['size'])} (~{skip['est_duration']:.1f} min)")
            if len(skipped_large) > 5:
                print(f"   ... and {len(skipped_large) - 5} more")
            
            self.skipped_large = skipped_large
        
        if not audio_files:
            print("❌ No audio files found under size limit!")
            return False
        
        print(f"\n📊 Will process {len(audio_files)} file(s) under 30 minutes")
        total_size = sum(f.stat().st_size for f in audio_files)
        print(f"   Total size to process: {format_size(total_size)}")
        
        # Estimate time
        est_time_minutes = (total_size / (1024 * 1024)) * 1.0  # Rough: 1 sec per MB for base model
        print(f"   Estimated time: ~{est_time_minutes:.0f} minutes")
        
        # Get existing transcripts to avoid duplicates
        existing_files = set()
        if skip_existing:
            try:
                response = requests.get(f"{self.api_url}/transcripts?limit=500")
                if response.status_code == 200:
                    transcripts = response.json().get('transcripts', [])
                    existing_files = {t['audio_filename'] for t in transcripts if t.get('audio_filename')}
                    if existing_files:
                        print(f"   ⚡ Will skip {len(existing_files)} already transcribed file(s)")
            except:
                pass
        
        # Process each file
        print(f"\n🎯 Starting transcription (Model: {self.model})...")
        print("-" * 50)
        
        processed = 0
        skipped_existing = 0
        failed = 0
        
        for i, file_path in enumerate(audio_files, 1):
            file_name = file_path.name
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            
            # Progress indicator
            print(f"\n[{i}/{len(audio_files)}] {file_name} ({file_size_mb:.1f} MB)")
            
            # Skip if already processed
            if skip_existing and file_name in existing_files:
                print("  ⏭️  Skipped (already transcribed)")
                skipped_existing += 1
                continue
            
            # Transcribe
            print("  ⏳ Transcribing...", end="", flush=True)
            start_time = time.time()
            
            result = self.transcribe_file(file_path)
            elapsed = time.time() - start_time
            
            if result['success']:
                text_preview = result['text'][:100] if result['text'] else "empty"
                print(f"\r  ✅ Success! ({elapsed:.1f}s)")
                print(f"     ID: {result['transcript_id']}")
                print(f"     Language: {result['language']}")
                print(f"     Text: {text_preview}...")
                processed += 1
                self.results.append(result)
            else:
                print(f"\r  ❌ Failed: {result['error']}")
                failed += 1
                self.errors.append(result)
            
            # Small delay to avoid overwhelming the server
            if i < len(audio_files):
                time.sleep(0.5)
        
        # Summary
        print("\n" + "=" * 70)
        print("BATCH PROCESSING COMPLETE")
        print("=" * 70)
        print(f"✅ Successfully transcribed: {processed}")
        print(f"⏭️  Skipped (existing): {skipped_existing}")
        print(f"⏭️  Skipped (too large): {len(skipped_large)}")
        print(f"❌ Failed: {failed}")
        
        # Check vector database status
        print("\n📊 Vector Database Status:")
        try:
            response = requests.get(f"{self.api_url}/vector/stats")
            if response.status_code == 200:
                stats = response.json()
                print(f"   Total transcripts: {stats['total_transcripts']}")
                print(f"   Searchable chunks: {stats['total_chunks']}")
                print(f"   Ready for semantic search! 🔍")
        except:
            pass
        
        # Save results to file
        output_file = f"transcription_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'processed': processed,
                'skipped_existing': skipped_existing,
                'skipped_large': len(skipped_large),
                'failed': failed,
                'results': self.results,
                'errors': self.errors,
                'skipped_large_files': [str(f['path']) for f in skipped_large]
            }, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Results saved to: {output_file}")
        
        return True

def main():
    parser = argparse.ArgumentParser(
        description='Batch transcribe audio files with size filtering'
    )
    
    parser.add_argument('folder', help='Path to folder containing audio files')
    parser.add_argument('--model', default='base', 
                      choices=['tiny', 'base', 'small', 'medium', 'large'],
                      help='Whisper model to use (default: base)')
    parser.add_argument('--max-duration', type=int, default=30,
                      help='Maximum duration in minutes (default: 30)')
    parser.add_argument('--no-skip', dest='skip', action='store_false',
                      help='Do not skip already transcribed files')
    
    args = parser.parse_args()
    
    # Create transcriber
    transcriber = FilteredBatchTranscriber(
        model=args.model,
        max_duration_minutes=args.max_duration
    )
    
    # Process folder
    success = transcriber.process_folder(
        args.folder,
        skip_existing=args.skip
    )
    
    if success:
        print("\n🎯 Next steps:")
        print("1. Open the search UI: http://localhost:8002/search.html")
        print("2. Search across all your transcripts!")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Batch Transcriber with Size Filter")
        print("-" * 40)
        print("Usage: python batch_transcribe_filtered.py <folder> [options]")
        print("\nThis will skip files >30 minutes by default")
        print("\nExample:")
        print("  python batch_transcribe_filtered.py '/mnt/c/Users/tekee.DESKTOP-VMDIEU8/OneDrive/Documents/Sound recordings'")
    else:
        main()