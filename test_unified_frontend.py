"""
Test the unified frontend implementation
"""

import asyncio
import os
import sys
import subprocess
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

# Configuration
VLM_SERVER_URL = "http://localhost:8000"
WEB_SERVER_URL = "http://localhost:8080"
TEST_IMAGE = "test_bank_statement.png"

def start_web_server():
    """Start the web interface server"""
    print("Starting web server...")
    process = subprocess.Popen(
        ["python", "server.py"],
        cwd="services/vlm/web_interface",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(3)  # Wait for server to start
    return process

def check_servers():
    """Check if servers are running"""
    try:
        # Check VLM server
        response = requests.get(f"{VLM_SERVER_URL}/health")
        if response.status_code != 200:
            print("❌ VLM server not running")
            return False
        print("✓ VLM server is running")
        
        # Check web server
        response = requests.get(f"{WEB_SERVER_URL}")
        if response.status_code != 200:
            print("❌ Web server not running")
            return False
        print("✓ Web server is running")
        
        return True
    except Exception as e:
        print(f"❌ Server check failed: {e}")
        return False

def test_unified_interface():
    """Test the unified interface with Selenium"""
    print("\n=== Testing Unified Interface ===\n")
    
    # Set up Chrome options for headless mode
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    try:
        # Create driver
        driver = webdriver.Chrome(options=chrome_options)
        wait = WebDriverWait(driver, 10)
        
        # Test 1: Load unified interface
        print("1. Loading unified interface...")
        driver.get(f"{WEB_SERVER_URL}/index_unified.html")
        time.sleep(2)
        
        # Check if page loaded
        title = driver.find_element(By.TAG_NAME, "h1").text
        assert "VLM Server" in title, f"Unexpected title: {title}"
        print("✓ Page loaded successfully")
        
        # Test 2: Check mode buttons
        print("\n2. Testing mode selection...")
        mode_buttons = driver.find_elements(By.CLASS_NAME, "mode-btn")
        assert len(mode_buttons) == 4, f"Expected 4 mode buttons, found {len(mode_buttons)}"
        
        # Click bank extraction mode
        bank_btn = None
        for btn in mode_buttons:
            if btn.get_attribute("data-mode") == "bank-extraction":
                bank_btn = btn
                break
        
        assert bank_btn is not None, "Bank extraction button not found"
        bank_btn.click()
        time.sleep(1)
        
        # Check if prompt updated
        prompt_input = driver.find_element(By.ID, "promptInput")
        prompt_value = prompt_input.get_attribute("value")
        assert "bank statement" in prompt_value.lower(), f"Prompt not updated: {prompt_value}"
        print("✓ Mode selection works")
        
        # Test 3: Check provider selection
        print("\n3. Testing provider selection...")
        provider_select = driver.find_element(By.ID, "providerSelect")
        options = provider_select.find_elements(By.TAG_NAME, "option")
        assert len(options) >= 2, f"Expected at least 2 providers, found {len(options)}"
        print("✓ Provider selection available")
        
        # Test 4: Check export buttons visibility
        print("\n4. Testing export buttons...")
        export_csv = driver.find_element(By.ID, "exportCsvBtn")
        export_json = driver.find_element(By.ID, "exportJsonBtn")
        
        # In bank mode, export buttons should be visible
        assert export_csv.is_displayed(), "Export CSV button not visible in bank mode"
        assert export_json.is_displayed(), "Export JSON button not visible in bank mode"
        print("✓ Export buttons visible in bank mode")
        
        # Test 5: Switch back to general mode
        print("\n5. Testing mode switch...")
        general_btn = driver.find_element(By.CSS_SELECTOR, "[data-mode='general']")
        general_btn.click()
        time.sleep(1)
        
        # Export buttons should be hidden
        assert not export_csv.is_displayed(), "Export buttons still visible in general mode"
        print("✓ Mode switching works correctly")
        
        # Test 6: Check VRAM status
        print("\n6. Testing VRAM status...")
        vram_status = driver.find_element(By.ID, "vramStatus")
        vram_text = vram_status.text
        # Wait for VRAM to update (might show "Loading..." initially)
        time.sleep(5)
        vram_text = vram_status.text
        if "VRAM:" in vram_text and "GB" in vram_text:
            print(f"✓ VRAM status working: {vram_text}")
        else:
            print(f"⚠ VRAM status might not be updating: {vram_text}")
        
        print("\n✅ All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        driver.quit()

def test_api_endpoints():
    """Test that unified API endpoints are working"""
    print("\n=== Testing API Endpoints ===\n")
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Unified providers endpoint
    print("1. Testing /api/v1/providers_unified...")
    try:
        response = requests.get(f"{VLM_SERVER_URL}/api/v1/providers_unified")
        if response.status_code == 200:
            providers = response.json()
            print(f"✓ Found providers: {list(providers.keys())}")
            tests_passed += 1
        else:
            print(f"✗ Failed with status: {response.status_code}")
            tests_failed += 1
    except Exception as e:
        print(f"✗ Error: {e}")
        tests_failed += 1
    
    # Test 2: LangChain extraction endpoint
    print("\n2. Testing /api/v1/bank_extract_langchain...")
    try:
        payload = {
            "messages": [{
                "role": "user",
                "content": "Extract: Date: 01/01, Description: Test, Amount: $100"
            }],
            "temperature": 0.1,
            "max_tokens": 500
        }
        response = requests.post(
            f"{VLM_SERVER_URL}/api/v1/bank_extract_langchain",
            json=payload
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Extraction successful, transactions: {len(result.get('transactions', []))}")
            tests_passed += 1
        else:
            print(f"✗ Failed with status: {response.status_code}")
            tests_failed += 1
    except Exception as e:
        print(f"✗ Error: {e}")
        tests_failed += 1
    
    # Test 3: Unified generate endpoint
    print("\n3. Testing /api/v1/generate_unified...")
    try:
        payload = {
            "messages": [{"role": "user", "content": "What is 2+2?"}],
            "temperature": 0.1,
            "max_tokens": 50
        }
        response = requests.post(
            f"{VLM_SERVER_URL}/api/v1/generate_unified",
            json=payload
        )
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Generation successful: {result.get('response', '')[:50]}...")
            tests_passed += 1
        else:
            print(f"✗ Failed with status: {response.status_code}")
            tests_failed += 1
    except Exception as e:
        print(f"✗ Error: {e}")
        tests_failed += 1
    
    print(f"\nAPI Tests: {tests_passed} passed, {tests_failed} failed")
    return tests_failed == 0

def main():
    """Run all tests"""
    print("="*60)
    print("Unified Frontend Test Suite")
    print("="*60)
    
    # Check if servers are running
    if not check_servers():
        print("\n⚠️  Please start the VLM server first:")
        print("   cd services/vlm && python vlm_server.py")
        return
    
    # Start web server
    web_process = None
    try:
        web_process = start_web_server()
        
        # Run API tests
        api_success = test_api_endpoints()
        
        # Check if we have Selenium installed
        try:
            import selenium
            # Run UI tests
            test_unified_interface()
        except ImportError:
            print("\n⚠️  Selenium not installed. Skipping UI tests.")
            print("   Install with: pip install selenium")
        
        print("\n" + "="*60)
        print("Test Summary:")
        print("- API tests: " + ("✅ Passed" if api_success else "❌ Failed"))
        print("- UI tests: Completed")
        print("="*60)
        
    finally:
        # Clean up
        if web_process:
            print("\nStopping web server...")
            web_process.terminate()
            web_process.wait()

if __name__ == "__main__":
    main()