#!/usr/bin/env python3
"""Test Audio-to-Chat Integration"""

import asyncio
import aiohttp
import json
import os
import wave
import numpy as np
from pathlib import Path

# Service URLs
AUDIO_API_URL = "http://localhost:8001"
AUDIO_WEB_URL = "http://localhost:8002"
VLM_API_URL = "http://localhost:8000"
VLM_WEB_URL = "http://localhost:8080"

def create_test_audio(filename="test_audio_integration.wav", text="This is a test of the audio to chat integration feature"):
    """Create a simple test audio file"""
    print(f"Creating test audio file: {filename}")
    
    # Generate a simple sine wave (placeholder for actual speech)
    duration = 2  # seconds
    sample_rate = 44100
    frequency = 440  # A4 note
    
    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_data = np.sin(2 * np.pi * frequency * t)
    
    # Scale to 16-bit integer
    audio_data = (audio_data * 32767).astype(np.int16)
    
    # Write WAV file
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())
    
    print(f"Test audio file created: {filename}")
    return filename

async def test_audio_transcription(audio_file):
    """Test audio transcription service"""
    print("\n1. Testing Audio Transcription Service...")
    
    async with aiohttp.ClientSession() as session:
        # Check health
        try:
            async with session.get(f"{AUDIO_API_URL}/health") as resp:
                health = await resp.json()
                print(f"   Audio service status: {health['status']}")
                print(f"   Model loaded: {health['model_loaded']}")
                print(f"   Current model: {health['current_model']}")
        except Exception as e:
            print(f"   ❌ Audio service not running: {e}")
            return None
        
        # Transcribe audio
        with open(audio_file, 'rb') as f:
            data = aiohttp.FormData()
            data.add_field('file', f, filename=audio_file, content_type='audio/wav')
            data.add_field('model', 'base')
            data.add_field('save_transcript', 'true')
            
            try:
                async with session.post(f"{AUDIO_API_URL}/transcribe", data=data) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        print(f"   ✅ Transcription successful!")
                        print(f"   Transcript ID: {result.get('transcript_id')}")
                        print(f"   Text: {result['transcription']['text']}")
                        return result.get('transcript_id')
                    else:
                        print(f"   ❌ Transcription failed: {resp.status}")
                        return None
            except Exception as e:
                print(f"   ❌ Error transcribing: {e}")
                return None

async def test_transcript_to_chat(transcript_id):
    """Test sending transcript to chat"""
    print("\n2. Testing Transcript-to-Chat API...")
    
    if not transcript_id:
        print("   ❌ No transcript ID available")
        return None
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(f"{AUDIO_API_URL}/transcripts/{transcript_id}/to-chat") as resp:
                if resp.status == 200:
                    chat_context = await resp.json()
                    print(f"   ✅ Chat context created!")
                    print(f"   Type: {chat_context['type']}")
                    print(f"   Content length: {len(chat_context['content'])} chars")
                    print(f"   Metadata: {json.dumps(chat_context['metadata'], indent=2)}")
                    return chat_context
                else:
                    print(f"   ❌ Failed to create chat context: {resp.status}")
                    return None
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return None

async def test_chat_qa(chat_context):
    """Test Q&A with the transcript in chat"""
    print("\n3. Testing Chat Q&A with Transcript...")
    
    if not chat_context:
        print("   ❌ No chat context available")
        return
    
    async with aiohttp.ClientSession() as session:
        # Check VLM health
        try:
            async with session.get(f"{VLM_API_URL}/health") as resp:
                health = await resp.json()
                print(f"   VLM service status: {health['status']}")
        except Exception as e:
            print(f"   ❌ VLM service not running: {e}")
            return
        
        # Create a chat message with transcript context
        messages = [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": f"Audio transcript from {chat_context['metadata']['filename']}: {chat_context['content']}"
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Can you summarize the main points from this transcript?"
                    }
                ]
            }
        ]
        
        try:
            async with session.post(
                f"{VLM_API_URL}/api/v1/generate",
                json={
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 500
                }
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    print(f"   ✅ Chat Q&A successful!")
                    print(f"   Response: {result['response'][:200]}...")
                else:
                    print(f"   ❌ Chat Q&A failed: {resp.status}")
        except Exception as e:
            print(f"   ❌ Error in chat Q&A: {e}")

async def test_list_transcripts():
    """Test listing saved transcripts"""
    print("\n4. Testing List Transcripts...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{AUDIO_API_URL}/transcripts") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    transcripts = data.get('transcripts', [])
                    print(f"   ✅ Found {len(transcripts)} transcript(s)")
                    for t in transcripts[:3]:  # Show first 3
                        print(f"      - ID: {t['id']}")
                        print(f"        File: {t.get('audio_filename', 'Unknown')}")
                        print(f"        Preview: {t.get('preview', '')[:50]}...")
                else:
                    print(f"   ❌ Failed to list transcripts: {resp.status}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

async def main():
    """Run all integration tests"""
    print("=" * 60)
    print("AUDIO-TO-CHAT INTEGRATION TEST")
    print("=" * 60)
    
    # Create test audio file
    audio_file = create_test_audio()
    
    try:
        # Test transcription
        transcript_id = await test_audio_transcription(audio_file)
        
        # Test transcript to chat
        chat_context = await test_transcript_to_chat(transcript_id)
        
        # Test chat Q&A
        await test_chat_qa(chat_context)
        
        # Test listing transcripts
        await test_list_transcripts()
        
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        if transcript_id and chat_context:
            print("✅ Audio-to-Chat integration is working!")
            print("\nTo test the full flow manually:")
            print("1. Open http://localhost:8002 (Audio Transcription)")
            print("2. Upload an audio file and transcribe it")
            print("3. Click 'Send to Chat' button")
            print("4. The chat interface will open with the transcript loaded")
            print("5. Ask questions about the transcript")
        else:
            print("❌ Some tests failed. Check the services are running:")
            print("   - Audio service: cd services/audio && python transcription_server.py")
            print("   - VLM service: cd services/vlm && python vlm_server.py")
            
    finally:
        # Cleanup
        if os.path.exists(audio_file):
            os.remove(audio_file)
            print(f"\nCleaned up test file: {audio_file}")

if __name__ == "__main__":
    asyncio.run(main())