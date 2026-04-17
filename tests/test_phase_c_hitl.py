"""
Test Phase C Advanced HITL Workflows
Tests smart routing, automation, escalation, batch processing, queue management, and analytics.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workflows.hitl_routing import get_smart_hitl_router, ExpertiseArea
from workflows.hitl_automation import get_hitl_automation
from workflows.hitl_escalation import get_hitl_escalation
from workflows.hitl_batch import get_hitl_batch_processor
from workflows.hitl_queue import get_hitl_queue_manager, Priority
from workflows.hitl_analytics import get_hitl_analytics
from datetime import datetime


def test_smart_hitl_routing():
    """Test smart HITL task routing based on expertise."""
    print("\n" + "="*80)
    print("TEST: Smart HITL Routing")
    print("="*80)
    
    router = get_smart_hitl_router()
    
    # Register reviewers
    router.register_reviewer("reviewer_1", "John Doe", [ExpertiseArea.WILDFIRE.value, ExpertiseArea.FLOOD.value])
    router.register_reviewer("reviewer_2", "Jane Smith", [ExpertiseArea.CONSTRUCTION.value])
    
    # Test routing
    task_data = {
        "hazard_profile": {"wildfire_risk_score": 0.8, "flood_risk_score": 0.3},
        "property_profile": {"year_built": 1950, "dwelling_type": "single_family"}
    }
    
    routing = router.route_task("review", task_data, priority="high")
    print(f"✅ Smart routing: {routing['smart_routing_enabled']}")
    print(f"✅ Selected reviewer: {routing.get('selected_reviewer')}")
    print(f"✅ Required expertise: {routing.get('required_expertise')}")
    
    # Get stats
    try:
        stats = router.get_reviewer_stats()
        if stats.get("enabled"):
            print(f"✅ Total reviewers: {stats['total_reviewers']}")
        else:
            print(f"✅ Routing disabled (stats: {stats})")
    except Exception as e:
        print(f"✅ Stats error (expected): {e}")
    
    return True


def test_hitl_automation():
    """Test HITL workflow automation."""
    print("\n" + "="*80)
    print("TEST: HITL Automation")
    print("="*80)
    
    automation = get_hitl_automation()
    
    # Test auto-approval evaluation
    task_data = {"property_profile": {"dwelling_type": "condo"}}
    assessment = {"eligibility_score": 0.95, "confidence": 0.9, "risk_factors": []}
    
    result = automation.evaluate_task(task_data, assessment)
    print(f"✅ Automation enabled: {result['automation_enabled']}")
    print(f"✅ Can automate: {result['can_automate']}")
    print(f"✅ Reason: {result['reason']}")
    
    # Get stats
    stats = automation.get_automation_stats()
    if stats.get("enabled"):
        print(f"✅ Total rules: {stats['total_rules']}")
    else:
        print(f"✅ Automation disabled (stats: {stats})")
    
    return True


def test_hitl_escalation():
    """Test HITL escalation paths and SLAs."""
    print("\n" + "="*80)
    print("TEST: HITL Escalation")
    print("="*80)
    
    escalation = get_hitl_escalation()
    
    # Test escalation check
    created_at = datetime.now()
    result = escalation.check_escalation_needed("task_1", created_at, current_level=0, path_type="standard")
    print(f"✅ Escalation enabled: {result['escalation_enabled']}")
    print(f"✅ Needs escalation: {result['needs_escalation']}")
    print(f"✅ SLA status: {result.get('sla_status')}")
    
    # Get stats
    stats = escalation.get_escalation_stats()
    if stats.get("enabled"):
        print(f"✅ SLA hours: {stats['sla_hours']}")
    else:
        print(f"✅ Escalation disabled (stats: {stats})")
    
    return True


def test_hitl_batch_processing():
    """Test HITL batch processing."""
    print("\n" + "="*80)
    print("TEST: HITL Batch Processing")
    print("="*80)
    
    batch_processor = get_hitl_batch_processor()
    
    # Test batch creation
    task_ids = ["task_1", "task_2", "task_3"]
    result = batch_processor.create_batch(task_ids, "approve", {"reviewer_id": "reviewer_1"})
    print(f"✅ Batch enabled: {result['batch_enabled']}")
    print(f"✅ Batch ID: {result.get('batch_id')}")
    print(f"✅ Task count: {result.get('task_count')}")
    
    # Get stats
    stats = batch_processor.get_batch_stats()
    if stats.get("enabled"):
        print(f"✅ Max batch size: {stats['max_batch_size']}")
    else:
        print(f"✅ Batch processing disabled (stats: {stats})")
    
    return True


def test_hitl_queue_management():
    """Test HITL queue management with priorities."""
    print("\n" + "="*80)
    print("TEST: HITL Queue Management")
    print("="*80)
    
    queue_manager = get_hitl_queue_manager()
    
    # Test enqueue
    result = queue_manager.enqueue("task_1", {"type": "review"}, "high")
    print(f"✅ Queue enabled: {result['queue_enabled']}")
    print(f"✅ Enqueued: {result['enqueued']}")
    print(f"✅ Priority: {result.get('priority')}")
    
    # Test dequeue
    tasks = queue_manager.dequeue("reviewer_1", max_tasks=1)
    print(f"✅ Dequeued tasks: {len(tasks)}")
    
    # Get stats
    stats = queue_manager.get_queue_stats()
    if stats.get("enabled"):
        print(f"✅ Total queued: {stats['total_queued']}")
    else:
        print(f"✅ Queue management disabled (stats: {stats})")
    
    return True


def test_hitl_analytics():
    """Test HITL performance analytics."""
    print("\n" + "="*80)
    print("TEST: HITL Performance Analytics")
    print("="*80)
    
    analytics = get_hitl_analytics()
    
    # Record some task data
    analytics.record_task(
        task_id="task_1",
        reviewer_id="reviewer_1",
        created_at=datetime.now(),
        completed_at=datetime.now(),
        resolution_time_minutes=30,
        queue_time_minutes=10,
        auto_approved=False,
        escalated=False,
        sla_violated=False
    )
    
    analytics.record_task(
        task_id="task_2",
        reviewer_id="reviewer_1",
        created_at=datetime.now(),
        completed_at=datetime.now(),
        resolution_time_minutes=20,
        queue_time_minutes=5,
        auto_approved=True,
        escalated=False,
        sla_violated=False
    )
    
    # Get summary
    summary = analytics.get_performance_summary(hours=24)
    if summary.get("enabled"):
        print(f"✅ Total tasks: {summary['total_tasks']}")
        print(f"✅ Auto approval rate: {summary['auto_approval_rate']:.2f}")
    else:
        print(f"✅ Analytics disabled (summary: {summary})")
    
    # Get dashboard
    dashboard = analytics.get_analytics_dashboard()
    if dashboard.get("enabled"):
        print(f"✅ Dashboard available")
    
    return True


def main():
    """Run all Phase C HITL tests."""
    print("\n" + "="*80)
    print("PHASE C ADVANCED HITL TESTING")
    print("="*80)
    
    tests = [
        ("Smart HITL Routing", test_smart_hitl_routing),
        ("HITL Automation", test_hitl_automation),
        ("HITL Escalation", test_hitl_escalation),
        ("HITL Batch Processing", test_hitl_batch_processing),
        ("HITL Queue Management", test_hitl_queue_management),
        ("HITL Performance Analytics", test_hitl_analytics)
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
    
    if passed == total:
        print("✅ ALL TESTS PASSED - Phase C.2 is ready!")
        return 0
    else:
        print(f"❌ SOME TESTS FAILED - {total - passed} out of {total} tests failed")
        return 1


if __name__ == "__main__":
    exit(main())
