"""
LLM Client Wrapper
OpenAI API integration for enhanced agent reasoning.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class LLMClient:
    """
    LLM client wrapper for OpenAI API integration.
    
    Requires OPENAI_API_KEY environment variable.
    Falls back to deterministic logic if API key is not available.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4", temperature: float = 0.2):
        """
        Initialize LLM client.
        
        Args:
            api_key: OpenAI API key. If None, uses OPENAI_API_KEY env var.
            model: Model to use (default: gpt-4)
            temperature: Temperature for randomness (default: 0.2 for determinism)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("LLM_MODEL", "gpt-4")
        self.temperature = float(os.getenv("LLM_TEMPERATURE", temperature))
        self.enabled = os.getenv("USE_LLM", "false").lower() == "true"
        self.total_cost = 0.0
        self.total_tokens = 0
        
        if not self.api_key:
            logger.warning("OpenAI API key not found. LLM features disabled.")
            self.enabled = False
        elif not self.enabled:
            logger.info("LLM features disabled via USE_LLM=false")
        else:
            logger.info(f"LLM client initialized with model={self.model}, temperature={self.temperature}")
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 1000,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Call OpenAI chat completion API.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Override default temperature
            
        Returns:
            Dict containing response, usage, and cost
        """
        if not self.enabled:
            return self._mock_completion(messages)
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature or self.temperature
            )
            
            # Calculate cost
            usage = response.usage
            input_tokens = usage.prompt_tokens
            output_tokens = usage.completion_tokens
            total_tokens = input_tokens + output_tokens
            
            # Cost calculation (approximate)
            cost_per_1k_input = 0.03 if "gpt-4" in self.model else 0.0015
            cost_per_1k_output = 0.06 if "gpt-4" in self.model else 0.002
            cost = (input_tokens / 1000) * cost_per_1k_input + (output_tokens / 1000) * cost_per_1k_output
            
            self.total_cost += cost
            self.total_tokens += total_tokens
            
            return {
                "content": response.choices[0].message.content,
                "finish_reason": response.choices[0].finish_reason,
                "usage": {
                    "prompt_tokens": input_tokens,
                    "completion_tokens": output_tokens,
                    "total_tokens": total_tokens
                },
                "cost": cost,
                "model": self.model,
                "cached": False
            }
            
        except Exception as e:
            logger.error(f"LLM API error: {e}", exc_info=True)
            # Fallback to mock completion on error
            return self._mock_completion(messages, error=str(e))
    
    def _mock_completion(self, messages: List[Dict[str, str]], error: Optional[str] = None) -> Dict[str, Any]:
        """
        Mock completion as fallback.
        """
        logger.warning(f"Using mock LLM completion (error={error or 'not enabled'})")
        
        return {
            "content": "Mock LLM response - deterministic logic should be used instead",
            "finish_reason": "mock",
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            },
            "cost": 0.0,
            "model": "mock",
            "cached": False,
            "error": error or "LLM not enabled"
        }
    
    def get_cost_stats(self) -> Dict[str, Any]:
        """
        Get cost statistics.
        
        Returns:
            Dict containing cost statistics
        """
        return {
            "total_cost": self.total_cost,
            "total_tokens": self.total_tokens,
            "model": self.model,
            "enabled": self.enabled
        }
    
    def reset_cost_stats(self):
        """Reset cost statistics."""
        self.total_cost = 0.0
        self.total_tokens = 0
        logger.info("LLM cost statistics reset")


# Global LLM client instance
_global_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """
    Get global LLM client instance (singleton pattern).
    
    Returns:
        LLMClient instance
    """
    global _global_llm_client
    if _global_llm_client is None:
        _global_llm_client = LLMClient()
    return _global_llm_client
