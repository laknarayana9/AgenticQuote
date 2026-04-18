"""
Event Streaming Module
Handles event streaming with Kafka for real-time data processing
"""

import json
import asyncio
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Event types for streaming"""
    CASE_CREATED = "case.created"
    CASE_UPDATED = "case.updated"
    CASE_APPROVED = "case.approved"
    CASE_REJECTED = "case.rejected"
    AGENT_STARTED = "agent.started"
    AGENT_COMPLETED = "agent.completed"
    AGENT_FAILED = "agent.failed"
    HITL_ASSIGNED = "hitl.assigned"
    HITL_COMPLETED = "hitl.completed"
    WEBHOOK_TRIGGERED = "webhook.triggered"
    METRICS_UPDATED = "metrics.updated"


@dataclass
class Event:
    """Event data structure"""
    event_type: str
    data: Dict[str, Any]
    event_id: str = field(default="")
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = "agenticquote"
    version: str = "1.0"
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class EventProducer:
    """Event producer for publishing events to Kafka"""
    
    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        self.bootstrap_servers = bootstrap_servers
        self.producer = None
        self._initialize_producer()
    
    def _initialize_producer(self):
        """Initialize Kafka producer"""
        try:
            from aiokafka import AIOKafkaProducer
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None
            )
            logger.info(f"Kafka producer initialized for {self.bootstrap_servers}")
        except ImportError:
            logger.warning("aiokafka not installed, using mock producer")
            self.producer = MockKafkaProducer()
    
    async def start(self):
        """Start the producer"""
        if hasattr(self.producer, 'start'):
            await self.producer.start()
    
    async def stop(self):
        """Stop the producer"""
        if hasattr(self.producer, 'stop'):
            await self.producer.stop()
    
    async def publish_event(
        self,
        topic: str,
        event: Event,
        key: Optional[str] = None
    ) -> bool:
        """Publish an event to a Kafka topic"""
        try:
            event_data = {
                "event_type": event.event_type,
                "event_id": event.event_id,
                "timestamp": event.timestamp.isoformat(),
                "source": event.source,
                "version": event.version,
                "correlation_id": event.correlation_id,
                "metadata": event.metadata,
                "data": event.data
            }
            
            if hasattr(self.producer, 'send_and_wait'):
                await self.producer.send_and_wait(
                    topic,
                    value=event_data,
                    key=key
                )
            else:
                await self.producer.send(topic, value=event_data, key=key)
            
            logger.info(f"Published event {event.event_type} to topic {topic}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            return False


class EventConsumer:
    """Event consumer for consuming events from Kafka"""
    
    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        group_id: str = "agenticquote-group"
    ):
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.consumer = None
        self.subscriptions: Dict[str, List[Callable]] = {}
        self._initialize_consumer()
    
    def _initialize_consumer(self):
        """Initialize Kafka consumer"""
        try:
            from aiokafka import AIOKafkaConsumer
            self.consumer = AIOKafkaConsumer(
                bootstrap_servers=self.bootstrap_servers,
                group_id=self.group_id,
                value_deserializer=lambda v: json.loads(v.decode('utf-8')),
                auto_offset_reset='latest'
            )
            logger.info(f"Kafka consumer initialized for {self.bootstrap_servers}")
        except ImportError:
            logger.warning("aiokafka not installed, using mock consumer")
            self.consumer = MockKafkaConsumer()
    
    async def start(self):
        """Start the consumer"""
        if hasattr(self.consumer, 'start'):
            await self.consumer.start()
    
    async def stop(self):
        """Stop the consumer"""
        if hasattr(self.consumer, 'stop'):
            await self.consumer.stop()
    
    def subscribe(self, topic: str, handler: Callable):
        """Subscribe to a topic with a handler"""
        if topic not in self.subscriptions:
            self.subscriptions[topic] = []
        self.subscriptions[topic].append(handler)
        logger.info(f"Subscribed to topic {topic}")
    
    async def consume(self, topics: List[str]):
        """Consume events from subscribed topics"""
        if hasattr(self.consumer, 'subscribe'):
            self.consumer.subscribe(topics)
        
        try:
            async for message in self.consumer:
                topic = message.topic
                event_data = message.value
                
                event = Event(
                    event_type=event_data.get("event_type"),
                    data=event_data.get("data", {}),
                    event_id=event_data.get("event_id"),
                    timestamp=datetime.fromisoformat(event_data.get("timestamp")),
                    source=event_data.get("source"),
                    version=event_data.get("version"),
                    correlation_id=event_data.get("correlation_id"),
                    metadata=event_data.get("metadata", {})
                )
                
                # Call handlers for this topic
                handlers = self.subscriptions.get(topic, [])
                for handler in handlers:
                    try:
                        await handler(event)
                    except Exception as e:
                        logger.error(f"Handler error for topic {topic}: {e}")
        except Exception as e:
            logger.error(f"Consumer error: {e}")


class EventStreamManager:
    """Manages event producers and consumers"""
    
    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        self.bootstrap_servers = bootstrap_servers
        self.producers: Dict[str, EventProducer] = {}
        self.consumers: Dict[str, EventConsumer] = {}
    
    def get_producer(self, name: str = "default") -> EventProducer:
        """Get or create an event producer"""
        if name not in self.producers:
            self.producers[name] = EventProducer(self.bootstrap_servers)
        return self.producers[name]
    
    def get_consumer(
        self,
        name: str = "default",
        group_id: Optional[str] = None
    ) -> EventConsumer:
        """Get or create an event consumer"""
        if name not in self.consumers:
            group_id = group_id or f"{name}-group"
            self.consumers[name] = EventConsumer(
                self.bootstrap_servers,
                group_id
            )
        return self.consumers[name]
    
    async def start_all(self):
        """Start all producers and consumers"""
        for producer in self.producers.values():
            await producer.start()
        
        for consumer in self.consumers.values():
            await consumer.start()
    
    async def stop_all(self):
        """Stop all producers and consumers"""
        for producer in self.producers.values():
            await producer.stop()
        
        for consumer in self.consumers.values():
            await consumer.stop()


class MockKafkaProducer:
    """Mock Kafka producer for testing without Kafka"""
    
    def __init__(self):
        self.messages = []
    
    async def start(self):
        pass
    
    async def stop(self):
        pass
    
    async def send(self, topic, value, key=None):
        self.messages.append({"topic": topic, "value": value, "key": key})
    
    async def send_and_wait(self, topic, value, key=None):
        await self.send(topic, value, key)


class MockKafkaConsumer:
    """Mock Kafka consumer for testing without Kafka"""
    
    def __init__(self):
        self.subscribed_topics = []
    
    async def start(self):
        pass
    
    async def stop(self):
        pass
    
    def subscribe(self, topics):
        self.subscribed_topics = topics
    
    def __aiter__(self):
        return self
    
    async def __anext__(self):
        await asyncio.sleep(1)
        raise StopAsyncIteration


# Global event stream manager
event_manager = EventStreamManager()


def create_event(
    event_type: str,
    data: Dict[str, Any],
    correlation_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Event:
    """Create a new event"""
    import uuid
    return Event(
        event_type=event_type,
        data=data,
        event_id=str(uuid.uuid4()),
        correlation_id=correlation_id,
        metadata=metadata or {}
    )


async def publish_event(
    topic: str,
    event_type: str,
    data: Dict[str, Any],
    correlation_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    key: Optional[str] = None
) -> bool:
    """Convenience function to publish an event"""
    event = create_event(event_type, data, correlation_id, metadata)
    producer = event_manager.get_producer()
    return await producer.publish_event(topic, event, key)
