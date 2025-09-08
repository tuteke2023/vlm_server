#!/usr/bin/env python3
"""
Simple video processor using ffmpeg directly (no OpenCV dependency)
"""

import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict
import json
import os

class SimpleVideoProcessor:
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
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return output_path
            else:
                print(f"Error extracting audio: {result.stderr}")
                return None
        except FileNotFoundError:
            print("ffmpeg not found. Please install ffmpeg.")
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None
            
    def extract_frames_ffmpeg(self, video_path: str, interval_seconds: float = 5.0) -> List[Dict]:
        """Extract frames using ffmpeg directly"""
        frames_data = []
        
        # Get video duration first
        duration = self.get_video_duration(video_path)
        if not duration:
            print("Could not determine video duration")
            return frames_data
            
        print(f"Video duration: {duration:.1f} seconds")
        print(f"Extracting frames every {interval_seconds} seconds...")
        
        # Extract frames at intervals
        frame_count = 0
        timestamp = 0
        
        while timestamp < duration:
            output_file = self.output_dir / f"frame_{frame_count:04d}_{timestamp:.1f}s.jpg"
            
            cmd = [
                'ffmpeg',
                '-ss', str(timestamp),  # Seek to timestamp
                '-i', video_path,
                '-frames:v', '1',  # Extract 1 frame
                '-q:v', '2',  # Quality (2 is good)
                '-y',  # Overwrite
                str(output_file)
            ]
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0 and output_file.exists():
                    frames_data.append({
                        'frame_number': frame_count,
                        'timestamp': timestamp,
                        'filename': str(output_file)
                    })
                    frame_count += 1
                    print(f"  Extracted frame at {timestamp:.1f}s")
            except Exception as e:
                print(f"  Error extracting frame at {timestamp}s: {e}")
                
            timestamp += interval_seconds
            
        print(f"Extracted {len(frames_data)} frames")
        return frames_data
        
    def get_video_duration(self, video_path: str) -> float:
        """Get video duration using ffprobe"""
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            video_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return float(result.stdout.strip())
        except:
            pass
            
        return None
        
    def get_video_info(self, video_path: str) -> Dict:
        """Get video information using ffprobe"""
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            video_path
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                
                # Find video stream
                video_stream = None
                for stream in data.get('streams', []):
                    if stream['codec_type'] == 'video':
                        video_stream = stream
                        break
                        
                if video_stream:
                    return {
                        'width': int(video_stream.get('width', 0)),
                        'height': int(video_stream.get('height', 0)),
                        'fps': eval(video_stream.get('r_frame_rate', '0/1')),
                        'duration': float(data.get('format', {}).get('duration', 0)),
                        'codec': video_stream.get('codec_name', 'unknown')
                    }
        except Exception as e:
            print(f"Error getting video info: {e}")
            
        return {
            'width': 0,
            'height': 0,
            'fps': 0,
            'duration': 0,
            'codec': 'unknown'
        }


# Test if ffmpeg is available
def check_ffmpeg():
    """Check if ffmpeg and ffprobe are available"""
    tools_available = True
    
    for tool in ['ffmpeg', 'ffprobe']:
        try:
            result = subprocess.run([tool, '-version'], capture_output=True)
            if result.returncode == 0:
                print(f"✓ {tool} is available")
            else:
                print(f"✗ {tool} not working properly")
                tools_available = False
        except FileNotFoundError:
            print(f"✗ {tool} not found. Please install ffmpeg.")
            tools_available = False
            
    return tools_available


if __name__ == "__main__":
    print("Checking ffmpeg availability...")
    if check_ffmpeg():
        print("\nffmpeg tools are ready!")
        print("\nYou can now use SimpleVideoProcessor for video processing.")
    else:
        print("\nPlease install ffmpeg:")
        print("  Ubuntu/Debian: sudo apt-get install ffmpeg")
        print("  macOS: brew install ffmpeg")
        print("  Windows: Download from https://ffmpeg.org/download.html")