"""
OpenAI API Provider for VLM Server
Provides GPT-4V capabilities as an alternative to local VLM
"""

import os
import base64
import logging
from typing import List, Dict, Optional, Union
from datetime import datetime
import openai
from openai import OpenAI
import json

logger = logging.getLogger(__name__)

class OpenAIProvider:
    """OpenAI API provider for vision and language tasks"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize OpenAI provider with API key from env or parameter"""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-4o"  # Use GPT-4o which supports vision
        logger.info(f"OpenAI provider initialized with model: {self.model}")
    
    def encode_image(self, image_data: str) -> str:
        """Ensure image is properly encoded for OpenAI API"""
        # If it's already a data URL, extract the base64 part
        if image_data.startswith('data:'):
            return image_data.split(',')[1]
        return image_data
    
    async def generate(self, messages: List[Dict], max_tokens: int = 4096, temperature: float = 0.7) -> Dict:
        """Generate response using OpenAI API"""
        try:
            start_time = datetime.now()
            
            # Convert messages to OpenAI format
            openai_messages = []
            
            for msg in messages:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                
                # Handle different content types
                if isinstance(content, str):
                    openai_messages.append({
                        "role": role,
                        "content": content
                    })
                elif isinstance(content, list):
                    # Handle mixed content (text + images)
                    content_parts = []
                    
                    for item in content:
                        # Handle both dict and object formats
                        if isinstance(item, dict):
                            item_type = item.get('type')
                            item_text = item.get('text', '')
                            item_image = item.get('image', '')
                        else:
                            # Handle object format (ContentItem)
                            item_type = getattr(item, 'type', None)
                            item_text = getattr(item, 'text', '')
                            item_image = getattr(item, 'image', '')
                        
                        if item_type == 'text':
                            content_parts.append({
                                "type": "text",
                                "text": item_text
                            })
                        elif item_type == 'image':
                            base64_image = self.encode_image(item_image)
                            content_parts.append({
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            })
                    
                    openai_messages.append({
                        "role": role,
                        "content": content_parts
                    })
            
            # Log external API usage if configured
            if os.getenv("LOG_EXTERNAL_API_USAGE", "true").lower() == "true":
                logger.info(f"Making OpenAI API call with {len(openai_messages)} messages, max_tokens={max_tokens}")
            
            # Make API call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Extract response
            result = {
                "response": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "processing_time": processing_time,
                "provider": "openai",
                "model": self.model
            }
            
            logger.info(f"OpenAI API call completed in {processing_time:.2f}s, tokens: {result['usage']['total_tokens']}")
            
            return result
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            raise Exception(f"OpenAI API error: {str(e)}")
    
    def check_sensitive_content(self, messages: List[Dict]) -> Dict[str, bool]:
        """Check if content might contain sensitive information"""
        sensitive_patterns = {
            'ssn': [r'\b\d{3}-\d{2}-\d{4}\b', r'\b\d{9}\b'],
            'credit_card': [r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'],
            'account_number': [r'\baccount\s*#?\s*:?\s*\d{6,}\b', r'\bacct\s*#?\s*:?\s*\d{6,}\b'],
            'routing_number': [r'\brouting\s*#?\s*:?\s*\d{9}\b'],
            'medical_terms': ['diagnosis', 'prescription', 'medical record', 'patient id'],
            'financial_terms': ['bank statement', 'tax return', 'income statement', 'balance sheet']
        }
        
        # Check text content for sensitive patterns
        text_content = ""
        for msg in messages:
            content = msg.get('content', '')
            if isinstance(content, str):
                text_content += content + " "
            elif isinstance(content, list):
                for item in content:
                    # Handle both dict and object formats
                    if isinstance(item, dict):
                        if item.get('type') == 'text':
                            text_content += item.get('text', '') + " "
                    else:
                        # Handle object format
                        if getattr(item, 'type', None) == 'text':
                            text_content += getattr(item, 'text', '') + " "
        
        text_lower = text_content.lower()
        
        # Check for sensitive content
        warnings = {
            'has_ssn': any(pattern in text_lower for pattern in ['ssn', 'social security']),
            'has_financial': any(term in text_lower for term in sensitive_patterns['financial_terms']),
            'has_medical': any(term in text_lower for term in sensitive_patterns['medical_terms']),
            'has_account_info': 'account' in text_lower and any(char.isdigit() for char in text_content)
        }
        
        warnings['is_sensitive'] = any(warnings.values())
        
        return warnings
    
    def get_cost_estimate(self, prompt_tokens: int, completion_tokens: int) -> float:
        """Estimate cost for OpenAI API usage"""
        # GPT-4V pricing (as of 2024)
        # These are example rates - update with current pricing
        input_price_per_1k = 0.01  # $0.01 per 1K input tokens
        output_price_per_1k = 0.03  # $0.03 per 1K output tokens
        
        input_cost = (prompt_tokens / 1000) * input_price_per_1k
        output_cost = (completion_tokens / 1000) * output_price_per_1k
        
        return input_cost + output_cost