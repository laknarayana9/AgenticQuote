"""
Minimal HITL escalation implementation for test compatibility
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class HITLEscalation:
    """Simple HITL escalation implementation"""
    
    def __init__(self):
        self.escalations: List[Dict[str, Any]] = []
        logger.info("HITL escalation initialized")
    
    def create_escalation(self, task: Dict[str, Any], reason: str) -> Dict[str, Any]:
        """Create escalation"""
        escalation = {
            "id": f"escal_{len(self.escalations)}",
            "task": task,
            "reason": reason,
            "status": "pending"
        }
        self.escalations.append(escalation)
        return escalation
    
    def get_escalation_count(self) -> int:
        """Get total escalation count"""
        return len(self.escalations)

def get_hitl_escalation():
    """Get HITL escalation instance"""
    return HITLEscalation()

__all__ = ["HITLEscalation", "get_hitl_escalation"]
