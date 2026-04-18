"""
Anomaly detection and alerting for Phase D.2
Detects anomalies in metrics using statistical methods and machine learning.
"""

import os
import logging
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import deque
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


@dataclass
class Anomaly:
    """Detected anomaly."""
    id: str
    metric: str
    value: float
    expected_value: float
    deviation: float
    severity: str
    timestamp: datetime
    description: str
    confidence: float
    labels: Dict[str, str]


class AnomalyDetector(ABC):
    """Base class for anomaly detectors."""
    
    def __init__(self, window_size: int = 100, threshold: float = 2.0):
        self.window_size = window_size
        self.threshold = threshold
        self.enabled = True
    
    @abstractmethod
    def detect(self, value: float, metric_data: List[float]) -> Optional[Anomaly]:
        """Detect if a value is anomalous."""
        pass


class StatisticalAnomalyDetector(AnomalyDetector):
    """Statistical anomaly detection using z-score."""
    
    def detect(self, value: float, metric_data: List[float]) -> Optional[Anomaly]:
        """Detect anomaly using z-score."""
        if not self.enabled or len(metric_data) < self.window_size:
            return None
        
        # Use recent window
        window = metric_data[-self.window_size:]
        
        mean = np.mean(window)
        std = np.std(window)
        
        if std == 0:
            return None
        
        z_score = abs((value - mean) / std)
        
        if z_score > self.threshold:
            severity = "critical" if z_score > 3 else "warning"
            return Anomaly(
                id=f"stat-{datetime.now().timestamp()}",
                metric="unknown",
                value=value,
                expected_value=mean,
                deviation=z_score,
                severity=severity,
                timestamp=datetime.now(),
                description=f"Value {value} is {z_score:.2f} standard deviations from mean {mean:.2f}",
                confidence=min(z_score / 3, 1.0),
                labels={"method": "statistical", "z_score": z_score}
            )
        
        return None


class MovingAverageAnomalyDetector(AnomalyDetector):
    """Anomaly detection using moving average with standard deviation."""
    
    def detect(self, value: float, metric_data: List[float]) -> Optional[Anomaly]:
        """Detect anomaly using moving average."""
        if not self.enabled or len(metric_data) < self.window_size:
            return None
        
        window = metric_data[-self.window_size:]
        mean = np.mean(window)
        std = np.std(window)
        
        upper_bound = mean + (self.threshold * std)
        lower_bound = mean - (self.threshold * std)
        
        if value > upper_bound or value < lower_bound:
            severity = "critical" if abs(value - mean) > 3 * std else "warning"
            deviation = (value - mean) / std if std > 0 else 0
            
            return Anomaly(
                id=f"ma-{datetime.now().timestamp()}",
                metric="unknown",
                value=value,
                expected_value=mean,
                deviation=deviation,
                severity=severity,
                timestamp=datetime.now(),
                description=f"Value {value} outside bounds [{lower_bound:.2f}, {upper_bound:.2f}]",
                confidence=min(abs(deviation) / 3, 1.0),
                labels={"method": "moving_average", "bounds": f"[{lower_bound:.2f}, {upper_bound:.2f}]"}
            )
        
        return None


class PercentileAnomalyDetector(AnomalyDetector):
    """Anomaly detection using percentiles."""
    
    def __init__(self, window_size: int = 100, threshold: float = 95.0):
        super().__init__(window_size, threshold)
        self.percentile = threshold
    
    def detect(self, value: float, metric_data: List[float]) -> Optional[Anomaly]:
        """Detect anomaly using percentiles."""
        if not self.enabled or len(metric_data) < self.window_size:
            return None
        
        window = metric_data[-self.window_size:]
        lower_p = (100 - self.threshold) / 2
        upper_p = 100 - lower_p
        
        lower_bound = np.percentile(window, lower_p)
        upper_bound = np.percentile(window, upper_p)
        
        if value > upper_bound or value < lower_bound:
            severity = "critical" if value > np.percentile(window, 99) or value < np.percentile(window, 1) else "warning"
            
            return Anomaly(
                id=f"pct-{datetime.now().timestamp()}",
                metric="unknown",
                value=value,
                expected_value=np.median(window),
                deviation=(value - np.median(window)) / (upper_bound - lower_bound) if upper_bound != lower_bound else 1,
                severity=severity,
                timestamp=datetime.now(),
                description=f"Value {value} outside {self.percentile}th percentile bounds [{lower_bound:.2f}, {upper_bound:.2f}]",
                confidence=0.8,
                labels={"method": "percentile", "percentile": self.threshold}
            )
        
        return None


