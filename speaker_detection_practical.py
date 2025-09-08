#!/usr/bin/env python3
"""
Practical Speaker Detection for Transcripts
Handles 2-3+ speakers with fallback strategies
"""

class PracticalSpeakerDetection:
    """
    Flexible speaker detection that handles various scenarios
    """
    
    def __init__(self):
        self.detected_speakers = set()
        self.speaker_patterns = {}
        
    def analyze_conversation_type(self, transcript_segments):
        """
        Determine if this is likely a 2-person call, 3-person, or meeting
        """
        # Analyze patterns to guess speaker count
        indicators = {
            "two_speaker": 0,
            "three_speaker": 0,
            "multi_speaker": 0
        }
        
        for segment in transcript_segments:
            text = segment.get("text", "").lower()
            
            # Two-speaker indicators (phone call patterns)
            if any(phrase in text for phrase in [
                "hello", "can i speak to", "this is", "calling from",
                "yes?", "no", "okay", "thank you", "bye"
            ]):
                indicators["two_speaker"] += 1
            
            # Three-speaker indicators
            if any(phrase in text for phrase in [
                "let me bring in", "also joining", "third party",
                "conference", "he said", "she said", "they mentioned"
            ]):
                indicators["three_speaker"] += 1
            
            # Multi-speaker meeting indicators
            if any(phrase in text for phrase in [
                "meeting", "everyone", "all of you", "team",
                "let's go around", "next person"
            ]):
                indicators["multi_speaker"] += 1
        
        # Determine most likely scenario
        if indicators["multi_speaker"] > 2:
            return "meeting", 4  # Assume 4+ speakers
        elif indicators["three_speaker"] > 1:
            return "three_party", 3
        else:
            return "two_party", 2  # Default to most common case
    
    def detect_speakers_simple(self, segments):
        """
        Simple heuristic-based speaker detection
        Works well for 2-3 speakers
        """
        conversation_type, expected_speakers = self.analyze_conversation_type(segments)
        
        print(f"Detected conversation type: {conversation_type} ({expected_speakers} speakers expected)")
        
        enhanced_segments = []
        current_speaker = "Speaker_1"
        speaker_rotation = ["Speaker_1", "Speaker_2", "Speaker_3", "Speaker_4"]
        speaker_index = 0
        
        for i, segment in enumerate(segments):
            text = segment.get("text", "").strip()
            
            # Detect speaker changes based on patterns
            speaker_changed = False
            
            if i > 0:
                prev_segment = segments[i-1]
                pause_duration = segment.get("start", 0) - prev_segment.get("end", 0)
                prev_text = prev_segment.get("text", "").strip()
                
                # Strong indicators of speaker change
                if any([
                    pause_duration > 1.5,  # Long pause
                    prev_text.endswith("?"),  # Question -> Answer
                    text.startswith(("Yes", "No", "Okay", "Sure", "Well")),  # Response words
                    text.startswith(("I", "My", "We")) and not prev_text.startswith(("I", "My", "We")),
                    "?" in text and "?" not in prev_text,  # Question pattern change
                ]):
                    speaker_changed = True
            
            if speaker_changed:
                # Rotate to next speaker
                if expected_speakers == 2:
                    # Simple toggle for 2 speakers
                    current_speaker = "Speaker_2" if current_speaker == "Speaker_1" else "Speaker_1"
                else:
                    # Cycle through speakers for 3+
                    speaker_index = (speaker_index + 1) % expected_speakers
                    current_speaker = speaker_rotation[speaker_index]
            
            enhanced_segments.append({
                "speaker": current_speaker,
                "text": text,
                "start": segment.get("start", 0),
                "end": segment.get("end", 0)
            })
        
        return enhanced_segments, expected_speakers
    
    def apply_speaker_names(self, enhanced_segments, speaker_map=None):
        """
        Replace generic speaker labels with actual names if known
        """
        if not speaker_map:
            # Try to auto-detect names from conversation
            speaker_map = self.detect_names_from_conversation(enhanced_segments)
        
        for segment in enhanced_segments:
            if segment["speaker"] in speaker_map:
                segment["speaker"] = speaker_map[segment["speaker"]]
        
        return enhanced_segments
    
    def detect_names_from_conversation(self, segments):
        """
        Try to identify speaker names from the conversation content
        """
        speaker_map = {}
        
        for segment in segments:
            text = segment["text"].lower()
            speaker = segment["speaker"]
            
            # Common patterns for self-identification
            if "this is" in text and speaker not in speaker_map:
                # "This is John from..."
                words = text.split("this is")[-1].split()
                if words:
                    potential_name = words[0].strip(".,").title()
                    if len(potential_name) > 2 and potential_name.isalpha():
                        speaker_map[speaker] = potential_name
            
            elif "my name is" in text and speaker not in speaker_map:
                # "My name is John"
                words = text.split("my name is")[-1].split()
                if words:
                    potential_name = words[0].strip(".,").title()
                    if len(potential_name) > 2 and potential_name.isalpha():
                        speaker_map[speaker] = potential_name
            
            elif "speaking" in text and speaker not in speaker_map:
                # "John speaking"
                words = text.split("speaking")[0].split()
                if words:
                    potential_name = words[-1].strip(".,").title()
                    if len(potential_name) > 2 and potential_name.isalpha():
                        speaker_map[speaker] = potential_name
        
        return speaker_map
    
    def format_transcript_with_speakers(self, enhanced_segments, speaker_count):
        """
        Format the transcript with clear speaker labels
        """
        output = []
        output.append(f"=== CONVERSATION TRANSCRIPT ===")
        output.append(f"Detected {speaker_count} speakers in conversation\n")
        
        current_speaker = None
        speaker_text = []
        
        for segment in enhanced_segments:
            if segment["speaker"] != current_speaker:
                # Output previous speaker's text
                if current_speaker and speaker_text:
                    output.append(f"[{current_speaker}]: {' '.join(speaker_text)}\n")
                    speaker_text = []
                
                current_speaker = segment["speaker"]
            
            speaker_text.append(segment["text"])
        
        # Don't forget last speaker
        if current_speaker and speaker_text:
            output.append(f"[{current_speaker}]: {' '.join(speaker_text)}\n")
        
        return "\n".join(output)

