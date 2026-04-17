"""
Test Phase C Multi-Agent Scenarios
Tests multi-agent collaboration, memory, learning, and conflict resolution.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workflows.multi_agent import get_multi_agent_orchestrator, AgentRole
from agents.memory import get_agent_memory_manager, MemoryType
from agents.learning import get_agent_learning_manager, FeedbackType
from agents.performance import get_agent_performance_manager
from agents.specialization import get_agent_specialization, RiskType
from agents.collaboration import get_agent_communication, MessageType
from agents.conflict_resolution import get_agent_conflict_resolver


def test_multi_agent_collaboration():
    """Test multi-agent collaboration framework."""
    print("\n" + "="*80)
    print("TEST: Multi-Agent Collaboration")
    print("="*80)
    
    orchestrator = get_multi_agent_orchestrator()
    
    # Create mock agents
    class MockAgent:
        def __init__(self, agent_id):
            self.agent_id = agent_id
        
        def assess(self, enrichment_data, evidence_chunks):
            return {
                "preliminary_decision": "REFER",
                "confidence": 0.7,
                "rationale": f"Mock assessment from {self.agent_id}"
            }
    
    # Register agents
    agent1 = MockAgent("agent_1")
    agent2 = MockAgent("agent_2")
    agent3 = MockAgent("agent_3")
    
    orchestrator.register_agent("agent_1", agent1, AgentRole.LEAD, ["assessment"])
    orchestrator.register_agent("agent_2", agent2, AgentRole.SPECIALIST, ["verification"])
    orchestrator.register_agent("agent_3", agent3, AgentRole.SPECIALIST, ["verification"])
    
    # Run collaboration
    case_data = {
        "case_id": "test_case_1",
        "enrichment": {"test": "data"},
        "evidence_chunks": []
    }
    
    result = orchestrator.initiate_collaboration(
        case_id="test_case_1",
        case_data=case_data,
        participating_agents=["agent_1", "agent_2", "agent_3"],
        lead_agent="agent_1"
    )
    
    print(f"✅ Collaboration session created: {result['session_id']}")
    print(f"✅ Status: {result['status']}")
    print(f"✅ Participants: {len(result['assessments'])}")
    print(f"✅ Consensus: {result['consensus']}")
    
    return True


def test_agent_memory():
    """Test agent memory with vector storage."""
    print("\n" + "="*80)
    print("TEST: Agent Memory")
    print("="*80)
    
    memory_manager = get_agent_memory_manager()
    memory = memory_manager.get_agent_memory("test_agent")
    
    # Store memories
    memory.store(
        memory_type=MemoryType.DECISION,
        content={"decision": "REFER", "confidence": 0.8},
        context={"case_id": "case_1"},
        importance=0.9
    )
    
    memory.store(
        memory_type=MemoryType.PATTERN,
        content={"pattern": "high_wildfire_REFER"},
        context={"wildfire_score": 0.8},
        importance=0.7
    )
    
    # Retrieve memories
    memories = memory.retrieve(
        query={"decision": "REFER"},
        memory_type=MemoryType.DECISION,
        limit=5
    )
    
    print(f"✅ Stored memories retrieved: {len(memories)}")
    
    # Get stats
    stats = memory.get_memory_stats()
    if stats.get("enabled"):
        print(f"✅ Total memories: {stats['total_memories']}")
        print(f"✅ Memory types: {stats['memory_types']}")
    else:
        print(f"✅ Memory disabled (stats: {stats})")
    
    return True


def test_agent_learning():
    """Test agent learning from HITL feedback."""
    print("\n" + "="*80)
    print("TEST: Agent Learning")
    print("="*80)
    
    learning_manager = get_agent_learning_manager()
    learning = learning_manager.get_agent_learning("test_agent")
    
    # Record feedback
    learning.record_feedback(
        original_decision="REFER",
        human_decision="REFER",
        feedback_type=FeedbackType.APPROVAL,
        case_data={"wildfire_score": 0.8, "flood_score": 0.3},
        notes="Correct decision"
    )
    
    learning.record_feedback(
        original_decision="ACCEPT",
        human_decision="REFER",
        feedback_type=FeedbackType.CORRECTION,
        case_data={"wildfire_score": 0.9, "flood_score": 0.2},
        notes="Should have referred due to high wildfire"
    )
    
    # Get summary
    summary = learning.get_learning_summary()
    if summary.get("enabled"):
        print(f"✅ Total feedback: {summary['metrics']['total_feedback']}")
        print(f"✅ Accuracy: {summary['metrics']['accuracy']:.2f}")
        print(f"✅ Patterns learned: {len(summary['patterns'])}")
    else:
        print(f"✅ Learning disabled (summary: {summary})")
    
    # Get recommendations
    recommendations = learning.get_recommendations({"wildfire_score": 0.85})
    print(f"✅ Recommendations: {len(recommendations)}")
    
    return True


def test_agent_performance():
    """Test agent performance tracking and ranking."""
    print("\n" + "="*80)
    print("TEST: Agent Performance")
    print("="*80)
    
    perf_manager = get_agent_performance_manager()
    
    # Track performance for multiple agents
    for agent_id in ["agent_1", "agent_2", "agent_3"]:
        perf = perf_manager.get_agent_performance(agent_id)
        
        # Record some decisions
        for i in range(10):
            perf.record_decision(
                decision="REFER" if i < 3 else "ACCEPT",
                confidence=0.7 + (i * 0.02),
                latency_ms=100 + (i * 10),
                hitl_required=i < 2,
                human_corrected=i == 0,
                cost=0.01
            )
    
    # Get summaries
    summaries = perf_manager.get_all_summaries()
    print(f"✅ Agents tracked: {len(summaries['agents'])}")
    
    # Get rankings
    rankings = perf_manager.get_rankings()
    print(f"✅ Rankings generated: {len(rankings)}")
    if rankings:
        print(f"✅ Top agent: {rankings[0]['agent_id']} (score: {rankings[0]['score']:.2f})")
    
    return True


def test_agent_specialization():
    """Test agent specialization by risk type."""
    print("\n" + "="*80)
    print("TEST: Agent Specialization")
    print("="*80)
    
    specialization = get_agent_specialization()
    
    # Register specialized agents
    class MockSpecialist:
        def __init__(self, agent_id):
            self.agent_id = agent_id
    
    specialization.register_specialized_agent(
        "wildfire_specialist",
        RiskType.WILDFIRE,
        MockSpecialist("wildfire_specialist")
    )
    
    specialization.register_specialized_agent(
        "flood_specialist",
        RiskType.FLOOD,
        MockSpecialist("flood_specialist")
    )
    
    # Test risk detection
    case_data = {
        "hazard_profile": {
            "wildfire_risk_score": 0.8,
            "flood_risk_score": 0.3
        },
        "property_profile": {
            "year_built": 1950,
            "occupancy": "owner_occupied_primary"
        },
        "claims_history": {
            "loss_count_5yr": 1
        }
    }
    
    dominant_risk = specialization.detect_dominant_risk(case_data)
    print(f"✅ Dominant risk detected: {dominant_risk.value}")
    
    # Test routing
    routing = specialization.route_to_specialist(case_data, MockSpecialist("general"))
    print(f"✅ Routing result: {routing['risk_type']}")
    print(f"✅ Specialization enabled: {routing['specialization_enabled']}")
    
    # Get stats
    stats = specialization.get_specialization_stats()
    print(f"✅ Specialized agents: {stats['specialized_agents']}")
    
    return True


def test_agent_communication():
    """Test agent-to-agent communication."""
    print("\n" + "="*80)
    print("TEST: Agent Communication")
    print("="*80)
    
    comm = get_agent_communication()
    
    # Register agents
    comm.register_agent("agent_1")
    comm.register_agent("agent_2")
    
    # Send messages
    message_id = comm.send_message(
        sender="agent_1",
        recipient="agent_2",
        message_type=MessageType.REQUEST,
        content={"query": "assessment_request"}
    )
    
    print(f"✅ Message sent: {message_id}")
    
    # Receive messages
    messages = comm.receive_messages("agent_2")
    print(f"✅ Messages received: {len(messages)}")
    
    # Broadcast
    message_ids = comm.broadcast(
        sender="agent_1",
        recipients=["agent_2"],
        message_type=MessageType.NOTIFICATION,
        content={"alert": "high_risk"}
    )
    print(f"✅ Broadcast messages: {len(message_ids)}")
    
    # Get stats
    stats = comm.get_stats()
    if stats.get("enabled"):
        print(f"✅ Registered agents: {stats['registered_agents']}")
        print(f"✅ Total messages: {stats['total_messages']}")
    else:
        print(f"✅ Communication disabled (stats: {stats})")
    
    return True


def test_conflict_resolution():
    """Test agent conflict resolution."""
    print("\n" + "="*80)
    print("TEST: Conflict Resolution")
    print("="*80)
    
    resolver = get_agent_conflict_resolver()
    
    # Create conflicting assessments
    assessments = {
        "agent_1": {
            "preliminary_decision": "ACCEPT",
            "confidence": 0.8
        },
        "agent_2": {
            "preliminary_decision": "REFER",
            "confidence": 0.7
        },
        "agent_3": {
            "preliminary_decision": "REFER",
            "confidence": 0.6
        }
    }
    
    # Detect conflicts
    conflicts = resolver.detect_conflicts(assessments)
    print(f"✅ Conflicts detected: {len(conflicts)}")
    
    if conflicts:
        # Resolve conflict
        resolution = resolver.resolve_conflict(conflicts[0], assessments, lead_agent="agent_1")
        print(f"✅ Conflict resolved: {resolution['resolved']}")
        print(f"✅ Strategy used: {resolution['strategy']}")
        print(f"✅ Final decision: {resolution['final_decision']}")
    
    # Get stats
    stats = resolver.get_conflict_stats()
    if stats.get("enabled"):
        print(f"✅ Total conflicts: {stats['total_conflicts']}")
        print(f"✅ Resolution rate: {stats['resolution_rate']:.2f}")
    else:
        print(f"✅ Conflict resolution disabled (stats: {stats})")
    
    return True


def main():
    """Run all Phase C multi-agent tests."""
    print("\n" + "="*80)
    print("PHASE C MULTI-AGENT TESTING")
    print("="*80)
    
    tests = [
        ("Multi-Agent Collaboration", test_multi_agent_collaboration),
        ("Agent Memory", test_agent_memory),
        ("Agent Learning", test_agent_learning),
        ("Agent Performance", test_agent_performance),
        ("Agent Specialization", test_agent_specialization),
        ("Agent Communication", test_agent_communication),
        ("Conflict Resolution", test_conflict_resolution)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed, None))
            print(f"✅ PASS: {name}")
        except Exception as e:
            results.append((name, False, str(e)))
            print(f"❌ FAIL: {name} - {e}")
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, p, _ in results if p)
    total = len(results)
    
    print(f"\nDEBUG: passed={passed}, total={total}, passed==total={passed==total}")
    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Success Rate: {passed/total*100:.1f}%")
    
    print("\nDetailed Results:")
    for name, test_passed, error in results:
        status = "✅ PASS" if test_passed else "❌ FAIL"
        print(f"  {status}: {name}")
        if error:
            print(f"    Error: {error}")
    
    print("\n" + "="*80)
    
    # Ensure correct comparison
    if passed == total:
        print("✅ ALL TESTS PASSED - Phase C.1 is ready!")
        return 0
    else:
        print(f"❌ SOME TESTS FAILED - {total - passed} out of {total} tests failed")
        return 1


if __name__ == "__main__":
    exit(main())
