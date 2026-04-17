"""
Phase A API Endpoints
Implements new API endpoints as specified in the enhancement document:
- POST /quotes
- POST /quotes/{run_id}/resume
- GET /runs/{run_id}/decision-packet
- HITL endpoints
- Mock provider endpoints
"""

from fastapi import APIRouter, HTTPException, Header, Depends
from typing import Optional, Dict, Any, List
import uuid
import hashlib
from datetime import datetime

from models.schemas import (
    HO3Submission, DecisionPacket, WorkflowState, QuoteRunResponse
)
from storage.database import db
from security import get_current_user
from monitoring import logger
from tools.mock_providers import MockProviderGateway


# Create router
router = APIRouter(prefix="/api/v1", tags=["phase-a"])


# ============================================================================
# Quote Endpoints
# ============================================================================

@router.post("/quotes", response_model=QuoteRunResponse)
async def create_quote(
    submission: HO3Submission,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """
    Create a new quote with idempotency protection.
    
    Idempotency-Key header is required to prevent duplicate submissions.
    """
    # Validate idempotency key
    if not idempotency_key:
        raise HTTPException(
            status_code=400,
            detail="Idempotency-Key header is required"
        )
    
    # Check for existing idempotency key
    existing = db.check_idempotency_key(idempotency_key)
    if existing:
        # Return the existing response
        return QuoteRunResponse(
            run_id=existing["response_run_id"],
            status="completed",
            message="Duplicate request - returning cached result"
        )
    
    # Generate run ID
    run_id = str(uuid.uuid4())
    quote_id = f"Q-2026-{uuid.uuid4().hex[:6].upper()}"
    
    # Create request hash for idempotency
    request_hash = hashlib.md5(submission.model_dump_json().encode()).hexdigest()
    
    # Store idempotency key
    db.store_idempotency_key(
        idempotency_key=idempotency_key,
        user_id=current_user.get("user_id") if current_user else "anonymous",
        request_hash=request_hash,
        response_run_id=run_id
    )
    
    logger.info("Quote created", run_id=run_id, quote_id=quote_id)
    
    # TODO: Integrate with workflow execution
    # For now, return a placeholder response
    return QuoteRunResponse(
        run_id=run_id,
        status="processing",
        message="Quote submitted for processing"
    )


@router.post("/quotes/{run_id}/resume", response_model=QuoteRunResponse)
async def resume_quote(
    run_id: str,
    additional_answers: Dict[str, Any],
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """
    Resume a quote that was waiting for additional information.
    
    Requires idempotency key for safe retries.
    """
    # Validate idempotency key
    if not idempotency_key:
        raise HTTPException(
            status_code=400,
            detail="Idempotency-Key header is required"
        )
    
    # Check if run exists and is in waiting state
    run_record = db.get_run_record(run_id)
    if not run_record:
        raise HTTPException(
            status_code=404,
            detail=f"Run {run_id} not found"
        )
    
    if run_record.status != "waiting_for_info":
        raise HTTPException(
            status_code=400,
            detail=f"Run {run_id} is not waiting for information (status: {run_record.status})"
        )
    
    # Check for existing idempotency key
    existing = db.check_idempotency_key(idempotency_key)
    if existing:
        return QuoteRunResponse(
            run_id=existing["response_run_id"],
            status="completed",
            message="Duplicate request - returning cached result"
        )
    
    # Store idempotency key
    request_hash = hashlib.md5(str(additional_answers).encode()).hexdigest()
    db.store_idempotency_key(
        idempotency_key=idempotency_key,
        user_id=current_user.get("user_id") if current_user else "anonymous",
        request_hash=request_hash,
        response_run_id=run_id
    )
    
    logger.info("Quote resumed", run_id=run_id, answers_count=len(additional_answers))
    
    # TODO: Resume workflow with additional answers
    # For now, return a placeholder response
    return QuoteRunResponse(
        run_id=run_id,
        status="processing",
        message="Quote resumed with additional information"
    )


# ============================================================================
# Decision Packet Endpoints
# ============================================================================

@router.get("/runs/{run_id}/decision-packet", response_model=DecisionPacket)
async def get_decision_packet(
    run_id: str,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """
    Get the final decision packet for a run.
    
    The decision packet contains all information needed for:
    - Producer-facing explanation
    - Underwriter review
    - Audit and replay
    """
    run_record = db.get_run_record(run_id)
    if not run_record:
        raise HTTPException(
            status_code=404,
            detail=f"Run {run_id} not found"
        )
    
    workflow_state = run_record.workflow_state
    
    # Check if decision packet exists
    if not workflow_state.decision_packet:
        raise HTTPException(
            status_code=404,
            detail=f"Decision packet not yet available for run {run_id}"
        )
    
    return workflow_state.decision_packet


# ============================================================================
# HITL Endpoints
# ============================================================================

@router.get("/hitl/tasks")
async def list_hitl_tasks(
    status: Optional[str] = None,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """
    List HITL tasks, optionally filtered by status.
    
    Access restricted to underwriter role.
    """
    # TODO: Implement role-based access control
    if current_user and current_user.get("role") != "underwriter":
        raise HTTPException(
            status_code=403,
            detail="Access restricted to underwriters"
        )
    
    tasks = db.list_hitl_tasks(status=status)
    return {"tasks": tasks, "count": len(tasks)}


@router.post("/hitl/{task_id}/actions")
async def hitl_task_action(
    task_id: str,
    action: Dict[str, Any],
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """
    Perform an action on a HITL task (approve/override/request-info).
    
    Access restricted to underwriter role.
    """
    # TODO: Implement role-based access control
    if current_user and current_user.get("role") != "underwriter":
        raise HTTPException(
            status_code=403,
            detail="Access restricted to underwriters"
        )
    
    action_type = action.get("action")
    if action_type not in ["approve", "override", "request_info"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action: {action_type}. Must be one of: approve, override, request_info"
        )
    
    # Get task
    task = db.get_hitl_task(task_id)
    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found"
        )
    
    # Perform action
    result = db.process_hitl_action(task_id, action, current_user.get("user_id"))
    
    logger.info("HITL action performed", task_id=task_id, action=action_type, user=current_user.get("user_id"))
    
    return result


# ============================================================================
# Retrieval Endpoints
# ============================================================================

@router.post("/retrieval/query")
async def retrieval_query(
    query: Dict[str, Any],
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """
    Query the retrieval system for guideline evidence.
    
    Access restricted to underwriter and admin roles.
    """
    # TODO: Implement role-based access control
    allowed_roles = ["underwriter", "admin"]
    if current_user and current_user.get("role") not in allowed_roles:
        raise HTTPException(
            status_code=403,
            detail="Access restricted to underwriters and admins"
        )
    
    question = query.get("question")
    filters = query.get("filters", {})
    
    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question is required"
        )
    
    # TODO: Integrate with RAG engine
    # For now, return a placeholder response
    return {
        "question": question,
        "filters": filters,
        "evidence_chunks": [],
        "retrieval_metrics": {
            "latency_ms": 0,
            "hit_count": 0
        }
    }


# ============================================================================
# Search Endpoints
# ============================================================================

@router.post("/search/preview")
async def search_preview(
    search_request: Dict[str, Any],
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """
    Preview a web search request before execution.
    
    Access restricted to underwriter and admin roles.
    """
    # TODO: Implement role-based access control
    allowed_roles = ["underwriter", "admin"]
    if current_user and current_user.get("role") not in allowed_roles:
        raise HTTPException(
            status_code=403,
            detail="Access restricted to underwriters and admins"
        )
    
    intent = search_request.get("intent")
    query = search_request.get("query")
    
    if not intent or not query:
        raise HTTPException(
            status_code=400,
            detail="Intent and query are required"
        )
    
    # Policy engine check
    # TODO: Implement policy engine for search governance
    policy_decision = {
        "approved": True,
        "reason": "Search is within policy bounds",
        "params": {
            "max_results": 5,
            "topic": "general"
        }
    }
    
    return policy_decision


# ============================================================================
# Admin Endpoints
# ============================================================================

@router.post("/guidelines/upload")
async def upload_guideline(
    file_metadata: Dict[str, Any],
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """
    Upload a new guideline document.
    
    Access restricted to admin role.
    """
    # TODO: Implement role-based access control
    if current_user and current_user.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Access restricted to admins"
        )
    
    doc_id = f"GUIDE-{uuid.uuid4().hex[:8].upper()}"
    version = file_metadata.get("version", "v1.0")
    
    # TODO: Implement file upload and ingestion
    logger.info("Guideline upload requested", doc_id=doc_id, version=version)
    
    return {
        "doc_id": doc_id,
        "version": version,
        "status": "pending_ingestion",
        "message": "Guideline uploaded and pending ingestion"
    }


@router.post("/guidelines/reindex")
async def reindex_guidelines(
    reindex_request: Dict[str, Any],
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """
    Reindex guideline documents.
    
    Access restricted to admin role.
    """
    # TODO: Implement role-based access control
    if current_user and current_user.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Access restricted to admins"
    )
    
    doc_id = reindex_request.get("doc_id")
    
    # TODO: Implement reindexing logic
    logger.info("Guideline reindex requested", doc_id=doc_id)
    
    return {
        "status": "reindexing",
        "doc_id": doc_id if doc_id else "all",
        "message": "Reindexing started"
    }


# ============================================================================
# Mock Provider Endpoints
# ============================================================================

@router.get("/mock/property/profile")
async def mock_property_profile(address: str):
    """
    Mock property profile endpoint.
    
    Returns structure facts (year built, roof, sqft) deterministically based on address.
    """
    gateway = MockProviderGateway()
    return gateway.mock_property_profile(address)


@router.get("/mock/hazard/score")
async def mock_hazard_score(lat: float, lon: float):
    """
    Mock hazard score endpoint.
    
    Returns wildfire/flood/wind/quake scores.
    """
    gateway = MockProviderGateway()
    # Generate a mock address for deterministic results
    address = f"lat_{lat}_lon_{lon}"
    return gateway.mock_hazard_scores(address, lat, lon)


@router.get("/mock/geocode")
async def mock_geocode(address: str):
    """
    Mock geocode endpoint.
    
    Returns lat/lon, county, FIPS codes.
    """
    gateway = MockProviderGateway()
    return gateway.mock_geocode(address)


@router.get("/mock/census")
async def mock_census(address: str):
    """
    Mock census endpoint.
    
    Returns neighborhood context (non-pricing, demo-only).
    """
    gateway = MockProviderGateway()
    return gateway.mock_census_data(address)


@router.get("/mock/claims")
async def mock_claims(address: str):
    """
    Mock claims history endpoint.
    
    Returns loss counts/severity buckets.
    """
    gateway = MockProviderGateway()
    return gateway.mock_claims_history(address)


@router.get("/mock/replacement-cost")
async def mock_replacement_cost(address: str, sqft: int, year_built: int):
    """
    Mock replacement cost endpoint.
    
    Returns dwelling RC estimate for Coverage A adequacy.
    """
    gateway = MockProviderGateway()
    return gateway.mock_replacement_cost(address, sqft, year_built)
