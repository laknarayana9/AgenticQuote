"""
Web Search Provider
Real provider implementation for web search integration (Tavily/Perplexity).
"""

import os
import logging
from typing import Dict, Any, Optional, List
import requests

logger = logging.getLogger(__name__)


class WebSearchProvider:
    """
    Real Web Search provider (Tavily/Perplexity).
    
    Requires WEB_SEARCH_API_KEY environment variable.
    Falls back to mock behavior if API key is not available.
    """
    
    def __init__(self, api_key: Optional[str] = None, provider: str = "tavily"):
        """
        Initialize Web Search provider.
        
        Args:
            api_key: Web Search API key. If None, uses WEB_SEARCH_API_KEY env var.
            provider: Search provider to use (tavily, perplexity)
        """
        self.api_key = api_key or os.getenv("WEB_SEARCH_API_KEY")
        self.provider = provider or os.getenv("WEB_SEARCH_PROVIDER", "tavily")
        self.enabled = os.getenv("USE_WEB_SEARCH", "false").lower() == "true"
        
        if self.provider == "tavily":
            self.base_url = "https://api.tavily.com/search"
        elif self.provider == "perplexity":
            self.base_url = "https://api.perplexity.ai/search"
        else:
            logger.warning(f"Unknown provider {self.provider}, defaulting to mock")
            self.enabled = False
        
        if not self.api_key:
            logger.warning("Web Search API key not found. Web search disabled.")
            self.enabled = False
        elif not self.enabled:
            logger.info("Web search disabled via USE_WEB_SEARCH=false")
        else:
            logger.info(f"Web search initialized with provider={self.provider}")
    
    def search(self, query: str, max_results: int = 5, search_depth: str = "basic") -> Dict[str, Any]:
        """
        Perform web search.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            search_depth: Search depth (basic, advanced)
            
        Returns:
            Dict containing search results
        """
        if not self.enabled:
            return self._mock_search(query)
        
        try:
            if self.provider == "tavily":
                return self._search_tavily(query, max_results, search_depth)
            elif self.provider == "perplexity":
                return self._search_perplexity(query, max_results)
            else:
                return self._mock_search(query)
                
        except Exception as e:
            logger.error(f"Web search error: {e}", exc_info=True)
            return self._mock_search(query)
    
    def _search_tavily(self, query: str, max_results: int, search_depth: str) -> Dict[str, Any]:
        """
        Search using Tavily API.
        """
        headers = {
            "Content-Type": "application/json"
        }
        
        params = {
            "api_key": self.api_key,
            "query": query,
            "max_results": max_results,
            "search_depth": search_depth,
            "include_answer": True,
            "include_raw_content": False
        }
        
        response = requests.post(self.base_url, json=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        results = []
        for item in data.get("results", []):
            results.append({
                "title": item.get("title"),
                "url": item.get("url"),
                "snippet": item.get("content"),
                "score": item.get("score", 0.0)
            })
        
        return {
            "query": query,
            "answer": data.get("answer", ""),
            "results": results,
            "provider": "tavily",
            "confidence": 0.8,
            "warnings": []
        }
    
    def _search_perplexity(self, query: str, max_results: int) -> Dict[str, Any]:
        """
        Search using Perplexity API.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        params = {
            "model": "sonar-medium-online",
            "messages": [{"role": "user", "content": query}],
            "max_results": max_results
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            json=params,
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        
        answer = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        results = []
        citations = data.get("citations", [])
        for i, citation in enumerate(citations[:max_results]):
            results.append({
                "title": f"Result {i+1}",
                "url": citation,
                "snippet": "",
                "score": 1.0
            })
        
        return {
            "query": query,
            "answer": answer,
            "results": results,
            "provider": "perplexity",
            "confidence": 0.8,
            "warnings": []
        }
    
    def _mock_search(self, query: str) -> Dict[str, Any]:
        """
        Mock web search as fallback.
        """
        logger.warning(f"Using mock web search for query: {query}")
        
        return {
            "query": query,
            "answer": f"Mock search result for: {query}",
            "results": [
                {
                    "title": "Mock Result 1",
                    "url": "https://example.com/mock1",
                    "snippet": "This is a mock search result",
                    "score": 0.9
                }
            ],
            "provider": "mock",
            "confidence": 0.3,
            "warnings": ["Using mock web search - API key not configured"]
        }
    
    def verify_property_risk(self, address: str, risk_type: str) -> Dict[str, Any]:
        """
        Verify property risk information via web search.
        
        Args:
            address: Property address
            risk_type: Type of risk (wildfire, flood, wind, earthquake)
            
        Returns:
            Dict containing verification results
        """
        query = f"{address} {risk_type} risk assessment insurance"
        
        search_result = self.search(query, max_results=3)
        
        return {
            "address": address,
            "risk_type": risk_type,
            "verification_result": search_result,
            "verified": search_result["confidence"] > 0.5,
            "external_sources": len(search_result["results"])
        }


# Global web search provider instance
_global_web_search: Optional[WebSearchProvider] = None


def get_web_search() -> WebSearchProvider:
    """
    Get global web search provider instance (singleton pattern).
    
    Returns:
        WebSearchProvider instance
    """
    global _global_web_search
    if _global_web_search is None:
        _global_web_search = WebSearchProvider()
    return _global_web_search
