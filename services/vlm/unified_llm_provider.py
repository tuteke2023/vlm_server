"""
Unified LLM Provider - Increment 1: Base implementation with local VLM support
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import time

logger = logging.getLogger(__name__)

# Forward declarations - these will be imported when running
GenerateRequest = None
Message = None
ContentItem = None


@dataclass
class LLMResponse:
    """Unified response format from any LLM provider"""
    content: str
    usage: Dict[str, int]
    metadata: Dict[str, Any]
    processing_time: float
    error: Optional[str] = None


class UnifiedLLMProvider:
    """
    Unified interface for LLM providers.
    Increment 2: Local VLM and OpenAI support
    """
    
    def __init__(self, vlm_server=None, openai_provider=None):
        """
        Initialize with existing providers
        
        Args:
            vlm_server: Existing VLMServer instance from vlm_server.py
            openai_provider: Existing OpenAIProvider instance
        """
        self.vlm_server = vlm_server
        self.openai_provider = openai_provider
        self.current_provider = "local"
        
        # Provider registry
        self.providers = {
            "local": {
                "instance": vlm_server,
                "available": bool(vlm_server),
                "name": "Local VLM"
            },
            "openai": {
                "instance": openai_provider,
                "available": bool(openai_provider),
                "name": "OpenAI GPT-4V"
            }
        }
        
        # Import VLM server types when provider is initialized
        global GenerateRequest, Message, ContentItem
        try:
            from vlm_server import GenerateRequest, Message, ContentItem
        except ImportError:
            # Try alternative import path
            try:
                from services.vlm.vlm_server import GenerateRequest, Message, ContentItem
            except ImportError:
                logger.warning("Could not import VLM server types")
        
        logger.info(f"UnifiedLLMProvider initialized with providers: {list(self.providers.keys())}")
    
    async def generate(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs
    ) -> LLMResponse:
        """
        Generate response using current provider
        
        Args:
            messages: List of message dicts with role and content
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters
            
        Returns:
            LLMResponse object with unified format
        """
        start_time = time.time()
        
        try:
            if self.current_provider == "local":
                response = await self._generate_local(
                    messages, 
                    temperature, 
                    max_tokens,
                    **kwargs
                )
            elif self.current_provider == "openai":
                response = await self._generate_openai(
                    messages,
                    temperature,
                    max_tokens,
                    **kwargs
                )
            else:
                raise ValueError(f"Unknown provider: {self.current_provider}")
            
            response.processing_time = time.time() - start_time
            return response
            
        except Exception as e:
            logger.error(f"Error in generate with {self.current_provider}: {str(e)}")
            
            # Check if fallback is requested and available
            if kwargs.get("allow_fallback", False) and self.current_provider == "openai":
                logger.info("Attempting fallback to local VLM")
                try:
                    # Temporarily switch to local
                    original_provider = self.current_provider
                    self.current_provider = "local"
                    response = await self._generate_local(
                        messages, 
                        temperature, 
                        max_tokens,
                        **kwargs
                    )
                    self.current_provider = original_provider
                    response.metadata["fallback_used"] = True
                    response.metadata["fallback_from"] = original_provider
                    response.metadata["fallback_reason"] = str(e)
                    response.processing_time = time.time() - start_time
                    return response
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed: {str(fallback_error)}")
            
            return LLMResponse(
                content="",
                usage={"prompt_tokens": 0, "completion_tokens": 0},
                metadata={"provider": self.current_provider, "error": str(e)},
                processing_time=time.time() - start_time,
                error=str(e)
            )
    
    async def _generate_local(
        self,
        messages: List[Dict[str, Any]],
        temperature: float,
        max_tokens: int,
        **kwargs
    ) -> LLMResponse:
        """
        Generate using local VLM server
        
        This wraps the existing VLM server functionality
        """
        if not self.vlm_server:
            raise ValueError("VLM server not initialized")
        
        # Convert dict messages to VLM server format
        message_objects = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if isinstance(content, str):
                # Simple text message
                message_objects.append(Message(role=role, content=content))
            elif isinstance(content, list):
                # Multimodal message
                content_items = []
                for item in content:
                    if item.get("type") == "text":
                        content_items.append(ContentItem(type="text", text=item.get("text", "")))
                    elif item.get("type") == "image":
                        content_items.append(ContentItem(type="image", image=item.get("image", "")))
                message_objects.append(Message(role=role, content=content_items))
        
        # Create request object
        request = GenerateRequest(
            messages=message_objects,
            temperature=temperature,
            max_new_tokens=max_tokens,
            **kwargs
        )
        
        # Use existing VLM server's generate method
        vlm_response = await self.vlm_server.generate(request)
        
        # Convert to unified format
        return LLMResponse(
            content=vlm_response.response,
            usage={
                "prompt_tokens": vlm_response.usage.get("prompt_tokens", 0),
                "completion_tokens": vlm_response.usage.get("completion_tokens", 0),
                "total_tokens": vlm_response.usage.get("total_tokens", 0)
            },
            metadata={
                "provider": "local",
                "model": self.vlm_server.current_model,
                "temperature": temperature,
                "max_tokens": max_tokens
            },
            processing_time=vlm_response.processing_time
        )
    
    async def _generate_openai(
        self,
        messages: List[Dict[str, Any]],
        temperature: float,
        max_tokens: int,
        **kwargs
    ) -> LLMResponse:
        """
        Generate using OpenAI provider
        
        This wraps the existing OpenAI provider functionality
        """
        if not self.openai_provider:
            raise ValueError("OpenAI provider not initialized")
        
        # OpenAI provider expects messages in the same format
        # Filter out unified-specific parameters
        openai_kwargs = {k: v for k, v in kwargs.items() if k != "allow_fallback"}
        
        openai_response = await self.openai_provider.generate(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **openai_kwargs
        )
        
        # Convert to unified format (OpenAI returns a dict, not an object)
        return LLMResponse(
            content=openai_response.get("response", ""),
            usage=openai_response.get("usage", {}),
            metadata={
                "provider": "openai",
                "model": openai_response.get("model", "gpt-4o"),
                "temperature": temperature,
                "max_tokens": max_tokens
            },
            processing_time=openai_response.get("processing_time", 0)
        )
    
    def get_current_provider(self) -> str:
        """Get the current provider name"""
        return self.current_provider
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about the current provider"""
        provider_data = self.providers.get(self.current_provider)
        if not provider_data:
            return {"name": self.current_provider, "available": False}
        
        if self.current_provider == "local":
            return {
                "name": "local",
                "type": "local",
                "model": self.vlm_server.current_model if self.vlm_server else "Unknown",
                "available": provider_data["available"],
                "features": ["vision", "text", "bank_extraction"]
            }
        elif self.current_provider == "openai":
            return {
                "name": "openai",
                "type": "cloud",
                "model": "gpt-4o",
                "available": provider_data["available"],
                "features": ["vision", "text", "bank_extraction"]
            }
        return {"name": self.current_provider, "available": False}
    
    def is_available(self) -> bool:
        """Check if the current provider is available"""
        provider_data = self.providers.get(self.current_provider)
        return provider_data["available"] if provider_data else False
    
    def switch_provider(self, provider_name: str) -> Dict[str, Any]:
        """
        Switch to a different provider
        
        Args:
            provider_name: Name of the provider to switch to
            
        Returns:
            Dict with status and current provider info
        """
        if provider_name not in self.providers:
            return {
                "status": "error",
                "message": f"Provider '{provider_name}' not found",
                "available_providers": list(self.providers.keys())
            }
        
        if not self.providers[provider_name]["available"]:
            return {
                "status": "error",
                "message": f"Provider '{provider_name}' is not available",
                "current_provider": self.current_provider
            }
        
        self.current_provider = provider_name
        logger.info(f"Switched to provider: {provider_name}")
        
        return {
            "status": "success",
            "current_provider": provider_name,
            "provider_info": self.get_provider_info()
        }
    
    def get_all_providers(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all available providers"""
        result = {}
        for name, data in self.providers.items():
            # Temporarily switch to get accurate info
            original = self.current_provider
            self.current_provider = name
            result[name] = {
                "available": data["available"],
                "display_name": data["name"],
                **self.get_provider_info()
            }
            self.current_provider = original
        return result
    
    def contains_sensitive_content(self, messages: List[Dict[str, Any]]) -> bool:
        """
        Check if messages contain sensitive content
        
        Args:
            messages: List of message dicts
            
        Returns:
            True if sensitive content detected
        """
        import re
        
        sensitive_patterns = [
            r'\b\d{3}-?\d{2}-?\d{4}\b',  # SSN
            r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',  # Credit card
            r'\baccount\s*(?:number|#|no\.?)?\s*:?\s*\d+\b',  # Account numbers
            r'\b(?:bank|checking|savings)\s+(?:account|statement)\b',  # Banking terms
            r'\b(?:balance|transaction|deposit|withdrawal)\b',  # Financial terms
        ]
        
        # Check all message content
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                text = content.lower()
            elif isinstance(content, list):
                # Extract text from multimodal content
                text = " ".join(
                    item.get("text", "") 
                    for item in content 
                    if item.get("type") == "text"
                ).lower()
            else:
                continue
            
            # Check patterns
            for pattern in sensitive_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return True
        
        return False