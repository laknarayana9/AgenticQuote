#!/usr/bin/env python3
"""
Performance Load Test
Realistic load testing for production evidence
Tests 10, 50, 100, 500 users with actual performance metrics
"""

import asyncio
import time
import statistics
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.complete import create_complete_app


class LoadTestRunner:
    """Load test runner for realistic performance testing"""
    
    def __init__(self):
        app = create_complete_app()
        self.client = TestClient(app)
        self.results = []
    
    def create_test_submission(self, variant: str = "normal") -> Dict[str, Any]:
        """Create test submission for load testing"""
        base_submission = {
            "applicant": {
                "full_name": f"Load Test User {variant}",
                "birth_date": "1980-01-01"
            },
            "risk": {
                "property_address": f"123 Load Test St, Test City, CA 94536",
                "property_type": "single_family",
                "year_built": 2015,
                "square_footage": 2000,
                "roof_type": "asphalt_shingle",
                "foundation_type": "slab",
                "construction_type": "frame"
            },
            "coverage_request": {
                "coverage_amount": 500000,
                "deductible": 1000
            }
        }
        
        # Add variation for different test scenarios
        if variant == "high_risk":
            base_submission["risk"]["year_built"] = 1965
            base_submission["risk"]["roof_type"] = "wood_shake"
            base_submission["risk"]["property_address"] = "456 Fire Zone Rd, High Risk City, CA 94569"
        elif variant == "large_coverage":
            base_submission["coverage_request"]["coverage_amount"] = 1000000
            base_submission["risk"]["square_footage"] = 4000
        elif variant == "hitl":
            base_submission["risk"]["roof_type"] = ""  # Missing info
            base_submission["risk"]["foundation_type"] = ""  # Missing info
        
        return base_submission
    
    def single_request(self, user_id: int, variant: str = "normal") -> Dict[str, Any]:
        """Execute single request and return metrics"""
        start_time = time.time()
        
        try:
            submission = self.create_test_submission(variant)
            response = self.client.post("/quote/ho3", json=submission)
            
            end_time = time.time()
            response_time_ms = (end_time - start_time) * 1000
            
            result = {
                "user_id": user_id,
                "variant": variant,
                "response_time_ms": response_time_ms,
                "status_code": response.status_code,
                "success": response.status_code == 200,
                "timestamp": start_time
            }
            
            if response.status_code == 200:
                data = response.json()
                result["decision"] = data.get("decision", {}).get("decision", "UNKNOWN")
                result["confidence"] = data.get("decision", {}).get("confidence", 0)
                result["requires_hitl"] = data.get("requires_human_review", False)
            else:
                result["error"] = response.text
            
            return result
            
        except Exception as e:
            end_time = time.time()
            return {
                "user_id": user_id,
                "variant": variant,
                "response_time_ms": (end_time - start_time) * 1000,
                "status_code": 0,
                "success": False,
                "error": str(e),
                "timestamp": start_time
            }
    
    def run_load_test(self, concurrent_users: int, total_requests: int, variant: str = "normal") -> Dict[str, Any]:
        """Run load test with specified parameters"""
        print(f"\n Load Test: {concurrent_users} concurrent users, {total_requests} total requests")
        print(f"   Variant: {variant}")
        
        start_time = time.time()
        results = []
        
        # Use ThreadPoolExecutor for concurrent requests
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            # Submit all requests
            futures = []
            for i in range(total_requests):
                user_id = i % concurrent_users
                future = executor.submit(self.single_request, user_id, variant)
                futures.append(future)
            
            # Collect results
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                
                # Progress indicator
                if len(results) % 10 == 0:
                    print(f"   Completed: {len(results)}/{total_requests}")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Calculate metrics
        successful_results = [r for r in results if r["success"]]
        failed_results = [r for r in results if not r["success"]]
        
        response_times = [r["response_time_ms"] for r in successful_results]
        
        if response_times:
            metrics = {
                "test_config": {
                    "concurrent_users": concurrent_users,
                    "total_requests": total_requests,
                    "variant": variant,
                    "total_time_seconds": total_time
                },
                "performance": {
                    "requests_per_second": total_requests / total_time,
                    "success_rate": len(successful_results) / total_requests,
                    "error_rate": len(failed_results) / total_requests,
                    "p50_ms": statistics.median(response_times),
                    "p95_ms": self._percentile(response_times, 95),
                    "p99_ms": self._percentile(response_times, 99),
                    "avg_ms": statistics.mean(response_times),
                    "min_ms": min(response_times),
                    "max_ms": max(response_times)
                },
                "decisions": self._analyze_decisions(successful_results),
                "errors": self._analyze_errors(failed_results),
                "raw_results": results
            }
        else:
            metrics = {
                "test_config": {
                    "concurrent_users": concurrent_users,
                    "total_requests": total_requests,
                    "variant": variant,
                    "total_time_seconds": total_time
                },
                "performance": {
                    "requests_per_second": 0,
                    "success_rate": 0,
                    "error_rate": 1.0
                },
                "errors": {"all_requests_failed": True},
                "raw_results": results
            }
        
        return metrics
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = (percentile / 100) * (len(sorted_data) - 1)
        lower = int(index)
        upper = min(lower + 1, len(sorted_data) - 1)
        weight = index - lower
        return sorted_data[lower] * (1 - weight) + sorted_data[upper] * weight
    
    def _analyze_decisions(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze decision distribution"""
        decisions = {}
        hitl_count = 0
        confidence_scores = []
        
        for result in results:
            decision = result.get("decision", "UNKNOWN")
            decisions[decision] = decisions.get(decision, 0) + 1
            
            if result.get("requires_hitl", False):
                hitl_count += 1
            
            confidence = result.get("confidence", 0)
            if confidence > 0:
                confidence_scores.append(confidence)
        
        analysis = {
            "decision_distribution": decisions,
            "hitl_rate": hitl_count / len(results) if results else 0
        }
        
        if confidence_scores:
            analysis["avg_confidence"] = statistics.mean(confidence_scores)
            analysis["min_confidence"] = min(confidence_scores)
            analysis["max_confidence"] = max(confidence_scores)
        
        return analysis
    
    def _analyze_errors(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze error patterns"""
        if not results:
            return {}
        
        error_types = {}
        status_codes = {}
        
        for result in results:
            status_code = result.get("status_code", 0)
            status_codes[status_code] = status_codes.get(status_code, 0) + 1
            
            error = result.get("error", "Unknown error")
            error_types[error] = error_types.get(error, 0) + 1
        
        return {
            "error_types": error_types,
            "status_codes": status_codes
        }
    
    def run_comprehensive_load_tests(self) -> Dict[str, Any]:
        """Run comprehensive load test suite"""
        print(" Starting Comprehensive Load Test Suite")
        print("=" * 60)
        
        test_scenarios = [
            {"users": 10, "requests": 50, "variant": "normal"},
            {"users": 50, "requests": 100, "variant": "normal"},
            {"users": 100, "requests": 200, "variant": "normal"},
            {"users": 500, "requests": 500, "variant": "normal"},
            {"users": 50, "requests": 100, "variant": "high_risk"},
            {"users": 50, "requests": 100, "variant": "hitl"},
        ]
        
        all_results = {}
        
        for scenario in test_scenarios:
            scenario_name = f"{scenario['users']}users_{scenario['requests']}req_{scenario['variant']}"
            print(f"\n Running: {scenario_name}")
            
            result = self.run_load_test(
                scenario["users"],
                scenario["requests"],
                scenario["variant"]
            )
            
            all_results[scenario_name] = result
            
            # Print summary
            perf = result["performance"]
            print(f"    RPS: {perf['requests_per_second']:.1f}")
            print(f"    Success Rate: {perf['success_rate']*100:.1f}%")
            print(f"    p95: {perf['p95_ms']:.1f}ms")
            print(f"    p99: {perf['p99_ms']:.1f}ms")
        
        return all_results


def main():
    """Run load tests and display results"""
    runner = LoadTestRunner()
    
    try:
        results = runner.run_comprehensive_load_tests()
        
        print("\n" + "=" * 60)
        print(" LOAD TEST RESULTS SUMMARY")
        print("=" * 60)
        
        for scenario_name, result in results.items():
            perf = result["performance"]
            config = result["test_config"]
            
            print(f"\n {scenario_name.replace('_', ' ').title()}")
            print(f"   Users: {config['concurrent_users']}, Requests: {config['total_requests']}")
            print(f"   RPS: {perf['requests_per_second']:.1f}")
            print(f"   Success Rate: {perf['success_rate']*100:.1f}%")
            print(f"   p50: {perf.get('p50_ms', 0):.1f}ms")
            print(f"   p95: {perf['p95_ms']:.1f}ms")
            print(f"   p99: {perf['p99_ms']:.1f}ms")
            
            if "decisions" in result:
                decisions = result["decisions"]
                print(f"   HITL Rate: {decisions.get('hitl_rate', 0)*100:.1f}%")
                if "avg_confidence" in decisions:
                    print(f"   Avg Confidence: {decisions['avg_confidence']:.2f}")
        
        # Performance targets check
        print(f"\n Performance Targets Analysis:")
        print(f"   Target p95: 200ms")
        print(f"   Target RPS: 1000+")
        print(f"   Target Success Rate: 99%+")
        
        for scenario_name, result in results.items():
            if "normal" in scenario_name:
                perf = result["performance"]
                p95_ok = perf["p95_ms"] <= 200
                rps_ok = perf["requests_per_second"] >= 100
                success_ok = perf["success_rate"] >= 0.99
                
                status = "" if (p95_ok and rps_ok and success_ok) else ""
                print(f"   {scenario_name}: {status}")
        
        return results
        
    except Exception as e:
        print(f"\n Load test failed: {e}")
        raise


if __name__ == "__main__":
    main()
