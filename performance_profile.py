#!/usr/bin/env python3
"""Performance profiling script for the unified LLM system."""

import asyncio
import time
import aiohttp
import json
import base64
import statistics
from datetime import datetime

async def measure_endpoint_performance(session, endpoint, payload, name):
    """Measure performance of a single endpoint."""
    times = []
    errors = 0
    
    for i in range(3):
        start = time.time()
        try:
            resp = await session.post(endpoint, json=payload)
            if resp.status == 200:
                result = await resp.json()
                elapsed = time.time() - start
                times.append(elapsed)
                print(f"  Run {i+1}: {elapsed:.2f}s")
            else:
                errors += 1
                print(f"  Run {i+1}: Error {resp.status}")
        except Exception as e:
            errors += 1
            print(f"  Run {i+1}: Exception {str(e)}")
        
        # Brief pause between runs
        await asyncio.sleep(2)
    
    if times:
        return {
            "name": name,
            "min": min(times),
            "max": max(times),
            "mean": statistics.mean(times),
            "median": statistics.median(times),
            "errors": errors,
            "runs": len(times)
        }
    else:
        return {"name": name, "errors": errors, "runs": 0}

async def profile_performance():
    """Profile performance of all major endpoints."""
    print("=== VLM Server Performance Profile ===")
    print(f"Started at: {datetime.now()}\n")
    
    # Load test image
    with open("./tests/BankStatementChequing.png", "rb") as f:
        img_base64 = base64.b64encode(f.read()).decode()
    
    # Test payloads
    bank_payload = {
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": "Extract all transactions from this bank statement"},
                {"type": "image", "image": img_base64}
            ]
        }],
        "temperature": 0.1,
        "max_tokens": 4000
    }
    
    general_payload = {
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": "What is shown in this image?"},
                {"type": "image", "image": img_base64}
            ]
        }],
        "temperature": 0.7,
        "max_tokens": 500
    }
    
    results = []
    
    async with aiohttp.ClientSession() as session:
        # Test provider switching
        print("1. Testing provider switching...")
        start = time.time()
        await session.post("http://localhost:8000/api/v1/switch_provider_unified",
                          json={"provider": "local"})
        switch_time = time.time() - start
        print(f"   Provider switch time: {switch_time:.3f}s\n")
        
        # Test endpoints
        endpoints = [
            ("http://localhost:8000/api/v1/generate_unified", general_payload, "Generate (unified)"),
            ("http://localhost:8000/api/v1/generate", general_payload, "Generate (legacy)"),
            ("http://localhost:8000/api/v1/bank_extract_langchain", bank_payload, "Bank Extract (LangChain)"),
            ("http://localhost:8000/api/v1/bank_extract_json", bank_payload, "Bank Extract (JSON)"),
        ]
        
        for idx, (endpoint, payload, name) in enumerate(endpoints, 2):
            print(f"{idx}. Testing {name}...")
            result = await measure_endpoint_performance(session, endpoint, payload, name)
            results.append(result)
            print()
        
        # Memory usage check
        print("5. Checking memory usage...")
        resp = await session.get("http://localhost:8000/vram_status")
        if resp.status == 200:
            vram = await resp.json()
            print(f"   VRAM allocated: {vram['allocated_gb']:.2f} GB")
            print(f"   VRAM free: {vram['free_gb']:.2f} GB")
            print(f"   Usage: {vram['usage_percentage']:.1f}%\n")
    
    # Summary
    print("=== Performance Summary ===")
    print(f"{'Endpoint':<30} {'Mean':<8} {'Min':<8} {'Max':<8} {'Errors'}")
    print("-" * 70)
    for r in results:
        if r['runs'] > 0:
            print(f"{r['name']:<30} {r['mean']:>6.2f}s {r['min']:>6.2f}s {r['max']:>6.2f}s {r['errors']:>6}")
        else:
            print(f"{r['name']:<30} {'N/A':>6} {'N/A':>6} {'N/A':>6} {r['errors']:>6}")
    
    # Bottleneck analysis
    print("\n=== Bottleneck Analysis ===")
    if results:
        # Find slowest endpoint
        valid_results = [r for r in results if r['runs'] > 0]
        if valid_results:
            slowest = max(valid_results, key=lambda x: x['mean'])
            print(f"Slowest endpoint: {slowest['name']} (avg {slowest['mean']:.2f}s)")
            
            # Compare unified vs legacy
            unified_gen = next((r for r in results if 'unified' in r['name'].lower() and 'generate' in r['name'].lower()), None)
            legacy_gen = next((r for r in results if 'legacy' in r['name'].lower() and 'generate' in r['name'].lower()), None)
            
            if unified_gen and legacy_gen and unified_gen['runs'] > 0 and legacy_gen['runs'] > 0:
                overhead = ((unified_gen['mean'] - legacy_gen['mean']) / legacy_gen['mean']) * 100
                print(f"Unified overhead: {overhead:+.1f}% vs legacy")
            
            # Bank extraction comparison
            langchain = next((r for r in results if 'langchain' in r['name'].lower()), None)
            json_ext = next((r for r in results if 'json' in r['name'].lower()), None)
            
            if langchain and json_ext and langchain['runs'] > 0 and json_ext['runs'] > 0:
                diff = ((langchain['mean'] - json_ext['mean']) / json_ext['mean']) * 100
                print(f"LangChain vs JSON: {diff:+.1f}% difference")

asyncio.run(profile_performance())