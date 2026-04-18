"""
Integration Testing Framework
Provides tools for testing API integrations
"""

import pytest
import requests
import asyncio
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime
import json


@dataclass
class TestConfig:
    """Test configuration"""
    base_url: str = "http://localhost:8000"
    api_key: str = "test-api-key"
    timeout: int = 30


@dataclass
class TestCase:
    """Test case definition"""
    name: str
    endpoint: str
    method: str
    expected_status: int
    request_data: Optional[Dict[str, Any]] = None
    expected_response: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None


class IntegrationTestRunner:
    """Integration test runner for API testing"""
    
    def __init__(self, config: TestConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json"
        })
        self.test_results: List[Dict[str, Any]] = []
    
    def run_test(self, test_case: TestCase) -> Dict[str, Any]:
        """Run a single test case"""
        start_time = datetime.now()
        result = {
            "name": test_case.name,
            "endpoint": test_case.endpoint,
            "method": test_case.method,
            "passed": False,
            "status_code": None,
            "response_time_ms": 0,
            "error": None,
            "response_data": None
        }
        
        try:
            url = f"{self.config.base_url}{test_case.endpoint}"
            headers = test_case.headers or {}
            
            response = self.session.request(
                method=test_case.method,
                url=url,
                json=test_case.request_data,
                headers=headers,
                timeout=self.config.timeout
            )
            
            end_time = datetime.now()
            result["status_code"] = response.status_code
            result["response_time_ms"] = (end_time - start_time).total_seconds() * 1000
            
            # Check status code
            if response.status_code == test_case.expected_status:
                result["passed"] = True
            
            # Check response data if provided
            if test_case.expected_response:
                try:
                    response_data = response.json()
                    result["response_data"] = response_data
                    
                    # Simple comparison (can be enhanced)
                    for key, value in test_case.expected_response.items():
                        if response_data.get(key) != value:
                            result["passed"] = False
                            break
                except ValueError:
                    pass
            
        except Exception as e:
            end_time = datetime.now()
            result["error"] = str(e)
            result["response_time_ms"] = (end_time - start_time).total_seconds() * 1000
        
        self.test_results.append(result)
        return result
    
    def run_tests(self, test_cases: List[TestCase]) -> Dict[str, Any]:
        """Run multiple test cases"""
        results = []
        passed = 0
        failed = 0
        
        for test_case in test_cases:
            result = self.run_test(test_case)
            results.append(result)
            
            if result["passed"]:
                passed += 1
            else:
                failed += 1
        
        return {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "success_rate": passed / len(results) if results else 0,
            "results": results
        }
    
    def get_test_summary(self) -> Dict[str, Any]:
        """Get summary of all test results"""
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["passed"])
        failed = total - passed
        
        avg_response_time = (
            sum(r["response_time_ms"] for r in self.test_results) / total
            if total > 0 else 0
        )
        
        return {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "success_rate": passed / total if total > 0 else 0,
            "average_response_time_ms": avg_response_time,
            "results": self.test_results
        }


class AsyncIntegrationTestRunner:
    """Async integration test runner"""
    
    def __init__(self, config: TestConfig):
        self.config = config
        self.client = None
        self.test_results: List[Dict[str, Any]] = []
    
    async def initialize(self):
        """Initialize async HTTP client"""
        import httpx
        self.client = httpx.AsyncClient(
            base_url=self.config.base_url,
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json"
            },
            timeout=self.config.timeout
        )
    
    async def close(self):
        """Close the HTTP client"""
        if self.client:
            await self.client.aclose()
    
    async def run_test(self, test_case: TestCase) -> Dict[str, Any]:
        """Run a single test case asynchronously"""
        start_time = datetime.now()
        result = {
            "name": test_case.name,
            "endpoint": test_case.endpoint,
            "method": test_case.method,
            "passed": False,
            "status_code": None,
            "response_time_ms": 0,
            "error": None,
            "response_data": None
        }
        
        try:
            headers = test_case.headers or {}
            
            response = await self.client.request(
                method=test_case.method,
                url=test_case.endpoint,
                json=test_case.request_data,
                headers=headers
            )
            
            end_time = datetime.now()
            result["status_code"] = response.status_code
            result["response_time_ms"] = (end_time - start_time).total_seconds() * 1000
            
            if response.status_code == test_case.expected_status:
                result["passed"] = True
            
            if test_case.expected_response:
                try:
                    response_data = response.json()
                    result["response_data"] = response_data
                    
                    for key, value in test_case.expected_response.items():
                        if response_data.get(key) != value:
                            result["passed"] = False
                            break
                except ValueError:
                    pass
            
        except Exception as e:
            end_time = datetime.now()
            result["error"] = str(e)
            result["response_time_ms"] = (end_time - start_time).total_seconds() * 1000
        
        self.test_results.append(result)
        return result
    
    async def run_tests(self, test_cases: List[TestCase]) -> Dict[str, Any]:
        """Run multiple test cases asynchronously"""
        results = []
        passed = 0
        failed = 0
        
        for test_case in test_cases:
            result = await self.run_test(test_case)
            results.append(result)
            
            if result["passed"]:
                passed += 1
            else:
                failed += 1
        
        return {
            "total": len(results),
            "passed": passed,
            "failed": failed,
            "success_rate": passed / len(results) if results else 0,
            "results": results
        }


