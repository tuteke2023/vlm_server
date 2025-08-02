#!/usr/bin/env python3
"""
Quick test script to generate a simple test image and test GPU-only processing
"""

import requests
import base64
import time
from PIL import Image, ImageDraw, ImageFont

def create_simple_test_image():
    """Create a simple test image with text"""
    width, height = 400, 200
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
    except:
        font = ImageFont.load_default()
    
    # Add some text
    draw.text((50, 50), "BANK STATEMENT", fill='black', font=font)
    draw.text((50, 80), "Date: 2024-01-15", fill='black', font=font)
    draw.text((50, 110), "Amount: $1,234.56", fill='black', font=font)
    draw.text((50, 140), "Description: Grocery Store", fill='black', font=font)
    
    # Save and return base64
    img.save("simple_test.png")
    
    with open("simple_test.png", "rb") as f:
        return base64.b64encode(f.read()).decode()

def test_image_processing():
    """Test image processing speed with GPU optimization"""
    print("🧪 Testing GPU-Optimized Image Processing")
    print("="*50)
    
    # Create test image
    print("📷 Creating test image...")
    image_b64 = create_simple_test_image()
    
    # Test with simple query
    prompt = "Extract the date, amount, and description from this bank statement entry."
    
    print(f"🔄 Processing image with prompt: '{prompt}'")
    start_time = time.time()
    
    try:
        response = requests.post('http://localhost:8000/api/v1/generate', json={
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "image", "image": f"data:image/png;base64,{image_b64}"},
                    {"type": "text", "text": prompt}
                ]
            }],
            "max_new_tokens": 100
        }, timeout=60)
        
        total_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            print("✅ SUCCESS!")
            print(f"📊 Total Time: {total_time:.2f}s")
            print(f"🔧 Server Processing Time: {result['processing_time']:.2f}s")
            print(f"🎯 Tokens: {result['usage']['total_tokens']}")
            print(f"⚡ Speed: {result['usage']['output_tokens'] / result['processing_time']:.1f} tokens/sec")
            print(f"💬 Response: {result['response']}")
            
            # Check VRAM after processing
            vram_response = requests.get('http://localhost:8000/vram_status')
            if vram_response.status_code == 200:
                vram = vram_response.json()
                print(f"💾 VRAM Usage: {vram['usage_percentage']:.1f}% ({vram['allocated_gb']:.1f}GB/{vram['total_gb']:.1f}GB)")
        else:
            print(f"❌ FAILED: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    test_image_processing()