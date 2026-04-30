"""
Minimal circuit breaker implementation for test compatibility
"""

import logging
import time
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    half_open_max_calls: int = 3

class CircuitBreakerOpenError(Exception):
    """Circuit breaker is open"""
    pass

class CircuitBreaker:
    """Simple circuit breaker implementation"""
    
    def __init__(self, config: Optional[CircuitBreakerConfig] = None):
        self.config = config or CircuitBreakerConfig()
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open
    
    def call(self, func, *args, **kwargs):
        """Call function with circuit breaker protection"""
        if self.state == "open":
            raise CircuitBreakerOpenError("Circuit breaker is open")
        
        try:
            result = func(*args, **kwargs)
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise
    
    def on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        self.state = "closed"
    
    def on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        if self.failure_count >= self.config.failure_threshold:
            self.state = "open"
            self.last_failure_time = time.time()

__all__ = ["CircuitBreaker", "CircuitBreakerConfig", "CircuitBreakerOpenError"]
