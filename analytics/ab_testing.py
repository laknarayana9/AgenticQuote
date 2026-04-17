"""
A/B Testing Framework
Enables A/B testing of decision rules and configurations.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import hashlib

logger = logging.getLogger(__name__)


class TestStatus(Enum):
    """A/B test status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    STOPPED = "stopped"


class ABTest:
    """A/B test configuration."""
    
    def __init__(
        self,
        test_id: str,
        name: str,
        variant_a: Dict[str, Any],
        variant_b: Dict[str, Any],
        traffic_split: float = 0.5
    ):
        self.test_id = test_id
        self.name = name
        self.variant_a = variant_a
        self.variant_b = variant_b
        self.traffic_split = traffic_split
        self.status = TestStatus.PENDING
        self.created_at = datetime.now()
        self.results_a = []
        self.results_b = []
        self.winner = None


class ABTestingFramework:
    """
    A/B testing framework for decision rules and configurations.
    
    Enables controlled experiments to test different approaches.
    """
    
    def __init__(self):
        """Initialize A/B testing framework."""
        self.enabled = os.getenv("AB_TESTING_ENABLED", "false").lower() == "true"
        
        # Tests
        self.tests = {}
        
        # User assignments (for consistent variant assignment)
        self.user_assignments = {}
        
        logger.info(f"A/B testing framework initialized (enabled={self.enabled})")
    
    def create_test(
        self,
        name: str,
        variant_a: Dict[str, Any],
        variant_b: Dict[str, Any],
        traffic_split: float = 0.5
    ) -> Dict[str, Any]:
        """
        Create a new A/B test.
        
        Args:
            name: Test name
            variant_a: Variant A configuration
            variant_b: Variant B configuration
            traffic_split: Traffic split for variant A (0-1)
            
        Returns:
            Test creation result
        """
        if not self.enabled:
            return {
                "ab_testing_enabled": False,
                "test_id": None,
                "reason": "A/B testing disabled"
            }
        
        test_id = f"test_{datetime.now().timestamp()}"
        test = ABTest(
            test_id=test_id,
            name=name,
            variant_a=variant_a,
            variant_b=variant_b,
            traffic_split=traffic_split
        )
        
        self.tests[test_id] = test
        
        return {
            "ab_testing_enabled": True,
            "test_id": test_id,
            "name": name,
            "status": test.status.value
        }
    
    def assign_variant(
        self,
        test_id: str,
        user_id: str
    ) -> Optional[str]:
        """
        Assign a variant to a user for a test.
        
        Args:
            test_id: Test ID
            user_id: User ID
            
        Returns:
            Variant name ("a" or "b") or None if test not found
        """
        if not self.enabled:
            return None
        
        if test_id not in self.tests:
            return None
        
        test = self.tests[test_id]
        
        # Check if user already assigned
        assignment_key = f"{test_id}:{user_id}"
        if assignment_key in self.user_assignments:
            return self.user_assignments[assignment_key]
        
        # Assign based on traffic split
        # Use hash for consistent assignment
        hash_val = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
        if (hash_val % 100) / 100 < test.traffic_split:
            variant = "a"
        else:
            variant = "b"
        
        self.user_assignments[assignment_key] = variant
        
        return variant
    
    def record_result(
        self,
        test_id: str,
        variant: str,
        success: bool,
        metrics: Dict[str, Any]
    ):
        """
        Record a test result.
        
        Args:
            test_id: Test ID
            variant: Variant ("a" or "b")
            success: Whether the result was successful
            metrics: Additional metrics
        """
        if not self.enabled:
            return
        
        if test_id not in self.tests:
            return
        
        test = self.tests[test_id]
        result = {
            "success": success,
            "metrics": metrics,
            "timestamp": datetime.now()
        }
        
        if variant == "a":
            test.results_a.append(result)
        elif variant == "b":
            test.results_b.append(result)
    
    def start_test(self, test_id: str) -> Dict[str, Any]:
        """
        Start an A/B test.
        
        Args:
            test_id: Test ID
            
        Returns:
            Test start result
        """
        if not self.enabled:
            return {
                "ab_testing_enabled": False,
                "reason": "A/B testing disabled"
            }
        
        if test_id not in self.tests:
            return {
                "ab_testing_enabled": True,
                "reason": "Test not found"
            }
        
        self.tests[test_id].status = TestStatus.RUNNING
        
        return {
            "ab_testing_enabled": True,
            "test_id": test_id,
            "status": self.tests[test_id].status.value
        }
    
    def stop_test(self, test_id: str) -> Dict[str, Any]:
        """
        Stop an A/B test.
        
        Args:
            test_id: Test ID
            
        Returns:
            Test stop result
        """
        if not self.enabled:
            return {
                "ab_testing_enabled": False,
                "reason": "A/B testing disabled"
            }
        
        if test_id not in self.tests:
            return {
                "ab_testing_enabled": True,
                "reason": "Test not found"
            }
        
        self.tests[test_id].status = TestStatus.STOPPED
        
        return {
            "ab_testing_enabled": True,
            "test_id": test_id,
            "status": self.tests[test_id].status.value
        }
    
    def analyze_test(self, test_id: str) -> Dict[str, Any]:
        """
        Analyze test results and determine winner.
        
        Args:
            test_id: Test ID
            
        Returns:
            Test analysis result
        """
        if not self.enabled:
            return {
                "ab_testing_enabled": False,
                "reason": "A/B testing disabled"
            }
        
        if test_id not in self.tests:
            return {
                "ab_testing_enabled": True,
                "reason": "Test not found"
            }
        
        test = self.tests[test_id]
        
        # Calculate success rates
        success_rate_a = sum(1 for r in test.results_a if r["success"]) / len(test.results_a) if test.results_a else 0
        success_rate_b = sum(1 for r in test.results_b if r["success"]) / len(test.results_b) if test.results_b else 0
        
        # Determine winner
        if success_rate_a > success_rate_b:
            winner = "a"
            improvement = (success_rate_a - success_rate_b) / success_rate_b if success_rate_b > 0 else 0
        elif success_rate_b > success_rate_a:
            winner = "b"
            improvement = (success_rate_b - success_rate_a) / success_rate_a if success_rate_a > 0 else 0
        else:
            winner = "tie"
            improvement = 0
        
        test.winner = winner
        test.status = TestStatus.COMPLETED
        
        return {
            "ab_testing_enabled": True,
            "test_id": test_id,
            "results_a": {
                "total": len(test.results_a),
                "success_rate": success_rate_a
            },
            "results_b": {
                "total": len(test.results_b),
                "success_rate": success_rate_b
            },
            "winner": winner,
            "improvement": improvement
        }
    
    def get_test_stats(self, test_id: str) -> Optional[Dict[str, Any]]:
        """
        Get statistics for a test.
        
        Args:
            test_id: Test ID
            
        Returns:
            Test statistics or None if not found
        """
        if not self.enabled:
            return {"enabled": False}
        
        if test_id not in self.tests:
            return None
        
        test = self.tests[test_id]
        
        return {
            "enabled": True,
            "test_id": test_id,
            "name": test.name,
            "status": test.status.value,
            "results_a_count": len(test.results_a),
            "results_b_count": len(test.results_b),
            "winner": test.winner
        }
    
    def get_all_tests(self) -> Dict[str, Any]:
        """
        Get all tests.
        
        Returns:
            All tests
        """
        if not self.enabled:
            return {"enabled": False}
        
        return {
            "enabled": True,
            "tests": {
                test_id: {
                    "name": test.name,
                    "status": test.status.value,
                    "results_a_count": len(test.results_a),
                    "results_b_count": len(test.results_b),
                    "winner": test.winner
                }
                for test_id, test in self.tests.items()
            }
        }


# Global A/B testing framework instance
_global_ab_testing: Optional[ABTestingFramework] = None


def get_ab_testing_framework() -> ABTestingFramework:
    """
    Get global A/B testing framework instance (singleton pattern).
    
    Returns:
        ABTestingFramework instance
    """
    global _global_ab_testing
    if _global_ab_testing is None:
        _global_ab_testing = ABTestingFramework()
    return _global_ab_testing
