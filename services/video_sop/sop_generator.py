#!/usr/bin/env python3
"""
SOP Generator using VLM for frame analysis and transcription integration
"""

import json
import requests
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import base64

class SOPGenerator:
    def __init__(self, vlm_url: str = "http://localhost:8000", 
                 transcription_url: str = "http://localhost:8001"):
        self.vlm_url = vlm_url
        self.transcription_url = transcription_url
        
    def switch_to_7b_model(self):
        """Switch VLM to use the 7B model for better accuracy"""
        try:
            response = requests.post(
                f"{self.vlm_url}/switch_model",
                json={"model_size": "7B"}
            )
            if response.status_code == 200:
                print("Switched to 7B VLM model")
                return True
        except Exception as e:
            print(f"Note: Could not switch to 7B model: {e}")
        return False
        
    def transcribe_audio(self, audio_path: str) -> Dict:
        """Send audio to transcription service"""
        with open(audio_path, 'rb') as f:
            files = {'file': (Path(audio_path).name, f, 'audio/mpeg')}
            data = {
                'enable_speaker_detection': 'true',
                'enable_corrections': 'true'
            }
            
            response = requests.post(
                f"{self.transcription_url}/transcribe",
                files=files,
                data=data
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Transcription error: {response.text}")
                return None
                
    def analyze_frame_with_vlm(self, frame_path: str, prompt: str = None) -> str:
        """Analyze a frame using VLM to understand what's happening"""
        if prompt is None:
            prompt = """Analyze this image and describe:
1. What action is being performed?
2. What UI elements or tools are visible?
3. What is the likely next step?
4. Any important details or warnings?

Provide a concise, instructional description suitable for an SOP."""

        with open(frame_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
            
        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                    ]
                }
            ],
            "temperature": 0.1,
            "max_tokens": 500
        }
        
        try:
            response = requests.post(
                f"{self.vlm_url}/api/v1/generate_unified",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('choices', [{}])[0].get('message', {}).get('content', '')
            else:
                print(f"VLM error: {response.text}")
                return ""
        except Exception as e:
            print(f"Error analyzing frame: {e}")
            return ""
            
    def correlate_transcript_with_frames(self, transcript: Dict, frames: List[Dict]) -> List[Dict]:
        """Match transcript segments with relevant frames"""
        correlated_steps = []
        
        # Get transcript segments
        segments = transcript.get('segments', [])
        if not segments and 'text' in transcript:
            # Create a single segment if no segments provided
            segments = [{'text': transcript['text'], 'start': 0, 'end': transcript.get('duration', 60)}]
            
        for i, segment in enumerate(segments):
            # Find the closest frame to this segment's timestamp
            segment_time = segment.get('start', i * 5)
            
            closest_frame = min(
                frames,
                key=lambda f: abs(f['timestamp'] - segment_time)
            )
            
            correlated_steps.append({
                'step_number': i + 1,
                'transcript': segment.get('text', ''),
                'timestamp': segment_time,
                'frame': closest_frame,
                'speaker': segment.get('speaker', 'Instructor')
            })
            
        return correlated_steps
        
    def generate_sop_steps(self, correlated_data: List[Dict]) -> List[Dict]:
        """Generate structured SOP steps from correlated data"""
        sop_steps = []
        
        for item in correlated_data:
            # Analyze the frame for this step
            frame_analysis = self.analyze_frame_with_vlm(
                item['frame']['filename'],
                f"Describe this step in a tutorial: {item['transcript']}"
            )
            
            # Combine transcript and visual analysis
            step = {
                'number': item['step_number'],
                'title': self._extract_step_title(item['transcript']),
                'instruction': item['transcript'],
                'visual_description': frame_analysis,
                'timestamp': f"{int(item['timestamp']//60):02d}:{int(item['timestamp']%60):02d}",
                'screenshot': item['frame']['filename'],
                'tips': self._extract_tips(frame_analysis),
                'warnings': self._extract_warnings(frame_analysis)
            }
            
            sop_steps.append(step)
            print(f"Generated step {step['number']}: {step['title']}")
            
        return sop_steps
        
    def _extract_step_title(self, text: str) -> str:
        """Extract a concise title from instruction text"""
        # Take first sentence or first 50 characters
        sentences = text.split('.')
        if sentences:
            title = sentences[0].strip()
            if len(title) > 50:
                title = title[:47] + "..."
            return title
        return text[:50] if len(text) > 50 else text
        
    def _extract_tips(self, analysis: str) -> List[str]:
        """Extract helpful tips from frame analysis"""
        tips = []
        
        # Look for tip indicators
        tip_keywords = ['tip:', 'note:', 'hint:', 'pro tip:', 'remember:']
        lines = analysis.lower().split('\n')
        
        for line in lines:
            for keyword in tip_keywords:
                if keyword in line:
                    tips.append(line.split(keyword)[-1].strip())
                    
        return tips
        
    def _extract_warnings(self, analysis: str) -> List[str]:
        """Extract warnings from frame analysis"""
        warnings = []
        
        # Look for warning indicators
        warning_keywords = ['warning:', 'caution:', 'important:', 'danger:', 'alert:']
        lines = analysis.lower().split('\n')
        
        for line in lines:
            for keyword in warning_keywords:
                if keyword in line:
                    warnings.append(line.split(keyword)[-1].strip())
                    
        return warnings
        
    def format_sop_document(self, title: str, steps: List[Dict], 
                           video_info: Dict = None) -> str:
        """Format the SOP as a markdown document"""
        
        sop = f"# {title}\n\n"
        sop += f"*Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n\n"
        
        if video_info:
            sop += "## Video Information\n"
            sop += f"- Duration: {video_info.get('duration', 0):.1f} seconds\n"
            sop += f"- Resolution: {video_info.get('width')}x{video_info.get('height')}\n\n"
            
        sop += "## Prerequisites\n"
        sop += "- [ ] Required tools and access ready\n"
        sop += "- [ ] Understanding of basic concepts\n\n"
        
        sop += "## Steps\n\n"
        
        for step in steps:
            sop += f"### Step {step['number']}: {step['title']}\n"
            sop += f"*Timestamp: {step['timestamp']}*\n\n"
            
            sop += f"**Instructions:**\n{step['instruction']}\n\n"
            
            if step.get('visual_description'):
                sop += f"**Visual Guide:**\n{step['visual_description']}\n\n"
                
            if step.get('screenshot'):
                sop += f"![Step {step['number']}]({step['screenshot']})\n\n"
                
            if step.get('tips'):
                sop += "**Tips:**\n"
                for tip in step['tips']:
                    sop += f"- 💡 {tip}\n"
                sop += "\n"
                
            if step.get('warnings'):
                sop += "**Warnings:**\n"
                for warning in step['warnings']:
                    sop += f"- ⚠️ {warning}\n"
                sop += "\n"
                
            sop += "---\n\n"
            
        sop += "## Summary\n"
        sop += f"This SOP contains {len(steps)} steps to complete the process.\n\n"
        
        sop += "## Notes\n"
        sop += "- Review each step carefully before proceeding\n"
        sop += "- Take screenshots if you encounter any issues\n"
        sop += "- Contact support if you need assistance\n"
        
        return sop
        
    def generate_sop_from_video(self, video_path: str, frames: List[Dict], 
                                audio_path: str = None, title: str = None) -> Dict:
        """Main method to generate complete SOP from video"""
        
        print("Starting SOP generation process...")
        
        # Switch to 7B model for better accuracy
        self.switch_to_7b_model()
        
        # Transcribe audio if provided
        transcript = None
        if audio_path:
            print("Transcribing audio...")
            transcript = self.transcribe_audio(audio_path)
            
        if not transcript:
            print("No transcript available, using visual analysis only")
            # Generate steps from frames only
            sop_steps = []
            for i, frame in enumerate(frames[:10]):  # Limit to 10 frames for testing
                analysis = self.analyze_frame_with_vlm(frame['filename'])
                sop_steps.append({
                    'number': i + 1,
                    'title': f"Step {i + 1}",
                    'instruction': analysis,
                    'visual_description': analysis,
                    'timestamp': f"{int(frame['timestamp']//60):02d}:{int(frame['timestamp']%60):02d}",
                    'screenshot': frame['filename'],
                    'tips': [],
                    'warnings': []
                })
        else:
            # Correlate transcript with frames
            print("Correlating transcript with frames...")
            correlated = self.correlate_transcript_with_frames(transcript, frames)
            
            # Generate structured steps
            print("Generating SOP steps...")
            sop_steps = self.generate_sop_steps(correlated)
            
        # Format as document
        if not title:
            title = Path(video_path).stem.replace('_', ' ').title()
            
        print("Formatting SOP document...")
        sop_document = self.format_sop_document(title, sop_steps)
        
        return {
            'title': title,
            'steps': sop_steps,
            'document': sop_document,
            'transcript': transcript,
            'frames_analyzed': len(frames)
        }


# Example usage
if __name__ == "__main__":
    generator = SOPGenerator()
    
    # Test with dummy data
    test_frames = [
        {'timestamp': 0, 'filename': 'frame_0.jpg'},
        {'timestamp': 5, 'filename': 'frame_1.jpg'},
        {'timestamp': 10, 'filename': 'frame_2.jpg'}
    ]
    
    result = generator.generate_sop_from_video(
        "test_video.mp4",
        test_frames,
        title="Test SOP Generation"
    )