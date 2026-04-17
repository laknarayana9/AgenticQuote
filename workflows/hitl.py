"""
HITL Workflow Orchestration
Human-in-the-loop workflow with actions and task management.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class HITLActionType(Enum):
    """HITL action types."""
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_INFO = "request_info"
    REFER = "refer"
    ESCALATE = "escalate"


class HITLTaskStatus(Enum):
    """HITL task statuses."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class HITLWorkflow:
    """
    Human-in-the-loop workflow orchestration.
    
    Manages HITL task creation, assignment, actions, and state management.
    """
    
    def __init__(self, db=None):
        """
        Initialize HITL workflow.
        
        Args:
            db: Database instance for HITL task persistence
        """
        self.db = db
        self.sla_hours = int(os.getenv("HITL_SLA_HOURS", "24"))
        self.notification_enabled = os.getenv("HITL_NOTIFICATIONS_ENABLED", "false").lower() == "true"
        
        logger.info(f"HITL workflow initialized with SLA={self.sla_hours}h")
    
    def create_hitl_task(
        self,
        run_id: str,
        task_type: str,
        description: str,
        priority: str = "medium",
        assignee: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new HITL task.
        
        Args:
            run_id: Workflow run ID
            task_type: Type of task (verification, review, approval)
            description: Task description
            priority: Task priority (low, medium, high, urgent)
            assignee: Assigned user (optional)
            metadata: Additional metadata
            
        Returns:
            Dict containing task information
        """
        task_id = str(uuid.uuid4())
        due_date = datetime.now() + timedelta(hours=self.sla_hours)
        
        task = {
            "task_id": task_id,
            "run_id": run_id,
            "task_type": task_type,
            "description": description,
            "status": HITLTaskStatus.PENDING.value,
            "priority": priority,
            "assignee": assignee,
            "created_at": datetime.now().isoformat(),
            "due_date": due_date.isoformat(),
            "completed_at": None,
            "actions": [],
            "metadata": metadata or {}
        }
        
        # Save to database if available
        if self.db:
            try:
                self.db.save_hitl_task(task)
            except Exception as e:
                logger.error(f"Failed to save HITL task to database: {e}")
        else:
            logger.debug(f"HITL task created (not saved to database): {task_id}")
        
        # Send notification if enabled
        if self.notification_enabled and assignee:
            self._send_notification(task_id, assignee, "created")
        
        logger.info(f"Created HITL task {task_id} for run {run_id}")
        return task
    
    def get_hitl_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get HITL task by ID.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task dict or None if not found
        """
        if self.db:
            try:
                return self.db.get_hitl_task(task_id)
            except Exception as e:
                logger.error(f"Failed to get HITL task: {e}")
                return None
        return None
    
    def update_hitl_task_status(
        self,
        task_id: str,
        status: str,
        assignee: Optional[str] = None
    ) -> bool:
        """
        Update HITL task status.
        
        Args:
            task_id: Task ID
            status: New status
            assignee: New assignee (optional)
            
        Returns:
            True if successful, False otherwise
        """
        if self.db:
            try:
                self.db.update_hitl_task(task_id, {"status": status})
                if assignee:
                    self.db.update_hitl_task(task_id, {"assignee": assignee})
                
                # Send notification on status change
                if status == HITLTaskStatus.IN_PROGRESS.value and assignee:
                    self._send_notification(task_id, assignee, "assigned")
                elif status == HITLTaskStatus.COMPLETED.value:
                    self._send_notification(task_id, assignee, "completed")
                
                return True
            except Exception as e:
                logger.error(f"Failed to update HITL task status: {e}")
                return False
        return False
    
    def execute_action(
        self,
        task_id: str,
        action: str,
        user: str,
        notes: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute an action on a HITL task.
        
        Args:
            task_id: Task ID
            action: Action type (approve, reject, request_info, refer, escalate)
            user: User performing the action
            notes: Action notes
            metadata: Additional metadata
            
        Returns:
            Dict containing action result
        """
        task = self.get_hitl_task(task_id)
        if not task:
            return {
                "success": False,
                "error": "Task not found"
            }
        
        # Validate action
        if action not in [a.value for a in HITLActionType]:
            return {
                "success": False,
                "error": f"Invalid action: {action}"
            }
        
        # Record action
        action_record = {
            "action": action,
            "user": user,
            "timestamp": datetime.now().isoformat(),
            "notes": notes,
            "metadata": metadata or {}
        }
        
        # Update task
        task["actions"].append(action_record)
        
        # Update status based on action
        if action == HITLActionType.APPROVE.value:
            task["status"] = HITLTaskStatus.COMPLETED.value
            task["completed_at"] = datetime.now().isoformat()
        elif action == HITLActionType.REJECT.value:
            task["status"] = HITLTaskStatus.COMPLETED.value
            task["completed_at"] = datetime.now().isoformat()
        elif action == HITLActionType.REQUEST_INFO.value:
            task["status"] = HITLTaskStatus.PENDING.value
        elif action == HITLActionType.REFER.value:
            task["status"] = HITLTaskStatus.COMPLETED.value
            task["completed_at"] = datetime.now().isoformat()
        elif action == HITLActionType.ESCALATE.value:
            task["priority"] = "urgent"
            task["status"] = HITLTaskStatus.PENDING.value
        
        # Save to database
        if self.db:
            try:
                self.db.update_hitl_task(task_id, {
                    "actions": task["actions"],
                    "status": task["status"],
                    "completed_at": task.get("completed_at"),
                    "priority": task.get("priority")
                })
            except Exception as e:
                logger.error(f"Failed to save HITL task action: {e}")
        
        logger.info(f"Executed action {action} on task {task_id} by user {user}")
        
        return {
            "success": True,
            "task_id": task_id,
            "action": action,
            "new_status": task["status"],
            "timestamp": action_record["timestamp"]
        }
    
    def get_tasks_for_run(self, run_id: str) -> List[Dict[str, Any]]:
        """
        Get all HITL tasks for a workflow run.
        
        Args:
            run_id: Workflow run ID
            
        Returns:
            List of HITL tasks
        """
        if self.db:
            try:
                return self.db.get_all_hitl_tasks()
            except Exception as e:
                logger.error(f"Failed to get HITL tasks for run: {e}")
                return []
        return []
    
    def check_sla_compliance(self) -> List[Dict[str, Any]]:
        """
        Check for SLA violations and return expired tasks.
        
        Returns:
            List of expired tasks
        """
        expired_tasks = []
        
        if self.db:
            try:
                all_tasks = self.db.get_all_hitl_tasks()
                now = datetime.now()
                
                for task in all_tasks:
                    if task["status"] == HITLTaskStatus.PENDING.value:
                        due_date = datetime.fromisoformat(task["due_date"])
                        if now > due_date:
                            task["status"] = HITLTaskStatus.EXPIRED.value
                            self.db.update_hitl_task(task["task_id"], {"status": HITLTaskStatus.EXPIRED.value})
                            expired_tasks.append(task)
                            
                            # Send notification for expired task
                            if self.notification_enabled:
                                self._send_notification(task["task_id"], task.get("assignee"), "expired")
            except Exception as e:
                logger.error(f"Failed to check SLA compliance: {e}")
        
        if expired_tasks:
            logger.warning(f"Found {len(expired_tasks)} expired HITL tasks")
        
        return expired_tasks
    
    def get_audit_trail(self, task_id: str) -> Dict[str, Any]:
        """
        Get audit trail for a HITL task.
        
        Args:
            task_id: Task ID
            
        Returns:
            Dict containing audit trail
        """
        task = self.get_hitl_task(task_id)
        if not task:
            return {
                "success": False,
                "error": "Task not found"
            }
        
        return {
            "success": True,
            "task_id": task_id,
            "created_at": task.get("created_at"),
            "created_by": task.get("metadata", {}).get("created_by"),
            "actions": task.get("actions", []),
            "status_history": self._build_status_history(task)
        }
    
    def _build_status_history(self, task: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build status history from task actions."""
        history = []
        
        # Initial status
        history.append({
            "status": HITLTaskStatus.PENDING.value,
            "timestamp": task.get("created_at"),
            "user": "system"
        })
        
        # Status changes from actions
        for action in task.get("actions", []):
            if action["action"] in [HITLActionType.APPROVE.value, HITLActionType.REJECT.value]:
                history.append({
                    "status": HITLTaskStatus.COMPLETED.value,
                    "timestamp": action["timestamp"],
                    "user": action["user"]
                })
        
        return history
    
    def _send_notification(self, task_id: str, assignee: str, event_type: str):
        """
        Send notification for HITL task event.
        
        Args:
            task_id: Task ID
            assignee: Assignee user
            event_type: Event type (created, assigned, completed, expired)
        """
        # Placeholder for notification system
        # In production, integrate with email, Slack, or other notification systems
        logger.info(f"Notification: {event_type} for task {task_id} to {assignee}")
        
        # TODO: Implement actual notification system
        # - Email notification
        # - Slack webhook
        # - In-app notification
        pass


# Global HITL workflow instance
_global_hitl_workflow: Optional[HITLWorkflow] = None


def get_hitl_workflow(db=None) -> HITLWorkflow:
    """
    Get global HITL workflow instance (singleton pattern).
    
    Args:
        db: Database instance (only used on first call)
        
    Returns:
        HITLWorkflow instance
    """
    global _global_hitl_workflow
    if _global_hitl_workflow is None:
        _global_hitl_workflow = HITLWorkflow(db)
    return _global_hitl_workflow
