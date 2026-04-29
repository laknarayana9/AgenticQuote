#!/usr/bin/env python3
"""
LLM Engine for Phase 3 - Advanced AI Integration
Handles GPT-4 integration for underwriting decisions
"""

import os
import json
import logging
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI not available, using mock LLM responses")

# Import circuit breaker for failure tolerance
from .circuit_breaker import circuit_breaker, CircuitBreakerConfig, CircuitBreakerOpenError

logger = logging.getLogger(__name__)


@dataclass
class LLMRequest:
    """Structure for LLM requests"""

    query: str
    context: List[str]
    evidence: List[Dict[str, Any]]
    query_type: str = "underwriting_decision"
    max_tokens: int = 1000
    temperature: float = 0.1
    confidence_threshold: float = 0.85  # Minimum confidence for LLM decisions


@dataclass
class LLMResponse:
    """Structure for LLM responses"""

    decision: str
    confidence: float
    reasoning: str
    citations: List[str]
    required_questions: List[str]
    referral_triggers: List[str]
    conditions: List[str]
    processing_time_ms: float


class LLMEngine:
    """
    LLM-powered decision engine for underwriting

    Features:
    - GPT-4 integration with rate limiting
    - Prompt engineering for underwriting decisions
    - Structured response parsing
    - Fallback to mock responses
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize LLM Engine

        Args:
            api_key: OpenAI API key (if None, uses environment variable)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = None

        if OPENAI_AVAILABLE and self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
                logger.info("✅ OpenAI client initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize OpenAI client: {e}")
                self.client = None
        else:
            logger.warning("⚠️ OpenAI not available, using mock responses")
            self.client = None
        
        # Initialize circuit breaker for LLM calls
        self.circuit_breaker_config = CircuitBreakerConfig(
            failure_threshold=5,      # 5 failures before opening
            timeout_seconds=30,      # 30 seconds timeout
            success_threshold=2       # 2 successes to close
        )
        
        # Apply circuit breaker to OpenAI calls
        if self.client:
            self._call_openai_with_circuit_breaker = circuit_breaker(
                "openai_llm", 
                self.circuit_breaker_config
            )(self._call_openai_internal)

    def generate_decision(self, request: LLMRequest) -> LLMResponse:
        """
        Generate underwriting decision using LLM with confidence-based fallback

        Args:
            request: LLM request with context and evidence

        Returns:
            Structured LLM response or deterministic fallback
        """
        start_time = datetime.now()

        try:
            if self.client:
                response = self._call_openai(request)
            else:
                response = self._mock_response(request)

            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            response.processing_time_ms = processing_time

            # Check confidence threshold and apply fallback if needed
            if response.confidence < request.confidence_threshold:
                logger.warning(
                    f"LLM confidence {response.confidence:.2f} below threshold "
                    f"{request.confidence_threshold:.2f} - applying deterministic fallback"
                )
                return self._deterministic_fallback(request, start_time, response)

            return response

        except (CircuitBreakerOpenError, asyncio.TimeoutError) as e:
            logger.error(f"❌ LLM service unavailable ({type(e).__name__}) - applying deterministic fallback")
            return self._deterministic_fallback(request, start_time, None)
        except Exception as e:
            logger.error(f"❌ LLM generation failed: {e}")
            return self._fallback_response(request, start_time)

    def _call_openai_internal(self, request: LLMRequest, prompt: str) -> LLMResponse:
        """Internal OpenAI API call with timeout enforcement"""

        try:
            # Enforce 2-second timeout using asyncio
            response = asyncio.run(self._call_openai_with_timeout(request, prompt))
            
            # Parse structured response
            content = json.loads(response.choices[0].message.content)
            return self._parse_llm_response(content)

        except asyncio.TimeoutError:
            logger.error("❌ OpenAI API call timed out after 2 seconds")
            raise
        except Exception as e:
            logger.error(f"❌ OpenAI API call failed: {e}")
            raise

    def _call_openai(self, request: LLMRequest) -> LLMResponse:
        """Call OpenAI API with circuit breaker and timeout enforcement"""

        # Build prompt based on query type
        prompt = self._build_prompt(request)

        try:
            # Use circuit breaker protected call
            if hasattr(self, '_call_openai_with_circuit_breaker'):
                return self._call_openai_with_circuit_breaker(request, prompt)
            else:
                # Fallback to direct call if circuit breaker not available
                return self._call_openai_internal(request, prompt)

        except CircuitBreakerOpenError:
            logger.error("❌ Circuit breaker is OPEN - LLM service unavailable")
            raise
        except Exception as e:
            logger.error(f"❌ LLM call failed: {e}")
            raise

    async def _call_openai_with_timeout(self, request: LLMRequest, prompt: str):
        """Call OpenAI API with timeout enforcement"""
        
        async def make_api_call():
            return self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": self._get_system_prompt(request.query_type)},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                response_format={"type": "json_object"},
            )
        
        # Enforce 2-second timeout
        try:
            return await asyncio.wait_for(make_api_call(), timeout=2.0)
        except asyncio.TimeoutError:
            logger.warning("LLM call exceeded 2-second timeout, falling back to deterministic rules")
            raise

    def _build_prompt(self, request: LLMRequest) -> str:
        """Build structured prompt for LLM"""

        prompt = f"""
