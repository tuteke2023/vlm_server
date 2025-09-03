#!/usr/bin/env python3
"""LangChain RAG Integration for Audio Transcripts"""

import aiohttp
import logging
from typing import List, Dict, Any, Optional
from langchain.schema import Document
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.callbacks.base import BaseCallbackHandler

logger = logging.getLogger(__name__)

class TranscriptRetriever:
    """Custom retriever that uses the audio service's vector search"""
    
    def __init__(self, audio_service_url: str = "http://localhost:8001"):
        self.audio_service_url = audio_service_url
    
    async def get_relevant_documents(
        self, 
        query: str,
        n_results: int = 5
    ) -> List[Document]:
        """Retrieve relevant transcript chunks"""
        
        async with aiohttp.ClientSession() as session:
            try:
                # Call audio service's semantic search
                data = aiohttp.FormData()
                data.add_field('query', query)
                data.add_field('n_results', str(n_results))
                
                async with session.post(
                    f"{self.audio_service_url}/transcripts/search",
                    data=data
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        
                        # Convert to LangChain Documents
                        documents = []
                        for item in result.get("results", []):
                            doc = Document(
                                page_content=item["text"],
                                metadata={
                                    "transcript_id": item.get("transcript_id"),
                                    "similarity_score": item.get("similarity_score"),
                                    "filename": item.get("transcript_metadata", {}).get("filename"),
                                    "chunk_index": item.get("chunk_index")
                                }
                            )
                            documents.append(doc)
                        
                        return documents
                    else:
                        logger.error(f"Search failed with status {resp.status}")
                        return []
                        
            except Exception as e:
                logger.error(f"Error retrieving documents: {e}")
                return []
    
    async def get_rag_context(
        self,
        query: str,
        max_context_length: int = 2000
    ) -> Dict[str, Any]:
        """Get formatted RAG context from audio service"""
        
        async with aiohttp.ClientSession() as session:
            try:
                data = aiohttp.FormData()
                data.add_field('query', query)
                data.add_field('max_context_length', str(max_context_length))
                
                async with session.post(
                    f"{self.audio_service_url}/transcripts/rag",
                    data=data
                ) as resp:
                    if resp.status == 200:
                        return await resp.json()
                    else:
                        return {
                            "context": "",
                            "sources": [],
                            "prompt": ""
                        }
                        
            except Exception as e:
                logger.error(f"Error getting RAG context: {e}")
                return {
                    "context": "",
                    "sources": [],
                    "prompt": ""
                }


class TranscriptQAChain:
    """Q&A chain for transcript analysis"""
    
    def __init__(self, llm, audio_service_url: str = "http://localhost:8001"):
        self.llm = llm
        self.retriever = TranscriptRetriever(audio_service_url)
        
        # Define custom prompt template
        self.qa_prompt = PromptTemplate(
            template="""You are analyzing audio transcripts. Use the following context to answer the question.
            
Context from transcripts:
{context}

Question: {question}

Instructions:
- Answer based ONLY on the provided context
- If the answer is not in the context, say "I cannot find this information in the transcripts"
- Be specific and cite relevant parts when possible
- If the context mentions specific people, times, or topics, include those details

Answer:""",
            input_variables=["context", "question"]
        )
    
    async def answer_question(
        self,
        question: str,
        include_sources: bool = True
    ) -> Dict[str, Any]:
        """Answer a question using transcript context"""
        
        # Get RAG context
        rag_result = await self.retriever.get_rag_context(question)
        
        if not rag_result.get("context"):
            return {
                "answer": "I couldn't find any relevant information in the transcripts to answer your question.",
                "context_used": "",
                "sources": []
            }
        
        # Format prompt
        prompt = self.qa_prompt.format(
            context=rag_result["context"],
            question=question
        )
        
        # Get answer from LLM
        try:
            # For unified LLM provider
            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant analyzing audio transcripts."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            response = await self.llm.agenerate(messages)
            answer = response.generations[0][0].text if response.generations else "Unable to generate answer"
            
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            answer = "Error generating answer from the context"
        
        result = {
            "answer": answer,
            "question": question,
            "context_used": rag_result["context"][:500] + "..." if len(rag_result["context"]) > 500 else rag_result["context"]
        }
        
        if include_sources:
            result["sources"] = rag_result.get("sources", [])
        
        return result
    
    async def summarize_transcript(
        self,
        transcript_id: Optional[str] = None,
        custom_prompt: Optional[str] = None
    ) -> str:
        """Summarize a transcript or all recent transcripts"""
        
        default_prompt = """Please provide a comprehensive summary of the transcript(s) including:
        1. Main topics discussed
        2. Key decisions or conclusions
        3. Action items mentioned
        4. Important dates or deadlines
        5. People involved and their roles"""
        
        prompt = custom_prompt or default_prompt
        
        if transcript_id:
            prompt = f"For transcript {transcript_id}: " + prompt
        
        result = await self.answer_question(prompt, include_sources=False)
        return result["answer"]
    
    async def extract_action_items(self) -> List[str]:
        """Extract action items from transcripts"""
        
        prompt = """Extract all action items, tasks, or to-dos mentioned in the transcripts.
        Format each as a bullet point starting with the responsible person (if mentioned) and the task."""
        
        result = await self.answer_question(prompt, include_sources=False)
        
        # Parse bullet points from answer
        lines = result["answer"].split('\n')
        action_items = [line.strip() for line in lines if line.strip().startswith(('-', '•', '*'))]
        
        return action_items
    
    async def analyze_sentiment(self) -> Dict[str, Any]:
        """Analyze sentiment and tone of transcripts"""
        
        prompt = """Analyze the overall sentiment and tone of the conversation(s) in the transcripts.
        Include:
        1. Overall sentiment (positive, negative, neutral)
        2. Emotional tone
        3. Any tensions or disagreements
        4. Consensus areas
        5. Energy level of discussion"""
        
        result = await self.answer_question(prompt, include_sources=False)
        
        return {
            "analysis": result["answer"],
            "context_preview": result.get("context_used", "")[:200]
        }
    
    async def find_mentions(self, entity: str) -> List[Dict[str, str]]:
        """Find all mentions of a specific entity (person, topic, etc.)"""
        
        prompt = f"""Find all mentions of '{entity}' in the transcripts.
        For each mention, provide:
        - The context in which it was mentioned
        - What was said about it
        - Who mentioned it (if identifiable)"""
        
        result = await self.answer_question(prompt)
        
        # Parse mentions from the answer
        mentions = []
        if result.get("sources"):
            for source in result["sources"]:
                mentions.append({
                    "transcript_id": source.get("transcript_id"),
                    "context": source.get("text", "")[:200],
                    "relevance": source.get("similarity_score", 0)
                })
        
        return mentions


class TranscriptAnalyzer:
    """High-level analyzer for transcript insights"""
    
    def __init__(self, qa_chain: TranscriptQAChain):
        self.qa_chain = qa_chain
    
    async def generate_meeting_minutes(self) -> Dict[str, Any]:
        """Generate structured meeting minutes from transcript"""
        
        sections = {}
        
        # Get summary
        sections["summary"] = await self.qa_chain.summarize_transcript()
        
        # Extract action items
        sections["action_items"] = await self.qa_chain.extract_action_items()
        
        # Get key decisions
        decisions_result = await self.qa_chain.answer_question(
            "What key decisions were made in this meeting?"
        )
        sections["decisions"] = decisions_result["answer"]
        
        # Get participants
        participants_result = await self.qa_chain.answer_question(
            "Who participated in this conversation? List all people mentioned."
        )
        sections["participants"] = participants_result["answer"]
        
        # Next steps
        next_steps_result = await self.qa_chain.answer_question(
            "What are the next steps or follow-ups mentioned?"
        )
        sections["next_steps"] = next_steps_result["answer"]
        
        return sections
    
    async def compare_transcripts(
        self,
        transcript_ids: List[str],
        aspects: List[str] = None
    ) -> Dict[str, Any]:
        """Compare multiple transcripts on specific aspects"""
        
        default_aspects = [
            "Main topics",
            "Sentiment/tone",
            "Decisions made",
            "Progress on action items"
        ]
        
        aspects = aspects or default_aspects
        comparisons = {}
        
        for aspect in aspects:
            prompt = f"""Compare the transcripts on: {aspect}
            Highlight similarities and differences between them."""
            
            result = await self.qa_chain.answer_question(prompt)
            comparisons[aspect] = result["answer"]
        
        return comparisons