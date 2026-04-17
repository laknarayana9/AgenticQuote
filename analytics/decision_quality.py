"""
Decision Quality Scoring
Scores decision quality based on multiple factors for continuous improvement.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class QualityScore:
    """Quality score components."""
    CONFIDENCE = "confidence"
    EVIDENCE = "evidence"
    CONSISTENCY = "consistency"
    COMPLETENESS = "completeness"
    COMPLIANCE = "compliance"


class DecisionQualityScorer:
    """
    Decision quality scoring system.
    
    Scores decisions based on confidence, evidence quality, consistency, and compliance.
    """
    
    def __init__(self):
        """Initialize decision quality scorer."""
        self.enabled = os.getenv("DECISION_QUALITY_ENABLED", "false").lower() == "true"
        
        # Quality history
        self.quality_history = []
        
        # Quality weights
        self.weights = {
            QualityScore.CONFIDENCE: 0.3,
            QualityScore.EVIDENCE: 0.25,
            QualityScore.CONSISTENCY: 0.2,
            QualityScore.COMPLETENESS: 0.15,
            QualityScore.COMPLIANCE: 0.1
        }
        
        logger.info(f"Decision quality scorer initialized (enabled={self.enabled})")
    
    def score_decision(
        self,
        decision: str,
        confidence: float,
        evidence_count: int,
        evidence_sources: List[str],
        risk_factors: List[str],
        required_fields: List[str],
        provided_fields: List[str],
        compliance_score: float
    ) -> Dict[str, Any]:
        """
        Score a decision based on multiple quality factors.
        
        Args:
            decision: Decision type
            confidence: Confidence score (0-1)
            evidence_count: Number of evidence items
            evidence_sources: List of evidence source types
            risk_factors: List of risk factors identified
            required_fields: List of required data fields
            provided_fields: List of provided data fields
            compliance_score: Compliance score (0-1)
            
        Returns:
            Quality score result
        """
        if not self.enabled:
            return {
                "quality_scoring_enabled": False,
                "overall_score": 0.5,
                "reason": "Quality scoring disabled"
            }
        
        # Calculate component scores
        confidence_score = confidence
        evidence_score = self._score_evidence(evidence_count, evidence_sources)
        consistency_score = self._score_consistency(risk_factors, decision)
        completeness_score = self._score_completeness(required_fields, provided_fields)
        compliance_score_actual = compliance_score
        
        # Calculate weighted overall score
        overall_score = (
            confidence_score * self.weights[QualityScore.CONFIDENCE] +
            evidence_score * self.weights[QualityScore.EVIDENCE] +
            consistency_score * self.weights[QualityScore.CONSISTENCY] +
            completeness_score * self.weights[QualityScore.COMPLETENESS] +
            compliance_score_actual * self.weights[QualityScore.COMPLIANCE]
        )
        
        # Record quality score
        quality_record = {
            "decision": decision,
            "overall_score": overall_score,
            "components": {
                "confidence": confidence_score,
                "evidence": evidence_score,
                "consistency": consistency_score,
                "completeness": completeness_score,
                "compliance": compliance_score_actual
            },
            "timestamp": datetime.now()
        }
        
        self.quality_history.append(quality_record)
        
        return {
            "quality_scoring_enabled": True,
            "overall_score": overall_score,
            "components": quality_record["components"],
            "quality_level": self._get_quality_level(overall_score)
        }
    
    def _score_evidence(self, evidence_count: int, evidence_sources: List[str]) -> float:
        """Score evidence quality."""
        # Base score on evidence count
        count_score = min(evidence_count / 5, 1.0)  # Max at 5 evidence items
        
        # Bonus for diverse sources
        unique_sources = len(set(evidence_sources))
        source_bonus = min(unique_sources / 3, 0.2)  # Max bonus 0.2 for 3+ sources
        
        return min(count_score + source_bonus, 1.0)
    
    def _score_consistency(self, risk_factors: List[str], decision: str) -> float:
        """Score decision consistency with risk factors."""
        if decision == "accept":
            # Should have minimal risk factors
            return max(1.0 - len(risk_factors) / 5, 0.0)
        elif decision in ["refer", "decline"]:
            # Should have relevant risk factors
            return min(len(risk_factors) / 3, 1.0)
        else:
            return 0.5  # Neutral for other decisions
    
    def _score_completeness(self, required_fields: List[str], provided_fields: List[str]) -> float:
        """Score data completeness."""
        if not required_fields:
            return 1.0
        
        provided_set = set(provided_fields)
        required_set = set(required_fields)
        
        missing = required_set - provided_set
        completeness = 1.0 - (len(missing) / len(required_set))
        
        return max(completeness, 0.0)
    
    def _get_quality_level(self, score: float) -> str:
        """Get quality level from score."""
        if score >= 0.9:
            return "excellent"
        elif score >= 0.8:
            return "good"
        elif score >= 0.7:
            return "acceptable"
        elif score >= 0.6:
            return "needs_improvement"
        else:
            return "poor"
    
    def get_quality_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get quality summary for a time window.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Quality summary
        """
        if not self.enabled:
            return {"enabled": False}
        
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_scores = [
            q for q in self.quality_history
            if q["timestamp"] >= cutoff
        ]
        
        if not recent_scores:
            return {
                "enabled": True,
                "time_window_hours": hours,
                "total_decisions": 0
            }
        
        scores = [q["overall_score"] for q in recent_scores]
        avg_score = sum(scores) / len(scores)
        
        # Count quality levels
        level_counts = defaultdict(int)
        for q in recent_scores:
            level_counts[self._get_quality_level(q["overall_score"])] += 1
        
        return {
            "enabled": True,
            "time_window_hours": hours,
            "total_decisions": len(recent_scores),
            "avg_quality_score": avg_score,
            "quality_level": self._get_quality_level(avg_score),
            "quality_distribution": dict(level_counts)
        }
    
    def get_component_averages(self) -> Dict[str, Any]:
        """
        Get average scores for each quality component.
        
        Returns:
            Component averages
        """
        if not self.enabled:
            return {"enabled": False}
        
        if not self.quality_history:
            return {
                "enabled": True,
                "averages": {}
            }
        
        component_sums = defaultdict(list)
        for q in self.quality_history:
            for component, score in q["components"].items():
                component_sums[component].append(score)
        
        averages = {}
        for component, scores in component_sums.items():
            averages[component] = sum(scores) / len(scores)
        
        return {
            "enabled": True,
            "averages": averages
        }


# Global decision quality scorer instance
_global_quality_scorer: Optional[DecisionQualityScorer] = None


def get_decision_quality_scorer() -> DecisionQualityScorer:
    """
    Get global decision quality scorer instance (singleton pattern).
    
    Returns:
        DecisionQualityScorer instance
    """
    global _global_quality_scorer
    if _global_quality_scorer is None:
        _global_quality_scorer = DecisionQualityScorer()
    return _global_quality_scorer
