"""
HITL Queue Management
Manages HITL task queues with priority-based processing.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import heapq

logger = logging.getLogger(__name__)


class Priority(Enum):
    """Task priority levels."""
    URGENT = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


class QueuedTask:
    """Task in queue with priority."""
    
    def __init__(
        self,
        task_id: str,
        priority: Priority,
        task_data: Dict[str, Any],
        created_at: datetime
    ):
        self.task_id = task_id
        self.priority = priority
        self.task_data = task_data
        self.created_at = created_at
        self.assigned_to = None
        self.assigned_at = None
    
    def __lt__(self, other):
        """Compare tasks for priority queue (lower priority value = higher priority)."""
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        # If same priority, use creation time (older tasks first)
        return self.created_at < other.created_at


class HITLQueueManager:
    """
    HITL queue manager with priority-based processing.
    
    Manages task queues with priority levels and automatic routing.
    """
    
    def __init__(self):
        """Initialize HITL queue manager."""
        self.enabled = os.getenv("HITL_QUEUE_MANAGEMENT", "false").lower() == "true"
        
        # Priority queues
        self.queues = {
            Priority.URGENT: [],
            Priority.HIGH: [],
            Priority.MEDIUM: [],
            Priority.LOW: []
        }
        
        # Task lookup
        self.task_lookup = {}
        
        # Queue statistics
        self.stats = {
            "total_queued": 0,
            "total_assigned": 0,
            "total_completed": 0
        }
        
        logger.info(f"HITL queue manager initialized (enabled={self.enabled})")
    
    def enqueue(
        self,
        task_id: str,
        task_data: Dict[str, Any],
        priority: str = "medium"
    ) -> Dict[str, Any]:
        """
        Add a task to the queue.
        
        Args:
            task_id: Task ID
            task_data: Task data
            priority: Priority level (urgent, high, medium, low)
            
        Returns:
            Enqueue result
        """
        if not self.enabled:
            return {
                "queue_enabled": False,
                "enqueued": False,
                "reason": "Queue management disabled"
            }
        
        # Convert priority string to enum
        try:
            priority_enum = Priority[priority.upper()]
        except KeyError:
            priority_enum = Priority.MEDIUM
        
        # Create queued task
        queued_task = QueuedTask(
            task_id=task_id,
            priority=priority_enum,
            task_data=task_data,
            created_at=datetime.now()
        )
        
        # Add to queue
        heapq.heappush(self.queues[priority_enum], queued_task)
        self.task_lookup[task_id] = queued_task
        self.stats["total_queued"] += 1
        
        return {
            "queue_enabled": True,
            "enqueued": True,
            "task_id": task_id,
            "priority": priority_enum.value,
            "queue_position": len(self.queues[priority_enum]),
            "reason": "Task enqueued successfully"
        }
    
    def dequeue(
        self,
        reviewer_id: str,
        max_tasks: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Dequeue tasks for a reviewer (highest priority first).
        
        Args:
            reviewer_id: Reviewer ID
            max_tasks: Maximum number of tasks to dequeue
            
        Returns:
            List of dequeued tasks
        """
        if not self.enabled:
            return []
        
        dequeued_tasks = []
        
        # Dequeue from highest priority queues first
        for priority in [Priority.URGENT, Priority.HIGH, Priority.MEDIUM, Priority.LOW]:
            while len(dequeued_tasks) < max_tasks and self.queues[priority]:
                task = heapq.heappop(self.queues[priority])
                task.assigned_to = reviewer_id
                task.assigned_at = datetime.now()
                self.stats["total_assigned"] += 1
                
                dequeued_tasks.append({
                    "task_id": task.task_id,
                    "priority": task.priority.value,
                    "task_data": task.task_data,
                    "created_at": task.created_at.isoformat(),
                    "assigned_at": task.assigned_at.isoformat()
                })
        
        return dequeued_tasks
    
    def complete_task(self, task_id: str):
        """
        Mark a task as completed and remove from lookup.
        
        Args:
            task_id: Task ID
        """
        if task_id in self.task_lookup:
            del self.task_lookup[task_id]
            self.stats["total_completed"] += 1
            logger.debug(f"Task {task_id} completed")
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """
        Get queue statistics.
        
        Returns:
            Dictionary with queue statistics
        """
        if not self.enabled:
            return {"enabled": False}
        
        return {
            "enabled": True,
            "total_queued": self.stats["total_queued"],
            "total_assigned": self.stats["total_assigned"],
            "total_completed": self.stats["total_completed"],
            "queue_sizes": {
                priority.value: len(queue)
                for priority, queue in self.queues.items()
            },
            "pending_tasks": len(self.task_lookup)
        }
    
    def get_task_position(self, task_id: str) -> Optional[int]:
        """
        Get position of a task in its queue.
        
        Args:
            task_id: Task ID
            
        Returns:
            Queue position or None if not found
        """
        if task_id not in self.task_lookup:
            return None
        
        task = self.task_lookup[task_id]
        queue = self.queues[task.priority]
        
        # Find position (inefficient but works for demo)
        for i, t in enumerate(queue):
            if t.task_id == task_id:
                return i + 1
        
        return None
    
    def reassign_task(self, task_id: str, new_reviewer_id: str):
        """
        Reassign a task to a different reviewer.
        
        Args:
            task_id: Task ID
            new_reviewer_id: New reviewer ID
        """
        if task_id in self.task_lookup:
            task = self.task_lookup[task_id]
            task.assigned_to = new_reviewer_id
            task.assigned_at = datetime.now()
            logger.debug(f"Task {task_id} reassigned to {new_reviewer_id}")
    
    def get_tasks_by_reviewer(self, reviewer_id: str) -> List[Dict[str, Any]]:
        """
        Get all tasks assigned to a reviewer.
        
        Args:
            reviewer_id: Reviewer ID
            
        Returns:
            List of assigned tasks
        """
        if not self.enabled:
            return []
        
        assigned_tasks = []
        for task in self.task_lookup.values():
            if task.assigned_to == reviewer_id:
                assigned_tasks.append({
                    "task_id": task.task_id,
                    "priority": task.priority.value,
                    "created_at": task.created_at.isoformat(),
                    "assigned_at": task.assigned_at.isoformat()
                })
        
        return assigned_tasks
    
    def update_priority(self, task_id: str, new_priority: str):
        """
        Update task priority (requires re-queuing).
        
        Args:
            task_id: Task ID
            new_priority: New priority level
        """
        if task_id not in self.task_lookup:
            return
        
        task = self.task_lookup[task_id]
        old_priority = task.priority
        
        # Convert new priority
        try:
            new_priority_enum = Priority[new_priority.upper()]
        except KeyError:
            return
        
        # Remove from old queue
        if task in self.queues[old_priority]:
            self.queues[old_priority].remove(task)
            heapq.heapify(self.queues[old_priority])
        
        # Update and add to new queue
        task.priority = new_priority_enum
        heapq.heappush(self.queues[new_priority_enum], task)
        
        logger.debug(f"Task {task_id} priority updated from {old_priority.value} to {new_priority_enum.value}")


# Global HITL queue manager instance
_global_queue_manager: Optional[HITLQueueManager] = None


def get_hitl_queue_manager() -> HITLQueueManager:
    """
    Get global HITL queue manager instance (singleton pattern).
    
    Returns:
        HITLQueueManager instance
    """
    global _global_queue_manager
    if _global_queue_manager is None:
        _global_queue_manager = HITLQueueManager()
    return _global_queue_manager
