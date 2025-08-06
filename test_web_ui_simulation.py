#!/usr/bin/env python3
"""Test that simulates web UI bank extraction flow."""

import asyncio
import aiohttp
import json
import base64

async def test_web_ui_flow():
    # Load test image
    with open("./tests/BankStatementChequing.png", "rb") as f:
        img_base64 = base64.b64encode(f.read()).decode()
    
    async with aiohttp.ClientSession() as session:
        # 1. Check providers
        print("1. Checking providers...")
        resp = await session.get("http://localhost:8000/api/v1/providers_unified")
        providers = await resp.json()
        print(f"   Available providers: {list(providers.keys())}")
        
        # 2. Ensure local provider is active
        print("\n2. Switching to local provider...")
        resp = await session.post("http://localhost:8000/api/v1/switch_provider_unified",
                                json={"provider": "local"})
        result = await resp.json()
        print(f"   Switch result: {result['status']}")
        
        # 3. Extract bank statement
        print("\n3. Extracting bank statement...")
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
        
        resp = await session.post("http://localhost:8000/api/v1/bank_extract_langchain", 
                                json=payload)
        
        if resp.status == 200:
            result = await resp.json()
            print(f"   ✅ Success!")
            print(f"   Provider: {result.get('metadata', {}).get('provider', 'unknown')}")
            print(f"   Transactions found: {len(result.get('transactions', []))}")
            
            if result.get('transactions'):
                print("\n   First 3 transactions:")
                for i, txn in enumerate(result['transactions'][:3]):
                    print(f"   {i+1}. {txn['date']} - {txn['description']}")
                    print(f"      Debit: ${txn.get('debit', 0) or 0:.2f}, Credit: ${txn.get('credit', 0) or 0:.2f}")
                    print(f"      Category: {txn.get('category', 'N/A')}")
            
            print(f"\n   Total debits: ${result.get('total_debits', 0):.2f}")
            print(f"   Total credits: ${result.get('total_credits', 0):.2f}")
            
            # 4. Test CSV export
            print("\n4. Testing CSV export...")
            export_resp = await session.post("http://localhost:8000/api/v1/bank_export",
                                           json={
                                               "messages": payload["messages"],
                                               "export_format": "csv"
                                           })
            
            if export_resp.status == 200:
                csv_data = await export_resp.text()
                print("   ✅ CSV export successful!")
                print(f"   CSV preview (first 200 chars):\n{csv_data[:200]}...")
            else:
                print(f"   ❌ CSV export failed: {export_resp.status}")
                
        else:
            print(f"   ❌ Failed with status {resp.status}")
            error = await resp.text()
            print(f"   Error: {error[:200]}")

asyncio.run(test_web_ui_flow())