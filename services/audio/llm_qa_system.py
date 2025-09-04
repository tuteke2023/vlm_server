"""
LLM-Powered Question Answering System for Audio Transcripts
Integrates with vector search to provide intelligent answers
"""

import requests
import json
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import re
from vector_storage import VectorTranscriptStorage

@dataclass
class QAResult:
    """Structure for Q&A results"""
    question: str
    answer: str
    confidence: float
    sources: List[Dict]
    context_used: str
    processing_time: float

class TranscriptQASystem:
    """Intelligent Q&A system for transcripts using local VLM"""
    
    def __init__(self, 
                 vector_storage: Optional[VectorTranscriptStorage] = None,
                 vlm_url: str = "http://localhost:8000",
                 vlm_model: str = "qwen2.5-vl-3b"):
        """Initialize Q&A system with vector storage and VLM"""
        self.vector_storage = vector_storage or VectorTranscriptStorage()
        self.vlm_url = vlm_url
        self.vlm_model = vlm_model
        
    def answer_question(self, 
                       question: str, 
                       max_context_length: int = 3000,
                       n_chunks: int = 5) -> QAResult:
        """
        Answer a question using RAG with local VLM
        
        Args:
            question: The question to answer
            max_context_length: Maximum context to send to LLM
            n_chunks: Number of relevant chunks to retrieve
        
        Returns:
            QAResult with answer and metadata
        """
        start_time = datetime.now()
        
        # Step 1: Retrieve relevant context
        search_results = self.vector_storage.search(
            query=question,
            n_results=n_chunks
        )
        
        # Step 2: Build context from search results
        context_parts = []
        sources = []
        
        for result in search_results:
            chunk_text = result['text']
            context_parts.append(chunk_text)
            sources.append({
                'transcript_id': result['transcript_id'],
                'chunk_index': result['chunk_index'],
                'relevance': result['similarity_score'],
                'filename': result.get('transcript_metadata', {}).get('filename', 'Unknown')
            })
        
        context = "\n\n---\n\n".join(context_parts)[:max_context_length]
        
        # Step 3: Create prompt for VLM
        prompt = self._create_qa_prompt(question, context)
        
        # Step 4: Get answer from VLM
        answer = self._query_vlm(prompt)
        
        # Step 5: Calculate confidence based on relevance scores
        avg_relevance = sum(s['relevance'] for s in sources) / len(sources) if sources else 0
        confidence = min(avg_relevance * 1.5, 1.0)  # Scale up but cap at 1.0
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return QAResult(
            question=question,
            answer=answer,
            confidence=confidence,
            sources=sources,
            context_used=context[:500] + "..." if len(context) > 500 else context,
            processing_time=processing_time
        )
    
    def _create_qa_prompt(self, question: str, context: str) -> str:
        """Create an effective prompt for Q&A"""
        return f"""You are a helpful assistant analyzing meeting transcripts and audio recordings.

Based on the following context from transcripts, please answer the question accurately and concisely.
If the answer is not in the context, say "I cannot find this information in the transcripts."

Context from transcripts:
{context}

Question: {question}

Please provide a clear, direct answer based only on the information provided above."""

    def _query_vlm(self, prompt: str) -> str:
        """Query the local VLM for an answer"""
        try:
            # Use the unified VLM endpoint
            payload = {
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant for analyzing transcripts."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,  # Low temperature for factual answers
                "max_tokens": 500
            }
            
            response = requests.post(
                f"{self.vlm_url}/api/v1/generate_unified",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', {}).get('content', 'Unable to generate answer')
            else:
                # Fallback to simple extraction if VLM is not available
                return self._fallback_extraction(prompt)
                
        except Exception as e:
            print(f"VLM query failed: {e}")
            return self._fallback_extraction(prompt)
    
    def _fallback_extraction(self, prompt: str) -> str:
        """Simple fallback extraction when VLM is not available"""
        # Extract key sentences that might answer the question
        lines = prompt.split('\n')
        context_start = False
        context_lines = []
        
        for line in lines:
            if "Context from transcripts:" in line:
                context_start = True
                continue
            elif "Question:" in line:
                break
            elif context_start and line.strip():
                context_lines.append(line.strip())
        
        if context_lines:
            return f"Based on the transcripts: {context_lines[0][:200]}..."
        return "Unable to process question without VLM service"
    
    def extract_action_items(self, 
                            time_range: Optional[tuple] = None,
                            person: Optional[str] = None) -> List[Dict]:
        """
        Extract action items from transcripts
        
        Args:
            time_range: Optional (start_date, end_date) tuple
            person: Optional person name to filter by
        
        Returns:
            List of action items with metadata
        """
        # Create targeted search query
        query = "action items tasks todo deliverables assigned"
        if person:
            query += f" {person}"
        
        # Get relevant chunks
        results = self.vector_storage.search(query, n_results=10)
        
        action_items = []
        for result in results:
            # Use VLM to extract structured action items
            prompt = f"""Extract any action items from this text. 
Format each as: [PERSON] - [TASK] - [DEADLINE if mentioned]

Text: {result['text']}

List action items (or "None found" if none):"""
            
            extracted = self._query_vlm(prompt)
            
            if extracted and "None found" not in extracted:
                action_items.append({
                    'source': result.get('transcript_metadata', {}).get('filename', 'Unknown'),
                    'transcript_id': result['transcript_id'],
                    'items': extracted,
                    'relevance': result['similarity_score']
                })
        
        return action_items
    
    def summarize_topic(self, 
                       topic: str,
                       max_length: int = 500) -> Dict:
        """
        Create a summary about a specific topic across all transcripts
        
        Args:
            topic: The topic to summarize
            max_length: Maximum length of summary
        
        Returns:
            Dictionary with summary and sources
        """
        # Search for topic
        results = self.vector_storage.search(topic, n_results=8)
        
        if not results:
            return {
                'topic': topic,
                'summary': 'No information found about this topic',
                'sources': []
            }
        
        # Combine relevant passages
        passages = [r['text'] for r in results]
        combined = "\n\n".join(passages)
        
        # Create summary prompt
        prompt = f"""Create a concise summary about "{topic}" based on these transcript excerpts.
Focus on key points, decisions, and outcomes.

Transcripts:
{combined[:4000]}

Summary (max {max_length} chars):"""
        
        summary = self._query_vlm(prompt)
        
        return {
            'topic': topic,
            'summary': summary[:max_length],
            'sources': [
                {
                    'filename': r.get('transcript_metadata', {}).get('filename', 'Unknown'),
                    'relevance': r['similarity_score']
                }
                for r in results[:3]
            ],
            'chunks_analyzed': len(results)
        }
    
    def compare_meetings(self, 
                        meeting1_query: str,
                        meeting2_query: str) -> Dict:
        """
        Compare two meetings or time periods
        
        Args:
            meeting1_query: Search query for first meeting
            meeting2_query: Search query for second meeting
        
        Returns:
            Comparison analysis
        """
        # Get chunks from both meetings
        meeting1_chunks = self.vector_storage.search(meeting1_query, n_results=5)
        meeting2_chunks = self.vector_storage.search(meeting2_query, n_results=5)
        
        if not meeting1_chunks or not meeting2_chunks:
            return {'error': 'Could not find both meetings'}
        
        # Prepare comparison prompt
        meeting1_text = "\n".join([c['text'] for c in meeting1_chunks])
        meeting2_text = "\n".join([c['text'] for c in meeting2_chunks])
        
        prompt = f"""Compare these two meetings and identify:
1. Key differences
2. Progress made
3. Changes in decisions or plans

First meeting:
{meeting1_text[:1500]}

Second meeting:
{meeting2_text[:1500]}

Comparison:"""
        
        comparison = self._query_vlm(prompt)
        
        return {
            'meeting1': meeting1_query,
            'meeting2': meeting2_query,
            'comparison': comparison,
            'sources': {
                'meeting1': [c.get('transcript_metadata', {}).get('filename', 'Unknown') 
                           for c in meeting1_chunks[:2]],
                'meeting2': [c.get('transcript_metadata', {}).get('filename', 'Unknown')
                           for c in meeting2_chunks[:2]]
            }
        }
    
    def extract_entities(self, entity_type: str = "all") -> Dict:
        """
        Extract named entities (people, companies, dates, money)
        
        Args:
            entity_type: Type of entity to extract or "all"
        
        Returns:
            Dictionary of extracted entities
        """
        entity_queries = {
            'people': 'person name speaker participant attendee',
            'companies': 'company organization firm business client',
            'dates': 'date deadline timeline schedule when',
            'money': 'dollar amount price cost budget investment thousand million'
        }
        
        if entity_type == "all":
            queries = entity_queries
        else:
            queries = {entity_type: entity_queries.get(entity_type, entity_type)}
        
        entities = {}
        
        for ent_type, query in queries.items():
            results = self.vector_storage.search(query, n_results=10)
            
            # Extract entities using VLM
            prompt = f"""Extract all {ent_type} mentioned in these texts.
List each unique {ent_type} only once.

Texts:
{chr(10).join([r['text'][:200] for r in results[:5]])}

{ent_type.title()} found (comma-separated):"""
            
            extracted = self._query_vlm(prompt)
            
            # Parse extracted entities
            if extracted and "none" not in extracted.lower():
                entities[ent_type] = [e.strip() for e in extracted.split(',')]
            else:
                entities[ent_type] = []
        
        return entities

    def generate_insights(self) -> Dict:
        """
        Generate high-level insights from all transcripts (OPTIMIZED)
        
        Returns:
            Dictionary of insights
        """
        insights = {}
        
        try:
            # 1. Get basic statistics first (fast)
            stats = self.vector_storage.get_statistics()
            insights['total_transcripts'] = stats.get('total_transcripts', 0)
            insights['total_chunks'] = stats.get('total_chunks', 0)
            
            # 2. Most discussed topics (limit search for speed)
            common_topics = [
                'budget', 'timeline', 'decision', 'problem', 'next steps'
            ]
            
            topic_relevance = {}
            for topic in common_topics[:3]:  # Only check top 3 for speed
                results = self.vector_storage.search(topic, n_results=2)  # Reduced from 3
                if results:
                    topic_relevance[topic] = sum(r['similarity_score'] for r in results) / len(results)
            
            insights['hot_topics'] = sorted(
                topic_relevance.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:3]  # Top 3 only
            
            # 3. Quick decision extraction (simplified)
            decision_results = self.vector_storage.search(
                "decided approved confirmed",
                n_results=2  # Reduced from 5
            )
            
            if decision_results:
                # Use simple extraction instead of VLM for speed
                decisions = []
                for result in decision_results:
                    text = result['text'][:150]
                    # Extract sentences with decision keywords
                    if any(word in text.lower() for word in ['decided', 'approved', 'will']):
                        decisions.append(f"• {text[:100]}...")
                
                insights['key_decisions'] = "\n".join(decisions) if decisions else "Processing decisions..."
            else:
                insights['key_decisions'] = "No clear decisions found"
                
            # 4. Add quick stats
            insights['quick_stats'] = {
                'avg_chunks_per_transcript': stats.get('average_chunks_per_transcript', 0),
                'processing_status': 'ready'
            }
            
        except Exception as e:
            # Return minimal insights on error
            insights = {
                'error': str(e),
                'total_transcripts': 'Unknown',
                'hot_topics': [],
                'key_decisions': 'Error generating insights'
            }
        
        return insights


# Convenience functions for common queries
def create_qa_system():
    """Create a Q&A system instance"""
    return TranscriptQASystem()

def quick_answer(question: str):
    """Quick function to answer a question"""
    qa = create_qa_system()
    result = qa.answer_question(question)
    return result.answer