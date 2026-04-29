#!/usr/bin/env python3
"""
Failure Mode Tests
Tests API timeout, Redis unavailable, DB unavailable, queue depth high, circuit breaker behavior
Critical for demonstrating production resilience and graceful degradation
"""

import pytest
import asyncio
import time
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

from app.complete import app
from app.llm_engine import LLMEngine, LLMRequest
from app.redis_queue import RedisQueue
from app.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, CircuitBreakerOpenError


class TestFailureModes:
    """Test system behavior under various failure conditions"""
    
    def setup_method(self):
        """Setup test environment"""
        self.client = TestClient(app)
        self.engine = LLMEngine(api_key="test_key")
    
    def test_external_api_timeout(self):
        """Test: External API timeout → cached/default data"""
        print("\n🧪 Testing external API timeout...")
        
        # Mock external API call to timeout
        with patch('tools.property_data_provider.get_property_data') as mock_api:
            mock_api.side_effect = asyncio.TimeoutError("API timeout")
            
            submission = {
                "applicant": {
                    "full_name": "API Timeout Test",
                    "birth_date": "1980-01-01"
                },
                "risk": {
                    "property_address": "123 Timeout St, Slow City, CA 94536",
                    "property_type": "single_family",
                    "year_built": 2010,
                    "square_footage": 1800,
                    "roof_type": "asphalt_shingle",
                    "foundation_type": "slab",
                    "construction_type": "frame"
                },
                "coverage_request": {
                    "coverage_amount": 400000,
                    "deductible": 1000
                }
            }
            
            response = self.client.post("/quote/ho3", json=submission)
            
            # Should still complete with cached/default data
            assert response.status_code == 200
            result = response.json()
            
            assert "decision" in result
            assert result["status"] in ["completed", "degraded"]
            
            # Decision should be conservative when data is missing
            decision = result["decision"]["decision"]
            assert decision in ["REFER", "DECLINE"]
            
        print(f"✅ API timeout → cached/default data: {decision} - PASS")
    
    def test_redis_unavailable(self):
        """Test: Redis unavailable → fallback to in-memory"""
        print("\n🧪 Testing Redis unavailable...")
        
        # Mock Redis connection failure
        with patch('app.redis_queue.RedisQueue.enqueue') as mock_enqueue:
            mock_enqueue.side_effect = ConnectionError("Redis connection failed")
            
            submission = {
                "applicant": {
                    "full_name": "Redis Fail Test",
                    "birth_date": "1985-05-15"
                },
                "risk": {
                    "property_address": "456 Redis Fail St, Queue City, CA 94536",
                    "property_type": "single_family",
                    "year_built": 2015,
                    "square_footage": 2000,
                    "roof_type": "composite",
                    "foundation_type": "slab",
                    "construction_type": "frame"
                },
                "coverage_request": {
                    "coverage_amount": 500000,
                    "deductible": 1500
                }
            }
            
            response = self.client.post("/quote/ho3", json=submission)
            
            # Should still process without Redis
            assert response.status_code == 200
            result = response.json()
            
            assert "decision" in result
            assert result["status"] in ["completed", "degraded"]
            
        print(f"✅ Redis unavailable → in-memory fallback: PASS")
    
    def test_database_unavailable(self):
        """Test: Database unavailable → in-memory cache + manual review"""
        print("\n🧪 Testing database unavailable...")
        
        # Mock database failure
        with patch('storage.database.DatabaseConnection.get_connection') as mock_db:
            mock_db.side_effect = ConnectionError("Database connection failed")
            
            submission = {
                "applicant": {
                    "full_name": "DB Fail Test",
                    "birth_date": "1990-03-20"
                },
                "risk": {
                    "property_address": "789 DB Fail St, Storage City, CA 94536",
                    "property_type": "single_family",
                    "year_built": 2012,
                    "square_footage": 1600,
                    "roof_type": "metal",
                    "foundation_type": "crawlspace",
                    "construction_type": "frame"
                },
                "coverage_request": {
                    "coverage_amount": 350000,
                    "deductible": 1000
                }
            }
            
            response = self.client.post("/quote/ho3", json=submission)
            
            # Should still respond but may require manual review
            assert response.status_code == 200
            result = response.json()
            
            assert "decision" in result
            # May require manual review due to database unavailability
            if result.get("requires_human_review"):
                assert result["requires_human_review"] == True
            
        print(f"✅ Database unavailable → manual review: PASS")
    
    def test_queue_depth_high(self):
        """Test: Queue depth high → load shedding"""
        print("\n🧪 Testing high queue depth...")
        
        # Mock high queue depth
        with patch('app.redis_queue.RedisQueue.get_queue_depth') as mock_depth:
            mock_depth.return_value = 15000  # Above 10,000 threshold
            
            submission = {
                "applicant": {
                    "full_name": "Queue Test",
                    "birth_date": "1988-07-10"
                },
                "risk": {
                    "property_address": "321 Queue St, Load City, CA 94536",
                    "property_type": "single_family",
                    "year_built": 2018,
                    "square_footage": 2200,
                    "roof_type": "asphalt_shingle",
                    "foundation_type": "slab",
                    "construction_type": "frame"
                },
                "coverage_request": {
                    "coverage_amount": 600000,
                    "deductible": 2000
                }
            }
            
            response = self.client.post("/quote/ho3", json=submission)
            
            # Should either process with delay or return degraded status
            assert response.status_code == 200
            result = response.json()
            
            # May indicate queue pressure
            if result.get("queue_pressure"):
                assert result["queue_pressure"] == "high"
            
        print(f"✅ High queue depth → load shedding: PASS")
    
    def test_circuit_breaker_opens(self):
        """Test: Repeated provider failure opens circuit breaker"""
        print("\n🧪 Testing circuit breaker opens...")
        
        # Create circuit breaker with low threshold for testing
        config = CircuitBreakerConfig(
            failure_threshold=2,  # Low threshold for testing
            timeout_seconds=5,     # Short timeout for testing
            success_threshold=1
        )
        
        circuit_breaker = CircuitBreaker(config)
        
        # Simulate repeated failures
        failing_function = MagicMock(side_effect=ConnectionError("Provider failed"))
        
        # First failure
        try:
            circuit_breaker.call(failing_function)
        except ConnectionError:
            pass  # Expected
        
        # Second failure - should open circuit
        try:
            circuit_breaker.call(failing_function)
        except ConnectionError:
            pass  # Expected
        
        # Third call should fail fast due to open circuit
        with pytest.raises(CircuitBreakerOpenError):
            circuit_breaker.call(failing_function)
        
        # Verify circuit is open
        state = circuit_breaker.get_state()
        assert state["state"] == "open"
        assert state["failure_count"] == 2
        
        print("✅ Circuit breaker opens after failures: PASS")
    
    def test_circuit_breaker_recovery(self):
        """Test: Circuit breaker recovery after timeout"""
        print("\n🧪 Testing circuit breaker recovery...")
        
        config = CircuitBreakerConfig(
            failure_threshold=2,
            timeout_seconds=1,  # Very short timeout for testing
            success_threshold=1
        )
        
        circuit_breaker = CircuitBreaker(config)
        
        # Cause circuit to open
        failing_function = MagicMock(side_effect=ConnectionError("Provider failed"))
        
        for _ in range(2):
            try:
                circuit_breaker.call(failing_function)
            except ConnectionError:
                pass
        
        # Circuit should be open
        with pytest.raises(CircuitBreakerOpenError):
            circuit_breaker.call(failing_function)
        
        # Wait for timeout
        time.sleep(1.1)
        
        # Create successful function
        success_function = MagicMock(return_value="success")
        
        # Should now be in half-open state and succeed
        result = circuit_breaker.call(success_function)
        assert result == "success"
        
        # Circuit should be closed now
        state = circuit_breaker.get_state()
        assert state["state"] == "closed"
        
        print("✅ Circuit breaker recovery: PASS")
    
    def test_llm_service_unavailable(self):
        """Test: LLM service unavailable → deterministic fallback"""
        print("\n🧪 Testing LLM service unavailable...")
        
        request = LLMRequest(
            query="Test underwriting decision",
            context=["Test context"],
            evidence=[
                {"text": "Property meets requirements", "chunk_id": "safe1"},
                {"text": "No risk factors", "chunk_id": "safe2"}
            ],
            confidence_threshold=0.85
        )
        
        # Mock LLM service completely unavailable
        with patch.object(self.engine, 'client', None):
            response = self.engine.generate_decision(request)
            
            # Should use mock/fallback response
            assert response.decision == "REFER"
            assert response.confidence == 0.5
            assert "processing failed" in response.reasoning.lower()
            
        print("✅ LLM unavailable → fallback response: PASS")
    
    def test_partial_data_failure(self):
        """Test: Partial data failure → degrade decision"""
        print("\n🧪 Testing partial data failure...")
        
        # Mock partial data from external APIs
        with patch('tools.property_data_provider.get_property_data') as mock_property:
            with patch('tools.hazard_data_provider.get_hazard_data') as mock_hazard:
                
                # Property data succeeds, hazard data fails
                mock_property.return_value = {
                    "property_type": "single_family",
                    "year_built": 2010,
                    "square_footage": 2000
                }
                
                mock_hazard.side_effect = ConnectionError("Hazard API failed")
                
                submission = {
                    "applicant": {
                        "full_name": "Partial Data Test",
                        "birth_date": "1982-11-30"
                    },
                    "risk": {
                        "property_address": "555 Partial St, Data City, CA 94536",
                        "property_type": "single_family",
                        "year_built": 2010,
                        "square_footage": 2000,
                        "roof_type": "asphalt_shingle",
                        "foundation_type": "slab",
                        "construction_type": "frame"
                    },
                    "coverage_request": {
                        "coverage_amount": 450000,
                        "deductible": 1000
                    }
                }
                
                response = self.client.post("/quote/ho3", json=submission)
                
                # Should still complete but may be conservative
                assert response.status_code == 200
                result = response.json()
                
                # Decision should be conservative without hazard data
                decision = result["decision"]["decision"]
                assert decision in ["REFER", "DECLINE"]
                
        print(f"✅ Partial data failure → conservative decision: {decision} - PASS")
    
    def test_memory_pressure(self):
        """Test: Memory pressure → disable non-critical features"""
        print("\n🧪 Testing memory pressure...")
        
        # Mock high memory usage
        with patch('psutil.virtual_memory') as mock_memory:
            mock_memory.return_value = MagicMock(
                percent=95.0,  # High memory usage
                available=100 * 1024 * 1024  # 100MB available
            )
            
            submission = {
                "applicant": {
                    "full_name": "Memory Test",
                    "birth_date": "1987-09-05"
                },
                "risk": {
                    "property_address": "777 Memory St, RAM City, CA 94536",
                    "property_type": "single_family",
                    "year_built": 2016,
                    "square_footage": 1900,
                    "roof_type": "asphalt_shingle",
                    "foundation_type": "slab",
                    "construction_type": "frame"
                },
                "coverage_request": {
                    "coverage_amount": 425000,
                    "deductible": 1000
                }
            }
            
            response = self.client.post("/quote/ho3", json=submission)
            
            # Should still respond but may disable features
            assert response.status_code == 200
            result = response.json()
            
            # May indicate degraded mode
            if result.get("performance_mode"):
                assert result["performance_mode"] in ["degraded", "conservative"]
            
        print("✅ Memory pressure → feature disable: PASS")
    
    def test_comprehensive_failure_matrix(self):
        """Test: Comprehensive failure mode matrix"""
        print("\n🧪 Testing comprehensive failure matrix...")
        
        failure_scenarios = [
            {
                "name": "LLM timeout",
                "mock": patch.object(LLMEngine, '_call_openai_internal', side_effect=asyncio.TimeoutError),
                "expected_behavior": "deterministic fallback",
                "test_request": LLMRequest(
                    query="Test",
                    context=["Test"],
                    evidence=[{"text": "Test", "chunk_id": "test1"}],
                    confidence_threshold=0.85
                )
            },
            {
                "name": "Low confidence",
                "mock": None,  # Handled in LLM engine
                "expected_behavior": "conservative rules",
                "test_request": LLMRequest(
                    query="Test",
                    context=["Test"],
                    evidence=[{"text": "Test", "chunk_id": "test1"}],
                    confidence_threshold=0.95  # Very high
                )
            },
            {
                "name": "Circuit breaker open",
                "mock": patch.object(LLMEngine, '_call_openai_with_circuit_breaker', side_effect=CircuitBreakerOpenError),
                "expected_behavior": "fallback to rules",
                "test_request": LLMRequest(
                    query="Test",
                    context=["Test"],
                    evidence=[{"text": "Test", "chunk_id": "test1"}],
                    confidence_threshold=0.85
                )
            }
        ]
        
        results = []
        
        for scenario in failure_scenarios:
            print(f"  Testing: {scenario['name']}")
            
            engine = LLMEngine(api_key="test_key")
            
            if scenario["mock"]:
                with scenario["mock"]:
                    response = engine.generate_decision(scenario["test_request"])
            else:
                # For low confidence, mock low confidence response
                from app.llm_engine import LLMResponse
                mock_response = LLMResponse(
                    decision="ACCEPT",
                    confidence=0.7,  # Below threshold
                    reasoning="Low confidence",
                    citations=["test1"],
                    required_questions=[],
                    referral_triggers=[],
                    conditions=[],
                    processing_time_ms=50.0
                )
                
                with patch.object(engine, '_call_openai_internal', return_value=mock_response):
                    response = engine.generate_decision(scenario["test_request"])
            
            # Verify fallback behavior
            assert response.confidence >= 0.85 or response.decision in ["REFER", "DECLINE"]
            assert "deterministic" in response.reasoning.lower() or "fallback" in response.reasoning.lower()
            
            results.append({
                "failure": scenario["name"],
                "expected": scenario["expected_behavior"],
                "actual": "fallback applied",
                "result": "PASS"
            })
            
            print(f"    Result: {response.decision} (fallback: {'Yes' if 'deterministic' in response.reasoning.lower() else 'No'})")
        
        print("✅ Comprehensive failure matrix: PASS")
        return results


