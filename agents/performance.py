"""
Agent Performance Tracking and Ranking
Tracks agent performance metrics and ranks agents by effectiveness.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class PerformanceMetric:
    """Performance metrics for agents."""
    ACCURACY = "accuracy"
    SPEED = "speed"
    CONSISTENCY = "consistency"
    CONFIDENCE = "confidence"
    HITL_RATE = "hitl_rate"
    COST = "cost"


class AgentPerformance:
    """
    Tracks performance metrics for a single agent.
    """
    
    def __init__(self, agent_id: str):
        """
        Initialize agent performance tracker.
        
        Args:
            agent_id: Unique agent identifier
        """
        self.agent_id = agent_id
        self.enabled = os.getenv("AGENT_PERFORMANCE_TRACKING", "true").lower() == "true"
        
        # Performance history
        self.decision_history = []
        
        # Metrics
        self.metrics = {
            "total_decisions": 0,
            "correct_decisions": 0,
            "incorrect_decisions": 0,
            "accuracy": 0.0,
            "avg_confidence": 0.0,
            "avg_latency_ms": 0.0,
            "hitl_rate": 0.0,
            "total_cost": 0.0
        }
        
        # Rolling metrics (last 100 decisions)
        self.rolling_metrics = {
            "accuracy": [],
            "confidence": [],
            "latency": []
        }
        
        logger.info(f"Agent performance tracker initialized for {agent_id} (enabled={self.enabled})")
    
    def record_decision(
        self,
        decision: str,
        confidence: float,
        latency_ms: float,
        hitl_required: bool,
        human_corrected: bool,
        cost: float = 0.0
    ):
        """
        Record a decision for performance tracking.
        
        Args:
            decision: Decision made
            confidence: Confidence score (0-1)
            latency_ms: Decision latency in milliseconds
            hitl_required: Whether HITL was required
            human_corrected: Whether human corrected the decision
            cost: Cost of decision (e.g., LLM cost)
        """
        if not self.enabled:
            return
        
        record = {
            "agent_id": self.agent_id,
            "decision": decision,
            "confidence": confidence,
            "latency_ms": latency_ms,
            "hitl_required": hitl_required,
            "human_corrected": human_corrected,
            "cost": cost,
            "timestamp": datetime.now().isoformat()
        }
        
        self.decision_history.append(record)
        
        # Update metrics
        self.metrics["total_decisions"] += 1
        self.metrics["total_cost"] += cost
        
        if human_corrected:
            self.metrics["incorrect_decisions"] += 1
        else:
            self.metrics["correct_decisions"] += 1
        
        # Update rolling metrics
        self.rolling_metrics["accuracy"].append(0 if human_corrected else 1)
        self.rolling_metrics["confidence"].append(confidence)
        self.rolling_metrics["latency"].append(latency_ms)
        
        # Keep only last 100 for rolling metrics
        for key in self.rolling_metrics:
            if len(self.rolling_metrics[key]) > 100:
                self.rolling_metrics[key] = self.rolling_metrics[key][-100:]
        
        # Recalculate metrics
        self._recalculate_metrics()
        
        logger.debug(f"Recorded decision for agent {self.agent_id}")
    
    def _recalculate_metrics(self):
        """Recalculate performance metrics."""
        total = self.metrics["total_decisions"]
        
        if total > 0:
            self.metrics["accuracy"] = self.metrics["correct_decisions"] / total
            self.metrics["avg_confidence"] = sum(self.rolling_metrics["confidence"]) / len(self.rolling_metrics["confidence"])
            self.metrics["avg_latency_ms"] = sum(self.rolling_metrics["latency"]) / len(self.rolling_metrics["latency"])
            
            hitl_count = sum(1 for d in self.decision_history if d["hitl_required"])
            self.metrics["hitl_rate"] = hitl_count / total
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get performance summary.
        
        Returns:
            Dictionary with performance metrics
        """
        if not self.enabled:
            return {"enabled": False}
        
        return {
            "enabled": True,
            "agent_id": self.agent_id,
            "metrics": self.metrics.copy(),
            "rolling_metrics": {
                "accuracy": sum(self.rolling_metrics["accuracy"]) / len(self.rolling_metrics["accuracy"]) if self.rolling_metrics["accuracy"] else 0,
                "confidence": sum(self.rolling_metrics["confidence"]) / len(self.rolling_metrics["confidence"]) if self.rolling_metrics["confidence"] else 0,
                "latency": sum(self.rolling_metrics["latency"]) / len(self.rolling_metrics["latency"]) if self.rolling_metrics["latency"] else 0
            },
            "total_decisions": len(self.decision_history)
        }
    
    def get_trend(self, metric: str, hours: int = 24) -> Dict[str, Any]:
        """
        Get performance trend for a metric over time.
        
        Args:
            metric: Metric to analyze
            hours: Number of hours to look back
            
        Returns:
            Dictionary with trend data
        """
        if not self.enabled:
            return {"enabled": False}
        
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_decisions = [
            d for d in self.decision_history
            if datetime.fromisoformat(d["timestamp"]) > cutoff
        ]
        
        if not recent_decisions:
            return {"trend": "insufficient_data"}
        
        # Calculate trend
        values = []
        for decision in recent_decisions:
            if metric == PerformanceMetric.ACCURACY:
                values.append(0 if decision["human_corrected"] else 1)
            elif metric == PerformanceMetric.CONFIDENCE:
                values.append(decision["confidence"])
            elif metric == PerformanceMetric.SPEED:
                values.append(decision["latency_ms"])
        
        if not values:
            return {"trend": "no_data"}
        
        # Calculate trend direction
        if len(values) < 2:
            return {"trend": "insufficient_data"}
        
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]
        
        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)
        
        if second_avg > first_avg * 1.05:
            trend = "improving"
        elif second_avg < first_avg * 0.95:
            trend = "declining"
        else:
            trend = "stable"
        
        return {
            "enabled": True,
            "metric": metric,
            "trend": trend,
            "first_half_avg": first_avg,
            "second_half_avg": second_avg,
            "change_percent": ((second_avg - first_avg) / first_avg) * 100 if first_avg > 0 else 0
        }


