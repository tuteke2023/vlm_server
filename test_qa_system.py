#!/usr/bin/env python3
"""Test the Q&A system with sample questions"""

import requests
import json

API_URL = "http://localhost:8001"

def test_qa():
    """Test basic Q&A functionality"""
    print("=" * 60)
    print("TESTING Q&A SYSTEM")
    print("=" * 60)
    
    # Test questions
    questions = [
        "What were the main topics discussed in the meetings?",
        "Were there any concerns about budget or costs?",
        "Who were the key people mentioned?",
        "What decisions were made?"
    ]
    
    for question in questions[:2]:  # Test first 2 questions
        print(f"\n📝 Question: {question}")
        print("-" * 40)
        
        try:
            response = requests.post(
                f"{API_URL}/qa/ask",
                data={
                    "question": question,
                    "n_chunks": 3
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Answer: {data['answer'][:300]}...")
                print(f"🎯 Confidence: {data['confidence']:.2%}")
                print(f"📚 Sources: {len(data['sources'])} chunks")
                
                if data['sources']:
                    print("\nTop source:")
                    source = data['sources'][0]
                    print(f"  - {source['filename']} (relevance: {source['relevance']:.2%})")
            else:
                print(f"❌ Error: HTTP {response.status_code}")
                print(response.text[:200])
                
        except Exception as e:
            print(f"❌ Error: {e}")

def test_action_items():
    """Test action items extraction"""
    print("\n" + "=" * 60)
    print("TESTING ACTION ITEMS EXTRACTION")
    print("=" * 60)
    
    try:
        response = requests.post(f"{API_URL}/qa/action_items")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {data['count']} sets of action items")
            
            for item in data['action_items'][:2]:  # Show first 2
                print(f"\nFrom: {item['source']}")
                print(f"Items: {item['items'][:200]}...")
        else:
            print(f"❌ Error: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_entities():
    """Test entity extraction"""
    print("\n" + "=" * 60)
    print("TESTING ENTITY EXTRACTION")
    print("=" * 60)
    
    entity_types = ['people', 'companies']
    
    for entity_type in entity_types:
        print(f"\n🔍 Extracting: {entity_type}")
        
        try:
            response = requests.post(
                f"{API_URL}/qa/entities",
                data={"entity_type": entity_type}
            )
            
            if response.status_code == 200:
                data = response.json()
                entities = data.get(entity_type, [])
                
                if entities:
                    print(f"✅ Found {len(entities)} {entity_type}:")
                    print(f"   {', '.join(entities[:10])}")
                else:
                    print(f"⚠️ No {entity_type} found")
            else:
                print(f"❌ Error: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

def test_insights():
    """Test insights generation"""
    print("\n" + "=" * 60)
    print("TESTING INSIGHTS GENERATION")
    print("=" * 60)
    
    try:
        response = requests.get(f"{API_URL}/qa/insights")
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ Generated insights:")
            
            if 'hot_topics' in data:
                print(f"\n🔥 Hot topics:")
                for topic, score in data['hot_topics'][:3]:
                    print(f"   - {topic}: {score:.3f}")
            
            if 'total_transcripts' in data:
                print(f"\n📊 Total transcripts: {data['total_transcripts']}")
            
            if 'key_decisions' in data:
                print(f"\n🎯 Key decisions:")
                print(f"   {data['key_decisions'][:200]}...")
        else:
            print(f"❌ Error: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    # Check if services are running
    print("Checking services...")
    
    # Check audio service
    try:
        r = requests.get(f"{API_URL}/health", timeout=2)
        if r.status_code == 200:
            print("✅ Audio service is running")
        else:
            print("❌ Audio service not responding properly")
    except:
        print("❌ Audio service not running on port 8001")
        return
    
    # Check VLM service
    try:
        r = requests.get("http://localhost:8000/health", timeout=2)
        if r.status_code == 200:
            print("✅ VLM service is running")
        else:
            print("⚠️ VLM service not responding - Q&A will use fallback mode")
    except:
        print("⚠️ VLM service not running - Q&A will use fallback mode")
    
    # Run tests
    test_qa()
    test_action_items()
    test_entities()
    test_insights()
    
    print("\n" + "=" * 60)
    print("✅ Q&A SYSTEM TEST COMPLETE")
    print("=" * 60)
    print("\nAccess the Q&A interface at:")
    print("http://localhost:8002/qa_interface.html")

if __name__ == "__main__":
    main()