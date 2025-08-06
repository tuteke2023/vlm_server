#!/usr/bin/env python3
"""Create a more complex audio pattern that Whisper might interpret"""

import numpy as np
import wave
import struct

# Create a more speech-like pattern
sample_rate = 16000
duration = 3

# Generate a pattern that sounds more like speech
audio_data = []

# Create syllable-like patterns
for i in range(6):  # 6 "syllables"
    # Rising tone (like speech inflection)
    freq_start = 200 + i * 50
    freq_end = 300 + i * 50
    
    t = np.linspace(0, 0.3, int(sample_rate * 0.3))
    freq_sweep = np.linspace(freq_start, freq_end, len(t))
    
    # Generate frequency sweep
    phase = 0
    for j, f in enumerate(freq_sweep):
        phase += 2 * np.pi * f / sample_rate
        audio_data.append(int(0.3 * 32767 * np.sin(phase)))
    
    # Add short pause
    audio_data.extend([0] * int(sample_rate * 0.1))

# Convert to bytes
audio_bytes = struct.pack('<' + 'h' * len(audio_data), *audio_data)

# Save as WAV
with wave.open('test_speech_pattern.wav', 'wb') as wav_file:
    wav_file.setnchannels(1)
    wav_file.setsampwidth(2)
    wav_file.setframerate(sample_rate)
    wav_file.writeframes(audio_bytes)

print("✅ Created test_speech_pattern.wav")
print("This has speech-like patterns that Whisper might interpret as words or sounds")