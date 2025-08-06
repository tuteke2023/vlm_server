"""
LangChain LLM Wrapper for UnifiedLLMProvider
Increment 3: Custom LangChain LLM implementation
"""

import asyncio
import logging
from typing import Any, List, Optional, Dict, Mapping
from langchain.llms.base import LLM
from langchain.callbacks.manager import CallbackManagerForLLMRun
from pydantic import Field, model_validator

logger = logging.getLogger(__name__)


class UnifiedLangChainLLM(LLM):
    """
    LangChain LLM wrapper for UnifiedLLMProvider
    
    This allows using our unified provider with LangChain chains and tools
    """
    
    # Required fields for LangChain
    unified_provider: Any = Field(..., description="UnifiedLLMProvider instance")
    temperature: float = Field(default=0.7, description="Sampling temperature")
    max_tokens: int = Field(default=2048, description="Maximum tokens to generate")
    allow_fallback: bool = Field(default=True, description="Allow fallback to local VLM")
    
    # Optional fields
    model_kwargs: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = {"arbitrary_types_allowed": True}
    
    @model_validator(mode='after')
    def validate_environment(self) -> 'UnifiedLangChainLLM':
        """Validate that unified provider is properly initialized."""
        if self.unified_provider is None:
            raise ValueError("unified_provider must be provided")
        
        # Check that provider has required methods
        if not hasattr(self.unified_provider, 'generate'):
            raise ValueError("unified_provider must have a 'generate' method")
        
        return self
    
    @property
    def _llm_type(self) -> str:
        """Return identifier of llm type."""
        return "unified_vlm"
    
    @property
    def _default_params(self) -> Mapping[str, Any]:
        """Get the default parameters for calling the model."""
        return {
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "allow_fallback": self.allow_fallback,
            **self.model_kwargs
        }
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """
        Call the unified LLM provider synchronously.
        
        Args:
            prompt: The prompt to pass into the model
            stop: List of stop words (not implemented yet)
            run_manager: Callback manager for the run
            **kwargs: Additional keyword arguments
            
        Returns:
            The string response from the model
        """
        # Merge default params with runtime kwargs
        params = {**self._default_params, **kwargs}
        
        # Convert prompt to message format
        messages = [{"role": "user", "content": prompt}]
        
        # Run async method in sync context
        try:
            # Check if we're already in an async context
            try:
                loop = asyncio.get_running_loop()
                # We're in an async context, can't use run_until_complete
                # Create a task and run it synchronously
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(
                        asyncio.run,
                        self.unified_provider.generate(
                            messages=messages,
                            temperature=params.get("temperature", self.temperature),
                            max_tokens=params.get("max_tokens", self.max_tokens),
                            allow_fallback=params.get("allow_fallback", self.allow_fallback),
                            **{k: v for k, v in params.items() 
                               if k not in ["temperature", "max_tokens", "allow_fallback"]}
                        )
                    )
                    response = future.result()
            except RuntimeError:
                # No event loop running, create one
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    response = loop.run_until_complete(
                        self.unified_provider.generate(
                            messages=messages,
                            temperature=params.get("temperature", self.temperature),
                            max_tokens=params.get("max_tokens", self.max_tokens),
                            allow_fallback=params.get("allow_fallback", self.allow_fallback),
                            **{k: v for k, v in params.items() 
                               if k not in ["temperature", "max_tokens", "allow_fallback"]}
                        )
                    )
                finally:
                    loop.close()
            
            # Handle fallback notification if present
            if response.metadata.get("fallback_used"):
                logger.warning(
                    f"Fallback used: {response.metadata.get('fallback_reason', 'Unknown reason')}"
                )
                if run_manager:
                    run_manager.on_text(
                        f"\n[Note: OpenAI failed, using local VLM]\n",
                        verbose=True
                    )
            
            # Return the content
            return response.content
            
        except Exception as e:
            logger.error(f"Error calling unified provider: {str(e)}")
            raise
    
    async def _acall(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """
        Call the unified LLM provider asynchronously.
        
        Args:
            prompt: The prompt to pass into the model
            stop: List of stop words (not implemented yet)
            run_manager: Callback manager for the run
            **kwargs: Additional keyword arguments
            
        Returns:
            The string response from the model
        """
        # Merge default params with runtime kwargs
        params = {**self._default_params, **kwargs}
        
        # Convert prompt to message format
        messages = [{"role": "user", "content": prompt}]
        
        try:
            response = await self.unified_provider.generate(
                messages=messages,
                temperature=params.get("temperature", self.temperature),
                max_tokens=params.get("max_tokens", self.max_tokens),
                allow_fallback=params.get("allow_fallback", self.allow_fallback),
                **{k: v for k, v in params.items() 
                   if k not in ["temperature", "max_tokens", "allow_fallback"]}
            )
            
            # Handle fallback notification if present
            if response.metadata.get("fallback_used"):
                logger.warning(
                    f"Fallback used: {response.metadata.get('fallback_reason', 'Unknown reason')}"
                )
                if run_manager:
                    await run_manager.on_text(
                        f"\n[Note: OpenAI failed, using local VLM]\n",
                        verbose=True
                    )
            
            # Return the content
            return response.content
            
        except Exception as e:
            logger.error(f"Error calling unified provider: {str(e)}")
            raise
    
    @property
    def _identifying_params(self) -> Mapping[str, Any]:
        """Get the identifying parameters."""
        return {
            "llm_type": self._llm_type,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "provider": self.unified_provider.get_current_provider(),
            "allow_fallback": self.allow_fallback,
        }
    
    def get_num_tokens(self, text: str) -> int:
        """
        Get the number of tokens present in the text.
        
        This is a rough estimate based on word count.
        For more accurate tokenization, we would need to use the specific
        tokenizer for the current model.
        """
        # Rough estimate: 1 token ≈ 0.75 words
        words = text.split()
        return int(len(words) / 0.75)
    
    def switch_provider(self, provider_name: str) -> Dict[str, Any]:
        """
        Switch the underlying provider
        
        Args:
            provider_name: Name of provider to switch to
            
        Returns:
            Status dict from provider switch
        """
        return self.unified_provider.switch_provider(provider_name)
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about current provider"""
        return self.unified_provider.get_provider_info()


class UnifiedLangChainChat(UnifiedLangChainLLM):
    """
    Chat-specific version of UnifiedLangChainLLM
    
    This handles multi-turn conversations better than the base LLM class
    """
    
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)
    
    def _format_messages(self, prompt: str) -> List[Dict[str, Any]]:
        """Format prompt with conversation history"""
        messages = []
        
        # Add conversation history
        for msg in self.conversation_history:
            messages.append(msg)
        
        # Add current prompt
        messages.append({"role": "user", "content": prompt})
        
        return messages
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Call with conversation history"""
        params = {**self._default_params, **kwargs}
        messages = self._format_messages(prompt)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(
                self.unified_provider.generate(
                    messages=messages,
                    **params
                )
            )
            
            # Update conversation history
            self.conversation_history.append({"role": "user", "content": prompt})
            self.conversation_history.append({"role": "assistant", "content": response.content})
            
            return response.content
        finally:
            loop.close()
    
    async def _acall(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Async call with conversation history"""
        params = {**self._default_params, **kwargs}
        messages = self._format_messages(prompt)
        
        response = await self.unified_provider.generate(
            messages=messages,
            **params
        )
        
        # Update conversation history
        self.conversation_history.append({"role": "user", "content": prompt})
        self.conversation_history.append({"role": "assistant", "content": response.content})
        
        return response.content
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []