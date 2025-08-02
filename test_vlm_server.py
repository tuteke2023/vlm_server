#!/usr/bin/env python3
"""
Comprehensive test suite for VLM Server
Tests all endpoints and functionality including GPU acceleration
"""

import asyncio
import time
import requests
import base64
import json
from pathlib import Path
from typing import Dict, List
import subprocess
import signal
import os

class VLMServerTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.server_process = None
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = "", duration: float = 0):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "duration": duration
        })
        print(f"{status} {test_name} ({duration:.2f}s)" + (f" - {details}" if details else ""))
        
    def wait_for_server(self, timeout: int = 60):
        """Wait for server to be ready"""
        print("⏳ Waiting for server to start...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.base_url}/health", timeout=5)
                if response.status_code == 200:
                    print("✅ Server is ready!")
                    return True
            except requests.exceptions.RequestException:
                pass
            time.sleep(2)
            
        print("❌ Server failed to start within timeout")
        return False
        
    def test_health_endpoint(self):
        """Test 1: Health check endpoint"""
        start_time = time.time()
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy" and data.get("model_loaded"):
                    device = data.get("device", "unknown")
                    self.log_test("Health Check", True, f"Device: {device}", duration)
                    return data
                else:
                    self.log_test("Health Check", False, "Model not loaded", duration)
            else:
                self.log_test("Health Check", False, f"Status: {response.status_code}", duration)
        except Exception as e:
            self.log_test("Health Check", False, str(e), time.time() - start_time)
        return None
        
    def test_vram_status_endpoint(self):
        """Test 2: VRAM status endpoint"""
        start_time = time.time()
        try:
            response = requests.get(f"{self.base_url}/vram_status", timeout=10)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                usage = data.get("usage_percentage", 0)
                total_gb = data.get("total_gb", 0)
                self.log_test("VRAM Status", True, f"Usage: {usage}% of {total_gb}GB", duration)
                return data
            else:
                self.log_test("VRAM Status", False, f"Status: {response.status_code}", duration)
        except Exception as e:
            self.log_test("VRAM Status", False, str(e), time.time() - start_time)
        return None
        
    def test_simple_text_generation(self):
        """Test 3: Simple text generation"""
        start_time = time.time()
        try:
            data = {
                "messages": [
                    {"role": "user", "content": "What is 2+2? Answer with just the number."}
                ],
                "max_new_tokens": 10
            }
            
            response = requests.post(f"{self.base_url}/api/v1/generate", json=data, timeout=60)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get("response", "").strip()
                usage = result.get("usage", {})
                
                if "4" in answer:
                    self.log_test("Simple Text Generation", True, 
                                f"Answer: '{answer}', Tokens: {usage.get('total_tokens', 0)}", duration)
                else:
                    self.log_test("Simple Text Generation", False, f"Wrong answer: '{answer}'", duration)
                return result
            else:
                self.log_test("Simple Text Generation", False, f"Status: {response.status_code}", duration)
        except Exception as e:
            self.log_test("Simple Text Generation", False, str(e), time.time() - start_time)
        return None
        
    def test_complex_text_generation(self):
        """Test 4: Complex text generation"""
        start_time = time.time()
        try:
            data = {
                "messages": [
                    {"role": "user", "content": "Explain quantum computing in exactly one sentence."}
                ],
                "max_new_tokens": 100,
                "temperature": 0.7
            }
            
            response = requests.post(f"{self.base_url}/api/v1/generate", json=data, timeout=120)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get("response", "")
                usage = result.get("usage", {})
                
                if len(answer) > 20 and ("quantum" in answer.lower() or "computing" in answer.lower()):
                    self.log_test("Complex Text Generation", True, 
                                f"Length: {len(answer)} chars, Tokens: {usage.get('total_tokens', 0)}", duration)
                else:
                    self.log_test("Complex Text Generation", False, f"Poor response: '{answer[:50]}...'", duration)
                return result
            else:
                self.log_test("Complex Text Generation", False, f"Status: {response.status_code}", duration)
        except Exception as e:
            self.log_test("Complex Text Generation", False, str(e), time.time() - start_time)
        return None
        
    def test_image_analysis_url(self):
        """Test 5: Image analysis from URL"""
        start_time = time.time()
        try:
            # Use a simple test image
            image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/240px-PNG_transparency_demonstration_1.png"
            
            data = {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "image", "image": image_url},
                            {"type": "text", "text": "What colors do you see in this image? Answer briefly."}
                        ]
                    }
                ],
                "max_new_tokens": 50
            }
            
            response = requests.post(f"{self.base_url}/api/v1/generate", json=data, timeout=180)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get("response", "").lower()
                usage = result.get("usage", {})
                
                # Check if it mentions colors
                color_words = ["red", "green", "blue", "yellow", "black", "white", "color", "transparent"]
                has_color = any(color in answer for color in color_words)
                
                if has_color:
                    self.log_test("Image Analysis (URL)", True, 
                                f"Response: '{result.get('response', '')[:50]}...', Tokens: {usage.get('total_tokens', 0)}", duration)
                else:
                    self.log_test("Image Analysis (URL)", False, f"No color mentioned: '{answer}'", duration)
                return result
            else:
                self.log_test("Image Analysis (URL)", False, f"Status: {response.status_code}", duration)
        except Exception as e:
            self.log_test("Image Analysis (URL)", False, str(e), time.time() - start_time)
        return None
        
    def test_multi_turn_conversation(self):
        """Test 6: Multi-turn conversation"""
        start_time = time.time()
        try:
            data = {
                "messages": [
                    {"role": "user", "content": "My name is Alice. What's 5 times 3?"},
                    {"role": "assistant", "content": "5 times 3 equals 15."},
                    {"role": "user", "content": "What's my name and what was the previous calculation?"}
                ],
                "max_new_tokens": 50
            }
            
            response = requests.post(f"{self.base_url}/api/v1/generate", json=data, timeout=120)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get("response", "").lower()
                
                # Check if it remembers the name and calculation
                has_name = "alice" in answer
                has_calc = "15" in answer or "fifteen" in answer
                
                if has_name and has_calc:
                    self.log_test("Multi-turn Conversation", True, 
                                f"Remembered name and calculation", duration)
                elif has_name or has_calc:
                    self.log_test("Multi-turn Conversation", False, 
                                f"Partial memory: name={has_name}, calc={has_calc}", duration)
                else:
                    self.log_test("Multi-turn Conversation", False, 
                                f"No memory: '{result.get('response', '')}'", duration)
                return result
            else:
                self.log_test("Multi-turn Conversation", False, f"Status: {response.status_code}", duration)
        except Exception as e:
            self.log_test("Multi-turn Conversation", False, str(e), time.time() - start_time)
        return None
        
    def test_parameter_variations(self):
        """Test 7: Different generation parameters"""
        start_time = time.time()
        try:
            # Test with different temperature values
            results = []
            for temp in [0.1, 0.7, 0.9]:
                data = {
                    "messages": [
                        {"role": "user", "content": "Describe a sunset in 10 words."}
                    ],
                    "max_new_tokens": 20,
                    "temperature": temp,
                    "top_p": 0.9
                }
                
                response = requests.post(f"{self.base_url}/api/v1/generate", json=data, timeout=60)
                if response.status_code == 200:
                    result = response.json()
                    results.append(result.get("response", ""))
                else:
                    results.append(None)
                    
            duration = time.time() - start_time
            
            # Check if responses are different (indicating temperature works)
            valid_responses = [r for r in results if r]
            if len(valid_responses) >= 2:
                # Simple check: responses should be different at different temperatures
                unique_responses = len(set(valid_responses))
                if unique_responses > 1:
                    self.log_test("Parameter Variations", True, 
                                f"Generated {unique_responses} different responses", duration)
                else:
                    self.log_test("Parameter Variations", False, 
                                "All responses identical despite different temps", duration)
            else:
                self.log_test("Parameter Variations", False, "Failed to generate responses", duration)
                
        except Exception as e:
            self.log_test("Parameter Variations", False, str(e), time.time() - start_time)
            
    def test_error_handling(self):
        """Test 8: Error handling"""
        start_time = time.time()
        errors_caught = 0
        
        # Test invalid endpoint
        try:
            response = requests.get(f"{self.base_url}/invalid_endpoint")
            if response.status_code == 404:
                errors_caught += 1
        except:
            pass
            
        # Test invalid request body
        try:
            response = requests.post(f"{self.base_url}/api/v1/generate", json={"invalid": "data"})
            if response.status_code in [400, 422]:  # Bad request or validation error
                errors_caught += 1
        except:
            pass
            
        # Test empty messages
        try:
            response = requests.post(f"{self.base_url}/api/v1/generate", json={"messages": []})
            if response.status_code in [400, 422]:
                errors_caught += 1
        except:
            pass
            
        duration = time.time() - start_time
        
        if errors_caught >= 2:
            self.log_test("Error Handling", True, f"Caught {errors_caught}/3 errors properly", duration)
        else:
            self.log_test("Error Handling", False, f"Only caught {errors_caught}/3 errors", duration)
            
    def test_vram_clear_endpoint(self):
        """Test 9: VRAM clearing"""
        start_time = time.time()
        try:
            response = requests.post(f"{self.base_url}/clear_vram", timeout=30)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    vram_status = data.get("vram_status", {})
                    usage = vram_status.get("usage_percentage", 0)
                    self.log_test("VRAM Clear", True, f"Usage after clear: {usage}%", duration)
                else:
                    self.log_test("VRAM Clear", False, "Status not success", duration)
            else:
                self.log_test("VRAM Clear", False, f"Status: {response.status_code}", duration)
        except Exception as e:
            self.log_test("VRAM Clear", False, str(e), time.time() - start_time)
            
    def test_performance_benchmark(self):
        """Test 10: Performance benchmark"""
        print("\n🚀 Running performance benchmark...")
        
        # Warm up
        try:
            requests.post(f"{self.base_url}/api/v1/generate", 
                         json={"messages": [{"role": "user", "content": "Hi"}], "max_new_tokens": 5}, 
                         timeout=60)
        except:
            pass
            
        # Benchmark different token lengths
        token_lengths = [10, 50, 100]
        for tokens in token_lengths:
            start_time = time.time()
            try:
                data = {
                    "messages": [
                        {"role": "user", "content": f"Write exactly {tokens//2} words about artificial intelligence."}
                    ],
                    "max_new_tokens": tokens
                }
                
                response = requests.post(f"{self.base_url}/api/v1/generate", json=data, timeout=120)
                duration = time.time() - start_time
                
                if response.status_code == 200:
                    result = response.json()
                    actual_tokens = result.get("usage", {}).get("output_tokens", 0)
                    tokens_per_sec = actual_tokens / duration if duration > 0 else 0
                    self.log_test(f"Performance ({tokens} tokens)", True, 
                                f"{tokens_per_sec:.1f} tokens/sec", duration)
                else:
                    self.log_test(f"Performance ({tokens} tokens)", False, 
                                f"Failed with status {response.status_code}", duration)
            except Exception as e:
                self.log_test(f"Performance ({tokens} tokens)", False, str(e), time.time() - start_time)
                
    def run_all_tests(self):
        """Run all test cases"""
        print("🧪 Starting VLM Server Test Suite\n")
        
        # Check if server is accessible
        if not self.wait_for_server():
            print("❌ Cannot connect to server. Make sure it's running.")
            return False
            
        print("\n📋 Running Test Cases:\n")
        
        # Run tests in order
        self.test_health_endpoint()
        self.test_vram_status_endpoint()
        self.test_simple_text_generation()
        self.test_complex_text_generation()
        self.test_image_analysis_url()
        self.test_multi_turn_conversation()
        self.test_parameter_variations()
        self.test_error_handling()
        self.test_vram_clear_endpoint()
        self.test_performance_benchmark()
        
        # Print summary
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
        print(f"Total Runtime: {sum(r['duration'] for r in self.test_results):.2f}s")
        
        # Show failed tests
        failed_tests = [r for r in self.test_results if not r["success"]]
        if failed_tests:
            print(f"\n❌ Failed Tests:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['details']}")
        else:
            print("\n🎉 All tests passed!")
            
        print("\n" + "="*60)
        return success_rate >= 80  # Consider 80%+ success rate as passing


def main():
    """Main test function"""
    tester = VLMServerTester()
    
    # Check if server is already running
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("🔍 Found running server, using existing instance")
            tester.run_all_tests()
            return
    except:
        pass
    
    print("⚠️  No server detected. Please start the server first:")
    print("   source ~/pytorch-env/bin/activate")
    print("   python vlm_server.py")
    print("\nThen run this test script again.")


if __name__ == "__main__":
    main()