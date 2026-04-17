"""
HITL Batch Processing
Enables batch processing of HITL tasks for efficiency.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class BatchStatus(Enum):
    """Batch processing status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIALLY_COMPLETED = "partially_completed"


class BatchOperation:
    """Batch operation configuration."""
    
    def __init__(
        self,
        batch_id: str,
        task_ids: List[str],
        operation: str,
        parameters: Dict[str, Any]
    ):
        self.batch_id = batch_id
        self.task_ids = task_ids
        self.operation = operation
        self.parameters = parameters
        self.status = BatchStatus.PENDING
        self.created_at = datetime.now()
        self.completed_at = None
        self.results = {}
        self.errors = {}


class HITLBatchProcessor:
    """
    HITL batch processing for efficient task management.
    
    Processes multiple HITL tasks in batch for improved efficiency.
    """
    
    def __init__(self):
        """Initialize HITL batch processor."""
        self.enabled = os.getenv("HITL_BATCH_PROCESSING", "false").lower() == "true"
        self.max_batch_size = int(os.getenv("HITL_MAX_BATCH_SIZE", "50"))
        
        # Batch operations
        self.batches = {}
        
        logger.info(f"HITL batch processor initialized (enabled={self.enabled}, max_batch_size={self.max_batch_size})")
    
    def create_batch(
        self,
        task_ids: List[str],
        operation: str,
        parameters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Create a batch operation.
        
        Args:
            task_ids: List of task IDs to batch
            operation: Operation to perform (approve, reject, refer, assign)
            parameters: Operation parameters
            
        Returns:
            Batch creation result
        """
        if not self.enabled:
            return {
                "batch_enabled": False,
                "batch_id": None,
                "reason": "Batch processing disabled"
            }
        
        # Validate batch size
        if len(task_ids) > self.max_batch_size:
            return {
                "batch_enabled": True,
                "batch_id": None,
                "reason": f"Batch size {len(task_ids)} exceeds max {self.max_batch_size}"
            }
        
        # Create batch
        batch_id = f"batch_{datetime.now().timestamp()}"
        batch = BatchOperation(
            batch_id=batch_id,
            task_ids=task_ids,
            operation=operation,
            parameters=parameters or {}
        )
        
        self.batches[batch_id] = batch
        
        return {
            "batch_enabled": True,
            "batch_id": batch_id,
            "task_count": len(task_ids),
            "operation": operation,
            "status": batch.status.value
        }
    
    def process_batch(
        self,
        batch_id: str,
        processor_func: callable
    ) -> Dict[str, Any]:
        """
        Process a batch operation.
        
        Args:
            batch_id: Batch ID
            processor_func: Function to process each task
            
        Returns:
            Batch processing result
        """
        if not self.enabled:
            return {
                "batch_enabled": False,
                "processed": False,
                "reason": "Batch processing disabled"
            }
        
        if batch_id not in self.batches:
            return {
                "batch_enabled": True,
                "processed": False,
                "reason": f"Batch {batch_id} not found"
            }
        
        batch = self.batches[batch_id]
        batch.status = BatchStatus.IN_PROGRESS
        
        # Process each task
        success_count = 0
        for task_id in batch.task_ids:
            try:
                result = processor_func(task_id, batch.operation, batch.parameters)
                batch.results[task_id] = result
                success_count += 1
            except Exception as e:
                batch.errors[task_id] = str(e)
                logger.error(f"Error processing task {task_id} in batch {batch_id}: {e}")
        
        # Update batch status
        if success_count == len(batch.task_ids):
            batch.status = BatchStatus.COMPLETED
        elif success_count > 0:
            batch.status = BatchStatus.PARTIALLY_COMPLETED
        else:
            batch.status = BatchStatus.FAILED
        
        batch.completed_at = datetime.now()
        
        return {
            "batch_enabled": True,
            "processed": True,
            "batch_id": batch_id,
            "status": batch.status.value,
            "total_tasks": len(batch.task_ids),
            "successful": success_count,
            "failed": len(batch.task_ids) - success_count,
            "duration_seconds": (batch.completed_at - batch.created_at).total_seconds()
        }
    
    def batch_approve(
        self,
        task_ids: List[str],
        reviewer_id: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Batch approve multiple tasks.
        
        Args:
            task_ids: List of task IDs to approve
            reviewer_id: Reviewer ID
            notes: Optional notes
            
        Returns:
            Batch approval result
        """
        return self.create_batch(
            task_ids=task_ids,
            operation="approve",
            parameters={
                "reviewer_id": reviewer_id,
                "notes": notes
            }
        )
    
    def batch_assign(
        self,
        task_ids: List[str],
        reviewer_id: str
    ) -> Dict[str, Any]:
        """
        Batch assign multiple tasks to a reviewer.
        
        Args:
            task_ids: List of task IDs to assign
            reviewer_id: Reviewer ID
            
        Returns:
            Batch assignment result
        """
        return self.create_batch(
            task_ids=task_ids,
            operation="assign",
            parameters={
                "reviewer_id": reviewer_id
            }
        )
    
    def batch_refer(
        self,
        task_ids: List[str],
        reason: str
    ) -> Dict[str, Any]:
        """
        Batch refer multiple tasks.
        
        Args:
            task_ids: List of task IDs to refer
            reason: Reason for referral
            
        Returns:
            Batch referral result
        """
        return self.create_batch(
            task_ids=task_ids,
            operation="refer",
            parameters={
                "reason": reason
            }
        )
    
    def get_batch_status(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """
        Get batch status.
        
        Args:
            batch_id: Batch ID
            
        Returns:
            Batch status or None if not found
        """
        if batch_id not in self.batches:
            return None
        
        batch = self.batches[batch_id]
        return {
            "batch_id": batch_id,
            "task_ids": batch.task_ids,
            "operation": batch.operation,
            "status": batch.status.value,
            "created_at": batch.created_at.isoformat(),
            "completed_at": batch.completed_at.isoformat() if batch.completed_at else None,
            "results_count": len(batch.results),
            "errors_count": len(batch.errors)
        }
    
    def get_batch_stats(self) -> Dict[str, Any]:
        """
        Get batch processing statistics.
        
        Returns:
            Dictionary with batch statistics
        """
        if not self.enabled:
            return {"enabled": False}
        
        total_batches = len(self.batches)
        completed = sum(1 for b in self.batches.values() if b.status == BatchStatus.COMPLETED)
        partially_completed = sum(1 for b in self.batches.values() if b.status == BatchStatus.PARTIALLY_COMPLETED)
        failed = sum(1 for b in self.batches.values() if b.status == BatchStatus.FAILED)
        
        return {
            "enabled": True,
            "max_batch_size": self.max_batch_size,
            "total_batches": total_batches,
            "completed": completed,
            "partially_completed": partially_completed,
            "failed": failed,
            "in_progress": total_batches - completed - partially_completed - failed
        }


# Global HITL batch processor instance
_global_batch_processor: Optional[HITLBatchProcessor] = None


def get_hitl_batch_processor() -> HITLBatchProcessor:
    """
    Get global HITL batch processor instance (singleton pattern).
    
    Returns:
        HITLBatchProcessor instance
    """
    global _global_batch_processor
    if _global_batch_processor is None:
        _global_batch_processor = HITLBatchProcessor()
    return _global_batch_processor
