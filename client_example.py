#!/usr/bin/env python3
"""
Example client for VLM Server API
Demonstrates various ways to interact with the server
"""

import requests
import base64
import json
from pathlib import Path
from typing import List, Dict, Optional, Union

class VLMClient:
    """Simple client for interacting with VLM Server"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        
    def health_check(self) -> Dict:
        """Check server health"""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
        
    def get_vram_status(self) -> Dict:
        """Get VRAM usage statistics"""
        response = self.session.get(f"{self.base_url}/vram_status")
        response.raise_for_status()
        return response.json()
        
    def clear_vram(self) -> Dict:
        """Manually trigger VRAM clearing"""
        response = self.session.post(f"{self.base_url}/clear_vram")
        response.raise_for_status()
        return response.json()
        
    def generate(
        self,
        messages: List[Dict],
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9
    ) -> Dict:
        """Generate response from VLM"""
        data = {
            "messages": messages,
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
            "top_p": top_p
        }
        
        response = self.session.post(
            f"{self.base_url}/api/v1/generate",
            json=data
        )
        response.raise_for_status()
        return response.json()
        
    def analyze_image_from_url(
        self,
        image_url: str,
        prompt: str,
        **kwargs
    ) -> str:
        """Analyze an image from URL"""
        messages = [{
            "role": "user",
            "content": [
                {"type": "image", "image": image_url},
                {"type": "text", "text": prompt}
            ]
        }]
        
        result = self.generate(messages, **kwargs)
        return result["response"]
        
    def analyze_image_from_file(
        self,
        image_path: Union[str, Path],
        prompt: str,
        **kwargs
    ) -> str:
        """Analyze an image from local file"""
        image_path = Path(image_path)
        
        # Read and encode image
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode()
            
        # Determine MIME type
        mime_type = "image/jpeg"
        if image_path.suffix.lower() == ".png":
            mime_type = "image/png"
            
        messages = [{
            "role": "user",
            "content": [
                {"type": "image", "image": f"data:{mime_type};base64,{image_data}"},
                {"type": "text", "text": prompt}
            ]
        }]
        
        result = self.generate(messages, **kwargs)
        return result["response"]
        
    def chat(
        self,
        message: str,
        conversation_history: Optional[List[Dict]] = None,
        **kwargs
    ) -> str:
        """Send a chat message"""
        messages = conversation_history or []
        messages.append({"role": "user", "content": message})
        
        result = self.generate(messages, **kwargs)
        return result["response"]


def main():
    """Example usage of VLM Client"""
    
    # Initialize client
    client = VLMClient()
    
    print("=== VLM Server Client Example ===\n")
    
    # 1. Health check
    print("1. Checking server health...")
    try:
        health = client.health_check()
        print(f"   Server status: {health['status']}")
        print(f"   Model loaded: {health['model_loaded']}")
        print(f"   Device: {health['device']}\n")
    except Exception as e:
        print(f"   Error: {e}")
        print("   Make sure the server is running!")
        return
        
    # 2. VRAM status
    print("2. Checking VRAM status...")
    vram = client.get_vram_status()
    print(f"   Usage: {vram['usage_percentage']}%")
    print(f"   Allocated: {vram['allocated_gb']} GB / {vram['total_gb']} GB\n")
    
    # 3. Simple text generation
    print("3. Simple text generation...")
    response = client.chat("What is the capital of Japan?")
    print(f"   Response: {response}\n")
    
    # 4. Analyze image from URL
    print("4. Analyzing image from URL...")
    image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/640px-PNG_transparency_demonstration_1.png"
    try:
        response = client.analyze_image_from_url(
            image_url,
            "What's in this image? Describe what you see."
        )
        print(f"   Response: {response}\n")
    except Exception as e:
        print(f"   Error: {e}\n")
        
    # 5. Multi-turn conversation
    print("5. Multi-turn conversation...")
    conversation = []
    
    # First turn
    response1 = client.chat("Hello! Can you help me with math?", conversation)
    conversation.append({"role": "user", "content": "Hello! Can you help me with math?"})
    conversation.append({"role": "assistant", "content": response1})
    print(f"   Assistant: {response1}")
    
    # Second turn
    response2 = client.chat("What's 15% of 240?", conversation)
    print(f"   User: What's 15% of 240?")
    print(f"   Assistant: {response2}\n")
    
    # 6. Analyze local image (if you have one)
    print("6. Analyzing local image...")
    local_image = Path("example_image.jpg")
    if local_image.exists():
        response = client.analyze_image_from_file(
            local_image,
            "Describe this image in detail.",
            max_new_tokens=1024
        )
        print(f"   Response: {response}\n")
    else:
        print("   No local image found (example_image.jpg)\n")
        
    # 7. Check token usage
    print("7. Checking token usage...")
    result = client.generate([{
        "role": "user",
        "content": "Count from 1 to 10"
    }])
    print(f"   Response: {result['response']}")
    print(f"   Input tokens: {result['usage']['input_tokens']}")
    print(f"   Output tokens: {result['usage']['output_tokens']}")
    print(f"   Processing time: {result['processing_time']:.2f}s\n")
    
    # 8. Clear VRAM
    print("8. Clearing VRAM...")
    clear_result = client.clear_vram()
    print(f"   Status: {clear_result['status']}")
    print(f"   VRAM after clearing: {clear_result['vram_status']['usage_percentage']}%")


if __name__ == "__main__":
    main()