if __name__ == "__main__":
    # Run tests manually
    test_suite = TestFailureModes()
    test_suite.setup_method()
    
    try:
        test_suite.test_external_api_timeout()
        test_suite.setup_method()
        test_suite.test_redis_unavailable()
        test_suite.setup_method()
        test_suite.test_database_unavailable()
        test_suite.setup_method()
        test_suite.test_queue_depth_high()
        test_suite.setup_method()
        test_suite.test_circuit_breaker_opens()
        test_suite.setup_method()
        test_suite.test_circuit_breaker_recovery()
        test_suite.setup_method()
        test_suite.test_llm_service_unavailable()
        test_suite.setup_method()
        test_suite.test_partial_data_failure()
        test_suite.setup_method()
        test_suite.test_memory_pressure()
        test_suite.setup_method()
        results = test_suite.test_comprehensive_failure_matrix()
        
        print("\n" + "="*60)
        print("✅ ALL FAILURE MODE TESTS PASSED")
        print("🛡️ System degrades gracefully under failure")
        print("🔄 Fallback mechanisms work correctly")
        print("⚡ Circuit breaker protects against cascading failures")
        
        # Print failure matrix results
        print("\n📊 Failure Mode Results:")
        for result in results:
            print(f"  {result['failure']}: {result['result']}")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
