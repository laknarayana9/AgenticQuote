"""
Agent Collaboration Module
Enables agent-to-agent communication protocols for multi-agent workflows.
"""

import os
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
import uuid

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
    Manages agent-to-agent communication.
    
    Handles message passing, routing, and protocol enforcement.
    """
    
    def __init__(self):
        """Initialize agent communication system."""
        self.enabled = os.getenv("AGENT_COLLABORATION_ENABLED", "false").lower() == "true"
        
        # Message queues for each agent
        self.message_queues = {}
        
        # Message handlers
        self.handlers = {}
        
        # Message history for debugging
        self.message_history = []
        
        logger.info(f"Agent communication system initialized (enabled={self.enabled})")
    
    def register_agent(self, agent_id: str):
        """
        Register an agent for communication.
        
        Args:
            agent_id: Unique agent identifier
        """
        self.message_queues[agent_id] = []
        logger.debug(f"Registered agent {agent_id} for communication")
    
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
        Send a message from one agent to another.
        
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
        
        # Add to recipient's queue
        if recipient not in self.message_queues:
            self.register_agent(recipient)
        
        self.message_queues[recipient].append(message)
        
        # Add to history
        self.message_history.append(message)
        
        logger.debug(f"Message sent from {sender} to {recipient}: {message_type}")
        return message.message_id
    
    def receive_messages(self, agent_id: str) -> List[AgentMessage]:
        """
        Receive messages for an agent.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            List of messages
        """
        if not self.enabled:
            return []
        
        if agent_id not in self.message_queues:
            return []
        
        messages = self.message_queues[agent_id]
        self.message_queues[agent_id] = []
        return messages
    
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
