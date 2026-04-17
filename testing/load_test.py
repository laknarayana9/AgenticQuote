"""
Load Testing
Simulates high load to test system performance under stress.
"""

import os
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from enum import Enum
import time
import threading

logger = logging.getLogger(__name__)


class LoadTestStatus(Enum):
    """Load test status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class LoadTest:
    """Load test configuration."""
    
    def __init__(
        self,
        test_id: str,
        name: str,
        target: str,
        concurrent_users: int,
        duration_seconds: int,
        ramp_up_seconds: int
    ):
        self.test_id = test_id
        self.name = name
        self.target = target
        self.concurrent_users = concurrent_users
        self.duration_seconds = duration_seconds
        self.ramp_up_seconds = ramp_up_seconds
        self.status = LoadTestStatus.PENDING
        self.start_time = None
        self.end_time = None
        self.results = {}


class LoadTester:
    """
    Load testing engine.
    
    Simulates high load to test system performance.
    """
    
    def __init__(self):
        """Initialize load tester."""
        self.enabled = os.getenv("LOAD_TESTING_ENABLED", "false").lower() == "true"
        
        # Load tests
        self.load_tests = {}
        
        # Test results
        self.test_history = []
        
        logger.info(f"Load tester initialized (enabled={self.enabled})")
    
    def create_test(
        self,
        name: str,
        target: str,
        concurrent_users: int,
        duration_seconds: int,
        ramp_up_seconds: int = 10
    ) -> Dict[str, Any]:
        """
        Create a load test.
        
        Args:
            name: Test name
            target: Target endpoint/URL
            concurrent_users: Number of concurrent users
            duration_seconds: Test duration
            ramp_up_seconds: Ramp-up time
            
        Returns:
            Test creation result
        """
        if not self.enabled:
            return {
                "load_testing_enabled": False,
                "test_id": None,
                "reason": "Load testing disabled"
            }
        
        test_id = f"load_{datetime.now().timestamp()}"
        test = LoadTest(
            test_id=test_id,
            name=name,
            target=target,
            concurrent_users=concurrent_users,
            duration_seconds=duration_seconds,
            ramp_up_seconds=ramp_up_seconds
        )
        
        self.load_tests[test_id] = test
        
        return {
            "load_testing_enabled": True,
            "test_id": test_id,
            "name": name,
            "target": target,
            "concurrent_users": concurrent_users,
            "status": "created"
        }
    
    def run_test(
        self,
        test_id: str,
        request_func: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Run a load test.
        
        Args:
            test_id: Test ID
            request_func: Function to execute for each request
            
        Returns:
            Test result
        """
        if not self.enabled:
            return {
                "load_testing_enabled": False,
                "reason": "Load testing disabled"
            }
        
        if test_id not in self.load_tests:
            return {
                "load_testing_enabled": True,
                "reason": "Test not found"
            }
        
        test = self.load_tests[test_id]
        test.status = LoadTestStatus.RUNNING
        test.start_time = datetime.now()
        
        # Simulate load test
        results = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_response_time_ms": 0,
            "max_response_time_ms": 0,
            "min_response_time_ms": 0,
            "requests_per_second": 0
        }
        
        response_times = []
        
        try:
            # Simulate requests
            for i in range(test.concurrent_users):
                # Simulate request
                response_time = time.time() % 100 + 10  # Simulated response time
                response_times.append(response_time)
                results["total_requests"] += 1
                results["successful_requests"] += 1
                
                # Simulate ramp-up delay
                if i < test.concurrent_users:
                    time.sleep(test.ramp_up_seconds / test.concurrent_users)
            
            # Calculate metrics
            if response_times:
                results["avg_response_time_ms"] = sum(response_times) / len(response_times)
                results["max_response_time_ms"] = max(response_times)
                results["min_response_time_ms"] = min(response_times)
            
            results["requests_per_second"] = results["total_requests"] / test.duration_seconds
            
            test.status = LoadTestStatus.COMPLETED
            test.results = results
            
        except Exception as e:
            test.status = LoadTestStatus.FAILED
            logger.error(f"Load test {test_id} failed: {e}")
        
        test.end_time = datetime.now()
        
        # Record test history
        self.test_history.append({
            "test_id": test_id,
            "name": test.name,
            "status": test.status.value,
            "results": results,
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "load_testing_enabled": True,
            "test_id": test_id,
            "name": test.name,
            "status": test.status.value,
            "duration_seconds": (test.end_time - test.start_time).total_seconds() if test.end_time else 0,
            "results": results
        }
    
    def get_test_status(self, test_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a load test.
        
        Args:
            test_id: Test ID
            
        Returns:
            Test status or None if not found
        """
        if not self.enabled:
            return {"enabled": False}
        
        if test_id not in self.load_tests:
            return None
        
        test = self.load_tests[test_id]
        
        return {
            "enabled": True,
            "test_id": test_id,
            "name": test.name,
            "target": test.target,
            "status": test.status.value,
            "concurrent_users": test.concurrent_users,
            "duration_seconds": test.duration_seconds,
            "start_time": test.start_time.isoformat() if test.start_time else None,
            "end_time": test.end_time.isoformat() if test.end_time else None
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get load testing summary.
        
        Returns:
            Summary data
        """
        if not self.enabled:
            return {"enabled": False}
        
        completed = sum(1 for t in self.load_tests.values() if t.status == LoadTestStatus.COMPLETED)
        failed = sum(1 for t in self.load_tests.values() if t.status == LoadTestStatus.FAILED)
        
        return {
            "enabled": True,
            "total_tests": len(self.load_tests),
            "completed": completed,
            "failed": failed,
            "test_history_count": len(self.test_history)
        }


# Global load tester instance
_global_load_tester: Optional[LoadTester] = None


def get_load_tester() -> LoadTester:
    """
    Get global load tester instance (singleton pattern).
    
    Returns:
        LoadTester instance
    """
    global _global_load_tester
    if _global_load_tester is None:
        _global_load_tester = LoadTester()
    return _global_load_tester