# Underwriting Decision Request

## Query Type: {request.query_type}
## Question: {request.query}

## Context Evidence:
{self._format_context(request.context)}

## Specific Evidence:
{self._format_evidence(request.evidence)}

## Instructions:
1. Analyze the provided evidence in the context of underwriting guidelines
2. Make a clear decision (ACCEPT, REFER, or DECLINE)
3. Provide detailed reasoning with specific citations
4. Identify any required questions for the applicant
5. List any referral triggers or conditions

## Response Format:
Please respond with a JSON object containing:
{{
    "decision": "ACCEPT|REFER|DECLINE",
    "confidence": 0.0-1.0,
    "reasoning": "Detailed explanation of the decision",
    "citations": ["List of specific evidence citations"],
    "required_questions": ["Questions for applicant"],
    "referral_triggers": ["Reasons for referral"],
    "conditions": ["Conditions for approval"]
}}
"""
        return prompt

    def _get_system_prompt(self, query_type: str) -> str:
        """Get system prompt based on query type"""

        base_prompt = """
You are an expert insurance underwriting AI assistant with deep knowledge of:
- Property insurance guidelines and regulations
- Risk assessment methodologies
- Underwriting best practices and compliance requirements
- Evidence-based decision making

Your role is to analyze underwriting requests and provide clear, well-reasoned decisions
based on the provided evidence and guidelines.
"""

        if query_type == "eligibility":
            return base_prompt + """
Focus on property eligibility criteria including:
- Property type and construction requirements
- Location and geographic risk factors
- Coverage limits and underwriting thresholds
- Mandatory documentation and verification
"""
        elif query_type == "endorsement":
            return base_prompt + """
Focus on endorsement analysis including:
- Endorsement eligibility and requirements
- Coverage enhancements and limitations
- Additional premium considerations
- Documentation and approval processes
"""
        elif query_type == "risk_assessment":
            return base_prompt + """
Focus on risk evaluation including:
- Property condition and age factors
- Hazard and exposure analysis
- Claims history and loss potential
- Mitigation and risk improvement options
"""
        else:
            return base_prompt

    def _format_context(self, context: List[str]) -> str:
        """Format context for prompt"""
        if not context:
            return "No additional context provided."

        formatted = []
        for i, ctx in enumerate(context, 1):
            formatted.append(f"{i}. {ctx}")

        return "\n".join(formatted)

    def _format_evidence(self, evidence: List[Dict[str, Any]]) -> str:
        """Format evidence for prompt"""
        if not evidence:
            return "No specific evidence provided."

        formatted = []
        for i, ev in enumerate(evidence, 1):
            formatted.append(f"""
