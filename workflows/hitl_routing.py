"""
Minimal HITL routing implementation for test compatibility
"""

import logging
from typing import Dict, Any, List
from enum import Enum

logger = logging.getLogger(__name__)

class ExpertiseArea(Enum):
    """Expertise areas for HITL routing"""
    UNDERWRITING = "underwriting"
    CLAIMS = "claims"
    POLICY = "policy"
    RISK = "risk"

class SmartHITLRouter:
    """Simple HITL router implementation"""
    
    def __init__(self):
        self.routes: Dict[str, List[str]] = {}
        logger.info("Smart HITL router initialized")
    
    def route_task(self, task: Dict[str, Any]) -> str:
        """Route task to appropriate expert"""
        task_type = task.get("type", "underwriting")
        return f"expert_{task_type}"
    
    def add_route(self, task_type: str, experts: List[str]):
        """Add routing rule"""
        self.routes[task_type] = experts
    
    def get_route_count(self) -> int:
        """Get total route count"""
        return len(self.routes)

def get_smart_hitl_router():
    """Get smart HITL router instance"""
    return SmartHITLRouter()

__all__ = ["SmartHITLRouter", "ExpertiseArea", "get_smart_hitl_router"]
