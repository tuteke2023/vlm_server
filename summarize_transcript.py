#!/usr/bin/env python3
"""
Summarize transcripts and extract action points using local VLM
"""

import requests
import json
import sys
from typing import Dict, List, Optional

class TranscriptSummarizer:
    def __init__(self, transcript_api="http://localhost:8001", vlm_api="http://localhost:8000"):
        self.transcript_api = transcript_api
        self.vlm_api = vlm_api
    
    def get_transcript(self, transcript_id: str) -> Optional[Dict]:
        """Fetch a transcript by ID"""
        try:
            response = requests.get(f"{self.transcript_api}/transcripts/{transcript_id}")
            if response.ok:
                return response.json()
        except Exception as e:
            print(f"Error fetching transcript: {e}")
        return None
    
    def search_transcript(self, query: str) -> Optional[str]:
        """Search for a transcript and return its ID"""
        try:
            response = requests.post(
                f"{self.transcript_api}/transcripts/search",
                data={"query": query, "n_results": 1}
            )
            if response.ok:
                data = response.json()
                if data["results"]:
                    return data["results"][0]["transcript_id"]
        except Exception as e:
            print(f"Error searching transcript: {e}")
        return None
    
    def summarize_with_vlm(self, content: str, task_type: str = "summary") -> str:
        """Use VLM to process transcript content"""
        
        prompts = {
            "summary": """Please provide a comprehensive summary of this conversation transcript. Include:
1. Main topic and participants
2. Key discussion points
3. Important decisions or conclusions
4. Overall outcome

Transcript:
{content}

Summary:""",
            
            "action_points": """Extract all action items and next steps from this conversation transcript. For each action item, identify:
- What needs to be done
- Who is responsible (if mentioned)
- Deadline or timeframe (if mentioned)
- Priority/urgency (if apparent)

Format as a numbered list.

Transcript:
{content}

Action Items:""",
            
            "key_facts": """Extract the key facts, dates, and important information from this conversation. Include:
- Important dates and deadlines
- Names and contact information
- Financial figures or amounts
- Legal or compliance requirements
- Critical decisions made

Transcript:
{content}

Key Facts:""",
            
            "comprehensive": """Provide a comprehensive analysis of this conversation transcript including:

SUMMARY:
- Main topic and context
- Key participants and their roles
- Main discussion points
- Conclusions reached

ACTION ITEMS:
- List all tasks that need to be completed
- Include responsible parties and deadlines where mentioned

KEY INFORMATION:
- Important dates, numbers, and facts
- Critical decisions made
- Risks or concerns raised

FOLLOW-UP REQUIRED:
- Any unresolved issues
- Next steps discussed

Transcript:
{content}

Analysis:"""
        }
        
        prompt = prompts.get(task_type, prompts["summary"]).format(
            content=content[:8000]  # Limit to avoid token limits
        )
        
        try:
            response = requests.post(
                f"{self.vlm_api}/api/v1/generate",
                json={
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens": 2000
                }
            )
            
            if response.ok:
                result = response.json()
                return result.get("response", "Unable to generate summary")
            else:
                return f"Error: {response.status_code} - {response.text}"
                
        except Exception as e:
            return f"Error calling VLM: {e}"
    
    def process_transcript(self, transcript_id: str = None, search_query: str = None):
        """Main function to process a transcript"""
        
        # Get transcript ID if searching
        if search_query and not transcript_id:
            print(f"🔍 Searching for: {search_query}")
            transcript_id = self.search_transcript(search_query)
            if not transcript_id:
                print("❌ No transcript found matching your search")
                return
        
        if not transcript_id:
            print("❌ Please provide either a transcript ID or search query")
            return
        
        # Fetch transcript
        print(f"📄 Fetching transcript {transcript_id}...")
        transcript = self.get_transcript(transcript_id)
        if not transcript:
            print("❌ Failed to fetch transcript")
            return
        
        print(f"✅ Found transcript: {transcript.get('audio_filename', 'Unknown')}")
        print(f"   Language: {transcript.get('language', 'Unknown')}")
        print(f"   Created: {transcript.get('created_at', 'Unknown')}")
        print()
        
        content = transcript.get("content", "")
        if not content:
            print("❌ Transcript has no content")
            return
        
        print(f"📝 Transcript length: {len(content)} characters")
        print("=" * 60)
        
        # Generate comprehensive analysis
        print("\n🤖 Generating comprehensive analysis with local VLM...")
        print("(This may take a moment...)\n")
        
        analysis = self.summarize_with_vlm(content, "comprehensive")
        print(analysis)
        
        # Save results
        filename = transcript.get('audio_filename', 'transcript').replace('.m4a', '').replace('.mp3', '')
        output_file = f"{filename}_analysis.txt"
        
        with open(output_file, 'w') as f:
            f.write(f"TRANSCRIPT ANALYSIS\n")
            f.write(f"{'=' * 60}\n")
            f.write(f"File: {transcript.get('audio_filename', 'Unknown')}\n")
            f.write(f"Transcript ID: {transcript_id}\n")
            f.write(f"Created: {transcript.get('created_at', 'Unknown')}\n")
            f.write(f"{'=' * 60}\n\n")
            f.write(analysis)
            f.write(f"\n\n{'=' * 60}\n")
            f.write("ORIGINAL TRANSCRIPT\n")
            f.write(f"{'=' * 60}\n\n")
            f.write(content)
        
        print(f"\n💾 Analysis saved to: {output_file}")
        
        return analysis

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Summarize transcripts using local VLM")
    parser.add_argument("--id", help="Transcript ID")
    parser.add_argument("--search", help="Search for transcript by keywords")
    parser.add_argument("--task", choices=["summary", "action_points", "key_facts", "comprehensive"], 
                       default="comprehensive", help="Type of analysis")
    
    args = parser.parse_args()
    
    summarizer = TranscriptSummarizer()
    
    if args.id:
        summarizer.process_transcript(transcript_id=args.id)
    elif args.search:
        summarizer.process_transcript(search_query=args.search)
    else:
        # Interactive mode
        print("🎙️ Transcript Summarizer using Local VLM")
        print("=" * 40)
        print("\nOptions:")
        print("1. Search for transcript by keywords")
        print("2. Enter transcript ID directly")
        
        choice = input("\nChoice (1 or 2): ").strip()
        
        if choice == "1":
            query = input("Enter search keywords: ").strip()
            summarizer.process_transcript(search_query=query)
        elif choice == "2":
            transcript_id = input("Enter transcript ID: ").strip()
            summarizer.process_transcript(transcript_id=transcript_id)
        else:
            print("Invalid choice")

if __name__ == "__main__":
    main()