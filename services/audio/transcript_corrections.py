#!/usr/bin/env python3
"""
Transcript Correction Module
Handles common transcription errors and domain-specific terminology
"""

import re
from typing import Dict, List, Tuple

class TranscriptCorrector:
    """
    Post-processing corrections for common transcription errors
    """
    
    def __init__(self):
        # Define correction mappings
        self.corrections = {
            # Names and proper nouns
            "Techie": "Teke",
            "techie": "Teke",
            "Stanley Ohm": "Stanley Ong",
            "stanley ohm": "Stanley Ong",
            
            # Organizations and acronyms
            "IPO": "ATO",
            "ipo": "ATO",
            "I.P.O": "ATO",
            "eye pee oh": "ATO",
            "ATL": "ATO",  # Another common misrecognition
            
            # Tax-specific terms
            "text agent": "tax agent",
            "text file number": "tax file number",
            "TFN": "TFN",  # Keep as is
            "super-guaranteed": "super guarantee",
            "SGC": "SGC",  # Super Guarantee Charge
            
            # Common Australian tax terms
            "FY20 tree": "FY2023",
            "FY 20 tree": "FY2023",
            "FY20tree": "FY2023",
            "FY 20 24": "FY2024",
            "FY2024": "FY2024",
            "airport 24": "April 2024",
            "Airport 24": "April 2024",
            
            # Business terms
            "plastic": "practice",  # Common in context of "tax practice"
            "op-yescent": "PAYG",  # Pay As You Go
            "payment summary": "payment summary",
            "income statement": "income statement",
            
            # Common phrases
            "single-part spay-room": "Single Touch Payroll",
            "STP": "STP",  # Single Touch Payroll
            "dock residency": "tax residency",
            "duck residency": "tax residency",
            "duck-gulagic": "tax",
            
            # Numbers and dates
            "17662.00": "17662",  # Agent number cleanup
            "September 17th": "17 September",
            "first of September": "1 September",
        }
        
        # Regex patterns for more complex corrections
        self.regex_corrections = [
            # Fix financial year formats
            (r"FY\s*20\s*(\d{2})", r"FY20\1"),
            (r"F\s*Y\s*(\d{4})", r"FY\1"),
            
            # Fix phone numbers
            (r"(\d{3}),?\s*(\d{3}),?\s*(\d{3})", r"\1-\2-\3"),
            
            # Fix dates
            (r"(\d{1,2})(st|nd|rd|th)\s+of\s+(\w+)", r"\1 \3"),
            
            # Fix currency amounts
            (r"\$(\d+),(\d{3})", r"$\1\2"),
        ]
        
        # Context-aware corrections (check surrounding words)
        self.context_corrections = [
            # If "agent" appears near these words, it's likely "tax agent"
            (["text", "agent"], "tax agent"),
            (["plastic", "mailbox"], "practice mailbox"),
            (["plastic", "number"], "practice number"),
        ]
    
    def correct_text(self, text: str) -> str:
        """
        Apply all corrections to the text
        """
        corrected = text
        
        # Apply simple replacements (case-insensitive)
        for wrong, right in self.corrections.items():
            # Use word boundaries to avoid partial replacements
            pattern = r'\b' + re.escape(wrong) + r'\b'
            corrected = re.sub(pattern, right, corrected, flags=re.IGNORECASE)
        
        # Apply regex corrections
        for pattern, replacement in self.regex_corrections:
            corrected = re.sub(pattern, replacement, corrected)
        
        # Apply context-aware corrections
        corrected = self.apply_context_corrections(corrected)
        
        return corrected
    
    def apply_context_corrections(self, text: str) -> str:
        """
        Apply corrections based on context
        """
        words = text.split()
        corrected_words = []
        i = 0
        
        while i < len(words):
            replaced = False
            
            # Check for multi-word patterns
            for pattern, replacement in self.context_corrections:
                if i + len(pattern) <= len(words):
                    # Check if the pattern matches
                    if all(words[i+j].lower() == pattern[j].lower() for j in range(len(pattern))):
                        corrected_words.append(replacement)
                        i += len(pattern)
                        replaced = True
                        break
            
            if not replaced:
                corrected_words.append(words[i])
                i += 1
        
        return ' '.join(corrected_words)
    
    def correct_segments(self, segments: List[Dict]) -> List[Dict]:
        """
        Correct transcript segments (with speaker labels)
        """
        corrected_segments = []
        
        for segment in segments:
            corrected_segment = segment.copy()
            
            # Correct the text
            if 'text' in corrected_segment:
                corrected_segment['text'] = self.correct_text(corrected_segment['text'])
            
            # Correct speaker names
            if 'speaker' in corrected_segment:
                speaker = corrected_segment['speaker']
                # Apply speaker corrections
                if speaker.lower() in ['techie', 'techie 2']:
                    corrected_segment['speaker'] = 'Teke'
                elif speaker.lower() in ['what', 'judy']:
                    corrected_segment['speaker'] = 'ATO Representative'
            
            corrected_segments.append(corrected_segment)
        
        return corrected_segments
    
    def get_correction_summary(self, original: str, corrected: str) -> List[Tuple[str, str]]:
        """
        Get a summary of what was corrected
        """
        corrections_made = []
        
        for wrong, right in self.corrections.items():
            if wrong.lower() in original.lower() and right in corrected:
                corrections_made.append((wrong, right))
        
        return corrections_made


