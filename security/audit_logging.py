"""
Audit Logging
Logs all security-relevant events for compliance and auditing.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Audit event types."""
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"
    ROLE_ASSIGNED = "role_assigned"
    ROLE_REVOKED = "role_revoked"
    DECISION_MADE = "decision_made"
    DECISION_OVERRIDDEN = "decision_overridden"
    DATA_ACCESSED = "data_accessed"
    DATA_MODIFIED = "data_modified"
    CONFIGURATION_CHANGED = "configuration_changed"
    SYSTEM_ERROR = "system_error"


class AuditLogger:
    """
    Audit logging system for security and compliance.
    
    Logs all security-relevant events for auditing and compliance.
    """
    
    def __init__(self):
        """Initialize audit logger."""
        self.enabled = os.getenv("AUDIT_LOGGING_ENABLED", "false").lower() == "true"
        
        # Audit log
        self.audit_log = []
        
        # Separate security logger
        self.security_logger = logging.getLogger("security.audit")
        handler = logging.FileHandler("logs/audit.log")
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.security_logger.addHandler(handler)
        self.security_logger.setLevel(logging.INFO)
        
        logger.info(f"Audit logger initialized (enabled={self.enabled})")
    
    def log_event(
        self,
        event_type: str,
        user_id: str,
        resource: str,
        action: str,
        details: Dict[str, Any] = None
    ):
        """
        Log an audit event.
        
        Args:
            event_type: Event type
            user_id: User ID
            resource: Resource affected
            action: Action performed
            details: Additional details
        """
        if not self.enabled:
            return
        
        try:
            event_type_enum = AuditEventType(event_type.lower())
        except ValueError:
            event_type_enum = AuditEventType.SYSTEM_ERROR
        
        event = {
            "event_type": event_type_enum.value,
            "user_id": user_id,
            "resource": resource,
            "action": action,
            "details": details or {},
            "timestamp": datetime.now().isoformat(),
            "ip_address": details.get("ip_address", "unknown") if details else "unknown"
        }
        
        self.audit_log.append(event)
        
        # Log to security logger
        log_message = f"{event_type_enum.value} - User: {user_id} - Resource: {resource} - Action: {action}"
        self.security_logger.info(log_message)
        
        logger.debug(f"Audit event logged: {event_type}")
    
    def log_decision(
        self,
        user_id: str,
        case_id: str,
        decision: str,
        confidence: float,
        details: Dict[str, Any] = None
    ):
        """
        Log a decision event.
        
        Args:
            user_id: User ID
            case_id: Case ID
            decision: Decision made
            confidence: Confidence score
            details: Additional details
        """
        self.log_event(
            event_type=AuditEventType.DECISION_MADE.value,
            user_id=user_id,
            resource=f"case:{case_id}",
            action=f"decision:{decision}",
            details={
                "confidence": confidence,
                **(details or {})
            }
        )
    
    def log_data_access(
        self,
        user_id: str,
        resource_type: str,
        resource_id: str,
        access_type: str
    ):
        """
        Log a data access event.
        
        Args:
            user_id: User ID
            resource_type: Type of resource
            resource_id: Resource ID
            access_type: Type of access (read, write, delete)
        """
        self.log_event(
            event_type=AuditEventType.DATA_ACCESSED.value,
            user_id=user_id,
            resource=f"{resource_type}:{resource_id}",
            action=f"access:{access_type}"
        )
    
    def log_permission_change(
        self,
        admin_id: str,
        target_user_id: str,
        permission: str,
        granted: bool
    ):
        """
        Log a permission change event.
        
        Args:
            admin_id: Admin user ID
            target_user_id: Target user ID
            permission: Permission changed
            granted: Whether permission was granted
        """
        event_type = AuditEventType.PERMISSION_GRANTED if granted else AuditEventType.PERMISSION_REVOKED
        self.log_event(
            event_type=event_type.value,
            user_id=admin_id,
            resource=f"user:{target_user_id}",
            action=f"permission:{permission}"
        )
    
    def log_role_change(
        self,
        admin_id: str,
        target_user_id: str,
        role: str,
        assigned: bool
    ):
        """
        Log a role change event.
        
        Args:
            admin_id: Admin user ID
            target_user_id: Target user ID
            role: Role changed
            assigned: Whether role was assigned
        """
        event_type = AuditEventType.ROLE_ASSIGNED if assigned else AuditEventType.ROLE_REVOKED
        self.log_event(
            event_type=event_type.value,
            user_id=admin_id,
            resource=f"user:{target_user_id}",
            action=f"role:{role}"
        )
    
    def get_audit_log(
        self,
        user_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get audit log entries.
        
        Args:
            user_id: Filter by user ID
            event_type: Filter by event type
            limit: Maximum number of entries
            
        Returns:
            List of audit log entries
        """
        if not self.enabled:
            return []
        
        filtered_log = self.audit_log
        
        if user_id:
            filtered_log = [e for e in filtered_log if e["user_id"] == user_id]
        
        if event_type:
            filtered_log = [e for e in filtered_log if e["event_type"] == event_type]
        
        # Return most recent entries
        return filtered_log[-limit:]
    
    def get_security_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get security summary for a time window.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Security summary
        """
        if not self.enabled:
            return {"enabled": False}
        
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_events = [
            e for e in self.audit_log
            if datetime.fromisoformat(e["timestamp"]) >= cutoff
        ]
        
        # Count events by type
        event_counts = {}
        for event in recent_events:
            event_type = event["event_type"]
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        return {
            "enabled": True,
            "time_window_hours": hours,
            "total_events": len(recent_events),
            "event_counts": event_counts,
            "unique_users": len(set(e["user_id"] for e in recent_events))
        }


# Global audit logger instance
_global_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """
    Get global audit logger instance (singleton pattern).
    
    Returns:
        AuditLogger instance
    """
    global _global_audit_logger
    if _global_audit_logger is None:
        _global_audit_logger = AuditLogger()
    return _global_audit_logger