class AnomalyDetectionManager:
    """Manage anomaly detection across multiple metrics."""
    
    def __init__(self):
        self.enabled = os.getenv("ANOMALY_DETECTION_ENABLED", "false").lower() == "true"
        self.metric_data: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.detectors: Dict[str, List[AnomalyDetector]] = defaultdict(list)
        self.anomalies: List[Anomaly] = []
        self._initialize_detectors()
        
        logger.info(f"Anomaly detection manager initialized (enabled={self.enabled})")
    
    def _initialize_detectors(self) -> None:
        """Initialize default detectors for all metrics."""
        default_detectors = [
            StatisticalAnomalyDetector(window_size=100, threshold=2.0),
            MovingAverageAnomalyDetector(window_size=100, threshold=2.0),
            PercentileAnomalyDetector(window_size=100, threshold=95.0)
        ]
        
        # Add detectors to all metrics (will be metric-specific later)
        self.detectors["default"] = default_detectors
    
    def add_metric_data(self, metric: str, value: float) -> None:
        """Add metric data point."""
        if not self.enabled:
            return
        
        self.metric_data[metric].append(value)
        
        # Detect anomalies
        self._detect_anomalies(metric, value)
    
    def _detect_anomalies(self, metric: str, value: float) -> None:
        """Detect anomalies for a metric."""
        detectors = self.detectors.get(metric, self.detectors["default"])
        metric_data = list(self.metric_data[metric])
        
        for detector in detectors:
            anomaly = detector.detect(value, metric_data)
            if anomaly:
                anomaly.metric = metric
                self.anomalies.append(anomaly)
                logger.warning(f"Anomaly detected: {anomaly.metric} - {anomaly.description}")
    
    def add_detector(self, metric: str, detector: AnomalyDetector) -> None:
        """Add a detector for a specific metric."""
        if metric not in self.detectors:
            self.detectors[metric] = []
        self.detectors[metric].append(detector)
        logger.info(f"Detector added for {metric}: {detector.__class__.__name__}")
    
    def get_recent_anomalies(self, limit: int = 100) -> List[Anomaly]:
        """Get recent anomalies."""
        return self.anomalies[-limit:]
    
    def get_anomalies_by_metric(self, metric: str, limit: int = 100) -> List[Anomaly]:
        """Get anomalies for a specific metric."""
        return [a for a in self.anomalies if a.metric == metric][-limit:]
    
    def get_anomalies_by_severity(self, severity: str, limit: int = 100) -> List[Anomaly]:
        """Get anomalies by severity."""
        return [a for a in self.anomalies if a.severity == severity][-limit:]
    
    def get_anomaly_summary(self, duration_hours: int = 24) -> Dict[str, Any]:
        """Get anomaly summary for a time period."""
        cutoff = datetime.now() - timedelta(hours=duration_hours)
        recent_anomalies = [a for a in self.anomalies if a.timestamp >= cutoff]
        
        return {
            "total_anomalies": len(recent_anomalies),
            "by_severity": {
                severity: len([a for a in recent_anomalies if a.severity == severity])
                for severity in ["critical", "warning", "info"]
            },
            "by_metric": {
                metric: len([a for a in recent_anomalies if a.metric == metric])
                for metric in set(a.metric for a in recent_anomalies)
            },
            "average_confidence": np.mean([a.confidence for a in recent_anomalies]) if recent_anomalies else 0,
            "duration_hours": duration_hours
        }
    
    def clear_old_anomalies(self, days: int = 7) -> int:
        """Clear anomalies older than specified days."""
        cutoff = datetime.now() - timedelta(days=days)
        old_count = len(self.anomalies)
        self.anomalies = [a for a in self.anomalies if a.timestamp >= cutoff]
        cleared = old_count - len(self.anomalies)
        logger.info(f"Cleared {cleared} old anomalies")
        return cleared
    
    def get_stats(self) -> Dict[str, Any]:
        """Get anomaly detection statistics."""
        return {
            "enabled": self.enabled,
            "total_metrics": len(self.metric_data),
            "total_detectors": sum(len(d) for d in self.detectors.values()),
            "total_anomalies": len(self.anomalies),
            "active_anomalies": len([a for a in self.anomalies if a.severity == "critical"]),
            "metric_data_points": sum(len(d) for d in self.metric_data.values())
        }


# Global anomaly detection manager instance
_global_anomaly_manager: Optional[AnomalyDetectionManager] = None


def get_anomaly_detection_manager() -> AnomalyDetectionManager:
    """Get the global anomaly detection manager instance."""
    global _global_anomaly_manager
    if _global_anomaly_manager is None:
        _global_anomaly_manager = AnomalyDetectionManager()
    return _global_anomaly_manager


from collections import defaultdict
