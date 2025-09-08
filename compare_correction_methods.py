#!/usr/bin/env python3
"""
Compare different transcript correction methods:
1. Rule-based (hardcoded corrections)
2. LLM-based (using local VLM)
3. Hybrid (LLM with rule-based fallback)
"""

import time
import json
from typing import Dict, List, Tuple
from services.audio.transcript_corrections import DomainSpecificCorrector
from services.audio.llm_transcript_corrector import SmartTranscriptCorrector

# Test cases with expected corrections
TEST_CASES = [
    # (original, expected_correction, domain)
    ("I am digital from the IPO", "I am digital from the ATO", "tax"),
    ("Techie speaking with the client", "Teke speaking with the client", "tax"),
    ("Stanley Ohm needs help", "Stanley Ong needs help", "tax"),
    ("The text agent filed the form", "The tax agent filed the form", "tax"),
    ("Contact the plastic mailbox", "Contact the practice mailbox", "tax"),
    ("Payment for FY20 tree", "Payment for FY2023", "tax"),
    ("Received in airport 24", "Received in April 2024", "tax"),
    ("The op-yescent form is ready", "The PAYG form is ready", "tax"),
    ("Meeting with the ATL officer", "Meeting with the ATO officer", "tax"),
    ("duck residency status", "tax residency status", "tax"),
]

# Longer text samples for realistic testing
LONG_SAMPLES = [
    """Techie is speaking with someone from the IPO about Stanley Ohm's case. 
    The text agent needs to review the FY20 tree returns and contact the plastic 
    to confirm the op-yescent details. Payment was received in airport 24.""",
    
    """I am digital from the IPO. Can I please speak to Mary Ann Degador? 
    She actually no longer working with us. Can I help? Could she lot an objection 
    for her client? Oh yeah, which client is it? Can I help? It's for Stanley Ohm.""",
]

