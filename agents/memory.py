"""
Agent Memory Module
Enables agents to remember past decisions and patterns using vector storage.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import hashlib

logger = logging.getLogger(__name__)


class MemoryType:
    """Types of agent memory."""
    DECISION = "decision"
    PATTERN = "pattern"
    FEEDBACK = "feedback"
    CONTEXT = "context"


class AgentMemory:
    """
    Agent memory with vector storage for remembering past decisions and patterns.
    
    Uses a simple in-memory vector store with cosine similarity for retrieval.
    Can be extended to use FAISS, Pinecone, or other vector databases.
    """
    
    def __init__(self, agent_id: str, max_memories: int = 1000):
        """
        Initialize agent memory.
        
        Args:
            agent_id: Unique agent identifier
            max_memories: Maximum number of memories to store
        """
        self.agent_id = agent_id
        self.max_memories = max_memories
        self.enabled = os.getenv("AGENT_MEMORY_ENABLED", "false").lower() == "true"
        
        # In-memory storage (can be replaced with vector database)
        self.memories = []
        self.memory_index = {}  # Simple index for fast lookup
        
        logger.info(f"Agent memory initialized for {agent_id} (enabled={self.enabled})")
    
    def store(
        self,
        memory_type: str,
        content: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
        importance: float = 0.5
    ) -> str:
        """
        Store a memory.
        
        Args:
            memory_type: Type of memory (decision, pattern, feedback, context)
            content: Memory content
            context: Additional context
            importance: Importance score (0-1)
            
        Returns:
            Memory ID
        """
        if not self.enabled:
            return None
        
        memory_id = self._generate_memory_id(content, context)
        
        memory = {
            "memory_id": memory_id,
            "agent_id": self.agent_id,
            "memory_type": memory_type,
            "content": content,
            "context": context or {},
            "importance": importance,
            "created_at": datetime.now().isoformat(),
            "access_count": 0,
            "last_accessed": None
        }
        
        # Store memory
        self.memories.append(memory)
        self.memory_index[memory_id] = memory
        
        # Prune old memories if limit exceeded
        if len(self.memories) > self.max_memories:
            self._prune_memories()
        
        logger.debug(f"Stored memory {memory_id} for agent {self.agent_id}")
        return memory_id
    
    def retrieve(
        self,
        query: Dict[str, Any],
        memory_type: Optional[str] = None,
        limit: int = 5,
        min_importance: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant memories based on query.
        
        Args:
            query: Query content to match against
            memory_type: Optional memory type filter
            limit: Maximum number of memories to return
            min_importance: Minimum importance score
            
        Returns:
            List of relevant memories
        """
        if not self.enabled:
            return []
        
        # Calculate similarity scores
        scored_memories = []
        for memory in self.memories:
            # Filter by memory type
            if memory_type and memory["memory_type"] != memory_type:
                continue
            
            # Filter by importance
            if memory["importance"] < min_importance:
                continue
            
            # Calculate similarity
            similarity = self._calculate_similarity(query, memory["content"])
            
            if similarity > 0:
                scored_memories.append({
                    "memory": memory,
                    "similarity": similarity
                })
        
        # Sort by similarity and importance
        scored_memories.sort(
            key=lambda x: (x["similarity"], x["memory"]["importance"]),
            reverse=True
        )
        
        # Update access counts
        for item in scored_memories[:limit]:
            memory = item["memory"]
            memory["access_count"] += 1
            memory["last_accessed"] = datetime.now().isoformat()
        
        # Return top memories
        return [item["memory"] for item in scored_memories[:limit]]
    
    def retrieve_by_type(self, memory_type: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve memories by type.
        
        Args:
            memory_type: Memory type
            limit: Maximum number of memories to return
            
        Returns:
            List of memories of specified type
        """
        if not self.enabled:
            return []
        
        filtered = [m for m in self.memories if m["memory_type"] == memory_type]
        filtered.sort(key=lambda x: x["importance"], reverse=True)
        return filtered[:limit]
    
    def get_recent_memories(self, hours: int = 24, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent memories.
        
        Args:
            hours: Number of hours to look back
            limit: Maximum number of memories to return
            
        Returns:
            List of recent memories
        """
        if not self.enabled:
            return []
        
        cutoff = datetime.now() - timedelta(hours=hours)
        recent = [
            m for m in self.memories
            if datetime.fromisoformat(m["created_at"]) > cutoff
        ]
        recent.sort(key=lambda x: x["created_at"], reverse=True)
        return recent[:limit]
    
    def update_importance(self, memory_id: str, new_importance: float):
        """
        Update importance score of a memory.
        
        Args:
            memory_id: Memory ID
            new_importance: New importance score
        """
        if memory_id in self.memory_index:
            self.memory_index[memory_id]["importance"] = max(0, min(1, new_importance))
            logger.debug(f"Updated importance for memory {memory_id}")
    
    def delete_memory(self, memory_id: str):
        """
        Delete a memory.
        
        Args:
            memory_id: Memory ID
        """
        if memory_id in self.memory_index:
            self.memories = [m for m in self.memories if m["memory_id"] != memory_id]
            del self.memory_index[memory_id]
            logger.debug(f"Deleted memory {memory_id}")
    
    def clear_all(self):
        """Clear all memories."""
        self.memories = []
        self.memory_index = {}
        logger.info(f"Cleared all memories for agent {self.agent_id}")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get memory statistics.
        
        Returns:
            Dictionary with memory statistics
        """
        if not self.enabled:
            return {"enabled": False}
        
        memory_types = {}
        for memory in self.memories:
            mtype = memory["memory_type"]
            memory_types[mtype] = memory_types.get(mtype, 0) + 1
        
        total_access_count = sum(m["access_count"] for m in self.memories)
        
        return {
            "enabled": True,
            "agent_id": self.agent_id,
            "total_memories": len(self.memories),
            "memory_types": memory_types,
            "total_access_count": total_access_count,
            "avg_importance": sum(m["importance"] for m in self.memories) / len(self.memories) if self.memories else 0,
            "max_memories": self.max_memories
        }
    
    def _generate_memory_id(self, content: Dict[str, Any], context: Dict[str, Any]) -> str:
        """Generate unique memory ID."""
        content_str = json.dumps(content, sort_keys=True)
        context_str = json.dumps(context, sort_keys=True)
        combined = f"{self.agent_id}{content_str}{context_str}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    def _calculate_similarity(self, query: Dict[str, Any], content: Dict[str, Any]) -> float:
        """
        Calculate similarity between query and content.
        
        Simple implementation using key overlap and value similarity.
        Can be enhanced with actual vector embeddings.
        
        Args:
            query: Query content
            content: Memory content
            
        Returns:
            Similarity score (0-1)
        """
        query_keys = set(query.keys())
        content_keys = set(content.keys())
        
        # Key overlap score
        key_overlap = len(query_keys & content_keys) / len(query_keys | content_keys) if query_keys | content_keys else 0
        
        # Value similarity for overlapping keys
        value_similarity = 0
        overlapping_keys = query_keys & content_keys
        if overlapping_keys:
            matches = 0
            for key in overlapping_keys:
                if query[key] == content[key]:
                    matches += 1
            value_similarity = matches / len(overlapping_keys)
        
        # Combined score
        return 0.3 * key_overlap + 0.7 * value_similarity
    
    def _prune_memories(self):
        """Prune old/low-importance memories to stay within limit."""
        # Sort by importance and recency
        self.memories.sort(
            key=lambda x: (x["importance"], x["created_at"]),
            reverse=True
        )
        
        # Keep only top memories
        kept = self.memories[:self.max_memories]
        removed = self.memories[self.max_memories:]
        
        # Update index
        self.memory_index = {m["memory_id"]: m for m in kept}
        self.memories = kept
        
        logger.debug(f"Pruned {len(removed)} memories for agent {self.agent_id}")


class AgentMemoryManager:
    """
    Manages memory for all agents.
    """
    
    def __init__(self):
        """Initialize agent memory manager."""
        self.agent_memories = {}
        self.enabled = os.getenv("AGENT_MEMORY_ENABLED", "false").lower() == "true"
        
        logger.info(f"Agent memory manager initialized (enabled={self.enabled})")
    
    def get_agent_memory(self, agent_id: str) -> AgentMemory:
        """
        Get or create memory for an agent.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            AgentMemory instance
        """
        if agent_id not in self.agent_memories:
            self.agent_memories[agent_id] = AgentMemory(agent_id)
        return self.agent_memories[agent_id]
    
    def get_all_stats(self) -> Dict[str, Any]:
        """
        Get statistics for all agent memories.
        
        Returns:
            Dictionary with all memory statistics
        """
        stats = {
            "enabled": self.enabled,
            "agents": {}
        }
        
        for agent_id, memory in self.agent_memories.items():
            stats["agents"][agent_id] = memory.get_memory_stats()
        
        return stats


# Global agent memory manager instance
_global_memory_manager: Optional[AgentMemoryManager] = None


def get_agent_memory_manager() -> AgentMemoryManager:
    """
    Get global agent memory manager instance (singleton pattern).
    
    Returns:
        AgentMemoryManager instance
    """
    global _global_memory_manager
    if _global_memory_manager is None:
        _global_memory_manager = AgentMemoryManager()
    return _global_memory_manager
