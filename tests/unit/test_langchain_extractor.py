"""
Unit tests for LangChainExtractor
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any
import json
from datetime import datetime

# These will be imported from the actual implementation
# from services.vlm.langchain_extractor import LangChainExtractor, LangChainLLM
# from services.vlm.bank_parser_v3 import BankTransaction, BankStatement


class TestLangChainLLM:
    """Test suite for custom LangChain LLM wrapper"""
    
    @pytest.fixture
    def mock_unified_provider(self):
        """Mock UnifiedLLMProvider"""
        provider = Mock()
        provider.generate = AsyncMock()
        provider.current_provider = "local"
        return provider
    
    @pytest.fixture
    def langchain_llm(self, mock_unified_provider):
        """Create LangChainLLM with mocked provider"""
        # llm = LangChainLLM(provider=mock_unified_provider)
        # return llm
        pass
    
    def test_call_method(self, langchain_llm, mock_unified_provider):
        """Test _call method that LangChain uses"""
        # Set up mock response
        mock_response = Mock()
        mock_response.content = "LLM response"
        mock_unified_provider.generate.return_value = mock_response
        
        # Test call
        prompt = "Extract bank transactions"
        result = langchain_llm._call(prompt)
        
        assert result == "LLM response"
        mock_unified_provider.generate.assert_called_once()
        
        # Check message format
        call_args = mock_unified_provider.generate.call_args
        messages = call_args[0][0]
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == prompt
    
    def test_llm_type_property(self, langchain_llm):
        """Test _llm_type property"""
        assert langchain_llm._llm_type == "unified_llm"
    
    def test_identifying_params(self, langchain_llm, mock_unified_provider):
        """Test _identifying_params property"""
        params = langchain_llm._identifying_params
        assert "provider" in params
        assert params["provider"] == "local"
    
    @pytest.mark.asyncio
    async def test_async_call(self, langchain_llm, mock_unified_provider):
        """Test async _acall method"""
        # Set up mock response
        mock_response = Mock()
        mock_response.content = "Async LLM response"
        mock_unified_provider.generate.return_value = mock_response
        
        # Test async call
        prompt = "Extract bank transactions"
        result = await langchain_llm._acall(prompt)
        
        assert result == "Async LLM response"
        mock_unified_provider.generate.assert_called_once()
    
    def test_error_handling(self, langchain_llm, mock_unified_provider):
        """Test error handling in LLM calls"""
        # Mock provider error
        mock_unified_provider.generate.side_effect = Exception("Provider error")
        
        # Test call with error
        with pytest.raises(Exception) as exc_info:
            langchain_llm._call("Test prompt")
        
        assert "Provider error" in str(exc_info.value)


class TestLangChainExtractor:
    """Test suite for LangChainExtractor"""
    
    @pytest.fixture
    def mock_llm(self):
        """Mock LangChain LLM"""
        llm = Mock()
        llm._call = Mock()
        llm._acall = AsyncMock()
        return llm
    
    @pytest.fixture
    def extractor(self, mock_llm):
        """Create LangChainExtractor with mocked LLM"""
        # extractor = LangChainExtractor(llm=mock_llm)
        # return extractor
        pass
    
    @pytest.mark.asyncio
    async def test_extract_bank_transactions(self, extractor, mock_llm):
        """Test bank transaction extraction"""
        # Mock LLM response with proper JSON
        mock_response = {
            "transactions": [
                {
                    "date": "01/15/2025",
                    "description": "GROCERY STORE",
                    "category": "Groceries",
                    "debit": 125.50,
                    "credit": 0,
                    "balance": 1874.50
                },
                {
                    "date": "01/16/2025",
                    "description": "SALARY DEPOSIT",
                    "category": "Income",
                    "debit": 0,
                    "credit": 3000.00,
                    "balance": 4874.50
                }
            ],
            "total_debits": 125.50,
            "total_credits": 3000.00
        }
        mock_llm._call.return_value = json.dumps(mock_response)
        
        # Test extraction
        image_data = "base64_encoded_image"
        result = await extractor.extract_bank_transactions(image_data)
        
        assert isinstance(result, dict)  # Should be BankStatement
        assert len(result["transactions"]) == 2
        assert result["total_debits"] == 125.50
        assert result["total_credits"] == 3000.00
    
    @pytest.mark.asyncio
    async def test_extract_with_fallback_parsing(self, extractor, mock_llm):
        """Test extraction with fallback to table parsing"""
        # Mock LLM response with table format (not JSON)
        mock_table_response = """
        Date | Description | Debit | Credit | Balance
        01/15/2025 | GROCERY STORE | 125.50 | - | 1874.50
        01/16/2025 | SALARY DEPOSIT | - | 3000.00 | 4874.50
        """
        mock_llm._call.return_value = mock_table_response
        
        # Test extraction
        image_data = "base64_encoded_image"
        result = await extractor.extract_bank_transactions(image_data)
        
        # Should fall back to table parsing
        assert isinstance(result, dict)
        assert len(result["transactions"]) == 2
    
    @pytest.mark.asyncio
    async def test_extract_general_content(self, extractor, mock_llm):
        """Test general content extraction"""
        # Mock LLM response
        mock_llm._call.return_value = "This image contains a cat"
        
        # Test extraction
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What's in this image?"},
                    {"type": "image", "image": "base64_image"}
                ]
            }
        ]
        result = await extractor.extract_general(messages)
        
        assert result == "This image contains a cat"
        mock_llm._call.assert_called_once()
    
    def test_create_bank_extraction_prompt(self, extractor):
        """Test bank extraction prompt creation"""
        prompt = extractor.create_bank_extraction_prompt()
        
        # Check key elements in prompt
        assert "bank statement" in prompt.lower()
        assert "transactions" in prompt.lower()
        assert "debit" in prompt.lower()
        assert "credit" in prompt.lower()
        assert "json" in prompt.lower()
    
    def test_validate_bank_statement(self, extractor):
        """Test bank statement validation"""
        # Valid statement
        valid_statement = {
            "transactions": [
                {
                    "date": "01/15/2025",
                    "description": "Test",
                    "debit": 100,
                    "credit": 0,
                    "balance": 900
                }
            ]
        }
        is_valid = extractor.validate_bank_statement(valid_statement)
        assert is_valid is True
        
        # Invalid statement (missing transactions)
        invalid_statement = {"data": "invalid"}
        is_valid = extractor.validate_bank_statement(invalid_statement)
        assert is_valid is False
    
    @pytest.mark.asyncio
    async def test_retry_mechanism(self, extractor, mock_llm):
        """Test retry mechanism on parsing failure"""
        # First attempt fails, second succeeds
        mock_llm._call.side_effect = [
            "Invalid response",
            json.dumps({
                "transactions": [
                    {"date": "01/15/2025", "description": "Test", "debit": 100}
                ]
            })
        ]
        
        # Test extraction with retry
        image_data = "base64_encoded_image"
        result = await extractor.extract_bank_transactions(image_data, max_retries=2)
        
        # Should succeed after retry
        assert len(result["transactions"]) == 1
        assert mock_llm._call.call_count == 2
    
    def test_parse_mixed_format_response(self, extractor):
        """Test parsing response with mixed formats"""
        # Response with both JSON and text
        mixed_response = """
        Here are the transactions:
        
        {
            "transactions": [
                {"date": "01/15/2025", "description": "Purchase", "debit": 50.00}
            ]
        }
        
        Total: $50.00
        """
        
        result = extractor.parse_bank_response(mixed_response)
        assert len(result["transactions"]) == 1
        assert result["transactions"][0]["debit"] == 50.00
    
    @pytest.mark.asyncio
    async def test_chain_composition(self, extractor):
        """Test LangChain chain composition"""
        # Test that the extractor properly composes chains
        chain = extractor.create_extraction_chain()
        
        assert hasattr(chain, "invoke")
        assert hasattr(chain, "ainvoke")
        
        # Test chain components
        assert "prompt" in chain.steps
        assert "llm" in chain.steps
        assert "parser" in chain.steps
    
    @pytest.mark.asyncio
    async def test_temperature_control(self, extractor, mock_llm):
        """Test temperature parameter usage"""
        # Extract with low temperature for consistency
        await extractor.extract_bank_transactions(
            "image_data",
            temperature=0.1
        )
        
        # Verify temperature was passed
        call_kwargs = mock_llm._call.call_args[1]
        assert call_kwargs.get("temperature") == 0.1
    
    def test_format_instructions(self, extractor):
        """Test format instructions for structured output"""
        instructions = extractor.get_format_instructions()
        
        # Should include schema details
        assert "date" in instructions
        assert "description" in instructions
        assert "debit" in instructions
        assert "credit" in instructions
        assert "balance" in instructions


class TestBankStatementValidation:
    """Test bank statement validation and processing"""
    
    def test_transaction_validation(self):
        """Test individual transaction validation"""
        # Valid transaction
        valid_tx = {
            "date": "01/15/2025",
            "description": "Purchase",
            "debit": 100.50,
            "credit": 0,
            "balance": 900.50
        }
        # tx = BankTransaction(**valid_tx)
        # assert tx.debit == 100.50
        
        # Invalid date format should be normalized
        invalid_date_tx = {
            "date": "15-01-2025",
            "description": "Purchase",
            "debit": 100
        }
        # tx = BankTransaction(**invalid_date_tx)
        # assert tx.date == "01/15/2025"  # Normalized
    
    def test_auto_categorization(self):
        """Test automatic transaction categorization"""
        transactions = [
            {"date": "01/15/2025", "description": "WALMART GROCERY", "debit": 150},
            {"date": "01/16/2025", "description": "SHELL GAS STATION", "debit": 75},
            {"date": "01/17/2025", "description": "SALARY DEPOSIT", "credit": 3000},
            {"date": "01/18/2025", "description": "NETFLIX SUBSCRIPTION", "debit": 15.99}
        ]
        
        # for tx_data in transactions:
        #     tx = BankTransaction(**tx_data)
        #     if "walmart" in tx.description.lower():
        #         assert tx.category == "Groceries"
        #     elif "shell" in tx.description.lower():
        #         assert tx.category == "Transportation"
        #     elif "salary" in tx.description.lower():
        #         assert tx.category == "Income"
        #     elif "netflix" in tx.description.lower():
        #         assert tx.category == "Entertainment"
    
    def test_balance_calculation(self):
        """Test running balance calculation"""
        statement_data = {
            "opening_balance": 1000.00,
            "transactions": [
                {"date": "01/15/2025", "description": "Purchase", "debit": 100},
                {"date": "01/16/2025", "description": "Deposit", "credit": 500}
            ]
        }
        
        # statement = BankStatement(**statement_data)
        # statement.calculate_totals()
        # 
        # assert statement.total_debits == 100
        # assert statement.total_credits == 500
        # Expected closing balance: 1000 - 100 + 500 = 1400


if __name__ == "__main__":
    pytest.main([__file__, "-v"])