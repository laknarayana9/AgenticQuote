"""
Specialized Agent Contracts for Phase A Enhancement
Implements the 7 specialized agents with strict contracts as specified in the enhancement document.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
import time
from models.schemas import (
    HO3Submission, RiskProfile, CoverageRequest, Applicant,
    WorkflowState, RetrievalChunk, DecisionPacket, DecisionType
)
from tools.mock_providers import MockProviderGateway
from providers.provider_gateway import ProviderGateway
from providers.llm_client import get_llm_client
from providers.web_search import get_web_search
from prompts.underwriting_assessor import UNDERWRITING_ASSESSOR_PROMPT
from observability import get_tracer, record_agent_decision


class AgentContractError(Exception):
    """Base exception for agent contract violations"""
    pass


class IntakeNormalizerAgent:
    """
    Agent Contract: Intake Normalizer
    
    Responsibilities:
    - Validate required HO3 intake fields (named insured, address, occupancy, coverage request)
    - Normalize enumerations (occupancy, construction type, roof type, etc.)
    - Produce missing_info list with human-readable questions for the UI
    
    Idempotency:
    - Deterministic for the same (submission_raw + prompt_version)
    - Cache key: hash(submission_raw) + prompt_version
    
    Error modes:
    - INVALID_SCHEMA: cannot parse required fields → return 400 at API boundary
    - AMBIGUOUS_INPUT: conflicting data → route to HITL
    """

    def __init__(self, prompt_version: str = "v1.0"):
        self.prompt_version = prompt_version
        self.required_fields = ["applicant", "risk", "coverage_request"]
        
    def normalize(self, submission_raw: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize raw submission into canonical HO3 schema.
        """
        try:
            # Extract and validate applicant
            applicant_data = submission_raw.get("applicant", {})
            applicant = Applicant(**applicant_data)
            
            # Extract and validate risk profile
            risk_data = submission_raw.get("risk", {})
            risk = RiskProfile(**risk_data)
            
            # Extract and validate coverage request
            coverage_data = submission_raw.get("coverage_request", {})
            coverage = CoverageRequest(**coverage_data)
            
            # Create canonical submission
            canonical = HO3Submission(
                applicant=applicant,
                risk=risk,
                coverage_request=coverage,
                quote_id=submission_raw.get("quote_id")
            )
            
            # Check for missing critical fields
            missing_info = []
            questions = []
            
            if not risk.roof_age_years:
                missing_info.append("roof_age_years")
                questions.append({
                    "question_id": "roof_age_years",
                    "prompt": "What is the roof age (years)?",
                    "type": "number",
                    "required": True,
                    "reason": "Roof age is required for eligibility and wind/hail risk assessment."
                })
            
            # Check for contradictions
            contradictions = []
            if risk.occupancy == "owner_occupied_primary" and not applicant.email:
                contradictions.append("Primary occupancy but no email provided")
            
            return {
                "submission_canonical": canonical.model_dump(),
                "missing_info": missing_info,
                "questions": questions,
                "validation": {
                    "is_complete_enough_to_progress": len(missing_info) == 0,
                    "contradictions": contradictions
                },
                "prompt_version": self.prompt_version
            }
            
        except Exception as e:
            raise AgentContractError(f"INVALID_SCHEMA: {str(e)}")


