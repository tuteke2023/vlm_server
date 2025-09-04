#!/usr/bin/env python3
"""Batch Transcribe Audio Files - Process entire folders and make them searchable"""

import os
import sys
import time
import requests
import argparse
from pathlib import Path
from datetime import datetime
import json

# Supported audio formats
SUPPORTED_FORMATS = {'.mp3', '.wav', '.m4a', '.mp4', '.flac', '.ogg', '.webm', '.opus'}

class BatchTranscriber:
    def __init__(self, api_url="http://localhost:8001", model="base"):
        self.api_url = api_url
        self.model = model
        self.results = []
        self.errors = []
        
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
        """Scan folder for audio files"""
        audio_files = []
        folder = Path(folder_path)
        
        if not folder.exists():
            print(f"❌ Folder does not exist: {folder_path}")
            return []
        
        # Scan recursively for audio files
        for file_path in folder.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_FORMATS:
                audio_files.append(file_path)
        
        return sorted(audio_files)
    
    def transcribe_file(self, file_path):
        """Transcribe a single audio file"""
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (file_path.name, f, 'audio/mpeg')}
                data = {
                    'model': self.model,
                    'save_transcript': 'true'  # This ensures vectorization
                }
                
                response = requests.post(
                    f"{self.api_url}/transcribe",
                    files=files,
                    data=data,
                    timeout=300  # 5 minute timeout for large files
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
    
    def process_folder(self, folder_path, recursive=True, skip_existing=True):
        """Process all audio files in a folder"""
        print("=" * 70)
        print("BATCH AUDIO TRANSCRIPTION")
        print("=" * 70)
        
        # Check service
        if not self.check_service():
            return False
        
        # Scan for audio files
        print(f"\n📂 Scanning folder: {folder_path}")
        audio_files = self.scan_folder(folder_path)
        
        if not audio_files:
            print("❌ No audio files found!")
            print(f"Supported formats: {', '.join(SUPPORTED_FORMATS)}")
            return False
        
        print(f"📊 Found {len(audio_files)} audio file(s)")
        
        # Get existing transcripts to avoid duplicates
        existing_files = set()
        if skip_existing:
            try:
                response = requests.get(f"{self.api_url}/transcripts?limit=100")
                if response.status_code == 200:
                    transcripts = response.json().get('transcripts', [])
                    existing_files = {t['audio_filename'] for t in transcripts if t.get('audio_filename')}
                    if existing_files:
                        print(f"⚡ Skipping {len(existing_files)} already transcribed file(s)")
            except:
                pass
        
        # Process each file
        print(f"\n🎯 Starting transcription (Model: {self.model})...")
        print("-" * 50)
        
        processed = 0
        skipped = 0
        failed = 0
        
        for i, file_path in enumerate(audio_files, 1):
            file_name = file_path.name
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            
            # Progress indicator
            print(f"\n[{i}/{len(audio_files)}] {file_name} ({file_size_mb:.1f} MB)")
            
            # Skip if already processed
            if skip_existing and file_name in existing_files:
                print("  ⏭️  Skipped (already transcribed)")
                skipped += 1
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
        print(f"⏭️  Skipped (existing): {skipped}")
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
        if self.results:
            output_file = f"transcription_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'processed': processed,
                    'skipped': skipped,
                    'failed': failed,
                    'results': self.results,
                    'errors': self.errors
                }, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Results saved to: {output_file}")
        
        return True

def main():
    parser = argparse.ArgumentParser(
        description='Batch transcribe audio files and add them to vector database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Transcribe all audio files in a folder
  python batch_transcribe.py /path/to/audio/folder
  
  # Use a specific model (tiny, base, small, medium, large)
  python batch_transcribe.py /path/to/audio/folder --model small
  
  # Process without skipping existing transcripts
  python batch_transcribe.py /path/to/audio/folder --no-skip
  
  # Non-recursive (only files in the specified folder)
  python batch_transcribe.py /path/to/audio/folder --no-recursive

Supported formats: .mp3, .wav, .m4a, .mp4, .flac, .ogg, .webm, .opus
        """
    )
    
    parser.add_argument('folder', help='Path to folder containing audio files')
    parser.add_argument('--model', default='base', 
                      choices=['tiny', 'base', 'small', 'medium', 'large'],
                      help='Whisper model to use (default: base)')
    parser.add_argument('--no-skip', dest='skip', action='store_false',
                      help='Do not skip already transcribed files')
    parser.add_argument('--no-recursive', dest='recursive', action='store_false',
                      help='Do not scan subfolders')
    parser.add_argument('--api-url', default='http://localhost:8001',
                      help='Audio service API URL')
    
    args = parser.parse_args()
    
    # Create transcriber
    transcriber = BatchTranscriber(api_url=args.api_url, model=args.model)
    
    # Process folder
    success = transcriber.process_folder(
        args.folder,
        recursive=args.recursive,
        skip_existing=args.skip
    )
    
    if success and transcriber.results:
        print("\n🎯 Next steps:")
        print("1. Open the search UI: http://localhost:8002/search.html")
        print("2. Search across all your transcripts with semantic search!")
        print("3. Try queries like:")
        print("   - 'important decisions'")
        print("   - 'action items'")
        print("   - 'problems discussed'")
        print("   - Or search in any language!")

if __name__ == "__main__":
    # If no arguments provided, show help
    if len(sys.argv) == 1:
        print("Batch Audio Transcriber - Process entire folders!")
        print("-" * 50)
        print("Usage: python batch_transcribe.py <folder_path> [options]")
        print("\nExample:")
        print("  python batch_transcribe.py ~/Music/Podcasts")
        print("  python batch_transcribe.py /path/to/meetings --model large")
        print("\nFor full help: python batch_transcribe.py --help")
    else:
        main()