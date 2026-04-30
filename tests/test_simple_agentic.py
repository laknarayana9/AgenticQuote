#!/usr/bin/env python3
"""
Simple test for agentic workflow - focused on demonstrating key capabilities
"""

import sys
import os
import logging

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_basic_functionality():
    """Test basic functionality of agentic systems"""
    
    print("=" * 60)
    print("SIMPLE AGENTIC SYSTEMS TEST")
    print("=" * 60)
    
    # Test 1: ReAct Engine
    print("\n1. Testing ReAct Engine...")
    try:
        from app.advanced_react import get_advanced_react_engine
        react_engine = get_advanced_react_engine()
        
        result = react_engine.execute_advanced_react(
            query="Basic underwriting test",
            context={"property": {"address": "123 Test St", "state": "CA"}},
            max_iterations=2
        )
        
        print(f"   Decision: {result.current_decision}")
        print(f"   Confidence: {result.confidence_score:.3f}")
        print("   ReAct Engine: WORKING")
        
    except Exception as e:
        print(f"   ReAct Engine: ERROR - {e}")
    
    # Test 2: Agent System
    print("\n2. Testing Agent System...")
    try:
        from app.hierarchical_agents import get_hierarchical_agent_system
        agent_system = get_hierarchical_agent_system()
        
        result = agent_system.process_with_hierarchy({
            "applicant_name": "Test User",
            "address": "456 Test Ave",
            "coverage_amount": 400000
        })
        
        print(f"   Decision: {result.get('final_decision', 'UNKNOWN')}")
        print(f"   Confidence: {result.get('confidence', 0.0):.3f}")
        print("   Agent System: WORKING")
        
    except Exception as e:
        print(f"   Agent System: ERROR - {e}")
    
    # Test 3: Multi-Modal Reasoning
    print("\n3. Testing Multi-Modal Reasoning...")
    try:
        from app.multimodal_reasoning import get_multimodal_reasoning_system, ReasoningStrategy
        multimodal_system = get_multimodal_reasoning_system()
        
        result = multimodal_system.reason_multi_modal(
            query="Test analysis",
            text_data="Test property description",
            structured_data={"property": {"value": 500000}},
            rule_set={"min_coverage": 100000},
            strategy=ReasoningStrategy.WEIGHTED_FUSION
        )
        
        print(f"   Conclusion: {result['conclusion']}")
        print(f"   Confidence: {result['confidence']:.3f}")
        print("   Multi-Modal Reasoning: WORKING")
        
    except Exception as e:
        print(f"   Multi-Modal Reasoning: ERROR - {e}")
    
    # Test 4: Adaptive Learning
    print("\n4. Testing Adaptive Learning...")
    try:
        from app.adaptive_learning import get_adaptive_learning_system
        learning_system = get_adaptive_learning_system()
        
        # Add example
        learning_system.add_learning_example(
            input_data={"property": {"state": "CA"}},
            prediction={"prediction": "REFER", "confidence": 0.6},
            actual_outcome={"decision": "REFER"},
            feedback={"score": 0.8}
        )
        
        # Make prediction
        prediction = learning_system.make_adaptive_prediction({"property": {"state": "CA"}})
        
        print(f"   Prediction: {prediction['prediction']}")
        print(f"   Confidence: {prediction['confidence']:.3f}")
        print("   Adaptive Learning: WORKING")
        
    except Exception as e:
        print(f"   Adaptive Learning: ERROR - {e}")
    
    # Test 5: Observability
    print("\n5. Testing Observability System...")
    try:
        from app.observability import get_observability_system
        obs_system = get_observability_system()
        
        health = obs_system.check_system_health()
        dashboard = obs_system.get_dashboard_data()
        
        print(f"   System Health: {health['overall_status']}")
        print(f"   Active Alerts: {len(dashboard.get('active_alerts', []))}")
        print("   Observability System: WORKING")
        
    except Exception as e:
        print(f"   Observability System: ERROR - {e}")
    
    print("\n" + "=" * 60)
    print("SIMPLE TEST COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    test_basic_functionality()
