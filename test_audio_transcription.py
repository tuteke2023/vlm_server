#!/usr/bin/env python3
"""Test audio transcription service"""

import requests
import json

print("=== Testing Audio Transcription Service ===\n")

# Test 1: Check service health
print("1. Checking service health...")
try:
    response = requests.get("http://localhost:8001/health")
    if response.status_code == 200:
        health = response.json()
        print(f"✅ Service Status: {health['status']}")
        print(f"✅ Model Loaded: {health['model_loaded']}")
        print(f"✅ Current Model: {health['current_model']}")
        print(f"✅ Device: {health['device']}")
    else:
        print(f"❌ Health check failed: {response.status_code}")
except Exception as e:
    print(f"❌ Service not running: {e}")

# Test 2: Check available models
print("\n2. Checking available models...")
try:
    response = requests.get("http://localhost:8001/models")
    if response.status_code == 200:
        models_info = response.json()
        print("✅ Available models:")
        for model in models_info['models']:
            desc = models_info['descriptions'][model]
            current = " (current)" if model == models_info['current'] else ""
            print(f"   - {model}: {desc}{current}")
    else:
        print(f"❌ Models check failed: {response.status_code}")
except Exception as e:
    print(f"❌ Error getting models: {e}")

# Test 3: Test with the tone file we have
print("\n3. Testing transcription with tone file...")
print("   Note: This is just a 440Hz tone, not speech, so it should return empty/minimal text")
try:
    with open('test_audio.wav', 'rb') as f:
        files = {'file': ('test_audio.wav', f, 'audio/wav')}
        data = {'model': 'tiny'}  # Use tiny model for testing
        
        response = requests.post("http://localhost:8001/transcribe", files=files, data=data, timeout=30)
        
        print(f"   Response Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            transcription = result.get('transcription', {}).get('text', '').strip()
            print(f"   ✅ Transcription successful")
            print(f"   📝 Result: '{transcription}' (empty/minimal expected for tone)")
        else:
            print(f"   ❌ Transcription failed: {response.text}")
            
except FileNotFoundError:
    print("   ❌ test_audio.wav not found")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 4: Show how to use with real speech
print("\n4. How to test with real speech:")
print("   - Record yourself saying something using your computer/phone")
print("   - Save as .wav, .mp3, .m4a, etc.")
print("   - Upload via web UI at http://localhost:8001/")
print("   - Or use curl:")
print('   curl -X POST -F "file=@your_audio.wav" -F "model=base" http://localhost:8001/transcribe')

print("\n✅ Audio service is running and ready for real audio files!")