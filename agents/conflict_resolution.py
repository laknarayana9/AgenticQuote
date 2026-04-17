"""
Agent Conflict Resolution Module
Resolves conflicts between agents in multi-agent workflows.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ConflictType(Enum):
    """Types of agent conflicts."""
    DECISION_DISAGREEMENT = "decision_disagreement"
    EVIDENCE_CONFLICT = "evidence_conflict"
    RATIONALE_CONFLICT = "rationale_conflict"
    THRESHOLD_CONFLICT = "threshold_conflict"


class ResolutionStrategy(Enum):
    """Conflict resolution strategies."""
    LEAD_AGENT_OVERRIDE = "lead_agent_override"
    MAJORITY_VOTE = "majority_vote"
    WEIGHTED_VOTE = "weighted_vote"
    CONSENSUS_BUILDING = "consensus_building"
    ESCALATION = "escalation"


class Conflict:
    """Represents a conflict between agents."""
    
    def __init__(
        self,
        conflict_id: str,
        conflict_type: str,
        conflicting_agents: List[str],
        details: Dict[str, Any]
    ):
        self.conflict_id = conflict_id
        self.conflict_type = conflict_type
        self.conflicting_agents = conflicting_agents
        self.details = details
        self.resolved = False
        self.resolution = None
        self.resolution_strategy = None


class AgentConflictResolver:
    """
    Resolves conflicts between agents in multi-agent workflows.
    
    Implements various resolution strategies based on conflict type and context.
    """
    
    def __init__(self):
        """Initialize conflict resolver."""
        self.enabled = os.getenv("AGENT_CONFLICT_RESOLUTION_ENABLED", "false").lower() == "true"
        
        # Conflict history
        self.conflict_history = []
        
        # Resolution strategy preferences by conflict type
        self.strategy_preferences = {
            ConflictType.DECISION_DISAGREEMENT: ResolutionStrategy.WEIGHTED_VOTE,
            ConflictType.EVIDENCE_CONFLICT: ResolutionStrategy.CONSENSUS_BUILDING,
            ConflictType.RATIONALE_CONFLICT: ResolutionStrategy.MAJORITY_VOTE,
            ConflictType.THRESHOLD_CONFLICT: ResolutionStrategy.LEAD_AGENT_OVERRIDE
        }
        
        logger.info(f"Agent conflict resolver initialized (enabled={self.enabled})")
    
    def detect_conflicts(
        self,
        assessments: Dict[str, Dict[str, Any]]
    ) -> List[Conflict]:
        """
        Detect conflicts between agent assessments.
        
        Args:
            assessments: Dictionary of agent_id -> assessment
            
        Returns:
            List of detected conflicts
        """
        if not self.enabled:
            return []
        
        conflicts = []
        agent_ids = list(assessments.keys())
        
        if len(agent_ids) < 2:
            return conflicts
        
        # Check for decision disagreements
        decisions = {
            agent_id: assessment.get("preliminary_decision") or assessment.get("decision")
            for agent_id, assessment in assessments.items()
        }
        
        unique_decisions = set(decisions.values())
        
        if len(unique_decisions) > 1:
            conflict = Conflict(
                conflict_id=f"conflict_{len(self.conflict_history)}",
                conflict_type=ConflictType.DECISION_DISAGREEMENT.value,
                conflicting_agents=agent_ids,
                details={
                    "decisions": decisions,
                    "unique_decisions": list(unique_decisions)
                }
            )
            conflicts.append(conflict)
        
        # Check for evidence conflicts
        all_citations = []
        for agent_id, assessment in assessments.items():
            citations = assessment.get("citations_used", [])
            all_citations.append((agent_id, set(citations)))
        
        # Check if agents are using different evidence
        if len(all_citations) >= 2:
            first_citations = all_citations[0][1]
            for agent_id, citations in all_citations[1:]:
                if citations != first_citations and len(citations.intersection(first_citations)) < min(len(citations), len(first_citations)) / 2:
                    conflict = Conflict(
                        conflict_id=f"conflict_{len(self.conflict_history)}",
                        conflict_type=ConflictType.EVIDENCE_CONFLICT.value,
                        conflicting_agents=[all_citations[0][0], agent_id],
                        details={
                            "evidence_mismatch": True
                        }
                    )
                    conflicts.append(conflict)
                    break
        
        return conflicts
    
    def resolve_conflict(
        self,
        conflict: Conflict,
        assessments: Dict[str, Dict[str, Any]],
        lead_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Resolve a conflict using appropriate strategy.
        
        Args:
            conflict: Conflict to resolve
            assessments: Agent assessments
            lead_agent: Optional lead agent for override strategy
            
        Returns:
            Resolution result
        """
        if not self.enabled:
            return {
                "resolved": False,
                "reason": "Conflict resolution disabled"
            }
        
        # Determine strategy
        conflict_type = ConflictType(conflict.conflict_type)
        strategy = self.strategy_preferences.get(conflict_type, ResolutionStrategy.MAJORITY_VOTE)
        
        # Apply resolution strategy
        if strategy == ResolutionStrategy.LEAD_AGENT_OVERRIDE:
            resolution = self._resolve_with_lead_override(conflict, assessments, lead_agent)
        elif strategy == ResolutionStrategy.MAJORITY_VOTE:
            resolution = self._resolve_with_majority_vote(conflict, assessments)
        elif strategy == ResolutionStrategy.WEIGHTED_VOTE:
            resolution = self._resolve_with_weighted_vote(conflict, assessments)
        elif strategy == ResolutionStrategy.CONSENSUS_BUILDING:
            resolution = self._resolve_with_consensus(conflict, assessments)
        elif strategy == ResolutionStrategy.ESCALATION:
            resolution = self._escalate(conflict, assessments)
        else:
            resolution = self._resolve_with_majority_vote(conflict, assessments)
        
        # Update conflict
        conflict.resolved = resolution["resolved"]
        conflict.resolution = resolution
        conflict.resolution_strategy = strategy.value
        
        # Add to history
        self.conflict_history.append(conflict)
        
        return resolution
    
    def _resolve_with_lead_override(
        self,
        conflict: Conflict,
        assessments: Dict[str, Dict[str, Any]],
        lead_agent: Optional[str]
    ) -> Dict[str, Any]:
        """
        Resolve conflict using lead agent override.
        
        Args:
            conflict: Conflict to resolve
            assessments: Agent assessments
            lead_agent: Lead agent ID
            
        Returns:
            Resolution result
        """
        if lead_agent and lead_agent in assessments:
            lead_assessment = assessments[lead_agent]
            decision = lead_assessment.get("preliminary_decision") or lead_assessment.get("decision")
            
            return {
                "resolved": True,
                "strategy": ResolutionStrategy.LEAD_AGENT_OVERRIDE.value,
                "final_decision": decision,
                "lead_agent": lead_agent,
                "rationale": f"Lead agent {lead_agent} decision used"
            }
        
        # Fallback to majority vote
        return self._resolve_with_majority_vote(conflict, assessments)
    
    def _resolve_with_majority_vote(
        self,
        conflict: Conflict,
        assessments: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Resolve conflict using majority vote.
        
        Args:
            conflict: Conflict to resolve
            assessments: Agent assessments
            
        Returns:
            Resolution result
        """
        decisions = []
        for agent_id, assessment in assessments.items():
            if agent_id in conflict.conflicting_agents:
                decision = assessment.get("preliminary_decision") or assessment.get("decision")
                if decision:
                    decisions.append(decision)
        
        if not decisions:
            return {
                "resolved": False,
                "strategy": ResolutionStrategy.MAJORITY_VOTE.value,
                "reason": "No decisions available"
            }
        
        # Count votes
        from collections import Counter
        decision_counts = Counter(decisions)
        majority_decision = decision_counts.most_common(1)[0][0]
        vote_count = decision_counts[majority_decision]
        
        return {
            "resolved": True,
            "strategy": ResolutionStrategy.MAJORITY_VOTE.value,
            "final_decision": majority_decision,
            "vote_count": vote_count,
            "total_votes": len(decisions),
            "rationale": f"Majority decision ({vote_count}/{len(decisions)} votes)"
        }
    
    def _resolve_with_weighted_vote(
        self,
        conflict: Conflict,
        assessments: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Resolve conflict using weighted vote (by confidence).
        
        Args:
            conflict: Conflict to resolve
            assessments: Agent assessments
            
        Returns:
            Resolution result
        """
        decision_weights = {}
        
        for agent_id, assessment in assessments.items():
            if agent_id in conflict.conflicting_agents:
                decision = assessment.get("preliminary_decision") or assessment.get("decision")
                confidence = assessment.get("confidence", 0.5)
                
                if decision:
                    if decision not in decision_weights:
                        decision_weights[decision] = 0
                    decision_weights[decision] += confidence
        
        if not decision_weights:
            return {
                "resolved": False,
                "strategy": ResolutionStrategy.WEIGHTED_VOTE.value,
                "reason": "No decisions available"
            }
        
        # Find highest weighted decision
        weighted_decision = max(decision_weights.items(), key=lambda x: x[1])[0]
        
        return {
            "resolved": True,
            "strategy": ResolutionStrategy.WEIGHTED_VOTE.value,
            "final_decision": weighted_decision,
            "weights": decision_weights,
            "rationale": f"Highest confidence decision selected"
        }
    
    def _resolve_with_consensus(
        self,
        conflict: Conflict,
        assessments: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Resolve conflict through consensus building.
        
        Args:
            conflict: Conflict to resolve
            assessments: Agent assessments
            
        Returns:
            Resolution result
        """
        # For now, fall back to weighted vote
        # In a full implementation, this would involve iterative negotiation
        return self._resolve_with_weighted_vote(conflict, assessments)
    
    def _escalate(
        self,
        conflict: Conflict,
        assessments: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Escalate conflict to human review.
        
        Args:
            conflict: Conflict to resolve
            assessments: Agent assessments
            
        Returns:
            Resolution result
        """
        return {
            "resolved": False,
            "strategy": ResolutionStrategy.ESCALATION.value,
            "final_decision": "REFER",
            "reason": "Conflict escalated to human review",
            "conflict_id": conflict.conflict_id
        }
    
    def get_conflict_stats(self) -> Dict[str, Any]:
        """
        Get conflict resolution statistics.
        
        Returns:
            Dictionary with conflict statistics
        """
        if not self.enabled:
            return {"enabled": False}
        
        resolved = sum(1 for c in self.conflict_history if c.resolved)
        unresolved = len(self.conflict_history) - resolved
        
        conflict_types = {}
        for conflict in self.conflict_history:
            ctype = conflict.conflict_type
            conflict_types[ctype] = conflict_types.get(ctype, 0) + 1
        
        resolution_strategies = {}
        for conflict in self.conflict_history:
            if conflict.resolution_strategy:
                strategy = conflict.resolution_strategy
                resolution_strategies[strategy] = resolution_strategies.get(strategy, 0) + 1
        
        return {
            "enabled": True,
            "total_conflicts": len(self.conflict_history),
            "resolved": resolved,
            "unresolved": unresolved,
            "resolution_rate": resolved / len(self.conflict_history) if self.conflict_history else 0,
            "conflict_types": conflict_types,
            "resolution_strategies": resolution_strategies
        }


# Global conflict resolver instance
_global_conflict_resolver: Optional[AgentConflictResolver] = None


def get_agent_conflict_resolver() -> AgentConflictResolver:
    """
    Get global conflict resolver instance (singleton pattern).
    
    Returns:
        AgentConflictResolver instance
    """
    global _global_conflict_resolver
    if _global_conflict_resolver is None:
        _global_conflict_resolver = AgentConflictResolver()
    return _global_conflict_resolver
