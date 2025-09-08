#!/usr/bin/env python3
"""
Test script for speaker detection in transcription
"""

import requests
import json
from pathlib import Path
import sys

def test_transcription_with_speakers(audio_file_path):
    """Test transcription with speaker detection"""
    
    # Check if file exists
    if not Path(audio_file_path).exists():
        print(f"❌ File not found: {audio_file_path}")
        return
    
    url = "http://localhost:8001/transcribe"
    
    print(f"Testing speaker detection with: {audio_file_path}")
    print("=" * 60)
    
    # Prepare the file
    with open(audio_file_path, 'rb') as f:
        files = {'file': (Path(audio_file_path).name, f, 'audio/mpeg')}
        
        # Test with speaker detection ENABLED
        print("\n1. Testing WITH speaker detection...")
        data = {
            'enable_speaker_detection': 'true',
            'save_transcript': 'true'
        }
        
        response = requests.post(url, files=files, data=data)
        
    if response.status_code == 200:
        result = response.json()
        
        print(f"✅ Transcription successful!")
        print(f"Processing version: {result.get('processing_version', 'unknown')}")
        print(f"Transcript ID: {result.get('transcript_id')}")
        
        transcription = result.get('transcription', {})
        
        # Check if speaker detection worked
        if 'speaker_segments' in transcription:
            speaker_count = transcription.get('speaker_count', 0)
            print(f"\n✅ Speaker detection successful!")
            print(f"Detected {speaker_count} speakers")
            
            # Show first few speaker segments
            print("\nFirst 5 speaker segments:")
            print("-" * 40)
            for i, segment in enumerate(transcription['speaker_segments'][:5]):
                speaker = segment.get('speaker', 'Unknown')
                text = segment.get('text', '')[:100]
                print(f"[{speaker}]: {text}...")
                if i >= 4:
                    break
                    
        else:
            print("\n⚠️  No speaker segments found - using version 1.0")
            
        # Show regular transcript preview
        print("\nRegular transcript preview:")
        print("-" * 40)
        text = transcription.get('text', '')[:500]
        print(text + "...")
        
        return result.get('transcript_id')
        
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return None

def get_transcript_details(transcript_id):
    """Get full transcript details including speaker segments"""
    
    url = f"http://localhost:8001/transcripts/{transcript_id}"
    response = requests.get(url)
    
    if response.status_code == 200:
        transcript = response.json()
        
        print("\n" + "=" * 60)
        print("TRANSCRIPT DETAILS FROM DATABASE")
        print("=" * 60)
        
        print(f"ID: {transcript.get('id')}")
        print(f"File: {transcript.get('audio_filename')}")
        print(f"Processing Version: {transcript.get('processing_version', '1.0')}")
        print(f"Speaker Count: {transcript.get('speaker_count', 'N/A')}")
        print(f"Created: {transcript.get('created_at')}")
        
        if transcript.get('speaker_segments'):
            segments = json.loads(transcript['speaker_segments']) if isinstance(transcript['speaker_segments'], str) else transcript['speaker_segments']
            
            print(f"\n✅ Speaker segments found: {len(segments)} segments")
            
            # Group by speaker
            speaker_texts = {}
            for segment in segments:
                speaker = segment.get('speaker', 'Unknown')
                if speaker not in speaker_texts:
                    speaker_texts[speaker] = []
                speaker_texts[speaker].append(segment.get('text', ''))
            
            print("\nSpeaker breakdown:")
            for speaker, texts in speaker_texts.items():
                word_count = sum(len(text.split()) for text in texts)
                print(f"  {speaker}: {len(texts)} segments, ~{word_count} words")
                
        else:
            print("\n⚠️  No speaker segments in database (Version 1.0 transcript)")
            
        return transcript
    else:
        print(f"❌ Could not retrieve transcript: {response.status_code}")
        return None

if __name__ == "__main__":
    # List available audio files
    audio_dir = Path("/mnt/c/Users/tekee/Documents/Sound Recordings")
    
    if audio_dir.exists():
        audio_files = list(audio_dir.glob("*.m4a")) + list(audio_dir.glob("*.mp3"))
        
        # Find Stanley ATO file as it's a good test case
        stanley_file = None
        for f in audio_files:
            if "Stanley" in f.name or "ATO" in f.name:
                stanley_file = f
                break
        
        if stanley_file:
            print(f"Found test file: {stanley_file.name}")
            transcript_id = test_transcription_with_speakers(str(stanley_file))
            
            if transcript_id:
                # Get full details from database
                get_transcript_details(transcript_id)
        else:
            # Use first available file
            if audio_files:
                test_file = audio_files[0]
                print(f"Using test file: {test_file.name}")
                transcript_id = test_transcription_with_speakers(str(test_file))
                
                if transcript_id:
                    get_transcript_details(transcript_id)
            else:
                print("❌ No audio files found for testing")
    else:
        print(f"❌ Audio directory not found: {audio_dir}")