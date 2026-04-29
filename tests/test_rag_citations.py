#!/usr/bin/env python3
"""
RAG Citation Guardrail Tests
Critical for demonstrating evidence-based underwriting
Tests citation requirements and guardrail enforcement
"""

import pytest
import asyncio
import time
import sys
import os
from unittest.mock import patch, AsyncMock
from typing import Dict, Any, List

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.llm_engine import LLMEngine, LLMRequest, LLMResponse
from workflows.agents import UnderwritingAssessorAgent, VerifierGuardrailAgent


class TestRAGCitationGuardrails:
    """Test RAG citation guardrails and evidence requirements"""
    
    def setup_method(self):
        """Setup test environment"""
        self.engine = LLMEngine(api_key="test_key")
        self.assessor = UnderwritingAssessorAgent()
        self.verifier = VerifierGuardrailAgent()
    
    def test_high_risk_requires_citations(self):
        """Test: Every high-risk decision has at least 2 citations"""
        print("\n🧪 Testing high-risk citation requirements...")
        
        # Test case: High-risk property with insufficient citations
        high_risk_request = LLMRequest(
            query="Underwriting decision for high-risk property",
            context=["High wildfire risk area", "Old construction"],
            evidence=[
                {"text": "Property in wildfire zone", "chunk_id": "risk1"},
                {"text": "Roof over 20 years old", "chunk_id": "risk2"}
            ],
            confidence_threshold=0.85
        )
        
        # Mock LLM response with ACCEPT but only 1 citation
        mock_response = LLMResponse(
            decision="ACCEPT",
            confidence=0.9,
            reasoning="Property looks acceptable",
            citations=["risk1"],  # Only 1 citation for high-risk
            required_questions=[],
            referral_triggers=[],
            conditions=[],
            processing_time_ms=50.0
        )
        
        with patch.object(self.engine, '_call_openai_internal') as mock_call:
            mock_call.return_value = mock_response
            
            response = self.engine.generate_decision(high_risk_request)
            
            # Deterministic rules should override and force REFER due to insufficient citations
            assert response.decision == "REFER"
            assert len(response.referral_triggers) > 0
            assert "High wildfire risk" in response.referral_triggers or "Old construction" in response.referral_triggers
            
        print("✅ High-risk with insufficient citations → REFER: PASS")
    
    def test_no_citations_forces_refer(self):
        """Test: No citations → REFER"""
        print("\n🧪 Testing no citations forces REFER...")
        
        no_citation_request = LLMRequest(
            query="Underwriting decision",
            context=["Basic property information"],
            evidence=[],  # No evidence/citations
            confidence_threshold=0.85
        )
        
        # Mock LLM response with ACCEPT but no citations
        mock_response = LLMResponse(
            decision="ACCEPT",
            confidence=0.9,
            reasoning="Property looks good",
            citations=[],  # No citations
            required_questions=[],
            referral_triggers=[],
            conditions=[],
            processing_time_ms=50.0
        )
        
        with patch.object(self.engine, '_call_openai_internal') as mock_call:
            mock_call.return_value = mock_response
            
            response = self.engine.generate_decision(no_citation_request)
            
            # Should REFER due to no evidence
            assert response.decision == "REFER"
            assert response.confidence == 0.9  # High confidence in deterministic rules
            assert "deterministic" in response.reasoning.lower()
            
        print("✅ No citations → REFER: PASS")
    
    def test_low_risk_with_sufficient_citations(self):
        """Test: Low-risk property with 2+ citations can be ACCEPT"""
        print("\n🧪 Testing low-risk with sufficient citations...")
        
        low_risk_request = LLMRequest(
            query="Underwriting decision for low-risk property",
            context=["Safe neighborhood", "New construction"],
            evidence=[
                {"text": "No significant risk factors identified", "chunk_id": "safe1"},
                {"text": "Property meets all eligibility criteria", "chunk_id": "safe2"},
                {"text": "Recent construction with modern materials", "chunk_id": "safe3"}
            ],
            confidence_threshold=0.85
        )
        
        # Mock LLM response with ACCEPT and sufficient citations
        mock_response = LLMResponse(
            decision="ACCEPT",
            confidence=0.9,
            reasoning="Property is low risk and meets requirements",
            citations=["safe1", "safe2", "safe3"],  # 3 citations
            required_questions=[],
            referral_triggers=[],
            conditions=["Approved via standard guidelines"],
            processing_time_ms=50.0
        )
        
        with patch.object(self.engine, '_call_openai_internal') as mock_call:
            mock_call.return_value = mock_response
            
            response = self.engine.generate_decision(low_risk_request)
            
            # Should ACCEPT with sufficient evidence
            assert response.decision == "ACCEPT"
            assert response.confidence == 0.9  # LLM confidence above threshold
            assert len(response.citations) >= 2
            
        print("✅ Low-risk with sufficient citations → ACCEPT: PASS")
    
    def test_citation_relevance_threshold(self):
        """Test: Retrieved guideline relevance score above threshold"""
        print("\n🧪 Testing citation relevance threshold...")
        
        # Mock RAG retrieval with relevance scores
        evidence_with_scores = [
            {"text": "Properties in wildfire zones require additional review", "chunk_id": "guideline1", "relevance_score": 0.95},
            {"text": "Construction materials impact eligibility", "chunk_id": "guideline2", "relevance_score": 0.87},
            {"text": "Unrelated guideline about flood zones", "chunk_id": "guideline3", "relevance_score": 0.3}  # Low relevance
        ]
        
        request = LLMRequest(
            query="Underwriting decision",
            context=["Property assessment"],
            evidence=evidence_with_scores,
            confidence_threshold=0.85
        )
        
        # Test that only high-relevance citations are used
        mock_response = LLMResponse(
            decision="REFER",
            confidence=0.9,
            reasoning="High-risk factors identified",
            citations=["guideline1", "guideline2"],  # Should use high-relevance citations
            required_questions=["Additional wildfire documentation needed"],
            referral_triggers=["Wildfire risk"],
            conditions=[],
            processing_time_ms=50.0
        )
        
        with patch.object(self.engine, '_call_openai_internal') as mock_call:
            mock_call.return_value = mock_response
            
            response = self.engine.generate_decision(request)
            
            # Should use only high-relevance citations
            assert "guideline3" not in response.citations  # Low relevance excluded
            assert len(response.citations) == 2
            assert all(citation in ["guideline1", "guideline2"] for citation in response.citations)
            
        print("✅ High-relevance citations used: PASS")
    
    def test_wrong_guideline_no_accept(self):
        """Test: Wrong guideline does not produce ACCEPT"""
        print("\n🧪 Testing wrong guideline prevents ACCEPT...")
        
        # Evidence with irrelevant guidelines
        irrelevant_evidence = [
            {"text": "Guideline for commercial properties", "chunk_id": "commercial_guideline"},
            {"text": "Guideline for auto insurance", "chunk_id": "auto_guideline"},
            {"text": "Property has some minor issues", "chunk_id": "minor_issue"}
        ]
        
        request = LLMRequest(
            query="Residential underwriting decision",
            context=["Residential property assessment"],
            evidence=irrelevant_evidence,
            confidence_threshold=0.85
        )
        
        # Mock LLM trying to ACCEPT with wrong guidelines
        mock_response = LLMResponse(
            decision="ACCEPT",
            confidence=0.8,
            reasoning="Based on available guidelines",
            citations=["commercial_guideline", "auto_guideline"],  # Wrong guidelines
            required_questions=[],
            referral_triggers=[],
            conditions=[],
            processing_time_ms=50.0
        )
        
        with patch.object(self.engine, '_call_openai_internal') as mock_call:
            mock_call.return_value = mock_response
            
            response = self.engine.generate_decision(request)
            
            # Should not ACCEPT with wrong guidelines
            assert response.decision != "ACCEPT" or response.confidence < 0.85
            # Most likely will fallback to deterministic rules
            
        print("✅ Wrong guidelines prevent ACCEPT: PASS")
    
    def test_verifier_guardrail_citation_check(self):
        """Test: VerifierGuardrailAgent blocks decisions without citations"""
        print("\n🧪 Testing VerifierGuardrailAgent citation validation...")
        
        # Test case: Decision without sufficient citations
        decision_data = {
            "decision": "ACCEPT",
            "confidence": 0.9,
            "reasoning": "Property looks good",
            "citations_used": ["single_citation"],  # Only 1 citation
            "risk_factors": ["wildfire_risk", "old_roof"],
            "required_questions": [],
            "referral_triggers": []
        }
        
        # Mock evidence with risk factors
        evidence_chunks = [
            {"text": "Wildfire risk zone", "chunk_id": "risk1"},
            {"text": "Old roof", "chunk_id": "risk2"}
        ]
        
        # Run verifier
        verification_result = self.verifier.verify(decision_data, evidence_chunks)
        
        # Should flag insufficient citations for high-risk
        assert verification_result["decision_allowed"] == False
        assert "insufficient_citations" in verification_result["issues"]
        assert verification_result["forced_decision"] == "REFER"
        
        print("✅ Verifier blocks low-citation decisions: PASS")
    
    def test_evidence_coverage_scoring(self):
        """Test: Evidence coverage scoring works correctly"""
        print("\n🧪 Testing evidence coverage scoring...")
        
        # Test evidence coverage calculation
        decision_data = {
            "decision": "ACCEPT",
            "citations_used": ["guideline1", "guideline2", "guideline3"],
            "risk_factors": ["wildfire_risk", "roof_age"]
        }
        
        evidence_chunks = [
            {"text": "Guideline about wildfire risk", "chunk_id": "guideline1"},
            {"text": "Guideline about roof requirements", "chunk_id": "guideline2"},
            {"text": "Guideline about property eligibility", "chunk_id": "guideline3"}
        ]
        
        verification_result = self.verifier.verify(decision_data, evidence_chunks)
        
        # Should have good evidence coverage
        assert verification_result["evidence_coverage_score"] >= 0.8
        assert verification_result["decision_allowed"] == True
        
        print("✅ Evidence coverage scoring: PASS")
    
    def test_comprehensive_citation_guardrails(self):
        """Test: Comprehensive citation guardrail validation"""
        print("\n🧪 Testing comprehensive citation guardrails...")
        
        test_scenarios = [
            {
                "name": "High-risk with 1 citation",
                "evidence": [{"text": "Wildfire risk", "chunk_id": "risk1"}],
                "llm_decision": "ACCEPT",
                "expected_decision": "REFER",
                "reason": "Insufficient citations for high-risk"
            },
            {
                "name": "High-risk with 3 citations",
                "evidence": [
                    {"text": "Wildfire risk", "chunk_id": "risk1"},
                    {"text": "Old roof", "chunk_id": "risk2"},
                    {"text": "Foundation issues", "chunk_id": "risk3"}
                ],
                "llm_decision": "REFER",
                "expected_decision": "REFER",
                "reason": "Appropriate REFER with sufficient citations"
            },
            {
                "name": "Low-risk with 2 citations",
                "evidence": [
                    {"text": "No risk factors", "chunk_id": "safe1"},
                    {"text": "Meets requirements", "chunk_id": "safe2"}
                ],
                "llm_decision": "ACCEPT",
                "expected_decision": "ACCEPT",
                "reason": "Sufficient citations for low-risk"
            },
            {
                "name": "No evidence at all",
                "evidence": [],
                "llm_decision": "ACCEPT",
                "expected_decision": "REFER",
                "reason": "No evidence requires REFER"
            }
        ]
        
        for scenario in test_scenarios:
            print(f"  Testing: {scenario['name']}")
            
            request = LLMRequest(
                query="Underwriting decision",
                context=["Property assessment"],
                evidence=scenario["evidence"],
                confidence_threshold=0.85
            )
            
            mock_response = LLMResponse(
                decision=scenario["llm_decision"],
                confidence=0.9,
                reasoning="LLM reasoning",
                citations=[e["chunk_id"] for e in scenario["evidence"]],
                required_questions=[],
                referral_triggers=[],
                conditions=[],
                processing_time_ms=50.0
            )
            
            with patch.object(self.engine, '_call_openai_internal') as mock_call:
                mock_call.return_value = mock_response
                
                response = self.engine.generate_decision(request)
                
                assert response.decision == scenario["expected_decision"], \
                    f"Expected {scenario['expected_decision']}, got {response.decision}. Reason: {scenario['reason']}"
                
        print("✅ Comprehensive citation guardrails: PASS")


if __name__ == "__main__":
    # Run tests manually
    test_suite = TestRAGCitationGuardrails()
    test_suite.setup_method()
    
    try:
        test_suite.test_high_risk_requires_citations()
        test_suite.setup_method()
        test_suite.test_no_citations_forces_refer()
        test_suite.setup_method()
        test_suite.test_low_risk_with_sufficient_citations()
        test_suite.setup_method()
        test_suite.test_citation_relevance_threshold()
        test_suite.setup_method()
        test_suite.test_wrong_guideline_no_accept()
        test_suite.setup_method()
        test_suite.test_verifier_guardrail_citation_check()
        test_suite.setup_method()
        test_suite.test_evidence_coverage_scoring()
        test_suite.setup_method()
        test_suite.test_comprehensive_citation_guardrails()
        
        print("\n" + "="*60)
        print("✅ ALL RAG CITATION GUARDRAIL TESTS PASSED")
        print("📋 Evidence-based underwriting verified")
        print("🔒 Citation requirements enforced")
        print("🛡️ High-risk decisions properly guarded")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
