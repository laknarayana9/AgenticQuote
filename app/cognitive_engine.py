"""
Minimal cognitive engine implementation for test compatibility
"""

import logging
from typing import List, Dict, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class KnowledgeChunk:
    """Knowledge chunk representation"""
    id: str
    content: str
    metadata: Dict[str, Any]

class CognitiveEngine:
    """Simple cognitive engine implementation"""
    
    def __init__(self):
        self.chunks: List[KnowledgeChunk] = []
        logger.info("Cognitive engine initialized")
    
    def add_chunk(self, chunk: KnowledgeChunk):
        """Add knowledge chunk"""
        self.chunks.append(chunk)
    
    def search(self, query: str) -> List[KnowledgeChunk]:
        """Search knowledge chunks"""
        return [chunk for chunk in self.chunks if query.lower() in chunk.content.lower()]
    
    def get_chunk_count(self) -> int:
        """Get total chunk count"""
        return len(self.chunks)

def get_cognitive_engine():
    """Get cognitive engine instance"""
    return CognitiveEngine()

__all__ = ["CognitiveEngine", "KnowledgeChunk", "get_cognitive_engine"]
