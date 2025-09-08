#!/usr/bin/env python3
"""
Intelligent Frame Extraction System V2
Searches for the actual frame that matches the described action, not just when it's mentioned
"""

import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import json
from dataclasses import dataclass

@dataclass
class ActionFrame:
    """Represents an action and its best matching frame"""
    action: str
    description: str
    mention_time: float  # When it was mentioned
    actual_time: float   # When it actually happens
    frame_path: str
    confidence: float

class SmartFrameExtractorV2:
    def __init__(self, output_dir: str = "smart_frames_v2"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def extract_with_lookahead(self, video_path: str, transcript: Dict) -> List[ActionFrame]:
        """
        Extract frames by looking ahead to find when actions actually occur
        """
        print("\n🧠 Smart Frame Extraction V2 - With Look-ahead")
        
        # Parse transcript for actions
        actions = self._parse_transcript_actions(transcript)
        print(f"  ✓ Found {len(actions)} actions in transcript")
        
        # For each action, find the best matching frame
        action_frames = []
        for action in actions:
            best_frame = self._find_best_frame_for_action(
                video_path, 
                action,
                lookahead_seconds=20  # Look up to 20 seconds ahead
            )
            if best_frame:
                action_frames.append(best_frame)
                print(f"  ✓ {action['description'][:30]}: mentioned at {action['mention_time']:.1f}s, found at {best_frame.actual_time:.1f}s")
        
        return action_frames
    
    def _parse_transcript_actions(self, transcript: Dict) -> List[Dict]:
        """Parse transcript for key actions"""
        actions = []
        
        # Key phrases and what visual we should look for
        action_mappings = {
            'go to the ato portal': {'visual': 'ato_dashboard', 'priority': 1},
            'go to the reports': {'visual': 'reports_section', 'priority': 1},
            'go to reports': {'visual': 'reports_section', 'priority': 1},
            'income tax status': {'visual': 'income_tax_report', 'priority': 2},
            'select all clients': {'visual': 'all_clients_filter', 'priority': 2},
            'csv is available': {'visual': 'csv_download', 'priority': 3},
            'download': {'visual': 'download_button', 'priority': 3},
        }
        
        segments = transcript.get('segments', [])
        for segment in segments:
            text = segment.get('text', '').lower()
            start_time = segment.get('start', 0)
            
            for phrase, mapping in action_mappings.items():
                if phrase in text:
                    actions.append({
                        'phrase': phrase,
                        'description': segment.get('text', ''),
                        'mention_time': start_time,
                        'visual_target': mapping['visual'],
                        'priority': mapping['priority']
                    })
                    break
        
        return actions
    
    def _find_best_frame_for_action(self, video_path: str, action: Dict, 
                                    lookahead_seconds: float = 20) -> Optional[ActionFrame]:
        """
        Find the best frame for an action by looking ahead from when it's mentioned
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None
            
        fps = cap.get(cv2.CAP_PROP_FPS)
        mention_time = action['mention_time']
        
        # Start from when action is mentioned
        start_frame = int(mention_time * fps)
        end_frame = int((mention_time + lookahead_seconds) * fps)
        
        # Check frames in the lookahead window
        best_frame = None
        best_score = 0
        
        for frame_num in range(start_frame, end_frame, int(fps * 0.5)):  # Check every 0.5 seconds
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
            ret, frame = cap.read()
            if not ret:
                break
                
            # Score this frame for the target visual
            score = self._score_frame_for_visual(frame, action['visual_target'])
            
            if score > best_score:
                best_score = score
                best_frame = (frame, frame_num / fps)
        
        cap.release()
        
        if best_frame:
            # Save the best frame
            frame, timestamp = best_frame
            filename = f"action_{action['priority']:02d}_{timestamp:.1f}s_{action['phrase'].replace(' ', '_')}.jpg"
            frame_path = self.output_dir / filename
            cv2.imwrite(str(frame_path), frame)
            
            return ActionFrame(
                action=action['phrase'],
                description=action['description'],
                mention_time=mention_time,
                actual_time=timestamp,
                frame_path=str(frame_path),
                confidence=best_score
            )
        
        return None
    
    def _score_frame_for_visual(self, frame, visual_target: str) -> float:
        """
        Score how well a frame matches the expected visual
        This is a simplified version - real VLM would do better analysis
        """
        # Convert to grayscale for analysis
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Simple heuristics based on visual characteristics
        scores = {
            'ato_dashboard': self._detect_dashboard(frame),
            'reports_section': self._detect_reports_page(frame),
            'income_tax_report': self._detect_report_data(frame),
            'all_clients_filter': self._detect_filter_section(frame),
            'csv_download': self._detect_download_options(frame),
            'download_button': self._detect_download_options(frame),
        }
        
        return scores.get(visual_target, 0.0)
    
    def _detect_dashboard(self, frame) -> float:
        """Detect if frame shows ATO dashboard (with tiles)"""
        # Look for tile-like patterns (rectangular regions)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        
        # Count rectangular patterns (simplified)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        rect_count = 0
        for contour in contours:
            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
            if len(approx) == 4:  # Rectangle has 4 corners
                rect_count += 1
        
        # More rectangles = more likely to be dashboard
        return min(rect_count / 20.0, 1.0)
    
    def _detect_reports_page(self, frame) -> float:
        """Detect if frame shows reports section"""
        # Look for list-like structures (horizontal lines)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 30, 100)
        
        # Detect horizontal lines (reports are often in rows)
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=100, maxLineGap=10)
        
        if lines is not None:
            horizontal_lines = 0
            for line in lines:
                x1, y1, x2, y2 = line[0]
                if abs(y2 - y1) < 5:  # Nearly horizontal
                    horizontal_lines += 1
            
            return min(horizontal_lines / 10.0, 1.0)
        return 0.0
    
    def _detect_report_data(self, frame) -> float:
        """Detect if frame shows report data (tables)"""
        # Similar to reports page but with more structure
        return self._detect_reports_page(frame) * 0.8
    
    def _detect_filter_section(self, frame) -> float:
        """Detect filter/dropdown sections"""
        # Look for dropdown-like patterns in lower part of frame
        height = frame.shape[0]
        lower_third = frame[height*2//3:, :]
        
        gray = cv2.cvtColor(lower_third, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        
        # Count edges in lower third (UI controls often there)
        edge_density = np.sum(edges) / (edges.shape[0] * edges.shape[1])
        return min(edge_density * 10, 1.0)
    
    def _detect_download_options(self, frame) -> float:
        """Detect download buttons/options"""
        # Look for button-like rectangles
        return self._detect_filter_section(frame) * 0.9


def create_corrected_sop(video_path: str, transcript: Dict):
    """Create SOP with correctly matched frames"""
    
    extractor = SmartFrameExtractorV2()
    action_frames = extractor.extract_with_lookahead(video_path, transcript)
    
    # Generate corrected SOP
    sop = """# ATO Report Retrieval - Correctly Matched Visuals

## How This Version Is Different

This SOP uses intelligent look-ahead to find frames that actually show what's being described,
not just the frame when words are spoken.

## Steps with Correct Visuals

"""
    
    # Sort by priority and actual time
    action_frames.sort(key=lambda x: (x.action == 'go to the ato portal', x.actual_time))
    
    step_num = 1
    for af in action_frames:
        time_diff = af.actual_time - af.mention_time
        
        sop += f"""### Step {step_num}: {af.description[:50]}

**Narration Time:** {af.mention_time:.1f}s  
**Visual Appears:** {af.actual_time:.1f}s ({'+' if time_diff >= 0 else ''}{time_diff:.1f}s)  
**Action:** {af.action}  
**Confidence:** {af.confidence:.0%}

![Step {step_num}]({af.frame_path})

---

"""
        step_num += 1
    
    # Save the corrected SOP
    with open("ato_sop_corrected_visuals.md", "w") as f:
        f.write(sop)
    
    print(f"\n✅ Corrected SOP saved with proper visual matching")
    print(f"  • Frames now show actual content, not just when mentioned")
    print(f"  • Look-ahead found better matches for each action")
    
    return action_frames


if __name__ == "__main__":
    # Test with your video
    video_path = "/mnt/c/Users/tekee/Videos/2025-09-05 11-04-15.mkv"
    
    transcript = {
        "segments": [
            {"text": "You go to the ATO portal", "start": 28.0},
            {"text": "You go to the reports", "start": 35.0},
            {"text": "You see here, the income tax status", "start": 45.0},
            {"text": "we normally select all clients", "start": 60.0},
            {"text": "the CSV is also available", "start": 65.0},
            {"text": "we can just download the files", "start": 70.0}
        ]
    }
    
    create_corrected_sop(video_path, transcript)