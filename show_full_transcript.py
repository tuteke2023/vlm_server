#!/usr/bin/env python3
"""
Display full transcript with speaker labels
"""

import requests
import json

def display_full_transcript(transcript_id):
    """Display the complete transcript with speaker formatting"""
    
    url = f"http://localhost:8001/transcripts/{transcript_id}"
    response = requests.get(url)
    
    if response.status_code != 200:
        print("Could not retrieve transcript")
        return
    
    transcript = response.json()
    
    print("=" * 80)
    print("FULL TRANSCRIPT WITH SPEAKER DETECTION")
    print("=" * 80)
    print(f"File: {transcript.get('audio_filename')}")
    print(f"Processing Version: {transcript.get('processing_version')}")
    print(f"Speakers: {transcript.get('speaker_count', 2)}")
    print(f"Date: {transcript.get('created_at')}")
    print("=" * 80)
    print()
    
    # Get speaker segments
    if transcript.get('speaker_segments'):
        segments = json.loads(transcript['speaker_segments']) if isinstance(transcript['speaker_segments'], str) else transcript['speaker_segments']
        
        print(f"Total segments: {len(segments)}")
        print()
        print("CONVERSATION:")
        print("-" * 80)
        
        current_speaker = None
        speaker_text = []
        
        for segment in segments:
            if segment["speaker"] != current_speaker:
                # Output previous speaker's text
                if current_speaker and speaker_text:
                    text = ' '.join(speaker_text)
                    print(f"\n[{current_speaker}]: {text}")
                    speaker_text = []
                
                current_speaker = segment["speaker"]
            
            speaker_text.append(segment["text"])
        
        # Don't forget last speaker
        if current_speaker and speaker_text:
            text = ' '.join(speaker_text)
            print(f"\n[{current_speaker}]: {text}")
        
        print()
        print("-" * 80)
        print("END OF TRANSCRIPT")
        print("-" * 80)
        
        # Summary statistics
        speaker_stats = {}
        for segment in segments:
            speaker = segment.get('speaker', 'Unknown')
            if speaker not in speaker_stats:
                speaker_stats[speaker] = {'segments': 0, 'words': 0}
            speaker_stats[speaker]['segments'] += 1
            speaker_stats[speaker]['words'] += len(segment.get('text', '').split())
        
        print("\nSUMMARY:")
        for speaker, stats in speaker_stats.items():
            print(f"  {speaker}: {stats['segments']} segments, ~{stats['words']} words")
        
    else:
        # Fall back to plain text if no speaker segments
        print("PLAIN TRANSCRIPT (No speaker detection):")
        print("-" * 80)
        print(transcript.get('content', 'No content available'))
        print("-" * 80)

if __name__ == "__main__":
    # Use the Stanley ATO transcript we created with speaker detection
    transcript_id = "f4418406-6261-476d-8a26-4dd28de8f96a"
    display_full_transcript(transcript_id)