#!/usr/bin/env python3
"""Monitor batch transcription progress"""

import time
import re
from pathlib import Path

def monitor_progress():
    log_file = Path("batch_transcribe.log")
    
    if not log_file.exists():
        print("❌ No transcription log found. Is batch transcription running?")
        return
    
    print("📊 TRANSCRIPTION PROGRESS MONITOR")
    print("=" * 60)
    
    while True:
        try:
            # Read last lines of log
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # Find progress indicators
            progress = None
            current_file = None
            stats = {}
            
            for line in lines:
                # Look for progress marker [X/Y]
                match = re.search(r'\[(\d+)/(\d+)\]', line)
                if match:
                    progress = (int(match.group(1)), int(match.group(2)))
                    current_file = line.strip()
                
                # Look for summary stats
                if "Successfully transcribed:" in line:
                    stats['success'] = re.search(r'(\d+)', line).group(1)
                elif "Skipped (existing):" in line:
                    stats['skipped'] = re.search(r'(\d+)', line).group(1)
                elif "Skipped (too large):" in line:
                    stats['large'] = re.search(r'(\d+)', line).group(1)
                elif "Failed:" in line:
                    stats['failed'] = re.search(r'(\d+)', line).group(1)
            
            # Display current status
            if progress:
                current, total = progress
                percentage = (current / total) * 100
                
                print(f"\r⏳ Progress: [{current}/{total}] ({percentage:.1f}%)", end="")
                
                # Estimate time remaining
                if current > 5:  # After a few files, estimate
                    avg_time_per_file = 15  # seconds, rough estimate
                    remaining = total - current
                    eta_seconds = remaining * avg_time_per_file
                    eta_minutes = eta_seconds / 60
                    
                    if eta_minutes < 60:
                        print(f" - ETA: ~{eta_minutes:.0f} minutes", end="")
                    else:
                        eta_hours = eta_minutes / 60
                        print(f" - ETA: ~{eta_hours:.1f} hours", end="")
                
                if current_file and len(current_file) < 100:
                    print(f"\n   Current: {current_file[:80]}", end="")
            
            # Check if completed
            if "BATCH PROCESSING COMPLETE" in ''.join(lines[-20:]):
                print("\n\n✅ TRANSCRIPTION COMPLETE!")
                if stats:
                    print(f"   Success: {stats.get('success', '?')}")
                    print(f"   Skipped: {stats.get('skipped', '?')}")
                    print(f"   Failed: {stats.get('failed', '?')}")
                break
            
            time.sleep(5)  # Check every 5 seconds
            
        except KeyboardInterrupt:
            print("\n\n👋 Monitoring stopped. Transcription continues in background.")
            break
        except Exception as e:
            print(f"\n⚠️ Error reading log: {e}")
            break

if __name__ == "__main__":
    monitor_progress()