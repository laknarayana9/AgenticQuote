"""
API Gateway Module
Handles API routing, rate limiting, authentication, and request/response transformation
"""

import time
import json
import hashlib
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime, timedelta
import asyncio
from functools import wraps

from fastapi import Request, Response, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


@dataclass
class RateLimitRule:
    """Rate limit rule configuration"""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_size: int = 10


@dataclass
class APIRoute:
    """API route configuration"""
    path: str
    method: str
    handler: Callable
    auth_required: bool = True
    rate_limit: Optional[RateLimitRule] = None
    version: str = "v1"


@dataclass
class APIKey:
    """API key configuration"""
    key: str
    partner_id: str
    permissions: List[str] = field(default_factory=list)
    rate_limit: Optional[RateLimitRule] = None
    expires_at: Optional[datetime] = None
    is_active: bool = True


class RateLimiter:
    """Rate limiter using sliding window algorithm"""
    
    def __init__(self):
        self.requests: Dict[str, List[float]] = defaultdict(list)
    
    def is_allowed(
        self,
        identifier: str,
        rule: RateLimitRule,
        current_time: Optional[float] = None
    ) -> bool:
        """Check if request is allowed based on rate limit rules"""
        if current_time is None:
            current_time = time.time()
        
        # Clean up old requests
        self._cleanup_old_requests(identifier, current_time)
        
        # Check burst limit
        if len(self.requests[identifier]) >= rule.burst_size:
            return False
        
        # Check per-minute limit
        minute_ago = current_time - 60
        minute_count = sum(1 for t in self.requests[identifier] if t > minute_ago)
        if minute_count >= rule.requests_per_minute:
            return False
        
        # Check per-hour limit
        hour_ago = current_time - 3600
        hour_count = sum(1 for t in self.requests[identifier] if t > hour_ago)
        if hour_count >= rule.requests_per_hour:
            return False
        
        # Check per-day limit
        day_ago = current_time - 86400
        day_count = sum(1 for t in self.requests[identifier] if t > day_ago)
        if day_count >= rule.requests_per_day:
            return False
        
        # Record request
        self.requests[identifier].append(current_time)
        return True
    
    def _cleanup_old_requests(self, identifier: str, current_time: float):
        """Remove requests older than 24 hours"""
        day_ago = current_time - 86400
        self.requests[identifier] = [
            t for t in self.requests[identifier] if t > day_ago
        ]
    
    def get_remaining_requests(
        self,
        identifier: str,
        rule: RateLimitRule,
        current_time: Optional[float] = None
    ) -> Dict[str, int]:
        """Get remaining requests for each time window"""
        if current_time is None:
            current_time = time.time()
        
        minute_ago = current_time - 60
        hour_ago = current_time - 3600
        day_ago = current_time - 86400
        
        minute_count = sum(1 for t in self.requests[identifier] if t > minute_ago)
        hour_count = sum(1 for t in self.requests[identifier] if t > hour_ago)
        day_count = sum(1 for t in self.requests[identifier] if t > day_ago)
        
        return {
            "minute": max(0, rule.requests_per_minute - minute_count),
            "hour": max(0, rule.requests_per_hour - hour_count),
            "day": max(0, rule.requests_per_day - day_count),
        }


