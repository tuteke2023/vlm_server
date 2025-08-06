"""
Test Increment 4: LangChain Extractor Integration with Server
"""

import asyncio
import aiohttp
import json
import base64
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.vlm.langchain_llm import UnifiedLangChainLLM
from services.vlm.langchain_extractor import LangChainExtractor


SERVER_URL = "http://localhost:8000"

# Sample bank statement text for testing
SAMPLE_BANK_TEXT = """
BANK OF TESTING
Account Statement
Account Number: ****1234
Statement Period: January 1-31, 2024

Date | Description | Withdrawals | Deposits | Balance
01/02/2024 | Opening Balance | - | - | 1,000.00
01/05/2024 | Grocery Store #123 | 45.67 | - | 954.33
01/10/2024 | Direct Deposit - Salary | - | 2,500.00 | 3,454.33
01/15/2024 | Electric Bill | 125.00 | - | 3,329.33
01/20/2024 | ATM Withdrawal | 100.00 | - | 3,229.33
01/25/2024 | Restaurant Purchase | 67.89 | - | 3,161.44
"""


async def test_with_server():
    """Test LangChain extractor with running server"""
    print("=== Test 1: LangChain Extractor with Server ===\n")
    
    async with aiohttp.ClientSession() as session:
        # Check server health
        async with session.get(f"{SERVER_URL}/health") as resp:
            if resp.status != 200:
                print("✗ Server not running")
                return False
        
        # Create server-based unified provider
        class ServerUnifiedProvider:
            def __init__(self, server_url, session):
                self.server_url = server_url
                self.session = session
                self.current_provider = "local"
            
            async def generate(self, messages, **kwargs):
                payload = {
                    "messages": messages,
                    **kwargs
                }
                
                async with self.session.post(
                    f"{self.server_url}/api/v1/generate_unified",
                    json=payload
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        from services.vlm.unified_llm_provider import LLMResponse
                        return LLMResponse(
                            content=data["response"],
                            usage=data.get("usage", {}),
                            metadata=data.get("metadata", {}),
                            processing_time=data.get("metadata", {}).get("processing_time", 0)
                        )
                    else:
                        raise Exception(f"Server error: {resp.status}")
            
            def get_current_provider(self):
                return self.current_provider
            
            def get_provider_info(self):
                return {"name": self.current_provider}
        
        # Create LangChain LLM with server provider
        provider = ServerUnifiedProvider(SERVER_URL, session)
        llm = UnifiedLangChainLLM(
            unified_provider=provider,
            temperature=0.1,
            max_tokens=3000
        )
        
        # Create extractor
        extractor = LangChainExtractor(llm)
        
        # Test extraction
        print("1. Testing text extraction...")
        result = await extractor.extract_bank_statement(
            content=SAMPLE_BANK_TEXT
        )
        
        print(f"✓ Extraction completed")
        print(f"  Bank: {result.get('bank_name', 'Not found')}")
        print(f"  Transactions: {len(result.get('transactions', []))}")
        
        for i, txn in enumerate(result.get('transactions', [])[:3]):
            print(f"\n  Transaction {i+1}:")
            print(f"    Date: {txn['date']}")
            print(f"    Description: {txn['description']}")
            print(f"    Category: {txn['category']}")
            print(f"    Debit: ${txn.get('debit') or '-'}")
            print(f"    Credit: ${txn.get('credit') or '-'}")
            print(f"    Balance: ${txn['balance']}")
        
        print(f"\n  Total debits: ${result.get('total_debits', 0)}")
        print(f"  Total credits: ${result.get('total_credits', 0)}")
        
        return True


async def test_with_openai():
    """Test with OpenAI provider"""
    print("\n=== Test 2: LangChain Extractor with OpenAI ===\n")
    
    async with aiohttp.ClientSession() as session:
        # Switch to OpenAI
        print("Switching to OpenAI provider...")
        async with session.post(
            f"{SERVER_URL}/api/v1/switch_provider_unified",
            json={"provider": "openai"}
        ) as resp:
            result = await resp.json()
            if result.get("status") != "success":
                print(f"⚠ Could not switch to OpenAI: {result}")
                return False
        
        # Create server provider
        class ServerUnifiedProvider:
            def __init__(self, server_url, session):
                self.server_url = server_url
                self.session = session
                self.current_provider = "openai"
            
            async def generate(self, messages, **kwargs):
                payload = {
                    "messages": messages,
                    **kwargs
                }
                
                async with self.session.post(
                    f"{self.server_url}/api/v1/generate_unified",
                    json=payload
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        from services.vlm.unified_llm_provider import LLMResponse
                        return LLMResponse(
                            content=data["response"],
                            usage=data.get("usage", {}),
                            metadata=data.get("metadata", {}),
                            processing_time=data.get("metadata", {}).get("processing_time", 0)
                        )
                    else:
                        raise Exception(f"Server error: {resp.status}")
            
            def get_current_provider(self):
                return self.current_provider
            
            def get_provider_info(self):
                return {"name": self.current_provider}
        
        # Create LangChain LLM
        provider = ServerUnifiedProvider(SERVER_URL, session)
        llm = UnifiedLangChainLLM(
            unified_provider=provider,
            temperature=0.1,
            max_tokens=2000
        )
        
        # Create extractor
        extractor = LangChainExtractor(llm)
        
        # Test with simpler content for OpenAI
        simple_text = """
        Bank Statement
        Date: 01/15/2024, Description: Coffee Shop, Amount: -$4.50, Balance: $995.50
        Date: 01/16/2024, Description: Salary Deposit, Amount: +$1000.00, Balance: $1995.50
        """
        
        print("Testing OpenAI extraction...")
        result = await extractor.extract_bank_statement(
            content=simple_text
        )
        
        print(f"✓ OpenAI extraction completed")
        print(f"  Provider: OpenAI")
        print(f"  Transactions: {len(result.get('transactions', []))}")
        
        # Switch back to local
        await session.post(
            f"{SERVER_URL}/api/v1/switch_provider_unified",
            json={"provider": "local"}
        )
        
        return True


async def test_table_extraction():
    """Test table format extraction fallback"""
    print("\n=== Test 3: Table Format Fallback ===\n")
    
    # Create mock LLM
    class MockLLM:
        def __init__(self):
            self.unified_provider = None
    
    llm = MockLLM()
    extractor = LangChainExtractor(llm)
    
    # Test table extraction
    result = extractor.extract_from_table_format(SAMPLE_BANK_TEXT)
    
    print(f"✓ Table extraction completed")
    print(f"  Transactions: {len(result.get('transactions', []))}")
    print(f"  Total debits: ${result.get('total_debits', 0)}")
    print(f"  Total credits: ${result.get('total_credits', 0)}")
    
    return True


async def main():
    """Run all integration tests"""
    print("="*60)
    print("Increment 4 Integration Tests")
    print("="*60 + "\n")
    
    print("NOTE: Make sure VLM server is running on http://localhost:8000\n")
    
    tests = [
        test_with_server,
        test_with_openai,
        test_table_extraction
    ]
    
    for test in tests:
        try:
            await test()
        except Exception as e:
            print(f"\n✗ Test failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*60)
    print("Integration tests complete!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())