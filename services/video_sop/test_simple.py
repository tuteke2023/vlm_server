#!/usr/bin/env python3
"""
Simple test to verify the Video-to-SOP system is working
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path

def test_basic_setup():
    """Test basic setup without requiring a video file"""
    
    print("\n" + "="*60)
    print("Video-to-SOP System Test")
    print("="*60 + "\n")
    
    # Check imports
    print("1. Checking Python modules...")
    try:
        from video_processor import VideoProcessor
        print("   ✓ VideoProcessor module loaded")
    except ImportError as e:
        print(f"   ✗ VideoProcessor import failed: {e}")
        return False
        
    try:
        from sop_generator import SOPGenerator
        print("   ✓ SOPGenerator module loaded")
    except ImportError as e:
        print(f"   ✗ SOPGenerator import failed: {e}")
        return False
        
    # Check services
    print("\n2. Checking service connectivity...")
    
    import requests
    
    # Check VLM service
    try:
        response = requests.get("http://localhost:8000/model_info", timeout=2)
        if response.status_code == 200:
            model_info = response.json()
            print(f"   ✓ VLM service running (Model: {model_info.get('model_size', 'Unknown')})")
        else:
            print(f"   ⚠ VLM service responded with status {response.status_code}")
    except:
        print("   ⚠ VLM service not accessible (start with: python services/vlm/vlm_server.py)")
        
    # Check transcription service
    try:
        response = requests.get("http://localhost:8001/", timeout=2)
        if response.status_code == 200:
            print("   ✓ Transcription service running")
        else:
            print(f"   ⚠ Transcription service responded with status {response.status_code}")
    except:
        print("   ⚠ Transcription service not accessible (start with: python services/audio/transcription_server.py)")
        
    print("\n3. System Configuration:")
    print(f"   - Frame output directory: frames/")
    print(f"   - Using 7B VLM model: Recommended for better accuracy")
    print(f"   - Audio formats supported: MP3, WAV, M4A, etc.")
    print(f"   - Video formats supported: MP4, AVI, MOV, WEBM")
    
    print("\n" + "="*60)
    print("Setup Summary:")
    print("="*60)
    print("\nTo use the Video-to-SOP converter:")
    print("1. Ensure VLM service is running (port 8000)")
    print("2. Ensure Transcription service is running (port 8001)")
    print("3. Run: python services/video_sop/test_video_to_sop.py <video_path>")
    
    print("\nExample video sources to test:")
    print("- Screen recording showing a software process")
    print("- Tutorial video with narration")
    print("- Equipment operation demonstration")
    
    return True


def create_sample_sop():
    """Create a sample SOP to show the expected output format"""
    
    sample_sop = """# Sample SOP: How to Export Data

*Generated on: 2025-01-09 10:00*

## Video Information
- Duration: 120.0 seconds
- Resolution: 1920x1080

## Prerequisites
- [ ] Required tools and access ready
- [ ] Understanding of basic concepts

## Steps

### Step 1: Open the Application
*Timestamp: 00:05*

**Instructions:**
Click on the application icon to launch the program.

**Visual Guide:**
The application icon is located on the desktop. Double-click to open.

![Step 1](frames/frame_0001_5.0s.jpg)

**Tips:**
- 💡 Make sure you have the latest version installed

---

### Step 2: Navigate to Export Menu
*Timestamp: 00:15*

**Instructions:**
Click on File menu, then select Export option.

**Visual Guide:**
The File menu is in the top-left corner. The Export option is the third item.

![Step 2](frames/frame_0002_15.0s.jpg)

**Warnings:**
- ⚠️ Ensure you have saved your work before exporting

---

### Step 3: Select Export Format
*Timestamp: 00:25*

**Instructions:**
Choose CSV format from the dropdown menu.

**Visual Guide:**
A dialog box appears with format options. Select CSV for Excel compatibility.

![Step 3](frames/frame_0003_25.0s.jpg)

**Tips:**
- 💡 CSV format works best for data analysis

---

## Summary
This SOP contains 3 steps to complete the process.

## Notes
- Review each step carefully before proceeding
- Take screenshots if you encounter any issues
- Contact support if you need assistance
"""
    
    print("\n" + "="*60)
    print("Sample SOP Output Format:")
    print("="*60)
    print(sample_sop)
    
    # Save sample
    with open("sample_sop.md", "w") as f:
        f.write(sample_sop)
    print("\nSample SOP saved to: sample_sop.md")


if __name__ == "__main__":
    # Run basic test
    if test_basic_setup():
        print("\n✓ Basic setup complete!")
        
        # Show sample output
        if "--sample" in sys.argv:
            create_sample_sop()
    else:
        print("\n✗ Setup incomplete. Please check the errors above.")