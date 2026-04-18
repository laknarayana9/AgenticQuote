"""
Advanced metrics collection for Phase D.2
Provides performance threshold monitoring, resource utilization tracking, error rate monitoring, and business metrics.
"""

import os
import logging
import psutil
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import deque, defaultdict
from enum import Enum

logger = logging.getLogger(__name__)


class ThresholdStatus(Enum):
    """Threshold status."""
    OK = "ok"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class Threshold:
    """Performance threshold definition."""
    id: str
    metric: str
    warning_threshold: float
    critical_threshold: float
    operator: str
    enabled: bool = True


@dataclass
class ThresholdAlert:
    """Threshold alert."""
    id: str
    threshold_id: str
    metric: str
    value: float
    status: str
    timestamp: datetime
    message: str


class PerformanceThresholdMonitor:
    """Monitor performance thresholds."""
    
    def __init__(self):
        self.enabled = os.getenv("PERFORMANCE_THRESHOLD_MONITORING_ENABLED", "false").lower() == "true"
        self.thresholds: Dict[str, Threshold] = {}
        self.alerts: List[ThresholdAlert] = []
        self._load_default_thresholds()
        
        logger.info(f"Performance threshold monitor initialized (enabled={self.enabled})")
    
    def _load_default_thresholds(self) -> None:
        """Load default performance thresholds."""
        default_thresholds = [
            Threshold(
                id="response_time_p95",
                metric="response_time_p95",
                warning_threshold=500,
                critical_threshold=1000,
                operator=">"
            ),
            Threshold(
                id="response_time_p99",
                metric="response_time_p99",
                warning_threshold=1000,
                critical_threshold=2000,
                operator=">"
            ),
            Threshold(
                id="throughput",
                metric="requests_per_second",
                warning_threshold=100,
                critical_threshold=50,
                operator="<"
            ),
            Threshold(
                id="queue_length",
                metric="request_queue_length",
                warning_threshold=100,
                critical_threshold=500,
                operator=">"
            )
        ]
        
        for threshold in default_thresholds:
            self.add_threshold(threshold)
    
    def add_threshold(self, threshold: Threshold) -> None:
        """Add a performance threshold."""
        self.thresholds[threshold.id] = threshold
        logger.info(f"Performance threshold added: {threshold.id}")
    
    def check_threshold(self, metric: str, value: float) -> Optional[ThresholdAlert]:
        """Check if a metric value triggers any thresholds."""
        if not self.enabled:
            return None
        
        for threshold_id, threshold in self.thresholds.items():
            if threshold.metric == metric and threshold.enabled:
                status = self._evaluate_threshold(threshold, value)
                
                if status != ThresholdStatus.OK:
                    alert = ThresholdAlert(
                        id=f"{threshold_id}-{int(time.time())}",
                        threshold_id=threshold_id,
                        metric=metric,
                        value=value,
                        status=status.value,
                        timestamp=datetime.now(),
                        message=f"{metric} = {value} exceeds {status.value} threshold"
                    )
                    self.alerts.append(alert)
                    logger.warning(f"Threshold alert: {alert.message}")
                    return alert
        
        return None
    
    def _evaluate_threshold(self, threshold: Threshold, value: float) -> ThresholdStatus:
        """Evaluate a threshold against a value."""
        critical_trigger = self._check_operator(threshold.operator, value, threshold.critical_threshold)
        warning_trigger = self._check_operator(threshold.operator, value, threshold.warning_threshold)
        
        if critical_trigger:
            return ThresholdStatus.CRITICAL
        elif warning_trigger:
            return ThresholdStatus.WARNING
        else:
            return ThresholdStatus.OK
    
    def _check_operator(self, operator: str, value: float, threshold: float) -> bool:
        """Check if value meets operator condition."""
        if operator == ">":
            return value > threshold
        elif operator == "<":
            return value < threshold
        elif operator == ">=":
            return value >= threshold
        elif operator == "<=":
            return value <= threshold
        elif operator == "==":
            return value == threshold
        return False
    
    def get_alerts(self, limit: int = 100) -> List[ThresholdAlert]:
        """Get recent threshold alerts."""
        return self.alerts[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get threshold monitor statistics."""
        return {
            "enabled": self.enabled,
            "total_thresholds": len(self.thresholds),
            "total_alerts": len(self.alerts),
            "active_alerts": len([a for a in self.alerts if a.status == ThresholdStatus.CRITICAL.value])
        }


class ResourceUtilizationTracker:
    """Track resource utilization metrics."""
    
    def __init__(self, window_size: int = 300):
        self.enabled = os.getenv("RESOURCE_TRACKING_ENABLED", "false").lower() == "true"
        self.window_size = window_size
        self.cpu_history: deque = deque(maxlen=window_size)
        self.memory_history: deque = deque(maxlen=window_size)
        self.disk_history: deque = deque(maxlen=window_size)
        self.network_history: deque = deque(maxlen=window_size)
        
        logger.info(f"Resource utilization tracker initialized (enabled={self.enabled})")
    
    def collect_metrics(self) -> Dict[str, Any]:
        """Collect current resource utilization metrics."""
        if not self.enabled:
            return {"enabled": False}
        
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            
            # Network metrics
            network = psutil.net_io_counters()
            
            # Store in history
            timestamp = time.time()
            self.cpu_history.append((timestamp, cpu_percent))
            self.memory_history.append((timestamp, memory.percent))
            self.disk_history.append((timestamp, (disk.used / disk.total) * 100))
            self.network_history.append((timestamp, network.bytes_sent + network.bytes_recv))
            
            return {
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count,
                    "freq_current": cpu_freq.current if cpu_freq else None,
                    "freq_max": cpu_freq.max if cpu_freq else None
                },
                "memory": {
                    "total_gb": memory.total / (1024**3),
                    "available_gb": memory.available / (1024**3),
                    "percent": memory.percent,
                    "used_gb": memory.used / (1024**3)
                },
                "disk": {
                    "total_gb": disk.total / (1024**3),
                    "used_gb": disk.used / (1024**3),
                    "free_gb": disk.free / (1024**3),
                    "percent": (disk.used / disk.total) * 100
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "bytes_total": network.bytes_sent + network.bytes_recv
                },
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error collecting resource metrics: {e}")
            return {"error": str(e)}
    
    def get_average_utilization(self, duration_seconds: int = 300) -> Dict[str, float]:
        """Get average resource utilization over a time period."""
        if not self.enabled:
            return {"enabled": False}
        
        cutoff = time.time() - duration_seconds
        
        def avg_from_history(history):
            values = [v for t, v in history if t >= cutoff]
            return sum(values) / len(values) if values else 0
        
        return {
            "cpu_avg": avg_from_history(self.cpu_history),
            "memory_avg": avg_from_history(self.memory_history),
            "disk_avg": avg_from_history(self.disk_history)
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get resource tracker statistics."""
        return {
            "enabled": self.enabled,
            "cpu_samples": len(self.cpu_history),
            "memory_samples": len(self.memory_history),
            "disk_samples": len(self.disk_history),
            "network_samples": len(self.network_history),
            "window_size": self.window_size
        }


class ErrorRateMonitor:
    """Monitor error rates across the system."""
    
    def __init__(self, window_size: int = 1000):
        self.enabled = os.getenv("ERROR_RATE_MONITORING_ENABLED", "false").lower() == "true"
        self.window_size = window_size
        self.requests: deque = deque(maxlen=window_size)
        self.errors: deque = deque(maxlen=window_size)
        self.error_counts: defaultdict = defaultdict(int)
        
        logger.info(f"Error rate monitor initialized (enabled={self.enabled})")
    
    def record_request(self, success: bool, error_type: str = None) -> None:
        """Record a request outcome."""
        if not self.enabled:
            return
        
        timestamp = time.time()
        self.requests.append(timestamp)
        
        if not success:
            self.errors.append(timestamp)
            if error_type:
                self.error_counts[error_type] += 1
    
    def get_error_rate(self, duration_seconds: int = 300) -> Dict[str, Any]:
        """Get error rate over a time period."""
        if not self.enabled:
            return {"enabled": False}
        
        cutoff = time.time() - duration_seconds
        
        total_requests = len([t for t in self.requests if t >= cutoff])
        total_errors = len([t for t in self.errors if t >= cutoff])
        
        error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate": error_rate,
            "success_rate": 100 - error_rate,
            "duration_seconds": duration_seconds,
            "error_breakdown": dict(self.error_counts)
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get error rate monitor statistics."""
        return {
            "enabled": self.enabled,
            "total_requests": len(self.requests),
            "total_errors": len(self.errors),
            "error_types": len(self.error_counts),
            "current_error_rate": self.get_error_rate()["error_rate"]
        }


class BusinessMetricsTracker:
    """Track business-level metrics."""
    
    def __init__(self):
        self.enabled = os.getenv("BUSINESS_METRICS_ENABLED", "false").lower() == "true"
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        
        logger.info(f"Business metrics tracker initialized (enabled={self.enabled})")
    
    def record_metric(self, metric_name: str, value: float, labels: Dict[str, str] = None) -> None:
        """Record a business metric."""
        if not self.enabled:
            return
        
        self.metrics[metric_name].append({
            "timestamp": time.time(),
            "value": value,
            "labels": labels or {}
        })
    
    def get_metric_summary(self, metric_name: str, duration_seconds: int = 3600) -> Dict[str, Any]:
        """Get summary statistics for a metric."""
        if not self.enabled or metric_name not in self.metrics:
            return {"error": "Metric not found or disabled"}
        
        cutoff = time.time() - duration_seconds
        values = [m["value"] for m in self.metrics[metric_name] if m["timestamp"] >= cutoff]
        
        if not values:
            return {"error": "No data in time period"}
        
        values.sort()
        n = len(values)
        
        return {
            "metric": metric_name,
            "count": n,
            "min": values[0],
            "max": values[-1],
            "avg": sum(values) / n,
            "median": values[n // 2],
            "p95": values[int(n * 0.95)] if n > 20 else None,
            "p99": values[int(n * 0.99)] if n > 100 else None,
            "duration_seconds": duration_seconds
        }
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get all business metrics for dashboard display."""
        if not self.enabled:
            return {"enabled": False}
        
        dashboard = {
            "enabled": self.enabled,
            "timestamp": datetime.now().isoformat(),
            "metrics": {}
        }
        
        # Define key business metrics
        key_metrics = [
            "cases_processed",
            "cases_automated",
            "automation_rate",
            "average_processing_time",
            "active_users",
            "revenue",
            "customer_satisfaction"
        ]
        
        for metric in key_metrics:
            if metric in self.metrics:
                summary = self.get_metric_summary(metric, duration_seconds=3600)
                if "error" not in summary:
                    dashboard["metrics"][metric] = summary
        
        return dashboard
    
    def get_stats(self) -> Dict[str, Any]:
        """Get business metrics statistics."""
        return {
            "enabled": self.enabled,
            "total_metrics": len(self.metrics),
            "total_data_points": sum(len(v) for v in self.metrics.values())
        }


# Global instances
_global_threshold_monitor: Optional[PerformanceThresholdMonitor] = None
_global_resource_tracker: Optional[ResourceUtilizationTracker] = None
_global_error_monitor: Optional[ErrorRateMonitor] = None
_global_business_tracker: Optional[BusinessMetricsTracker] = None


def get_performance_threshold_monitor() -> PerformanceThresholdMonitor:
    """Get the global performance threshold monitor instance."""
    global _global_threshold_monitor
    if _global_threshold_monitor is None:
        _global_threshold_monitor = PerformanceThresholdMonitor()
    return _global_threshold_monitor


def get_resource_utilization_tracker() -> ResourceUtilizationTracker:
    """Get the global resource utilization tracker instance."""
    global _global_resource_tracker
    if _global_resource_tracker is None:
        _global_resource_tracker = ResourceUtilizationTracker()
    return _global_resource_tracker


def get_error_rate_monitor() -> ErrorRateMonitor:
    """Get the global error rate monitor instance."""
    global _global_error_monitor
    if _global_error_monitor is None:
        _global_error_monitor = ErrorRateMonitor()
    return _global_error_monitor


def get_business_metrics_tracker() -> BusinessMetricsTracker:
    """Get the global business metrics tracker instance."""
    global _global_business_tracker
    if _global_business_tracker is None:
        _global_business_tracker = BusinessMetricsTracker()
    return _global_business_tracker