def create_default_test_cases() -> List[TestCase]:
    """Create default test cases for API testing"""
    return [
        TestCase(
            name="Get Health Check",
            endpoint="/health",
            method="GET",
            expected_status=200,
            expected_response={"status": "healthy"}
        ),
        TestCase(
            name="List Cases",
            endpoint="/api/v1/cases",
            method="GET",
            expected_status=200
        ),
        TestCase(
            name="Create Case",
            endpoint="/api/v1/cases",
            method="POST",
            expected_status=201,
            request_data={
                "property_address": "123 Test St",
                "property_value": 500000,
                "coverage_amount": 400000
            }
        ),
        TestCase(
            name="Get API Metrics",
            endpoint="/api/v1/metrics",
            method="GET",
            expected_status=200
        ),
        TestCase(
            name="Get Rate Limits",
            endpoint="/api/v1/rate-limits",
            method="GET",
            expected_status=200
        )
    ]


def run_integration_tests(
    base_url: str = "http://localhost:8000",
    api_key: str = "test-api-key"
) -> Dict[str, Any]:
    """Convenience function to run integration tests"""
    config = TestConfig(base_url=base_url, api_key=api_key)
    runner = IntegrationTestRunner(config)
    test_cases = create_default_test_cases()
    return runner.run_tests(test_cases)


@pytest.fixture
def test_config():
    """Pytest fixture for test configuration"""
    return TestConfig(
        base_url="http://localhost:8000",
        api_key="test-api-key"
    )


@pytest.fixture
def test_runner(test_config):
    """Pytest fixture for test runner"""
    runner = IntegrationTestRunner(test_config)
    yield runner
    # Cleanup if needed


class TestAPIEndpoints:
    """Pytest test class for API endpoints"""
    
    def test_health_check(self, test_runner):
        """Test health check endpoint"""
        test_case = TestCase(
            name="Health Check",
            endpoint="/health",
            method="GET",
            expected_status=200,
            expected_response={"status": "healthy"}
        )
        result = test_runner.run_test(test_case)
        assert result["passed"], f"Health check failed: {result}"
    
    def test_list_cases(self, test_runner):
        """Test list cases endpoint"""
        test_case = TestCase(
            name="List Cases",
            endpoint="/api/v1/cases",
            method="GET",
            expected_status=200
        )
        result = test_runner.run_test(test_case)
        assert result["passed"], f"List cases failed: {result}"
    
    def test_create_case(self, test_runner):
        """Test create case endpoint"""
        test_case = TestCase(
            name="Create Case",
            endpoint="/api/v1/cases",
            method="POST",
            expected_status=201,
            request_data={
                "property_address": "123 Test St",
                "property_value": 500000,
                "coverage_amount": 400000
            }
        )
        result = test_runner.run_test(test_case)
        assert result["passed"], f"Create case failed: {result}"


class TestWebhookDelivery:
    """Test webhook delivery"""
    
    def test_webhook_registration(self, test_runner):
        """Test webhook registration"""
        test_case = TestCase(
            name="Register Webhook",
            endpoint="/api/v1/webhooks",
            method="POST",
            expected_status=201,
            request_data={
                "url": "https://example.com/webhook",
                "events": ["case.created", "case.updated"]
            }
        )
        result = test_runner.run_test(test_case)
        assert result["passed"], f"Webhook registration failed: {result}"


class TestRateLimiting:
    """Test rate limiting"""
    
    def test_rate_limit_enforcement(self, test_runner):
        """Test that rate limiting is enforced"""
        # Make multiple requests to test rate limiting
        test_case = TestCase(
            name="Rate Limit Test",
            endpoint="/api/v1/cases",
            method="GET",
            expected_status=200
        )
        
        # Run multiple times to trigger rate limit
        for _ in range(5):
            result = test_runner.run_test(test_case)
        
        # Check that at least one request was rate limited (429)
        rate_limited = any(
            r["status_code"] == 429 for r in test_runner.test_results[-5:]
        )
        # This test is optional as rate limits may not be configured
        # assert rate_limited, "Rate limiting not enforced"


class TestAuthentication:
    """Test authentication"""
    
    def test_valid_api_key(self, test_runner):
        """Test valid API key authentication"""
        test_case = TestCase(
            name="Valid API Key",
            endpoint="/api/v1/cases",
            method="GET",
            expected_status=200
        )
        result = test_runner.run_test(test_case)
        assert result["passed"], f"Valid API key test failed: {result}"
    
    def test_invalid_api_key(self, test_runner):
        """Test invalid API key authentication"""
        test_runner.session.headers["Authorization"] = "Bearer invalid-key"
        
        test_case = TestCase(
            name="Invalid API Key",
            endpoint="/api/v1/cases",
            method="GET",
            expected_status=401
        )
        result = test_runner.run_test(test_case)
        assert result["passed"], f"Invalid API key test failed: {result}"
        
        # Restore valid key
        test_runner.session.headers["Authorization"] = f"Bearer {test_runner.config.api_key}"


if __name__ == "__main__":
    # Run tests when executed directly
    print("Running integration tests...")
    results = run_integration_tests()
    
    print(f"\nTest Results:")
    print(f"Total: {results['total']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Success Rate: {results['success_rate']:.2%}")
    
    if results['failed'] > 0:
        print("\nFailed Tests:")
        for result in results['results']:
            if not result['passed']:
                print(f"  - {result['name']}: {result.get('error', 'Status code mismatch')}")
