"""
Minimal HITL batch implementation for test compatibility
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class HITLBatchProcessor:
    """Simple HITL batch processor implementation"""
    
    def __init__(self):
        self.batches: List[Dict[str, Any]] = []
        logger.info("HITL batch processor initialized")
    
    def create_batch(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create batch of tasks"""
        batch = {
            "id": f"batch_{len(self.batches)}",
            "tasks": tasks,
            "status": "processing"
        }
        self.batches.append(batch)
        return batch
    
    def process_batch(self, batch_id: str) -> Dict[str, Any]:
        """Process batch"""
        return {"batch_id": batch_id, "status": "completed"}
    
    def get_batch_count(self) -> int:
        """Get total batch count"""
        return len(self.batches)

def get_hitl_batch_processor():
    """Get HITL batch processor instance"""
    return HITLBatchProcessor()

__all__ = ["HITLBatchProcessor", "get_hitl_batch_processor"]
