"""
Mock Redis server for testing when Redis is not available.
This provides a simple in-memory Redis-like interface.
"""

import asyncio
import json
import uuid
from typing import Dict, Any, Optional, Set
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class MockRedis:
    """Mock Redis implementation for testing without Redis server."""
    
    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._sorted_sets: Dict[str, Dict[str, float]] = {}
        self._hashes: Dict[str, Dict[str, str]] = {}
        self._expiration: Dict[str, datetime] = {}
        self._lock = asyncio.Lock()
    
    async def ping(self) -> bool:
        """Mock ping - always returns True."""
        return True
    
    async def zadd(self, key: str, mapping: Dict[str, float]) -> int:
        """Add to sorted set."""
        async with self._lock:
            if key not in self._sorted_sets:
                self._sorted_sets[key] = {}
            
            self._sorted_sets[key].update(mapping)
            return len(mapping)
    
    async def zcard(self, key: str) -> int:
        """Get sorted set size."""
        async with self._lock:
            return len(self._sorted_sets.get(key, {}))
    
    async def zrange(self, key: str, start: int, end: int, withscores: bool = False) -> list:
        """Get range from sorted set."""
        async with self._lock:
            if key not in self._sorted_sets:
                return []
            
            # Sort by score (negative for priority)
            sorted_items = sorted(
                self._sorted_sets[key].items(),
                key=lambda x: x[1]
            )
            
            items = sorted_items[start:end+1] if end != -1 else sorted_items[start:]
            
            if withscores:
                return items
            else:
                return [item[0] for item in items]
    
    async def zpopmin(self, key: str, count: int = 1) -> list:
        """Pop lowest score items from sorted set."""
        async with self._lock:
            if key not in self._sorted_sets:
                return []
            
            # Sort by score (lowest first)
            sorted_items = sorted(
                self._sorted_sets[key].items(),
                key=lambda x: x[1]
            )
            
            result = sorted_items[:count]
            
            # Remove popped items
            for item, score in result:
                del self._sorted_sets[key][item]
            
            return result
    
    async def hset(self, key: str, mapping: Dict[str, str] | str, value: Optional[str] = None) -> int:
        """Set hash field."""
        async with self._lock:
            if isinstance(mapping, str) and value is not None:
                # Single field set
                if key not in self._hashes:
                    self._hashes[key] = {}
                
                field = mapping
                self._hashes[key][field] = value
                return 1
            elif isinstance(mapping, dict):
                # Multiple fields set
                if key not in self._hashes:
                    self._hashes[key] = {}
                
                self._hashes[key].update(mapping)
                return len(mapping)
            else:
                return 0
    
    async def hget(self, key: str, field: str) -> Optional[str]:
        """Get hash field."""
        async with self._lock:
            return self._hashes.get(key, {}).get(field)
    
    async def hgetall(self, key: str) -> Dict[str, str]:
        """Get all hash fields."""
        async with self._lock:
            return self._hashes.get(key, {}).copy()
    
    async def hdel(self, key: str, *fields: str) -> int:
        """Delete hash fields."""
        async with self._lock:
            if key not in self._hashes:
                return 0
            
            deleted = 0
            for field in fields:
                if field in self._hashes[key]:
                    del self._hashes[key][field]
                    deleted += 1
            
            return deleted
    
    async def hlen(self, key: str) -> int:
        """Get hash size."""
        async with self._lock:
            return len(self._hashes.get(key, {}))
    
    async def hincrby(self, key: str, field: str, increment: int = 1) -> int:
        """Increment hash field."""
        async with self._lock:
            if key not in self._hashes:
                self._hashes[key] = {}
            
            current = int(self._hashes[key].get(field, 0))
            new_value = current + increment
            self._hashes[key][field] = str(new_value)
            return new_value
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set key expiration."""
        async with self._lock:
            self._expiration[key] = datetime.now() + timedelta(seconds=seconds)
            return True
    
    async def keys(self, pattern: str) -> list:
        """Get keys matching pattern."""
        async with self._lock:
            all_keys = set(self._data.keys()) | set(self._sorted_sets.keys()) | set(self._hashes.keys())
            
            # Simple pattern matching (only supports * wildcard)
            if pattern == "*":
                return list(all_keys)
            elif pattern.startswith("*") and pattern.endswith("*"):
                # Contains pattern
                search = pattern[1:-1]
                return [key for key in all_keys if search in key]
            elif pattern.endswith("*"):
                # Starts with pattern
                search = pattern[:-1]
                return [key for key in all_keys if key.startswith(search)]
            elif pattern.startswith("*"):
                # Ends with pattern
                search = pattern[1:]
                return [key for key in all_keys if key.endswith(search)]
            else:
                # Exact match
                return [key for key in all_keys if key == pattern]
    
    async def cleanup_expired(self):
        """Clean up expired keys."""
        async with self._lock:
            now = datetime.now()
            expired_keys = [
                key for key, expiry in self._expiration.items()
                if expiry <= now
            ]
            
            for key in expired_keys:
                self._data.pop(key, None)
                self._sorted_sets.pop(key, None)
                self._hashes.pop(key, None)
                self._expiration.pop(key, None)
            
            return len(expired_keys)


# Global mock Redis instance
mock_redis = MockRedis()