class AgentRanking:
    """
    Ranks agents by performance metrics.
    """
    
    def __init__(self):
        """Initialize agent ranking system."""
        self.agent_performances = {}
        self.ranking_criteria = {
            "accuracy": 0.4,
            "hitl_rate": 0.3,
            "speed": 0.2,
            "cost": 0.1
        }
    
    def register_agent(self, agent_performance: AgentPerformance):
        """
        Register an agent for ranking.
        
        Args:
            agent_performance: AgentPerformance instance
        """
        self.agent_performances[agent_performance.agent_id] = agent_performance
    
    def get_rankings(self) -> List[Dict[str, Any]]:
        """
        Get agent rankings.
        
        Returns:
            List of agents sorted by ranking score
        """
        rankings = []
        
        for agent_id, performance in self.agent_performances.items():
            summary = performance.get_performance_summary()
            
            if not summary.get("enabled"):
                continue
            
            metrics = summary["metrics"]
            
            # Calculate ranking score
            score = 0
            score += metrics["accuracy"] * self.ranking_criteria["accuracy"]
            score += (1 - metrics["hitl_rate"]) * self.ranking_criteria["hitl_rate"]  # Lower HITL rate is better
            score += (1 - min(metrics["avg_latency_ms"] / 1000, 1)) * self.ranking_criteria["speed"]  # Lower latency is better
            score += (1 - min(metrics["total_cost"] / 10, 1)) * self.ranking_criteria["cost"]  # Lower cost is better
            
            rankings.append({
                "agent_id": agent_id,
                "score": score,
                "metrics": metrics,
                "rank": 0  # Will be set after sorting
            })
        
        # Sort by score (descending)
        rankings.sort(key=lambda x: x["score"], reverse=True)
        
        # Assign ranks
        for i, ranking in enumerate(rankings, 1):
            ranking["rank"] = i
        
        return rankings
    
    def get_top_agent(self) -> Optional[str]:
        """
        Get the top-performing agent.
        
        Returns:
            Agent ID of top performer, or None if no agents registered
        """
        rankings = self.get_rankings()
        return rankings[0]["agent_id"] if rankings else None
    
    def get_agent_rank(self, agent_id: str) -> Optional[int]:
        """
        Get rank of a specific agent.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Rank of agent, or None if agent not found
        """
        rankings = self.get_rankings()
        for ranking in rankings:
            if ranking["agent_id"] == agent_id:
                return ranking["rank"]
        return None


class AgentPerformanceManager:
    """
    Manages performance tracking for all agents.
    """
    
    def __init__(self):
        """Initialize agent performance manager."""
        self.agent_performances = {}
        self.ranking = AgentRanking()
        self.enabled = os.getenv("AGENT_PERFORMANCE_TRACKING", "true").lower() == "true"
        
        logger.info(f"Agent performance manager initialized (enabled={self.enabled})")
    
    def get_agent_performance(self, agent_id: str) -> AgentPerformance:
        """
        Get or create performance tracker for an agent.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            AgentPerformance instance
        """
        if agent_id not in self.agent_performances:
            performance = AgentPerformance(agent_id)
            self.agent_performances[agent_id] = performance
            self.ranking.register_agent(performance)
        return self.agent_performances[agent_id]
    
    def get_all_summaries(self) -> Dict[str, Any]:
        """
        Get performance summaries for all agents.
        
        Returns:
            Dictionary with all performance summaries
        """
        summaries = {
            "enabled": self.enabled,
            "agents": {}
        }
        
        for agent_id, performance in self.agent_performances.items():
            summaries["agents"][agent_id] = performance.get_performance_summary()
        
        return summaries
    
    def get_rankings(self) -> List[Dict[str, Any]]:
        """
        Get agent rankings.
        
        Returns:
            List of agent rankings
        """
        return self.ranking.get_rankings()


# Global agent performance manager instance
_global_performance_manager: Optional[AgentPerformanceManager] = None


def get_agent_performance_manager() -> AgentPerformanceManager:
    """
    Get global agent performance manager instance (singleton pattern).
    
    Returns:
        AgentPerformanceManager instance
    """
    global _global_performance_manager
    if _global_performance_manager is None:
        _global_performance_manager = AgentPerformanceManager()
    return _global_performance_manager
