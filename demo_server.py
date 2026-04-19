#!/usr/bin/env python3
"""
Simple demo server for HITL functionality without complex imports
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import os
import uuid
import random
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Agentic Quote-to-Underwrite - Demo")

@app.post("/quote/run")
async def run_quote_processing(request: dict):
    """Enhanced quote processing with HITL pausing demo"""
    try:
        submission = request.get("submission", {})
        use_agentic = request.get("use_agentic", False)
        additional_answers = request.get("additional_answers", {})
        
        if use_agentic:
            # Check for missing required fields
            required_fields = ["roof_age_years", "construction_type", "occupancy_type"]
            missing_fields = []
            for field in required_fields:
                if field not in submission or not submission.get(field):
                    missing_fields.append(field)
            
            # Determine status based on missing info
            if missing_fields and not additional_answers:
                status = "waiting_for_info"
                message = "Additional information required - please answer the following questions"
                required_questions = [
                    {
                        "question_id": f"missing_{field}",
                        "question_text": f"Please provide {field.replace('_', ' ')}",
                        "question_type": "text",
                        "required": True
                    }
                    for field in missing_fields
                ]
                
                # Return waiting state
                response = {
                    "run_id": str(uuid.uuid4()),
                    "status": status,
                    "message": message,
                    "required_questions": required_questions,
                    "missing_info": missing_fields,
                    "requires_human_review": True,
                    "current_node": "handle_missing_info"
                }
                return JSONResponse(response)
            
            # If we have answers or no missing info, continue processing
            status = "completed"
            message = "Quote processing completed"
            
            # Use real underwriting content for demo
            rag_evidence = [
                {
                    "chunk_id": "uw_guidelines_2_1",
                    "doc_title": "Homeowners Underwriting Guidelines",
                    "section": "2. Construction & Maintenance Standards",
                    "text": "If roof age is > 20 years, the risk SHALL BE REFERRED. Roof condition must be documented with recent photos or inspection report.",
                    "relevance_score": 0.92,
                    "rule_strength": "mandatory"
                },
                {
                    "chunk_id": "uw_guidelines_1_1",
                    "doc_title": "Homeowners Underwriting Guidelines", 
                    "section": "1. Eligibility Overview",
                    "text": "Properties used for short-term rental SHALL BE REFERRED. Home office businesses require HOB-02 endorsement.",
                    "relevance_score": 0.87,
                    "rule_strength": "required"
                }
            ]
            
            # Generate decision based on missing info and evidence
            if missing_fields:
                decision = "REFER"
                confidence = 0.65
            else:
                decision = "ACCEPT"
                confidence = 0.82
        
        # Mock logic fallback (when not using agentic)
        else:
            decisions = ["ACCEPT", "REFER", "DECLINE"]
            decision = random.choice(decisions)
            confidence = random.uniform(0.6, 0.95)
            rag_evidence = []
        
        # Build final response
        response = {
            "run_id": str(uuid.uuid4()),
            "status": status,
            "decision": {
                "decision": decision,
                "confidence": confidence,
                "reason": f"{'Agentic' if use_agentic else 'Mock'} {decision.lower()} decision based on evidence review"
            },
            "premium": {
                "annual_premium": round(random.uniform(500, 2000), 2),
                "monthly_premium": round(random.uniform(40, 170), 2),
                "coverage_amount": submission.get("coverage_amount", 500000)
            },
            "citations": rag_evidence if use_agentic else [
                {
                    "doc_title": "Underwriting Guidelines",
                    "text": f"Mock citation for {decision} decision",
                    "relevance_score": random.uniform(0.8, 0.95)
                }
            ],
            "required_questions": [
                {
                    "question": "Please provide additional documentation",
                    "description": "Required for underwriting review"
                }
            ] if decision == "REFER" else [],
            "referral_triggers": [f"{'Real RAG' if use_agentic else 'Mock'} trigger for {decision}"],
            "conditions": [f"{'Real RAG' if use_agentic else 'Mock'} condition for {decision}"],
            "rag_evidence": rag_evidence,
            "requires_human_review": decision in ["REFER", "DECLINE"],
            "human_review_details": {
                "review_type": "agentic_review" if use_agentic else "mock_review",
                "assigned_reviewer": "underwriting_team",
                "review_priority": "high" if decision in ["REFER", "DECLINE"] else "low",
                "estimated_review_time": "24-48 hours" if decision in ["REFER", "DECLINE"] else "N/A"
            },
            "message": f"{'Agentic' if use_agentic else 'Mock'} quote processing completed - {decision}",
            "processing_time_ms": random.randint(100, 300)
        }
        
        # Fix JSON serialization for Pydantic models
        def fix_json_serialization(obj):
            """Convert Pydantic models to dicts for JSON serialization"""
            if hasattr(obj, 'model_dump'):
                return obj.model_dump()
            elif hasattr(obj, 'dict'):
                return obj.dict()
            elif isinstance(obj, dict):
                return {k: fix_json_serialization(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [fix_json_serialization(item) for item in obj]
            else:
                return obj
        
        # Fix the response for JSON serialization
        fixed_response = fix_json_serialization(response)
        
        return JSONResponse(fixed_response)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quote processing failed: {str(e)}")

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat(), "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    print("Starting Demo Server with HITL functionality")
    print("Server will be available at: http://localhost:8000")
    uvicorn.run("demo_server:app", host="0.0.0.0", port=8000, reload=True)
