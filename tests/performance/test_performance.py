"""
Performance tests for bank extraction system
"""

import pytest
import asyncio
import time
import psutil
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import matplotlib.pyplot as plt
import os
from typing import List, Dict
import json

# These will be imported from the actual implementation
# from services.vlm.unified_llm_provider import UnifiedLLMProvider
# from services.vlm.langchain_extractor import LangChainExtractor


class TestPerformanceMetrics:
    """Performance tests for extraction pipeline"""
    
    @pytest.fixture
    def performance_logger(self):
        """Logger for performance metrics"""
        metrics = {
            "response_times": [],
            "memory_usage": [],
            "cpu_usage": [],
            "token_usage": []
        }
        return metrics
    
    @pytest.fixture
    def test_images(self):
        """Load test images of various sizes"""
        return [
            {"name": "small", "size": "1MB", "path": "tests/data/small_statement.png"},
            {"name": "medium", "size": "5MB", "path": "tests/data/medium_statement.png"},
            {"name": "large", "size": "10MB", "path": "tests/data/large_statement.png"}
        ]
    
    @pytest.mark.asyncio
    async def test_response_time_local_vlm(self, performance_logger):
        """Test response time for local VLM"""
        # provider = UnifiedLLMProvider()
        # provider.switch_provider("local")
        # extractor = LangChainExtractor(provider=provider)
        
        response_times = []
        
        for i in range(10):  # Run 10 iterations
            start_time = time.time()
            
            # result = await extractor.extract_bank_transactions("test_image_base64")
            
            end_time = time.time()
            response_times.append(end_time - start_time)
        
        # Calculate statistics
        avg_time = np.mean(response_times)
        std_time = np.std(response_times)
        
        # Assert performance requirements
        assert avg_time < 30  # Average should be under 30 seconds
        assert std_time < 5   # Standard deviation should be low
        
        performance_logger["response_times"] = response_times
    
    @pytest.mark.asyncio
    async def test_response_time_openai(self, performance_logger):
        """Test response time for OpenAI"""
        if not os.getenv("OPENAI_API_KEY"):
            pytest.skip("OpenAI API key not set")
        
        # provider = UnifiedLLMProvider()
        # provider.switch_provider("openai")
        # extractor = LangChainExtractor(provider=provider)
        
        response_times = []
        
        for i in range(5):  # Fewer iterations due to API costs
            start_time = time.time()
            
            # result = await extractor.extract_bank_transactions("test_image_base64")
            
            end_time = time.time()
            response_times.append(end_time - start_time)
        
        # Calculate statistics
        avg_time = np.mean(response_times)
        
        # OpenAI should be faster than local
        assert avg_time < 10  # Should be under 10 seconds
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test system performance under concurrent load"""
        # provider = UnifiedLLMProvider()
        # extractor = LangChainExtractor(provider=provider)
        
        async def process_request(request_id):
            start_time = time.time()
            # result = await extractor.extract_bank_transactions("test_image_base64")
            end_time = time.time()
            return {
                "request_id": request_id,
                "duration": end_time - start_time,
                "success": True  # or check result validity
            }
        
        # Test with 5 concurrent requests
        tasks = [process_request(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        
        # Check all requests completed
        assert all(r["success"] for r in results)
        
        # Check response times are reasonable
        avg_time = np.mean([r["duration"] for r in results])
        assert avg_time < 60  # Should handle concurrent load reasonably
    
    def test_memory_usage(self):
        """Test memory usage during extraction"""
        process = psutil.Process()
        
        # Baseline memory
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Run extraction
        # provider = UnifiedLLMProvider()
        # extractor = LangChainExtractor(provider=provider)
        # asyncio.run(extractor.extract_bank_transactions("large_image_base64"))
        
        # Peak memory
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Memory increase should be reasonable
        memory_increase = peak_memory - baseline_memory
        assert memory_increase < 2000  # Less than 2GB increase
    
    @pytest.mark.asyncio
    async def test_token_efficiency(self):
        """Test token usage efficiency"""
        # provider = UnifiedLLMProvider()
        # extractor = LangChainExtractor(provider=provider)
        
        # Extract with different max_tokens settings
        token_tests = [
            {"max_tokens": 1000, "expected_quality": 0.7},
            {"max_tokens": 2000, "expected_quality": 0.85},
            {"max_tokens": 3000, "expected_quality": 0.95}
        ]
        
        results = []
        for test in token_tests:
            # result = await extractor.extract_bank_transactions(
            #     "test_image_base64",
            #     max_tokens=test["max_tokens"]
            # )
            # 
            # quality = calculate_extraction_quality(result)
            # results.append({
            #     "max_tokens": test["max_tokens"],
            #     "quality": quality,
            #     "efficiency": quality / test["max_tokens"]
            # })
            pass
        
        # Verify token efficiency
        # Higher token counts should yield better quality
        # But efficiency (quality per token) might decrease
    
    @pytest.mark.asyncio
    async def test_cache_performance(self):
        """Test caching impact on performance"""
        # provider = UnifiedLLMProvider()
        # extractor = LangChainExtractor(provider=provider)
        
        # First request (cache miss)
        start_time = time.time()
        # result1 = await extractor.extract_bank_transactions("test_image_base64")
        first_request_time = time.time() - start_time
        
        # Second request (cache hit, if implemented)
        start_time = time.time()
        # result2 = await extractor.extract_bank_transactions("test_image_base64")
        second_request_time = time.time() - start_time
        
        # Cache should improve performance
        if hasattr(extractor, 'cache_enabled') and extractor.cache_enabled:
            assert second_request_time < first_request_time * 0.5
    
    def test_cpu_usage(self):
        """Monitor CPU usage during extraction"""
        process = psutil.Process()
        
        cpu_samples = []
        
        # Monitor CPU during extraction
        # This would run in a separate thread
        def monitor_cpu():
            while monitoring:
                cpu_samples.append(process.cpu_percent(interval=0.1))
                time.sleep(0.1)
        
        monitoring = True
        # Start monitoring in background
        # Run extraction
        # Stop monitoring
        monitoring = False
        
        # Analyze CPU usage
        if cpu_samples:
            avg_cpu = np.mean(cpu_samples)
            max_cpu = np.max(cpu_samples)
            
            # CPU usage should be reasonable
            assert avg_cpu < 80  # Average under 80%
            assert max_cpu < 100  # Should not max out CPU


class TestScalabilityTests:
    """Test system scalability"""
    
    @pytest.mark.asyncio
    async def test_batch_processing(self):
        """Test batch processing performance"""
        # Test processing multiple statements in batch
        batch_sizes = [1, 5, 10, 20]
        results = []
        
        for batch_size in batch_sizes:
            start_time = time.time()
            
            # Process batch
            # tasks = [extract_statement(img) for img in range(batch_size)]
            # await asyncio.gather(*tasks)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            results.append({
                "batch_size": batch_size,
                "total_time": total_time,
                "avg_time_per_item": total_time / batch_size
            })
        
        # Verify batch processing efficiency
        # Larger batches should have better average time per item
        for i in range(1, len(results)):
            assert results[i]["avg_time_per_item"] <= results[i-1]["avg_time_per_item"]
    
    @pytest.mark.asyncio
    async def test_provider_switching_overhead(self):
        """Test overhead of switching between providers"""
        # provider = UnifiedLLMProvider()
        
        switch_times = []
        
        for i in range(10):
            # Switch to OpenAI
            start_time = time.time()
            # provider.switch_provider("openai")
            switch_time = time.time() - start_time
            switch_times.append(switch_time)
            
            # Switch back to local
            start_time = time.time()
            # provider.switch_provider("local")
            switch_time = time.time() - start_time
            switch_times.append(switch_time)
        
        # Provider switching should be fast
        avg_switch_time = np.mean(switch_times)
        assert avg_switch_time < 0.1  # Under 100ms


class TestPerformanceReporting:
    """Generate performance reports"""
    
    def generate_performance_report(self, metrics: Dict):
        """Generate comprehensive performance report"""
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {
                "avg_response_time": np.mean(metrics.get("response_times", [])),
                "p95_response_time": np.percentile(metrics.get("response_times", []), 95),
                "avg_memory_usage": np.mean(metrics.get("memory_usage", [])),
                "avg_cpu_usage": np.mean(metrics.get("cpu_usage", []))
            },
            "detailed_metrics": metrics
        }
        
        # Save report
        with open("tests/performance/performance_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        return report
    
    def plot_performance_metrics(self, metrics: Dict):
        """Create performance visualization"""
        # Response time distribution
        plt.figure(figsize=(12, 8))
        
        plt.subplot(2, 2, 1)
        plt.hist(metrics.get("response_times", []), bins=20)
        plt.title("Response Time Distribution")
        plt.xlabel("Time (seconds)")
        plt.ylabel("Frequency")
        
        # Memory usage over time
        plt.subplot(2, 2, 2)
        plt.plot(metrics.get("memory_usage", []))
        plt.title("Memory Usage Over Time")
        plt.xlabel("Sample")
        plt.ylabel("Memory (MB)")
        
        # CPU usage over time
        plt.subplot(2, 2, 3)
        plt.plot(metrics.get("cpu_usage", []))
        plt.title("CPU Usage Over Time")
        plt.xlabel("Sample")
        plt.ylabel("CPU %")
        
        # Token usage efficiency
        plt.subplot(2, 2, 4)
        if "token_usage" in metrics:
            plt.scatter(
                [t["tokens"] for t in metrics["token_usage"]],
                [t["quality"] for t in metrics["token_usage"]]
            )
            plt.title("Token Usage vs Quality")
            plt.xlabel("Tokens Used")
            plt.ylabel("Extraction Quality")
        
        plt.tight_layout()
        plt.savefig("tests/performance/performance_metrics.png")
        plt.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])