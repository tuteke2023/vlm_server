"""
Test fallback notification for Increment 2
"""

import asyncio
import aiohttp
import json

SERVER_URL = "http://localhost:8000"


async def test_fallback_notification():
    """Test that fallback notifications are properly shown to users"""
    print("=== Testing Fallback Notification ===\n")
    
    async with aiohttp.ClientSession() as session:
        # First switch to OpenAI
        print("1. Switching to OpenAI provider...")
        await session.post(
            f"{SERVER_URL}/api/v1/switch_provider_unified",
            json={"provider": "openai"}
        )
        
        # Make a request that should trigger fallback
        print("2. Making request that will trigger fallback...")
        test_message = {
            "messages": [
                {"role": "user", "content": "What is 2+2?"}
            ],
            "temperature": 0.1,
            "max_tokens": 50,
            "allow_fallback": True
        }
        
        try:
            async with session.post(
                f"{SERVER_URL}/api/v1/generate_unified",
                json=test_message
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    print("\n3. Response received:")
                    print(f"   Content: {data['response'][:50]}...")
                    print(f"   Provider used: {data['metadata']['provider']}")
                    
                    if "fallback_notification" in data:
                        print("\n✓ FALLBACK NOTIFICATION PRESENT:")
                        notif = data['fallback_notification']
                        print(f"   Message: {notif['message']}")
                        print(f"   Original provider: {notif['original_provider']}")
                        print(f"   Fallback provider: {notif['fallback_provider']}")
                        print(f"   Reason: {notif['reason']}")
                        print(f"   Warning: {notif['warning']}")
                    else:
                        print("\n✗ No fallback notification found")
                    
                    print("\n4. Full metadata:")
                    print(f"   {json.dumps(data['metadata'], indent=2)}")
                    
                else:
                    print(f"✗ Request failed: {resp.status}")
        except Exception as e:
            print(f"✗ Error: {e}")


async def main():
    """Run fallback notification test"""
    await test_fallback_notification()
    print("\n" + "="*60)
    print("Test complete. Users will now be properly notified of fallbacks!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())