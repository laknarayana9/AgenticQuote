#!/usr/bin/env python3
"""
IntelliUnderwrite AI Platform - Core Intelligence Module

This package implements the core artificial intelligence components
of the IntelliUnderwrite enterprise underwriting platform.

Core Intelligence Components:
- Cognitive Knowledge Retrieval System
- Advanced Reasoning Engine  
- Multi-Modal Document Understanding
- Continuous Learning & Adaptation
- Explainable AI Framework

Version: 1.0.0
Platform: IntelliUnderwrite AI Platform
"""

__version__ = "1.0.0"
__title__ = "IntelliUnderwrite AI Platform"
__description__ = "Enterprise AI-Powered Underwriting Solution"
__author__ = "IntelliUnderwrite AI Team"

# Core intelligence components
from .cognitive_engine import get_cognitive_engine, CognitiveKnowledgeRetrieval
from .intelligent_reasoning import get_reasoning_engine, AdvancedReasoningEngine
from .llm_engine import get_llm_engine, LLMEngine

# Legacy components (maintained for compatibility)
from .rag_engine import get_rag_engine, RAGEngine
from .evidence_verifier import get_evidence_verifier, EvidenceVerifier
from .decision_composer import get_decision_composer, DecisionComposer

__all__ = [
    # Core intelligence components
    "get_cognitive_engine",
    "CognitiveKnowledgeRetrieval", 
    "get_reasoning_engine",
    "AdvancedReasoningEngine",
    "get_llm_engine",
    "LLMEngine",
    
    # Legacy compatibility components
    "get_rag_engine",
    "RAGEngine",
    "get_evidence_verifier", 
    "EvidenceVerifier",
    "get_decision_composer",
    "DecisionComposer",
    
    # Package metadata
    "__version__",
    "__title__",
    "__description__",
    "__author__"
]

# Platform initialization logging
import logging
logger = logging.getLogger(__name__)

logger.info("🧠 IntelliUnderwrite AI Platform initialized")
logger.info(f"📦 Version: {__version__}")
logger.info(f"🎯 Description: {__description__}")
logger.info("🚀 Core AI components loaded")
