"""
Response caching for VLM server
Caches recent responses to avoid redundant processing
"""

import hashlib
import json
import time
from typing import Dict, Any, Optional, Tuple
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class ResponseCache:
    """Simple LRU cache with TTL for VLM responses"""
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 900):  # 15 min TTL
        """
        Initialize cache
        
        Args:
            max_size: Maximum number of cached items
            ttl_seconds: Time to live in seconds
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Tuple[float, Any]] = {}
        self.access_order = []  # Track access order for LRU
    
    def _generate_key(self, messages: list, endpoint: str) -> str:
        """Generate cache key from messages and endpoint"""
        # Create a stable representation of the messages
        key_data = {
            "endpoint": endpoint,
            "messages": []
        }
        
        for msg in messages:
            # Handle both dict and object messages
            if hasattr(msg, 'role'):
                msg_data = {"role": msg.role}
                content = msg.content
            else:
                msg_data = {"role": msg.get("role")}
                content = msg.get("content", [])
            
            if isinstance(content, str):
                msg_data["content"] = content
            elif isinstance(content, list):
                content_key = []
                for item in content:
                    if item.get("type") == "text":
                        content_key.append({"type": "text", "text": item.get("text", "")})
                    elif item.get("type") == "image":
                        # For images, use first 100 chars as key (enough for uniqueness)
                        img_data = item.get("image", "")[:100]
                        content_key.append({"type": "image", "preview": img_data})
                msg_data["content"] = content_key
            
            key_data["messages"].append(msg_data)
        
        # Generate hash
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()
    
    def get(self, messages: list, endpoint: str) -> Optional[Any]:
        """Get cached response if available and not expired"""
        key = self._generate_key(messages, endpoint)
        
        if key in self.cache:
            timestamp, response = self.cache[key]
            
            # Check if expired
            if time.time() - timestamp > self.ttl_seconds:
                del self.cache[key]
                if key in self.access_order:
                    self.access_order.remove(key)
                logger.debug(f"Cache expired for key {key[:8]}...")
                return None
            
            # Update access order (move to end)
            if key in self.access_order:
                self.access_order.remove(key)
            self.access_order.append(key)
            
            logger.info(f"Cache hit for {endpoint} (key: {key[:8]}...)")
            return response
        
        return None
    
    def set(self, messages: list, endpoint: str, response: Any):
        """Cache a response"""
        key = self._generate_key(messages, endpoint)
        
        # Enforce max size
        if len(self.cache) >= self.max_size and key not in self.cache:
            # Remove least recently used
            if self.access_order:
                lru_key = self.access_order.pop(0)
                del self.cache[lru_key]
                logger.debug(f"Evicted LRU key {lru_key[:8]}...")
        
        # Store with timestamp
        self.cache[key] = (time.time(), response)
        
        # Update access order
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)
        
        logger.info(f"Cached response for {endpoint} (key: {key[:8]}...)")
    
    def clear(self):
        """Clear all cached responses"""
        self.cache.clear()
        self.access_order.clear()
        logger.info("Cache cleared")
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "ttl_seconds": self.ttl_seconds,
            "keys": [k[:8] + "..." for k in self.cache.keys()]
        }


# Global cache instance
_response_cache = None


def get_cache() -> ResponseCache:
    """Get or create the global cache instance"""
    global _response_cache
    if _response_cache is None:
        _response_cache = ResponseCache()
    return _response_cache