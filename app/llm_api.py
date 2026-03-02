#!/usr/bin/env python3
"""
LLM API Routes for Phase 3
Enhanced RAG endpoints with LLM integration
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime

from app.llm_engine import get_llm_engine, LLMRequest, LLMResponse
from app.rag_engine import get_rag_engine
from app.evidence_verifier import get_evidence_verifier
from app.decision_composer import get_decision_composer

logger = logging.getLogger(__name__)

# Pydantic models for LLM API
class LLMQueryRequest(BaseModel):
    """Request model for LLM-powered query"""
    query: str = Field(..., description="Underwriting query")
    query_type: str = Field(default="eligibility", description="Type of query")
    use_llm: bool = Field(default=True, description="Use LLM for decision generation")
    max_evidence: int = Field(default=10, description="Maximum evidence chunks to retrieve")
    max_tokens: int = Field(default=1000, description="Maximum tokens for LLM response")
    temperature: float = Field(default=0.3, description="LLM temperature")

class LLMQueryResponse(BaseModel):
    """Response model for LLM-powered query"""
    query: str
    query_type: str
    llm_decision: Optional[Dict[str, Any]] = None
    rag_decision: Optional[Dict[str, Any]] = None
    evidence: List[Dict[str, Any]]
    comparison: Optional[Dict[str, Any]] = None
    processing_time_ms: float
    timestamp: str

class LLMHealthResponse(BaseModel):
    """Health check response for LLM engine"""
    status: str
    openai_available: bool
    api_key_configured: bool
    client_initialized: bool
    timestamp: str

# Create router
router = APIRouter(prefix="/api/llm", tags=["llm"])

@router.post("/query", response_model=LLMQueryResponse)
async def llm_query(request: LLMQueryRequest):
    """
    Process underwriting query with LLM-enhanced decision making
    
    Combines RAG evidence retrieval with LLM decision generation
    """
    start_time = datetime.now()
    
    try:
        logger.info(f"🤖 Processing LLM query: {request.query}")
        
        # Step 1: Retrieve evidence using RAG
        rag_engine = get_rag_engine()
        evidence_chunks = rag_engine.retrieve(
            query=request.query,
            n_results=request.max_evidence
        )
        
        logger.info(f"📊 Retrieved {len(evidence_chunks)} evidence chunks")
        
        # Step 2: Verify evidence quality
        verifier = get_evidence_verifier()
        evidence_assessment = verifier.verify_evidence(evidence_chunks, request.query_type)
        
        # Step 3: Generate traditional RAG decision
        composer = get_decision_composer()
        rag_decision = composer.compose_decision(evidence_chunks, request.query_type)
        
        # Step 4: Generate LLM decision if requested
        llm_decision = None
        comparison = None
        
        if request.use_llm:
            llm_engine = get_llm_engine()
            
            # Prepare LLM request
            llm_req = LLMRequest(
                query=request.query,
                context=[f"Query type: {request.query_type}"],
                evidence=[
                    {
                        "doc_title": chunk.metadata.get("doc_title", "Unknown"),
                        "section": chunk.section,
                        "text": chunk.text,
                        "relevance_score": chunk.relevance_score,
                        "rule_strength": chunk.metadata.get("rule_strength", "informational")
                    }
                    for chunk in evidence_chunks
                ],
                query_type=request.query_type,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )
            
            # Generate LLM decision
            llm_response = llm_engine.generate_decision(llm_req)
            
            llm_decision = {
                "decision": llm_response.decision,
                "confidence": llm_response.confidence,
                "reasoning": llm_response.reasoning,
                "citations": llm_response.citations,
                "required_questions": llm_response.required_questions,
                "referral_triggers": llm_response.referral_triggers,
                "conditions": llm_response.conditions,
                "processing_time_ms": llm_response.processing_time_ms
            }
            
            # Compare decisions
            comparison = compare_decisions(rag_decision, llm_response)
        
        # Format evidence for response
        formatted_evidence = [
            {
                "chunk_id": chunk.chunk_id,
                "doc_title": chunk.metadata.get("doc_title", "Unknown"),
                "section": chunk.section,
                "text": chunk.text,
                "relevance_score": chunk.relevance_score,
                "rule_strength": chunk.metadata.get("rule_strength", "informational")
            }
            for chunk in evidence_chunks
        ]
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        response = LLMQueryResponse(
            query=request.query,
            query_type=request.query_type,
            llm_decision=llm_decision,
            rag_decision={
                "decision": rag_decision.decision_type.value,
                "confidence": rag_decision.confidence_score,
                "reason": rag_decision.primary_reason,
                "citations": [{"citation_id": c.citation_id, "text": c.text} for c in rag_decision.citations],
                "required_questions": [{"question": q.question, "priority": q.priority.value} for q in rag_decision.required_questions],
                "referral_triggers": rag_decision.referral_triggers,
                "conditions": rag_decision.conditions
            },
            evidence=formatted_evidence,
            comparison=comparison,
            processing_time_ms=processing_time,
            timestamp=datetime.now().isoformat()
        )
        
        logger.info(f"✅ LLM query completed in {processing_time:.2f}ms")
        return response
        
    except Exception as e:
        logger.error(f"❌ LLM query failed: {e}")
        raise HTTPException(status_code=500, detail=f"LLM query processing failed: {str(e)}")

@router.get("/health", response_model=LLMHealthResponse)
async def llm_health_check():
    """Check LLM engine health status"""
    try:
        llm_engine = get_llm_engine()
        health = llm_engine.health_check()
        
        return LLMHealthResponse(**health)
        
    except Exception as e:
        logger.error(f"❌ LLM health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.post("/compare")
async def compare_decisions_endpoint(
    rag_decision: Dict[str, Any],
    llm_decision: Dict[str, Any]
):
    """
    Compare RAG and LLM decisions
    """
    try:
        comparison = compare_decisions_dict(rag_decision, llm_decision)
        return comparison
        
    except Exception as e:
        logger.error(f"❌ Decision comparison failed: {e}")
        raise HTTPException(status_code=500, detail=f"Decision comparison failed: {str(e)}")

@router.get("/prompts")
async def get_prompt_templates():
    """Get available prompt templates"""
    return {
        "query_types": [
            {
                "type": "eligibility",
                "description": "Property eligibility assessment",
                "focus": "Property type, location, coverage requirements"
            },
            {
                "type": "endorsement", 
                "description": "Endorsement analysis and requirements",
                "focus": "Coverage enhancements, conditions, documentation"
            },
            {
                "type": "risk_assessment",
                "description": "Risk evaluation and mitigation",
                "focus": "Property condition, hazards, exposure analysis"
            }
        ],
        "parameters": {
            "max_tokens": {"min": 100, "max": 4000, "default": 1000},
            "temperature": {"min": 0.0, "max": 1.0, "default": 0.3},
            "max_evidence": {"min": 1, "max": 50, "default": 10}
        }
    }

def compare_decisions(rag_decision, llm_response: LLMResponse) -> Dict[str, Any]:
    """Compare RAG and LLM decisions"""
    
    rag_decision_type = rag_decision.decision_type.value
    llm_decision_type = llm_response.decision
    
    agreement = rag_decision_type == llm_decision_type
    
    confidence_diff = abs(rag_decision.confidence_score - llm_response.confidence)
    
    return {
        "agreement": agreement,
        "rag_decision": rag_decision_type,
        "llm_decision": llm_decision_type,
        "confidence_difference": confidence_diff,
        "rag_confidence": rag_decision.confidence_score,
        "llm_confidence": llm_response.confidence,
        "recommendation": get_comparison_recommendation(agreement, confidence_diff),
        "analysis": {
            "evidence_alignment": "Both decisions based on similar evidence patterns",
            "reasoning_comparison": f"RAG: {rag_decision.primary_reason[:100]}... vs LLM: {llm_response.reasoning[:100]}...",
            "citation_overlap": len(set([c.citation_id for c in rag_decision.citations]) & set(llm_response.citations))
        }
    }

def compare_decisions_dict(rag_decision: Dict[str, Any], llm_decision: Dict[str, Any]) -> Dict[str, Any]:
    """Compare decisions from dictionaries"""
    
    rag_decision_type = rag_decision.get("decision", "REFER")
    llm_decision_type = llm_decision.get("decision", "REFER")
    
    agreement = rag_decision_type == llm_decision_type
    
    rag_confidence = rag_decision.get("confidence", 0.5)
    llm_confidence = llm_decision.get("confidence", 0.5)
    confidence_diff = abs(rag_confidence - llm_confidence)
    
    return {
        "agreement": agreement,
        "rag_decision": rag_decision_type,
        "llm_decision": llm_decision_type,
        "confidence_difference": confidence_diff,
        "rag_confidence": rag_confidence,
        "llm_confidence": llm_confidence,
        "recommendation": get_comparison_recommendation(agreement, confidence_diff)
    }

def get_comparison_recommendation(agreement: bool, confidence_diff: float) -> str:
    """Get recommendation based on decision comparison"""
    
    if agreement and confidence_diff < 0.2:
        return "High confidence - both systems agree"
    elif agreement and confidence_diff >= 0.2:
        return "Moderate confidence - systems agree but confidence varies"
    elif not agreement and confidence_diff < 0.2:
        return "Low confidence - systems disagree with similar confidence"
    else:
        return "Manual review required - significant disagreement"
