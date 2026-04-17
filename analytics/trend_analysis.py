"""
Trend Analysis
Analyzes trends in decisions, risks, and performance over time.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

logger = logging.getLogger(__name__)


class TrendDirection(Enum):
    """Trend direction."""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"


class TrendAnalysis:
    """
    Trend analysis for decision and risk patterns.
    
    Analyzes trends over time to identify patterns and anomalies.
    """
    
    def __init__(self):
        """Initialize trend analysis."""
        self.enabled = os.getenv("TREND_ANALYSIS_ENABLED", "false").lower() == "true"
        
        # Time-series data
        self.time_series_data = defaultdict(list)
        
        logger.info(f"Trend analysis initialized (enabled={self.enabled})")
    
    def record_data_point(
        self,
        metric: str,
        value: float,
        timestamp: Optional[datetime] = None
    ):
        """
        Record a data point for trend analysis.
        
        Args:
            metric: Metric name
            value: Metric value
            timestamp: Timestamp (defaults to now)
        """
        if not self.enabled:
            return
        
        if timestamp is None:
            timestamp = datetime.now()
        
        self.time_series_data[metric].append({
            "value": value,
            "timestamp": timestamp
        })
        
        logger.debug(f"Recorded data point for {metric}: {value}")
    
    def analyze_trend(
        self,
        metric: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze trend for a metric over time.
        
        Args:
            metric: Metric name
            days: Number of days to analyze
            
        Returns:
            Trend analysis result
        """
        if not self.enabled:
            return {
                "trend_analysis_enabled": False,
                "metric": metric,
                "reason": "Trend analysis disabled"
            }
        
        if metric not in self.time_series_data:
            return {
                "trend_analysis_enabled": True,
                "metric": metric,
                "reason": "No data for metric"
            }
        
        cutoff = datetime.now() - timedelta(days=days)
        recent_data = [
            d for d in self.time_series_data[metric]
            if d["timestamp"] >= cutoff
        ]
        
        if len(recent_data) < 2:
            return {
                "trend_analysis_enabled": True,
                "metric": metric,
                "reason": "Insufficient data for trend analysis"
            }
        
        # Calculate trend
        values = [d["value"] for d in recent_data]
        
        # Split into two halves for trend direction
        mid_point = len(values) // 2
        first_half = values[:mid_point]
        second_half = values[mid_point:]
        
        if not first_half or not second_half:
            return {
                "trend_analysis_enabled": True,
                "metric": metric,
                "reason": "Insufficient data for trend calculation"
            }
        
        first_avg = statistics.mean(first_half)
        second_avg = statistics.mean(second_half)
        
        # Determine direction
        change_percent = ((second_avg - first_avg) / first_avg) * 100 if first_avg != 0 else 0
        
        if change_percent > 5:
            direction = TrendDirection.INCREASING
        elif change_percent < -5:
            direction = TrendDirection.DECREASING
        else:
            direction = TrendDirection.STABLE
        
        # Calculate volatility
        if len(values) > 1:
            volatility = statistics.stdev(values)
        else:
            volatility = 0
        
        return {
            "trend_analysis_enabled": True,
            "metric": metric,
            "direction": direction.value,
            "change_percent": change_percent,
            "volatility": volatility,
            "current_value": values[-1],
            "avg_value": statistics.mean(values),
            "min_value": min(values),
            "max_value": max(values)
        }
    
    def get_all_trends(self, days: int = 30) -> Dict[str, Any]:
        """
        Get trends for all metrics.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            All trends
        """
        if not self.enabled:
            return {"enabled": False}
        
        trends = {}
        for metric in self.time_series_data:
            trends[metric] = self.analyze_trend(metric, days)
        
        return {
            "enabled": True,
            "days": days,
            "trends": trends
        }
    
    def detect_anomalies(
        self,
        metric: str,
        days: int = 30,
        std_dev_threshold: float = 2.0
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalies in a metric.
        
        Args:
            metric: Metric name
            days: Number of days to analyze
            std_dev_threshold: Standard deviation threshold for anomaly detection
            
        Returns:
            List of anomalies
        """
        if not self.enabled:
            return []
        
        if metric not in self.time_series_data:
            return []
        
        cutoff = datetime.now() - timedelta(days=days)
        recent_data = [
            d for d in self.time_series_data[metric]
            if d["timestamp"] >= cutoff
        ]
        
        if len(recent_data) < 10:
            return []
        
        values = [d["value"] for d in recent_data]
        mean = statistics.mean(values)
        std_dev = statistics.stdev(values) if len(values) > 1 else 0
        
        anomalies = []
        for data_point in recent_data:
            value = data_point["value"]
            if std_dev > 0 and abs(value - mean) > std_dev_threshold * std_dev:
                anomalies.append({
                    "metric": metric,
                    "value": value,
                    "expected_range": (mean - std_dev_threshold * std_dev, mean + std_dev_threshold * std_dev),
                    "timestamp": data_point["timestamp"].isoformat(),
                    "deviation": abs(value - mean) / std_dev
                })
        
        return anomalies
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get trend analysis summary.
        
        Returns:
            Summary data
        """
        if not self.enabled:
            return {"enabled": False}
        
        return {
            "enabled": True,
            "metrics_tracked": len(self.time_series_data),
            "total_data_points": sum(len(data) for data in self.time_series_data.values())
        }


# Global trend analysis instance
_global_trend_analysis: Optional[TrendAnalysis] = None


def get_trend_analysis() -> TrendAnalysis:
    """
    Get global trend analysis instance (singleton pattern).
    
    Returns:
        TrendAnalysis instance
    """
    global _global_trend_analysis
    if _global_trend_analysis is None:
        _global_trend_analysis = TrendAnalysis()
    return _global_trend_analysis
