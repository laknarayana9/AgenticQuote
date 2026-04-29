from typing import Dict, Any
from langgraph.graph import StateGraph, END
from models.schemas import WorkflowState, DecisionType
from workflows.nodes import UnderwritingNodes


def create_agentic_underwriting_graph() -> StateGraph:
    """
    Create the enhanced LangGraph workflow with missing-info loop.
    """
    # Initialize nodes
    nodes = UnderwritingNodes()
    
    # Create the graph
    workflow = StateGraph(WorkflowState)
    
    # Add nodes
    workflow.add_node("validate", nodes.validate_submission)
    workflow.add_node("enrich", nodes.enrich_data)
    workflow.add_node("retrieve_guidelines", nodes.retrieve_guidelines)
    workflow.add_node("uw_assess", nodes.assess_underwriting)
    workflow.add_node("citation_guardrail", nodes.apply_citation_guardrail)
    workflow.add_node("rate", nodes.rate_policy)
    workflow.add_node("decide", nodes.make_decision)
    workflow.add_node("handle_missing_info", nodes.handle_missing_info)
    
    # Define the flow
    workflow.set_entry_point("validate")
    
    # Check if validation passes
    def should_continue(state: WorkflowState) -> str:
        if state.missing_info:
            return "missing_info"
        return "enrich"
    
    workflow.add_conditional_edges(
        "validate",
        should_continue,
        {
            "missing_info": "handle_missing_info",
            "enrich": "enrich"
        }
    )
    
    # Handle missing info - check if questions were answered
    def check_missing_info_resolved(state: WorkflowState) -> str:
        # Check if all missing info has been addressed
        if state.missing_info:
            return "still_missing"
        return "resolved"
    
    workflow.add_conditional_edges(
        "handle_missing_info",
        check_missing_info_resolved,
        {
            "still_missing": "decide",  # Still missing info -> refer for manual review
            "resolved": "enrich"  # Info provided -> continue processing
        }
    )
    
    # Linear flow for successful validation
    workflow.add_edge("enrich", "retrieve_guidelines")
    workflow.add_edge("retrieve_guidelines", "uw_assess")
    workflow.add_edge("uw_assess", "citation_guardrail")
    
    # Check if citation guardrail was triggered
    def check_citation_guardrail(state: WorkflowState) -> str:
        if hasattr(state, 'citation_guardrail_triggered') and state.citation_guardrail_triggered:
            return "guardrail_triggered"
        return "guardrail_passed"
    
    workflow.add_conditional_edges(
        "citation_guardrail",
        check_citation_guardrail,
        {
            "guardrail_triggered": "decide",  # Skip rating, go straight to decision
            "guardrail_passed": "rate"
        }
    )
    
    workflow.add_edge("rate", "decide")
    
    # End immediately — HITL pause is signalled at the API layer via missing_info,
    # not by looping the graph (which causes recursion limit errors).
    workflow.add_edge("decide", END)
    
    return workflow


async def run_agentic_underwriting_workflow(submission_data,
                                    additional_answers: Dict[str, Any] = None) -> WorkflowState:
    """
    Run agentic underwriting workflow with given submission data.
    """
    from models.schemas import QuoteSubmission

    # Create graph
    graph = create_agentic_underwriting_graph()
    compiled_graph = graph.compile()

    # Accept either a QuoteSubmission object or a plain dict
    if isinstance(submission_data, QuoteSubmission):
        submission = submission_data
    else:
        submission = QuoteSubmission(**submission_data)
    
    initial_state = WorkflowState(
        quote_submission=submission,
        current_node="start",
        additional_answers=additional_answers or {}
    )
    
    # Run workflow
    result_dict = compiled_graph.invoke(initial_state)
    
    # Convert datetime objects to strings for JSON serialization
    def serialize_datetime(obj):
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        return obj
    
    # Recursively serialize datetime objects
    def serialize_dict(d):
        if isinstance(d, dict):
            return {k: serialize_dict(v) for k, v in d.items()}
        elif isinstance(d, list):
            return [serialize_dict(item) for item in d]
        else:
            return serialize_datetime(d)
    
    result_dict_serialized = serialize_dict(result_dict)
    
    # Convert result back to WorkflowState
    result = WorkflowState(**result_dict_serialized)
    
    return result
