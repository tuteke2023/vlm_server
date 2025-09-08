#!/usr/bin/env python3
"""
Test script for Video-to-SOP conversion
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from video_processor import VideoProcessor
from sop_generator import SOPGenerator
import json

def test_video_to_sop(video_path: str):
    """Test the video to SOP conversion pipeline"""
    
    print(f"\n{'='*60}")
    print(f"Testing Video-to-SOP Conversion")
    print(f"Video: {video_path}")
    print(f"{'='*60}\n")
    
    # Check if video exists
    if not Path(video_path).exists():
        print(f"Error: Video file not found: {video_path}")
        return
        
    # Initialize components
    processor = VideoProcessor(output_dir="frames")
    generator = SOPGenerator()
    
    try:
        # Step 1: Get video information
        print("Step 1: Analyzing video...")
        video_info = processor.get_video_info(video_path)
        print(f"Video Duration: {video_info['duration']:.1f} seconds")
        print(f"Resolution: {video_info['width']}x{video_info['height']}")
        print(f"FPS: {video_info['fps']}")
        
        # Step 2: Extract audio
        print("\nStep 2: Extracting audio...")
        audio_path = processor.extract_audio(video_path, "temp_audio.mp3")
        if audio_path:
            print(f"Audio extracted to: {audio_path}")
        else:
            print("No audio track found or extraction failed")
            
        # Step 3: Extract frames
        print("\nStep 3: Extracting frames...")
        
        # Use key frame extraction for shorter videos, interval for longer
        if video_info['duration'] < 60:
            frames = processor.extract_key_frames(video_path, sensitivity=25.0)
        else:
            # Extract frame every 10 seconds for longer videos
            frames = processor.extract_frames(video_path, interval_seconds=10.0)
            
        print(f"Extracted {len(frames)} frames")
        
        # Step 4: Generate SOP
        print("\nStep 4: Generating SOP (this may take a few minutes)...")
        print("Note: Using 7B VLM for better accuracy")
        
        result = generator.generate_sop_from_video(
            video_path=video_path,
            frames=frames[:5],  # Limit to first 5 frames for testing
            audio_path=audio_path if audio_path else None,
            title=Path(video_path).stem.replace('_', ' ').title()
        )
        
        # Step 5: Save results
        print("\nStep 5: Saving results...")
        
        # Save SOP document
        sop_file = Path("generated_sop.md")
        with open(sop_file, 'w') as f:
            f.write(result['document'])
        print(f"SOP document saved to: {sop_file}")
        
        # Save metadata
        meta_file = Path("sop_metadata.json")
        metadata = {
            'title': result['title'],
            'video_path': video_path,
            'video_duration': video_info['duration'],
            'frames_analyzed': result['frames_analyzed'],
            'steps_generated': len(result['steps']),
            'has_transcript': result['transcript'] is not None
        }
        with open(meta_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        print(f"Metadata saved to: {meta_file}")
        
        # Display summary
        print(f"\n{'='*60}")
        print("SOP Generation Complete!")
        print(f"{'='*60}")
        print(f"Title: {result['title']}")
        print(f"Steps Generated: {len(result['steps'])}")
        print(f"Frames Analyzed: {result['frames_analyzed']}")
        print(f"Transcript Available: {'Yes' if result['transcript'] else 'No'}")
        
        # Show first 3 steps as preview
        print("\nPreview of generated steps:")
        print("-" * 40)
        for step in result['steps'][:3]:
            print(f"\nStep {step['number']}: {step['title']}")
            print(f"Time: {step['timestamp']}")
            if len(step['instruction']) > 100:
                print(f"Instruction: {step['instruction'][:100]}...")
            else:
                print(f"Instruction: {step['instruction']}")
                
        print("\nFull SOP saved to generated_sop.md")
        
        # Cleanup temporary audio file
        if audio_path and Path(audio_path).exists():
            Path(audio_path).unlink()
            
    except Exception as e:
        print(f"\nError during processing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Check if video path provided
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
    else:
        # Ask for video path
        video_path = input("Enter the path to your video file: ").strip()
        
    test_video_to_sop(video_path)