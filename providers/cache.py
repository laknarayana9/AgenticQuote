"""
Provider Response Caching
Caches provider responses to reduce API calls and costs.
"""

import os
import logging
import json
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)


class ProviderCache:
    """
    In-memory cache for provider responses with TTL support.
    """
    
    def __init__(self, default_ttl_seconds: int = 3600):
        """
        Initialize provider cache.
        
        Args:
            default_ttl_seconds: Default time-to-live for cache entries (default: 1 hour)
        """
        self.default_ttl = default_ttl_seconds
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.enabled = os.getenv("PROVIDER_CACHE_ENABLED", "true").lower() == "true"
        
        if self.enabled:
            logger.info(f"Provider cache enabled with TTL={default_ttl_seconds}s")
        else:
            logger.info("Provider cache disabled")
    
    def _generate_key(self, provider: str, method: str, **kwargs) -> str:
        """
        Generate cache key from provider, method, and parameters.
        
        Args:
            provider: Provider name
            method: Method name
            **kwargs: Method parameters
            
        Returns:
            Cache key string
        """
        # Create a deterministic key from parameters
        key_data = f"{provider}:{method}:{json.dumps(kwargs, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, provider: str, method: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Get cached response if available and not expired.
        
        Args:
            provider: Provider name
            method: Method name
            **kwargs: Method parameters
            
        Returns:
            Cached response or None if not found/expired
        """
        if not self.enabled:
            return None
        
        key = self._generate_key(provider, method, **kwargs)
        
        if key in self.cache:
            entry = self.cache[key]
            
            # Check if expired
            if datetime.now() < entry["expires_at"]:
                entry["hit_count"] += 1
                logger.debug(f"Cache HIT: {provider}.{method} (hit_count={entry['hit_count']})")
                return entry["data"]
            else:
                # Remove expired entry
                del self.cache[key]
                logger.debug(f"Cache EXPIRED: {provider}.{method}")
        
        logger.debug(f"Cache MISS: {provider}.{method}")
        return None
    
    def set(self, provider: str, method: str, data: Dict[str, Any], ttl_seconds: Optional[int] = None, **kwargs):
        """
        Cache a provider response.
        
        Args:
            provider: Provider name
            method: Method name
            data: Response data to cache
            ttl_seconds: Time-to-live in seconds (uses default if None)
            **kwargs: Method parameters
        """
        if not self.enabled:
            return
        
        ttl = ttl_seconds or self.default_ttl
        key = self._generate_key(provider, method, **kwargs)
        
        self.cache[key] = {
            "data": data,
            "created_at": datetime.now(),
            "expires_at": datetime.now() + timedelta(seconds=ttl),
            "hit_count": 0,
            "provider": provider,
            "method": method,
            "ttl": ttl
        }
        
        logger.debug(f"Cached: {provider}.{method} (TTL={ttl}s)")
    
    def clear(self):
        """Clear all cache entries."""
        self.cache.clear()
        logger.info("Provider cache cleared")
    
    def clear_provider(self, provider: str):
        """
        Clear all cache entries for a specific provider.
        
        Args:
            provider: Provider name
        """
        keys_to_delete = [k for k, v in self.cache.items() if v["provider"] == provider]
        for key in keys_to_delete:
            del self.cache[key]
        logger.info(f"Cleared {len(keys_to_delete)} cache entries for {provider}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dict containing cache statistics
        """
        total_entries = len(self.cache)
        total_hits = sum(entry["hit_count"] for entry in self.cache.values())
        
        # Group by provider
        provider_stats = {}
        for entry in self.cache.values():
            provider = entry["provider"]
            if provider not in provider_stats:
                provider_stats[provider] = {
                    "entries": 0,
                    "hits": 0
                }
            provider_stats[provider]["entries"] += 1
            provider_stats[provider]["hits"] += entry["hit_count"]
        
        return {
            "enabled": self.enabled,
            "total_entries": total_entries,
            "total_hits": total_hits,
            "hit_rate": total_hits / total_entries if total_entries > 0 else 0,
            "default_ttl": self.default_ttl,
            "by_provider": provider_stats
        }
    
    def cleanup_expired(self):
        """Remove all expired cache entries."""
        now = datetime.now()
        expired_keys = [k for k, v in self.cache.items() if v["expires_at"] < now]
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")


# Global cache instance
_global_cache: Optional[ProviderCache] = None


def get_cache() -> ProviderCache:
    """
    Get global cache instance (singleton pattern).
    
    Returns:
        ProviderCache instance
    """
    global _global_cache
    if _global_cache is None:
        _global_cache = ProviderCache()
    return _global_cache
