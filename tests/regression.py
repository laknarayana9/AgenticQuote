"""
Automated Regression Testing
Automated regression testing framework for system validation.
"""

import os
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class TestStatus(Enum):
    """Test status."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class RegressionTest:
    """Regression test definition."""
    
    def __init__(
        self,
        test_id: str,
        name: str,
        test_func: Callable,
        category: str = "general"
    ):
        self.test_id = test_id
        self.name = name
        self.test_func = test_func
        self.category = category
        self.status = TestStatus.PENDING
        self.result = None
        self.error = None
        self.duration = 0


class RegressionTestSuite:
    """
    Automated regression testing suite.
    
    Runs regression tests to ensure system stability.
    """
    
    def __init__(self):
        """Initialize regression test suite."""
        self.enabled = os.getenv("REGRESSION_TESTING_ENABLED", "false").lower() == "true"
        
        # Test registry
        self.tests = {}
        
        # Test results
        self.test_results = []
        
        logger.info(f"Regression test suite initialized (enabled={self.enabled})")
    
    def register_test(
        self,
        test_id: str,
        name: str,
        test_func: Callable,
        category: str = "general"
    ):
        """
        Register a regression test.
        
        Args:
            test_id: Test ID
            name: Test name
            test_func: Test function
            category: Test category
        """
        test = RegressionTest(test_id, name, test_func, category)
        self.tests[test_id] = test
        logger.debug(f"Registered test: {test_id}")
    
    def run_test(self, test_id: str) -> Dict[str, Any]:
        """
        Run a specific test.
        
        Args:
            test_id: Test ID
            
        Returns:
            Test result
        """
        if not self.enabled:
            return {
                "regression_testing_enabled": False,
                "test_id": test_id,
                "reason": "Regression testing disabled"
            }
        
        if test_id not in self.tests:
            return {
                "regression_testing_enabled": True,
                "test_id": test_id,
                "reason": "Test not found"
            }
        
        test = self.tests[test_id]
        test.status = TestStatus.RUNNING
        start_time = datetime.now()
        
        try:
            result = test.test_func()
            test.status = TestStatus.PASSED
            test.result = result
            test.error = None
        except Exception as e:
            test.status = TestStatus.FAILED
            test.error = str(e)
            logger.error(f"Test {test_id} failed: {e}")
        
        test.duration = (datetime.now() - start_time).total_seconds()
        
        # Record result
        self.test_results.append({
            "test_id": test_id,
            "name": test.name,
            "status": test.status.value,
            "duration": test.duration,
            "error": test.error,
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "regression_testing_enabled": True,
            "test_id": test_id,
            "name": test.name,
            "status": test.status.value,
            "duration": test.duration,
            "error": test.error
        }
    
    def run_suite(self, category: Optional[str] = None) -> Dict[str, Any]:
        """
        Run all tests or tests in a category.
        
        Args:
            category: Test category to run (all if None)
            
        Returns:
            Suite results
        """
        if not self.enabled:
            return {
                "regression_testing_enabled": False,
                "reason": "Regression testing disabled"
            }
        
        tests_to_run = []
        for test_id, test in self.tests.items():
            if category is None or test.category == category:
                tests_to_run.append(test_id)
        
        results = []
        for test_id in tests_to_run:
            result = self.run_test(test_id)
            results.append(result)
        
        # Calculate summary
        passed = sum(1 for r in results if r.get("status") == "passed")
        failed = sum(1 for r in results if r.get("status") == "failed")
        total = len(results)
        
        return {
            "regression_testing_enabled": True,
            "category": category or "all",
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "success_rate": passed / total if total > 0 else 0,
            "results": results
        }
    
    def get_test_results(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent test results.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of test results
        """
        if not self.enabled:
            return []
        
        return self.test_results[-limit:]
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get regression test summary.
        
        Returns:
            Summary data
        """
        if not self.enabled:
            return {"enabled": False}
        
        # Calculate recent statistics
        recent_results = self.get_test_results(50)
        passed = sum(1 for r in recent_results if r["status"] == "passed")
        failed = sum(1 for r in recent_results if r["status"] == "failed")
        
        return {
            "enabled": True,
            "total_tests": len(self.tests),
            "recent_results": len(recent_results),
            "recent_passed": passed,
            "recent_failed": failed,
            "recent_success_rate": passed / len(recent_results) if recent_results else 0
        }


# Global regression test suite instance
_global_regression_suite: Optional[RegressionTestSuite] = None


def get_regression_suite() -> RegressionTestSuite:
    """
    Get global regression test suite instance (singleton pattern).
    
    Returns:
        RegressionTestSuite instance
    """
    global _global_regression_suite
    if _global_regression_suite is None:
        _global_regression_suite = RegressionTestSuite()
    return _global_regression_suite


# Decorator for registering tests
def regression_test(test_id: str, name: str, category: str = "general"):
    """
    Decorator to register a regression test.
    
    Args:
        test_id: Test ID
        name: Test name
        category: Test category
    """
    def decorator(func):
        suite = get_regression_suite()
        suite.register_test(test_id, name, func, category)
        return func
    return decorator
