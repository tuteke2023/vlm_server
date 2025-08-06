"""
Unit tests for UnifiedLLMProvider
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any
import json
import os

# These will be imported from the actual implementation
# from services.vlm.unified_llm_provider import UnifiedLLMProvider, LLMMessage, LLMResponse
# from services.vlm.openai_provider import OpenAIProvider
# from services.vlm.local_vlm_provider import LocalVLMProvider


class TestUnifiedLLMProvider:
    """Test suite for UnifiedLLMProvider"""
    
    @pytest.fixture
    def mock_local_provider(self):
        """Mock local VLM provider"""
        provider = Mock()
        provider.name = "local"
        provider.is_available = Mock(return_value=True)
        provider.generate = AsyncMock()
        provider.get_model_info = Mock(return_value={"name": "Qwen2.5-VL-3B-Instruct", "size": "3B"})
        return provider
    
    @pytest.fixture
    def mock_openai_provider(self):
        """Mock OpenAI provider"""
        provider = Mock()
        provider.name = "openai"
        provider.is_available = Mock(return_value=True)
        provider.generate = AsyncMock()
        provider.get_model_info = Mock(return_value={"name": "gpt-4o", "type": "cloud"})
        return provider
    
    @pytest.fixture
    def unified_provider(self, mock_local_provider, mock_openai_provider):
        """Create UnifiedLLMProvider with mocked providers"""
        # This will be replaced with actual implementation
        # provider = UnifiedLLMProvider()
        # provider.providers = {
        #     "local": mock_local_provider,
        #     "openai": mock_openai_provider
        # }
        # return provider
        pass
    
    @pytest.mark.asyncio
    async def test_provider_switching(self, unified_provider):
        """Test switching between providers"""
        # Test switching to OpenAI
        result = unified_provider.switch_provider("openai")
        assert result["status"] == "success"
        assert unified_provider.current_provider == "openai"
        
        # Test switching to local
        result = unified_provider.switch_provider("local")
        assert result["status"] == "success"
        assert unified_provider.current_provider == "local"
        
        # Test switching to invalid provider
        result = unified_provider.switch_provider("invalid")
        assert result["status"] == "error"
        assert "not found" in result["message"]
    
    @pytest.mark.asyncio
    async def test_generate_with_local_provider(self, unified_provider, mock_local_provider):
        """Test generation with local provider"""
        # Set up mock response
        mock_response = Mock()
        mock_response.content = "Local VLM response"
        mock_response.metadata = {"provider": "local", "model": "Qwen2.5-VL-3B"}
        mock_response.usage = {"prompt_tokens": 100, "completion_tokens": 50}
        mock_local_provider.generate.return_value = mock_response
        
        # Test generation
        messages = [{"role": "user", "content": "Test prompt"}]
        response = await unified_provider.generate(messages)
        
        assert response.content == "Local VLM response"
        assert response.metadata["provider"] == "local"
        mock_local_provider.generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_with_openai_provider(self, unified_provider, mock_openai_provider):
        """Test generation with OpenAI provider"""
        # Switch to OpenAI
        unified_provider.switch_provider("openai")
        
        # Set up mock response
        mock_response = Mock()
        mock_response.content = "OpenAI response"
        mock_response.metadata = {"provider": "openai", "model": "gpt-4o"}
        mock_response.usage = {"prompt_tokens": 100, "completion_tokens": 50}
        mock_openai_provider.generate.return_value = mock_response
        
        # Test generation
        messages = [{"role": "user", "content": "Test prompt"}]
        response = await unified_provider.generate(messages)
        
        assert response.content == "OpenAI response"
        assert response.metadata["provider"] == "openai"
        mock_openai_provider.generate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_fallback_mechanism(self, unified_provider, mock_openai_provider, mock_local_provider):
        """Test fallback from OpenAI to local on error"""
        # Switch to OpenAI
        unified_provider.switch_provider("openai")
        
        # Mock OpenAI failure
        mock_openai_provider.generate.side_effect = Exception("API Error")
        
        # Mock local success
        mock_response = Mock()
        mock_response.content = "Fallback response"
        mock_local_provider.generate.return_value = mock_response
        
        # Test generation with fallback
        messages = [{"role": "user", "content": "Test prompt"}]
        response = await unified_provider.generate(messages, allow_fallback=True)
        
        # Should have tried OpenAI first, then fallen back to local
        assert mock_openai_provider.generate.called
        assert mock_local_provider.generate.called
        assert response.content == "Fallback response"
    
    @pytest.mark.asyncio
    async def test_sensitive_content_detection(self, unified_provider):
        """Test sensitive content detection"""
        # Test with sensitive content
        messages = [{"role": "user", "content": "Process bank statement for account 123456789"}]
        is_sensitive = unified_provider.contains_sensitive_content(messages)
        assert is_sensitive is True
        
        # Test with non-sensitive content
        messages = [{"role": "user", "content": "What is the weather today?"}]
        is_sensitive = unified_provider.contains_sensitive_content(messages)
        assert is_sensitive is False
    
    @pytest.mark.asyncio
    async def test_provider_availability_check(self, unified_provider, mock_openai_provider):
        """Test provider availability checking"""
        # Test when OpenAI is available
        mock_openai_provider.is_available.return_value = True
        available = unified_provider.is_provider_available("openai")
        assert available is True
        
        # Test when OpenAI is not available (no API key)
        mock_openai_provider.is_available.return_value = False
        available = unified_provider.is_provider_available("openai")
        assert available is False
    
    @pytest.mark.asyncio
    async def test_message_format_conversion(self, unified_provider):
        """Test message format conversion for different providers"""
        # Test with text and image message
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Analyze this image"},
                    {"type": "image", "image": "base64_image_data"}
                ]
            }
        ]
        
        # Convert for local provider
        local_messages = unified_provider.convert_messages_for_provider(messages, "local")
        assert len(local_messages) == 1
        assert local_messages[0]["role"] == "user"
        assert isinstance(local_messages[0]["content"], list)
        
        # Convert for OpenAI provider
        openai_messages = unified_provider.convert_messages_for_provider(messages, "openai")
        assert len(openai_messages) == 1
        assert openai_messages[0]["role"] == "user"
        assert isinstance(openai_messages[0]["content"], list)
        assert openai_messages[0]["content"][1]["type"] == "image_url"
    
    def test_get_all_providers(self, unified_provider):
        """Test getting all available providers"""
        providers = unified_provider.get_all_providers()
        assert "local" in providers
        assert "openai" in providers
        assert providers["local"]["available"] is True
        assert providers["local"]["model"]["name"] == "Qwen2.5-VL-3B-Instruct"
    
    @pytest.mark.asyncio
    async def test_temperature_and_max_tokens(self, unified_provider, mock_local_provider):
        """Test passing temperature and max_tokens parameters"""
        messages = [{"role": "user", "content": "Test"}]
        
        # Test with custom parameters
        await unified_provider.generate(
            messages,
            temperature=0.5,
            max_tokens=2000
        )
        
        # Verify parameters were passed to provider
        call_args = mock_local_provider.generate.call_args
        assert call_args[1]["temperature"] == 0.5
        assert call_args[1]["max_tokens"] == 2000
    
    @pytest.mark.asyncio
    async def test_error_handling(self, unified_provider, mock_local_provider):
        """Test error handling in generation"""
        # Mock provider error
        mock_local_provider.generate.side_effect = Exception("Provider error")
        
        # Test generation without fallback
        messages = [{"role": "user", "content": "Test"}]
        with pytest.raises(Exception) as exc_info:
            await unified_provider.generate(messages, allow_fallback=False)
        
        assert "Provider error" in str(exc_info.value)


class TestProviderIntegration:
    """Integration tests for provider implementations"""
    
    @pytest.mark.asyncio
    async def test_local_provider_initialization(self):
        """Test local VLM provider initialization"""
        # Test implementation would check actual initialization
        pass
    
    @pytest.mark.asyncio
    async def test_openai_provider_initialization(self):
        """Test OpenAI provider initialization"""
        # Test with API key
        os.environ["OPENAI_API_KEY"] = "test_key"
        # provider = OpenAIProvider()
        # assert provider.is_available() is True
        
        # Test without API key
        os.environ.pop("OPENAI_API_KEY", None)
        # provider = OpenAIProvider()
        # assert provider.is_available() is False
    
    @pytest.mark.asyncio
    async def test_provider_response_format(self):
        """Test that all providers return consistent response format"""
        # This would test actual provider implementations
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])