#!/usr/bin/env python3
"""
Transcribe a single audio file with optional speaker detection and corrections
"""

import requests
import json
import sys
from pathlib import Path

def transcribe_file(file_path, enable_speakers=None):
    """
    Transcribe an audio file with optional enhancements
    
    Args:
        file_path: Path to the audio file
        enable_speakers: True/False/None (None = ask user)
    """
    
    # Convert Windows path if needed
    if file_path.startswith("C:\\"):
        # Convert to WSL path
        file_path = file_path.replace("C:\\", "/mnt/c/")
        file_path = file_path.replace("\\", "/")
    
    print(f"Transcribing: {file_path}")
    
    # Check if file exists
    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        return None
    
    # Get file size
    file_size_mb = Path(file_path).stat().st_size / (1024 * 1024)
    print(f"File size: {file_size_mb:.1f} MB")
    
    # Ask user about speaker detection if not specified
    if enable_speakers is None:
        print("\n" + "=" * 60)
        print("SPEAKER DETECTION OPTIONS:")
        print("-" * 60)
        print("Speaker detection can identify different speakers in the audio.")
        print("This is useful for:")
        print("  • Conversations, interviews, meetings")
        print("  • Multiple people talking")
        print("  • Tracking who said what")
        print("\nNOT needed for:")
        print("  • Single speaker presentations")
        print("  • Music or non-speech audio")
        print("  • When you just need the text")
        print("-" * 60)
        
        while True:
            choice = input("\nEnable speaker detection? (y/n) [default: y]: ").strip().lower()
            if choice in ['', 'y', 'yes']:
                enable_speakers = True
                break
            elif choice in ['n', 'no']:
                enable_speakers = False
                break
            else:
                print("Please enter 'y' for yes or 'n' for no")
    
    url = "http://localhost:8001/transcribe"
    
    # Open and send file
    with open(file_path, 'rb') as f:
        files = {'file': (Path(file_path).name, f, 'audio/mpeg')}
        data = {
            'enable_speaker_detection': 'true' if enable_speakers else 'false',
            'enable_corrections': 'true',
            'domain': 'general',  # Use general domain for unknown content
            'save_transcript': 'true'
        }
        
        print("\nSending to transcription server...")
        print(f"- Speaker detection: {'ENABLED' if enable_speakers else 'DISABLED'}")
        print("- Corrections: ENABLED")
        print("- Domain: general")
        print("\nThis may take a few minutes...")
        
        response = requests.post(url, files=files, data=data, timeout=600)
    
    if response.status_code == 200:
        result = response.json()
        
        print("\n✅ Transcription completed!")
        
        # Extract transcript info
        transcript_id = result.get('transcript_id')
        processing_version = result.get('processing_version')
        transcription = result.get('transcription', {})
        
        print(f"Transcript ID: {transcript_id}")
        print(f"Processing version: {processing_version}")
        
        # Check for speaker detection
        if 'speaker_segments' in transcription:
            speaker_count = transcription.get('speaker_count', 0)
            segments = transcription.get('speaker_segments', [])
            print(f"Speakers detected: {speaker_count}")
            print(f"Total segments: {len(segments)}")
        else:
            print("Speaker detection: Not available")
        
        # Save transcript to file
        output_file = Path(file_path).stem + "_transcript.txt"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Transcript of: {Path(file_path).name}\n")
            f.write("=" * 80 + "\n\n")
            
            if 'speaker_segments' in transcription:
                # Write with speaker labels
                current_speaker = None
                speaker_text = []
                
                for segment in transcription['speaker_segments']:
                    if segment['speaker'] != current_speaker:
                        if current_speaker and speaker_text:
                            f.write(f"\n[{current_speaker}]: {' '.join(speaker_text)}\n")
                            speaker_text = []
                        current_speaker = segment['speaker']
                    speaker_text.append(segment['text'])
                
                # Last speaker
                if current_speaker and speaker_text:
                    f.write(f"\n[{current_speaker}]: {' '.join(speaker_text)}\n")
            else:
                # Write plain transcript
                f.write(transcription.get('text', ''))
        
        print(f"\n📝 Transcript saved to: {output_file}")
        
        # Show preview
        print("\n" + "=" * 80)
        print("TRANSCRIPT PREVIEW (first 500 chars):")
        print("-" * 80)
        
        text = transcription.get('text', '')[:500]
        print(text + "...")
        
        return result
        
    else:
        print(f"❌ Transcription failed: {response.status_code}")
        print(response.text)
        return None

if __name__ == "__main__":
    # File to transcribe
    file_path = r"C:\Users\tekee\Downloads\639831872-ERLesson3mp4 (Source).mp3"
    
    result = transcribe_file(file_path)
    
    if result:
        print("\n✅ Transcription complete!")
        print("Check the generated transcript file for full content.")