class CorrectionComparison:
    """Compare different correction methods"""
    
    def __init__(self):
        self.rule_corrector = DomainSpecificCorrector("tax")
        self.llm_corrector = SmartTranscriptCorrector("http://localhost:8000")
        
    def calculate_accuracy(self, corrected: str, expected: str) -> float:
        """Calculate accuracy as percentage of matching words"""
        corrected_words = corrected.lower().split()
        expected_words = expected.lower().split()
        
        if len(expected_words) == 0:
            return 0.0
            
        matches = sum(1 for c, e in zip(corrected_words, expected_words) if c == e)
        return (matches / len(expected_words)) * 100
    
    def measure_performance(self, text: str, method: str, domain: str = "tax") -> Tuple[str, float]:
        """Measure correction performance and time"""
        start_time = time.time()
        
        if method == "rule":
            corrected = self.rule_corrector.correct_text(text)
        elif method == "llm":
            corrected = self.llm_corrector.correct(text, domain, use_llm=True)
        elif method == "hybrid":
            corrected = self.llm_corrector.correct(text, domain, use_llm=True)
        else:
            corrected = text
            
        elapsed = time.time() - start_time
        return corrected, elapsed
    
    def run_comparison(self):
        """Run comprehensive comparison"""
        print("=" * 80)
        print("TRANSCRIPT CORRECTION METHOD COMPARISON")
        print("=" * 80)
        print()
        
        results = {
            "rule": {"correct": 0, "total": 0, "time": 0},
            "llm": {"correct": 0, "total": 0, "time": 0},
            "hybrid": {"correct": 0, "total": 0, "time": 0}
        }
        
        # Test short samples
        print("SHORT SAMPLE TESTS:")
        print("-" * 80)
        
        for original, expected, domain in TEST_CASES:
            print(f"\nOriginal:  {original}")
            print(f"Expected:  {expected}")
            print()
            
            # Test each method
            for method in ["rule", "llm", "hybrid"]:
                corrected, elapsed = self.measure_performance(original, method, domain)
                accuracy = self.calculate_accuracy(corrected, expected)
                
                # Update results
                results[method]["total"] += 1
                if accuracy >= 90:  # Consider 90%+ as correct
                    results[method]["correct"] += 1
                results[method]["time"] += elapsed
                
                # Display results
                symbol = "✓" if accuracy >= 90 else "✗"
                print(f"{method:6} {symbol}: {corrected}")
                print(f"           Accuracy: {accuracy:.1f}%, Time: {elapsed:.3f}s")
        
        print()
        print("=" * 80)
        print("LONG SAMPLE TESTS:")
        print("-" * 80)
        
        for i, sample in enumerate(LONG_SAMPLES, 1):
            print(f"\nSample {i} ({len(sample)} chars):")
            print(f"Original: {sample[:100]}...")
            print()
            
            for method in ["rule", "llm", "hybrid"]:
                corrected, elapsed = self.measure_performance(sample, method, "tax")
                print(f"{method:6}: {corrected[:100]}...")
                print(f"         Time: {elapsed:.3f}s")
                results[method]["time"] += elapsed
        
        # Summary
        print()
        print("=" * 80)
        print("SUMMARY RESULTS:")
        print("-" * 80)
        
        print(f"{'Method':<10} {'Accuracy':<15} {'Avg Time':<15} {'Total Time':<15}")
        print("-" * 60)
        
        for method in ["rule", "llm", "hybrid"]:
            r = results[method]
            accuracy = (r["correct"] / r["total"] * 100) if r["total"] > 0 else 0
            avg_time = r["time"] / (r["total"] + len(LONG_SAMPLES))
            
            print(f"{method:<10} {accuracy:>6.1f}% ({r['correct']}/{r['total']}) "
                  f"{avg_time:>8.3f}s      {r['time']:>8.3f}s")
        
        print()
        print("=" * 80)
        print("ANALYSIS:")
        print("-" * 80)
        
        # Determine best method
        best_accuracy = max(results.values(), key=lambda x: x["correct"] / x["total"] if x["total"] > 0 else 0)
        fastest = min(results.values(), key=lambda x: x["time"])
        
        print("PROS AND CONS:")
        print()
        print("Rule-based:")
        print("  ✓ Fast and consistent")
        print("  ✓ No external dependencies")
        print("  ✓ Predictable corrections")
        print("  ✗ Limited to predefined rules")
        print("  ✗ Can't handle context or variations")
        print()
        print("LLM-based:")
        print("  ✓ Context-aware corrections")
        print("  ✓ Handles variations and unknowns")
        print("  ✓ Can learn and improve")
        print("  ✗ Slower (network calls)")
        print("  ✗ Requires VLM server running")
        print("  ✗ May be inconsistent")
        print()
        print("Hybrid:")
        print("  ✓ Best of both worlds")
        print("  ✓ LLM intelligence with rule fallback")
        print("  ✓ Ensures critical corrections")
        print("  ✗ Most complex implementation")
        print("  ✗ Slightly slower than pure rules")
        
        return results

def main():
    """Run the comparison"""
    
    print("Starting correction method comparison...")
    print("Make sure the VLM server is running on http://localhost:8000")
    print()
    
    comparison = CorrectionComparison()
    
    try:
        results = comparison.run_comparison()
        
        # Save results
        with open("correction_comparison_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print()
        print("Results saved to correction_comparison_results.json")
        
    except Exception as e:
        print(f"Error during comparison: {e}")
        print("\nNote: Make sure the VLM server is running for LLM-based corrections")
        print("Falling back to rule-based comparison only...")
        
        # Test rule-based only
        corrector = DomainSpecificCorrector("tax")
        print("\nRule-based corrections:")
        for original, expected, _ in TEST_CASES[:5]:
            corrected = corrector.correct_text(original)
            print(f"  {original} → {corrected}")

if __name__ == "__main__":
    main()