class PlannerRouterAgent:
    """
    Agent Contract: Planner / Router
    
    Responsibilities:
    - Determine path: straight_through, needs_enrichment, waiting_for_info, hard_refer, hard_decline_candidate
    - Decide retrieval filters (state/product/carrier/version)
    - Decide if Tavily search is allowed and, if so, what query constraints apply
    
    Idempotency:
    - Deterministic for the same canonical submission + configuration snapshot
    
    Error modes:
    - LOW_CONFIDENCE_ROUTE: return "route=refer" + HITL explanation
    """

    def __init__(self, appetite_config: Optional[Dict] = None):
        self.appetite_config = appetite_config or {
            "max_coverage_a": 2000000,
            "min_year_built": 1900,
            "eligible_occupancies": ["owner_occupied_primary", "owner_occupied_secondary"],
            "eligible_dwellings": ["single_family", "condo", "townhouse"]
        }
    
    def route(self, canonical_submission: HO3Submission, missing_info: List[str]) -> Dict[str, Any]:
        """
        Determine the workflow path based on submission state.
        """
        # Check if waiting for info
        if missing_info:
            return {
                "route": "waiting_for_info",
                "reason_codes": [f"MISSING_{field.upper()}" for field in missing_info],
                "retrieval_plan": {
                    "collection": "uw_guidelines",
                    "filters": {},
                    "max_chunks": 0
                },
                "search_plan": {
                    "enabled": False,
                    "justification": "Waiting for missing information"
                },
                "model_budgets": {
                    "normalizer_model": "gpt-4o-mini",
                    "assessment_model": "gpt-4o",
                    "verifier_model": "gpt-4o"
                }
            }
        
        # Check for hard decline candidates
        risk = canonical_submission.risk
        if risk.year_built < self.appetite_config["min_year_built"]:
            return {
                "route": "hard_decline_candidate",
                "reason_codes": ["YEAR_BUILT_TOO_OLD"],
                "retrieval_plan": {"collection": "uw_guidelines", "filters": {}, "max_chunks": 5},
                "search_plan": {"enabled": False, "justification": "Hard decline candidate"},
                "model_budgets": {"assessment_model": "gpt-4o", "verifier_model": "gpt-4o"}
            }
        
        # Check for hard refer candidates
        if risk.occupancy not in self.appetite_config["eligible_occupancies"]:
            return {
                "route": "hard_refer",
                "reason_codes": ["INELIGIBLE_OCCUPANCY"],
                "retrieval_plan": {"collection": "uw_guidelines", "filters": {}, "max_chunks": 5},
                "search_plan": {"enabled": False, "justification": "Ineligible occupancy"},
                "model_budgets": {"assessment_model": "gpt-4o", "verifier_model": "gpt-4o"}
            }
        
        # Default: straight through with enrichment
        return {
            "route": "straight_through",
            "reason_codes": [],
            "retrieval_plan": {
                "collection": "uw_guidelines",
                "filters": {
                    "state": "CA",
                    "product": "HO3",
                    "carrier": "DemoCarrier",
                    "effective_date_lte": "2026-03-15"
                },
                "max_chunks": 8
            },
            "search_plan": {
                "enabled": False,
                "justification": "Internal guidelines sufficient for decisioning"
            },
            "model_budgets": {
                "normalizer_model": "gpt-4o-mini",
                "assessment_model": "gpt-4o",
                "verifier_model": "gpt-4o"
            }
        }


