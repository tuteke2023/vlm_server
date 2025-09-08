#!/usr/bin/env python3
"""
Intelligent Frame Extraction System
Extracts meaningful frames based on content, not just fixed intervals
"""

import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import json
import subprocess
from dataclasses import dataclass
from datetime import timedelta
import re

@dataclass
class KeyMoment:
    """Represents a key moment in the video"""
    timestamp: float
    action: str
    description: str
    confidence: float
    frame_path: Optional[str] = None

class IntelligentFrameExtractor:
    def __init__(self, output_dir: str = "smart_frames"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def extract_smart_frames(self, video_path: str, transcript: Dict) -> List[Dict]:
        """
        Extract frames intelligently based on transcript and visual changes
        """
        print("\n🧠 Intelligent Frame Extraction Starting...")
        
        # 1. Analyze transcript for key moments
        key_moments = self._identify_key_moments(transcript)
        print(f"  ✓ Identified {len(key_moments)} key moments from transcript")
        
        # 2. Detect scene changes in video
        scene_changes = self._detect_scene_changes(video_path)
        print(f"  ✓ Detected {len(scene_changes)} scene changes")
        
        # 3. Detect UI transitions (significant visual changes)
        ui_transitions = self._detect_ui_transitions(video_path)
        print(f"  ✓ Found {len(ui_transitions)} UI transitions")
        
        # 4. Correlate and merge all moments
        final_moments = self._correlate_moments(
            key_moments, 
            scene_changes, 
            ui_transitions,
            transcript
        )
        print(f"  ✓ Correlated to {len(final_moments)} final extraction points")
        
        # 5. Extract frames at these specific moments
        frames = self._extract_frames_at_moments(video_path, final_moments)
        print(f"  ✓ Extracted {len(frames)} frames")
        
        # 6. Validate and rank frames
        validated_frames = self._validate_and_rank_frames(frames, transcript)
        
        return validated_frames
    
    def _identify_key_moments(self, transcript: Dict) -> List[KeyMoment]:
        """
        Identify key moments from transcript text
        """
        key_moments = []
        
        # Action keywords that indicate important moments
        action_keywords = [
            'click', 'select', 'navigate', 'go to', 'open', 'choose',
            'download', 'filter', 'search', 'enter', 'type', 'press',
            'scroll', 'find', 'locate', 'access', 'view', 'see',
            'shows', 'displays', 'appears', 'available', 'visible'
        ]
        
        # Process segments if available
        segments = transcript.get('segments', [])
        if not segments and 'text' in transcript:
            # Create segments from full text
            text = transcript['text']
            sentences = re.split(r'[.!?]+', text)
            segments = []
            time_per_sentence = 80.0 / len(sentences) if sentences else 5.0
            
            for i, sentence in enumerate(sentences):
                segments.append({
                    'text': sentence.strip(),
                    'start': i * time_per_sentence,
                    'end': (i + 1) * time_per_sentence
                })
        
        for segment in segments:
            text = segment.get('text', '').lower()
            start_time = segment.get('start', 0)
            
            # Check for action keywords
            for keyword in action_keywords:
                if keyword in text:
                    # Calculate confidence based on keyword importance
                    confidence = 0.9 if keyword in ['click', 'select', 'download'] else 0.7
                    
                    moment = KeyMoment(
                        timestamp=start_time,
                        action=keyword,
                        description=segment.get('text', '')[:100],
                        confidence=confidence
                    )
                    key_moments.append(moment)
                    break  # One moment per segment
        
        return key_moments
    
    def _detect_scene_changes(self, video_path: str, threshold: float = 30.0) -> List[float]:
        """
        Detect scene changes using frame difference analysis
        """
        scene_changes = []
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            return scene_changes
            
        fps = cap.get(cv2.CAP_PROP_FPS)
        prev_frame = None
        prev_hist = None
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Convert to grayscale for comparison
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Calculate histogram for better scene detection
            hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
            hist = cv2.normalize(hist, hist).flatten()
            
            if prev_hist is not None:
                # Compare histograms
                correlation = cv2.compareHist(prev_hist, hist, cv2.HISTCMP_CORREL)
                
                # If correlation is low, it's likely a scene change
                if correlation < 0.7:  # Threshold for scene change
                    timestamp = frame_count / fps
                    scene_changes.append(timestamp)
                    
            prev_hist = hist
            frame_count += 1
            
            # Skip frames for faster processing (check every 0.5 seconds)
            skip_frames = int(fps * 0.5)
            for _ in range(skip_frames):
                cap.read()
                frame_count += 1
                
        cap.release()
        return scene_changes
    
    def _detect_ui_transitions(self, video_path: str) -> List[float]:
        """
        Detect UI transitions (menu opens, page loads, etc.)
        """
        ui_transitions = []
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            return ui_transitions
            
        fps = cap.get(cv2.CAP_PROP_FPS)
        prev_edges = None
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            # Edge detection to find UI elements
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 50, 150)
            
            if prev_edges is not None:
                # Calculate difference in edge patterns
                diff = cv2.absdiff(edges, prev_edges)
                change_amount = np.sum(diff) / (edges.shape[0] * edges.shape[1])
                
                # Significant change in edges indicates UI transition
                if change_amount > 50:  # Threshold for UI change
                    timestamp = frame_count / fps
                    ui_transitions.append(timestamp)
                    
            prev_edges = edges
            frame_count += 1
            
            # Skip frames for faster processing
            skip_frames = int(fps * 0.5)
            for _ in range(skip_frames):
                cap.read()
                frame_count += 1
                
        cap.release()
        return ui_transitions
    
    def _correlate_moments(self, key_moments: List[KeyMoment], 
                          scene_changes: List[float],
                          ui_transitions: List[float],
                          transcript: Dict) -> List[KeyMoment]:
        """
        Correlate all detected moments and merge nearby ones
        """
        all_moments = []
        
        # Add key moments from transcript
        all_moments.extend(key_moments)
        
        # Add scene changes as moments
        for timestamp in scene_changes:
            moment = KeyMoment(
                timestamp=timestamp,
                action="scene_change",
                description="Visual scene change detected",
                confidence=0.6
            )
            all_moments.append(moment)
            
        # Add UI transitions as moments
        for timestamp in ui_transitions:
            moment = KeyMoment(
                timestamp=timestamp,
                action="ui_transition",
                description="UI transition detected",
                confidence=0.5
            )
            all_moments.append(moment)
            
        # Sort by timestamp
        all_moments.sort(key=lambda x: x.timestamp)
        
        # Merge nearby moments (within 2 seconds)
        merged_moments = []
        last_timestamp = -10
        
        for moment in all_moments:
            if moment.timestamp - last_timestamp > 2.0:
                merged_moments.append(moment)
                last_timestamp = moment.timestamp
            else:
                # Merge with previous, keeping higher confidence
                if merged_moments and moment.confidence > merged_moments[-1].confidence:
                    merged_moments[-1] = moment
                    
        return merged_moments
    
    def _extract_frames_at_moments(self, video_path: str, 
                                   moments: List[KeyMoment]) -> List[Dict]:
        """
        Extract frames at specific moments
        """
        frames = []
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            return frames
            
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        for i, moment in enumerate(moments):
            # Seek to the moment
            frame_number = int(moment.timestamp * fps)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            
            ret, frame = cap.read()
            if ret:
                # Save frame
                frame_filename = f"smart_frame_{i:04d}_{moment.timestamp:.1f}s_{moment.action}.jpg"
                frame_path = self.output_dir / frame_filename
                cv2.imwrite(str(frame_path), frame)
                
                moment.frame_path = str(frame_path)
                
                frames.append({
                    'frame_number': i,
                    'timestamp': moment.timestamp,
                    'filename': str(frame_path),
                    'action': moment.action,
                    'description': moment.description,
                    'confidence': moment.confidence,
                    'is_key_frame': True
                })
                
        cap.release()
        return frames
    
    def _validate_and_rank_frames(self, frames: List[Dict], 
                                  transcript: Dict) -> List[Dict]:
        """
        Validate frames and rank by importance
        """
        # Sort by confidence and timestamp
        frames.sort(key=lambda x: (x['confidence'], -x['timestamp']), reverse=True)
        
        # Mark top frames as primary
        for i, frame in enumerate(frames):
            frame['priority'] = 'high' if i < 10 else 'medium' if i < 20 else 'low'
            
        # Re-sort by timestamp for chronological order
        frames.sort(key=lambda x: x['timestamp'])
        
        return frames
    
    def generate_smart_sop(self, frames: List[Dict], transcript: Dict) -> str:
        """
        Generate SOP using intelligently extracted frames
        """
        sop = "# Intelligently Generated SOP\n\n"
        
        # Group frames by action type
        action_frames = {}
        for frame in frames:
            action = frame['action']
            if action not in action_frames:
                action_frames[action] = []
            action_frames[action].append(frame)
        
        # Generate steps based on high-priority frames
        high_priority = [f for f in frames if f.get('priority') == 'high']
        
        for i, frame in enumerate(high_priority):
            sop += f"\n## Step {i+1}: {frame['description'][:50]}\n"
            sop += f"*Timestamp: {frame['timestamp']:.1f}s*\n\n"
            sop += f"**Action Type:** {frame['action']}\n"
            sop += f"**Confidence:** {frame['confidence']:.0%}\n\n"
            sop += f"![Step {i+1}]({frame['filename']})\n\n"
            
        return sop