class APIGateway:
    """Main API Gateway class"""
    
    def __init__(self):
        self.routes: Dict[str, Dict[str, APIRoute]] = defaultdict(dict)
        self.api_keys: Dict[str, APIKey] = {}
        self.rate_limiter = RateLimiter()
        self.security = HTTPBearer()
        self.middleware: List[Callable] = []
        self.metrics: Dict[str, Any] = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "rate_limited_requests": 0,
            "auth_failures": 0,
        }
    
    def register_route(
        self,
        path: str,
        method: str,
        handler: Callable,
        auth_required: bool = True,
        rate_limit: Optional[RateLimitRule] = None,
        version: str = "v1"
    ):
        """Register an API route"""
        route = APIRoute(
            path=path,
            method=method.upper(),
            handler=handler,
            auth_required=auth_required,
            rate_limit=rate_limit,
            version=version
        )
        self.routes[version][f"{method.upper()} {path}"] = route
    
    def add_middleware(self, middleware: Callable):
        """Add middleware to the gateway"""
        self.middleware.append(middleware)
    
    def generate_api_key(
        self,
        partner_id: str,
        permissions: List[str],
        rate_limit: Optional[RateLimitRule] = None,
        expires_in_days: Optional[int] = None
    ) -> str:
        """Generate a new API key"""
        key = self._generate_key()
        
        expires_at = None
        if expires_in_days:
            expires_at = datetime.now() + timedelta(days=expires_in_days)
        
        api_key = APIKey(
            key=key,
            partner_id=partner_id,
            permissions=permissions,
            rate_limit=rate_limit,
            expires_at=expires_at,
            is_active=True
        )
        
        self.api_keys[key] = api_key
        return key
    
    def revoke_api_key(self, key: str) -> bool:
        """Revoke an API key"""
        if key in self.api_keys:
            self.api_keys[key].is_active = False
            return True
        return False
    
    def validate_api_key(self, key: str) -> Optional[APIKey]:
        """Validate an API key"""
        api_key = self.api_keys.get(key)
        
        if not api_key:
            return None
        
        if not api_key.is_active:
            return None
        
        if api_key.expires_at and api_key.expires_at < datetime.now():
            return None
        
        return api_key
    
    async def handle_request(
        self,
        request: Request,
        path: str,
        method: str,
        version: str = "v1"
    ) -> Response:
        """Handle an incoming API request"""
        self.metrics["total_requests"] += 1
        
        # Find route
        route_key = f"{method.upper()} {path}"
        route = self.routes.get(version, {}).get(route_key)
        
        if not route:
            self.metrics["failed_requests"] += 1
            raise HTTPException(status_code=404, detail="Route not found")
        
        # Apply middleware
        for middleware in self.middleware:
            request = await middleware(request)
        
        # Authentication
        if route.auth_required:
            credentials: HTTPAuthorizationCredentials = await self.security(request)
            api_key = self.validate_api_key(credentials.credentials)
            
            if not api_key:
                self.metrics["auth_failures"] += 1
                self.metrics["failed_requests"] += 1
                raise HTTPException(status_code=401, detail="Invalid API key")
            
            # Rate limiting
            rate_limit = route.rate_limit or api_key.rate_limit
            if rate_limit:
                identifier = f"{api_key.partner_id}:{api_key.key}"
                if not self.rate_limiter.is_allowed(identifier, rate_limit):
                    self.metrics["rate_limited_requests"] += 1
                    self.metrics["failed_requests"] += 1
                    raise HTTPException(
                        status_code=429,
                        detail="Rate limit exceeded",
                        headers={
                            "X-RateLimit-Remaining": json.dumps(
                                self.rate_limiter.get_remaining_requests(identifier, rate_limit)
                            )
                        }
                    )
        
        # Execute handler
        try:
            response = await route.handler(request)
            self.metrics["successful_requests"] += 1
            return response
        except Exception as e:
            self.metrics["failed_requests"] += 1
            raise e
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get gateway metrics"""
        return self.metrics.copy()
    
    def get_routes(self, version: str = "v1") -> List[Dict[str, Any]]:
        """Get all registered routes"""
        routes = []
        for route_key, route in self.routes.get(version, {}).items():
            routes.append({
                "path": route.path,
                "method": route.method,
                "auth_required": route.auth_required,
                "version": route.version,
            })
        return routes
    
    def _generate_key(self) -> str:
        """Generate a unique API key"""
        timestamp = str(time.time()).encode()
        random_bytes = f"{time.time()}:{time.time()}".encode()
        hash_obj = hashlib.sha256(random_bytes)
        return f"ak_{hash_obj.hexdigest()[:32]}"


# Global gateway instance
gateway = APIGateway()


def rate_limit(requests_per_minute: int = 60, requests_per_hour: int = 1000):
    """Decorator for rate limiting"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Rate limiting logic would be applied here
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_permission(permission: str):
    """Decorator for permission checking"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Permission checking logic would be applied here
            return await func(*args, **kwargs)
        return wrapper
    return decorator
