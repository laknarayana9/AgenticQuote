"""
Agent Learning Module
Enables agents to learn from HITL feedback and improve decision-making over time.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class FeedbackType:
    """Types of HITL feedback."""
    APPROVAL = "approval"
    REJECTION = "rejection"
    CORRECTION = "correction"
    SUGGESTION = "suggestion"


class LearningStrategy:
    """Learning strategies for agent improvement."""
    REINFORCEMENT = "reinforcement"  # Reinforce correct decisions
    CORRECTION = "correction"  # Correct incorrect decisions
    PATTERN_LEARNING = "pattern_learning"  # Learn patterns from feedback
    THRESHOLD_TUNING = "threshold_tuning"  # Adjust decision thresholds


class AgentLearning:
    """
    Agent learning from HITL feedback.
    
    Tracks feedback, identifies patterns, and adjusts agent behavior.
    """
    
    def __init__(self, agent_id: str):
        """
        Initialize agent learning.
        
        Args:
            agent_id: Unique agent identifier
        """
        self.agent_id = agent_id
        self.enabled = os.getenv("AGENT_LEARNING_ENABLED", "false").lower() == "true"
        
        # Feedback storage
        self.feedback_history = []
        
        # Learning metrics
        self.metrics = {
            "total_feedback": 0,
            "approvals": 0,
            "rejections": 0,
            "corrections": 0,
            "accuracy": 0.0
        }
        
        # Learned patterns
        self.patterns = defaultdict(int)
        
        # Threshold adjustments
        self.thresholds = {
            "wildfire_risk_threshold": 0.6,
            "flood_risk_threshold": 0.6,
            "age_threshold": 1940,
            "claims_threshold": 2
        }
        
        logger.info(f"Agent learning initialized for {agent_id} (enabled={self.enabled})")
    
    def record_feedback(
        self,
        original_decision: str,
        human_decision: str,
        feedback_type: str,
        case_data: Dict[str, Any],
        notes: Optional[str] = None
    ) -> str:
        """
        Record HITL feedback for learning.
        
        Args:
            original_decision: Agent's original decision
            human_decision: Human reviewer's decision
            feedback_type: Type of feedback
            case_data: Case data that led to the decision
            notes: Additional notes from reviewer
            
        Returns:
            Feedback ID
        """
        if not self.enabled:
            return None
        
        feedback_id = f"feedback_{datetime.now().timestamp()}"
        
        feedback = {
            "feedback_id": feedback_id,
            "agent_id": self.agent_id,
            "original_decision": original_decision,
            "human_decision": human_decision,
            "feedback_type": feedback_type,
            "case_data": self._extract_key_features(case_data),
            "notes": notes,
            "timestamp": datetime.now().isoformat()
        }
        
        self.feedback_history.append(feedback)
        self._update_metrics(feedback)
        self._learn_from_feedback(feedback)
        
        logger.debug(f"Recorded feedback {feedback_id} for agent {self.agent_id}")
        return feedback_id
    
    def get_learning_summary(self) -> Dict[str, Any]:
        """
        Get learning summary.
        
        Returns:
            Dictionary with learning statistics
        """
        if not self.enabled:
            return {"enabled": False}
        
        return {
            "enabled": True,
            "agent_id": self.agent_id,
            "metrics": self.metrics,
            "patterns": dict(self.patterns),
            "thresholds": self.thresholds,
            "feedback_count": len(self.feedback_history)
        }
    
    def get_recommendations(self, case_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get learning-based recommendations for a case.
        
        Args:
            case_data: Case data
            
        Returns:
            List of recommendations
        """
        if not self.enabled:
            return []
        
        recommendations = []
        features = self._extract_key_features(case_data)
        
        # Check against learned patterns
        for pattern, count in self.patterns.items():
            if count > 3 and self._pattern_matches(pattern, features):
                recommendations.append({
                    "type": "pattern_match",
                    "pattern": pattern,
                    "confidence": min(count / 10, 0.9),
                    "suggestion": f"Consider pattern: {pattern}"
                })
        
        # Check threshold adjustments
        if features.get("wildfire_score", 0) > self.thresholds["wildfire_risk_threshold"]:
            recommendations.append({
                "type": "threshold_alert",
                "threshold": "wildfire_risk",
                "current_value": features.get("wildfire_score"),
                "threshold_value": self.thresholds["wildfire_risk_threshold"],
                "suggestion": "Wildfire risk exceeds learned threshold"
            })
        
        return recommendations
    
    def apply_learning(self) -> bool:
        """
        Apply learned adjustments to agent behavior.
        
        Returns:
            True if learning was applied successfully
        """
        if not self.enabled:
            return False
        
        # Apply threshold adjustments based on feedback
        self._adjust_thresholds()
        
        logger.info(f"Applied learning adjustments for agent {self.agent_id}")
        return True
    
    def _extract_key_features(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract key features from case data for learning.
        
        Args:
            case_data: Full case data
            
        Returns:
            Dictionary with key features
        """
        features = {}
        
        # Extract hazard scores
        hazard_profile = case_data.get("hazard_profile", {})
        features["wildfire_score"] = hazard_profile.get("wildfire_risk_score", 0)
        features["flood_score"] = hazard_profile.get("flood_risk_score", 0)
        
        # Extract property features
        property_profile = case_data.get("property_profile", {})
        features["year_built"] = property_profile.get("year_built", 2026)
        features["dwelling_type"] = property_profile.get("dwelling_type", "single_family")
        features["occupancy"] = property_profile.get("occupancy", "owner_occupied_primary")
        
        # Extract claims features
        claims_history = case_data.get("claims_history", {})
        features["loss_count"] = claims_history.get("loss_count_5yr", 0)
        
        return features
    
    def _update_metrics(self, feedback: Dict[str, Any]):
        """
        Update learning metrics.
        
        Args:
            feedback: Feedback record
        """
        self.metrics["total_feedback"] += 1
        
        if feedback["feedback_type"] == FeedbackType.APPROVAL:
            self.metrics["approvals"] += 1
        elif feedback["feedback_type"] == FeedbackType.REJECTION:
            self.metrics["rejections"] += 1
        elif feedback["feedback_type"] == FeedbackType.CORRECTION:
            self.metrics["corrections"] += 1
        
        # Calculate accuracy (approvals / total feedback)
        if self.metrics["total_feedback"] > 0:
            self.metrics["accuracy"] = self.metrics["approvals"] / self.metrics["total_feedback"]
    
    def _learn_from_feedback(self, feedback: Dict[str, Any]):
        """
        Learn from feedback.
        
        Args:
            feedback: Feedback record
        """
        features = feedback["case_data"]
        
        # Learn patterns from corrections
        if feedback["feedback_type"] == FeedbackType.CORRECTION:
            pattern = self._generate_pattern(features, feedback["human_decision"])
            self.patterns[pattern] += 1
        
        # Learn from rejections
        if feedback["feedback_type"] == FeedbackType.REJECTION:
            pattern = self._generate_pattern(features, feedback["human_decision"])
            self.patterns[pattern] += 2  # Weight rejections higher
    
    def _generate_pattern(self, features: Dict[str, Any], decision: str) -> str:
        """
        Generate a pattern string from features and decision.
        
        Args:
            features: Case features
            decision: Decision made
            
        Returns:
            Pattern string
        """
        pattern_parts = []
        
        if features.get("wildfire_score", 0) > 0.6:
            pattern_parts.append("high_wildfire")
        
        if features.get("flood_score", 0) > 0.6:
            pattern_parts.append("high_flood")
        
        if features.get("year_built", 2026) < 1940:
            pattern_parts.append("old_construction")
        
        if features.get("loss_count", 0) > 2:
            pattern_parts.append("high_claims")
        
        if features.get("dwelling_type") == "condo":
            pattern_parts.append("condo")
        
        pattern_parts.append(decision)
        
        return "_".join(pattern_parts)
    
    def _pattern_matches(self, pattern: str, features: Dict[str, Any]) -> bool:
        """
        Check if features match a pattern.
        
        Args:
            pattern: Pattern string
            features: Case features
            
        Returns:
            True if pattern matches
        """
        pattern_parts = pattern.split("_")
        
        for part in pattern_parts:
            if part == "high_wildfire" and features.get("wildfire_score", 0) <= 0.6:
                return False
            elif part == "high_flood" and features.get("flood_score", 0) <= 0.6:
                return False
            elif part == "old_construction" and features.get("year_built", 2026) >= 1940:
                return False
            elif part == "high_claims" and features.get("loss_count", 0) <= 2:
                return False
            elif part == "condo" and features.get("dwelling_type") != "condo":
                return False
        
        return True
    
    def _adjust_thresholds(self):
        """Adjust decision thresholds based on feedback."""
        if self.metrics["total_feedback"] < 10:
            return  # Not enough data to adjust
        
        # Calculate average features for rejections
        rejection_features = []
        for feedback in self.feedback_history:
            if feedback["feedback_type"] == FeedbackType.REJECTION:
                rejection_features.append(feedback["case_data"])
        
        if not rejection_features:
            return
        
        avg_wildfire = sum(f.get("wildfire_score", 0) for f in rejection_features) / len(rejection_features)
        avg_flood = sum(f.get("flood_score", 0) for f in rejection_features) / len(rejection_features)
        
        # Adjust thresholds slightly based on rejection patterns
        if avg_wildfire < self.thresholds["wildfire_risk_threshold"]:
            self.thresholds["wildfire_risk_threshold"] = max(0.3, avg_wildfire - 0.1)
        
        if avg_flood < self.thresholds["flood_risk_threshold"]:
            self.thresholds["flood_risk_threshold"] = max(0.3, avg_flood - 0.1)
        
        logger.debug(f"Adjusted thresholds for agent {self.agent_id}")


class AgentLearningManager:
    """
    Manages learning for all agents.
    """
    
    def __init__(self):
        """Initialize agent learning manager."""
        self.agent_learning = {}
        self.enabled = os.getenv("AGENT_LEARNING_ENABLED", "false").lower() == "true"
        
        logger.info(f"Agent learning manager initialized (enabled={self.enabled})")
    
    def get_agent_learning(self, agent_id: str) -> AgentLearning:
        """
        Get or create learning for an agent.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            AgentLearning instance
        """
        if agent_id not in self.agent_learning:
            self.agent_learning[agent_id] = AgentLearning(agent_id)
        return self.agent_learning[agent_id]
    
    def get_all_summaries(self) -> Dict[str, Any]:
        """
        Get learning summaries for all agents.
        
        Returns:
            Dictionary with all learning summaries
        """
        summaries = {
            "enabled": self.enabled,
            "agents": {}
        }
        
        for agent_id, learning in self.agent_learning.items():
            summaries["agents"][agent_id] = learning.get_learning_summary()
        
        return summaries


# Global agent learning manager instance
_global_learning_manager: Optional[AgentLearningManager] = None


def get_agent_learning_manager() -> AgentLearningManager:
    """
    Get global agent learning manager instance (singleton pattern).
    
    Returns:
        AgentLearningManager instance
    """
    global _global_learning_manager
    if _global_learning_manager is None:
        _global_learning_manager = AgentLearningManager()
    return _global_learning_manager
