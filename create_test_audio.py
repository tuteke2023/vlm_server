#!/usr/bin/env python3
"""Create a test audio file for transcription testing"""

import numpy as np
import wave

# Create a simple tone for testing
sample_rate = 16000
duration = 2  # seconds
frequency = 440  # Hz (A4 note)

# Generate samples
t = np.linspace(0, duration, int(sample_rate * duration))
samples = (0.3 * np.sin(2 * np.pi * frequency * t) * 32767).astype(np.int16)

# Add some silence and variation
silence = np.zeros(int(sample_rate * 0.5), dtype=np.int16)
samples = np.concatenate([silence, samples, silence])

# Save as WAV file
with wave.open('test_audio.wav', 'w') as wav_file:
    wav_file.setnchannels(1)  # Mono
    wav_file.setsampwidth(2)   # 16-bit
    wav_file.setframerate(sample_rate)
    wav_file.writeframes(samples.tobytes())

print("✅ Created test_audio.wav (3 seconds, 440Hz tone)")
print("Note: This is just a tone, not speech, so transcription will be empty or nonsensical")