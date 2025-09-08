#!/usr/bin/env python3
"""
Show speaker detection example from Stanley ATO transcript
"""

import requests
import json
from datetime import datetime

def get_latest_stanley_transcript():
    """Get the most recent Stanley ATO transcript with speakers"""
    
    # Search for Stanley transcripts
    url = "http://localhost:8001/transcripts"
    response = requests.get(url, params={"limit": 100})
    
    if response.status_code == 200:
        transcripts = response.json().get("transcripts", [])
        
        # Find Stanley transcript with speaker detection (version 2.0)
        for transcript in transcripts:
            if transcript.get("audio_filename") and "Stanley" in transcript["audio_filename"]:
                if transcript.get("processing_version") == "2.0":
                    return transcript["id"]
    
    return None

def format_speaker_conversation(transcript_id):
    """Format transcript with clear speaker labels"""
    
    url = f"http://localhost:8001/transcripts/{transcript_id}"
    response = requests.get(url)
    
    if response.status_code != 200:
        print("Could not retrieve transcript")
        return
    
    transcript = response.json()
    
    print("=" * 80)
    print("SPEAKER DETECTION EXAMPLE: Stanley ATO Objection Call")
    print("=" * 80)
    print(f"File: {transcript.get('audio_filename')}")
    print(f"Processing Version: {transcript.get('processing_version')}")
    print(f"Speakers Detected: {transcript.get('speaker_count', 2)}")
    print(f"Transcribed: {transcript.get('created_at')}")
    print("=" * 80)
    print()
    
    # Get speaker segments
    if transcript.get('speaker_segments'):
        segments = json.loads(transcript['speaker_segments']) if isinstance(transcript['speaker_segments'], str) else transcript['speaker_segments']
        
        # Show first portion of conversation with clear speaker labels
        print("CONVERSATION WITH SPEAKER LABELS:")
        print("-" * 80)
        
        current_speaker = None
        speaker_text = []
        conversation_lines = []
        
        for i, segment in enumerate(segments[:50]):  # Show first 50 segments
            if segment["speaker"] != current_speaker:
                # Output previous speaker's text
                if current_speaker and speaker_text:
                    text = ' '.join(speaker_text)
                    conversation_lines.append(f"\n[{current_speaker}]: {text}")
                    speaker_text = []
                
                current_speaker = segment["speaker"]
            
            speaker_text.append(segment["text"])
        
        # Don't forget last speaker
        if current_speaker and speaker_text:
            text = ' '.join(speaker_text)
            conversation_lines.append(f"\n[{current_speaker}]: {text}")
        
        # Print formatted conversation
        for line in conversation_lines:
            print(line)
        
        print("\n... (showing first 50 segments of 594 total)")
        print()
        print("-" * 80)
        print("KEY TOPICS IDENTIFIED FROM CONVERSATION:")
        print("-" * 80)
        
        # Analyze key topics
        full_text = transcript.get('content', '').lower()
        
        topics = []
        if 'objection' in full_text:
            topics.append("✓ Tax objection filing")
        if 'stanley' in full_text:
            topics.append("✓ Client: Stanley Ong")
        if 'payment plan' in full_text or 'payment' in full_text:
            topics.append("✓ Payment arrangements")
        if 'deadline' in full_text or 'due date' in full_text:
            topics.append("✓ Important deadlines")
        if 'agent number' in full_text:
            topics.append("✓ Agent verification")
        
        for topic in topics:
            print(topic)
        
        print()
        print("=" * 80)
        print("SPEAKER STATISTICS:")
        print("=" * 80)
        
        # Calculate speaker statistics
        speaker_stats = {}
        for segment in segments:
            speaker = segment.get('speaker', 'Unknown')
            if speaker not in speaker_stats:
                speaker_stats[speaker] = {
                    'segments': 0,
                    'words': 0,
                    'sample_texts': []
                }
            
            speaker_stats[speaker]['segments'] += 1
            speaker_stats[speaker]['words'] += len(segment.get('text', '').split())
            
            # Collect sample texts
            if len(speaker_stats[speaker]['sample_texts']) < 3:
                text = segment.get('text', '').strip()
                if len(text) > 20:  # Only meaningful segments
                    speaker_stats[speaker]['sample_texts'].append(text[:100])
        
        for speaker, stats in speaker_stats.items():
            print(f"\n{speaker}:")
            print(f"  - Segments: {stats['segments']}")
            print(f"  - Words spoken: ~{stats['words']}")
            print(f"  - Speaking share: {stats['segments'] * 100 / len(segments):.1f}%")
            
            if stats['sample_texts']:
                print(f"  - Sample phrases:")
                for sample in stats['sample_texts']:
                    print(f"    • \"{sample}...\"")
        
        print()
        print("=" * 80)
        print("BENEFITS OF SPEAKER DETECTION:")
        print("=" * 80)
        print("1. Clear attribution: Know exactly who said what")
        print("2. Action tracking: ATO's requests vs your responses")
        print("3. Compliance record: Important for tax matters")
        print("4. Better summaries: AI can follow the conversation flow")
        print("5. Searchable: Find all ATO statements or your commitments")
        
    else:
        print("This transcript doesn't have speaker detection (Version 1.0)")
        print("Only new transcripts get speaker detection automatically")

if __name__ == "__main__":
    # Use the transcript we just created in testing
    transcript_id = "f4418406-6261-476d-8a26-4dd28de8f96a"
    format_speaker_conversation(transcript_id)