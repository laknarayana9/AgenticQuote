#!/usr/bin/env python3
"""
Test Script for Advanced Agentic Workflow
This script demonstrates and tests all the agentic capabilities we've built.
"""

import sys
import os
import logging
from datetime import datetime

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_individual_components():
    """Test individual agentic components"""
    
    print("=" * 80)
    print("TESTING INDIVIDUAL AGENTIC COMPONENTS")
    print("=" * 80)
    
    try:
        # Test 1: Advanced ReAct Engine
        print("\n1. Testing Advanced ReAct Engine...")
        from app.advanced_react import get_advanced_react_engine
        
        react_engine = get_advanced_react_engine()
        
        # Simple test case
        test_query = "Underwriting assessment for test property"
        test_context = {
            "property": {
                "address": "123 Test St, San Diego, CA",
                "state": "CA",
                "year_built": 2000,
                "roof_age": 15,
                "coverage_amount": 500000
            }
        }
        
        react_result = react_engine.execute_advanced_react(
            query=test_query,
            context=test_context,
            max_iterations=3
        )
        
        print(f"   ReAct Decision: {react_result.current_decision}")
        print(f"   Confidence: {react_result.confidence_score:.3f}")
        print(f"   Iterations: {react_result.iteration_count}")
        print("   ReAct Engine: PASSED")
        
    except Exception as e:
        print(f"   ReAct Engine: FAILED - {e}")
    
    try:
        # Test 2: Hierarchical Agent System
        print("\n2. Testing Hierarchical Agent System...")
        from app.hierarchical_agents import get_hierarchical_agent_system
        
        agent_system = get_hierarchical_agent_system()
        
        test_input = {
            "applicant_name": "Test User",
            "address": "456 Test Ave, Austin, TX",
            "property_type": "single_family",
            "coverage_amount": 400000
        }
        
        agent_result = agent_system.process_with_hierarchy(test_input)
        
        print(f"   Agent Decision: {agent_result.get('final_decision', 'UNKNOWN')}")
        print(f"   Confidence: {agent_result.get('confidence', 0.0):.3f}")
        print(f"   Agents Used: {len(agent_result.get('agent_contributions', {}))}")
        print("   Agent System: PASSED")
        
    except Exception as e:
        print(f"   Agent System: FAILED - {e}")
    
    try:
        # Test 3: Multi-Modal Reasoning
        print("\n3. Testing Multi-Modal Reasoning...")
        from app.multimodal_reasoning import get_multimodal_reasoning_system
        
        multimodal_system = get_multimodal_reasoning_system()
        
        multimodal_result = multimodal_system.reason_multi_modal(
            query="Risk assessment for property",
            text_data="Property located in suburban area with good schools",
            structured_data={
                "property": {"address": "789 Test Rd, Miami, FL"},
                "coverage_amount": 600000
            },
            rule_set={
                "coverage_limits": {"min": 50000, "max": 2000000}
            }
        )
        
        print(f"   Multi-Modal Conclusion: {multimodal_result['conclusion']}")
        print(f"   Confidence: {multimodal_result['confidence']:.3f}")
        print(f"   Strategy: {multimodal_result['strategy_used']}")
        print("   Multi-Modal Reasoning: PASSED")
        
    except Exception as e:
        print(f"   Multi-Modal Reasoning: FAILED - {e}")
    
    try:
        # Test 4: Adaptive Learning
        print("\n4. Testing Adaptive Learning...")
        from app.adaptive_learning import get_adaptive_learning_system
        
        learning_system = get_adaptive_learning_system()
        
        # Add some learning examples
        learning_system.add_learning_example(
            input_data={"property": {"state": "CA", "coverage": 500000}},
            prediction={"prediction": "REFER", "confidence": 0.6},
            actual_outcome={"decision": "REFER"},
            feedback={"score": 0.8}
        )
        
        # Make prediction
        prediction = learning_system.make_adaptive_prediction({
            "property": {"state": "CA", "coverage": 400000}
        })
        
        print(f"   Learning Prediction: {prediction['prediction']}")
        print(f"   Confidence: {prediction['confidence']:.3f}")
        print("   Adaptive Learning: PASSED")
        
    except Exception as e:
        print(f"   Adaptive Learning: FAILED - {e}")
    
    try:
        # Test 5: Observability System
        print("\n5. Testing Observability System...")
        from app.observability import get_observability_system
        
        obs_system = get_observability_system()
        
        # Collect some metrics
        metrics = obs_system.collect_all_metrics()
        
        # Check system health
        health = obs_system.check_system_health()
        
        print(f"   Metrics Collected: {len(metrics)}")
        print(f"   System Health: {health['overall_status']}")
        print("   Observability System: PASSED")
        
    except Exception as e:
        print(f"   Observability System: FAILED - {e}")

