#!/usr/bin/env python3
"""
Video to SOP Converter - User-Friendly Interface
Convert any instructional video into a comprehensive Standard Operating Procedure
"""

import sys
import os
import argparse
import json
import requests
from pathlib import Path
from hybrid_sop_generator import HybridSOPGenerator
import subprocess
import time

class VideoToSOPConverter:
    def __init__(self):
        self.vlm_url = "http://localhost:8000"
        self.transcription_url = "http://localhost:8001"
        
    def check_services(self):
        """Check if required services are running"""
        services_ok = True
        
        # Check VLM service
        try:
            response = requests.get(f"{self.vlm_url}/model_info", timeout=2)
            if response.status_code == 200:
                print("✅ VLM Service is running")
            else:
                print("❌ VLM Service not ready")
                services_ok = False
        except:
            print("❌ VLM Service not running on port 8000")
            print("   Start it with: python services/vlm/real_vlm_server.py")
            services_ok = False
            
        # Check Transcription service
        try:
            response = requests.get(f"{self.transcription_url}/", timeout=2)
            if response.status_code == 200:
                print("✅ Transcription Service is running")
            else:
                print("❌ Transcription Service not ready")
                services_ok = False
        except:
            print("❌ Transcription Service not running on port 8001")
            print("   Start it with: python services/audio/transcription_server.py")
            services_ok = False
            
        return services_ok
    
    def extract_audio(self, video_path: str) -> str:
        """Extract audio from video"""
        print("\n📹 Extracting audio from video...")
        audio_path = Path(video_path).with_suffix('.wav')
        
        cmd = [
            'ffmpeg', '-i', video_path,
            '-vn', '-acodec', 'pcm_s16le',
            '-ar', '16000', '-ac', '1',
            str(audio_path), '-y'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ Audio extracted to: {audio_path}")
            return str(audio_path)
        else:
            print(f"   ❌ Failed to extract audio: {result.stderr}")
            return None
    
    def transcribe_audio(self, audio_path: str) -> dict:
        """Transcribe audio using transcription service"""
        print("\n🎤 Transcribing audio...")
        
        with open(audio_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f"{self.transcription_url}/transcribe",
                files=files
            )
        
        if response.status_code == 200:
            transcript = response.json()
            print(f"   ✅ Transcription complete")
            print(f"   📝 Found {len(transcript.get('segments', []))} segments")
            return transcript
        else:
            print(f"   ❌ Transcription failed")
            return None
    
    def identify_key_segments(self, transcript: dict) -> list:
        """Identify key segments from transcript"""
        print("\n🔍 Identifying key segments...")
        
        # Keywords that indicate important steps
        action_keywords = [
            'click', 'select', 'navigate', 'go to', 'open', 'choose',
            'enter', 'type', 'download', 'upload', 'save', 'submit',
            'press', 'tap', 'scroll', 'find', 'locate', 'verify',
            'check', 'confirm', 'review', 'approve', 'reject'
        ]
        
        key_segments = []
        for segment in transcript.get('segments', []):
            text = segment.get('text', '').lower()
            
            # Check if segment contains action keywords
            for keyword in action_keywords:
                if keyword in text:
                    # Try to identify what visual element to look for
                    if 'button' in text:
                        segment['expected_visual'] = 'button'
                    elif 'menu' in text:
                        segment['expected_visual'] = 'menu'
                    elif 'form' in text or 'field' in text:
                        segment['expected_visual'] = 'form field'
                    elif 'page' in text or 'screen' in text:
                        segment['expected_visual'] = 'page or screen'
                    else:
                        segment['expected_visual'] = keyword
                    
                    key_segments.append(segment)
                    break
        
        print(f"   ✅ Found {len(key_segments)} key action segments")
        return key_segments
    
    def convert_video_to_sop(self, video_path: str, output_dir: str = None):
        """Main conversion process"""
        print("\n" + "="*60)
        print("🚀 VIDEO TO SOP CONVERTER")
        print("="*60)
        
        # Validate video exists
        if not Path(video_path).exists():
            print(f"❌ Video not found: {video_path}")
            return False
        
        print(f"📹 Input: {video_path}")
        
        # Check services
        if not self.check_services():
            print("\n⚠️  Please start the required services first")
            return False
        
        # Extract audio
        audio_path = self.extract_audio(video_path)
        if not audio_path:
            return False
        
        # Transcribe
        transcript = self.transcribe_audio(audio_path)
        if not transcript:
            return False
        
        # Identify key segments
        key_segments = self.identify_key_segments(transcript)
        
        # Prepare transcript for hybrid generator
        transcript_for_generator = {
            'segments': key_segments
        }
        
        # Use hybrid generator
        print("\n🤖 Generating comprehensive SOP...")
        generator = HybridSOPGenerator()
        
        # Set custom output directory if provided
        if output_dir:
            generator.output_dir = Path(output_dir)
            generator.output_dir.mkdir(exist_ok=True)
        
        # Generate SOP
        sop = generator.generate_comprehensive_sop(video_path, transcript_for_generator)
        
        # Save transcript for reference
        transcript_path = generator.output_dir / "transcript.json"
        with open(transcript_path, 'w') as f:
            json.dump(transcript, f, indent=2)
        
        print("\n" + "="*60)
        print("✅ SOP GENERATION COMPLETE!")
        print("="*60)
        print(f"\n📁 Output Directory: {generator.output_dir}")
        print(f"📄 SOP Document: {generator.output_dir}/hybrid_comprehensive_sop.md")
        print(f"📝 Transcript: {transcript_path}")
        print(f"🖼️  Frame Images: {generator.output_dir}/step_*.jpg")
        
        # Cleanup audio file
        Path(audio_path).unlink(missing_ok=True)
        
        return True


def main():
    parser = argparse.ArgumentParser(
        description='Convert instructional videos to Standard Operating Procedures',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python video_to_sop.py video.mp4
  python video_to_sop.py video.mp4 --output ./my_sops
  python video_to_sop.py "C:\\Videos\\tutorial.mkv" --output ./output

Requirements:
  - VLM Server running on port 8000
  - Transcription Server running on port 8001
  - FFmpeg installed
  - GPU with 16GB+ VRAM for 7B model
        """
    )
    
    parser.add_argument('video', help='Path to the video file')
    parser.add_argument('--output', '-o', help='Output directory (default: ./hybrid_sop_output)')
    
    args = parser.parse_args()
    
    # Convert video to SOP
    converter = VideoToSOPConverter()
    success = converter.convert_video_to_sop(args.video, args.output)
    
    if success:
        print("\n💡 Tip: Open the .md file in a markdown viewer or VS Code")
        print("   The images should display inline with the instructions")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()