class DomainSpecificCorrector(TranscriptCorrector):
    """
    Extended corrector for specific domains (tax, legal, medical, etc.)
    """
    
    def __init__(self, domain: str = "tax"):
        super().__init__()
        self.domain = domain
        
        if domain == "tax":
            self.add_tax_corrections()
        elif domain == "legal":
            self.add_legal_corrections()
        # Add more domains as needed
    
    def add_tax_corrections(self):
        """
        Add tax-specific corrections
        """
        tax_terms = {
            # Australian tax terms
            "GST": "GST",  # Goods and Services Tax
            "BAS": "BAS",  # Business Activity Statement
            "ABN": "ABN",  # Australian Business Number
            "PAYG": "PAYG",  # Pay As You Go
            "CGT": "CGT",  # Capital Gains Tax
            
            # Common misrecognitions
            "deductions": "deductions",
            "assessable income": "assessable income",
            "taxable income": "taxable income",
            "tax return": "tax return",
            "tax bracket": "tax bracket",
            "marginal tax rate": "marginal tax rate",
        }
        
        self.corrections.update(tax_terms)
    
    def add_legal_corrections(self):
        """
        Add legal-specific corrections
        """
        legal_terms = {
            "plaintiff": "plaintiff",
            "defendant": "defendant",
            "litigation": "litigation",
            # Add more legal terms
        }
        
        self.corrections.update(legal_terms)


# Convenience function for easy use
def correct_transcript(text: str, domain: str = "tax") -> str:
    """
    Correct a transcript with domain-specific corrections
    """
    corrector = DomainSpecificCorrector(domain)
    return corrector.correct_text(text)


def correct_transcript_segments(segments: List[Dict], domain: str = "tax") -> List[Dict]:
    """
    Correct transcript segments with domain-specific corrections
    """
    corrector = DomainSpecificCorrector(domain)
    return corrector.correct_segments(segments)


# Example usage
if __name__ == "__main__":
    # Test corrections
    test_texts = [
        "Techie speaking with the IPO about Stanley Ohm",
        "The text agent needs the TFN for FY20 tree",
        "Contact the plastic mailbox at 037, 046, 05",
        "The ATL won't process the op-yescent form",
        "Stanley Ohm received payment in airport 24",
    ]
    
    corrector = DomainSpecificCorrector("tax")
    
    print("Transcript Correction Examples:")
    print("=" * 60)
    
    for original in test_texts:
        corrected = corrector.correct_text(original)
        if original != corrected:
            print(f"Original:  {original}")
            print(f"Corrected: {corrected}")
            print()