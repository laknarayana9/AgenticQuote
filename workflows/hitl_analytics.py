"""
HITL Performance Analytics
Tracks and analyzes HITL workflow performance metrics.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class HITLPerformanceAnalytics:
    """
    HITL performance analytics and reporting.
    
    Tracks key metrics for HITL workflow optimization.
    """
    
    def __init__(self):
        """Initialize HITL performance analytics."""
        self.enabled = os.getenv("HITL_ANALYTICS_ENABLED", "false").lower() == "true"
        
        # Performance data
        self.task_history = []
        self.reviewer_performance = defaultdict(dict)
        
        # Metrics
        self.metrics = {
            "total_tasks": 0,
            "auto_approved": 0,
            "human_reviewed": 0,
            "escalated": 0,
            "sla_violations": 0,
            "avg_resolution_time_minutes": 0,
            "avg_queue_time_minutes": 0
        }
        
        logger.info(f"HITL performance analytics initialized (enabled={self.enabled})")
    
    def record_task(
        self,
        task_id: str,
        reviewer_id: Optional[str],
        created_at: datetime,
        completed_at: Optional[datetime],
        resolution_time_minutes: float,
        queue_time_minutes: float,
        auto_approved: bool,
        escalated: bool,
        sla_violated: bool
    ):
        """
        Record task performance data.
        
        Args:
            task_id: Task ID
            reviewer_id: Reviewer ID (if applicable)
            created_at: Task creation timestamp
            completed_at: Task completion timestamp
            resolution_time_minutes: Time to resolve (minutes)
            queue_time_minutes: Time in queue (minutes)
            auto_approved: Whether auto-approved
            escalated: Whether escalated
            sla_violated: Whether SLA was violated
        """
        if not self.enabled:
            return
        
        task_record = {
            "task_id": task_id,
            "reviewer_id": reviewer_id,
            "created_at": created_at,
            "completed_at": completed_at,
            "resolution_time_minutes": resolution_time_minutes,
            "queue_time_minutes": queue_time_minutes,
            "auto_approved": auto_approved,
            "escalated": escalated,
            "sla_violated": sla_violated
        }
        
        self.task_history.append(task_record)
        
        # Update metrics
        self.metrics["total_tasks"] += 1
        if auto_approved:
            self.metrics["auto_approved"] += 1
        else:
            self.metrics["human_reviewed"] += 1
        if escalated:
            self.metrics["escalated"] += 1
        if sla_violated:
            self.metrics["sla_violations"] += 1
        
        # Update reviewer performance
        if reviewer_id:
            if "total_tasks" not in self.reviewer_performance[reviewer_id]:
                self.reviewer_performance[reviewer_id]["total_tasks"] = 0
                self.reviewer_performance[reviewer_id]["avg_resolution_time"] = []
            
            self.reviewer_performance[reviewer_id]["total_tasks"] += 1
            self.reviewer_performance[reviewer_id]["avg_resolution_time"].append(resolution_time_minutes)
        
        # Recalculate averages
        self._recalculate_averages()
    
    def _recalculate_averages(self):
        """Recalculate average metrics."""
        if not self.task_history:
            return
        
        resolution_times = [t["resolution_time_minutes"] for t in self.task_history if t["resolution_time_minutes"]]
        queue_times = [t["queue_time_minutes"] for t in self.task_history if t["queue_time_minutes"]]
        
        if resolution_times:
            self.metrics["avg_resolution_time_minutes"] = sum(resolution_times) / len(resolution_times)
        
        if queue_times:
            self.metrics["avg_queue_time_minutes"] = sum(queue_times) / len(queue_times)
    
    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get performance summary for a time window.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Performance summary
        """
        if not self.enabled:
            return {"enabled": False}
        
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_tasks = [
            t for t in self.task_history
            if t["created_at"] >= cutoff
        ]
        
        summary = {
            "enabled": True,
            "time_window_hours": hours,
            "total_tasks": len(recent_tasks),
            "auto_approved": sum(1 for t in recent_tasks if t["auto_approved"]),
            "human_reviewed": sum(1 for t in recent_tasks if not t["auto_approved"]),
            "escalated": sum(1 for t in recent_tasks if t["escalated"]),
            "sla_violations": sum(1 for t in recent_tasks if t["sla_violated"]),
            "auto_approval_rate": 0,
            "escalation_rate": 0,
            "sla_violation_rate": 0
        }
        
        if recent_tasks:
            summary["auto_approval_rate"] = summary["auto_approved"] / len(recent_tasks)
            summary["escalation_rate"] = summary["escalated"] / len(recent_tasks)
            summary["sla_violation_rate"] = summary["sla_violations"] / len(recent_tasks)
        
        resolution_times = [t["resolution_time_minutes"] for t in recent_tasks if t["resolution_time_minutes"]]
        if resolution_times:
            summary["avg_resolution_time_minutes"] = sum(resolution_times) / len(resolution_times)
        else:
            summary["avg_resolution_time_minutes"] = 0
        
        return summary
    
    def get_reviewer_performance(self, reviewer_id: str) -> Dict[str, Any]:
        """
        Get performance data for a specific reviewer.
        
        Args:
            reviewer_id: Reviewer ID
            
        Returns:
            Reviewer performance data
        """
        if not self.enabled:
            return {"enabled": False}
        
        if reviewer_id not in self.reviewer_performance:
            return {
                "enabled": True,
                "reviewer_id": reviewer_id,
                "found": False
            }
        
        perf = self.reviewer_performance[reviewer_id]
        avg_resolution = sum(perf["avg_resolution_time"]) / len(perf["avg_resolution_time"]) if perf["avg_resolution_time"] else 0
        
        return {
            "enabled": True,
            "reviewer_id": reviewer_id,
            "found": True,
            "total_tasks": perf["total_tasks"],
            "avg_resolution_time_minutes": avg_resolution
        }
    
    def get_top_reviewers(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get top-performing reviewers.
        
        Args:
            limit: Maximum number of reviewers to return
            
        Returns:
            List of top reviewers
        """
        if not self.enabled:
            return []
        
        reviewer_scores = []
        for reviewer_id, perf in self.reviewer_performance.items():
            if perf["avg_resolution_time"]:
                avg_time = sum(perf["avg_resolution_time"]) / len(perf["avg_resolution_time"])
                # Lower resolution time = better performance
                score = 1 / avg_time
            else:
                score = 0
            
            reviewer_scores.append({
                "reviewer_id": reviewer_id,
                "total_tasks": perf["total_tasks"],
                "avg_resolution_time_minutes": avg_time if perf["avg_resolution_time"] else 0,
                "score": score
            })
        
        reviewer_scores.sort(key=lambda x: x["score"], reverse=True)
        return reviewer_scores[:limit]
    
    def get_trends(self, metric: str, days: int = 7) -> Dict[str, Any]:
        """
        Get trend data for a metric over time.
        
        Args:
            metric: Metric to analyze
            days: Number of days to look back
            
        Returns:
            Trend data
        """
        if not self.enabled:
            return {"enabled": False}
        
        cutoff = datetime.now() - timedelta(days=days)
        recent_tasks = [
            t for t in self.task_history
            if t["created_at"] >= cutoff
        ]
        
        # Group by day
        daily_data = defaultdict(list)
        for task in recent_tasks:
            day = task["created_at"].date()
            if metric == "resolution_time":
                daily_data[day].append(task["resolution_time_minutes"])
            elif metric == "queue_time":
                daily_data[day].append(task["queue_time_minutes"])
            elif metric == "auto_approval_rate":
                daily_data[day].append(1 if task["auto_approved"] else 0)
        
        # Calculate daily averages
        trend_data = {}
        for day, values in daily_data.items():
            if values:
                trend_data[day.isoformat()] = sum(values) / len(values)
        
        return {
            "enabled": True,
            "metric": metric,
            "days": days,
            "trend_data": trend_data
        }
    
    def get_analytics_dashboard(self) -> Dict[str, Any]:
        """
        Get comprehensive analytics dashboard data.
        
        Returns:
            Dashboard data
        """
        if not self.enabled:
            return {"enabled": False}
        
        return {
            "enabled": True,
            "overall_metrics": self.metrics.copy(),
            "last_24h": self.get_performance_summary(hours=24),
            "last_7d": self.get_performance_summary(hours=168),
            "top_reviewers": self.get_top_reviewers(limit=5),
            "total_reviewers": len(self.reviewer_performance)
        }


# Global HITL performance analytics instance
_global_analytics: Optional[HITLPerformanceAnalytics] = None


def get_hitl_analytics() -> HITLPerformanceAnalytics:
    """
    Get global HITL performance analytics instance (singleton pattern).
    
    Returns:
        HITLPerformanceAnalytics instance
    """
    global _global_analytics
    if _global_analytics is None:
        _global_analytics = HITLPerformanceAnalytics()
    return _global_analytics
