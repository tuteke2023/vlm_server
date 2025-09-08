#!/usr/bin/env python3
"""
Video processor for extracting frames and audio from videos
"""

import cv2
import os
import subprocess
import tempfile
import json
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np

class VideoProcessor:
    def __init__(self, output_dir: str = "frames"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def extract_audio(self, video_path: str, output_path: str = None) -> str:
        """Extract audio from video using ffmpeg"""
        if output_path is None:
            output_path = tempfile.mktemp(suffix='.mp3')
            
        cmd = [
            'ffmpeg', '-i', video_path,
            '-vn',  # No video
            '-acodec', 'mp3',
            '-ab', '192k',  # Audio bitrate
            '-ar', '16000',  # Sample rate for Whisper
            '-y',  # Overwrite
            output_path
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return output_path
        except subprocess.CalledProcessError as e:
            print(f"Error extracting audio: {e.stderr.decode()}")
            return None
            
    def extract_frames(self, video_path: str, interval_seconds: float = 5.0) -> List[Dict]:
        """Extract frames at regular intervals"""
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
            
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        
        frames_data = []
        frame_interval = int(fps * interval_seconds)
        
        print(f"Video info: {fps} FPS, {total_frames} frames, {duration:.1f} seconds")
        print(f"Extracting frames every {interval_seconds} seconds...")
        
        frame_count = 0
        saved_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            if frame_count % frame_interval == 0:
                timestamp = frame_count / fps
                frame_filename = f"frame_{saved_count:04d}_{timestamp:.1f}s.jpg"
                frame_path = self.output_dir / frame_filename
                
                cv2.imwrite(str(frame_path), frame)
                
                frames_data.append({
                    'frame_number': saved_count,
                    'timestamp': timestamp,
                    'filename': str(frame_path),
                    'original_frame': frame_count
                })
                
                saved_count += 1
                
            frame_count += 1
            
        cap.release()
        
        print(f"Extracted {saved_count} frames")
        return frames_data
        
    def extract_key_frames(self, video_path: str, sensitivity: float = 30.0) -> List[Dict]:
        """Extract frames when significant changes occur (scene detection)"""
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
            
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        frames_data = []
        prev_frame = None
        frame_count = 0
        saved_count = 0
        
        print("Extracting key frames based on scene changes...")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # First frame or scene change detection
            if prev_frame is None:
                save_frame = True
            else:
                # Calculate difference between frames
                diff = cv2.absdiff(prev_frame, gray)
                mean_diff = np.mean(diff)
                
                # Save if significant change
                save_frame = mean_diff > sensitivity
                
            if save_frame:
                timestamp = frame_count / fps
                frame_filename = f"keyframe_{saved_count:04d}_{timestamp:.1f}s.jpg"
                frame_path = self.output_dir / frame_filename
                
                cv2.imwrite(str(frame_path), frame)
                
                frames_data.append({
                    'frame_number': saved_count,
                    'timestamp': timestamp,
                    'filename': str(frame_path),
                    'is_key_frame': True,
                    'original_frame': frame_count
                })
                
                saved_count += 1
                prev_frame = gray
                
            frame_count += 1
            
            # Also save a frame every 10 seconds minimum
            if frame_count % (int(fps) * 10) == 0:
                prev_frame = gray
                
        cap.release()
        
        print(f"Extracted {saved_count} key frames")
        return frames_data
        
    def get_video_info(self, video_path: str) -> Dict:
        """Get basic video information"""
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")
            
        info = {
            'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            'fps': cap.get(cv2.CAP_PROP_FPS),
            'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
            'duration': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) / cap.get(cv2.CAP_PROP_FPS)
        }
        
        cap.release()
        return info


# Example usage
if __name__ == "__main__":
    processor = VideoProcessor()
    
    # Example video path
    video_path = "/path/to/video.mp4"
    
    if Path(video_path).exists():
        # Extract audio
        audio_path = processor.extract_audio(video_path)
        print(f"Audio extracted to: {audio_path}")
        
        # Extract frames
        frames = processor.extract_frames(video_path, interval_seconds=5)
        
        # Get video info
        info = processor.get_video_info(video_path)
        print(f"Video info: {json.dumps(info, indent=2)}")