#!/usr/bin/env python3
"""Test if LangChain endpoint is fixed."""

import asyncio
import aiohttp
import json
import base64

async def test_langchain_fix():
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
        print("Testing LangChain endpoint after fix...")
        resp = await session.post("http://localhost:8000/api/v1/bank_extract_langchain", 
                                 json=payload)
        
        if resp.status == 200:
            result = await resp.json()
            print(f"✅ Success!")
            print(f"Provider: {result.get('metadata', {}).get('provider', 'unknown')}")
            print(f"Transactions found: {len(result.get('transactions', []))}")
            
            if result.get('transactions'):
                print("\nFirst 3 transactions:")
                for i, txn in enumerate(result['transactions'][:3]):
                    print(f"{i+1}. {txn['date']} - {txn['description']}")
                    print(f"   Debit: ${txn.get('debit', 0) or 0:.2f}, Credit: ${txn.get('credit', 0) or 0:.2f}")
                    print(f"   Category: {txn.get('category', 'N/A')}")
            
            print(f"\nTotal debits: ${result.get('total_debits', 0):.2f}")
            print(f"Total credits: ${result.get('total_credits', 0):.2f}")
            
            return True
        else:
            print(f"❌ Failed with status {resp.status}")
            error = await resp.text()
            print(f"Error: {error[:200]}")
            return False

asyncio.run(test_langchain_fix())