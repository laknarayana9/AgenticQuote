"""
Phase A Workflow using 7 Specialized Agents
Implements the canonical HO3 underwriting workflow with the new agent contracts.
"""
import uuid
from typing import Dict, Any
from datetime import datetime

from models.schemas import HO3Submission, WorkflowState, QuoteSubmission
from workflows.agents import (
    IntakeNormalizerAgent,
    PlannerRouterAgent,
    EnrichmentAgent,
    RetrievalAgent,
    UnderwritingAssessorAgent,
    VerifierGuardrailAgent,
    DecisionPackagerAgent
)
from app.rag_engine import RAGEngine
from tools.rating_tool import RatingTool


class PhaseAWorkflow:
    """
    Phase A workflow using the 7 specialized agents.
    Implements the canonical HO3 underwriting flow.
    """

    def __init__(self):
        # Initialize agents
        self.intake_normalizer = IntakeNormalizerAgent(prompt_version="v1.0")
        self.planner_router = PlannerRouterAgent()
        self.enrichment_agent = EnrichmentAgent()
        self.retrieval_agent = None  # Will be initialized with RAG engine
        self.assessor_agent = UnderwritingAssessorAgent()
        self.verifier_agent = VerifierGuardrailAgent()
        self.decision_packager = DecisionPackagerAgent()

        # Initialize supporting services
        self.rag_engine = RAGEngine()
        self.rag_engine.ingest_documents()
        self.retrieval_agent = RetrievalAgent(self.rag_engine)
        self.rating_tool = RatingTool()

    def run(self, submission_raw: Dict[str, Any]) -> WorkflowState:
        """
        Run the Phase A workflow with a raw HO3 submission.
        """
        # Generate run ID
        run_id = str(uuid.uuid4())
        quote_id = f"Q-2026-{uuid.uuid4().hex[:6].upper()}"

        # Initialize workflow state
        # For backward compatibility, create a QuoteSubmission from the HO3 data
        quote_submission = self._convert_to_quote_submission(submission_raw)
        
        workflow_state = WorkflowState(
            run_id=run_id,
            quote_id=quote_id,
            status="processing",
            quote_submission=quote_submission,
            submission_raw=submission_raw,
            current_node="start"
        )

        try:
            # Step 1: Intake Normalization
            workflow_state.current_node = "intake_normalization"
            normalization_result = self.intake_normalizer.normalize(submission_raw)
            workflow_state.submission_canonical = HO3Submission(**submission_raw)
            workflow_state.missing_info = normalization_result["missing_info"]

            # Step 2: Planning/Routing
            workflow_state.current_node = "planner"
            routing_decision = self.planner_router.route(
                workflow_state.submission_canonical,
                workflow_state.missing_info
            )

            # Check if waiting for info
            if routing_decision["route"] == "waiting_for_info":
                workflow_state.status = "waiting_for_info"
                # Create decision packet for missing info
                questions = normalization_result["questions"]
                decision_packet = self.decision_packager.package(
                    {
                        "preliminary_decision": "REFER",
                        "eligibility_score": 0.5,
                        "risk_factors": [],
                        "required_questions": questions,
                        "citations_used": [],
                        "confidence": 0.7
                    },
                    None,  # No rating yet
                    []
                )
                workflow_state.decision_packet = decision_packet
                return workflow_state

            # Check for hard decline or refer candidates - create decision packets
            if routing_decision["route"] in ["hard_decline_candidate", "hard_refer"]:
                workflow_state.status = "pending_review"
                decision_type = "DECLINE" if routing_decision["route"] == "hard_decline_candidate" else "REFER"
                decision_packet = self.decision_packager.package(
                    {
                        "preliminary_decision": decision_type,
                        "eligibility_score": 0.3,
                        "risk_factors": [{"code": code, "severity": "high", "because": reason, "citations": []} 
                                       for code, reason in zip(routing_decision["reason_codes"], routing_decision["reason_codes"])],
                        "required_questions": [],
                        "citations_used": [],
                        "confidence": 0.8
                    },
                    None,
                    []
                )
                workflow_state.decision_packet = decision_packet
                return workflow_state

            # Step 3: Enrichment
            workflow_state.current_node = "enrichment"
            enrichment_data = self.enrichment_agent.enrich(
                workflow_state.submission_canonical
            )
            workflow_state.enrichment = enrichment_data

            # Step 4: Retrieval
            workflow_state.current_node = "retrieval"
            retrieval_result = self.retrieval_agent.retrieve(
                enrichment_data,
                routing_decision["retrieval_plan"]
            )
            workflow_state.retrieval = retrieval_result

            # Step 5: Underwriting Assessment
            workflow_state.current_node = "assessment"
            assessment_result = self.assessor_agent.assess(
                enrichment_data,
                retrieval_result["evidence_chunks"]
            )
            workflow_state.assessment = assessment_result

            # Step 6: Verification
            workflow_state.current_node = "verification"
            verification_result = self.verifier_agent.verify(
                assessment_result,
                retrieval_result["evidence_chunks"],
                None  # No web search in Phase A
            )
            workflow_state.verification = verification_result

            # Check if verification failed - but still continue to decision packaging
            needs_review = not verification_result["decision_allowed"]
            if needs_review:
                workflow_state.status = "pending_review"
                # Override assessment decision if verification failed
                if verification_result["forced_decision"]:
                    assessment_result["preliminary_decision"] = verification_result["forced_decision"]

            # Step 7: Rating
            workflow_state.current_node = "rating"
            rating_data = self._prepare_rating_data(
                workflow_state.submission_canonical,
                enrichment_data
            )
            rating_result = self.rating_tool(rating_data)
            workflow_state.rating = rating_result

            # Step 8: Decision Packaging
            workflow_state.current_node = "decision_packaging"
            tool_calls_summary = self._extract_tool_calls(workflow_state)
            decision_packet = self.decision_packager.package(
                assessment_result,
                rating_result,
                tool_calls_summary
            )
            workflow_state.decision_packet = decision_packet

            # Set final status
            if decision_packet.needs_human_review:
                workflow_state.status = "pending_review"
            else:
                workflow_state.status = "completed"

            # Log completion
            workflow_state.events.append({
                "event": "workflow_completed",
                "timestamp": datetime.now().isoformat(),
                "decision": decision_packet.decision.value
            })

            return workflow_state

        except Exception as e:
            workflow_state.status = "failed"
            workflow_state.events.append({
                "event": "workflow_error",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            })
            raise

    def _convert_to_quote_submission(self, ho3_data: Dict[str, Any]) -> QuoteSubmission:
        """
        Convert HO3 submission to QuoteSubmission for backward compatibility.
        """
        applicant = ho3_data.get("applicant", {})
        risk = ho3_data.get("risk", {})
        coverage = ho3_data.get("coverage_request", {})

        return QuoteSubmission(
            applicant_name=applicant.get("full_name", ""),
            address=risk.get("property_address", ""),
            property_type=risk.get("dwelling_type", "single_family"),
            coverage_amount=coverage.get("coverage_a", 500000),
            construction_year=risk.get("year_built"),
            square_footage=None,
            roof_type=None,
            foundation_type=None,
            additional_info=None
        )

    def _create_need_info_decision(self, questions: list) -> Dict[str, Any]:
        """Create a decision for missing information."""
        from models.schemas import DecisionType

        return {
            "decision": DecisionType.REFER,
            "rationale": "Additional information required to complete underwriting",
            "citations": [],
            "required_questions": questions,
            "next_steps": ["Provide required information and resubmit"]
        }

    def _create_refer_decision(self, reasons: list) -> Dict[str, Any]:
        """Create a referral decision."""
        from models.schemas import DecisionType

        return {
            "decision": DecisionType.REFER,
            "rationale": "; ".join(reasons),
            "citations": [],
            "required_questions": [],
            "next_steps": ["Manual underwriter review required"]
        }

    def _prepare_rating_data(self, submission: HO3Submission, enrichment: Dict) -> Dict[str, Any]:
        """Prepare data for rating engine."""
        property_profile = enrichment.get("property_profile", {})
        hazard_profile = enrichment.get("hazard_profile", {})

        return {
            "coverage_amount": submission.coverage_request.coverage_a,
            "property_type": submission.risk.dwelling_type,
            "hazard_scores": {
                "wildfire_risk": hazard_profile.get("wildfire_risk_score", 0),
                "flood_risk": hazard_profile.get("flood_risk_score", 0),
                "wind_risk": hazard_profile.get("wind_risk_score", 0),
                "earthquake_risk": hazard_profile.get("earthquake_risk_score", 0)
            },
            "construction_year": submission.risk.year_built
        }

    def _extract_tool_calls(self, workflow_state: WorkflowState) -> list:
        """Extract tool calls from workflow state."""
        tool_calls = []
        
        if workflow_state.enrichment:
            tool_calls.append({
                "tool": "enrichment_agent",
                "timestamp": datetime.now().isoformat(),
                "status": "completed"
            })
        
        if workflow_state.retrieval:
            tool_calls.append({
                "tool": "retrieval_agent",
                "timestamp": datetime.now().isoformat(),
                "status": "completed",
                "metrics": workflow_state.retrieval.get("retrieval_metrics", {})
            })
        
        if workflow_state.assessment:
            tool_calls.append({
                "tool": "underwriting_assessor",
                "timestamp": datetime.now().isoformat(),
                "status": "completed"
            })
        
        if workflow_state.verification:
            tool_calls.append({
                "tool": "verifier_guardrail",
                "timestamp": datetime.now().isoformat(),
                "status": "completed"
            })
        
        return tool_calls


def run_phase_a_workflow(submission_raw: Dict[str, Any]) -> WorkflowState:
    """
    Convenience function to run the Phase A workflow.
    """
    workflow = PhaseAWorkflow()
    return workflow.run(submission_raw)
