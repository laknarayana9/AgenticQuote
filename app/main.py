from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any
import uuid
from datetime import datetime
import asyncio

from models.schemas import (
    QuoteSubmission, RunRecord, RunStatusResponse, 
    QuoteRunRequest, QuoteRunResponse, RunListResponse,
    WorkflowState
)
from workflows.graph import run_underwriting_workflow
from workflows.agentic_graph import run_agentic_underwriting_workflow
from storage.database import db
from config import settings
from metrics_dashboard import create_dashboard_routes
from security import (
    init_security, init_redis, get_current_user, 
    security_headers_middleware, InputValidator
)
from performance import (
    init_performance, init_cache, cache_manager, 
    performance_monitor, perf_monitor
)
from monitoring import (
    setup_monitoring, monitoring_middleware, 
    health_endpoint, metrics_endpoint, logger, monitoring_loop
)

# Initialize FastAPI app
app = FastAPI(
    title=settings.title,
    description=settings.description,
    version=settings.version
)

# Add security headers middleware
app.middleware("http")(security_headers_middleware)

# Add monitoring middleware
app.middleware("http")(monitoring_middleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Add dashboard routes
create_dashboard_routes(app)

# Add monitoring endpoints
app.add_route("/metrics", metrics_endpoint, methods=["GET"])
app.add_route("/health", health_endpoint, methods=["GET"])

# Initialize production components
@app.on_event("startup")
async def startup_event():
    """Initialize production components on startup."""
    logger.info("Starting Agentic Quote-to-Underwrite application")
    
    # Initialize security
    init_security(settings.secret_key, settings.jwt_secret_key)
    
    # Initialize Redis for caching and rate limiting
    if hasattr(settings, 'redis_url'):
        init_redis(settings.redis_url)
        init_cache(settings.redis_url)
    
    # Initialize performance optimization
    init_performance("storage/underwriting.db", getattr(settings, 'redis_url', None))
    
    # Setup monitoring and alerting
    setup_monitoring()
    
    # Start background monitoring
    asyncio.create_task(monitoring_loop())
    
    logger.info("Application startup completed")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down application")
    # Add cleanup logic here
    logger.info("Application shutdown completed")


def store_run_record(workflow_state: WorkflowState, status: str = "completed", error_message: Optional[str] = None):
    """
    Store the workflow result in the database.
    """
    run_id = str(uuid.uuid4())
    
    # Create node outputs for audit trail
    node_outputs = {
        "validation": {
            "missing_info": workflow_state.missing_info,
            "tool_calls": [call.model_dump() for call in workflow_state.tool_calls if call.tool_name == "validate_submission"]
        },
        "enrichment": {
            "normalized_address": workflow_state.enrichment_result.normalized_address.model_dump() if workflow_state.enrichment_result else None,
            "hazard_scores": workflow_state.enrichment_result.hazard_scores.model_dump() if workflow_state.enrichment_result else None,
            "tool_calls": [call.model_dump() for call in workflow_state.tool_calls if call.tool_name in ["address_normalize", "hazard_score"]]
        },
        "retrieval": {
            "guidelines_count": len(workflow_state.retrieved_guidelines),
            "citations": [chunk.doc_id for chunk in workflow_state.retrieved_guidelines],
            "tool_calls": [call.model_dump() for call in workflow_state.tool_calls if call.tool_name == "rag_retrieval"]
        },
        "assessment": {
            "eligibility_score": workflow_state.uw_assessment.eligibility_score if workflow_state.uw_assessment else None,
            "triggers": [t.model_dump() for t in workflow_state.uw_assessment.triggers] if workflow_state.uw_assessment else [],
            "tool_calls": [call.model_dump() for call in workflow_state.tool_calls if call.tool_name == "underwriting_assessment"]
        },
        "rating": {
            "premium": workflow_state.premium_breakdown.model_dump() if workflow_state.premium_breakdown else None,
            "tool_calls": [call.model_dump() for call in workflow_state.tool_calls if call.tool_name == "rating_calculation"]
        },
        "decision": {
            "decision": workflow_state.decision.decision if workflow_state.decision else None,
            "rationale": workflow_state.decision.rationale if workflow_state.decision else None,
            "tool_calls": [call.model_dump() for call in workflow_state.tool_calls if call.tool_name == "decision_making"]
        }
    }
    
    run_record = RunRecord(
        run_id=run_id,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        status=status,
        workflow_state=workflow_state,
        node_outputs=node_outputs,
        error_message=error_message
    )
    
    db.save_run_record(run_record)
    return run_id


@app.post("/quote/run")
async def run_quote_processing(
    request: QuoteRunRequest,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """
    Process a quote through the underwriting workflow.
    """
    perf_monitor.start_timer("quote_processing")
    
    try:
        # Input validation
        validator = InputValidator()
        
        # Validate submission data
        if not validator.validate_email(request.submission.applicant_email):
            raise HTTPException(status_code=400, detail="Invalid email address")
        
        if not validator.validate_address(request.submission.address):
            raise HTTPException(status_code=400, detail="Invalid address format")
        
        if not validator.validate_coverage_amount(request.submission.coverage_amount):
            raise HTTPException(status_code=400, detail="Invalid coverage amount")
        
        if request.submission.construction_year:
            if not validator.validate_year(request.submission.construction_year):
                raise HTTPException(status_code=400, detail="Invalid construction year")
        
        # Sanitize string inputs
        request.submission.applicant_name = validator.sanitize_string(request.submission.applicant_name)
        request.submission.address = validator.sanitize_string(request.submission.address)
        
        logger.info("Quote processing started", 
                   quote_id=request.quote_id,
                   use_agentic=request.use_agentic,
                   user_id=current_user.get("user_id") if current_user else None)
        
        # Run the appropriate workflow
        if request.use_agentic:
            workflow_state = await run_agentic_underwriting_workflow(
                request.submission, 
                request.additional_answers
            )
        else:
            workflow_state = await run_underwriting_workflow(request.submission)
        
        # Store the run record
        store_run_record(workflow_state)
        
        # Prepare response
        decision_dict = workflow_state.decision.model_dump() if workflow_state.decision else None
        premium_dict = workflow_state.premium_breakdown.model_dump() if workflow_state.premium_breakdown else None
        citations = [citation.model_dump() for citation in workflow_state.retrieved_chunks]
        required_questions = workflow_state.missing_info
        message = "Quote processing completed successfully"
        
        response = QuoteRunResponse(
            run_id=workflow_state.run_id,
            status="completed",
            decision=decision_dict,
            premium=premium_dict,
            citations=citations,
            required_questions=required_questions,
            message=message
        )
        
        perf_monitor.end_timer("quote_processing")
        
        logger.info("Quote processing completed", 
                   run_id=workflow_state.run_id,
                   decision=decision_dict.get("decision") if decision_dict else None,
                   duration=perf_monitor.get_stats("quote_processing").get("avg", 0))
        
        return response
        
    except Exception as e:
        # Create a failed run record
        error_state = WorkflowState(quote_submission=request.submission)
        run_id = store_run_record(error_state, status="failed", error_message=str(e))
        
        raise HTTPException(
            status_code=500,
            detail=f"Processing failed: {str(e)}"
        )


@app.get("/runs/{run_id}", response_model=RunStatusResponse)
async def get_run_status(run_id: str):
    """
    Get the status and details of a specific run.
    """
    run_record = db.get_run_record(run_id)
    
    if run_record is None:
        raise HTTPException(status_code=404, detail="Run not found")
    
    return RunStatusResponse(
        run_id=run_record.run_id,
        status=run_record.status,
        created_at=run_record.created_at,
        updated_at=run_record.updated_at,
        workflow_state=run_record.workflow_state.model_dump(),
        error_message=run_record.error_message
    )


@app.get("/runs", response_model=RunListResponse)
async def list_runs(limit: int = 50, status: Optional[str] = None):
    """
    List recent runs with optional status filter.
    """
    runs = db.list_runs(limit=limit, status=status)
    
    return RunListResponse(
        runs=runs,
        total_count=len(runs)
    )


@app.get("/runs/{run_id}/audit")
async def get_run_audit(run_id: str):
    """
    Get the full audit trail for a run including all node outputs.
    """
    run_record = db.get_run_record(run_id)
    
    if run_record is None:
        raise HTTPException(status_code=404, detail="Run not found")
    
    return {
        "run_id": run_record.run_id,
        "status": run_record.status,
        "created_at": run_record.created_at,
        "updated_at": run_record.updated_at,
        "workflow_state": run_record.workflow_state.model_dump(),
        "node_outputs": run_record.node_outputs,
        "tool_calls": [call.model_dump() for call in run_record.workflow_state.tool_calls],
        "error_message": run_record.error_message
    }


@app.get("/stats")
async def get_statistics():
    """
    Get basic statistics about the system.
    """
    return db.get_statistics()


@app.get("/")
async def root():
    """
    Root endpoint that serves the UI.
    """
    return {"message": "Agentic Quote-to-Underwrite API", "ui_url": "/static/index.html"}


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