# Test function
def test_intelligent_extraction(video_path: str):
    """Test the intelligent frame extraction"""
    
    print("\n" + "="*60)
    print("🚀 Testing Intelligent Frame Extraction")
    print("="*60)
    
    extractor = IntelligentFrameExtractor()
    
    # Load transcript (you would get this from transcription service)
    # For testing, create a mock transcript
    mock_transcript = {
        'text': "Go to the ATO portal. Click on Reports. Select all clients and download CSV.",
        'segments': [
            {'text': 'Go to the ATO portal', 'start': 0, 'end': 5},
            {'text': 'Click on Reports', 'start': 40, 'end': 45},
            {'text': 'Select all clients and download CSV', 'start': 60, 'end': 70}
        ]
    }
    
    # Extract frames intelligently
    smart_frames = extractor.extract_smart_frames(video_path, mock_transcript)
    
    print(f"\n📊 Results:")
    print(f"  • Extracted {len(smart_frames)} intelligent frames")
    print(f"  • High priority: {len([f for f in smart_frames if f.get('priority') == 'high'])}")
    print(f"  • Actions detected: {set(f['action'] for f in smart_frames)}")
    
    # Generate SOP
    sop = extractor.generate_smart_sop(smart_frames, mock_transcript)
    
    with open("intelligent_sop.md", "w") as f:
        f.write(sop)
        
    print(f"\n✅ Intelligent SOP saved to: intelligent_sop.md")
    
    return smart_frames


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
        test_intelligent_extraction(video_path)
    else:
        print("Usage: python intelligent_frame_extractor.py <video_path>")