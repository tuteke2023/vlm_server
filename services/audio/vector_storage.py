#!/usr/bin/env python3
"""Vector Storage Module for Audio Transcripts using ChromaDB"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional, Tuple
import hashlib
import json
import logging
from pathlib import Path
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class VectorTranscriptStorage:
    """Handle vector storage and semantic search for transcripts"""
    
    def __init__(self, persist_directory: str = "./transcript_vectors"):
        """Initialize ChromaDB client and collection"""
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Create or get collection
        try:
            self.collection = self.client.get_collection(
                name="transcripts"
            )
            logger.info(f"Loaded existing collection with {self.collection.count()} documents")
        except:
            self.collection = self.client.create_collection(
                name="transcripts",
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("Created new transcript collection")
    
    def chunk_text(
        self, 
        text: str, 
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        min_chunk_size: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Intelligently chunk text while preserving sentence boundaries
        """
        chunks = []
        
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        current_chunk = ""
        current_word_count = 0
        chunk_index = 0
        
        for sentence in sentences:
            sentence_word_count = len(sentence.split())
            
            # If adding this sentence exceeds chunk size, save current chunk
            if current_word_count + sentence_word_count > chunk_size and current_chunk:
                chunks.append({
                    "text": current_chunk.strip(),
                    "index": chunk_index,
                    "word_count": current_word_count
                })
                
                # Start new chunk with overlap
                overlap_words = current_chunk.split()[-chunk_overlap:] if chunk_overlap > 0 else []
                current_chunk = " ".join(overlap_words) + " " + sentence
                current_word_count = len(overlap_words) + sentence_word_count
                chunk_index += 1
            else:
                current_chunk += " " + sentence
                current_word_count += sentence_word_count
        
        # Add final chunk if it meets minimum size
        if current_word_count >= min_chunk_size:
            chunks.append({
                "text": current_chunk.strip(),
                "index": chunk_index,
                "word_count": current_word_count
            })
        
        return chunks
    
    def add_transcript(
        self,
        transcript_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        chunk_size: int = 500
    ) -> Dict[str, Any]:
        """
        Add a transcript to the vector store
        """
        # Chunk the transcript
        chunks = self.chunk_text(text, chunk_size)
        
        if not chunks:
            logger.warning(f"No chunks created for transcript {transcript_id}")
            return {"success": False, "message": "Text too short to chunk"}
        
        # Prepare data for ChromaDB
        documents = []
        ids = []
        metadatas = []
        
        for chunk in chunks:
            # Create unique ID for each chunk
            chunk_id = f"{transcript_id}_chunk_{chunk['index']}"
            
            # Prepare metadata
            chunk_metadata = {
                "transcript_id": transcript_id,
                "chunk_index": chunk["index"],
                "word_count": chunk["word_count"],
                "created_at": datetime.now().isoformat()
            }
            
            # Add custom metadata if provided
            if metadata:
                chunk_metadata.update(metadata)
            
            documents.append(chunk["text"])
            ids.append(chunk_id)
            metadatas.append(chunk_metadata)
        
        # Add to ChromaDB
        try:
            self.collection.add(
                documents=documents,
                ids=ids,
                metadatas=metadatas
            )
            
            logger.info(f"Added {len(chunks)} chunks for transcript {transcript_id}")
            
            return {
                "success": True,
                "transcript_id": transcript_id,
                "chunks_created": len(chunks),
                "total_words": sum(c["word_count"] for c in chunks)
            }
            
        except Exception as e:
            logger.error(f"Error adding transcript to vector store: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        transcript_ids: Optional[List[str]] = None,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Semantic search across transcripts
        """
        where_clause = {}
        
        # Filter by transcript IDs if provided
        if transcript_ids:
            where_clause["transcript_id"] = {"$in": transcript_ids}
        
        # Add metadata filters if provided
        if metadata_filter:
            where_clause.update(metadata_filter)
        
        try:
            # Perform search
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_clause if where_clause else None,
                include=["documents", "metadatas", "distances"]
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results["documents"][0])):
                formatted_results.append({
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "similarity_score": 1 - results["distances"][0][i],  # Convert distance to similarity
                    "transcript_id": results["metadatas"][0][i].get("transcript_id"),
                    "chunk_index": results["metadatas"][0][i].get("chunk_index")
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching transcripts: {e}")
            return []
    
    def get_transcript_chunks(self, transcript_id: str) -> List[Dict[str, Any]]:
        """
        Get all chunks for a specific transcript
        """
        try:
            results = self.collection.get(
                where={"transcript_id": transcript_id},
                include=["documents", "metadatas"]
            )
            
            # Sort by chunk index
            chunks = []
            for i in range(len(results["documents"])):
                chunks.append({
                    "text": results["documents"][i],
                    "metadata": results["metadatas"][i],
                    "chunk_index": results["metadatas"][i].get("chunk_index", 0)
                })
            
            # Sort by chunk index
            chunks.sort(key=lambda x: x["chunk_index"])
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error getting transcript chunks: {e}")
            return []
    
    def delete_transcript(self, transcript_id: str) -> bool:
        """
        Delete all chunks for a transcript
        """
        try:
            # Get all chunk IDs for this transcript
            results = self.collection.get(
                where={"transcript_id": transcript_id},
                include=[]
            )
            
            if results["ids"]:
                self.collection.delete(ids=results["ids"])
                logger.info(f"Deleted {len(results['ids'])} chunks for transcript {transcript_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting transcript: {e}")
            return False
    
    def hybrid_search(
        self,
        query: str,
        keyword: Optional[str] = None,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Combine semantic and keyword search
        """
        # Get semantic search results
        semantic_results = self.search(query, n_results * 2)  # Get more for filtering
        
        # Filter by keyword if provided
        if keyword:
            filtered_results = []
            for result in semantic_results:
                if keyword.lower() in result["text"].lower():
                    filtered_results.append(result)
            
            return filtered_results[:n_results]
        
        return semantic_results[:n_results]
    
    def find_similar_transcripts(
        self,
        transcript_id: str,
        n_results: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Find transcripts similar to a given transcript
        """
        # Get a representative chunk from the transcript
        chunks = self.get_transcript_chunks(transcript_id)
        
        if not chunks:
            return []
        
        # Use the first chunk as representative
        representative_text = chunks[0]["text"]
        
        # Search for similar content, excluding the same transcript
        results = self.search(
            representative_text,
            n_results + 5  # Get extra to filter out same transcript
        )
        
        # Filter out chunks from the same transcript and group by transcript
        transcript_scores = {}
        for result in results:
            tid = result["transcript_id"]
            if tid != transcript_id:
                if tid not in transcript_scores:
                    transcript_scores[tid] = []
                transcript_scores[tid].append(result["similarity_score"])
        
        # Average scores per transcript
        similar_transcripts = []
        for tid, scores in transcript_scores.items():
            avg_score = sum(scores) / len(scores)
            similar_transcripts.append({
                "transcript_id": tid,
                "similarity_score": avg_score,
                "matching_chunks": len(scores)
            })
        
        # Sort by similarity score
        similar_transcripts.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        return similar_transcripts[:n_results]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store
        """
        try:
            total_chunks = self.collection.count()
            
            # Get unique transcript IDs
            results = self.collection.get(include=["metadatas"])
            transcript_ids = set()
            
            for metadata in results["metadatas"]:
                if "transcript_id" in metadata:
                    transcript_ids.add(metadata["transcript_id"])
            
            return {
                "total_chunks": total_chunks,
                "total_transcripts": len(transcript_ids),
                "average_chunks_per_transcript": (
                    total_chunks / len(transcript_ids) if transcript_ids else 0
                ),
                "storage_path": str(self.persist_directory)
            }
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {
                "error": str(e)
            }


class TranscriptRAG:
    """
    Retrieval-Augmented Generation for transcript Q&A
    """
    
    def __init__(self, vector_storage: VectorTranscriptStorage):
        self.vector_storage = vector_storage
    
    def get_context_for_query(
        self,
        query: str,
        max_context_length: int = 2000,
        n_chunks: int = 5
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Get relevant context for a query
        """
        # Search for relevant chunks
        results = self.vector_storage.search(query, n_results=n_chunks)
        
        if not results:
            return "", []
        
        # Combine chunks into context
        context_parts = []
        total_length = 0
        included_sources = []
        
        for result in results:
            chunk_text = result["text"]
            chunk_length = len(chunk_text)
            
            # Check if adding this chunk would exceed max length
            if total_length + chunk_length > max_context_length:
                break
            
            context_parts.append(chunk_text)
            total_length += chunk_length
            
            included_sources.append({
                "transcript_id": result["transcript_id"],
                "chunk_index": result["chunk_index"],
                "similarity_score": result["similarity_score"]
            })
        
        context = "\n\n".join(context_parts)
        
        return context, included_sources
    
    def format_rag_prompt(
        self,
        query: str,
        context: str,
        instructions: Optional[str] = None
    ) -> str:
        """
        Format a RAG prompt for the LLM
        """
        default_instructions = (
            "Use the following context from audio transcripts to answer the question. "
            "If the answer cannot be found in the context, say so. "
            "Be specific and cite relevant parts of the context when possible."
        )
        
        instructions = instructions or default_instructions
        
        prompt = f"""{instructions}

Context from transcripts:
{context}

Question: {query}

Answer:"""
        
        return prompt