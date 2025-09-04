#!/usr/bin/env python3
"""Process selected important large files with truncation"""

import subprocess
import sys
from pathlib import Path

# Selected important files to process
IMPORTANT_FILES = [
    # Business/Pitch calls (likely important)
    "Joe Wong Pitchcall.m4a",  # ~81 min
    "Dhanuka Senaratne Booking Call 14 August 2023.m4a",  # ~39 min
    "conversation with David Zimmerman.m4a",  # ~37 min
    "James Ko.m4a",  # ~42 min
    "John Lu - Crypto.m4a",  # ~42 min
    # One of the very long recordings to test
    "GregTeke.mp3",  # ~267 min - will truncate to 60 min
]

def main():
    base_path = Path("/mnt/c/Users/tekee.DESKTOP-VMDIEU8/OneDrive/Documents/Sound recordings")
    
    print("=" * 70)
    print("PROCESSING SELECTED IMPORTANT FILES")
    print("=" * 70)
    print(f"Will process {len(IMPORTANT_FILES)} selected files")
    print("Truncating files >60 minutes to first hour only\n")
    
    success_count = 0
    failed_files = []
    
    for i, filename in enumerate(IMPORTANT_FILES, 1):
        file_path = base_path / filename
        
        print(f"\n[{i}/{len(IMPORTANT_FILES)}] {filename}")
        print("-" * 50)
        
        if not file_path.exists():
            print(f"❌ File not found, skipping")
            failed_files.append(filename)
            continue
        
        # Run the transcribe_truncated script
        cmd = [
            "python3", "transcribe_truncated.py",
            "--file", str(file_path),
            "--duration", "60",
            "--model", "base"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0 and "Processing complete!" in result.stdout:
                print("✅ Successfully processed!")
                success_count += 1
                
                # Extract transcript ID
                for line in result.stdout.split('\n'):
                    if "Transcript ID:" in line:
                        print(f"   {line.strip()}")
            else:
                print("❌ Processing failed")
                failed_files.append(filename)
                if result.stderr:
                    print(f"   Error: {result.stderr[:200]}")
        
        except subprocess.TimeoutExpired:
            print("❌ Processing timed out (>10 minutes)")
            failed_files.append(filename)
        except Exception as e:
            print(f"❌ Error: {e}")
            failed_files.append(filename)
    
    # Summary
    print("\n" + "=" * 70)
    print("PROCESSING COMPLETE")
    print("=" * 70)
    print(f"✅ Successfully processed: {success_count}/{len(IMPORTANT_FILES)}")
    
    if failed_files:
        print(f"❌ Failed files ({len(failed_files)}):")
        for f in failed_files:
            print(f"   - {f}")
    
    print("\n🔍 All successful transcripts are now searchable at:")
    print("   http://localhost:8002/search.html")
    
    print("\n💡 Next steps:")
    print("1. Review transcripts of business calls for important information")
    print("2. Search for specific topics across all transcripts")
    print("3. Process additional files if needed with:")
    print("   python3 transcribe_truncated.py --file '<path>'")

if __name__ == "__main__":
    main()