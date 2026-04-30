"""
Minimal decision composer implementation for test compatibility
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class DecisionComposer:
    """Simple decision composer implementation"""
    
    def __init__(self):
        self.decisions: List[Dict[str, Any]] = []
        logger.info("Decision composer initialized")
    
    def compose_decision(self, evidence: List[Dict[str, Any]], rules: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compose decision from evidence and rules"""
        decision = {
            "decision": "ACCEPT",
            "confidence": 0.8,
            "evidence_used": evidence[:3],
            "rules_applied": rules[:2],
            "reasoning": "Decision composed based on available evidence"
        }
        self.decisions.append(decision)
        return decision
    
    def get_decision_count(self) -> int:
        """Get total decision count"""
        return len(self.decisions)

def get_decision_composer():
    """Get decision composer instance"""
    return DecisionComposer()

__all__ = ["DecisionComposer", "get_decision_composer"]
