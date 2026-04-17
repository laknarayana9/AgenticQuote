"""
Performance Metrics Tracking
Tracks system performance metrics including latency, throughput, and error rates.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import time

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """
    Performance metrics tracking for system optimization.
    
    Tracks latency, throughput, error rates, and resource utilization.
    """
    
    def __init__(self):
        """Initialize performance metrics tracker."""
        self.enabled = os.getenv("PERFORMANCE_ANALYTICS_ENABLED", "false").lower() == "true"
        
        # Performance history
        self.performance_history = []
        
        # Metrics
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_latency_ms": 0.0,
            "p95_latency_ms": 0.0,
            "p99_latency_ms": 0.0,
            "throughput_per_second": 0.0,
            "error_rate": 0.0
        }
        
        # Latency history for percentiles
        self.latency_history = []
        
        # Metrics by endpoint
        self.metrics_by_endpoint = defaultdict(lambda: {
            "requests": 0,
            "errors": 0,
            "total_latency": 0
        })
        
        logger.info(f"Performance metrics tracker initialized (enabled={self.enabled})")
    
    def record_request(
        self,
        endpoint: str,
        latency_ms: float,
        success: bool,
        error_message: Optional[str] = None
    ):
        """
        Record a request for performance tracking.
        
        Args:
            endpoint: API endpoint or workflow name
            latency_ms: Request latency in milliseconds
            success: Whether request was successful
            error_message: Error message if failed
        """
        if not self.enabled:
            return
        
        record = {
            "endpoint": endpoint,
            "latency_ms": latency_ms,
            "success": success,
            "error_message": error_message,
            "timestamp": datetime.now()
        }
        
        self.performance_history.append(record)
        self.latency_history.append(latency_ms)
        
        # Update metrics
        self.metrics["total_requests"] += 1
        if success:
            self.metrics["successful_requests"] += 1
        else:
            self.metrics["failed_requests"] += 1
        
        # Update endpoint metrics
        self.metrics_by_endpoint[endpoint]["requests"] += 1
        self.metrics_by_endpoint[endpoint]["total_latency"] += latency_ms
        if not success:
            self.metrics_by_endpoint[endpoint]["errors"] += 1
        
        # Recalculate metrics
        self._recalculate_metrics()
        
        logger.debug(f"Recorded request to {endpoint}: {latency_ms}ms, success={success}")
    
    def _recalculate_metrics(self):
        """Recalculate performance metrics."""
        total = self.metrics["total_requests"]
        if total == 0:
            return
        
        # Calculate error rate
        self.metrics["error_rate"] = self.metrics["failed_requests"] / total
        
        # Calculate average latency
        if self.latency_history:
            self.metrics["avg_latency_ms"] = sum(self.latency_history) / len(self.latency_history)
            
            # Calculate percentiles
            sorted_latencies = sorted(self.latency_history)
            p95_index = int(len(sorted_latencies) * 0.95)
            p99_index = int(len(sorted_latencies) * 0.99)
            self.metrics["p95_latency_ms"] = sorted_latencies[p95_index] if p95_index < len(sorted_latencies) else sorted_latencies[-1]
            self.metrics["p99_latency_ms"] = sorted_latencies[p99_index] if p99_index < len(sorted_latencies) else sorted_latencies[-1]
        
        # Calculate throughput (requests per second over last minute)
        cutoff = datetime.now() - timedelta(seconds=60)
        recent_requests = [r for r in self.performance_history if r["timestamp"] >= cutoff]
        self.metrics["throughput_per_second"] = len(recent_requests) / 60 if recent_requests else 0
    
    def get_metrics(self, hours: int = 1) -> Dict[str, Any]:
        """
        Get performance metrics for a time window.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Performance metrics
        """
        if not self.enabled:
            return {"enabled": False}
        
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_requests = [
            r for r in self.performance_history
            if r["timestamp"] >= cutoff
        ]
        
        if not recent_requests:
            return {
                "enabled": True,
                "time_window_hours": hours,
                "total_requests": 0,
                "metrics": {}
            }
        
        # Calculate metrics for time window
        total = len(recent_requests)
        successful = sum(1 for r in recent_requests if r["success"])
        failed = total - successful
        latencies = [r["latency_ms"] for r in recent_requests]
        
        sorted_latencies = sorted(latencies)
        p95_index = int(len(sorted_latencies) * 0.95)
        p99_index = int(len(sorted_latencies) * 0.99)
        
        return {
            "enabled": True,
            "time_window_hours": hours,
            "total_requests": total,
            "metrics": {
                "success_rate": successful / total,
                "error_rate": failed / total,
                "avg_latency_ms": sum(latencies) / len(latencies),
                "p95_latency_ms": sorted_latencies[p95_index] if p95_index < len(sorted_latencies) else sorted_latencies[-1],
                "p99_latency_ms": sorted_latencies[p99_index] if p99_index < len(sorted_latencies) else sorted_latencies[-1]
            }
        }
    
    def get_endpoint_metrics(self, endpoint: str) -> Dict[str, Any]:
        """
        Get metrics for a specific endpoint.
        
        Args:
            endpoint: Endpoint name
            
        Returns:
            Endpoint metrics
        """
        if not self.enabled:
            return {"enabled": False}
        
        if endpoint not in self.metrics_by_endpoint:
            return {
                "enabled": True,
                "endpoint": endpoint,
                "found": False
            }
        
        metrics = self.metrics_by_endpoint[endpoint]
        avg_latency = metrics["total_latency"] / metrics["requests"] if metrics["requests"] > 0 else 0
        error_rate = metrics["errors"] / metrics["requests"] if metrics["requests"] > 0 else 0
        
        return {
            "enabled": True,
            "endpoint": endpoint,
            "found": True,
            "requests": metrics["requests"],
            "errors": metrics["errors"],
            "avg_latency_ms": avg_latency,
            "error_rate": error_rate
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get performance summary.
        
        Returns:
            Summary data
        """
        if not self.enabled:
            return {"enabled": False}
        
        return {
            "enabled": True,
            "total_requests": self.metrics["total_requests"],
            "metrics": self.metrics.copy(),
            "endpoints": {
                endpoint: {
                    "requests": data["requests"],
                    "errors": data["errors"],
                    "avg_latency_ms": data["total_latency"] / data["requests"] if data["requests"] > 0 else 0
                }
                for endpoint, data in self.metrics_by_endpoint.items()
            }
        }


# Global performance metrics instance
_global_performance_metrics: Optional[PerformanceMetrics] = None


def get_performance_metrics() -> PerformanceMetrics:
    """
    Get global performance metrics instance (singleton pattern).
    
    Returns:
        PerformanceMetrics instance
    """
    global _global_performance_metrics
    if _global_performance_metrics is None:
        _global_performance_metrics = PerformanceMetrics()
    return _global_performance_metrics
