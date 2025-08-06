#!/usr/bin/env python3
"""Quick performance check for key endpoints."""

import asyncio
import time
import aiohttp
import base64

async def quick_check():
    # Load test image
    with open("./tests/BankStatementChequing.png", "rb") as f:
        img_base64 = base64.b64encode(f.read()).decode()
    
    payload = {
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
    
    async with aiohttp.ClientSession() as session:
        print("Performance Quick Check:\n")
        
        # LangChain endpoint
        print("1. LangChain endpoint:")
        start = time.time()
        resp = await session.post("http://localhost:8000/api/v1/bank_extract_langchain", json=payload)
        langchain_time = time.time() - start
        if resp.status == 200:
            result = await resp.json()
            print(f"   Time: {langchain_time:.2f}s")
            print(f"   Transactions: {len(result.get('transactions', []))}")
        else:
            print(f"   Error: {resp.status}")
        
        print("\n2. JSON endpoint:")
        start = time.time()
        resp = await session.post("http://localhost:8000/api/v1/bank_extract_json", json=payload)
        json_time = time.time() - start
        if resp.status == 200:
            result = await resp.json()
            print(f"   Time: {json_time:.2f}s")
            print(f"   Transactions: {result['data']['transaction_count']}")
        else:
            print(f"   Error: {resp.status}")
        
        print("\n3. VRAM Status:")
        resp = await session.get("http://localhost:8000/vram_status")
        if resp.status == 200:
            vram = await resp.json()
            print(f"   Allocated: {vram['allocated_gb']:.2f} GB")
            print(f"   Free: {vram['free_gb']:.2f} GB")
            print(f"   Usage: {vram['usage_percentage']:.1f}%")
        
        print(f"\nPerformance difference: {((langchain_time - json_time) / json_time * 100):+.1f}%")

asyncio.run(quick_check())