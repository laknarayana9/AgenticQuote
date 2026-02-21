"""
Redis-based message queue implementation for production-grade asynchronous processing.
"""

import asyncio
import uuid
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum

try:
    import redis.asyncio as redis
    from redis.asyncio import ConnectionPool
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

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
    """Message in the Redis-based processing queue."""
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

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Redis storage."""
        return {
            "id": self.id,
            "payload": self.payload,
            "priority": self.priority.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "timeout_seconds": self.timeout_seconds
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QueueMessage':
        """Create from dictionary from Redis storage."""
        message = cls(
            id=data["id"],
            payload=data["payload"],
            priority=MessagePriority(data["priority"]),
            status=QueueStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            error_message=data.get("error_message"),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            timeout_seconds=data.get("timeout_seconds", 300)
        )
        
        if data.get("started_at"):
            message.started_at = datetime.fromisoformat(data["started_at"])
        if data.get("completed_at"):
            message.completed_at = datetime.fromisoformat(data["completed_at"])
            
        return message


class RedisMessageQueue:
    """Redis-based message queue with priority processing and persistence."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379", max_size: int = 10000):
        self.redis_url = redis_url
        self.max_size = max_size
        self._pool = None
        self._redis = None
        self._mock_redis = None
        self._use_mock = False
        
        # Redis keys
        self.QUEUE_KEY = "quote_processing_queue"
        self.PROCESSING_KEY = "quote_processing_processing"
        self.COMPLETED_KEY = "quote_processing_completed"
        self.STATS_KEY = "quote_processing_stats"
        
    async def initialize(self):
        """Initialize Redis connection or fall back to mock."""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available, using mock Redis")
            from app.mock_redis import mock_redis
            self._mock_redis = mock_redis
            self._use_mock = True
            logger.info("Mock Redis queue initialized successfully")
            return
        
        try:
            self._pool = ConnectionPool.from_url(self.redis_url, max_connections=20)
            self._redis = redis.Redis(connection_pool=self._pool)
            
            # Test connection
            await self._redis.ping()
            logger.info("Redis message queue initialized successfully")
            
        except Exception as e:
            logger.warning(f"Failed to initialize Redis: {e}, falling back to mock")
            from app.mock_redis import mock_redis
            self._mock_redis = mock_redis
            self._use_mock = True
            logger.info("Mock Redis queue initialized successfully")
    
    async def close(self):
        """Close Redis connections."""
        if self._pool:
            await self._pool.close()
            logger.info("Redis connections closed")
    
    async def enqueue(self, payload: Dict[str, Any], priority: MessagePriority = MessagePriority.NORMAL) -> str:
        """Add a message to the Redis queue with priority."""
        if not self._redis and not self._mock_redis:
            await self.initialize()
        
        try:
            if self._use_mock:
                # Use mock Redis
                queue_size = await self._mock_redis.zcard(self.QUEUE_KEY)
                if queue_size >= self.max_size:
                    raise ValueError(f"Queue is full (max size: {self.max_size})")
                
                message = QueueMessage(payload=payload, priority=priority)
                
                # Add to sorted set with negative priority for high-to-low ordering
                await self._mock_redis.zadd(
                    self.QUEUE_KEY,
                    {json.dumps(message.to_dict()): -message.priority.value}
                )
                
                # Update stats
                await self._mock_redis.hincrby(self.STATS_KEY, "total_enqueued", 1)
                
                logger.info(f"Message {message.id} enqueued with priority {priority.name} (mock)")
                return message.id
            else:
                # Use real Redis
                queue_size = await self._redis.zcard(self.QUEUE_KEY)
                if queue_size >= self.max_size:
                    raise ValueError(f"Queue is full (max size: {self.max_size})")
                
                message = QueueMessage(payload=payload, priority=priority)
                
                # Add to sorted set with negative priority for high-to-low ordering
                await self._redis.zadd(
                    self.QUEUE_KEY,
                    {json.dumps(message.to_dict()): -message.priority.value}
                )
                
                # Update stats
                await self._redis.hincrby(self.STATS_KEY, "total_enqueued", 1)
                
                logger.info(f"Message {message.id} enqueued with priority {priority.name}")
                return message.id
            
        except Exception as e:
            logger.error(f"Failed to enqueue message: {e}")
            raise
    
    async def dequeue(self) -> Optional[QueueMessage]:
        """Get the next message from the queue (highest priority first)."""
        if not self._redis and not self._mock_redis:
            await self.initialize()
        
        try:
            if self._use_mock:
                # Use mock Redis
                result = await self._mock_redis.zpopmin(self.QUEUE_KEY, count=1)
                
                if not result:
                    return None
                
                message_json, _ = result[0]
                message_data = json.loads(message_json)
                message = QueueMessage.from_dict(message_data)
                
                # Update status to processing
                message.status = QueueStatus.PROCESSING
                message.started_at = datetime.now()
                
                # Move to processing set
                await self._mock_redis.hset(
                    self.PROCESSING_KEY,
                    message.id,
                    json.dumps(message.to_dict())
                )
                
                # Update stats
                await self._mock_redis.hincrby(self.STATS_KEY, "total_dequeued", 1)
                await self._mock_redis.hincrby(self.STATS_KEY, "currently_processing", 1)
                
                logger.info(f"Message {message.id} dequeued for processing (mock)")
                return message
            else:
                # Use real Redis
                result = await self._redis.zpopmin(self.QUEUE_KEY, count=1)
                
                if not result:
                    return None
                
                message_json, _ = result[0]
                message_data = json.loads(message_json)
                message = QueueMessage.from_dict(message_data)
                
                # Update status to processing
                message.status = QueueStatus.PROCESSING
                message.started_at = datetime.now()
                
                # Move to processing set with timeout
                await self._redis.hset(
                    self.PROCESSING_KEY,
                    message.id,
                    json.dumps(message.to_dict())
                )
                
                # Set expiration for processing messages (timeout handling)
                await self._redis.expire(self.PROCESSING_KEY, message.timeout_seconds + 60)
                
                # Update stats
                await self._redis.hincrby(self.STATS_KEY, "total_dequeued", 1)
                await self._redis.hincrby(self.STATS_KEY, "currently_processing", 1)
                
                logger.info(f"Message {message.id} dequeued for processing")
                return message
            
        except Exception as e:
            logger.error(f"Failed to dequeue message: {e}")
            raise
    
    async def complete(self, message_id: str, result: Optional[Dict[str, Any]] = None) -> bool:
        """Mark a message as completed."""
        if not self._redis and not self._mock_redis:
            await self.initialize()
        
        try:
            if self._use_mock:
                # Use mock Redis
                # Get message from processing
                message_json = await self._mock_redis.hget(self.PROCESSING_KEY, message_id)
                if not message_json:
                    return False
                
                message_data = json.loads(message_json)
                message = QueueMessage.from_dict(message_data)
                
                # Update completion details
                message.status = QueueStatus.COMPLETED
                message.completed_at = datetime.now()
                
                # Store result in payload
                if result:
                    message.payload.update(result)
                
                # Move to completed set
                await self._mock_redis.hset(
                    self.COMPLETED_KEY,
                    message_id,
                    json.dumps(message.to_dict())
                )
                
                # Remove from processing
                await self._mock_redis.hdel(self.PROCESSING_KEY, message_id)
                
                # Update stats
                await self._mock_redis.hincrby(self.STATS_KEY, "total_completed", 1)
                await self._mock_redis.hincrby(self.STATS_KEY, "currently_processing", -1)
                
                logger.info(f"Message {message_id} completed successfully (mock)")
                return True
            else:
                # Use real Redis
                # Get message from processing
                message_json = await self._redis.hget(self.PROCESSING_KEY, message_id)
                if not message_json:
                    return False
                
                message_data = json.loads(message_json)
                message = QueueMessage.from_dict(message_data)
                
                # Update completion details
                message.status = QueueStatus.COMPLETED
                message.completed_at = datetime.now()
                
                # Store result in payload
                if result:
                    message.payload.update(result)
                
                # Move to completed set
                await self._redis.hset(
                    self.COMPLETED_KEY,
                    message_id,
                    json.dumps(message.to_dict())
                )
                
                # Remove from processing
                await self._redis.hdel(self.PROCESSING_KEY, message_id)
                
                # Set expiration for completed messages (cleanup)
                await self._redis.expire(self.COMPLETED_KEY, 86400)  # 24 hours
                
                # Update stats
                await self._redis.hincrby(self.STATS_KEY, "total_completed", 1)
                await self._redis.hincrby(self.STATS_KEY, "currently_processing", -1)
                
                logger.info(f"Message {message_id} completed successfully")
                return True
            
        except Exception as e:
            logger.error(f"Failed to complete message {message_id}: {e}")
            raise
    
    async def fail(self, message_id: str, error_message: str) -> bool:
        """Mark a message as failed or retry if retries available."""
        if not self._redis and not self._mock_redis:
            await self.initialize()
        
        try:
            if self._use_mock:
                # Use mock Redis
                # Get message from processing
                message_json = await self._mock_redis.hget(self.PROCESSING_KEY, message_id)
                if not message_json:
                    return False
                
                message_data = json.loads(message_json)
                message = QueueMessage.from_dict(message_data)
                
                message.error_message = error_message
                message.retry_count += 1
                
                if message.retry_count < message.max_retries:
                    # Retry the message
                    message.status = QueueStatus.PENDING
                    message.started_at = None
                    
                    # Re-add to queue with same priority
                    await self._mock_redis.zadd(
                        self.QUEUE_KEY,
                        {json.dumps(message.to_dict()): -message.priority.value}
                    )
                    
                    # Remove from processing
                    await self._mock_redis.hdel(self.PROCESSING_KEY, message_id)
                    
                    # Update stats
                    await self._mock_redis.hincrby(self.STATS_KEY, "total_retries", 1)
                    await self._mock_redis.hincrby(self.STATS_KEY, "currently_processing", -1)
                    
                    logger.warning(f"Message {message_id} failed, retrying ({message.retry_count}/{message.max_retries}): {error_message}")
                else:
                    # Max retries reached, mark as failed
                    message.status = QueueStatus.FAILED
                    message.completed_at = datetime.now()
                    
                    # Move to completed set as failed
                    await self._mock_redis.hset(
                        self.COMPLETED_KEY,
                        message_id,
                        json.dumps(message.to_dict())
                    )
                    
                    # Remove from processing
                    await self._mock_redis.hdel(self.PROCESSING_KEY, message_id)
                    
                    # Update stats
                    await self._mock_redis.hincrby(self.STATS_KEY, "total_failed", 1)
                    await self._mock_redis.hincrby(self.STATS_KEY, "currently_processing", -1)
                    
                    logger.error(f"Message {message_id} failed permanently after {message.max_retries} retries: {error_message}")
                
                return True
            else:
                # Use real Redis
                # Get message from processing
                message_json = await self._redis.hget(self.PROCESSING_KEY, message_id)
                if not message_json:
                    return False
                
                message_data = json.loads(message_json)
                message = QueueMessage.from_dict(message_data)
                
                message.error_message = error_message
                message.retry_count += 1
                
                if message.retry_count < message.max_retries:
                    # Retry the message
                    message.status = QueueStatus.PENDING
                    message.started_at = None
                    
                    # Re-add to queue with same priority
                    await self._redis.zadd(
                        self.QUEUE_KEY,
                        {json.dumps(message.to_dict()): -message.priority.value}
                    )
                    
                    # Remove from processing
                    await self._redis.hdel(self.PROCESSING_KEY, message_id)
                    
                    # Update stats
                    await self._redis.hincrby(self.STATS_KEY, "total_retries", 1)
                    await self._redis.hincrby(self.STATS_KEY, "currently_processing", -1)
                    
                    logger.warning(f"Message {message_id} failed, retrying ({message.retry_count}/{message.max_retries}): {error_message}")
                else:
                    # Max retries reached, mark as failed
                    message.status = QueueStatus.FAILED
                    message.completed_at = datetime.now()
                    
                    # Move to completed set as failed
                    await self._redis.hset(
                        self.COMPLETED_KEY,
                        message_id,
                        json.dumps(message.to_dict())
                    )
                    
                    # Remove from processing
                    await self._redis.hdel(self.PROCESSING_KEY, message_id)
                    
                    # Update stats
                    await self._redis.hincrby(self.STATS_KEY, "total_failed", 1)
                    await self._redis.hincrby(self.STATS_KEY, "currently_processing", -1)
                    
                    logger.error(f"Message {message_id} failed permanently after {message.max_retries} retries: {error_message}")
                
                return True
            
        except Exception as e:
            logger.error(f"Failed to mark message {message_id} as failed: {e}")
            raise
    
    async def get_status(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a message from all possible locations."""
        if not self._redis and not self._mock_redis:
            await self.initialize()
        
        try:
            if self._use_mock:
                # Use mock Redis
                # Check in queue
                queue_data = await self._mock_redis.zrange(self.QUEUE_KEY, 0, -1)
                for item in queue_data:
                    message_data = json.loads(item)
                    if message_data["id"] == message_id:
                        return message_data
                
                # Check in processing
                processing_json = await self._mock_redis.hget(self.PROCESSING_KEY, message_id)
                if processing_json:
                    return json.loads(processing_json)
                
                # Check in completed
                completed_json = await self._mock_redis.hget(self.COMPLETED_KEY, message_id)
                if completed_json:
                    return json.loads(completed_json)
                
                return None
            else:
                # Use real Redis
                # Check in queue
                queue_data = await self._redis.zrange(self.QUEUE_KEY, 0, -1)
                for item in queue_data:
                    message_data = json.loads(item)
                    if message_data["id"] == message_id:
                        return message_data
                
                # Check in processing
                processing_json = await self._redis.hget(self.PROCESSING_KEY, message_id)
                if processing_json:
                    return json.loads(processing_json)
                
                # Check in completed
                completed_json = await self._redis.hget(self.COMPLETED_KEY, message_id)
                if completed_json:
                    return json.loads(completed_json)
                
                return None
            
        except Exception as e:
            logger.error(f"Failed to get status for message {message_id}: {e}")
            raise
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get comprehensive queue statistics."""
        if not self._redis and not self._mock_redis:
            await self.initialize()
        
        try:
            if self._use_mock:
                # Use mock Redis
                pending_count = await self._mock_redis.zcard(self.QUEUE_KEY)
                processing_count = await self._mock_redis.hlen(self.PROCESSING_KEY)
                completed_count = await self._mock_redis.hlen(self.COMPLETED_KEY)
                
                # Get stats from hash
                stats = await self._mock_redis.hgetall(self.STATS_KEY)
                
                return {
                    "pending_count": pending_count,
                    "processing_count": processing_count,
                    "completed_count": completed_count,
                    "max_size": self.max_size,
                    "oldest_pending": None,
                    "longest_processing": 0,
                    "total_enqueued": int(stats.get("total_enqueued", 0)),
                    "total_dequeued": int(stats.get("total_dequeued", 0)),
                    "total_completed": int(stats.get("total_completed", 0)),
                    "total_failed": int(stats.get("total_failed", 0)),
                    "total_retries": int(stats.get("total_retries", 0)),
                    "currently_processing": int(stats.get("currently_processing", 0))
                }
            else:
                # Use real Redis
                pending_count = await self._redis.zcard(self.QUEUE_KEY)
                processing_count = await self._redis.hlen(self.PROCESSING_KEY)
                completed_count = await self._redis.hlen(self.COMPLETED_KEY)
                
                # Get stats from hash
                stats = await self._redis.hgetall(self.STATS_KEY)
                
                # Get oldest pending message
                oldest_pending = None
                if pending_count > 0:
                    oldest_data = await self._redis.zrange(self.QUEUE_KEY, 0, 0, withscores=True)
                    if oldest_data:
                        message_data = json.loads(oldest_data[0][0])
                        oldest_pending = message_data["created_at"]
                
                # Get processing times
                longest_processing = 0
                if processing_count > 0:
                    processing_messages = await self._redis.hgetall(self.PROCESSING_KEY)
                    current_time = datetime.now()
                    
                    for msg_json in processing_messages.values():
                        message_data = json.loads(msg_json)
                        if message_data.get("started_at"):
                            started_at = datetime.fromisoformat(message_data["started_at"])
                            processing_time = (current_time - started_at).total_seconds()
                            longest_processing = max(longest_processing, processing_time)
                
                return {
                    "pending_count": pending_count,
                    "processing_count": processing_count,
                    "completed_count": completed_count,
                    "max_size": self.max_size,
                    "oldest_pending": oldest_pending,
                    "longest_processing": longest_processing,
                    "total_enqueued": int(stats.get("total_enqueued", 0)),
                    "total_dequeued": int(stats.get("total_dequeued", 0)),
                    "total_completed": int(stats.get("total_completed", 0)),
                    "total_failed": int(stats.get("total_failed", 0)),
                    "total_retries": int(stats.get("total_retries", 0)),
                    "currently_processing": int(stats.get("currently_processing", 0))
                }
            
        except Exception as e:
            logger.error(f"Failed to get queue stats: {e}")
            raise
    
    async def cleanup_old_messages(self, older_than_hours: int = 24) -> int:
        """Clean up old completed messages."""
        if not self._redis:
            await self.initialize()
        
        try:
            cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
            
            # Get all completed messages
            completed_messages = await self._redis.hgetall(self.COMPLETED_KEY)
            old_message_ids = []
            
            for message_id, message_json in completed_messages.items():
                message_data = json.loads(message_json)
                if message_data.get("completed_at"):
                    completed_at = datetime.fromisoformat(message_data["completed_at"])
                    if completed_at < cutoff_time:
                        old_message_ids.append(message_id)
            
            # Delete old messages
            if old_message_ids:
                await self._redis.hdel(self.COMPLETED_KEY, *old_message_ids)
                logger.info(f"Cleaned up {len(old_message_ids)} old completed messages")
            
            return len(old_message_ids)
            
        except Exception as e:
            logger.error(f"Failed to cleanup old messages: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Redis queue health."""
        try:
            if self._use_mock:
                # Mock Redis is always healthy
                stats = await self.get_queue_stats()
                return {
                    "status": "healthy",
                    "redis_connected": False,
                    "using_mock": True,
                    "queue_stats": stats
                }
            else:
                # Try to use real Redis
                if not self._redis:
                    await self.initialize()
                
                # Test Redis connection
                await self._redis.ping()
                
                # Get basic stats
                stats = await self.get_queue_stats()
                
                return {
                    "status": "healthy",
                    "redis_connected": True,
                    "using_mock": False,
                    "queue_stats": stats
                }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "redis_connected": False,
                "using_mock": False,
                "error": str(e)
            }


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


# Global Redis queue instance
redis_message_queue = RedisMessageQueue()
