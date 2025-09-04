#!/usr/bin/env python3
"""Test Q&A system performance"""

import time
import requests

API_URL = "http://localhost:8001"

def time_endpoint(name, method, endpoint, data=None):
    """Time an endpoint call"""
    print(f"\n⏱️  Testing {name}...")
    start = time.time()
    
    try:
        if method == "GET":
            response = requests.get(f"{API_URL}{endpoint}", timeout=10)
        else:
            response = requests.post(f"{API_URL}{endpoint}", data=data, timeout=10)
        
        elapsed = time.time() - start
        
        if response.status_code == 200:
            print(f"✅ Success in {elapsed:.2f} seconds")
            return elapsed
        else:
            print(f"❌ Failed with status {response.status_code}")
            return None
    except requests.Timeout:
        print(f"❌ Timeout after 10 seconds")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

print("=" * 60)
print("Q&A SYSTEM PERFORMANCE TEST")
print("=" * 60)

# Test each endpoint
tests = [
    ("Insights Generation", "GET", "/qa/insights", None),
    ("Simple Search", "POST", "/transcripts/search", {"query": "budget", "n_results": "3"}),
    ("Question Answering", "POST", "/qa/ask", {"question": "What was discussed?", "n_chunks": "3"}),
    ("Entity Extraction", "POST", "/qa/entities", {"entity_type": "people"}),
    ("Vector Stats", "GET", "/vector/stats", None),
]

times = []
for name, method, endpoint, data in tests:
    elapsed = time_endpoint(name, method, endpoint, data)
    if elapsed:
        times.append(elapsed)

if times:
    print("\n" + "=" * 60)
    print("PERFORMANCE SUMMARY")
    print("=" * 60)
    print(f"✅ Average response time: {sum(times)/len(times):.2f} seconds")
    print(f"⚡ Fastest: {min(times):.2f} seconds")
    print(f"🐌 Slowest: {max(times):.2f} seconds")
    
    if max(times) > 3:
        print("\n⚠️  RECOMMENDATION: Some endpoints are slow (>3s)")
        print("   Consider caching or pre-computing results")
    else:
        print("\n✅ All endpoints respond within 3 seconds - good UX!")
else:
    print("\n❌ No successful tests")