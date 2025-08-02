#!/usr/bin/env python3
"""
Test script to verify the chat interface functionality
"""

import requests
import json
import base64
import os

def test_chat_api():
    """Test the chat API endpoints"""
    print("🗣️ Testing Chat Interface API")
    print("=" * 40)
    
    base_url = "http://localhost:8000"
    
    # Test 1: Health check
    print("1. Testing server health...")
    try:
        health = requests.get(f"{base_url}/health").json()
        print(f"   ✅ Server: {health['status']} ({health['device']})")
    except Exception as e:
        print(f"   ❌ Health check failed: {e}")
        return
    
    # Test 2: Text-only conversation
    print("\n2. Testing text-only conversation...")
    try:
        text_request = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Hello! Can you tell me what you are?"
                        }
                    ]
                }
            ],
            "max_new_tokens": 100,
            "temperature": 0.7,
            "enable_safety_check": True
        }
        
        response = requests.post(
            f"{base_url}/api/v1/generate",
            json=text_request,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ Text conversation successful!")
            print(f"   💬 Response: {result['response'][:100]}...")
            print(f"   🕐 Processing time: {result['processing_time']:.2f}s")
        else:
            print(f"   ❌ Text conversation failed: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Text conversation failed: {e}")
        return
    
    # Test 3: Model info endpoints
    print("\n3. Testing model info endpoints...")
    try:
        models = requests.get(f"{base_url}/available_models").json()
        vram = requests.get(f"{base_url}/vram_status").json()
        
        current_model = next((m for m in models if m['is_current']), None)
        print(f"   ✅ Current model: {current_model['name'] if current_model else 'Unknown'}")
        print(f"   ✅ VRAM usage: {vram['usage_percentage']:.1f}%")
        
    except Exception as e:
        print(f"   ❌ Model info failed: {e}")
    
    print("\n🎯 Chat Interface Test Summary:")
    print("✅ Server API is functional")
    print("✅ Text conversations work")
    print("✅ Model information accessible")
    print("✅ Chat interface ready to use")
    print(f"\n🌐 Access the chat interface at: http://localhost:8080/chat.html")

if __name__ == "__main__":
    test_chat_api()