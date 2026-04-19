"""
Agent Collaboration Module
Enables agent-to-agent communication protocols for multi-agent workflows.
"""

import os
import logging
import threading
import queue
import time
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import uuid
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class MessageType:
    """Message types for agent communication."""
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    QUERY = "query"
    ACKNOWLEDGMENT = "acknowledgment"


class AgentMessage:
    """Message between agents."""
    
    def __init__(
        self,
        sender: str,
        recipient: str,
        message_type: str,
        content: Dict[str, Any],
        correlation_id: Optional[str] = None
    ):
        self.message_id = str(uuid.uuid4())
        self.sender = sender
        self.recipient = recipient
        self.message_type = message_type
        self.content = content
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.timestamp = datetime.now()
        self.reply_to = None


class AgentCommunication:
    """
    Manages agent-to-agent communication with real threading.
    
    Handles message passing, routing, and protocol enforcement using
    ThreadPoolExecutor and thread-safe message queues.
    """
    
    def __init__(self):
        """Initialize agent communication system with threading."""
        self.enabled = os.getenv("AGENT_COLLABORATION_ENABLED", "true").lower() == "true"
        
        # Thread-safe message queues for each agent
        self.message_queues = {}
        self.queue_lock = threading.Lock()
        
        # Message handlers
        self.handlers = {}
        self.handlers_lock = threading.Lock()
        
        # Message history for debugging
        self.message_history = []
        self.history_lock = threading.Lock()
        
        # Thread pool for message processing
        self.executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix="AgentComm")
        
        # Event for shutdown
        self.shutdown_event = threading.Event()
        
        # Message processing threads
        self.processing_threads = {}
        
        logger.info(f"Agent communication system initialized with threading (enabled={self.enabled})")
    
    def register_agent(self, agent_id: str):
        """
        Register an agent for communication with thread-safe queue.
        
        Args:
            agent_id: Unique agent identifier
        """
        with self.queue_lock:
            if agent_id not in self.message_queues:
                self.message_queues[agent_id] = queue.Queue()
                # Start a processing thread for this agent
                self._start_agent_processor(agent_id)
                logger.debug(f"Registered agent {agent_id} for communication with thread-safe queue")
    
    def _start_agent_processor(self, agent_id: str):
        """Start a thread to process messages for an agent."""
        def process_messages():
            while not self.shutdown_event.is_set():
                try:
                    msg_queue = self.message_queues[agent_id]
                    message = msg_queue.get(timeout=1.0)  # Wait 1 second for message
                    
                    # Process the message
                    self._process_message(message)
                    msg_queue.task_done()
                    
                except queue.Empty:
                    continue  # Timeout, continue waiting
                except Exception as e:
                    logger.error(f"Error processing message for {agent_id}: {e}")
        
        thread = threading.Thread(target=process_messages, name=f"AgentProcessor-{agent_id}")
        thread.daemon = True
        thread.start()
        self.processing_threads[agent_id] = thread
        logger.debug(f"Started message processor thread for agent {agent_id}")
    
    def register_handler(
        self,
        agent_id: str,
        message_type: str,
        handler: Callable
    ):
        """
        Register a message handler for an agent.
        
        Args:
            agent_id: Agent ID
            message_type: Message type to handle
            handler: Handler function
        """
        key = f"{agent_id}:{message_type}"
        self.handlers[key] = handler
        logger.debug(f"Registered handler for {key}")
    
    def send_message(
        self,
        sender: str,
        recipient: str,
        message_type: str,
        content: Dict[str, Any],
        correlation_id: Optional[str] = None
    ) -> str:
        """
        Send a message from one agent to another using threading.
        
        Args:
            sender: Sender agent ID
            recipient: Recipient agent ID
            message_type: Message type
            content: Message content
            correlation_id: Optional correlation ID for request/response
            
        Returns:
            Message ID
        """
        if not self.enabled:
            return None
        
        message = AgentMessage(
            sender=sender,
            recipient=recipient,
            message_type=message_type,
            content=content,
            correlation_id=correlation_id
        )
        
        # Ensure recipient is registered
        if recipient not in self.message_queues:
            self.register_agent(recipient)
        
        # Add to thread-safe queue
        try:
            self.message_queues[recipient].put(message, timeout=5.0)
            
            # Add to history thread-safely
            with self.history_lock:
                self.message_history.append(message)
            
            logger.debug(f"Message sent from {sender} to {recipient}: {message_type}")
            return message.message_id
            
        except queue.Full:
            logger.error(f"Message queue full for {recipient}, dropping message")
            return None
        except Exception as e:
            logger.error(f"Error sending message from {sender} to {recipient}: {e}")
            return None
    
    def _process_message(self, message: AgentMessage):
        """Process a message in a separate thread."""
        handler_key = f"{message.recipient}:{message.message_type}"
        
        with self.handlers_lock:
            handler = self.handlers.get(handler_key)
        
        if handler:
            try:
                # Execute handler in thread pool
                future = self.executor.submit(handler, message)
                # Don't wait for result to avoid blocking
                logger.debug(f"Submitted message {message.message_id} for processing")
            except Exception as e:
                logger.error(f"Error submitting message for processing: {e}")
        else:
            logger.warning(f"No handler found for {handler_key}")
    
    def receive_messages(self, agent_id: str) -> List[AgentMessage]:
        """
        Receive messages for an agent (non-blocking).
        
        Args:
            agent_id: Agent ID
            
        Returns:
            List of messages
        """
        if not self.enabled:
            return []
        
        messages = []
        if agent_id in self.message_queues:
            try:
                # Get all available messages without blocking
                while True:
                    message = self.message_queues[agent_id].get_nowait()
                    messages.append(message)
            except queue.Empty:
                pass  # No more messages
        
        return messages
    
    def shutdown(self):
        """Shutdown the agent communication system gracefully."""
        logger.info("Shutting down agent communication system...")
        
        # Signal shutdown
        self.shutdown_event.set()
        
        # Wait for processing threads to finish
        for agent_id, thread in self.processing_threads.items():
            thread.join(timeout=2.0)
            if thread.is_alive():
                logger.warning(f"Thread for agent {agent_id} did not shutdown gracefully")
        
        # Shutdown thread pool
        self.executor.shutdown(wait=True, timeout=5.0)
        
        logger.info("Agent communication system shutdown complete")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get communication system statistics."""
        with self.queue_lock:
            queue_sizes = {
                agent_id: queue.qsize() 
                for agent_id, queue in self.message_queues.items()
            }
        
        with self.history_lock:
            total_messages = len(self.message_history)
        
        return {
            "enabled": self.enabled,
            "registered_agents": list(self.message_queues.keys()),
            "queue_sizes": queue_sizes,
            "total_messages": total_messages,
            "active_threads": len([t for t in self.processing_threads.values() if t.is_alive()])
        }
    
    def send_request(
        self,
        sender: str,
        recipient: str,
        content: Dict[str, Any],
        timeout_ms: int = 5000
    ) -> Optional[Dict[str, Any]]:
        """
        Send a request and wait for response (synchronous).
        
        Args:
            sender: Sender agent ID
            recipient: Recipient agent ID
            content: Request content
            timeout_ms: Timeout in milliseconds
            
        Returns:
            Response content or None if timeout
        """
        if not self.enabled:
            return None
        
        correlation_id = str(uuid.uuid4())
        self.send_message(
            sender=sender,
            recipient=recipient,
            message_type=MessageType.REQUEST,
            content=content,
            correlation_id=correlation_id
        )
        
        # Wait for response (simplified synchronous implementation)
        # In production, this would use async/await with proper message passing
        import time
        
        start_time = time.time()
        timeout_seconds = timeout_ms / 1000.0
        
        while time.time() - start_time < timeout_seconds:
            # Check for response message
            messages = self.get_messages(recipient)
            for message in messages:
                if (message.message_type == MessageType.RESPONSE and 
                    message.correlation_id == correlation_id and
                    message.reply_to == correlation_id):
                    return message.content
            
            # Small delay to prevent busy waiting
            time.sleep(0.01)
        
        # Timeout reached
        logger.warning(f"Request timeout from {sender} to {recipient} (correlation_id: {correlation_id})")
        return None
    
    def broadcast(
        self,
        sender: str,
        recipients: List[str],
        message_type: str,
        content: Dict[str, Any]
    ) -> List[str]:
        """
        Broadcast a message to multiple recipients.
        
        Args:
            sender: Sender agent ID
            recipients: List of recipient agent IDs
            message_type: Message type
            content: Message content
            
        Returns:
            List of message IDs
        """
        if not self.enabled:
            return []
        
        message_ids = []
        for recipient in recipients:
            message_id = self.send_message(
                sender=sender,
                recipient=recipient,
                message_type=message_type,
                content=content
            )
            message_ids.append(message_id)
        
        return message_ids
    
    def get_message_history(
        self,
        agent_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get message history.
        
        Args:
            agent_id: Optional agent ID filter
            limit: Maximum number of messages to return
            
        Returns:
            List of message history entries
        """
        if not self.enabled:
            return []
        
        history = self.message_history
        
        if agent_id:
            history = [
                m for m in history
                if m.sender == agent_id or m.recipient == agent_id
            ]
        
        # Return most recent messages
        history = history[-limit:]
        
        return [
            {
                "message_id": m.message_id,
                "sender": m.sender,
                "recipient": m.recipient,
                "message_type": m.message_type,
                "timestamp": m.timestamp.isoformat(),
                "correlation_id": m.correlation_id
            }
            for m in history
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get communication statistics.
        
        Returns:
            Dictionary with communication statistics
        """
        if not self.enabled:
            return {"enabled": False}
        
        return {
            "enabled": True,
            "registered_agents": len(self.message_queues),
            "total_messages": len(self.message_history),
            "message_queues": {
                agent_id: len(queue)
                for agent_id, queue in self.message_queues.items()
            }
        }


# Global agent communication instance
_global_communication: Optional[AgentCommunication] = None


def get_agent_communication() -> AgentCommunication:
    """
    Get global agent communication instance (singleton pattern).
    
    Returns:
        AgentCommunication instance
    """
    global _global_communication
    if _global_communication is None:
        _global_communication = AgentCommunication()
    return _global_communication
