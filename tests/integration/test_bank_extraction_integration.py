"""
Integration tests for bank extraction pipeline
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import json
import base64
from pathlib import Path
import os

# These will be imported from the actual implementation
# from services.vlm.unified_llm_provider import UnifiedLLMProvider
# from services.vlm.langchain_extractor import LangChainExtractor
# from services.vlm.bank_parser_v3 import BankStatement
# from services.vlm.vlm_server import extract_bank_transactions


class TestBankExtractionPipeline:
    """Integration tests for complete bank extraction pipeline"""
    
    @pytest.fixture
    def test_image_path(self):
        """Path to test bank statement image"""
        return "/home/teke/projects/vlm_server/tests/BankStatementChequing.png"
    
    @pytest.fixture
    def test_image_base64(self, test_image_path):
        """Load test image as base64"""
        if os.path.exists(test_image_path):
            with open(test_image_path, "rb") as f:
                return base64.b64encode(f.read()).decode()
        return None
    
    @pytest.fixture
    async def unified_provider(self):
        """Create real UnifiedLLMProvider"""
        # provider = UnifiedLLMProvider()
        # await provider.initialize()
        # return provider
        pass
    
    @pytest.fixture
    def langchain_extractor(self, unified_provider):
        """Create LangChainExtractor with unified provider"""
        # extractor = LangChainExtractor(provider=unified_provider)
        # return extractor
        pass
    
    @pytest.mark.asyncio
    async def test_local_vlm_extraction(self, langchain_extractor, test_image_base64):
        """Test bank extraction using local VLM"""
        if not test_image_base64:
            pytest.skip("Test image not found")
        
        # Ensure using local provider
        langchain_extractor.provider.switch_provider("local")
        
        # Extract transactions
        result = await langchain_extractor.extract_bank_transactions(test_image_base64)
        
        # Validate result
        assert isinstance(result, dict)
        assert "transactions" in result
        assert len(result["transactions"]) > 0
        
        # Check transaction structure
        first_tx = result["transactions"][0]
        assert "date" in first_tx
        assert "description" in first_tx
        assert "debit" in first_tx or "credit" in first_tx
        assert "balance" in first_tx
    
    @pytest.mark.asyncio
    @pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OpenAI API key not set")
    async def test_openai_extraction(self, langchain_extractor, test_image_base64):
        """Test bank extraction using OpenAI"""
        if not test_image_base64:
            pytest.skip("Test image not found")
        
        # Switch to OpenAI provider
        langchain_extractor.provider.switch_provider("openai")
        
        # Extract transactions
        result = await langchain_extractor.extract_bank_transactions(test_image_base64)
        
        # Validate result
        assert isinstance(result, dict)
        assert "transactions" in result
        assert len(result["transactions"]) > 0
    
    @pytest.mark.asyncio
    async def test_provider_fallback(self, langchain_extractor, test_image_base64):
        """Test fallback from OpenAI to local on error"""
        if not test_image_base64:
            pytest.skip("Test image not found")
        
        # Mock OpenAI to fail
        with patch.object(langchain_extractor.provider.providers["openai"], "generate") as mock_openai:
            mock_openai.side_effect = Exception("API Error")
            
            # Switch to OpenAI
            langchain_extractor.provider.switch_provider("openai")
            
            # Extract with fallback enabled
            result = await langchain_extractor.extract_bank_transactions(
                test_image_base64,
                allow_fallback=True
            )
            
            # Should still get results via fallback
            assert isinstance(result, dict)
            assert "transactions" in result
    
    @pytest.mark.asyncio
    async def test_csv_export(self, langchain_extractor, test_image_base64):
        """Test CSV export functionality"""
        if not test_image_base64:
            pytest.skip("Test image not found")
        
        # Extract transactions
        result = await langchain_extractor.extract_bank_transactions(test_image_base64)
        
        # Convert to CSV
        bank_statement = BankStatement(**result)
        csv_content = bank_statement.to_csv()
        
        # Validate CSV
        assert "Date,Description,Category,Debit,Credit,Balance" in csv_content
        assert len(csv_content.split("\n")) > 2  # Header + transactions
    
    @pytest.mark.asyncio
    async def test_json_export(self, langchain_extractor, test_image_base64):
        """Test JSON export functionality"""
        if not test_image_base64:
            pytest.skip("Test image not found")
        
        # Extract transactions
        result = await langchain_extractor.extract_bank_transactions(test_image_base64)
        
        # Convert to JSON
        bank_statement = BankStatement(**result)
        json_content = bank_statement.to_json_pretty()
        
        # Validate JSON
        parsed = json.loads(json_content)
        assert "transactions" in parsed
        assert isinstance(parsed["transactions"], list)
    
    @pytest.mark.asyncio
    async def test_transaction_validation(self, langchain_extractor, test_image_base64):
        """Test transaction validation and normalization"""
        if not test_image_base64:
            pytest.skip("Test image not found")
        
        # Extract transactions
        result = await langchain_extractor.extract_bank_transactions(test_image_base64)
        
        # Validate each transaction
        for tx in result["transactions"]:
            # Date should be normalized to MM/DD/YYYY
            assert len(tx["date"].split("/")) == 3
            
            # Amounts should be positive
            if tx.get("debit"):
                assert tx["debit"] >= 0
            if tx.get("credit"):
                assert tx["credit"] >= 0
            
            # Should have a category
            assert tx.get("category") is not None
    
    @pytest.mark.asyncio
    async def test_balance_consistency(self, langchain_extractor, test_image_base64):
        """Test balance calculation consistency"""
        if not test_image_base64:
            pytest.skip("Test image not found")
        
        # Extract transactions
        result = await langchain_extractor.extract_bank_transactions(test_image_base64)
        
        # Check balance consistency
        if len(result["transactions"]) > 1:
            for i in range(1, len(result["transactions"])):
                prev_tx = result["transactions"][i-1]
                curr_tx = result["transactions"][i]
                
                # Calculate expected balance
                expected_balance = prev_tx.get("balance", 0)
                expected_balance -= curr_tx.get("debit", 0)
                expected_balance += curr_tx.get("credit", 0)
                
                # Allow small rounding differences
                if curr_tx.get("balance"):
                    assert abs(curr_tx["balance"] - expected_balance) < 0.01


class TestAPIIntegration:
    """Test API endpoint integration"""
    
    @pytest.fixture
    def mock_app(self):
        """Mock FastAPI app"""
        # from services.vlm.vlm_server import app
        # return app
        pass
    
    @pytest.mark.asyncio
    async def test_bank_extract_endpoint(self, mock_app):
        """Test /api/v1/bank_extract endpoint"""
        # Create test request
        request_data = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extract bank transactions"},
                        {"type": "image", "image": "base64_image_data"}
                    ]
                }
            ],
            "max_new_tokens": 3000,
            "temperature": 0.1
        }
        
        # Test endpoint
        # response = await mock_app.post("/api/v1/bank_extract", json=request_data)
        # assert response.status_code == 200
        # 
        # data = response.json()
        # assert data["status"] == "success"
        # assert "data" in data
        # assert "metadata" in data
    
    @pytest.mark.asyncio
    async def test_provider_switching_endpoint(self, mock_app):
        """Test provider switching via API"""
        # Test switching to OpenAI
        # response = await mock_app.post("/api/v1/switch_provider", json={"provider": "openai"})
        # assert response.status_code == 200
        # assert response.json()["current_provider"] == "openai"
        
        # Test switching back to local
        # response = await mock_app.post("/api/v1/switch_provider", json={"provider": "local"})
        # assert response.status_code == 200
        # assert response.json()["current_provider"] == "local"
        pass
    
    @pytest.mark.asyncio
    async def test_sensitive_content_warning(self, mock_app):
        """Test sensitive content detection and warning"""
        # Create request with sensitive content
        request_data = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Process bank account 123456789"},
                        {"type": "image", "image": "base64_image_data"}
                    ]
                }
            ]
        }
        
        # Test with OpenAI provider (should trigger warning)
        # await mock_app.post("/api/v1/switch_provider", json={"provider": "openai"})
        # response = await mock_app.post("/api/v1/generate", json=request_data)
        # 
        # # Should include warning in response
        # assert "sensitive_content_warning" in response.json()
        pass


class TestErrorHandling:
    """Test error handling across the pipeline"""
    
    @pytest.mark.asyncio
    async def test_invalid_image_handling(self, langchain_extractor):
        """Test handling of invalid image data"""
        # Test with invalid base64
        with pytest.raises(Exception):
            await langchain_extractor.extract_bank_transactions("invalid_base64")
    
    @pytest.mark.asyncio
    async def test_empty_response_handling(self, langchain_extractor):
        """Test handling of empty LLM responses"""
        # Mock empty response
        with patch.object(langchain_extractor.llm, "_call") as mock_call:
            mock_call.return_value = ""
            
            result = await langchain_extractor.extract_bank_transactions("image_data")
            
            # Should return empty statement
            assert result["transactions"] == []
    
    @pytest.mark.asyncio
    async def test_malformed_json_handling(self, langchain_extractor):
        """Test handling of malformed JSON responses"""
        # Mock malformed JSON
        with patch.object(langchain_extractor.llm, "_call") as mock_call:
            mock_call.return_value = '{"transactions": [{"date": "invalid"'
            
            result = await langchain_extractor.extract_bank_transactions("image_data")
            
            # Should attempt table parsing or return empty
            assert isinstance(result, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])