Evidence {i}:
- Source: {ev.get('doc_title', 'Unknown')}
- Section: {ev.get('section', 'Unknown')}
- Content: {ev.get('text', 'No text available')}
- Relevance: {ev.get('relevance_score', 'N/A')}
- Rule Strength: {ev.get('rule_strength', 'N/A')}
""")

        return "\n".join(formatted)

    def _parse_llm_response(self, content: Dict[str, Any]) -> LLMResponse:
        """Parse LLM response into structured format"""

        return LLMResponse(
            decision=content.get("decision", "REFER"),
            confidence=float(content.get("confidence", 0.5)),
            reasoning=content.get("reasoning", "No reasoning provided"),
            citations=content.get("citations", []),
            required_questions=content.get("required_questions", []),
            referral_triggers=content.get("referral_triggers", []),
            conditions=content.get("conditions", []),
            processing_time_ms=0.0,  # Will be set by caller
        )

    def _mock_response(self, request: LLMRequest) -> LLMResponse:
        """Generate mock response when OpenAI is not available"""

        # Simple rule-based mock logic
        if "high" in request.query.lower() or "decline" in request.query.lower():
            decision = "DECLINE"
            confidence = 0.9
            reasoning = "Mock response: High risk factors identified based on query analysis"
        elif "refer" in request.query.lower() or "review" in request.query.lower():
            decision = "REFER"
            confidence = 0.7
            reasoning = "Mock response: Requires underwriter review based on evidence analysis"
        else:
            decision = "ACCEPT"
            confidence = 0.8
            reasoning = "Mock response: Meets standard underwriting criteria"

        return LLMResponse(
            decision=decision,
            confidence=confidence,
            reasoning=reasoning,
            citations=[f"Mock citation {i + 1}" for i in range(min(3, len(request.evidence)))],
            required_questions=(
                ["Please provide additional documentation"] if decision == "REFER" else []
            ),
            referral_triggers=["Mock referral trigger"] if decision in ["REFER", "DECLINE"] else [],
            conditions=["Mock condition"] if decision == "ACCEPT" else [],
            processing_time_ms=50.0,
        )

    def _deterministic_fallback(self, request: LLMRequest, start_time: datetime, llm_response: Optional[LLMResponse]) -> LLMResponse:
        """
        Apply deterministic rules when LLM confidence is below threshold or LLM is unavailable
        
        Args:
            request: Original LLM request
            start_time: Request start time
            llm_response: LLM response (if available but low confidence)
        
        Returns:
            Deterministic fallback response
        """
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # Apply deterministic rules based on evidence
        decision = self._apply_deterministic_rules(request.evidence)
        reasoning = f"Deterministic rules applied (LLM confidence {llm_response.confidence if llm_response else 'unavailable':.2f} below threshold {request.confidence_threshold:.2f})"
        
        return LLMResponse(
            decision=decision["decision"],
            confidence=0.9,  # High confidence in deterministic rules
            reasoning=reasoning,
            citations=decision["citations"],
            required_questions=decision["required_questions"],
            referral_triggers=decision["referral_triggers"],
            conditions=decision["conditions"],
            processing_time_ms=processing_time,
        )

    def _apply_deterministic_rules(self, evidence: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Apply deterministic underwriting rules when LLM is unavailable or low confidence
        
        Args:
            evidence: Available evidence chunks
        
        Returns:
            Deterministic decision with reasoning
        """
        # Default to REFER for safety
        decision = "REFER"
        citations = []
        required_questions = []
        referral_triggers = ["LLM fallback applied"]
        conditions = ["Manual review required due to LLM unavailability"]
        
        # Check for high-risk factors in evidence
        high_risk_factors = []
        for chunk in evidence:
            text = chunk.get("text", "").lower()
            
            # Look for high-risk indicators
            if "wildfire" in text and ("high" in text or "severe" in text):
                high_risk_factors.append("High wildfire risk")
                citations.append(chunk.get("chunk_id", ""))
            
            if "flood" in text and ("zone" in text and ("a" in text or "high" in text)):
                high_risk_factors.append("Flood zone")
                citations.append(chunk.get("chunk_id", ""))
            
            if "earthquake" in text and ("fault" in text or "high" in text):
                high_risk_factors.append("Earthquake risk")
                citations.append(chunk.get("chunk_id", ""))
        
        # If no high-risk factors and sufficient evidence, consider ACCEPT
        if len(high_risk_factors) == 0 and len(evidence) >= 2:
            decision = "ACCEPT"
            referral_triggers = []
            conditions = ["Approved via deterministic rules"]
            citations = [chunk.get("chunk_id", "") for chunk in evidence[:2]]
        
        # If high-risk factors found, require more information
        elif len(high_risk_factors) > 0:
            required_questions = [
                f"Please provide additional documentation for: {', '.join(high_risk_factors)}"
            ]
            referral_triggers.extend(high_risk_factors)
        
        return {
            "decision": decision,
            "citations": citations,
            "required_questions": required_questions,
            "referral_triggers": referral_triggers,
            "conditions": conditions
        }

    def _fallback_response(self, request: LLMRequest, start_time: datetime) -> LLMResponse:
        """Generate fallback response when LLM fails completely"""

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        return LLMResponse(
            decision="REFER",
            confidence=0.5,
            reasoning="LLM processing failed - requires manual underwriter review",
            citations=[],
            required_questions=["Please contact underwriting team for assistance"],
            referral_triggers=["LLM system failure"],
            conditions=["Manual review required"],
            processing_time_ms=processing_time,
        )

    def health_check(self) -> Dict[str, Any]:
        """Check LLM engine health including circuit breaker status"""
        health = {
            "status": "healthy" if self.client else "mock_mode",
            "openai_available": OPENAI_AVAILABLE,
            "api_key_configured": bool(self.api_key),
            "client_initialized": self.client is not None,
            "timestamp": datetime.now().isoformat(),
        }
        
        # Add circuit breaker status if available
        if hasattr(self, 'circuit_breaker_config'):
            from .circuit_breaker import get_all_circuit_breaker_states
            cb_states = get_all_circuit_breaker_states()
            health["circuit_breaker"] = cb_states.get("openai_llm", {"status": "not_initialized"})
        
        return health


# Global LLM engine instance
_llm_engine: Optional[LLMEngine] = None


def get_llm_engine() -> LLMEngine:
    """Get global LLM engine instance"""
    global _llm_engine
    if _llm_engine is None:
        _llm_engine = LLMEngine()
    return _llm_engine


def reset_llm_engine():
    """Reset global LLM engine (for testing)"""
    global _llm_engine
    _llm_engine = None
