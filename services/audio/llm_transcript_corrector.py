#!/usr/bin/env python3
"""
LLM-based Transcript Correction Module
Uses local VLM to intelligently correct transcription errors
"""

import json
import requests
import logging
from typing import Dict, List, Optional, Tuple
import re

logger = logging.getLogger(__name__)

class LLMTranscriptCorrector:
    """
    Uses local LLM to intelligently correct transcription errors
    """
    
    def __init__(self, vlm_url: str = "http://localhost:8000", context_info: Dict = None):
        self.vlm_url = vlm_url
        self.context_info = context_info or {}
        
    def correct_with_llm(self, text: str, domain: str = "tax") -> str:
        """
        Use LLM to intelligently correct transcription errors
        """
        
        # Build context-aware prompt
        prompt = self._build_correction_prompt(text, domain)
        
        try:
            # Call local VLM
            response = requests.post(
                f"{self.vlm_url}/api/v1/generate",
                json={
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a transcript correction assistant. Fix transcription errors while preserving the original meaning. Only output the corrected text, nothing else."
                        },
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    "temperature": 0.1,  # Low temperature for consistency
                    "max_tokens": len(text) * 2  # Allow some expansion
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                corrected = result.get('response', text)
                logger.info("LLM correction successful")
                return corrected.strip()
            else:
                logger.warning(f"LLM correction failed: {response.status_code}")
                return text
                
        except Exception as e:
            logger.error(f"LLM correction error: {e}")
            return text
    
    def _build_correction_prompt(self, text: str, domain: str) -> str:
        """
        Build a context-aware prompt for corrections
        """
        
        domain_contexts = {
            "tax": """
Context: This is a transcript of a tax-related conversation, likely with the Australian Tax Office (ATO).
Common corrections needed:
- IPO/I.P.O/eye pee oh → ATO (Australian Tax Office)
- text agent → tax agent
- plastic → practice (as in tax practice)
- FY20 tree → FY2023
- Names: Techie → Teke, Stanley Ohm → Stanley Ong
- Tax terms: TFN (Tax File Number), PAYG, GST, BAS
""",
            "legal": """
Context: This is a legal transcript.
Focus on legal terminology, case names, and formal language.
""",
            "medical": """
Context: This is a medical transcript.
Focus on medical terminology, drug names, and procedures.
""",
            "general": """
Context: General conversation transcript.
Focus on common names, places, and standard English.
"""
        }
        
        context = domain_contexts.get(domain, domain_contexts["general"])
        
        # Add any known context from previous conversations
        if self.context_info:
            context += f"\nAdditional context:\n"
            if self.context_info.get("speakers"):
                context += f"- Speakers: {', '.join(self.context_info['speakers'])}\n"
            if self.context_info.get("topic"):
                context += f"- Topic: {self.context_info['topic']}\n"
            if self.context_info.get("company"):
                context += f"- Company/Organization: {self.context_info['company']}\n"
        
        prompt = f"""{context}

Please correct the following transcript segment, fixing any obvious transcription errors:

"{text}"

Corrected version:"""
        
        return prompt
    
    def correct_segments_batch(self, segments: List[Dict], domain: str = "tax") -> List[Dict]:
        """
        Correct multiple segments efficiently using batch processing
        """
        
        # Group segments into reasonable batches
        batch_size = 10  # Process 10 segments at a time
        corrected_segments = []
        
        for i in range(0, len(segments), batch_size):
            batch = segments[i:i+batch_size]
            
            # Combine batch text
            combined_text = "\n---\n".join([
                f"[{seg.get('speaker', 'Unknown')}]: {seg.get('text', '')}"
                for seg in batch
            ])
            
            # Get corrections
            corrected_text = self.correct_with_llm(combined_text, domain)
            
            # Split back into segments
            corrected_parts = corrected_text.split("\n---\n")
            
            for j, seg in enumerate(batch):
                corrected_seg = seg.copy()
                if j < len(corrected_parts):
                    # Extract speaker and text from corrected part
                    match = re.match(r'\[(.*?)\]:\s*(.*)', corrected_parts[j])
                    if match:
                        corrected_seg['speaker'] = match.group(1)
                        corrected_seg['text'] = match.group(2)
                    else:
                        corrected_seg['text'] = corrected_parts[j]
                
                corrected_segments.append(corrected_seg)
        
        return corrected_segments
    
    def learn_from_feedback(self, original: str, corrected: str, domain: str = "tax"):
        """
        Learn from user corrections (store for future context)
        """
        # This could be extended to save corrections to a database
        # for improving future corrections
        
        logger.info(f"Learning from correction: '{original}' -> '{corrected}'")
        
        # Extract potential corrections
        if original != corrected:
            # Could save to a corrections database
            pass


class SmartTranscriptCorrector:
    """
    Hybrid approach: Use LLM with fallback to rule-based corrections
    """
    
    def __init__(self, vlm_url: str = "http://localhost:8000"):
        self.llm_corrector = LLMTranscriptCorrector(vlm_url)
        
        # Keep some critical corrections as fallback
        self.critical_corrections = {
            "IPO": "ATO",
            "I.P.O": "ATO",
            "eye pee oh": "ATO",
        }
    
    def correct(self, text: str, domain: str = "tax", use_llm: bool = True) -> str:
        """
        Correct transcript using LLM with fallback
        """
        
        if use_llm:
            # Try LLM first
            corrected = self.llm_corrector.correct_with_llm(text, domain)
            
            # Apply critical corrections if LLM missed them
            for wrong, right in self.critical_corrections.items():
                pattern = r'\b' + re.escape(wrong) + r'\b'
                corrected = re.sub(pattern, right, corrected, flags=re.IGNORECASE)
            
            return corrected
        else:
            # Fallback to simple replacements
            corrected = text
            for wrong, right in self.critical_corrections.items():
                pattern = r'\b' + re.escape(wrong) + r'\b'
                corrected = re.sub(pattern, right, corrected, flags=re.IGNORECASE)
            return corrected
    
    def correct_with_context(self, text: str, context: Dict, domain: str = "tax") -> str:
        """
        Correct with additional context information
        """
        self.llm_corrector.context_info = context
        return self.correct(text, domain)


# Example prompts for different correction scenarios
CORRECTION_PROMPTS = {
    "names": """
You are correcting a transcript where names may be misspelled.
Known names in this conversation: {known_names}
Please correct any misspelled names.
""",
    
    "acronyms": """
You are correcting a transcript with organization acronyms.
This is a {domain} conversation. Common acronyms:
- ATO (Australian Tax Office) - may be transcribed as IPO, I.P.O, etc.
- TFN (Tax File Number)
- PAYG (Pay As You Go)
Please correct any misrecognized acronyms.
""",
    
    "technical": """
You are correcting a technical transcript in the {domain} domain.
Focus on correcting technical terminology while preserving the speaker's intent.
""",
    
    "conversational": """
You are correcting a conversational transcript between {speakers}.
Fix obvious transcription errors while maintaining natural speech patterns.
Don't over-formalize casual speech.
"""
}


def create_smart_corrector(vlm_url: str = "http://localhost:8000") -> SmartTranscriptCorrector:
    """
    Factory function to create a smart corrector
    """
    return SmartTranscriptCorrector(vlm_url)


# Test the LLM corrector
if __name__ == "__main__":
    # Test examples
    test_cases = [
        ("I am from the IPO calling about Stanley Ohm", "tax"),
        ("The text agent needs the TFN", "tax"),
        ("Contact the plastic mailbox", "tax"),
        ("We need to discuss the op-yescent form", "tax"),
    ]
    
    print("Testing LLM-based Transcript Correction")
    print("=" * 60)
    
    corrector = SmartTranscriptCorrector()
    
    for original, domain in test_cases:
        print(f"\nOriginal:  {original}")
        
        # Try LLM correction
        corrected = corrector.correct(original, domain, use_llm=True)
        print(f"LLM:       {corrected}")
        
        # Fallback correction
        fallback = corrector.correct(original, domain, use_llm=False)
        print(f"Fallback:  {fallback}")
    
    print("\n" + "=" * 60)
    print("With context:")
    
    # Test with context
    context = {
        "speakers": ["Teke", "ATO Representative"],
        "topic": "Tax objection for Stanley Ong",
        "company": "Australian Tax Office"
    }
    
    text = "Techie is speaking with someone from the IPO about Stanley Ohm's case"
    corrected = corrector.correct_with_context(text, context, "tax")
    print(f"\nOriginal:  {text}")
    print(f"Corrected: {corrected}")