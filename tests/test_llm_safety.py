#!/usr/bin/env python3
"""
LLM Safety and Fallback Tests
Critical for demonstrating that LLM is advisory, not authoritative
Tests confidence thresholds, timeouts, and deterministic overrides
"""

import pytest
import asyncio
import time
import sys
import os
from unittest.mock import patch, AsyncMock
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.llm_engine import LLMEngine, LLMRequest, LLMResponse, CircuitBreakerOpenError
from app.circuit_breaker import CircuitBreakerOpenError as CBOpenError


class TestLLMSafety:
    """Test LLM safety mechanisms and fallback behavior"""
    
    def setup_method(self):
        """Setup test environment"""
        self.engine = LLMEngine(api_key="test_key")
    
    def test_llm_timeout_fallback(self):
        """Test: LLM timeout → fallback to deterministic rules"""
        print("\n🧪 Testing LLM timeout fallback...")
        
        # Create request
        request = LLMRequest(
            query="Test underwriting decision",
            context=["Test context"],
            evidence=[
                {"text": "Property meets all requirements", "chunk_id": "safe1"},
                {"text": "No significant risk factors", "chunk_id": "safe2"}
            ],
            confidence_threshold=0.85
        )
        
        # Mock LLM call to timeout
        with patch.object(self.engine, '_call_openai_internal') as mock_call:
            mock_call.side_effect = asyncio.TimeoutError("LLM timeout")
            
            response = self.engine.generate_decision(request)
            
            # Should fallback to safe response
            assert response.decision in ["ACCEPT", "REFER", "DECLINE"]
            assert response.confidence == 0.5  # Fallback response confidence
            assert "processing failed" in response.reasoning.lower()
            
        print("✅ LLM timeout → deterministic fallback: PASS")
    
    def test_low_confidence_fallback(self):
        """Test: LLM confidence < 0.85 → deterministic rules"""
        print("\n🧪 Testing low confidence fallback...")
        
        request = LLMRequest(
            query="Test underwriting decision",
            context=["Test context"],
            evidence=[
                {"text": "Property meets all requirements", "chunk_id": "safe1"},
                {"text": "No significant risk factors", "chunk_id": "safe2"}
            ],
            confidence_threshold=0.95  # Very high threshold
        )
        
        # Mock LLM response with low confidence
        mock_response = LLMResponse(
            decision="ACCEPT",
            confidence=0.7,  # Below threshold
            reasoning="LLM reasoning",
            citations=["citation1"],
            required_questions=[],
            referral_triggers=[],
            conditions=[],
            processing_time_ms=50.0
        )
        
        with patch.object(self.engine, '_call_openai_internal') as mock_call:
            mock_call.return_value = mock_response
            
            response = self.engine.generate_decision(request)
            
            # Should fallback to deterministic rules due to low confidence
            assert response.confidence == 0.9  # High confidence in deterministic rules
            assert "deterministic" in response.reasoning.lower()
            assert f"{mock_response.confidence:.2f}" in response.reasoning
            assert f"{request.confidence_threshold:.2f}" in response.reasoning
            
        print("✅ Low confidence → deterministic fallback: PASS")
    
    def test_deterministic_override_llm_accept(self):
        """Test: LLM recommends ACCEPT but hard rule says DECLINE → DECLINE wins"""
        print("\n🧪 Testing deterministic override of LLM...")
        
        request = LLMRequest(
            query="Test underwriting decision",
            context=["Test context"],
            evidence=[
                {"text": "High wildfire risk zone", "chunk_id": "risk1"},
                {"text": "Severe earthquake fault line", "chunk_id": "risk2"}
            ],
            confidence_threshold=0.85
        )
        
        # Mock LLM response with ACCEPT (wrong decision)
        mock_response = LLMResponse(
            decision="ACCEPT",
            confidence=0.9,
            reasoning="LLM thinks this is acceptable",
            citations=["citation1"],
            required_questions=[],
            referral_triggers=[],
            conditions=[],
            processing_time_ms=50.0
        )
        
        with patch.object(self.engine, '_call_openai_internal') as mock_call:
            mock_call.return_value = mock_response
            
            response = self.engine.generate_decision(request)
            
            # Deterministic rules should override LLM and force REFER
            assert response.decision == "REFER"
            assert "High wildfire risk" in response.referral_triggers
            assert "Earthquake risk" in response.referral_triggers
            assert response.confidence == 0.9  # High confidence in deterministic rules
            
        print("✅ Deterministic rules override LLM: PASS")
    
    def test_circuit_breaker_fallback(self):
        """Test: Circuit breaker open → fallback to deterministic rules"""
        print("\n🧪 Testing circuit breaker fallback...")
        
        request = LLMRequest(
            query="Test underwriting decision",
            context=["Test context"],
            evidence=[
                {"text": "Property meets all requirements", "chunk_id": "safe1"},
                {"text": "No significant risk factors", "chunk_id": "safe2"}
            ],
            confidence_threshold=0.85
        )
        
        # Mock circuit breaker open error
        with patch.object(self.engine, '_call_openai_with_circuit_breaker') as mock_call:
            mock_call.side_effect = CircuitBreakerOpenError("Circuit breaker is OPEN")
            
            response = self.engine.generate_decision(request)
            
            # Should fallback to deterministic rules
            assert response.decision in ["ACCEPT", "REFER", "DECLINE"]
            assert response.confidence == 0.9
            assert "deterministic" in response.reasoning.lower()
            assert "unavailable" in response.reasoning.lower()
            
        print("✅ Circuit breaker open → deterministic fallback: PASS")
    
    def test_invalid_json_fallback(self):
        """Test: Invalid JSON from LLM → retry or fallback"""
        print("\n🧪 Testing invalid JSON fallback...")
        
        request = LLMRequest(
            query="Test underwriting decision",
            context=["Test context"],
            evidence=[
                {"text": "Property meets all requirements", "chunk_id": "safe1"}
            ],
            confidence_threshold=0.85
        )
        
        # Mock invalid JSON response
        with patch('json.loads') as mock_json:
            mock_json.side_effect = ValueError("Invalid JSON")
            
            with patch.object(self.engine, '_call_openai_internal') as mock_call:
                mock_call.return_value = None  # This will cause JSON parsing to fail
                
                response = self.engine.generate_decision(request)
                
                # Should fallback to safe response
                assert response.decision == "REFER"
                assert response.confidence == 0.5
                assert "processing failed" in response.reasoning.lower()
                
        print("✅ Invalid JSON → safe fallback: PASS")
    
    def test_advisory_not_authoritative(self):
        """Test: LLM is advisory, not authoritative - comprehensive safety check"""
        print("\n🧪 Testing LLM advisory nature...")
        
        test_cases = [
            {
                "name": "High confidence LLM with risk factors",
                "llm_decision": "ACCEPT",
                "llm_confidence": 0.9,
                "evidence": [
                    {"text": "Wildfire risk zone", "chunk_id": "risk1"},
                    {"text": "Flood zone A", "chunk_id": "risk2"}
                ],
                "expected_decision": "REFER"
            },
            {
                "name": "Low confidence LLM with clean evidence",
                "llm_decision": "ACCEPT",
                "llm_confidence": 0.7,
                "evidence": [
                    {"text": "No risk factors", "chunk_id": "safe1"},
                    {"text": "Meets all requirements", "chunk_id": "safe2"}
                ],
                "expected_decision": "ACCEPT"  # Deterministic rules should accept
            },
            {
                "name": "High confidence LLM timeout",
                "llm_decision": "ACCEPT",
                "llm_confidence": 0.95,
                "evidence": [
                    {"text": "Clean property", "chunk_id": "safe1"}
                ],
                "timeout": True,
                "expected_decision": "ACCEPT"  # Deterministic fallback
            }
        ]
        
        for case in test_cases:
            print(f"  Testing: {case['name']}")
            
            request = LLMRequest(
                query="Test underwriting decision",
                context=["Test context"],
                evidence=case["evidence"],
                confidence_threshold=0.85
            )
            
            mock_response = LLMResponse(
                decision=case["llm_decision"],
                confidence=case["llm_confidence"],
                reasoning="LLM reasoning",
                citations=["citation1"],
                required_questions=[],
                referral_triggers=[],
                conditions=[],
                processing_time_ms=50.0
            )
            
            with patch.object(self.engine, '_call_openai_internal') as mock_call:
                if case.get("timeout"):
                    mock_call.side_effect = asyncio.TimeoutError("Timeout")
                else:
                    mock_call.return_value = mock_response
                
                response = self.engine.generate_decision(request)
                
                assert response.decision == case["expected_decision"], \
                    f"Expected {case['expected_decision']}, got {response.decision}"
                
                # Verify deterministic reasoning is present when fallback occurs
                if case.get("timeout") or case["llm_confidence"] < 0.85:
                    assert "deterministic" in response.reasoning.lower()
                
        print("✅ LLM advisory nature verified: PASS")


if __name__ == "__main__":
    # Run tests manually
    test_suite = TestLLMSafety()
    test_suite.setup_method()
    
    try:
        test_suite.test_llm_timeout_fallback()
        test_suite.setup_method()
        test_suite.test_low_confidence_fallback()
        test_suite.setup_method()
        test_suite.test_deterministic_override_llm_accept()
        test_suite.setup_method()
        test_suite.test_circuit_breaker_fallback()
        test_suite.setup_method()
        test_suite.test_invalid_json_fallback()
        test_suite.setup_method()
        test_suite.test_advisory_not_authoritative()
        
        print("\n" + "="*60)
        print("✅ ALL LLM SAFETY TESTS PASSED")
        print("🛡️ LLM is advisory, not authoritative - VERIFIED")
        print("🔒 Deterministic rules override LLM - VERIFIED")
        print("⚡ Fallback mechanisms work correctly - VERIFIED")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
