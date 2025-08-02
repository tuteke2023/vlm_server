#!/usr/bin/env python3
"""
Debug script to identify the "Failed to fetch" issue
"""

import requests
import json
import time

def debug_server_issue():
    """Debug the server connectivity and API issues"""
    base_url = "http://localhost:8000"
    
    print("🔍 Debugging 'Failed to fetch' Issue")
    print("=" * 50)
    
    # Test 1: Basic connectivity
    print("1. Testing basic server connectivity...")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"✅ Server responded: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Available endpoints: {list(data.get('endpoints', {}).keys())}")
        else:
            print(f"❌ Unexpected status: {response.text}")
    except requests.exceptions.ConnectionError:
        print("❌ Connection refused - server not running")
        return
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return
    
    # Test 2: Health check
    print("\n2. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"✅ Health check: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Status: {data}")
        else:
            print(f"❌ Health check failed: {response.text}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    # Test 3: Check if new endpoints exist
    print("\n3. Testing new quantization endpoints...")
    endpoints_to_test = [
        "/vram_status",
        "/vram_prediction", 
        "/quantization_options",
        "/reload_model"
    ]
    
    for endpoint in endpoints_to_test:
        try:
            if endpoint == "/reload_model":
                # POST endpoint
                response = requests.post(f"{base_url}{endpoint}", 
                                       json={"quantization": None}, 
                                       timeout=5)
            else:
                # GET endpoint
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
            
            if response.status_code in [200, 404, 422]:  # 422 is validation error, means endpoint exists
                print(f"✅ {endpoint}: {response.status_code}")
            else:
                print(f"❌ {endpoint}: {response.status_code} - {response.text[:100]}")
        except Exception as e:
            print(f"❌ {endpoint}: Error - {e}")
    
    # Test 4: Test document processing request
    print("\n4. Testing document processing request format...")
    try:
        # Simple test request
        test_request = {
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "text", "text": "Hello, can you process this?"}
                ]
            }],
            "max_new_tokens": 50,
            "quantization": "8bit",
            "enable_safety_check": True
        }
        
        response = requests.post(f"{base_url}/api/v1/generate", 
                               json=test_request, 
                               timeout=10)
        print(f"✅ Generate endpoint: {response.status_code}")
        if response.status_code != 200:
            print(f"   Response: {response.text[:200]}")
        
    except Exception as e:
        print(f"❌ Generate endpoint error: {e}")
    
    print("\n🎯 Diagnosis:")
    print("The 'Failed to fetch' error suggests:")
    print("1. Server may not be running due to CUDA compatibility issues")
    print("2. New API endpoints may not be available on running server")
    print("3. CORS issues with cross-origin requests")
    print("4. Request format incompatibility")

if __name__ == "__main__":
    debug_server_issue()