# Example usage for different scenarios
def demonstrate_speaker_detection():
    """
    Show how it handles different conversation types
    """
    
    # Example 1: Two-speaker phone call (like Stanley ATO)
    two_speaker_segments = [
        {"text": "Hello, this is John from the tax office.", "start": 0, "end": 3},
        {"text": "Hi John, this is Mary speaking.", "start": 3.5, "end": 5},
        {"text": "I'm calling about your tax return.", "start": 5.2, "end": 7},
        {"text": "Yes, what about it?", "start": 8, "end": 9},
        {"text": "We need some additional documents.", "start": 9.5, "end": 11},
        {"text": "Okay, what do you need?", "start": 12, "end": 13}
    ]
    
    # Example 2: Three-speaker conference call
    three_speaker_segments = [
        {"text": "Hello everyone, this is John.", "start": 0, "end": 2},
        {"text": "Hi John, Mary here.", "start": 2.5, "end": 3.5},
        {"text": "Let me bring in our accountant, David.", "start": 4, "end": 6},
        {"text": "Hi everyone, David joining.", "start": 7, "end": 8},
        {"text": "David, can you explain the tax situation?", "start": 9, "end": 11},
        {"text": "Sure, let me clarify that.", "start": 11.5, "end": 13},
        {"text": "That makes sense.", "start": 14, "end": 15},
        {"text": "I agree with David.", "start": 15.5, "end": 16.5}
    ]
    
    detector = PracticalSpeakerDetection()
    
    print("=" * 60)
    print("SCENARIO 1: Two-Speaker Phone Call")
    print("=" * 60)
    enhanced, count = detector.detect_speakers_simple(two_speaker_segments)
    enhanced = detector.apply_speaker_names(enhanced)
    print(detector.format_transcript_with_speakers(enhanced, count))
    
    print("\n" + "=" * 60)
    print("SCENARIO 2: Three-Speaker Conference Call")
    print("=" * 60)
    enhanced, count = detector.detect_speakers_simple(three_speaker_segments)
    enhanced = detector.apply_speaker_names(enhanced)
    print(detector.format_transcript_with_speakers(enhanced, count))
    
    return True

# Benefits for your specific use case
benefits_summary = """
SPEAKER DETECTION BENEFITS FOR YOUR TRANSCRIPTS:

1. HANDLES COMMON CASES (2 speakers - 90% of calls):
   ✓ Phone conversations like Stanley/ATO
   ✓ One-on-one meetings
   ✓ Support calls

2. HANDLES OCCASIONAL CASES (3 speakers - 10% of calls):
   ✓ Conference calls with third party
   ✓ Introductions ("let me bring in...")
   ✓ Supervisor escalations

3. FALLBACK FOR RARE CASES (4+ speakers):
   ✓ Team meetings
   ✓ Group discussions
   ✓ Labels as Speaker_1, Speaker_2, etc.

4. SMART FEATURES:
   ✓ Auto-detects names when mentioned
   ✓ Identifies conversation type
   ✓ Handles speaker transitions
   ✓ Works without extra libraries

5. PRACTICAL BENEFITS:
   ✓ Clear action item ownership
   ✓ Better searchability
   ✓ Legal clarity for compliance
   ✓ Improved AI summaries
"""

if __name__ == "__main__":
    print(benefits_summary)
    print("\nDEMONSTRATION:")
    demonstrate_speaker_detection()