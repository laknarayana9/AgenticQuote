"""
HITL Escalation Paths and SLA Management
Manages escalation paths and SLA tracking for HITL tasks.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class EscalationLevel(Enum):
    """Escalation levels."""
    LEVEL_1 = "level_1"  # Standard reviewer
    LEVEL_2 = "level_2"  # Senior reviewer
    LEVEL_3 = "level_3"  # Manager
    LEVEL_4 = "level_4"  # Director
    ESCALATED = "escalated"  # Fully escalated


class SLAStatus(Enum):
    """SLA status."""
    ON_TRACK = "on_track"
    AT_RISK = "at_risk"
    VIOLATED = "violated"
    EXPIRED = "expired"


class EscalationPath:
    """Escalation path configuration."""
    
    def __init__(
        self,
        path_id: str,
        name: str,
        levels: List[Dict[str, Any]],
        time_per_level_hours: int
    ):
        self.path_id = path_id
        self.name = name
        self.levels = levels
        self.time_per_level_hours = time_per_level_hours


class HITLEscalation:
    """
    HITL escalation paths and SLA management.
    
    Manages escalation through multiple levels and tracks SLA compliance.
    """
    
    def __init__(self):
        """Initialize HITL escalation system."""
        self.enabled = os.getenv("HITL_ESCALATION_ENABLED", "false").lower() == "true"
        self.sla_hours = int(os.getenv("HITL_SLA_HOURS", "24"))
        
        # Escalation paths
        self.escalation_paths = {}
        
        # Task escalation tracking
        self.task_escalations = {}
        
        # SLA violations
        self.sla_violations = []
        
        # Load default escalation paths
        self._load_default_paths()
        
        logger.info(f"HITL escalation initialized (enabled={self.enabled}, SLA={self.sla_hours}h)")
    
    def _load_default_paths(self):
        """Load default escalation paths."""
        # Standard escalation path
        self.escalation_paths["standard"] = EscalationPath(
            path_id="standard",
            name="Standard Escalation",
            levels=[
                {"level": EscalationLevel.LEVEL_1, "role": "reviewer"},
                {"level": EscalationLevel.LEVEL_2, "role": "senior_reviewer"},
                {"level": EscalationLevel.LEVEL_3, "role": "manager"}
            ],
            time_per_level_hours=8
        )
        
        # Urgent escalation path (faster escalation)
        self.escalation_paths["urgent"] = EscalationPath(
            path_id="urgent",
            name="Urgent Escalation",
            levels=[
                {"level": EscalationLevel.LEVEL_1, "role": "reviewer"},
                {"level": EscalationLevel.LEVEL_2, "role": "senior_reviewer"},
                {"level": EscalationLevel.LEVEL_3, "role": "manager"},
                {"level": EscalationLevel.LEVEL_4, "role": "director"}
            ],
            time_per_level_hours=4
        )
    
    def check_escalation_needed(
        self,
        task_id: str,
        created_at: datetime,
        current_level: int = 0,
        path_type: str = "standard"
    ) -> Dict[str, Any]:
        """
        Check if a task needs escalation based on time and level.
        
        Args:
            task_id: Task ID
            created_at: Task creation timestamp
            current_level: Current escalation level
            path_type: Type of escalation path
            
        Returns:
            Escalation result
        """
        if not self.enabled:
            return {
                "escalation_enabled": False,
                "needs_escalation": False,
                "reason": "Escalation disabled"
            }
        
        path = self.escalation_paths.get(path_type)
        if not path:
            return {
                "escalation_enabled": True,
                "needs_escalation": False,
                "reason": f"Escalation path {path_type} not found"
            }
        
        # Check if current level is max
        if current_level >= len(path.levels):
            return {
                "escalation_enabled": True,
                "needs_escalation": False,
                "reason": "Already at maximum escalation level"
            }
        
        # Calculate time at current level
        time_at_level_hours = (datetime.now() - created_at).total_seconds() / 3600
        time_allowed = (current_level + 1) * path.time_per_level_hours
        
        # Check SLA status
        total_time_hours = (datetime.now() - created_at).total_seconds() / 3600
        sla_status = self._check_sla_status(total_time_hours, self.sla_hours)
        
        # Check if escalation needed
        if time_at_level_hours >= path.time_per_level_hours:
            next_level = current_level + 1
            next_level_config = path.levels[next_level - 1]
            
            return {
                "escalation_enabled": True,
                "needs_escalation": True,
                "current_level": current_level,
                "next_level": next_level,
                "next_level_config": next_level_config,
                "time_at_level_hours": time_at_level_hours,
                "time_allowed": path.time_per_level_hours,
                "sla_status": sla_status,
                "reason": f"Time at level exceeded ({time_at_level_hours:.1f}h >= {path.time_per_level_hours}h)"
            }
        
        # Check if SLA at risk
        if sla_status == SLAStatus.AT_RISK:
            return {
                "escalation_enabled": True,
                "needs_escalation": False,
                "sla_status": sla_status,
                "time_remaining_hours": self.sla_hours - total_time_hours,
                "reason": "SLA at risk but not yet time for escalation"
            }
        
        return {
            "escalation_enabled": True,
            "needs_escalation": False,
            "sla_status": sla_status,
            "time_remaining_hours": self.sla_hours - total_time_hours,
            "reason": "No escalation needed"
        }
    
    def escalate_task(
        self,
        task_id: str,
        current_level: int,
        reason: str
    ) -> Dict[str, Any]:
        """
        Escalate a task to the next level.
        
        Args:
            task_id: Task ID
            current_level: Current escalation level
            reason: Reason for escalation
            
        Returns:
            Escalation result
        """
        if not self.enabled:
            return {
                "escalation_enabled": False,
                "escalated": False,
                "reason": "Escalation disabled"
            }
        
        # Track escalation
        self.task_escalations[task_id] = {
            "task_id": task_id,
            "current_level": current_level + 1,
            "escalated_at": datetime.now().isoformat(),
            "reason": reason
        }
        
        return {
            "escalation_enabled": True,
            "escalated": True,
            "new_level": current_level + 1,
            "reason": reason
        }
    
    def _check_sla_status(self, time_elapsed_hours: float, sla_hours: float) -> str:
        """
        Check SLA status.
        
        Args:
            time_elapsed_hours: Time elapsed in hours
            sla_hours: SLA in hours
            
        Returns:
            SLA status
        """
        if time_elapsed_hours >= sla_hours:
            return SLAStatus.VIOLATED.value
        elif time_elapsed_hours >= sla_hours * 0.75:
            return SLAStatus.AT_RISK.value
        else:
            return SLAStatus.ON_TRACK.value
    
    def record_sla_violation(
        self,
        task_id: str,
        violation_type: str,
        details: Dict[str, Any]
    ):
        """
        Record an SLA violation.
        
        Args:
            task_id: Task ID
            violation_type: Type of violation
            details: Violation details
        """
        self.sla_violations.append({
            "task_id": task_id,
            "violation_type": violation_type,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
        logger.warning(f"SLA violation recorded for task {task_id}: {violation_type}")
    
    def get_escalation_stats(self) -> Dict[str, Any]:
        """
        Get escalation statistics.
        
        Returns:
            Dictionary with escalation statistics
        """
        if not self.enabled:
            return {"enabled": False}
        
        return {
            "enabled": True,
            "sla_hours": self.sla_hours,
            "total_escalations": len(self.task_escalations),
            "total_violations": len(self.sla_violations),
            "escalation_paths": {
                path_id: {
                    "name": path.name,
                    "levels": len(path.levels),
                    "time_per_level_hours": path.time_per_level_hours
                }
                for path_id, path in self.escalation_paths.items()
            }
        }
    
    def add_escalation_path(
        self,
        path_id: str,
        name: str,
        levels: List[Dict[str, Any]],
        time_per_level_hours: int
    ):
        """
        Add a custom escalation path.
        
        Args:
            path_id: Path ID
            name: Path name
            levels: Escalation levels
            time_per_level_hours: Time per level in hours
        """
        self.escalation_paths[path_id] = EscalationPath(
            path_id=path_id,
            name=name,
            levels=levels,
            time_per_level_hours=time_per_level_hours
        )
        logger.info(f"Added escalation path: {path_id}")


# Global HITL escalation instance
_global_escalation: Optional[HITLEscalation] = None


def get_hitl_escalation() -> HITLEscalation:
    """
    Get global HITL escalation instance (singleton pattern).
    
    Returns:
        HITLEscalation instance
    """
    global _global_escalation
    if _global_escalation is None:
        _global_escalation = HITLEscalation()
    return _global_escalation
