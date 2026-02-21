"""
Message queue implementation for asynchronous quote processing.
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


class QueueStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MessagePriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class QueueMessage:
    """Message in the processing queue."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: MessagePriority = MessagePriority.NORMAL
    status: QueueStatus = QueueStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: int = 300  # 5 minutes default timeout


class MessageQueue:
    """In-memory message queue with priority processing."""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._queue: List[QueueMessage] = []
        self._processing: Dict[str, QueueMessage] = {}
        self._completed: Dict[str, QueueMessage] = {}
        self._lock = asyncio.Lock()
        
    async def enqueue(self, payload: Dict[str, Any], priority: MessagePriority = MessagePriority.NORMAL) -> str:
        """Add a message to the queue."""
        async with self._lock:
            if len(self._queue) >= self.max_size:
                raise ValueError("Queue is full")
            
            message = QueueMessage(payload=payload, priority=priority)
            self._queue.append(message)
            # Sort by priority (higher first) and creation time (older first)
            self._queue.sort(key=lambda m: (-m.priority.value, m.created_at))
            
            logger.info(f"Message {message.id} enqueued with priority {priority.name}")
            return message.id
    
    async def dequeue(self) -> Optional[QueueMessage]:
        """Get the next message from the queue."""
        async with self._lock:
            if not self._queue:
                return None
            
            message = self._queue.pop(0)
            message.status = QueueStatus.PROCESSING
            message.started_at = datetime.now()
            self._processing[message.id] = message
            
            logger.info(f"Message {message.id} dequeued for processing")
            return message
    
    async def complete(self, message_id: str, result: Optional[Dict[str, Any]] = None) -> bool:
        """Mark a message as completed."""
        async with self._lock:
            if message_id not in self._processing:
                return False
            
            message = self._processing.pop(message_id)
            message.status = QueueStatus.COMPLETED
            message.completed_at = datetime.now()
            
            # Store result in payload
            if result:
                message.payload.update(result)
            
            self._completed[message_id] = message
            
            logger.info(f"Message {message_id} completed successfully")
            return True
    
    async def fail(self, message_id: str, error_message: str) -> bool:
        """Mark a message as failed or retry if retries available."""
        async with self._lock:
            if message_id not in self._processing:
                return False
            
            message = self._processing.pop(message_id)
            message.error_message = error_message
            message.retry_count += 1
            
            if message.retry_count < message.max_retries:
                # Retry the message
                message.status = QueueStatus.PENDING
                message.started_at = None
                self._queue.append(message)
                self._queue.sort(key=lambda m: (-m.priority.value, m.created_at))
                
                logger.warning(f"Message {message_id} failed, retrying ({message.retry_count}/{message.max_retries}): {error_message}")
            else:
                # Max retries reached, mark as failed
                message.status = QueueStatus.FAILED
                message.completed_at = datetime.now()
                self._completed[message_id] = message
                
                logger.error(f"Message {message_id} failed permanently after {message.max_retries} retries: {error_message}")
            
            return True
    
    async def get_status(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a message."""
        async with self._lock:
            # Check in queue
            for msg in self._queue:
                if msg.id == message_id:
                    return self._message_to_dict(msg)
            
            # Check in processing
            if message_id in self._processing:
                return self._message_to_dict(self._processing[message_id])
            
            # Check in completed
            if message_id in self._completed:
                return self._message_to_dict(self._completed[message_id])
            
            return None
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        async with self._lock:
            return {
                "pending_count": len(self._queue),
                "processing_count": len(self._processing),
                "completed_count": len(self._completed),
                "max_size": self.max_size,
                "oldest_pending": self._queue[0].created_at.isoformat() if self._queue else None,
                "longest_processing": max(
                    (datetime.now() - msg.started_at).total_seconds()
                    for msg in self._processing.values()
                ) if self._processing else 0
            }
    
    async def cleanup_old_messages(self, older_than_hours: int = 24) -> int:
        """Clean up old completed messages."""
        async with self._lock:
            cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
            old_messages = [
                msg_id for msg_id, msg in self._completed.items()
                if msg.completed_at and msg.completed_at < cutoff_time
            ]
            
            for msg_id in old_messages:
                del self._completed[msg_id]
            
            logger.info(f"Cleaned up {len(old_messages)} old completed messages")
            return len(old_messages)
    
    def _message_to_dict(self, message: QueueMessage) -> Dict[str, Any]:
        """Convert message to dictionary for API responses."""
        return {
            "id": message.id,
            "status": message.status.value,
            "priority": message.priority.name,
            "created_at": message.created_at.isoformat(),
            "started_at": message.started_at.isoformat() if message.started_at else None,
            "completed_at": message.completed_at.isoformat() if message.completed_at else None,
            "error_message": message.error_message,
            "retry_count": message.retry_count,
            "max_retries": message.max_retries,
            "payload": message.payload
        }


# Global queue instance
message_queue = MessageQueue()


async def process_quote_async(message_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulate asynchronous quote processing.
    In a real system, this would call the actual underwriting workflow.
    """
    try:
        # Simulate processing time
        await asyncio.sleep(2)
        
        # Extract submission data
        submission = payload.get("submission", {})
        coverage = submission.get("coverage_amount", 0)
        
        # Mock decision logic
        if coverage > 500000:
            decision = "REFER"
            reason = "Coverage amount exceeds maximum limit - requires human review"
            requires_human_review = True
        elif coverage < 100000:
            decision = "REFER"
            reason = "Coverage amount below minimum threshold - requires human review"
            requires_human_review = True
        else:
            decision = "ACCEPT"
            reason = "Standard risk profile"
            requires_human_review = False
        
        # Mock premium calculation
        premium = coverage * 0.002
        
        result = {
            "run_id": str(uuid.uuid4()),
            "status": "completed",
            "decision": {
                "decision": decision,
                "confidence": 0.85,
                "reason": reason
            },
            "premium": {
                "annual_premium": premium,
                "monthly_premium": premium / 12,
                "coverage_amount": coverage
            },
            "requires_human_review": requires_human_review,
            "processing_time_ms": 2000,
            "message": f"Quote processing completed - {decision}"
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing quote {message_id}: {str(e)}")
        raise