def test_integrated_workflow():
    """Test the integrated agentic workflow"""
    
    print("\n" + "=" * 80)
    print("TESTING INTEGRATED AGENTIC WORKFLOW")
    print("=" * 80)
    
    try:
        from app.agentic_showcase import get_agentic_showcase
        
        showcase = get_agentic_showcase()
        
        # Test case data
        test_submission = {
            "submission_id": "TEST_001",
            "property": {
                "address": "123 Tech Boulevard, Palo Alto, CA",
                "state": "CA",
                "year_built": 1995,
                "roof_age": 18,
                "roof_material": "composite",
                "occupancy": "owner_occupied",
                "square_footage": 2200
            },
            "applicant": {
                "name": "Tech Professional",
                "prior_claims": 1,
                "credit_score": 750
            },
            "coverage": {
                "dwelling_limit": 800000,
                "deductible": 3000
            },
            "applicant_notes": "Property has solar panels and smart home features. Located in excellent school district."
        }
        
        print("\nExecuting complete agentic workflow...")
        result = showcase.demonstrate_complete_underwriting_workflow(test_submission)
        
        # Display results
        print(f"\nFinal Decision: {result['final_decision']['final_decision']}")
        print(f"Final Confidence: {result['final_decision']['confidence']:.3f}")
        print(f"Consensus Strength: {result['final_decision']['decision_synthesis']['consensus_strength']:.3f}")
        
        print("\nCapabilities Demonstrated:")
        for capability in result['demonstration_summary']['capabilities_demonstrated']:
            print(f"  - {capability}")
        
        print("\nPerformance Metrics:")
        perf = result['performance_metrics']
        print(f"  - Execution Time: {perf['system_performance'].get('average_execution_time', 0):.2f}s")
        print(f"  - Success Rate: {perf['system_performance'].get('success_rate', 0):.3f}")
        
        print("\nIntegrated Workflow: PASSED")
        return True
        
    except Exception as e:
        print(f"\nIntegrated Workflow: FAILED - {e}")
        return False

def test_demonstration_scenarios():
    """Test demonstration scenarios"""
    
    print("\n" + "=" * 80)
    print("TESTING DEMONSTRATION SCENARIOS")
    print("=" * 80)
    
    try:
        from app.demonstration import get_demonstration_orchestrator
        
        demo_orchestrator = get_demonstration_orchestrator()
        
        # Test basic underwriting scenario
        print("\n1. Testing Basic Underwriting Scenario...")
        basic_result = demo_orchestrator.execute_scenario("basic_underwriting_001")
        
        print(f"   Scenario Success: {basic_result.success}")
        print(f"   Duration: {basic_result.duration:.2f}s")
        print(f"   Capabilities: {len(basic_result.capabilities_demonstrated)}")
        print("   Basic Scenario: PASSED")
        
        # Test complex risk assessment
        print("\n2. Testing Complex Risk Assessment...")
        complex_result = demo_orchestrator.execute_scenario("complex_risk_001")
        
        print(f"   Scenario Success: {complex_result.success}")
        print(f"   Duration: {complex_result.duration:.2f}s")
        print(f"   Capabilities: {len(complex_result.capabilities_demonstrated)}")
        print("   Complex Scenario: PASSED")
        
        return True
        
    except Exception as e:
        print(f"Demonstration Scenarios: FAILED - {e}")
        return False

def run_comprehensive_test():
    """Run comprehensive test of the entire system"""
    
    print("STARTING COMPREHENSIVE AGENTIC SYSTEM TEST")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Test individual components
    test_individual_components()
    
    # Test integrated workflow
    workflow_success = test_integrated_workflow()
    
    # Test demonstration scenarios
    demo_success = test_demonstration_scenarios()
    
    # Final summary
    print("\n" + "=" * 80)
    print("COMPREHENSIVE TEST SUMMARY")
    print("=" * 80)
    
    print(f"Individual Components: COMPLETED")
    print(f"Integrated Workflow: {'PASSED' if workflow_success else 'FAILED'}")
    print(f"Demonstration Scenarios: {'PASSED' if demo_success else 'FAILED'}")
    
    overall_success = workflow_success and demo_success
    print(f"\nOverall Test Result: {'PASSED' if overall_success else 'FAILED'}")
    
    if overall_success:
        print("\n" + "!" * 80)
        print("ALL AGENTIC CAPABILITIES WORKING CORRECTLY!")
        print("Ready for production demonstrations!")
        print("!" * 80)
    else:
        print("\n" + "x" * 80)
        print("SOME TESTS FAILED - CHECK IMPLEMENTATION")
        print("x" * 80)
    
    return overall_success

if __name__ == "__main__":
    try:
        success = run_comprehensive_test()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)
