"""
Decision Analytics Dashboard
Provides comprehensive analytics for underwriting decisions.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum

logger = logging.getLogger(__name__)


class DecisionType(Enum):
    """Decision types."""
    ACCEPT = "accept"
    REFER = "refer"
    DECLINE = "decline"
    NEED_INFO = "need_info"


class DecisionAnalytics:
    """
    Decision analytics dashboard for underwriting decisions.
    
    Tracks decision patterns, quality metrics, and provides insights.
    """
    
    def __init__(self):
        """Initialize decision analytics."""
        self.enabled = os.getenv("ANALYTICS_ENABLED", "false").lower() == "true"
        
        # Decision history
        self.decision_history = []
        
        # Decision metrics
        self.metrics = {
            "total_decisions": 0,
            "accept_rate": 0.0,
            "refer_rate": 0.0,
            "decline_rate": 0.0,
            "need_info_rate": 0.0,
            "avg_confidence": 0.0,
            "avg_processing_time_seconds": 0.0
        }
        
        # Decision breakdown by factors
        self.decision_by_risk_type = defaultdict(lambda: defaultdict(int))
        self.decision_by_property_type = defaultdict(lambda: defaultdict(int))
        self.decision_by_region = defaultdict(lambda: defaultdict(int))
        
        logger.info(f"Decision analytics initialized (enabled={self.enabled})")
    
    def record_decision(
        self,
        decision: str,
        confidence: float,
        processing_time_seconds: float,
        risk_factors: List[str],
        property_type: str,
        region: str,
        metadata: Dict[str, Any] = None
    ):
        """
        Record a decision for analytics.
        
        Args:
            decision: Decision type
            confidence: Confidence score (0-1)
            processing_time_seconds: Processing time
            risk_factors: List of risk factors
            property_type: Property type
            region: Geographic region
            metadata: Additional metadata
        """
        if not self.enabled:
            return
        
        decision_record = {
            "decision": decision,
            "confidence": confidence,
            "processing_time_seconds": processing_time_seconds,
            "risk_factors": risk_factors,
            "property_type": property_type,
            "region": region,
            "metadata": metadata or {},
            "timestamp": datetime.now()
        }
        
        self.decision_history.append(decision_record)
        
        # Update decision breakdowns
        for risk in risk_factors:
            self.decision_by_risk_type[risk][decision] += 1
        self.decision_by_property_type[property_type][decision] += 1
        self.decision_by_region[region][decision] += 1
        
        # Update metrics
        self._recalculate_metrics()
        
        logger.debug(f"Recorded decision: {decision}")
    
    def _recalculate_metrics(self):
        """Recalculate decision metrics."""
        total = len(self.decision_history)
        if total == 0:
            return
        
        # Calculate decision rates
        decision_counts = defaultdict(int)
        for record in self.decision_history:
            decision_counts[record["decision"]] += 1
        
        self.metrics["total_decisions"] = total
        self.metrics["accept_rate"] = decision_counts.get("accept", 0) / total
        self.metrics["refer_rate"] = decision_counts.get("refer", 0) / total
        self.metrics["decline_rate"] = decision_counts.get("decline", 0) / total
        self.metrics["need_info_rate"] = decision_counts.get("need_info", 0) / total
        
        # Calculate average confidence
        confidences = [r["confidence"] for r in self.decision_history if r["confidence"]]
        if confidences:
            self.metrics["avg_confidence"] = sum(confidences) / len(confidences)
        
        # Calculate average processing time
        times = [r["processing_time_seconds"] for r in self.decision_history if r["processing_time_seconds"]]
        if times:
            self.metrics["avg_processing_time_seconds"] = sum(times) / len(times)
    
    def get_dashboard_data(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get dashboard data for a time window.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Dashboard data
        """
        if not self.enabled:
            return {"enabled": False}
        
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_decisions = [
            d for d in self.decision_history
            if d["timestamp"] >= cutoff
        ]
        
        return {
            "enabled": True,
            "time_window_hours": hours,
            "total_decisions": len(recent_decisions),
            "metrics": self._calculate_metrics_from_decisions(recent_decisions),
            "decision_breakdown": self._get_decision_breakdown(recent_decisions),
            "top_risk_factors": self._get_top_risk_factors(recent_decisions)
        }
    
    def _calculate_metrics_from_decisions(self, decisions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate metrics from a list of decisions."""
        if not decisions:
            return {}
        
        decision_counts = defaultdict(int)
        for d in decisions:
            decision_counts[d["decision"]] += 1
        
        total = len(decisions)
        confidences = [d["confidence"] for d in decisions if d["confidence"]]
        times = [d["processing_time_seconds"] for d in decisions if d["processing_time_seconds"]]
        
        return {
            "accept_rate": decision_counts.get("accept", 0) / total,
            "refer_rate": decision_counts.get("refer", 0) / total,
            "decline_rate": decision_counts.get("decline", 0) / total,
            "need_info_rate": decision_counts.get("need_info", 0) / total,
            "avg_confidence": sum(confidences) / len(confidences) if confidences else 0,
            "avg_processing_time_seconds": sum(times) / len(times) if times else 0
        }
    
    def _get_decision_breakdown(self, decisions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get decision breakdown by category."""
        breakdown = {
            "by_risk_type": dict(self.decision_by_risk_type),
            "by_property_type": dict(self.decision_by_property_type),
            "by_region": dict(self.decision_by_region)
        }
        return breakdown
    
    def _get_top_risk_factors(self, decisions: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
        """Get top risk factors."""
        risk_counts = defaultdict(int)
        for d in decisions:
            for risk in d["risk_factors"]:
                risk_counts[risk] += 1
        
        sorted_risks = sorted(risk_counts.items(), key=lambda x: x[1], reverse=True)
        return [{"risk": risk, "count": count} for risk, count in sorted_risks[:limit]]
    
    def get_decision_trends(self, days: int = 7) -> Dict[str, Any]:
        """
        Get decision trends over time.
        
        Args:
            days: Number of days to look back
            
        Returns:
            Trend data
        """
        if not self.enabled:
            return {"enabled": False}
        
        cutoff = datetime.now() - timedelta(days=days)
        recent_decisions = [
            d for d in self.decision_history
            if d["timestamp"] >= cutoff
        ]
        
        # Group by day
        daily_data = defaultdict(lambda: defaultdict(int))
        for d in recent_decisions:
            day = d["timestamp"].date()
            daily_data[day][d["decision"]] += 1
        
        # Convert to list
        trend_data = []
        for day, counts in sorted(daily_data.items()):
            trend_data.append({
                "date": day.isoformat(),
                "accept": counts.get("accept", 0),
                "refer": counts.get("refer", 0),
                "decline": counts.get("decline", 0),
                "need_info": counts.get("need_info", 0)
            })
        
        return {
            "enabled": True,
            "days": days,
            "trend_data": trend_data
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get analytics summary.
        
        Returns:
            Summary data
        """
        if not self.enabled:
            return {"enabled": False}
        
        return {
            "enabled": True,
            "total_decisions": self.metrics["total_decisions"],
            "metrics": self.metrics.copy(),
            "decision_breakdown": self._get_decision_breakdown(self.decision_history)
        }


# Global decision analytics instance
_global_decision_analytics: Optional[DecisionAnalytics] = None


def get_decision_analytics() -> DecisionAnalytics:
    """
    Get global decision analytics instance (singleton pattern).
    
    Returns:
        DecisionAnalytics instance
    """
    global _global_decision_analytics
    if _global_decision_analytics is None:
        _global_decision_analytics = DecisionAnalytics()
    return _global_decision_analytics
