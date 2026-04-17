"""
Test script to run 10 Phase A demo scenarios
Tests the complete Phase A workflow with the 7 specialized agents.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workflows.phase_a_graph import run_phase_a_workflow
from tests.demo_scenarios import get_all_scenarios, create_submission_from_scenario


def test_scenario(scenario, index):
    """Test a single scenario against the Phase A workflow."""
    print(f"\n{'='*80}")
    print(f"Testing Scenario {index}: {scenario['name']}")
    print(f"Description: {scenario['description']}")
    print(f"Expected Decision: {scenario['expected_decision']}")
    print(f"{'='*80}")
    
    try:
        # Create submission from scenario
        submission = create_submission_from_scenario(scenario)
        
        # Run Phase A workflow
        workflow_state = run_phase_a_workflow(submission.model_dump())
        
        # Check results
        print(f"\n✅ Workflow Status: {workflow_state.status}")
        
        if workflow_state.decision_packet:
            actual_decision = workflow_state.decision_packet.decision.value
            print(f"✅ Actual Decision: {actual_decision}")
            print(f"✅ Reason Summary: {workflow_state.decision_packet.reason_summary}")
            print(f"✅ Confidence: {workflow_state.decision_packet.decision_confidence}")
            print(f"✅ Citations: {len(workflow_state.decision_packet.citations)}")
            print(f"✅ Needs Human Review: {workflow_state.decision_packet.needs_human_review}")
            
            # Check if decision matches expected
            if actual_decision == scenario['expected_decision']:
                print(f"✅ PASS: Decision matches expected ({scenario['expected_decision']})")
                result = True
            else:
                print(f"❌ FAIL: Expected {scenario['expected_decision']}, got {actual_decision}")
                result = False
        else:
            print(f"❌ FAIL: No decision packet generated")
            result = False
            
        print(f"DEBUG: Returning {result}")
        return result
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        print(f"DEBUG: Returning False due to exception")
        return False


def main():
    """Run all 10 demo scenarios."""
    print("\n" + "="*80)
    print("PHASE A DEMO SCENARIO TESTING")
    print("="*80)
    
    scenarios = get_all_scenarios()
    results = []
    
    for i, scenario in enumerate(scenarios, 1):
        passed = test_scenario(scenario, i)
        results.append({
            "scenario": scenario['name'],
            "expected": scenario['expected_decision'],
            "passed": passed
        })
        # Flush to ensure output is captured
        import sys
        sys.stdout.flush()
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed_count = sum(1 for r in results if r['passed'])
    total_count = len(results)
    
    print(f"\nTotal Scenarios: {total_count}")
    print(f"Passed: {passed_count}")
    print(f"Failed: {total_count - passed_count}")
    print(f"Success Rate: {passed_count/total_count*100:.1f}%")
    
    print("\nDetailed Results:")
    for result in results:
        status = "✅ PASS" if result['passed'] else "❌ FAIL"
        print(f"  {status}: {result['scenario']} (Expected: {result['expected']})")
    
    print("\n" + "="*80)
    
    if passed_count == total_count:
        print("✅ ALL SCENARIOS PASSED - Phase A is ready for demo!")
        return 0
    else:
        print("❌ SOME SCENARIOS FAILED - Review and fix issues")
        return 1


if __name__ == "__main__":
    exit(main())
