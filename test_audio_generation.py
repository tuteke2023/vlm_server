#!/usr/bin/env python3
"""Generate a test speech audio file using text-to-speech"""

import os

# Use espeak to generate speech (commonly available on Linux)
text = "Hello, this is a test of the audio transcription service. The quick brown fox jumps over the lazy dog."
output_file = "test_speech.wav"

# Generate speech using espeak
cmd = f'espeak -w {output_file} "{text}"'
result = os.system(cmd)

if result == 0:
    print(f"✅ Created {output_file} with speech: '{text[:50]}...'")
else:
    print("❌ Failed to create speech file. Trying alternative method...")
    
    # Alternative: Create a simple audio file with pydub if available
    try:
        from pydub import AudioSegment
        from pydub.generators import Sine
        
        # Create a more complex audio pattern that might be interpreted as speech
        audio = AudioSegment.silent(duration=500)
        
        # Add varying tones to simulate speech patterns
        for freq in [200, 300, 400, 300, 200, 400, 500, 300]:
            tone = Sine(freq).to_audio_segment(duration=200)
            audio += tone
            
        audio.export(output_file, format="wav")
        print(f"✅ Created {output_file} with tones")
    except ImportError:
        print("❌ pydub not available. Using existing test_audio.wav")