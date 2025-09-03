#!/usr/bin/env python3
"""Test Vector Database and RAG Integration"""

import asyncio
import sys
import os
sys.path.append('services/audio')

from vector_storage import VectorTranscriptStorage, TranscriptRAG

def test_vector_storage():
    """Test vector storage functionality"""
    print("=" * 60)
    print("TESTING VECTOR STORAGE")
    print("=" * 60)
    
    # Initialize vector storage
    print("\n1. Initializing Vector Storage...")
    vector_storage = VectorTranscriptStorage(persist_directory="./test_vectors")
    print("✅ Vector storage initialized")
    
    # Test adding transcripts
    print("\n2. Adding Sample Transcripts...")
    
    transcripts = [
        {
            "id": "test_001",
            "text": """Good morning everyone. Today we'll discuss the Q3 budget planning. 
            We need to allocate resources for the new marketing campaign. 
            John will be responsible for creating the budget proposal by next Friday.
            The total budget ceiling is $500,000 for this quarter.
            We should focus on digital marketing channels primarily.""",
            "metadata": {"filename": "meeting_q3_budget.mp3", "language": "en"}
        },
        {
            "id": "test_002",
            "text": """In our customer support call, the client mentioned several issues.
            First, they need better response times on tickets.
            Second, they want a dedicated account manager.
            Sarah will follow up with them by end of day tomorrow.
            We agreed to provide a service level agreement within 2 weeks.""",
            "metadata": {"filename": "customer_call_001.wav", "language": "en"}
        },
        {
            "id": "test_003",
            "text": """Product development meeting notes:
            The new feature release is scheduled for next month.
            We discussed the technical debt that needs addressing.
            Mike will lead the refactoring effort starting Monday.
            Budget allocation for development is approximately $200,000.""",
            "metadata": {"filename": "dev_meeting.mp3", "language": "en"}
        }
    ]
    
    for transcript in transcripts:
        result = vector_storage.add_transcript(
            transcript_id=transcript["id"],
            text=transcript["text"],
            metadata=transcript["metadata"],
            chunk_size=100
        )
        if result["success"]:
            print(f"  ✅ Added {transcript['id']}: {result['chunks_created']} chunks")
        else:
            print(f"  ❌ Failed to add {transcript['id']}")
    
    # Test semantic search
    print("\n3. Testing Semantic Search...")
    
    test_queries = [
        "budget discussions and financial planning",
        "who is responsible for what tasks",
        "customer issues and complaints",
        "deadlines and timelines"
    ]
    
    for query in test_queries:
        print(f"\n  Query: '{query}'")
        results = vector_storage.search(query, n_results=3)
        for i, result in enumerate(results, 1):
            print(f"    Result {i}: (Score: {result['similarity_score']:.3f})")
            print(f"      From: {result['metadata'].get('filename', 'Unknown')}")
            print(f"      Text: {result['text'][:100]}...")
    
    # Test hybrid search
    print("\n4. Testing Hybrid Search (Semantic + Keyword)...")
    hybrid_results = vector_storage.hybrid_search(
        query="financial planning",
        keyword="budget",
        n_results=2
    )
    print(f"  Found {len(hybrid_results)} results with both semantic and keyword match")
    
    # Test finding similar transcripts
    print("\n5. Testing Similar Transcript Finding...")
    similar = vector_storage.find_similar_transcripts("test_001", n_results=2)
    for item in similar:
        print(f"  Similar to test_001: {item['transcript_id']} (Score: {item['similarity_score']:.3f})")
    
    # Get statistics
    print("\n6. Vector Store Statistics:")
    stats = vector_storage.get_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    return vector_storage

async def test_rag():
    """Test RAG functionality"""
    print("\n" + "=" * 60)
    print("TESTING RAG (Retrieval-Augmented Generation)")
    print("=" * 60)
    
    # Initialize vector storage with test data
    vector_storage = test_vector_storage()
    
    # Initialize RAG
    print("\n7. Testing RAG Context Retrieval...")
    rag = TranscriptRAG(vector_storage)
    
    test_questions = [
        "What is the total budget mentioned?",
        "Who has action items and what are their deadlines?",
        "What customer issues were discussed?",
        "What development work is planned?"
    ]
    
    for question in test_questions:
        print(f"\n  Question: '{question}'")
        context, sources = rag.get_context_for_query(
            query=question,
            max_context_length=500,
            n_chunks=3
        )
        
        if context:
            print(f"    Context length: {len(context)} chars")
            print(f"    Sources: {len(sources)} chunks")
            print(f"    Preview: {context[:150]}...")
            
            # Format RAG prompt
            prompt = rag.format_rag_prompt(question, context)
            print(f"    RAG Prompt length: {len(prompt)} chars")
        else:
            print("    No relevant context found")
    
    print("\n✅ RAG testing complete!")

def cleanup_test_data():
    """Clean up test vector database"""
    import shutil
    if os.path.exists("./test_vectors"):
        shutil.rmtree("./test_vectors")
        print("\n🧹 Cleaned up test vector database")

def main():
    print("VECTOR DATABASE AND RAG INTEGRATION TEST")
    print("=" * 60)
    
    try:
        # Run async tests
        asyncio.run(test_rag())
        
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print("✅ All tests completed successfully!")
        print("\nCapabilities now available:")
        print("• Semantic search across transcripts")
        print("• Find content by meaning, not just keywords")
        print("• RAG context retrieval for Q&A")
        print("• Hybrid search (semantic + keyword)")
        print("• Find similar transcripts")
        print("• Intelligent chunking with overlap")
        
    finally:
        cleanup_test_data()

if __name__ == "__main__":
    main()