#!/usr/bin/env python3
"""
Simple FastAPI server for Phase 3 testing
Includes LLM integration for advanced decision making
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import os
import uuid
import random
from datetime import datetime
import json

# Create FastAPI app
app = FastAPI(title="Agentic Quote-to-Underwrite - Phase 3")

# Mount static files
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    """Serve main page"""
    try:
        with open("static/index.html", "r") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        return HTMLResponse("""
        <html>
        <body>
            <h1>Agentic Quote-to-Underwrite</h1>
            <p>Error: static/index.html not found</p>
            <p>Please ensure you're running from the project root directory.</p>
        </body>
        </html>
        """)

@app.post("/quote/run")
async def run_quote_processing(request: dict):
    """Enhanced quote processing with LLM integration"""
    try:
        submission = request.get("submission", {})
        use_agentic = request.get("use_agentic", False)
        use_llm = request.get("use_llm", False)  # Phase 3 LLM option
        
        # Generate mock decision
        decisions = ["ACCEPT", "REFER", "DECLINE"]
        decision = random.choice(decisions)
        confidence = random.uniform(0.6, 0.95)
        
        # Mock RAG evidence if agentic is enabled
        rag_evidence = []
        rag_assessment = None
        llm_decision = None
        
        if use_agentic:
            # Mock evidence chunks
            rag_evidence = [
                {
                    "chunk_id": f"mock_chunk_{i}",
                    "doc_title": f"Underwriting Guidelines {i+1}",
                    "section": f"Section {i+1}",
                    "text": f"Mock evidence text for {decision} decision based on underwriting rules...",
                    "relevance_score": random.uniform(0.7, 0.95),
                    "rule_strength": random.choice(["mandatory", "required", "recommended"])
                }
                for i in range(3)
            ]
            
            rag_assessment = {
                "assessment": {
                    "quality": random.choice(["high", "medium", "low"]),
                    "confidence": confidence,
                    "rule_strength": random.choice(["mandatory", "required", "recommended"])
                },
                "chunks_count": len(rag_evidence)
            }
        
        # Mock LLM decision if enabled
        if use_llm and use_agentic:
            llm_decision = {
                "decision": decision,
                "confidence": min(0.95, confidence + random.uniform(-0.1, 0.1)),
                "reasoning": f"LLM analysis: Based on the provided evidence and underwriting guidelines, the property {decision.lower()} due to specific risk factors and compliance requirements. The decision considers property characteristics, location risks, and coverage needs.",
                "citations": [f"LLM Citation {i+1}" for i in range(2)],
                "required_questions": [
                    {
                        "question": "Please provide additional property documentation",
                        "description": "Required for comprehensive risk assessment"
                    }
                ] if decision == "REFER" else [],
                "referral_triggers": [f"LLM identified trigger: {decision} factors"],
                "conditions": [f"LLM condition: {decision} requirements"],
                "processing_time_ms": random.randint(200, 500)
            }
        
        # Mock response
        response = {
            "run_id": str(uuid.uuid4()),
            "status": "completed",
            "decision": {
                "decision": decision,
                "confidence": confidence,
                "reason": f"Mock {decision.lower()} decision based on evidence review"
            },
            "premium": {
                "annual_premium": round(random.uniform(500, 2000), 2),
                "monthly_premium": round(random.uniform(40, 170), 2),
                "coverage_amount": submission.get("coverage_amount", 500000)
            },
            "citations": [
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
            "referral_triggers": [f"Mock trigger for {decision}"],
            "conditions": [f"Mock condition for {decision}"],
            "rag_evidence": rag_evidence,
            "rag_assessment": rag_assessment,
            "llm_decision": llm_decision,
            "decision_comparison": compare_mock_decisions(decision, confidence, llm_decision) if llm_decision else None,
            "requires_human_review": decision in ["REFER", "DECLINE"],
            "human_review_details": {
                "review_type": "mock_review",
                "assigned_reviewer": "underwriting_team",
                "review_priority": "high" if decision in ["REFER", "DECLINE"] else "low",
                "estimated_review_time": "24-48 hours" if decision in ["REFER", "DECLINE"] else "N/A"
            },
            "message": f"Quote processing completed - {decision}",
            "processing_time_ms": random.randint(100, 300)
        }
        
        return JSONResponse(response)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quote processing failed: {str(e)}")

@app.post("/api/llm/query")
async def llm_query(request: dict):
    """Mock LLM query endpoint"""
    try:
        query = request.get("query", "")
        query_type = request.get("query_type", "eligibility")
        use_llm = request.get("use_llm", True)
        
        # Mock evidence
        evidence = [
            {
                "chunk_id": f"llm_chunk_{i}",
                "doc_title": f"LLM Guidelines {i+1}",
                "section": f"Section {i+1}",
                "text": f"LLM evidence text for {query_type} analysis...",
                "relevance_score": random.uniform(0.8, 0.95),
                "rule_strength": random.choice(["mandatory", "required", "recommended"])
            }
            for i in range(5)
        ]
        
        # Mock decisions
        rag_decision = {
            "decision": random.choice(["ACCEPT", "REFER", "DECLINE"]),
            "confidence": random.uniform(0.6, 0.9),
            "reason": "RAG-based decision analysis"
        }
        
        llm_decision = None
        comparison = None
        
        if use_llm:
            llm_decision = {
                "decision": rag_decision["decision"],
                "confidence": min(0.95, rag_decision["confidence"] + 0.1),
                "reasoning": f"LLM comprehensive analysis for {query_type}: The evidence supports {rag_decision['decision'].lower()} based on underwriting guidelines and risk assessment principles.",
                "citations": [f"LLM Citation {i+1}" for i in range(3)],
                "required_questions": ["Please provide additional information"] if rag_decision["decision"] == "REFER" else [],
                "referral_triggers": ["LLM identified risk factors"],
                "conditions": ["LLM specified conditions"],
                "processing_time_ms": random.randint(300, 600)
            }
            
            comparison = {
                "agreement": True,
                "rag_decision": rag_decision["decision"],
                "llm_decision": llm_decision["decision"],
                "confidence_difference": abs(rag_decision["confidence"] - llm_decision["confidence"]),
                "recommendation": "High confidence - both systems agree"
            }
        
        return JSONResponse({
            "query": query,
            "query_type": query_type,
            "llm_decision": llm_decision,
            "rag_decision": rag_decision,
            "evidence": evidence,
            "comparison": comparison,
            "processing_time_ms": random.randint(200, 400),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM query failed: {str(e)}")

@app.get("/api/llm/health")
async def llm_health():
    """LLM engine health check"""
    return JSONResponse({
        "status": "mock_mode",
        "openai_available": False,
        "api_key_configured": False,
        "client_initialized": False,
        "timestamp": datetime.now().isoformat()
    })

@app.get("/runs")
async def get_runs(limit: int = 100):
    """Get recent runs for display"""
    # Mock recent runs data
    mock_runs = [
        {
            "run_id": f"mock_run_{i}",
            "status": random.choice(["completed", "pending", "referred"]),
            "decision": {
                "decision": random.choice(["ACCEPT", "REFER", "DECLINE"]),
                "confidence": round(random.uniform(0.6, 0.95), 3)
            },
            "created_at": datetime.now().isoformat(),
            "premium": {
                "annual_premium": round(random.uniform(500, 2000), 2),
                "coverage_amount": random.choice([300000, 500000, 750000])
            },
            "llm_enhanced": random.choice([True, False])  # Phase 3 addition
        }
        for i in range(10)  # Generate 10 mock runs
    ]
    
    return {
        "runs": mock_runs[:limit],
        "total_count": len(mock_runs)
    }

@app.get("/templates/evidence-panel.html")
async def get_evidence_panel():
    """Serve evidence panel template"""
    try:
        with open("templates/evidence-panel.html", "r") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        return HTMLResponse("""
        <html>
        <body>
            <h1>Evidence Panel Template</h1>
            <p>Error: templates/evidence-panel.html not found</p>
        </body>
        </html>
        """)

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "phase": "3", "llm_enabled": True}

def compare_mock_decisions(decision: str, confidence: float, llm_decision: dict) -> dict:
    """Compare mock RAG and LLM decisions"""
    if not llm_decision:
        return None
    
    llm_dec = llm_decision.get("decision", decision)
    llm_conf = llm_decision.get("confidence", confidence)
    
    agreement = decision == llm_dec
    confidence_diff = abs(confidence - llm_conf)
    
    return {
        "agreement": agreement,
        "rag_decision": decision,
        "llm_decision": llm_dec,
        "confidence_difference": confidence_diff,
        "recommendation": "High confidence" if agreement and confidence_diff < 0.2 else "Manual review"
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Phase 2 Evidence-First Underwriting Server")
    print("🌐 Server will be available at: http://localhost:8000")
    print("📄 Main page: http://localhost:8000/")
    print("🎯 Ready for testing!")
    uvicorn.run("simple_server:app", host="0.0.0.0", port=8000, reload=True)
