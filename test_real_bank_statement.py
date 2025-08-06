"""
Test bank statement extraction with a real image
"""

import asyncio
import aiohttp
import json
import base64
import os
import sys

SERVER_URL = "http://localhost:8000"

async def test_with_image(image_path):
    """Test bank extraction with an actual image"""
    print(f"\n=== Testing with image: {os.path.basename(image_path)} ===\n")
    
    # Check if file exists
    if not os.path.exists(image_path):
        print(f"✗ Image file not found: {image_path}")
        return False
    
    # Read and encode image
    with open(image_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')
    
    async with aiohttp.ClientSession() as session:
        # Test 1: LangChain extraction
        print("1. Testing LangChain extraction...")
        request_data = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extract all transactions from this bank statement"},
                        {"type": "image", "image": image_data}
                    ]
                }
            ],
            "temperature": 0.1,
            "max_new_tokens": 4000
        }
        
        async with session.post(
            f"{SERVER_URL}/api/v1/bank_extract_langchain",
            json=request_data
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"✓ LangChain extraction successful!")
                print(f"  Provider: {data.get('metadata', {}).get('provider')}")
                print(f"  Bank: {data.get('bank_name', 'Not found')}")
                print(f"  Period: {data.get('statement_period', 'Not found')}")
                print(f"  Transactions: {len(data.get('transactions', []))}")
                print(f"  Total Debits: ${data.get('total_debits', 0)}")
                print(f"  Total Credits: ${data.get('total_credits', 0)}")
                
                # Show all transactions
                if data.get('transactions'):
                    print("\n  All transactions:")
                    for i, txn in enumerate(data['transactions'], 1):
                        print(f"    {i}. {txn['date']} - {txn['description']}")
                        print(f"       Category: {txn['category']}")
                        if txn.get('debit'):
                            print(f"       Debit: ${txn['debit']}")
                        if txn.get('credit'):
                            print(f"       Credit: ${txn['credit']}")
                        print(f"       Balance: ${txn['balance']}")
                        print()
            else:
                error = await resp.text()
                print(f"✗ LangChain extraction failed: {resp.status}")
                print(f"  Error: {error}")
                return False
        
        # Test 2: Legacy JSON extraction for comparison
        print("\n2. Testing legacy JSON extraction for comparison...")
        legacy_request = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extract bank transactions"},
                        {"type": "image", "image": image_data}
                    ]
                }
            ],
            "max_new_tokens": 4000
        }
        
        async with session.post(
            f"{SERVER_URL}/api/v1/bank_extract_json",
            json=legacy_request
        ) as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f"✓ Legacy extraction successful!")
                print(f"  Transactions: {data.get('data', {}).get('transaction_count', 0)}")
                
                # Save results
                output_file = image_path.replace('.png', '_langchain_results.json').replace('.jpg', '_langchain_results.json')
                with open(output_file, 'w') as f:
                    json.dump(data, f, indent=2)
                print(f"\n✓ Results saved to: {output_file}")
            else:
                print(f"✗ Legacy extraction failed: {resp.status}")
    
    return True


async def main():
    """Run tests with available bank statement images"""
    print("="*60)
    print("Real Bank Statement Extraction Test")
    print("="*60)
    
    # Look for test images
    test_images = []
    
    # Check common locations
    possible_images = [
        "test_bank_statement.png",
        "tests/bank_statement_1.png",
        "tests/bank_statement_2.png",
        "tests/bank_statement_3.png",
        "tests/sample_bank_statement.png",
        "../test_bank_statement.png"
    ]
    
    for img in possible_images:
        if os.path.exists(img):
            test_images.append(img)
    
    if not test_images:
        print("\n⚠ No test bank statement images found.")
        print("Please provide a bank statement image as argument:")
        print(f"  python {sys.argv[0]} <path_to_bank_statement_image>")
        
        if len(sys.argv) > 1:
            test_images = [sys.argv[1]]
    
    # Run tests
    for image_path in test_images:
        await test_with_image(image_path)
    
    if not test_images:
        print("\nTo test with a specific image:")
        print(f"  python {sys.argv[0]} path/to/bank_statement.png")


if __name__ == "__main__":
    asyncio.run(main())