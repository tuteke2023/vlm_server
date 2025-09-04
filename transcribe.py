#!/usr/bin/env python3
"""
User-friendly transcription CLI with options
"""

import argparse
import requests
import json
from pathlib import Path
import sys

def transcribe_audio(file_path, speaker_detection=None, corrections=True, domain="general", save=True):
    """
    Transcribe audio with configurable options
    """
    
    # Convert Windows path if needed
    if file_path.startswith("C:\\") or file_path.startswith("c:\\"):
        file_path = file_path.replace("C:\\", "/mnt/c/").replace("c:\\", "/mnt/c/")
        file_path = file_path.replace("\\", "/")
    
    # Check file exists
    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        return None
    
    file_size_mb = Path(file_path).stat().st_size / (1024 * 1024)
    
    print("=" * 70)
    print("AUDIO TRANSCRIPTION SERVICE")
    print("=" * 70)
    print(f"📁 File: {Path(file_path).name}")
    print(f"📊 Size: {file_size_mb:.1f} MB")
    print("-" * 70)
    
    # Interactive mode if speaker_detection not specified
    if speaker_detection is None:
        print("\n🎤 SPEAKER DETECTION")
        print("Identify different speakers in the audio (useful for conversations)")
        choice = input("Enable speaker detection? (y/n) [y]: ").strip().lower()
        speaker_detection = choice != 'n'
    
    print("\n⚙️  Settings:")
    print(f"  • Speaker Detection: {'✓ Enabled' if speaker_detection else '✗ Disabled'}")
    print(f"  • Auto-Corrections: {'✓ Enabled' if corrections else '✗ Disabled'}")
    print(f"  • Domain: {domain}")
    print(f"  • Save to Database: {'✓ Yes' if save else '✗ No'}")
    
    # Confirm
    if input("\nProceed with transcription? (y/n) [y]: ").strip().lower() == 'n':
        print("Cancelled.")
        return None
    
    print("\n🔄 Processing...")
    print("This may take several minutes depending on file size...")
    
    url = "http://localhost:8001/transcribe"
    
    with open(file_path, 'rb') as f:
        files = {'file': (Path(file_path).name, f, 'audio/mpeg')}
        data = {
            'enable_speaker_detection': str(speaker_detection).lower(),
            'enable_corrections': str(corrections).lower(),
            'domain': domain,
            'save_transcript': str(save).lower()
        }
        
        try:
            response = requests.post(url, files=files, data=data, timeout=1200)
        except requests.exceptions.Timeout:
            print("❌ Timeout: File too large or server busy")
            return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    if response.status_code == 200:
        result = response.json()
        transcription = result.get('transcription', {})
        
        print("\n✅ TRANSCRIPTION COMPLETE!")
        print("=" * 70)
        
        # Stats
        if result.get('transcript_id'):
            print(f"📝 Transcript ID: {result['transcript_id']}")
        
        if 'speaker_segments' in transcription:
            segments = transcription.get('speaker_segments', [])
            speaker_count = transcription.get('speaker_count', 0)
            print(f"👥 Speakers: {speaker_count}")
            print(f"📊 Segments: {len(segments)}")
            
            # Speaker breakdown
            speaker_stats = {}
            for seg in segments:
                speaker = seg.get('speaker', 'Unknown')
                if speaker not in speaker_stats:
                    speaker_stats[speaker] = 0
                speaker_stats[speaker] += len(seg.get('text', '').split())
            
            print("\n📈 Speaker Breakdown:")
            for speaker, words in speaker_stats.items():
                print(f"   • {speaker}: ~{words} words")
        
        # Save to file
        output_file = Path(file_path).stem + "_transcript.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Transcript: {Path(file_path).name}\n")
            f.write("=" * 70 + "\n")
            f.write(f"Settings: Speakers={'ON' if speaker_detection else 'OFF'}, "
                   f"Corrections={'ON' if corrections else 'OFF'}, Domain={domain}\n")
            f.write("=" * 70 + "\n\n")
            
            if 'speaker_segments' in transcription and speaker_detection:
                # Format with speakers
                current_speaker = None
                for seg in transcription['speaker_segments']:
                    if seg['speaker'] != current_speaker:
                        current_speaker = seg['speaker']
                        f.write(f"\n[{current_speaker}]: ")
                    f.write(seg['text'] + " ")
            else:
                # Plain text
                f.write(transcription.get('text', ''))
        
        print(f"\n💾 Saved to: {output_file}")
        
        # Preview
        text = transcription.get('text', '')
        if len(text) > 300:
            preview = text[:300] + "..."
        else:
            preview = text
        
        print("\n📄 Preview:")
        print("-" * 70)
        print(preview)
        
        return result
    else:
        print(f"\n❌ Transcription failed: {response.status_code}")
        print(response.text[:500])
        return None

def main():
    parser = argparse.ArgumentParser(
        description='Transcribe audio files with optional speaker detection',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s audio.mp3                    # Interactive mode
  %(prog)s audio.mp3 --no-speakers      # Disable speaker detection
  %(prog)s audio.mp3 --speakers         # Enable speaker detection
  %(prog)s audio.mp3 --domain tax       # Use tax-specific corrections
  
Domains available: general, tax, legal, medical
        """
    )
    
    parser.add_argument('file', help='Audio file to transcribe')
    parser.add_argument('--speakers', action='store_true', 
                       help='Enable speaker detection')
    parser.add_argument('--no-speakers', action='store_true',
                       help='Disable speaker detection')
    parser.add_argument('--no-corrections', action='store_true',
                       help='Disable auto-corrections')
    parser.add_argument('--domain', default='general',
                       choices=['general', 'tax', 'legal', 'medical'],
                       help='Domain for corrections (default: general)')
    parser.add_argument('--no-save', action='store_true',
                       help="Don't save to database")
    
    args = parser.parse_args()
    
    # Determine speaker detection preference
    if args.speakers:
        speaker_detection = True
    elif args.no_speakers:
        speaker_detection = False
    else:
        speaker_detection = None  # Ask user
    
    # Run transcription
    result = transcribe_audio(
        args.file,
        speaker_detection=speaker_detection,
        corrections=not args.no_corrections,
        domain=args.domain,
        save=not args.no_save
    )
    
    if result:
        print("\n✨ Done!")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()