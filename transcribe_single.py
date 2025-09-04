#!/usr/bin/env python3
"""Transcribe a single audio file regardless of duration"""

import sys
import requests
import argparse
from pathlib import Path
import time

def format_size(bytes):
    """Format bytes into human readable size"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.1f} TB"

def transcribe_file(file_path, model='base', api_url='http://localhost:8001'):
    """Transcribe a single audio file"""
    
    file_path = Path(file_path)
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return False
    
    file_size = file_path.stat().st_size
    print(f"\n📄 File: {file_path.name}")
    print(f"📊 Size: {format_size(file_size)}")
    print(f"🎯 Model: {model}")
    print(f"⏳ Starting transcription...")
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f, 'audio/mpeg')}
            data = {
                'model': model,
                'save_transcript': 'true'
            }
            
            start_time = time.time()
            response = requests.post(
                f"{api_url}/transcribe",
                files=files,
                data=data,
                timeout=3600  # 60 minute timeout for very long files
            )
            
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                print(f"\n✅ SUCCESS!")
                print(f"⏱️  Time: {elapsed:.1f} seconds")
                print(f"🆔 ID: {result.get('transcript_id')}")
                print(f"🌐 Language: {result['transcription'].get('language', 'unknown')}")
                
                text = result['transcription']['text']
                print(f"\n📝 Transcript preview:")
                print("-" * 60)
                print(text[:500] if len(text) > 500 else text)
                if len(text) > 500:
                    print("...")
                print("-" * 60)
                
                # Save full transcript to file
                output_file = f"{file_path.stem}_transcript.txt"
                with open(output_file, 'w', encoding='utf-8') as out:
                    out.write(f"File: {file_path.name}\n")
                    out.write(f"Transcript ID: {result.get('transcript_id')}\n")
                    out.write(f"Language: {result['transcription'].get('language')}\n")
                    out.write(f"Duration: {elapsed:.1f} seconds\n")
                    out.write("=" * 60 + "\n\n")
                    out.write(text)
                
                print(f"\n💾 Full transcript saved to: {output_file}")
                print(f"🔍 Searchable in vector database!")
                
                return True
            else:
                print(f"\n❌ Failed: HTTP {response.status_code}")
                return False
                
    except requests.exceptions.Timeout:
        print(f"\n❌ Request timed out (exceeded 60 minutes)")
        return False
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description='Transcribe a single audio file (no duration limit)',
        epilog="""
Examples:
  # Transcribe a specific file
  python3 transcribe_single.py "/path/to/audio.mp3"
  
  # Use a different model
  python3 transcribe_single.py "/path/to/audio.mp3" --model large
  
  # Transcribe a 2-hour meeting recording
  python3 transcribe_single.py "Recording (9).m4a" --model base
        """
    )
    
    parser.add_argument('file', help='Path to audio file to transcribe')
    parser.add_argument('--model', default='base',
                      choices=['tiny', 'base', 'small', 'medium', 'large'],
                      help='Whisper model to use (default: base)')
    parser.add_argument('--api-url', default='http://localhost:8001',
                      help='Audio service API URL')
    
    args = parser.parse_args()
    
    # Check if service is running
    print("🔍 Checking audio service...")
    try:
        response = requests.get(f"{args.api_url}/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            print(f"✅ Audio service is running (Model: {health['current_model']})")
        else:
            raise Exception("Service not responding")
    except:
        print("❌ Audio service is not running!")
        print("Please start it with:")
        print("  cd services/audio && source audio-env/bin/activate && python transcription_server.py")
        return
    
    # Transcribe the file
    success = transcribe_file(args.file, args.model, args.api_url)
    
    if success:
        print("\n🎯 Next steps:")
        print("1. Search this transcript: http://localhost:8002/search.html")
        print("2. Or transcribe another file with this script")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Single File Transcriber")
        print("-" * 40)
        print("Usage: python3 transcribe_single.py <file_path> [options]")
        print("\nExample:")
        print("  python3 transcribe_single.py 'James Ko.m4a' --model base")
        print("\nFor full help: python3 transcribe_single.py --help")
    else:
        main()