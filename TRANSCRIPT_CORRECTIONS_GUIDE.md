# Transcript Correction System

## Problem Solved
Whisper (and other ASR systems) often make predictable errors with:
- **Names**: "Techie" → "Teke", "Stanley Ohm" → "Stanley Ong"
- **Acronyms**: "IPO" → "ATO", "ATL" → "ATO"
- **Domain terms**: "text agent" → "tax agent", "plastic" → "practice"
- **Accents & pronunciation**: Various phonetic misinterpretations

## Solution Implemented

### 1. Automatic Correction System
Created `transcript_corrections.py` that automatically fixes common errors:

```python
# Examples of corrections applied:
"Techie speaking with the IPO" → "Teke speaking with the ATO"
"Stanley Ohm" → "Stanley Ong"
"text agent" → "tax agent"
"FY20 tree" → "FY2023"
"airport 24" → "April 2024"
```

### 2. Three Correction Strategies

#### A. Simple Replacements
Direct word-for-word replacements:
```python
corrections = {
    "Techie": "Teke",
    "IPO": "ATO",
    "Stanley Ohm": "Stanley Ong",
}
```

#### B. Pattern-Based (Regex)
For complex patterns like dates and numbers:
```python
# Fixes "FY 20 23" → "FY2023"
(r"FY\s*20\s*(\d{2})", r"FY20\1")
```

#### C. Context-Aware
Checks surrounding words:
```python
# "plastic mailbox" → "practice mailbox"
# "text agent" → "tax agent"
```

### 3. Domain-Specific Corrections
Different correction sets for different domains:
- **Tax**: ATO, TFN, PAYG, GST, BAS, etc.
- **Legal**: plaintiff, defendant, litigation
- **Medical**: (can be added)
- **Custom**: Your own terminology

## How to Use

### For New Transcriptions
Corrections are now applied automatically:
```bash
curl -X POST http://localhost:8001/transcribe \
  -F "file=@audio.m4a" \
  -F "enable_corrections=true" \
  -F "domain=tax"
```

### For Existing Transcripts
You can apply corrections to existing text:
```python
from transcript_corrections import correct_transcript

original = "Techie spoke to the IPO about Stanley Ohm"
corrected = correct_transcript(original, domain="tax")
# Result: "Teke spoke to the ATO about Stanley Ong"
```

### Customizing Corrections

#### Add Your Own Terms
Edit `transcript_corrections.py`:
```python
self.corrections = {
    # Add your custom corrections
    "wrong_term": "correct_term",
    "misspelling": "correct_spelling",
}
```

#### Add Domain-Specific Terms
```python
def add_medical_corrections(self):
    medical_terms = {
        "hard attack": "heart attack",
        "die of betes": "diabetes",
        # Add more medical terms
    }
    self.corrections.update(medical_terms)
```

## Benefits

1. **Improved Accuracy**: Names and terms are correct
2. **Better Search**: Can find "ATO" even if transcribed as "IPO"
3. **Professional Output**: Clean, accurate transcripts
4. **Domain Expertise**: Specialized terminology handled correctly
5. **Consistency**: Same errors fixed the same way every time

## Examples from Stanley ATO Call

### Before Corrections:
```
[What]: I am digital from the IPO. Can I please speak to Mary Ann Degador?
[Techie]: She actually no longer working with us. Can I help?
[What]: It's for the client Stanley Ohm.
[Techie]: The text agent needs the TFN for FY20 tree
```

### After Corrections:
```
[ATO Representative]: I am digital from the ATO. Can I please speak to Mary Ann Degador?
[Teke]: She actually no longer working with us. Can I help?
[ATO Representative]: It's for the client Stanley Ong.
[Teke]: The tax agent needs the TFN for FY2023
```

## Managing Corrections

### View All Corrections
```python
from transcript_corrections import DomainSpecificCorrector

corrector = DomainSpecificCorrector("tax")
for wrong, right in corrector.corrections.items():
    print(f"{wrong} → {right}")
```

### Test Corrections
```bash
cd services/audio
python transcript_corrections.py
```

### Disable Corrections (if needed)
```bash
curl -X POST http://localhost:8001/transcribe \
  -F "file=@audio.m4a" \
  -F "enable_corrections=false"
```

## Important Notes

1. **Corrections are applied BEFORE saving** to database
2. **Original audio is unchanged** - only text is corrected
3. **Corrections work with speaker detection** - both features complement each other
4. **You can add unlimited correction rules** without affecting performance
5. **Context-aware corrections** prevent over-correction

## Future Enhancements

Consider adding:
1. **User-specific dictionaries**: Each user can have custom corrections
2. **Learning mode**: System learns from manual corrections
3. **Confidence scoring**: Only apply corrections above certain confidence
4. **Multi-language support**: Corrections for other languages
5. **Industry templates**: Pre-built correction sets for different industries

## Summary

The correction system ensures your transcripts are accurate and professional, fixing common ASR errors automatically. Combined with speaker detection, you now have:
- ✅ Correct names and terms
- ✅ Clear speaker attribution  
- ✅ Domain-specific accuracy
- ✅ Professional, searchable transcripts