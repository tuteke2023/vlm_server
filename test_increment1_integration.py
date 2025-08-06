"""
Integration test for Increment 1: Test UnifiedLLMProvider with running VLM server
"""

import asyncio
import aiohttp
import json
import sys
import base64
from pathlib import Path

# Server configuration
SERVER_URL = "http://localhost:8000"
TEST_IMAGE_PATH = "tests/BankStatementChequing.png"


async def test_server_health():
    """Check if server is running and healthy"""
    print("=== Testing Server Health ===")
    
    async with aiohttp.ClientSession() as session:
        try:
            # Check health endpoint
            async with session.get(f"{SERVER_URL}/health") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"✓ Server is healthy: {data}")
                    return True
                else:
                    print(f"✗ Server health check failed: {resp.status}")
                    return False
        except Exception as e:
            print(f"✗ Cannot connect to server: {e}")
            print("\nPlease ensure the VLM server is running:")
            print("  cd services/vlm")
            print("  python vlm_server.py")
            return False


async def test_unified_endpoint():
    """Test the new unified provider endpoint"""
    print("\n=== Testing Unified Provider Endpoint ===")
    
    async with aiohttp.ClientSession() as session:
        # Test 1: Simple text generation
        print("\n1. Testing simple text generation...")
        request_data = {
            "messages": [
                {"role": "user", "content": "What is 2+2?"}
            ],
            "temperature": 0.1,
            "max_tokens": 100
        }
        
        try:
            async with session.post(
                f"{SERVER_URL}/api/v1/generate_unified",
                json=request_data
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"✓ Response: {data['response'][:100]}...")
                    print(f"✓ Usage: {data['usage']}")
                    print(f"✓ Metadata: {data['metadata']}")
                else:
                    error = await resp.text()
                    print(f"✗ Request failed ({resp.status}): {error}")
                    return False
        except Exception as e:
            print(f"✗ Error: {e}")
            return False
        
        # Test 2: Multimodal generation (if image exists)
        if Path(TEST_IMAGE_PATH).exists():
            print("\n2. Testing multimodal generation with image...")
            
            # Load and encode image
            with open(TEST_IMAGE_PATH, "rb") as f:
                image_data = base64.b64encode(f.read()).decode()
            
            request_data = {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "What's in this image?"},
                            {"type": "image", "image": image_data}
                        ]
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 500
            }
            
            try:
                async with session.post(
                    f"{SERVER_URL}/api/v1/generate_unified",
                    json=request_data
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        print(f"✓ Response: {data['response'][:200]}...")
                        print(f"✓ Processing time: {data['processing_time']:.2f}s")
                    else:
                        error = await resp.text()
                        print(f"✗ Request failed ({resp.status}): {error}")
            except Exception as e:
                print(f"✗ Error: {e}")
        else:
            print("\n2. Skipping multimodal test (image not found)")
    
    return True


async def test_compatibility():
    """Test that existing endpoints still work"""
    print("\n=== Testing Backward Compatibility ===")
    
    async with aiohttp.ClientSession() as session:
        # Test original generate endpoint
        request_data = {
            "messages": [
                {"role": "user", "content": "Hello, how are you?"}
            ],
            "temperature": 0.7,
            "max_new_tokens": 100
        }
        
        try:
            async with session.post(
                f"{SERVER_URL}/api/v1/generate",
                json=request_data
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print("✓ Original /generate endpoint still works")
                    print(f"  Response: {data['response'][:100]}...")
                else:
                    print(f"✗ Original endpoint failed: {resp.status}")
                    return False
        except Exception as e:
            print(f"✗ Error testing original endpoint: {e}")
            return False
    
    return True


async def test_performance_comparison():
    """Compare performance between original and unified endpoints"""
    print("\n=== Performance Comparison ===")
    
    import time
    
    async with aiohttp.ClientSession() as session:
        test_message = {
            "messages": [{"role": "user", "content": "Explain quantum computing in one sentence."}],
            "temperature": 0.7
        }
        
        # Test original endpoint
        start = time.time()
        test_message["max_new_tokens"] = 100
        async with session.post(f"{SERVER_URL}/api/v1/generate", json=test_message) as resp:
            if resp.status == 200:
                data = await resp.json()
                original_time = time.time() - start
                print(f"Original endpoint: {original_time:.2f}s")
        
        # Test unified endpoint
        start = time.time()
        test_message["max_tokens"] = 100
        del test_message["max_new_tokens"]
        async with session.post(f"{SERVER_URL}/api/v1/generate_unified", json=test_message) as resp:
            if resp.status == 200:
                data = await resp.json()
                unified_time = time.time() - start
                print(f"Unified endpoint: {unified_time:.2f}s")
        
        # Compare
        diff = abs(unified_time - original_time)
        if diff < 0.5:  # Less than 0.5s difference
            print(f"✓ Performance is comparable (difference: {diff:.2f}s)")
        else:
            print(f"⚠ Performance difference: {diff:.2f}s")
    
    return True


async def main():
    """Run all integration tests"""
    print("Testing Increment 1: UnifiedLLMProvider Integration\n")
    
    # Check server is running
    if not await test_server_health():
        sys.exit(1)
    
    # Run tests
    all_passed = True
    
    if not await test_unified_endpoint():
        all_passed = False
    
    if not await test_compatibility():
        all_passed = False
    
    if not await test_performance_comparison():
        all_passed = False
    
    # Summary
    print("\n" + "="*50)
    if all_passed:
        print("🎉 All integration tests passed!")
        print("✓ UnifiedLLMProvider is working correctly with VLM server")
        print("✓ Backward compatibility maintained")
        print("✓ Ready to proceed to Increment 2")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    print("="*50)


if __name__ == "__main__":
    asyncio.run(main())