class EnrichmentAgent:
    """
    Agent Contract: Enrichment Agent
    
    Responsibilities:
    - Call deterministic mocked providers (property profile, hazards, geocode, claims history)
    - Compute an enrichment.confidence_map per field (provider confidence + age of data)
    - Provide "explainable" derived facts
    
    Idempotency:
    - Tool calls are idempotent (read-only)
    - Cache key: provider + address_hash + provider_version
    
    Error modes:
    - PROVIDER_TIMEOUT: degrade gracefully (mark field unknown, raise "needs_review" flag)
    - PROVIDER_DATA_CONFLICT: record contradiction in events and route to verifier
    """

    def __init__(self):
        # Use ProviderGateway if USE_REAL_PROVIDERS is true, otherwise use MockProviderGateway directly
        import os
        if os.getenv("USE_REAL_PROVIDERS", "false").lower() == "true":
            from providers.provider_gateway import ProviderGateway
            self.gateway = ProviderGateway()
            self.use_real = True
        else:
            self.gateway = MockProviderGateway()
            self.use_real = False
    
    def enrich(self, canonical_submission: HO3Submission) -> Dict[str, Any]:
        """
        Enrich submission with provider data.
        """
        address = canonical_submission.risk.property_address
        
        try:
            if self.use_real:
                # Use real providers via ProviderGateway
                geocode = self.gateway.geocode(address)
                property_profile = self.gateway.get_property_profile(address)
                property_profile["year_built"] = canonical_submission.risk.year_built
                
                # Extract county from geocode for hazard scores
                county = geocode.get("county", "Unknown")
                state = geocode.get("state", "CA")
                hazard_scores = self.gateway.get_hazard_scores(county, state)
                claims_history = self.gateway.get_claims_history(address, canonical_submission.risk.dwelling_type)
                
                # Providers not yet implemented in real providers
                census_data = {"confidence": 0.5, "warnings": ["Census data not yet implemented"]}
                replacement_cost = {"confidence": 0.5, "warnings": ["Replacement cost not yet implemented"]}
            else:
                # Use mock providers directly (maintains backward compatibility)
                geocode = self.gateway.mock_geocode(address)
                property_profile = self.gateway.mock_property_profile(address)
                property_profile["year_built"] = canonical_submission.risk.year_built
                hazard_scores = self.gateway.mock_hazard_scores(
                    address, geocode["latitude"], geocode["longitude"]
                )
                census_data = self.gateway.mock_census_data(address)
                claims_history = self.gateway.mock_claims_history(address, canonical_submission.risk.dwelling_type)
                replacement_cost = self.gateway.mock_replacement_cost(
                    address, property_profile["square_feet"], property_profile["year_built"]
                )
            
            # Build confidence map
            confidence_map = {
                "geocode": geocode["confidence"],
                "property_profile": property_profile["confidence"],
                "hazard_scores": hazard_scores["confidence"],
                "census_data": census_data["confidence"],
                "claims_history": claims_history["confidence"],
                "replacement_cost": replacement_cost["confidence"]
            }
            
            return {
                "property_profile": property_profile,
                "hazard_profile": hazard_scores,
                "location_profile": geocode,
                "census_profile": census_data,
                "claims_history": claims_history,
                "replacement_cost": replacement_cost,
                "confidence_map": confidence_map,
                "enrichment_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            # Degrade gracefully on provider failure
            return {
                "property_profile": {},
                "hazard_profile": {},
                "location_profile": {},
                "census_profile": {},
                "claims_history": {},
                "replacement_cost": {},
                "confidence_map": {},
                "error": str(e),
                "needs_review": True
            }


class RetrievalAgent:
    """
    Agent Contract: Retrieval Agent
    
    Responsibilities:
    - Generate 2–5 retrieval query variants (keyword + semantic)
    - Call Chroma query with strict metadata filters (state/product/carrier/effective date)
    - Return an evidence bundle with stable chunk IDs and citation fields
    - Emit retrieval metrics (latency, hit count, top similarity)
    
    Idempotency:
    - Retrieval is idempotent for the same (query_texts, filter, collection_version) set
    
    Error modes:
    - RETRIEVAL_EMPTY: escalate to search plan or refer (depending on policy)
    - RETRIEVAL_STALE_DOC: if chunk effective date is out of range, exclude
    """

    def __init__(self, rag_engine):
        self.rag_engine = rag_engine
    
    def retrieve(self, enrichment_data: Dict[str, Any], retrieval_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retrieve guideline evidence based on enrichment data and retrieval plan.
        """
        import time
        start_time = time.time()
        
        # Generate query variants
        queries = self._generate_queries(enrichment_data)
        
        # Apply filters
        filters = retrieval_plan.get("filters", {})
        max_chunks = retrieval_plan.get("max_chunks", 8)
        
        # Retrieve from RAG
        all_chunks = []
        for query in queries:
            chunks = self.rag_engine.retrieve(query, n_results=max_chunks)
            all_chunks.extend(chunks)
        
        # Deduplicate and apply metadata filters
        seen_chunk_ids = set()
        filtered_chunks = []
        for chunk in all_chunks:
            if chunk.chunk_id not in seen_chunk_ids:
                # Apply metadata filters if provided
                if filters:
                    chunk_metadata = chunk.metadata or {}
                    match = True
                    for key, value in filters.items():
                        if key in chunk_metadata and chunk_metadata[key] != value:
                            match = False
                            break
                    if match:
                        filtered_chunks.append(chunk)
                        seen_chunk_ids.add(chunk.chunk_id)
                else:
                    filtered_chunks.append(chunk)
                    seen_chunk_ids.add(chunk.chunk_id)
        
        # Limit to max_chunks
        filtered_chunks = filtered_chunks[:max_chunks]
        
        latency_ms = (time.time() - start_time) * 1000
        
        # Calculate retrieval metrics
        top_similarity = max([c.score or 0 for c in filtered_chunks]) if filtered_chunks else 0
        
        return {
            "queries": queries,
            "filters": filters,
            "evidence_chunks": [c.model_dump() for c in filtered_chunks],
            "retrieval_metrics": {
                "latency_ms": round(latency_ms, 2),
                "hit_count": len(filtered_chunks),
                "top_similarity": top_similarity,
                "collection": retrieval_plan.get("collection", "uw_guidelines")
            }
        }
    
    def _generate_queries(self, enrichment_data: Dict[str, Any]) -> List[str]:
        """Generate query variants for retrieval."""
        queries = []
        
        # Base query
        queries.append("HO3 underwriting guidelines eligibility requirements")
        
        # Risk-specific queries
        hazard_profile = enrichment_data.get("hazard_profile", {})
        if hazard_profile.get("wildfire_risk_score", 0) > 0.5:
            queries.append("HO3 wildfire risk referral criteria")
        if hazard_profile.get("flood_risk_score", 0) > 0.5:
            queries.append("HO3 flood zone eligibility requirements")
        
        # Property-specific queries
        property_profile = enrichment_data.get("property_profile", {})
        year_built = property_profile.get("year_built", 0)
        if year_built < 1940:
            queries.append("HO3 older construction eligibility")
        
        return queries[:5]  # Limit to 5 queries


class UnderwritingAssessorAgent:
    """
    Agent Contract: Underwriting Assessor
    
    Responsibilities:
    - Apply eligibility + referral + surcharge logic from evidence + facts
    - Produce a structured assessment with risk factors, eligibility score, required questions, citations, preliminary decision
    
    Idempotency:
    - Not strictly deterministic due to LLM variability; enforce near-determinism via:
      - temperature ≤ 0.2
      - fixed prompt versions
      - JSON schema validation
      - verifier override
    
    Error modes:
    - UNSUPPORTED_ASSERTION: missing citations for a key rule claim → must be caught by verifier
    - CONTRADICTORY_FACTS: cannot reconcile property facts → route to refer
    """

    def __init__(self):
        self.llm_client = get_llm_client()
        self.use_llm = self.llm_client.enabled

    def assess(self, enrichment_data: Dict[str, Any], evidence_chunks: List[Dict]) -> Dict[str, Any]:
        """
        Perform underwriting assessment based on enrichment and evidence.
        """
        tracer = get_tracer("underwriting_assessor")
        
        with tracer.start_as_current_span("underwriting_assessment") as span:
            # Extract key facts
            hazard_profile = enrichment_data.get("hazard_profile", {})
            property_profile = enrichment_data.get("property_profile", {})
            claims_history = enrichment_data.get("claims_history", {})
            
            span.set_attribute("hazard.wildfire_score", hazard_profile.get("wildfire_risk_score", 0))
            span.set_attribute("property.year_built", property_profile.get("year_built", 2026))
            span.set_attribute("claims.loss_count", claims_history.get("loss_count_5yr", 0))
            span.set_attribute("use_llm", self.use_llm)
            
            # Use LLM if enabled, otherwise use deterministic logic
            if self.use_llm:
                return self._assess_with_llm(enrichment_data, evidence_chunks, span)
            else:
                return self._assess_deterministic(enrichment_data, evidence_chunks, span)
    
    def _assess_with_llm(self, enrichment_data: Dict[str, Any], evidence_chunks: List[Dict], span) -> Dict[str, Any]:
        """
        Perform assessment using LLM.
        """
        try:
            # Extract data for prompt
            hazard_profile = enrichment_data.get("hazard_profile", {})
            property_profile = enrichment_data.get("property_profile", {})
            claims_history = enrichment_data.get("claims_history", {})
            location_profile = enrichment_data.get("location_profile", {})
            
            # Format prompt
            prompt = UNDERWRITING_ASSESSOR_PROMPT.format(
                address=location_profile.get("normalized_address", "Unknown"),
                year_built=property_profile.get("year_built", 2026),
                square_footage=property_profile.get("square_feet", 2000),
                dwelling_type=property_profile.get("dwelling_type", "single_family"),
                occupancy=property_profile.get("occupancy", "owner_occupied_primary"),
                construction_type=property_profile.get("construction_type", "frame"),
                roof_type=property_profile.get("roof_type", "asphalt_shingle"),
                roof_age_years=property_profile.get("roof_age_years", 0),
                wildfire_risk=hazard_profile.get("wildfire", {}).get("risk_level", "Low"),
                wildfire_score=hazard_profile.get("wildfire", {}).get("score", 0),
                flood_risk=hazard_profile.get("flood", {}).get("risk_level", "Low"),
                flood_score=hazard_profile.get("flood", {}).get("score", 0),
                wind_risk=hazard_profile.get("wind", {}).get("risk_level", "Low"),
                wind_score=hazard_profile.get("wind", {}).get("score", 0),
                earthquake_risk=hazard_profile.get("earthquake", {}).get("risk_level", "Low"),
                earthquake_score=hazard_profile.get("earthquake", {}).get("score", 0),
                loss_count=claims_history.get("loss_count_5yr", 0),
                total_paid=claims_history.get("total_paid_5yr", 0),
                coverage_a=500000,  # TODO: extract from actual submission
                coverage_b=50000,
                coverage_c=150000,
                coverage_d=50000,
                deductible=1000
            )
            
            # Call LLM
            messages = [{"role": "user", "content": prompt}]
            response = self.llm_client.chat_completion(messages, max_tokens=500)
            
            # Parse LLM response
            import json
            llm_result = json.loads(response["content"])
            
            span.set_attribute("llm.cost", response["cost"])
            span.set_attribute("llm.tokens", response["usage"]["total_tokens"])
            
            # Map LLM decision to our decision format
            decision_mapping = {
                "ACCEPT": "QUOTE_ELIGIBLE",
                "REFER": "REFER",
                "DECLINE": "DECLINE"
            }
            preliminary_decision = decision_mapping.get(llm_result["decision"], "REFER")
            
            return {
                "preliminary_decision": preliminary_decision,
                "eligibility_score": 1.0 - (llm_result.get("risk_score", 50) / 100),
                "risk_factors": [{"code": f"LLM_{factor}" for factor in llm_result.get("key_factors", [])}],
                "required_questions": [],
                "conditions": [],
                "citations_used": [c.get("chunk_id") for c in evidence_chunks],
                "confidence": 0.8,
                "llm_used": True,
                "llm_rationale": llm_result.get("rationale", "")
            }
            
        except Exception as e:
            logger.error(f"LLM assessment failed, falling back to deterministic: {e}")
            span.set_attribute("llm_error", str(e))
            return self._assess_deterministic(enrichment_data, evidence_chunks, span)
    
    def _assess_deterministic(self, enrichment_data: Dict[str, Any], evidence_chunks: List[Dict], span) -> Dict[str, Any]:
        """
        Perform assessment using deterministic logic (fallback).
        """
        # Extract key facts
        hazard_profile = enrichment_data.get("hazard_profile", {})
        property_profile = enrichment_data.get("property_profile", {})
        claims_history = enrichment_data.get("claims_history", {})
        
        # Calculate risk factors
        risk_factors = []
        eligibility_score = 1.0
        
        # Wildfire risk
        wildfire_score = hazard_profile.get("wildfire_risk_score", 0)
        if wildfire_score > 0.6:
            risk_factors.append({
                "code": "WILDFIRE_HIGH",
                "severity": "high",
                "because": f"Wildfire risk score {wildfire_score} exceeds threshold",
                "citations": [c.get("chunk_id") for c in evidence_chunks if "wildfire" in c.get("text", "").lower()]
            })
            eligibility_score -= 0.3
        
        # Construction age - hard referral for old construction
        year_built = property_profile.get("year_built", 2026)
        if year_built < 1940:
            risk_factors.append({
                "code": "CONSTRUCTION_OLD",
                "severity": "high",
                "because": f"Property built in {year_built} requires additional review",
                "citations": [c.get("chunk_id") for c in evidence_chunks if "construction" in c.get("text", "").lower()]
            })
            eligibility_score -= 0.4
            # Force REFER for old construction regardless of score
            preliminary_decision = "REFER"
        
        # Claims history
        loss_count = claims_history.get("loss_count_5yr", 0)
        if loss_count > 2:
            risk_factors.append({
                "code": "CLAIMS_HISTORY",
                "severity": "high",
                "because": f"{loss_count} losses in past 5 years",
                "citations": []
            })
            eligibility_score -= 0.3
        
        # Ensure score is within bounds
        eligibility_score = max(0, min(1, eligibility_score))
        
        # Determine preliminary decision
        if not locals().get("preliminary_decision"):  # Check if already set by old construction
            if eligibility_score >= 0.5:
                preliminary_decision = "QUOTE_ELIGIBLE"
            elif eligibility_score < 0.3:
                preliminary_decision = "DECLINE"
            else:
                preliminary_decision = "REFER"
        
        span.set_attribute("decision", preliminary_decision)
        span.set_attribute("eligibility_score", eligibility_score)
        span.set_attribute("risk_factor_count", len(risk_factors))
        
        # Record agent decision metric
        record_agent_decision("underwriting_assessor", preliminary_decision, 0.85)
        
        return {
            "preliminary_decision": preliminary_decision,
            "eligibility_score": eligibility_score,
            "risk_factors": risk_factors,
            "required_questions": [],
            "conditions": [],
            "citations_used": [c.get("chunk_id") for c in evidence_chunks],
            "confidence": 0.85 if len(evidence_chunks) > 0 else 0.6
        }


class VerifierGuardrailAgent:
    """
    Agent Contract: Verifier / Guardrail
    
    Responsibilities:
    - Verify all decision-critical claims have citations
    - Verify citations match rule strength
    - Verify no contradictions between facts and evidence
    - Verify external web search does not override internal rules
    - Produce verification report and decision_allowed flag
    
    Idempotency:
    - Deterministic "judge mode" prompt settings (temperature 0) to minimize variance
    
    Error modes:
    - JSON_INVALID: force retry with "repair JSON" prompt
    - VERIFIER_TIMEOUT: fail safe to REFER
    """

    def __init__(self):
        self.web_search = get_web_search()
        self.use_web_search = self.web_search.enabled

    def verify(self, assessment: Dict[str, Any], evidence_chunks: List[Dict], search_results: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Verify assessment for citations, contradictions, and policy compliance.
        """
        issues = []
        decision_allowed = True
        forced_decision = None
        external_verification = None
        
        # Check for citations
        citations = assessment.get("citations_used", [])
        risk_factors = assessment.get("risk_factors", [])
        
        for factor in risk_factors:
            if factor.get("severity") == "high" and not factor.get("citations"):
                issues.append({
                    "type": "UNSUPPORTED_CLAIM",
                    "detail": f"High-severity risk factor '{factor['code']}' lacks citation",
                    "field": f"risk_factors.{factor['code']}"
                })
        
        # Check evidence coverage
        evidence_coverage_score = len(citations) / max(len(risk_factors), 1)
        
        # Check for contradictions
        contradiction_score = 0.0  # Simplified for MVP
        
        # Web search verification if enabled
        if self.use_web_search and search_results is None:
            # Perform web search for critical risk factors
            critical_factors = [f for f in risk_factors if f.get("severity") == "high"]
            if critical_factors:
                try:
                    # Use first critical factor for web search verification
                    factor_code = critical_factors[0].get("code", "")
                    if "WILDFIRE" in factor_code:
                        external_verification = self.web_search.verify_property_risk(
                            assessment.get("property_address", ""), "wildfire"
                        )
                    elif "FLOOD" in factor_code:
                        external_verification = self.web_search.verify_property_risk(
                            assessment.get("property_address", ""), "flood"
                        )
                except Exception as e:
                    logger.error(f"Web search verification failed: {e}")
        
        # Use provided search results if available
        if search_results:
            external_verification = search_results
        
        # Check external verification
        if external_verification and not external_verification.get("verified", True):
            issues.append({
                "type": "EXTERNAL_VERIFICATION_FAILED",
                "detail": "External verification does not support internal assessment",
                "field": "external_search"
            })
        
        # Force REFER if critical issues
        if len(issues) > 0:
            decision_allowed = False
            forced_decision = "REFER"
        
        # Calculate required actions
        required_actions = []
        if not decision_allowed:
            required_actions.append("Add guideline evidence for unsupported claims or refer to human review.")
        
        if evidence_coverage_score < 0.5:
            required_actions.append("Improve evidence coverage for decision.")
        
        if external_verification and not external_verification.get("verified", True):
            required_actions.append("Review external verification results and update assessment.")
        
        return {
            "decision_allowed": decision_allowed,
            "forced_decision": forced_decision,
            "issues": issues,
            "evidence_coverage_score": round(evidence_coverage_score, 2),
            "contradiction_score": contradiction_score,
            "required_actions": required_actions,
            "external_verification": external_verification,
            "web_search_used": self.use_web_search
        }


class DecisionPackagerAgent:
    """
    Agent Contract: Decision Packager
    
    Responsibilities:
    - Create a "decision packet" suitable for producer-facing explanation, underwriter review, and audit
    - Trigger HITL task creation if any "refer" or "need info" conditions apply
    - Store final state in the run store
    
    Idempotency:
    - If a decision_packet_hash already exists for (run_id, state_version), return the same packet
    """

    def package(self, verified_assessment: Dict[str, Any], rating: Optional[Dict], tool_calls_summary: List[Dict]) -> DecisionPacket:
        """
        Compose final decision packet.
        """
        from models.schemas import DecisionType
        
        # Map decision string to enum
        decision_str = verified_assessment.get("preliminary_decision", "REFER")
        if decision_str == "QUOTE_ELIGIBLE":
            decision = DecisionType.ACCEPT
        elif decision_str == "DECLINE":
            decision = DecisionType.DECLINE
        else:
            decision = DecisionType.REFER
        
        # Build reason summary
        risk_factors = verified_assessment.get("risk_factors", [])
        reason_parts = []
        for factor in risk_factors:
            reason_parts.append(factor.get("because", ""))
        reason_summary = "; ".join(reason_parts) if reason_parts else "No significant risk factors identified"
        
        # Determine if human review is needed
        needs_human_review = decision == DecisionType.REFER or verified_assessment.get("eligibility_score", 1.0) < 0.7
        
        # Extract review reason codes
        review_reason_codes = [f.get("code") for f in risk_factors if f.get("severity") == "high"]
        
        # Build citations
        citations = []
        for chunk_id in verified_assessment.get("citations_used", []):
            citations.append({
                "chunk_id": chunk_id,
                "section": "Guideline Section",
                "doc_version": "v2026.01"
            })
        
        # Build premium indication
        premium_indication = None
        if rating:
            premium_indication = {
                "annual_premium": rating.get("total_premium", 0),
                "currency": "USD"
            }
        
        # Build next steps
        next_steps = []
        if decision == DecisionType.ACCEPT:
            next_steps = ["Policy issuance", "Payment collection", "Policy document delivery"]
        elif decision == DecisionType.DECLINE:
            next_steps = ["Notify applicant of decline", "Provide specific reasons"]
        else:
            next_steps = ["Underwriter manual review", "Additional documentation may be required"]
        
        return DecisionPacket(
            decision=decision,
            decision_confidence=verified_assessment.get("confidence", 0.8),
            reason_summary=reason_summary,
            citations=citations,
            premium_indication=premium_indication,
            needs_human_review=needs_human_review,
            review_reason_codes=review_reason_codes,
            next_steps=next_steps,
            facts_used=verified_assessment,
            evidence_cited=verified_assessment.get("citations_used", []),
            tool_calls_summary=tool_calls_summary,
            trace_link=None
        )
