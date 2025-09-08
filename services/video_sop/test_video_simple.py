#!/usr/bin/env python3
"""
Simple test for Video-to-SOP conversion using ffmpeg
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from video_processor_simple import SimpleVideoProcessor, check_ffmpeg
from sop_generator import SOPGenerator
import json

def test_video_to_sop(video_path: str):
    """Test the video to SOP conversion pipeline"""
    
    print(f"\n{'='*60}")
    print(f"Video-to-SOP Conversion Test")
    print(f"Video: {video_path}")
    print(f"{'='*60}\n")
    
    # Check ffmpeg first
    if not check_ffmpeg():
        print("\nError: ffmpeg is required but not available")
        return
    
    # Check if video exists
    if not Path(video_path).exists():
        print(f"Error: Video file not found: {video_path}")
        print("\nPlease provide a valid video file path.")
        print("Example: python test_video_simple.py /path/to/your/video.mp4")
        return
        
    # Initialize components
    processor = SimpleVideoProcessor(output_dir="frames")
    generator = SOPGenerator()
    
    try:
        # Step 1: Get video information
        print("\nStep 1: Analyzing video...")
        video_info = processor.get_video_info(video_path)
        if video_info['duration'] > 0:
            print(f"  Duration: {video_info['duration']:.1f} seconds")
            print(f"  Resolution: {video_info['width']}x{video_info['height']}")
            print(f"  Codec: {video_info['codec']}")
        else:
            print("  Could not get video information, continuing anyway...")
            
        # Step 2: Extract audio
        print("\nStep 2: Extracting audio...")
        audio_path = processor.extract_audio(video_path, "temp_audio.mp3")
        if audio_path and Path(audio_path).exists():
            print(f"  ✓ Audio extracted to: {audio_path}")
        else:
            print("  ⚠ No audio extracted (video may not have audio track)")
            audio_path = None
            
        # Step 3: Extract frames
        print("\nStep 3: Extracting frames...")
        
        # Determine interval based on video duration
        duration = video_info.get('duration', 60)
        if duration > 0 and duration < 60:
            interval = 5.0  # Every 5 seconds for short videos
        elif duration < 300:
            interval = 10.0  # Every 10 seconds for medium videos
        else:
            interval = 20.0  # Every 20 seconds for long videos
            
        frames = processor.extract_frames_ffmpeg(video_path, interval_seconds=interval)
        
        if not frames:
            print("  ✗ No frames extracted")
            return
            
        print(f"  ✓ Extracted {len(frames)} frames")
        
        # Step 4: Check services
        print("\nStep 4: Checking required services...")
        
        import requests
        vlm_available = False
        transcription_available = False
        
        try:
            response = requests.get("http://localhost:8000/model_info", timeout=2)
            if response.status_code == 200:
                print("  ✓ VLM service is running")
                vlm_available = True
                
                # Try to switch to 7B model
                print("  Attempting to switch to 7B model for better accuracy...")
                generator.switch_to_7b_model()
        except:
            print("  ⚠ VLM service not running (start with: python services/vlm/vlm_server.py)")
            
        if audio_path:
            try:
                response = requests.get("http://localhost:8001/", timeout=2)
                if response.status_code == 200:
                    print("  ✓ Transcription service is running")
                    transcription_available = True
            except:
                print("  ⚠ Transcription service not running (start with: python services/audio/transcription_server.py)")
        
        if not vlm_available:
            print("\n⚠ VLM service is required for frame analysis")
            print("Please start the VLM service first.")
            return
            
        # Step 5: Generate SOP
        print("\nStep 5: Generating SOP...")
        print("  Note: This may take a few minutes depending on video length")
        
        # Limit frames for testing (use first 5 frames)
        test_frames = frames[:5] if len(frames) > 5 else frames
        print(f"  Processing {len(test_frames)} frames for this test...")
        
        result = generator.generate_sop_from_video(
            video_path=video_path,
            frames=test_frames,
            audio_path=audio_path if transcription_available else None,
            title=Path(video_path).stem.replace('_', ' ').title()
        )
        
        # Step 6: Save results
        print("\nStep 6: Saving results...")
        
        # Save SOP document
        sop_file = Path("generated_sop.md")
        with open(sop_file, 'w') as f:
            f.write(result['document'])
        print(f"  ✓ SOP document saved to: {sop_file}")
        
        # Save metadata
        meta_file = Path("sop_metadata.json")
        metadata = {
            'title': result['title'],
            'video_path': str(video_path),
            'video_duration': video_info.get('duration', 0),
            'frames_analyzed': result['frames_analyzed'],
            'steps_generated': len(result['steps']),
            'has_transcript': result['transcript'] is not None
        }
        with open(meta_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        print(f"  ✓ Metadata saved to: {meta_file}")
        
        # Display summary
        print(f"\n{'='*60}")
        print("✓ SOP Generation Complete!")
        print(f"{'='*60}")
        print(f"  Title: {result['title']}")
        print(f"  Steps Generated: {len(result['steps'])}")
        print(f"  Frames Analyzed: {result['frames_analyzed']}")
        print(f"  Transcript: {'Available' if result['transcript'] else 'Not available'}")
        
        # Show first 2 steps as preview
        if result['steps']:
            print("\nPreview of generated steps:")
            print("-" * 40)
            for step in result['steps'][:2]:
                print(f"\nStep {step['number']}: {step['title']}")
                print(f"  Time: {step['timestamp']}")
                instruction = step['instruction']
                if len(instruction) > 100:
                    print(f"  Instruction: {instruction[:100]}...")
                else:
                    print(f"  Instruction: {instruction}")
                    
        print(f"\n✓ Full SOP saved to: {sop_file}")
        print(f"  View with: cat {sop_file}")
        
        # Cleanup temporary audio file
        if audio_path and Path(audio_path).exists():
            try:
                Path(audio_path).unlink()
                print(f"\n  Cleaned up temporary audio file")
            except:
                pass
                
    except Exception as e:
        print(f"\n✗ Error during processing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Check if video path provided
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
    else:
        print("\n" + "="*60)
        print("Video-to-SOP Converter")
        print("="*60)
        print("\nUsage: python test_video_simple.py <video_path>")
        print("\nExample:")
        print("  python test_video_simple.py /path/to/tutorial.mp4")
        print("\nSupported formats: MP4, AVI, MOV, WEBM, MKV")
        print("\nNote: For best results:")
        print("  1. Use videos with clear narration")
        print("  2. Keep videos under 5 minutes for testing")
        print("  3. Ensure good video quality")
        
        video_path = input("\nEnter video path (or press Enter to exit): ").strip()
        if not video_path:
            print("Exiting...")
            sys.exit(0)
            
    test_video_to_sop(video_path)