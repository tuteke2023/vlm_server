#!/usr/bin/env python3
"""
Comprehensive Web UI Test Suite for VLM Server
Tests the web interface functionality with various document types
"""

import os
import time
import base64
import requests
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import io

class WebUITester:
    def __init__(self, server_url="http://localhost:8000", web_url="http://localhost:8080"):
        self.server_url = server_url
        self.web_url = web_url
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = "", response_time: float = 0):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "response_time": response_time
        })
        print(f"{status} {test_name} ({response_time:.2f}s)" + (f" - {details}" if details else ""))
        
    def check_server_health(self):
        """Check if VLM server is healthy"""
        try:
            response = requests.get(f"{self.server_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    print(f"✅ VLM Server is healthy on {data.get('device', 'unknown')}")
                    return True
            print("❌ VLM Server is not healthy")
            return False
        except:
            print("❌ Cannot connect to VLM server")
            return False
            
    def check_web_interface(self):
        """Check if web interface is accessible"""
        try:
            response = requests.get(self.web_url, timeout=10)
            if response.status_code == 200 and "VLM Server" in response.text:
                print("✅ Web interface is accessible")
                return True
            print("❌ Web interface is not accessible")
            return False
        except:
            print("❌ Cannot connect to web interface")
            return False
    
    def create_test_bank_statement(self):
        """Create a test bank statement image"""
        # Create a simple bank statement image
        width, height = 800, 600
        img = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(img)
        
        # Try to use a basic font, fallback to default if not available
        try:
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
            font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Header
        draw.rectangle([0, 0, width, 80], fill='#1e3a8a')
        draw.text((20, 25), "FIRST NATIONAL BANK", fill='white', font=font_large)
        
        # Account info
        draw.text((20, 100), "Account Statement", fill='black', font=font_large)
        draw.text((20, 130), "Account: *****1234", fill='black', font=font_medium)
        draw.text((20, 150), "Statement Period: 01/01/2024 - 01/31/2024", fill='black', font=font_medium)
        
        # Transaction header
        y_pos = 200
        draw.text((20, y_pos), "Date", fill='black', font=font_medium)
        draw.text((120, y_pos), "Description", fill='black', font=font_medium)
        draw.text((400, y_pos), "Amount", fill='black', font=font_medium)
        draw.text((500, y_pos), "Balance", fill='black', font=font_medium)
        
        # Sample transactions
        transactions = [
            ("01/02/2024", "Direct Deposit - SALARY", "+2,500.00", "2,500.00"),
            ("01/03/2024", "Grocery Store #123", "-85.50", "2,414.50"),
            ("01/05/2024", "Gas Station SHELL", "-45.00", "2,369.50"),
            ("01/07/2024", "Restaurant ABC", "-67.25", "2,302.25"),
            ("01/10/2024", "ATM Withdrawal", "-100.00", "2,202.25"),
            ("01/15/2024", "Online Transfer", "-500.00", "1,702.25"),
            ("01/20/2024", "Insurance Payment", "-150.00", "1,552.25"),
        ]
        
        y_pos = 230
        for date, desc, amount, balance in transactions:
            draw.text((20, y_pos), date, fill='black', font=font_small)
            draw.text((120, y_pos), desc, fill='black', font=font_small)
            color = 'green' if '+' in amount else 'red'
            draw.text((400, y_pos), amount, fill=color, font=font_small)
            draw.text((500, y_pos), balance, fill='black', font=font_small)
            y_pos += 25
        
        # Save the image
        test_path = Path("test_bank_statement.png")
        img.save(test_path)
        return test_path
        
    def create_test_receipt(self):
        """Create a test receipt image"""
        width, height = 400, 600
        img = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(img)
        
        try:
            font_medium = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        except:
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Store header
        draw.text((20, 20), "SUPERMARKET PLUS", fill='black', font=font_medium)
        draw.text((20, 40), "123 Main Street", fill='black', font=font_small)
        draw.text((20, 55), "City, State 12345", fill='black', font=font_small)
        draw.text((20, 70), "Tel: (555) 123-4567", fill='black', font=font_small)
        
        # Receipt details
        y_pos = 110
        draw.text((20, y_pos), "Date: 2024-01-15", fill='black', font=font_small)
        y_pos += 15
        draw.text((20, y_pos), "Time: 14:30:25", fill='black', font=font_small)
        y_pos += 15
        draw.text((20, y_pos), "Cashier: Alice", fill='black', font=font_small)
        y_pos += 30
        
        # Items
        items = [
            ("Milk 2% 1 Gallon", "3.99"),
            ("Bread Whole Wheat", "2.49"),
            ("Eggs Large Dozen", "4.25"),
            ("Chicken Breast 2lb", "8.99"),
            ("Apples Red 3lb", "5.47"),
            ("Rice Brown 2lb", "3.99"),
        ]
        
        for item, price in items:
            draw.text((20, y_pos), item, fill='black', font=font_small)
            draw.text((320, y_pos), f"${price}", fill='black', font=font_small)
            y_pos += 20
            
        # Total
        y_pos += 20
        draw.line([20, y_pos, 360, y_pos], fill='black', width=1)
        y_pos += 10
        draw.text((20, y_pos), "SUBTOTAL:", fill='black', font=font_small)
        draw.text((320, y_pos), "$29.18", fill='black', font=font_small)
        y_pos += 15
        draw.text((20, y_pos), "TAX:", fill='black', font=font_small)
        draw.text((320, y_pos), "$2.33", fill='black', font=font_small)
        y_pos += 15
        draw.text((20, y_pos), "TOTAL:", fill='black', font=font_medium)
        draw.text((320, y_pos), "$31.51", fill='black', font=font_medium)
        
        # Payment info
        y_pos += 30
        draw.text((20, y_pos), "PAYMENT METHOD: CREDIT CARD", fill='black', font=font_small)
        y_pos += 15
        draw.text((20, y_pos), "CARD: **** **** **** 1234", fill='black', font=font_small)
        
        test_path = Path("test_receipt.png")
        img.save(test_path)
        return test_path
        
    def create_test_document(self):
        """Create a test document image"""
        width, height = 600, 800
        img = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(img)
        
        try:
            font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
            font_text = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
        except:
            font_title = ImageFont.load_default()
            font_text = ImageFont.load_default()
        
        # Document content
        draw.text((50, 50), "BUSINESS PROPOSAL", fill='black', font=font_title)
        
        content = [
            "",
            "Executive Summary:",
            "This proposal outlines a new software development project that will",
            "revolutionize how businesses manage their document workflows.",
            "",
            "Key Benefits:",
            "• Increased efficiency by 40%",
            "• Cost reduction of $50,000 annually",
            "• Improved customer satisfaction",
            "• Streamlined operations",
            "",
            "Implementation Timeline:",
            "Phase 1: Planning and Design (2 months)",
            "Phase 2: Development (4 months)",
            "Phase 3: Testing and Deployment (2 months)",
            "",
            "Budget Requirements:",
            "Development Team: $150,000",
            "Software Licenses: $25,000",
            "Infrastructure: $30,000",
            "Total Project Cost: $205,000",
            "",
            "Expected ROI: 300% within first year",
            "",
            "Contact Information:",
            "John Smith, Project Manager",
            "Email: john.smith@company.com",
            "Phone: (555) 987-6543",
        ]
        
        y_pos = 100
        for line in content:
            draw.text((50, y_pos), line, fill='black', font=font_text)
            y_pos += 25
            
        test_path = Path("test_document.png")
        img.save(test_path)
        return test_path
        
    def image_to_base64(self, image_path):
        """Convert image to base64"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
            
    def test_bank_transaction_extraction(self):
        """Test bank transaction extraction functionality"""
        print("\n🏦 Testing Bank Transaction Extraction...")
        
        # Create test bank statement
        bank_statement = self.create_test_bank_statement()
        image_b64 = self.image_to_base64(bank_statement)
        
        prompt = """Analyze this bank statement and extract the following information in a structured format:
        - Transaction dates
        - Transaction descriptions  
        - Transaction amounts (specify if debit or credit)
        - Running balances
        - Account information
        
        Present the data in a clear table format with proper headers."""
        
        start_time = time.time()
        try:
            response = requests.post(f"{self.server_url}/api/v1/generate", json={
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "image", "image": f"data:image/png;base64,{image_b64}"},
                        {"type": "text", "text": prompt}
                    ]
                }],
                "max_new_tokens": 1000
            }, timeout=120)
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                response_text = result["response"].lower()
                
                # Check if it extracted key elements
                found_elements = []
                if "01/02/2024" in response_text or "direct deposit" in response_text:
                    found_elements.append("transactions")
                if "salary" in response_text or "2,500" in response_text:
                    found_elements.append("amounts")
                if "grocery" in response_text or "gas station" in response_text:
                    found_elements.append("descriptions")
                    
                if len(found_elements) >= 2:
                    self.log_test("Bank Statement Analysis", True, 
                                f"Extracted: {', '.join(found_elements)}", response_time)
                    print(f"💰 Sample Response: {result['response'][:200]}...")
                else:
                    self.log_test("Bank Statement Analysis", False, 
                                f"Missing key elements: {response_text[:100]}...", response_time)
            else:
                self.log_test("Bank Statement Analysis", False, 
                            f"HTTP {response.status_code}", response_time)
                
        except Exception as e:
            self.log_test("Bank Statement Analysis", False, str(e), time.time() - start_time)
        
        # Cleanup
        bank_statement.unlink(missing_ok=True)
        
    def test_receipt_processing(self):
        """Test receipt processing"""
        print("\n🧾 Testing Receipt Processing...")
        
        receipt_image = self.create_test_receipt()
        image_b64 = self.image_to_base64(receipt_image)
        
        prompt = """Extract all information from this receipt including:
        - Store name and address
        - Date and time
        - All items purchased with prices
        - Subtotal, tax, and total amounts
        - Payment method
        
        Format the response as a structured summary."""
        
        start_time = time.time()
        try:
            response = requests.post(f"{self.server_url}/api/v1/generate", json={
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "image", "image": f"data:image/png;base64,{image_b64}"},
                        {"type": "text", "text": prompt}
                    ]
                }],
                "max_new_tokens": 800
            }, timeout=120)
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                response_text = result["response"].lower()
                
                found_elements = []
                if "supermarket" in response_text:
                    found_elements.append("store name")
                if "31.51" in response_text or "total" in response_text:
                    found_elements.append("total amount")
                if "milk" in response_text or "bread" in response_text:
                    found_elements.append("items")
                if "credit card" in response_text:
                    found_elements.append("payment method")
                    
                if len(found_elements) >= 3:
                    self.log_test("Receipt Processing", True, 
                                f"Extracted: {', '.join(found_elements)}", response_time)
                else:
                    self.log_test("Receipt Processing", False, 
                                f"Missing elements. Found: {', '.join(found_elements)}", response_time)
            else:
                self.log_test("Receipt Processing", False, 
                            f"HTTP {response.status_code}", response_time)
                
        except Exception as e:
            self.log_test("Receipt Processing", False, str(e), time.time() - start_time)
        
        receipt_image.unlink(missing_ok=True)
        
    def test_document_summarization(self):
        """Test document summarization"""
        print("\n📄 Testing Document Summarization...")
        
        doc_image = self.create_test_document()
        image_b64 = self.image_to_base64(doc_image)
        
        prompt = """Provide a medium-length executive summary of this business proposal document. 
        Include:
        - Main purpose and objectives
        - Key benefits mentioned
        - Budget and timeline information
        - Expected return on investment
        
        Use executive summary style with clear, professional language."""
        
        start_time = time.time()
        try:
            response = requests.post(f"{self.server_url}/api/v1/generate", json={
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "image", "image": f"data:image/png;base64,{image_b64}"},
                        {"type": "text", "text": prompt}
                    ]
                }],
                "max_new_tokens": 600
            }, timeout=120)
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                response_text = result["response"].lower()
                
                found_elements = []
                if "software" in response_text or "development" in response_text:
                    found_elements.append("project type")
                if "205,000" in response_text or "budget" in response_text:
                    found_elements.append("budget")
                if "300%" in response_text or "roi" in response_text:
                    found_elements.append("ROI")
                if "efficiency" in response_text or "benefits" in response_text:
                    found_elements.append("benefits")
                    
                if len(found_elements) >= 3:
                    self.log_test("Document Summarization", True, 
                                f"Captured: {', '.join(found_elements)}", response_time)
                    print(f"📋 Summary Sample: {result['response'][:150]}...")
                else:
                    self.log_test("Document Summarization", False, 
                                f"Incomplete summary. Found: {', '.join(found_elements)}", response_time)
            else:
                self.log_test("Document Summarization", False, 
                            f"HTTP {response.status_code}", response_time)
                
        except Exception as e:
            self.log_test("Document Summarization", False, str(e), time.time() - start_time)
        
        doc_image.unlink(missing_ok=True)
        
    def test_custom_queries(self):
        """Test custom query functionality"""
        print("\n❓ Testing Custom Queries...")
        
        # Create a test image with contact information
        width, height = 500, 300
        img = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        except:
            font = ImageFont.load_default()
        
        # Contact card content
        draw.text((50, 50), "BUSINESS CARD", fill='black', font=font)
        draw.text((50, 100), "Sarah Johnson", fill='black', font=font)
        draw.text((50, 130), "Marketing Director", fill='black', font=font)
        draw.text((50, 160), "Email: sarah.j@techcorp.com", fill='black', font=font)
        draw.text((50, 190), "Phone: (555) 123-4567", fill='black', font=font)
        draw.text((50, 220), "Address: 456 Business Ave, Suite 200", fill='black', font=font)
        
        contact_image = Path("test_contact.png")
        img.save(contact_image)
        
        image_b64 = self.image_to_base64(contact_image)
        
        # Test specific extraction query
        query = "Extract all contact information including name, email, phone number, and address. Format as a structured list."
        
        start_time = time.time()
        try:
            response = requests.post(f"{self.server_url}/api/v1/generate", json={
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "image", "image": f"data:image/png;base64,{image_b64}"},
                        {"type": "text", "text": query}
                    ]
                }],
                "max_new_tokens": 300
            }, timeout=120)
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                response_text = result["response"].lower()
                
                found_elements = []
                if "sarah" in response_text or "johnson" in response_text:
                    found_elements.append("name")
                if "sarah.j@techcorp.com" in response_text or "email" in response_text:
                    found_elements.append("email")
                if "555" in response_text or "phone" in response_text:
                    found_elements.append("phone")
                if "business ave" in response_text or "address" in response_text:
                    found_elements.append("address")
                    
                if len(found_elements) >= 3:
                    self.log_test("Custom Query Processing", True, 
                                f"Extracted: {', '.join(found_elements)}", response_time)
                else:
                    self.log_test("Custom Query Processing", False, 
                                f"Incomplete extraction. Found: {', '.join(found_elements)}", response_time)
            else:
                self.log_test("Custom Query Processing", False, 
                            f"HTTP {response.status_code}", response_time)
                
        except Exception as e:
            self.log_test("Custom Query Processing", False, str(e), time.time() - start_time)
        
        contact_image.unlink(missing_ok=True)
        
    def test_error_handling(self):
        """Test error handling scenarios"""
        print("\n🚨 Testing Error Handling...")
        
        # Test 1: Invalid image data
        start_time = time.time()
        try:
            response = requests.post(f"{self.server_url}/api/v1/generate", json={
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "image", "image": "invalid_base64_data"},
                        {"type": "text", "text": "Analyze this image"}
                    ]
                }]
            }, timeout=30)
            
            response_time = time.time() - start_time
            
            if response.status_code in [400, 422, 500]:
                self.log_test("Error Handling - Invalid Image", True, 
                            f"Properly rejected invalid image", response_time)
            else:
                self.log_test("Error Handling - Invalid Image", False, 
                            f"Unexpected response: {response.status_code}", response_time)
                
        except Exception as e:
            self.log_test("Error Handling - Invalid Image", True, 
                        f"Exception caught: {type(e).__name__}", time.time() - start_time)
        
        # Test 2: Empty messages
        start_time = time.time()
        try:
            response = requests.post(f"{self.server_url}/api/v1/generate", json={
                "messages": []
            }, timeout=30)
            
            response_time = time.time() - start_time
            
            if response.status_code in [400, 422]:
                self.log_test("Error Handling - Empty Messages", True, 
                            f"Properly rejected empty messages", response_time)
            else:
                self.log_test("Error Handling - Empty Messages", False, 
                            f"Unexpected response: {response.status_code}", response_time)
                
        except Exception as e:
            self.log_test("Error Handling - Empty Messages", True, 
                        f"Exception caught: {type(e).__name__}", time.time() - start_time)
    
    def test_performance_metrics(self):
        """Test performance and response times"""
        print("\n⚡ Testing Performance Metrics...")
        
        # Simple text query for baseline
        start_time = time.time()
        try:
            response = requests.post(f"{self.server_url}/api/v1/generate", json={
                "messages": [{"role": "user", "content": "What is 2+2? Answer with just the number."}],
                "max_new_tokens": 5
            }, timeout=30)
            
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                tokens_per_second = result["usage"]["output_tokens"] / result["processing_time"]
                
                self.log_test("Performance - Text Generation", True, 
                            f"{tokens_per_second:.1f} tokens/sec", response_time)
            else:
                self.log_test("Performance - Text Generation", False, 
                            f"HTTP {response.status_code}", response_time)
                
        except Exception as e:
            self.log_test("Performance - Text Generation", False, str(e), time.time() - start_time)
    
    def run_all_tests(self):
        """Run all test cases"""
        print("🧪 Starting Comprehensive Web UI Test Suite\n")
        print("="*60)
        
        # Prerequisites
        if not self.check_server_health():
            print("❌ VLM Server not available. Tests cannot continue.")
            return False
            
        if not self.check_web_interface():
            print("❌ Web interface not available. Some tests may fail.")
        
        print("\n🔬 Running Test Cases:")
        print("="*60)
        
        # Core functionality tests
        self.test_bank_transaction_extraction()
        self.test_receipt_processing()
        self.test_document_summarization()
        self.test_custom_queries()
        self.test_error_handling()
        self.test_performance_metrics()
        
        # Print summary
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        avg_response_time = sum(r["response_time"] for r in self.test_results) / total if total > 0 else 0
        
        print(f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
        print(f"Average Response Time: {avg_response_time:.2f}s")
        
        # Show failed tests
        failed_tests = [r for r in self.test_results if not r["success"]]
        if failed_tests:
            print(f"\n❌ Failed Tests:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['details']}")
        else:
            print("\n🎉 All tests passed!")
            
        # Test recommendations
        print(f"\n💡 Recommendations:")
        if success_rate >= 90:
            print("  ✅ Web interface is working excellently!")
        elif success_rate >= 70:
            print("  ⚠️  Web interface is mostly working, minor issues detected")
        else:
            print("  ❌ Web interface has significant issues that need attention")
            
        if avg_response_time < 5:
            print("  ⚡ Response times are excellent")
        elif avg_response_time < 15:
            print("  ⏱️  Response times are acceptable")
        else:
            print("  🐌 Response times are slow, consider optimization")
            
        print("\n" + "="*60)
        return success_rate >= 80

def main():
    """Main test function"""
    tester = WebUITester()
    
    print("🚀 VLM Server Web UI Test Suite")
    print("Testing comprehensive document intelligence features")
    print(f"VLM Server: {tester.server_url}")
    print(f"Web Interface: {tester.web_url}")
    print()
    
    success = tester.run_all_tests()
    
    if success:
        print("🎉 Overall Result: Web interface is functioning well!")
        return 0
    else:
        print("⚠️  Overall Result: Web interface needs attention")
        return 1

if __name__ == "__main__":
    exit(main())