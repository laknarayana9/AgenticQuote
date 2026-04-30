"""
Minimal HITL automation implementation for test compatibility
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class HITLAutomation:
    """Simple HITL automation implementation"""
    
    def __init__(self):
        self.automations: List[Dict[str, Any]] = []
        logger.info("HITL automation initialized")
    
    def create_automation(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Create automation rule"""
        automation = {
            "id": f"auto_{len(self.automations)}",
            "task": task,
            "status": "active"
        }
        self.automations.append(automation)
        return automation
    
    def get_automation_count(self) -> int:
        """Get total automation count"""
        return len(self.automations)

def get_hitl_automation():
    """Get HITL automation instance"""
    return HITLAutomation()

__all__ = ["HITLAutomation", "get_hitl_automation"]
