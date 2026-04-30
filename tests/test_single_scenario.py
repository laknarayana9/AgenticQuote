"""
Test single scenario to debug
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workflows.agent_workflow import run_agent_workflow
from tests.demo_scenarios import get_scenario, create_submission_from_scenario

# Test Scenario 9
scenario = get_scenario(9)
print(f"Testing Scenario 9: {scenario['name']}")
print(f"Expected Decision: {scenario['expected_decision']}")

submission = create_submission_from_scenario(scenario)
workflow_state = run_agent_workflow(submission.model_dump())

print(f"\nWorkflow Status: {workflow_state.status}")
print(f"Has decision_packet: {workflow_state.decision_packet is not None}")

if workflow_state.decision_packet:
    actual_decision = workflow_state.decision_packet.get('decision', 'UNKNOWN')
    print(f"Actual Decision: {actual_decision}")
    print(f"Reason: {workflow_state.decision_packet.get('reason_summary', 'No reason provided')}")
    print(f"Match: {actual_decision == scenario['expected_decision']}")
else:
    print("No decision packet")
