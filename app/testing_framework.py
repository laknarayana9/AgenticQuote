"""
Comprehensive Testing and Validation Framework
Implements robust testing for agentic AI systems:

- Unit tests for individual components
- Integration tests for system interactions
- Performance benchmarks
- Validation scenarios for edge cases
- Regression testing
- Load testing capabilities
- Test data generation and management
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid
import json
import statistics
import time
import asyncio
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


class TestType(Enum):
    """Types of tests"""
    UNIT = "unit"
    INTEGRATION = "integration"
    PERFORMANCE = "performance"
    VALIDATION = "validation"
    REGRESSION = "regression"
    LOAD = "load"
    EDGE_CASE = "edge_case"


class TestStatus(Enum):
    """Test execution status"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


class TestPriority(Enum):
    """Test priority levels"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class TestCase:
    """Individual test case definition"""
    test_id: str
    name: str
    description: str
    test_type: TestType
    priority: TestPriority
    test_function: Callable
    expected_result: Any
    timeout: float = 30.0
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    setup_data: Dict[str, Any] = field(default_factory=dict)
    cleanup_function: Optional[Callable] = None


@dataclass
class TestResult:
    """Result of test execution"""
    test_id: str
    status: TestStatus
    execution_time: float
    start_time: datetime
    end_time: datetime
    actual_result: Any
    expected_result: Any
    error_message: Optional[str] = None
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    logs: List[str] = field(default_factory=list)


@dataclass
class TestSuite:
    """Collection of related test cases"""
    suite_id: str
    name: str
    description: str
    test_cases: List[TestCase]
    setup_function: Optional[Callable] = None
    teardown_function: Optional[Callable] = None
    parallel_execution: bool = False


@dataclass
class BenchmarkResult:
    """Result of performance benchmark"""
    benchmark_id: str
    metric_name: str
    value: float
    unit: str
    baseline_value: Optional[float] = None
    improvement_percentage: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class TestDataProvider:
    """Provides test data for various scenarios"""
    
    def __init__(self):
        self.test_scenarios = {}
        self.edge_cases = {}
        self.performance_data = {}
        
    def register_scenario(self, name: str, data: Dict[str, Any]):
        """Register a test scenario"""
        self.test_scenarios[name] = data
    
    def register_edge_case(self, name: str, data: Dict[str, Any]):
        """Register an edge case"""
        self.edge_cases[name] = data
    
    def get_scenario(self, name: str) -> Dict[str, Any]:
        """Get test scenario data"""
        return self.test_scenarios.get(name, {})
    
    def get_edge_case(self, name: str) -> Dict[str, Any]:
        """Get edge case data"""
        return self.edge_cases.get(name, {})
    
    def generate_underwriting_test_data(self) -> List[Dict[str, Any]]:
        """Generate comprehensive underwriting test data"""
        
        test_data = []
        
        # Standard case
        test_data.append({
            "case_id": "standard_ca_property",
            "property": {
                "address": "123 Main St, San Diego, CA",
                "state": "CA",
                "year_built": 1998,
                "roof_age": 10,
                "roof_material": "composite",
                "occupancy": "owner_occupied",
                "square_footage": 2000
            },
            "applicant": {
                "prior_claims": 1,
                "credit_score": 750
            },
            "coverage": {
                "dwelling_limit": 500000,
                "deductible": 2500
            },
            "expected_decision": "ACCEPT",
            "expected_confidence_range": (0.7, 0.9)
        })
        
        # High risk case
        test_data.append({
            "case_id": "high_risk_wildfire",
            "property": {
                "address": "456 Oak Ave, Malibu, CA",
                "state": "CA",
                "year_built": 1960,
                "roof_age": 25,
                "roof_material": "wood",
                "occupancy": "owner_occupied",
                "square_footage": 3500
            },
            "applicant": {
                "prior_claims": 3,
                "credit_score": 620
            },
            "coverage": {
                "dwelling_limit": 1500000,
                "deductible": 1000
            },
            "expected_decision": "REFER",
            "expected_confidence_range": (0.5, 0.8)
        })
        
        # Missing data case
        test_data.append({
            "case_id": "missing_roof_info",
            "property": {
                "address": "789 Pine Rd, Austin, TX",
                "state": "TX",
                "year_built": 2010,
                "roof_age": None,
                "roof_material": None,
                "occupancy": "owner_occupied",
                "square_footage": 1800
            },
            "applicant": {
                "prior_claims": 0,
                "credit_score": 800
            },
            "coverage": {
                "dwelling_limit": 300000,
                "deductible": 2000
            },
            "expected_decision": "REFER",
            "expected_confidence_range": (0.3, 0.6)
        })
        
        # Decline case
        test_data.append({
            "case_id": "decline_candidate",
            "property": {
                "address": "321 Fire Ln, Paradise, CA",
                "state": "CA",
                "year_built": 1940,
                "roof_age": 40,
                "roof_material": "wood",
                "occupancy": "owner_occupied",
                "square_footage": 1200
            },
            "applicant": {
                "prior_claims": 5,
                "credit_score": 500
            },
            "coverage": {
                "dwelling_limit": 200000,
                "deductible": 500
            },
            "expected_decision": "DECLINE",
            "expected_confidence_range": (0.6, 0.9)
        })
        
        return test_data
    
    def generate_performance_test_data(self, load_factor: int = 1) -> List[Dict[str, Any]]:
        """Generate data for performance testing"""
        
        base_data = self.generate_underwriting_test_data()
        
        # Scale data based on load factor
        performance_data = []
        
        for i in range(load_factor):
            for base_case in base_data:
                case = base_case.copy()
                case["case_id"] = f"{case['case_id']}_load_{i}"
                # Add some variation
                if "coverage" in case:
                    case["coverage"]["dwelling_limit"] *= (1 + (i * 0.01))
                performance_data.append(case)
        
        return performance_data


class TestExecutor:
    """Executes test cases and manages test runs"""
    
    def __init__(self):
        self.test_results: Dict[str, TestResult] = {}
        self.current_execution: Optional[str] = None
        self.execution_history: List[Dict[str, Any]] = []
        
    def execute_test_case(self, test_case: TestCase, context: Dict[str, Any] = None) -> TestResult:
        """Execute a single test case"""
        
        start_time = datetime.now()
        test_result = TestResult(
            test_id=test_case.test_id,
            status=TestStatus.RUNNING,
            execution_time=0.0,
            start_time=start_time,
            end_time=start_time,
            actual_result=None,
            expected_result=test_case.expected_result
        )
        
        try:
            logger.info(f"Executing test: {test_case.name}")
            
            # Setup test data
            test_context = context or {}
            test_context.update(test_case.setup_data)
            
            # Execute test with timeout
            if test_case.timeout:
                result = self._execute_with_timeout(test_case.test_function, test_context, test_case.timeout)
            else:
                result = test_case.test_function(test_context)
            
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # Evaluate result
            if self._evaluate_result(result, test_case.expected_result):
                test_result.status = TestStatus.PASSED
            else:
                test_result.status = TestStatus.FAILED
            
            test_result.actual_result = result
            test_result.execution_time = execution_time
            test_result.end_time = end_time
            
            logger.info(f"Test {test_case.name} completed: {test_result.status.value}")
            
        except Exception as e:
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            test_result.status = TestStatus.ERROR
            test_result.error_message = str(e)
            test_result.execution_time = execution_time
            test_result.end_time = end_time
            
            logger.error(f"Test {test_case.name} failed with error: {e}")
        
        finally:
            # Cleanup
            if test_case.cleanup_function:
                try:
                    test_case.cleanup_function(test_context)
                except Exception as e:
                    logger.warning(f"Test cleanup failed: {e}")
        
        self.test_results[test_case.test_id] = test_result
        return test_result
    
    def execute_test_suite(self, test_suite: TestSuite, context: Dict[str, Any] = None) -> Dict[str, TestResult]:
        """Execute a test suite"""
        
        logger.info(f"Executing test suite: {test_suite.name}")
        
        suite_results = {}
        execution_context = context or {}
        
        # Suite setup
        if test_suite.setup_function:
            try:
                test_suite.setup_function(execution_context)
            except Exception as e:
                logger.error(f"Test suite setup failed: {e}")
                return {}
        
        # Execute tests
        if test_suite.parallel_execution:
            suite_results = self._execute_parallel(test_suite.test_cases, execution_context)
        else:
            suite_results = self._execute_sequential(test_suite.test_cases, execution_context)
        
        # Suite teardown
        if test_suite.teardown_function:
            try:
                test_suite.teardown_function(execution_context)
            except Exception as e:
                logger.warning(f"Test suite teardown failed: {e}")
        
        # Store execution record
        execution_record = {
            "suite_id": test_suite.suite_id,
            "suite_name": test_suite.name,
            "timestamp": datetime.now(),
            "total_tests": len(test_suite.test_cases),
            "passed": sum(1 for result in suite_results.values() if result.status == TestStatus.PASSED),
            "failed": sum(1 for result in suite_results.values() if result.status == TestStatus.FAILED),
            "errors": sum(1 for result in suite_results.values() if result.status == TestStatus.ERROR),
            "total_execution_time": sum(result.execution_time for result in suite_results.values())
        }
        
        self.execution_history.append(execution_record)
        
        logger.info(f"Test suite {test_suite.name} completed: {execution_record['passed']}/{execution_record['total_tests']} passed")
        
        return suite_results
    
    def _execute_with_timeout(self, function: Callable, context: Dict[str, Any], timeout: float) -> Any:
        """Execute function with timeout"""
        
        # Simple timeout implementation using threading
        result_container = {}
        exception_container = {}
        
        def target():
            try:
                result_container["result"] = function(context)
            except Exception as e:
                exception_container["exception"] = e
        
        thread = threading.Thread(target=target)
        thread.start()
        thread.join(timeout)
        
        if thread.is_alive():
            raise TimeoutError(f"Test execution timed out after {timeout} seconds")
        
        if "exception" in exception_container:
            raise exception_container["exception"]
        
        return result_container["result"]
    
    def _execute_sequential(self, test_cases: List[TestCase], context: Dict[str, Any]) -> Dict[str, TestResult]:
        """Execute test cases sequentially"""
        
        results = {}
        
        for test_case in test_cases:
            # Check dependencies
            if self._check_dependencies(test_case, results):
                result = self.execute_test_case(test_case, context)
                results[test_case.test_id] = result
            else:
                # Skip due to unmet dependencies
                skipped_result = TestResult(
                    test_id=test_case.test_id,
                    status=TestStatus.SKIPPED,
                    execution_time=0.0,
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                    actual_result=None,
                    expected_result=test_case.expected_result
                )
                results[test_case.test_id] = skipped_result
        
        return results
    
    def _execute_parallel(self, test_cases: List[TestCase], context: Dict[str, Any]) -> Dict[str, TestResult]:
        """Execute test cases in parallel"""
        
        results = {}
        
        # Filter tests that can run in parallel (no dependencies)
        independent_tests = [tc for tc in test_cases if not tc.dependencies]
        
        with ThreadPoolExecutor(max_workers=min(4, len(independent_tests))) as executor:
            # Submit all independent tests
            future_to_test = {
                executor.submit(self.execute_test_case, test_case, context): test_case
                for test_case in independent_tests
            }
            
            # Collect results
            for future in as_completed(future_to_test):
                test_case = future_to_test[future]
                try:
                    result = future.result()
                    results[test_case.test_id] = result
                except Exception as e:
                    logger.error(f"Parallel test execution failed for {test_case.name}: {e}")
        
        # Execute dependent tests sequentially
        dependent_tests = [tc for tc in test_cases if tc.dependencies]
        for test_case in dependent_tests:
            if self._check_dependencies(test_case, results):
                result = self.execute_test_case(test_case, context)
                results[test_case.test_id] = result
        
        return results
    
    def _check_dependencies(self, test_case: TestCase, results: Dict[str, TestResult]) -> bool:
        """Check if test dependencies are satisfied"""
        
        for dependency in test_case.dependencies:
            if dependency not in results:
                return False
            
            dependency_result = results[dependency]
            if dependency_result.status != TestStatus.PASSED:
                return False
        
        return True
    
    def _evaluate_result(self, actual: Any, expected: Any) -> bool:
        """Evaluate if test result matches expectation"""
        
        if isinstance(expected, dict) and "type" in expected:
            # Special evaluation based on type
            if expected["type"] == "range":
                return expected["min"] <= actual <= expected["max"]
            elif expected["type"] == "contains":
                return expected["value"] in actual
            elif expected["type"] == "regex":
                import re
                return bool(re.match(expected["pattern"], str(actual)))
        
        # Direct comparison
        return actual == expected
    
    def get_test_summary(self, suite_id: Optional[str] = None) -> Dict[str, Any]:
        """Get test execution summary"""
        
        if suite_id:
            # Filter results for specific suite
            suite_record = next((record for record in self.execution_history if record["suite_id"] == suite_id), None)
            if suite_record:
                return suite_record
        
        # Overall summary
        if not self.execution_history:
            return {"status": "no_executions"}
        
        total_tests = sum(record["total_tests"] for record in self.execution_history)
        total_passed = sum(record["passed"] for record in self.execution_history)
        total_failed = sum(record["failed"] for record in self.execution_history)
        total_errors = sum(record["errors"] for record in self.execution_history)
        
        return {
            "total_executions": len(self.execution_history),
            "total_tests": total_tests,
            "total_passed": total_passed,
            "total_failed": total_failed,
            "total_errors": total_errors,
            "success_rate": total_passed / total_tests if total_tests > 0 else 0.0,
            "average_execution_time": statistics.mean([record["total_execution_time"] for record in self.execution_history]),
            "last_execution": self.execution_history[-1]["timestamp"].isoformat() if self.execution_history else None
        }


class PerformanceBenchmark:
    """Performance benchmarking system"""
    
    def __init__(self):
        self.benchmarks: Dict[str, Callable] = {}
        self.baseline_results: Dict[str, BenchmarkResult] = {}
        self.current_results: List[BenchmarkResult] = []
        
    def register_benchmark(self, name: str, benchmark_function: Callable):
        """Register a benchmark"""
        self.benchmarks[name] = benchmark_function
    
    def run_benchmark(self, name: str, iterations: int = 10) -> BenchmarkResult:
        """Run a single benchmark"""
        
        if name not in self.benchmarks:
            raise ValueError(f"Benchmark {name} not registered")
        
        benchmark_function = self.benchmarks[name]
        execution_times = []
        
        # Warm up
        try:
            benchmark_function()
        except:
            pass
        
        # Run benchmark
        for i in range(iterations):
            start_time = time.time()
            try:
                benchmark_function()
                end_time = time.time()
                execution_times.append(end_time - start_time)
            except Exception as e:
                logger.error(f"Benchmark iteration {i} failed: {e}")
        
        if not execution_times:
            raise RuntimeError("All benchmark iterations failed")
        
        # Calculate metrics
        avg_time = statistics.mean(execution_times)
        median_time = statistics.median(execution_times)
        min_time = min(execution_times)
        max_time = max(execution_times)
        
        result = BenchmarkResult(
            benchmark_id=str(uuid.uuid4()),
            metric_name=f"{name}_execution_time",
            value=avg_time,
            unit="seconds",
            metadata={
                "iterations": iterations,
                "median_time": median_time,
                "min_time": min_time,
                "max_time": max_time,
                "std_dev": statistics.stdev(execution_times) if len(execution_times) > 1 else 0.0
            }
        )
        
        # Calculate improvement if baseline exists
        if name in self.baseline_results:
            baseline = self.baseline_results[name]
            improvement = ((baseline.value - result.value) / baseline.value) * 100
            result.baseline_value = baseline.value
            result.improvement_percentage = improvement
        
        self.current_results.append(result)
        return result
    
    def set_baseline(self, name: str, result: BenchmarkResult):
        """Set baseline result for benchmark"""
        self.baseline_results[name] = result
    
    def run_all_benchmarks(self) -> Dict[str, BenchmarkResult]:
        """Run all registered benchmarks"""
        
        results = {}
        
        for name in self.benchmarks:
            try:
                result = self.run_benchmark(name)
                results[name] = result
            except Exception as e:
                logger.error(f"Benchmark {name} failed: {e}")
        
        return results
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        
        if not self.current_results:
            return {"status": "no_benchmarks"}
        
        # Group by benchmark name
        benchmark_groups = {}
        for result in self.current_results:
            base_name = result.metric_name.replace("_execution_time", "")
            if base_name not in benchmark_groups:
                benchmark_groups[base_name] = []
            benchmark_groups[base_name].append(result)
        
        # Calculate trends
        report = {
            "benchmarks": {},
            "overall_trends": {
                "total_benchmarks": len(benchmark_groups),
                "improving_benchmarks": 0,
                "degrading_benchmarks": 0,
                "stable_benchmarks": 0
            }
        }
        
        for name, results in benchmark_groups.items():
            latest_result = results[-1]
            
            benchmark_info = {
                "latest_result": {
                    "value": latest_result.value,
                    "unit": latest_result.unit,
                    "timestamp": latest_result.timestamp.isoformat()
                },
                "trend": "stable",
                "improvement": latest_result.improvement_percentage
            }
            
            if latest_result.improvement_percentage is not None:
                if latest_result.improvement_percentage > 5:
                    benchmark_info["trend"] = "improving"
                    report["overall_trends"]["improving_benchmarks"] += 1
                elif latest_result.improvement_percentage < -5:
                    benchmark_info["trend"] = "degrading"
                    report["overall_trends"]["degrading_benchmarks"] += 1
                else:
                    report["overall_trends"]["stable_benchmarks"] += 1
            
            report["benchmarks"][name] = benchmark_info
        
        return report


class ValidationTestSuite:
    """Specialized test suite for validation scenarios"""
    
    def __init__(self):
        self.test_data_provider = TestDataProvider()
        self.validation_scenarios = {}
        
    def register_validation_scenario(self, name: str, validation_function: Callable):
        """Register a validation scenario"""
        self.validation_scenarios[name] = validation_function
    
    def run_validation_tests(self, system_under_test: Any) -> Dict[str, TestResult]:
        """Run all validation tests"""
        
        results = {}
        test_data = self.test_data_provider.generate_underwriting_test_data()
        
        for scenario_name, validation_function in self.validation_scenarios.items():
            for test_case in test_data:
                test_id = f"{scenario_name}_{test_case['case_id']}"
                
                try:
                    start_time = datetime.now()
                    
                    # Run validation
                    validation_result = validation_function(system_under_test, test_case)
                    
                    end_time = datetime.now()
                    execution_time = (end_time - start_time).total_seconds()
                    
                    # Evaluate validation
                    expected_decision = test_case["expected_decision"]
                    actual_decision = validation_result.get("decision", "UNKNOWN")
                    
                    status = TestStatus.PASSED if actual_decision == expected_decision else TestStatus.FAILED
                    
                    # Check confidence range
                    if "expected_confidence_range" in test_case:
                        min_conf, max_conf = test_case["expected_confidence_range"]
                        actual_conf = validation_result.get("confidence", 0.0)
                        
                        if not (min_conf <= actual_conf <= max_conf):
                            status = TestStatus.FAILED
                    
                    result = TestResult(
                        test_id=test_id,
                        status=status,
                        execution_time=execution_time,
                        start_time=start_time,
                        end_time=end_time,
                        actual_result=validation_result,
                        expected_result=expected_decision
                    )
                    
                    results[test_id] = result
                    
                except Exception as e:
                    result = TestResult(
                        test_id=test_id,
                        status=TestStatus.ERROR,
                        execution_time=0.0,
                        start_time=datetime.now(),
                        end_time=datetime.now(),
                        actual_result=None,
                        expected_result=test_case["expected_decision"],
                        error_message=str(e)
                    )
                    
                    results[test_id] = result
        
        return results


class TestingFramework:
    """Main testing framework that coordinates all testing components"""
    
    def __init__(self):
        """Initialize testing framework"""
        
        self.test_executor = TestExecutor()
        self.performance_benchmark = PerformanceBenchmark()
        self.validation_suite = ValidationTestSuite()
        self.test_data_provider = TestDataProvider()
        
        # Test suites
        self.test_suites: Dict[str, TestSuite] = {}
        
        # Test results storage
        self.test_history: List[Dict[str, Any]] = []
        
        # Setup default test suites
        self._setup_default_test_suites()
        
        # Setup default benchmarks
        self._setup_default_benchmarks()
        
        # Setup default validation scenarios
        self._setup_default_validation_scenarios()
        
        logger.info("Testing framework initialized")
    
    def register_test_suite(self, test_suite: TestSuite):
        """Register a test suite"""
        
        self.test_suites[test_suite.suite_id] = test_suite
        logger.info(f"Registered test suite: {test_suite.name}")
    
    def run_test_suite(self, suite_id: str, context: Dict[str, Any] = None) -> Dict[str, TestResult]:
        """Run a specific test suite"""
        
        if suite_id not in self.test_suites:
            raise ValueError(f"Test suite {suite_id} not found")
        
        test_suite = self.test_suites[suite_id]
        results = self.test_executor.execute_test_suite(test_suite, context)
        
        # Store test run
        test_run = {
            "suite_id": suite_id,
            "timestamp": datetime.now(),
            "results": results,
            "summary": self.test_executor.get_test_summary(suite_id)
        }
        
        self.test_history.append(test_run)
        
        return results
    
    def run_all_tests(self, context: Dict[str, Any] = None) -> Dict[str, Dict[str, TestResult]]:
        """Run all registered test suites"""
        
        all_results = {}
        
        for suite_id in self.test_suites:
            try:
                results = self.run_test_suite(suite_id, context)
                all_results[suite_id] = results
            except Exception as e:
                logger.error(f"Test suite {suite_id} failed: {e}")
                all_results[suite_id] = {}
        
        return all_results
    
    def run_performance_tests(self) -> Dict[str, BenchmarkResult]:
        """Run performance benchmarks"""
        
        return self.performance_benchmark.run_all_benchmarks()
    
    def run_validation_tests(self, system_under_test: Any) -> Dict[str, TestResult]:
        """Run validation tests"""
        
        return self.validation_suite.run_validation_tests(system_under_test)
    
    def generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        
        # Test execution summary
        test_summary = self.test_executor.get_test_summary()
        
        # Performance report
        performance_report = self.performance_benchmark.get_performance_report()
        
        # Recent test runs
        recent_runs = self.test_history[-5:] if self.test_history else []
        
        return {
            "timestamp": datetime.now().isoformat(),
            "test_summary": test_summary,
            "performance_report": performance_report,
            "registered_suites": [
                {
                    "suite_id": suite_id,
                    "name": suite.name,
                    "test_count": len(suite.test_cases),
                    "parallel_execution": suite.parallel_execution
                }
                for suite_id, suite in self.test_suites.items()
            ],
            "recent_test_runs": [
                {
                    "suite_id": run["suite_id"],
                    "timestamp": run["timestamp"].isoformat(),
                    "total_tests": run["summary"]["total_tests"],
                    "success_rate": run["summary"]["success_rate"]
                }
                for run in recent_runs
            ],
            "test_coverage": self._calculate_test_coverage(),
            "recommendations": self._generate_recommendations()
        }
    
    def _setup_default_test_suites(self):
        """Setup default test suites"""
        
        # Unit tests for ReAct engine
        react_unit_tests = self._create_react_unit_tests()
        self.register_test_suite(react_unit_tests)
        
        # Integration tests for multi-agent system
        agent_integration_tests = self._create_agent_integration_tests()
        self.register_test_suite(agent_integration_tests)
        
        # Performance tests
        performance_tests = self._create_performance_tests()
        self.register_test_suite(performance_tests)
    
    def _create_react_unit_tests(self) -> TestSuite:
        """Create unit tests for ReAct engine"""
        
        test_cases = []
        
        def test_react_initialization(context):
            from app.advanced_react import get_advanced_react_engine
            engine = get_advanced_react_engine()
            return engine is not None and hasattr(engine, 'execute_advanced_react')
        
        test_cases.append(TestCase(
            test_id="react_init_001",
            name="ReAct Engine Initialization",
            description="Test that ReAct engine initializes correctly",
            test_type=TestType.UNIT,
            priority=TestPriority.CRITICAL,
            test_function=test_react_initialization,
            expected_result=True
        ))
        
        def test_react_basic_reasoning(context):
            from app.advanced_react import get_advanced_react_engine
            engine = get_advanced_react_engine()
            
            query = "Test underwriting query"
            context_data = {"property": {"address": "123 Test St"}}
            
            result = engine.execute_advanced_react(query, context_data, max_iterations=3)
            
            return result is not None and hasattr(result, 'current_decision')
        
        test_cases.append(TestCase(
            test_id="react_reasoning_001",
            name="ReAct Basic Reasoning",
            description="Test basic ReAct reasoning functionality",
            test_type=TestType.UNIT,
            priority=TestPriority.HIGH,
            test_function=test_react_basic_reasoning,
            expected_result=True
        ))
        
        return TestSuite(
            suite_id="react_unit_tests",
            name="ReAct Engine Unit Tests",
            description="Unit tests for ReAct reasoning engine",
            test_cases=test_cases,
            parallel_execution=True
        )
    
    def _create_agent_integration_tests(self) -> TestSuite:
        """Create integration tests for multi-agent system"""
        
        test_cases = []
        
        def test_agent_system_initialization(context):
            from app.hierarchical_agents import get_hierarchical_agent_system
            system = get_hierarchical_agent_system()
            return system is not None and hasattr(system, 'process_with_hierarchy')
        
        test_cases.append(TestCase(
            test_id="agent_init_001",
            name="Agent System Initialization",
            description="Test that hierarchical agent system initializes correctly",
            test_type=TestType.INTEGRATION,
            priority=TestPriority.CRITICAL,
            test_function=test_agent_system_initialization,
            expected_result=True
        ))
        
        def test_agent_coordination(context):
            from app.hierarchical_agents import get_hierarchical_agent_system
            system = get_hierarchical_agent_system()
            
            test_input = {
                "applicant_name": "Test User",
                "address": "123 Test St",
                "property_type": "single_family",
                "coverage_amount": 500000
            }
            
            result = system.process_with_hierarchy(test_input)
            
            return result is not None and "final_decision" in result
        test_cases.append(TestCase(
            test_id="agent_coord_001",
            name="Agent Coordination",
            description="Test agent coordination and decision making",
            test_type=TestType.INTEGRATION,
            priority=TestPriority.HIGH,
            test_function=test_agent_coordination,
            expected_result=True
        ))
        
        return TestSuite(
            suite_id="agent_integration_tests",
            name="Multi-Agent Integration Tests",
            description="Integration tests for hierarchical agent system",
            test_cases=test_cases,
            parallel_execution=False  # Sequential due to shared system state
        )
    
    def _create_performance_tests(self) -> TestSuite:
        """Create performance tests"""
        
        test_cases = []
        
        def test_react_performance(context):
            from app.advanced_react import get_advanced_react_engine
            engine = get_advanced_react_engine()
            
            start_time = time.time()
            
            # Run multiple iterations
            for i in range(10):
                query = f"Performance test query {i}"
                context_data = {"property": {"address": f"{i} Test St"}}
                result = engine.execute_advanced_react(query, context_data, max_iterations=2)
            
            end_time = time.time()
            total_time = end_time - start_time
            avg_time = total_time / 10
            
            # Should complete in under 5 seconds on average
            return avg_time < 5.0
        
        test_cases.append(TestCase(
            test_id="perf_react_001",
            name="ReAct Engine Performance",
            description="Test ReAct engine performance under load",
            test_type=TestType.PERFORMANCE,
            priority=TestPriority.HIGH,
            test_function=test_react_performance,
            expected_result=True,
            timeout=60.0  # Allow more time for performance tests
        ))
        
        return TestSuite(
            suite_id="performance_tests",
            name="Performance Tests",
            description="Performance and load tests",
            test_cases=test_cases,
            parallel_execution=False  # Sequential to avoid interference
        )
    
    def _setup_default_benchmarks(self):
        """Setup default performance benchmarks"""
        
        def benchmark_react_reasoning():
            from app.advanced_react import get_advanced_react_engine
            engine = get_advanced_react_engine()
            
            query = "Benchmark test query"
            context_data = {"property": {"address": "Benchmark St"}}
            
            result = engine.execute_advanced_react(query, context_data, max_iterations=5)
            return result is not None
        
        self.performance_benchmark.register_benchmark("react_reasoning", benchmark_react_reasoning)
        
        def benchmark_agent_coordination():
            from app.hierarchical_agents import get_hierarchical_agent_system
            system = get_hierarchical_agent_system()
            
            test_input = {
                "applicant_name": "Benchmark User",
                "address": "Benchmark St",
                "property_type": "single_family",
                "coverage_amount": 500000
            }
            
            result = system.process_with_hierarchy(test_input)
            return result is not None
        
        self.performance_benchmark.register_benchmark("agent_coordination", benchmark_agent_coordination)
    
    def _setup_default_validation_scenarios(self):
        """Setup default validation scenarios"""
        
        def validate_react_underwriting(system_under_test, test_case):
            """Validate ReAct underwriting decisions"""
            
            query = "Underwriting assessment"
            result = system_under_test.execute_advanced_react(query, test_case, max_iterations=10)
            
            return {
                "decision": result.current_decision,
                "confidence": result.confidence_score,
                "iterations": result.iteration_count
            }
        
        self.validation_suite.register_validation_scenario("react_underwriting", validate_react_underwriting)
        
        def validate_agent_underwriting(system_under_test, test_case):
            """Validate agent-based underwriting decisions"""
            
            result = system_under_test.process_with_hierarchy(test_case)
            
            return {
                "decision": result.get("final_decision"),
                "confidence": result.get("confidence", 0.0),
                "agent_count": len(result.get("agent_contributions", {}))
            }
        
        self.validation_suite.register_validation_scenario("agent_underwriting", validate_agent_underwriting)
    
    def _calculate_test_coverage(self) -> Dict[str, float]:
        """Calculate test coverage metrics"""
        
        # Mock coverage calculation
        total_components = 10  # Total number of components to test
        tested_components = len(self.test_suites)
        
        return {
            "overall_coverage": tested_components / total_components,
            "unit_test_coverage": 0.8,  # Mock values
            "integration_coverage": 0.7,
            "performance_coverage": 0.6
        }
    
    def _generate_recommendations(self) -> List[str]:
        """Generate testing recommendations"""
        
        recommendations = []
        
        test_summary = self.test_executor.get_test_summary()
        
        if test_summary.get("success_rate", 0) < 0.9:
            recommendations.append("Consider investigating failing tests to improve success rate")
        
        if len(self.test_suites) < 5:
            recommendations.append("Add more test suites to improve coverage")
        
        performance_report = self.performance_benchmark.get_performance_report()
        if performance_report.get("overall_trends", {}).get("degrading_benchmarks", 0) > 0:
            recommendations.append("Investigate performance degradation in benchmarks")
        
        if not recommendations:
            recommendations.append("Testing framework is performing well")
        
        return recommendations


# Global testing framework instance
_global_testing_framework: Optional[TestingFramework] = None


def get_testing_framework() -> TestingFramework:
    """Get global testing framework instance"""
    global _global_testing_framework
    if _global_testing_framework is None:
        _global_testing_framework = TestingFramework()
    return _global_testing_framework
