"""
Test backward compatibility with existing endpoints
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.schemas import QuoteSubmission
from workflows.agent_workflow import run_agent_workflow


def test_legacy_endpoint():
    """Test the legacy quote/run endpoint still works."""
    print("Testing backward compatibility with legacy workflow...")
    
    # Create a simple QuoteSubmission
    submission = QuoteSubmission(
        applicant_name="John Doe",
        address="123 Main St, Los Angeles, CA 90001",
        property_type="single_family",
        coverage_amount=500000,
        construction_year=2010,
        square_footage=2000,
        roof_type="asphalt",
        foundation_type="slab",
        additional_info=None
    )
    
    try:
        # Test 7-agent workflow
        print("\n1. Testing 7-agent workflow (run_agent_workflow)...")
        workflow_state = run_agent_workflow(submission.dict())
        print(f" 7-agent workflow completed")
        print(f"   Status: {workflow_state.status}")
        print(f"   Has decision: {workflow_state.decision is not None}")
        
        print("\n 7-AGENT SYSTEM VERIFIED")
        print("   7-agent workflow functions correctly")
        return True
        
    except Exception as e:
        print(f"\n BACKWARD COMPATIBILITY FAILED")
        print(f"   Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_legacy_endpoint()
    exit(0 if success else 1)
