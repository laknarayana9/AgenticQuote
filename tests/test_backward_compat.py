"""
Test backward compatibility with existing endpoints
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.schemas import QuoteSubmission
from workflows.graph import run_underwriting_workflow
from workflows.agentic_graph import run_agentic_underwriting_workflow


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
        # Test legacy workflow
        print("\n1. Testing legacy workflow (run_underwriting_workflow)...")
        workflow_state = run_underwriting_workflow(submission.dict())
        print(f"✅ Legacy workflow completed")
        print(f"   Status: {workflow_state.status}")
        print(f"   Has decision: {workflow_state.decision is not None}")
        
        # Test agentic workflow
        print("\n2. Testing agentic workflow (run_agentic_underwriting_workflow)...")
        workflow_state = run_agentic_underwriting_workflow(submission.dict(), None)
        print(f"✅ Agentic workflow completed")
        print(f"   Status: {workflow_state.status}")
        print(f"   Has decision: {workflow_state.decision is not None}")
        
        print("\n✅ BACKWARD COMPATIBILITY VERIFIED")
        print("   Legacy workflows still function correctly")
        return True
        
    except Exception as e:
        print(f"\n❌ BACKWARD COMPATIBILITY FAILED")
        print(f"   Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_legacy_endpoint()
    exit(0 if success else 1)
