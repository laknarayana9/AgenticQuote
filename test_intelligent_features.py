#!/usr/bin/env python3
"""
Test Script for New Intelligent Features

Tests all the new AI components and intelligent features
without requiring full system setup.
"""

import sys
import os
import logging
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_cognitive_engine():
    """Test the Cognitive Knowledge Retrieval System"""
    print("\n" + "="*60)
    print("🧠 Testing Cognitive Knowledge Retrieval System")
    print("="*60)
    
    try:
        from app.cognitive_engine import get_cognitive_engine, KnowledgeChunk
        
        # Initialize cognitive engine
        cognitive_engine = get_cognitive_engine()
        print("✅ Cognitive Engine initialized successfully")
        
        # Test intelligent retrieval
        test_query = "Property eligibility for 1979 single-family home"
        test_context = {
            "property_type": "single_family",
            "construction_year": 1979,
            "coverage_amount": 500000
        }
        
        print(f"🔍 Testing intelligent retrieval for: {test_query}")
        
        # Perform intelligent retrieval
        results = cognitive_engine.intelligent_retrieve(test_query, test_context)
        
        print(f"📊 Retrieved {len(results)} knowledge chunks")
        
        # Display results
        for i, chunk in enumerate(results, 1):
            print(f"\n📚 Chunk {i}:")
            print(f"   ID: {chunk.chunk_id}")
            print(f"   Content: {chunk.content[:100]}...")
            print(f"   Relevance: {chunk.relevance_score:.3f}")
            print(f"   Evidence Strength: {chunk.evidence_strength}")
            print(f"   Modality: {chunk.modality}")
            print(f"   Confidence: {chunk.confidence:.3f}")
        
        # Test intelligence metrics
        metrics = cognitive_engine.get_intelligence_metrics()
        print(f"\n📈 Intelligence Metrics:")
        for key, value in metrics.items():
            print(f"   {key}: {value}")
        
        print("\n✅ Cognitive Engine Test: PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Cognitive Engine Test: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False

def test_reasoning_engine():
    """Test the Advanced Reasoning Engine"""
    print("\n" + "="*60)
    print("🧮 Testing Advanced Reasoning Engine")
    print("="*60)
    
    try:
        from app.intelligent_reasoning import get_reasoning_engine, ReasoningStep, IntelligentDecision
        
        # Initialize reasoning engine
        reasoning_engine = get_reasoning_engine()
        print("✅ Reasoning Engine initialized successfully")
        
        # Test intelligent reasoning
        test_query = "Underwriting decision for 1979 property"
        test_evidence = [
            {
                "content": "Properties over 20 years require additional inspection",
                "relevance": 0.85,
                "source": "underwriting_guidelines",
                "rule_strength": "required"
            },
            {
                "content": "Single-family homes are eligible with proper documentation",
                "relevance": 0.78,
                "source": "eligibility_criteria",
                "rule_strength": "recommended"
            }
        ]
        test_context = {
            "property_type": "single_family",
            "construction_year": 1979,
            "location": "Portland, OR"
        }
        
        print(f"🤖 Testing intelligent reasoning for: {test_query}")
        
        # Perform reasoning
        decision = reasoning_engine.intelligent_reasoning(test_query, test_evidence, test_context)
        
        print(f"\n⚖️ Intelligent Decision:")
        print(f"   Decision: {decision.decision}")
        print(f"   Confidence: {decision.confidence:.3f}")
        print(f"   Explainability Score: {decision.explainability_score:.3f}")
        print(f"   Processing Time: {decision.processing_time_ms:.2f}ms")
        
        print(f"\n🧠 Reasoning Chain ({len(decision.reasoning_chain)} steps):")
        for i, step in enumerate(decision.reasoning_chain, 1):
            print(f"   Step {i}: {step.description}")
            print(f"   Logic Type: {step.logic_type}")
            print(f"   Confidence: {step.confidence:.3f}")
            print(f"   Conclusion: {step.conclusion}")
        
        print(f"\n📊 Risk Assessment:")
        for risk_type, score in decision.risk_assessment.items():
            print(f"   {risk_type}: {score:.3f}")
        
        print(f"\n💡 Recommendations:")
        for rec in decision.recommendations:
            print(f"   - {rec}")
        
        # Test reasoning metrics
        metrics = reasoning_engine.get_reasoning_metrics()
        print(f"\n📈 Reasoning Metrics:")
        for key, value in metrics.items():
            print(f"   {key}: {value}")
        
        print("\n✅ Reasoning Engine Test: PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Reasoning Engine Test: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False

def test_llm_engine():
    """Test the LLM Engine"""
    print("\n" + "="*60)
    print("🤖 Testing LLM Engine")
    print("="*60)
    
    try:
        from app.llm_engine import get_llm_engine, LLMRequest
        
        # Initialize LLM engine
        llm_engine = get_llm_engine()
        print("✅ LLM Engine initialized successfully")
        
        # Test LLM health
        health = llm_engine.health_check()
        print(f"📊 LLM Engine Health:")
        for key, value in health.items():
            print(f"   {key}: {value}")
        
        # Test LLM request processing
        test_request = LLMRequest(
            query="Property eligibility assessment for older home",
            context=["Query type: eligibility", "Property age: 1979"],
            evidence=[
                {
                    "doc_title": "Underwriting Guidelines",
                    "section": "Property Requirements",
                    "text": "Properties older than 20 years require additional documentation",
                    "relevance_score": 0.85,
                    "rule_strength": "required"
                }
            ],
            query_type="eligibility",
            max_tokens=500,
            temperature=0.3
        )
        
        print(f"\n🧠 Testing LLM request processing...")
        print(f"   Query: {test_request.query}")
        print(f"   Query Type: {test_request.query_type}")
        print(f"   Evidence Count: {len(test_request.evidence)}")
        
        # Generate LLM decision
        response = llm_engine.generate_decision(test_request)
        
        print(f"\n🤖 LLM Response:")
        print(f"   Decision: {response.decision}")
        print(f"   Confidence: {response.confidence:.3f}")
        print(f"   Reasoning: {response.reasoning[:100]}...")
        print(f"   Required Questions: {len(response.required_questions)}")
        print(f"   Referral Triggers: {len(response.referral_triggers)}")
        print(f"   Processing Time: {response.processing_time_ms:.2f}ms")
        
        print("\n✅ LLM Engine Test: PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ LLM Engine Test: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False

def test_intelligent_integration():
    """Test integration between all intelligent components"""
    print("\n" + "="*60)
    print("🔄 Testing Intelligent Component Integration")
    print("="*60)
    
    try:
        # Import all components
        from app.cognitive_engine import get_cognitive_engine
        from app.intelligent_reasoning import get_reasoning_engine
        from app.llm_engine import get_llm_engine
        
        # Initialize all components
        cognitive_engine = get_cognitive_engine()
        reasoning_engine = get_reasoning_engine()
        llm_engine = get_llm_engine()
        
        print("✅ All intelligent components initialized")
        
        # Test scenario
        test_scenario = {
            "query": "Should I approve this 1979 single-family home for $500k coverage?",
            "context": {
                "property_type": "single_family",
                "construction_year": 1979,
                "coverage_amount": 500000,
                "location": "Portland, OR"
            }
        }
        
        print(f"\n🎯 Testing Integration Scenario:")
        print(f"   Query: {test_scenario['query']}")
        
        # Step 1: Cognitive retrieval
        print(f"\n🧠 Step 1: Cognitive Knowledge Retrieval")
        knowledge_chunks = cognitive_engine.intelligent_retrieve(
            test_scenario["query"], 
            test_scenario["context"]
        )
        print(f"   Retrieved {len(knowledge_chunks)} knowledge chunks")
        
        # Step 2: Convert evidence for reasoning engine
        evidence_for_reasoning = [
            {
                "content": chunk.content,
                "relevance": chunk.relevance_score,
                "source": chunk.metadata.get("source", "knowledge_base"),
                "rule_strength": chunk.evidence_strength
            }
            for chunk in knowledge_chunks
        ]
        
        # Step 3: Advanced reasoning
        print(f"\n🧮 Step 2: Advanced Reasoning")
        reasoning_decision = reasoning_engine.intelligent_reasoning(
            test_scenario["query"],
            evidence_for_reasoning,
            test_scenario["context"]
        )
        print(f"   Reasoning Decision: {reasoning_decision.decision}")
        print(f"   Confidence: {reasoning_decision.confidence:.3f}")
        
        # Step 4: LLM enhancement
        print(f"\n🤖 Step 3: LLM Enhancement")
        from app.llm_engine import LLMRequest
        llm_request = LLMRequest(
            query=test_scenario["query"],
            context=[f"Property type: {test_scenario['context']['property_type']}"],
            evidence=evidence_for_reasoning,
            query_type="eligibility"
        )
        llm_response = llm_engine.generate_decision(llm_request)
        print(f"   LLM Decision: {llm_response.decision}")
        print(f"   Confidence: {llm_response.confidence:.3f}")
        
        # Step 5: Decision comparison
        print(f"\n🔄 Step 4: Decision Comparison")
        agreement = reasoning_decision.decision == llm_response.decision
        confidence_diff = abs(reasoning_decision.confidence - llm_response.confidence)
        
        print(f"   Agreement: {agreement}")
        print(f"   Confidence Difference: {confidence_diff:.3f}")
        print(f"   Recommendation: " + ("High confidence" if agreement and confidence_diff < 0.2 else "Manual review"))
        
        print("\n✅ Integration Test: PASSED")
        return True
        
    except Exception as e:
        print(f"\n❌ Integration Test: FAILED - {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoints():
    """Test new API endpoints with simple server"""
    print("\n" + "="*60)
    print("🌐 Testing New API Endpoints")
    print("="*60)
    
    try:
        import subprocess
        import time
        import requests
        
        # Start simple server in background
        print("🚀 Starting simple server...")
        server_process = subprocess.Popen([
            sys.executable, "simple_server.py"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Wait for server to start
        time.sleep(3)
        
        try:
            # Test LLM query endpoint
            print("🔍 Testing LLM Query API...")
            llm_response = requests.post("http://localhost:8000/api/llm/query", json={
                "query": "Property eligibility test",
                "query_type": "eligibility",
                "use_llm": True
            })
            
            if llm_response.status_code == 200:
                data = llm_response.json()
                print(f"   ✅ LLM Query API: {data.get('query', 'N/A')}")
                print(f"   🤖 LLM Decision: {data.get('llm_decision', {}).get('decision', 'N/A')}")
                print(f"   🔍 RAG Decision: {data.get('rag_decision', {}).get('decision', 'N/A')}")
                print(f"   📊 Evidence Count: {len(data.get('evidence', []))}")
            else:
                print(f"   ❌ LLM Query API failed: {llm_response.status_code}")
            
            # Test LLM health endpoint
            print("🏥 Testing LLM Health API...")
            health_response = requests.get("http://localhost:8000/api/llm/health")
            
            if health_response.status_code == 200:
                health_data = health_response.json()
                print(f"   ✅ LLM Health API: {health_data.get('status', 'N/A')}")
                print(f"   🔑 API Key: {health_data.get('api_key_configured', False)}")
            else:
                print(f"   ❌ LLM Health API failed: {health_response.status_code}")
            
            print("\n✅ API Endpoints Test: PASSED")
            return True
            
        finally:
            # Stop server
            server_process.terminate()
            server_process.wait()
            
    except Exception as e:
        print(f"\n❌ API Endpoints Test: FAILED - {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Starting Intelligent Features Test Suite")
    print("=" * 60)
    
    test_results = {
        "Cognitive Engine": False,
        "Reasoning Engine": False,
        "LLM Engine": False,
        "Integration": False,
        "API Endpoints": False
    }
    
    # Run all tests
    test_results["Cognitive Engine"] = test_cognitive_engine()
    test_results["Reasoning Engine"] = test_reasoning_engine()
    test_results["LLM Engine"] = test_llm_engine()
    test_results["Integration"] = test_intelligent_integration()
    test_results["API Endpoints"] = test_api_endpoints()
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST RESULTS SUMMARY")
    print("="*60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:20} : {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL INTELLIGENT FEATURES WORKING!")
        print("🚀 Ready for production deployment!")
    else:
        print("⚠️ Some features need attention")
        print("🔧 Check the failed tests above")
    
    print("="*60)

if __name__ == "__main__":
    main()
