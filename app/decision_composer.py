"""
Decision Composer for Evidence-First Underwriting

Generates structured underwriting decisions based on verified evidence,
with proper citation mapping and confidence scoring.
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import re

from models.schemas import RetrievalChunk, Decision, DecisionType
from app.evidence_verifier import EvidenceVerifier, EvidenceAssessment, EvidenceQuality


class DecisionCategory(Enum):
    """Categories of underwriting decisions"""
    ELIGIBILITY = "eligibility"
    REFERRAL = "referral"
    ENDORSEMENT = "endorsement"
    MISSING_INFO = "missing_info"
    DECLINE = "decline"


@dataclass
class DecisionEvidence:
    """Evidence supporting a specific decision component"""
    chunk_ids: List[str]
    excerpts: List[str]
    relevance_scores: List[float]
    rule_strengths: List[str]
    confidence: float


@dataclass
class StructuredDecision:
    """Structured underwriting decision with evidence mapping"""
    decision_type: DecisionType
    primary_reason: str
    confidence_score: float
    evidence_map: Dict[str, DecisionEvidence]
    required_questions: List[Dict[str, Any]]
    referral_triggers: List[str]
    conditions: List[str]
    endorsements: List[Dict[str, Any]]
    citations: List[Dict[str, Any]]


class DecisionComposer:
    """
    Composes evidence-based underwriting decisions
    
    Features:
    - Evidence-to-decision mapping
    - Confidence-based decision logic
    - Citation tracking
    - Question generation from evidence gaps
    """
    
    def __init__(self):
        self.evidence_verifier = EvidenceVerifier()
        
        # Decision rules based on evidence quality
        self.decision_thresholds = {
            EvidenceQuality.STRONG: {
                "auto_accept": 0.8,
                "auto_refer": 0.6,
                "auto_decline": 0.9
            },
            EvidenceQuality.MODERATE: {
                "auto_accept": 0.9,  # Higher threshold for moderate evidence
                "auto_refer": 0.7,
                "auto_decline": 0.95
            },
            EvidenceQuality.WEAK: {
                "auto_accept": 1.0,  # No auto-accept for weak evidence
                "auto_refer": 0.8,
                "auto_decline": 1.0
            },
            EvidenceQuality.INSUFFICIENT: {
                "auto_accept": 1.0,  # Always refer for insufficient evidence
                "auto_refer": 0.5,
                "auto_decline": 1.0
            }
        }
        
        # Decision patterns
        self.decision_patterns = {
            DecisionType.DECLINE: [
                r'\bMUST\s+BE\s+DECLINED\b',
                r'\bDECLINE\b.*(?:unless|except)',
                r'\bNOT\s+ACCEPTABLE\b',
                r'\bAUTOMATIC\s+DECLINE\b'
            ],
            DecisionType.REFER: [
                r'\bSHALL\s+BE\s+REFERRED\b',
                r'\bREFER\b.*(?:for|if|when)',
                r'\bREQUIRES\s+UW\s+(?:APPROVAL|REVIEW)\b',
                r'\bSUBJECT\s+TO\s+UW\s+APPROVAL\b'
            ],
            DecisionType.ACCEPT: [
                r'\bACCEPTABLE\b',
                r'\bMAY\s+BE\s+ACCEPTED\b',
                r'\bELIGIBLE\b',
                r'\bSTANDARD\s+RISK\b'
            ]
        }
    
    def compose_decision(self, chunks: List[RetrievalChunk], query_type: str,
                         submission_data: Optional[Dict[str, Any]] = None) -> StructuredDecision:
        """
        Compose evidence-based underwriting decision
        
        Args:
            chunks: Retrieved evidence chunks
            query_type: Type of underwriting query
            submission_data: Optional submission data for context
            
        Returns:
            Structured decision with evidence mapping
        """
        # Verify evidence quality
        evidence_assessment = self.evidence_verifier.verify_evidence(chunks, query_type)
        
        # Analyze decision patterns in evidence
        decision_analysis = self._analyze_decision_patterns(chunks)
        
        # Determine decision type and confidence
        decision_type, confidence = self._determine_decision_type(
            evidence_assessment, decision_analysis, query_type
        )
        
        # Generate decision components
        primary_reason = self._generate_primary_reason(decision_type, chunks, decision_analysis)
        evidence_map = self._create_evidence_map(chunks, decision_type)
        required_questions = self._generate_required_questions(chunks, evidence_assessment)
        referral_triggers = self._extract_referral_triggers(chunks)
        conditions = self._extract_conditions(chunks)
        endorsements = self._extract_endorsements(chunks)
        citations = self._create_citations(chunks)
        
        return StructuredDecision(
            decision_type=decision_type,
            primary_reason=primary_reason,
            confidence_score=confidence,
            evidence_map=evidence_map,
            required_questions=required_questions,
            referral_triggers=referral_triggers,
            conditions=conditions,
            endorsements=endorsements,
            citations=citations
        )
    
    def _analyze_decision_patterns(self, chunks: List[RetrievalChunk]) -> Dict[str, Any]:
        """Analyze decision patterns in evidence chunks"""
        pattern_counts = {decision_type.value: 0 for decision_type in DecisionType}
        pattern_evidence = {decision_type.value: [] for decision_type in DecisionType}
        
        for chunk in chunks:
            text = chunk.text.upper()
            
            for decision_type, patterns in self.decision_patterns.items():
                for pattern in patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    if matches:
                        pattern_counts[decision_type.value] += len(matches)
                        pattern_evidence[decision_type.value].append({
                            "chunk_id": chunk.chunk_id,
                            "matches": matches,
                            "relevance": chunk.relevance_score or 0.0
                        })
        
        return {
            "pattern_counts": pattern_counts,
            "pattern_evidence": pattern_evidence,
            "dominant_pattern": max(pattern_counts, key=pattern_counts.get)
        }
    
    def _determine_decision_type(self, evidence_assessment: EvidenceAssessment,
                                decision_analysis: Dict[str, Any], query_type: str) -> Tuple[DecisionType, float]:
        """Determine decision type based on evidence analysis"""
        quality = evidence_assessment.quality
        confidence = evidence_assessment.confidence_score
        dominant_pattern = decision_analysis["dominant_pattern"]
        
        # Get thresholds for this evidence quality
        thresholds = self.decision_thresholds[quality]
        
        # Check for mandatory decline patterns
        if decision_analysis["pattern_counts"][DecisionType.DECLINE.value] > 0:
            if confidence >= thresholds["auto_decline"]:
                return DecisionType.DECLINE, confidence
            else:
                return DecisionType.REFER, confidence * 0.8  # Reduce confidence for borderline cases
        
        # Check for mandatory referral patterns
        if decision_analysis["pattern_counts"][DecisionType.REFER.value] > 0:
            if confidence >= thresholds["auto_refer"]:
                return DecisionType.REFER, confidence
            else:
                return DecisionType.ACCEPT, confidence * 0.7  # Lower confidence for weak referral evidence
        
        # Check for accept patterns
        if decision_analysis["pattern_counts"][DecisionType.ACCEPT.value] > 0:
            if confidence >= thresholds["auto_accept"]:
                return DecisionType.ACCEPT, confidence
            else:
                return DecisionType.REFER, confidence * 0.6  # Refer if confidence too low
        
        # Default based on evidence quality
        if quality == EvidenceQuality.STRONG and confidence >= 0.8:
            return DecisionType.ACCEPT, confidence
        elif quality in [EvidenceQuality.MODERATE, EvidenceQuality.WEAK]:
            return DecisionType.REFER, confidence
        else:
            return DecisionType.REFER, confidence * 0.5  # Low confidence for insufficient evidence
    
    def _generate_primary_reason(self, decision_type: DecisionType, chunks: List[RetrievalChunk],
                                decision_analysis: Dict[str, Any]) -> str:
        """Generate primary reason for decision"""
        pattern_evidence = decision_analysis["pattern_evidence"][decision_type.value]
        
        if pattern_evidence:
            # Use the most relevant evidence
            best_evidence = max(pattern_evidence, key=lambda x: x["relevance"])
            
            # Find the chunk with this evidence
            chunk = next((c for c in chunks if c.chunk_id == best_evidence["chunk_id"]), None)
            if chunk:
                # Extract relevant sentence
                sentences = chunk.text.split('.')
                for sentence in sentences:
                    if any(pattern.lower() in sentence.lower() for pattern in best_evidence["matches"]):
                        return sentence.strip()
        
        # Fallback reasons
        fallback_reasons = {
            DecisionType.ACCEPT: "Meets standard underwriting guidelines",
            DecisionType.REFER: "Requires underwriter review due to risk factors",
            DecisionType.DECLINE: "Does not meet eligibility requirements"
        }
        
        return fallback_reasons.get(decision_type, "Underwriting decision based on evidence review")
    
    def _create_evidence_map(self, chunks: List[RetrievalChunk], decision_type: DecisionType) -> Dict[str, DecisionEvidence]:
        """Create evidence mapping for decision components"""
        evidence_map = {}
        
        # Map evidence to decision components
        for chunk in chunks:
            component = self._classify_evidence_component(chunk, decision_type)
            
            if component not in evidence_map:
                evidence_map[component] = DecisionEvidence(
                    chunk_ids=[],
                    excerpts=[],
                    relevance_scores=[],
                    rule_strengths=[],
                    confidence=0.0
                )
            
            evidence_map[component].chunk_ids.append(chunk.chunk_id)
            evidence_map[component].excerpts.append(chunk.text[:200] + "...")
            evidence_map[component].relevance_scores.append(chunk.relevance_score or 0.0)
            evidence_map[component].rule_strengths.append(chunk.metadata.get("rule_strength", "informational"))
        
        # Calculate confidence for each component
        for component, evidence in evidence_map.items():
            if evidence.relevance_scores:
                evidence.confidence = sum(evidence.relevance_scores) / len(evidence.relevance_scores)
        
        return evidence_map
    
    def _classify_evidence_component(self, chunk: RetrievalChunk, decision_type: DecisionType) -> str:
        """Classify evidence to decision component"""
        text = chunk.text.lower()
        section = chunk.section.lower()
        
        # Component classification
        if any(keyword in text for keyword in ["eligible", "eligibility", "acceptable"]):
            return "eligibility"
        elif any(keyword in text for keyword in ["refer", "referral", "review", "approval"]):
            return "referral_trigger"
        elif any(keyword in text for keyword in ["endorsement", "coverage", "additional"]):
            return "endorsement"
        elif any(keyword in text for keyword in ["require", "need", "missing", "information"]):
            return "required_info"
        elif any(keyword in text for keyword in ["decline", "ineligible", "not acceptable"]):
            return "decline_reason"
        elif any(keyword in text for keyword in ["condition", "provided that", "if", "when"]):
            return "condition"
        else:
            return "general_evidence"
    
    def _generate_required_questions(self, chunks: List[RetrievalChunk], 
                                    evidence_assessment: EvidenceAssessment) -> List[Dict[str, Any]]:
        """Generate required questions based on evidence gaps"""
        questions = []
        
        # Questions from evidence verifier recommendations
        for recommendation in evidence_assessment.recommendations:
            if "require" in recommendation.lower() or "need" in recommendation.lower():
                questions.append({
                    "question": recommendation,
                    "priority": "P1",  # High priority
                    "source": "evidence_verifier",
                    "evidence_gap": True
                })
        
        # Questions from chunk analysis
        for chunk in chunks:
            text = chunk.text.lower()
            
            # Look for question patterns
            question_patterns = [
                r"(.+?)\s+must\s+be\s+provided",
                r"(.+?)\s+shall\s+be\s+requested",
                r"require(?:s|d)?\s+(.+?)\s+for",
                r"information\s+(.+?)\s+(?:is|are)\s+required"
            ]
            
            for pattern in question_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    questions.append({
                        "question": f"Please provide {match.strip()}",
                        "priority": "P1" if "must" in text else "P2",
                        "source": chunk.chunk_id,
                        "evidence_gap": False
                    })
        
        return questions
    
    def _extract_referral_triggers(self, chunks: List[RetrievalChunk]) -> List[str]:
        """Extract referral triggers from evidence"""
        triggers = []
        
        for chunk in chunks:
            text = chunk.text
            
            # Look for referral trigger patterns
            trigger_patterns = [
                r"refer(?:s|red)?\s+(?:for|if|when|due to)\s+([^.\n]+)",
                r"requires?\s+(?:uw\s+)?(?:approval|review)\s+(?:for|if|when)\s+([^.\n]+)",
                r"subject\s+to\s+(?:uw\s+)?(?:approval|review)\s+(?:for|if|when)\s+([^.\n]+)"
            ]
            
            for pattern in trigger_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    triggers.append(match.strip())
        
        return list(set(triggers))  # Remove duplicates
    
    def _extract_conditions(self, chunks: List[RetrievalChunk]) -> List[str]:
        """Extract conditions from evidence"""
        conditions = []
        
        for chunk in chunks:
            text = chunk.text
            
            # Look for condition patterns
            condition_patterns = [
                r"if\s+([^,\n]+)",
                r"when\s+([^,\n]+)",
                r"provided\s+(?:that\s+)?([^,\n]+)",
                r"subject\s+to\s+([^,\n]+)",
                r"unless\s+([^,\n]+)"
            ]
            
            for pattern in condition_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    condition = match.strip()
                    if len(condition) > 5 and len(condition) < 200:  # Reasonable length
                        conditions.append(condition)
        
        return list(set(conditions))  # Remove duplicates
    
    def _extract_endorsements(self, chunks: List[RetrievalChunk]) -> List[Dict[str, Any]]:
        """Extract endorsement requirements from evidence"""
        endorsements = []
        
        for chunk in chunks:
            text = chunk.text.lower()
            
            # Look for endorsement patterns
            endorsement_patterns = [
                r"([a-z0-9\-]+)\s+endorsement",
                r"endorsement\s+([a-z0-9\-]+)",
                r"coverage\s+add\s+(.+?)\s+(?:is|shall|must)",
                r"(.+?)\s+(?:is|shall|must)\s+be\s+(?:recommended|required|attached)"
            ]
            
            for pattern in endorsement_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    endorsements.append({
                        "endorsement_code": match if match.isalnum() else "UNKNOWN",
                        "description": match,
                        "requirement": "required" if "must" in text or "shall" in text else "recommended",
                        "source_chunk": chunk.chunk_id
                    })
        
        return endorsements
    
    def _create_citations(self, chunks: List[RetrievalChunk]) -> List[Dict[str, Any]]:
        """Create proper citations for all evidence"""
        citations = []
        
        for i, chunk in enumerate(chunks):
            citation = {
                "citation_id": f"G{i+1}",
                "doc_id": chunk.doc_id,
                "doc_title": chunk.metadata.get("doc_title", "Unknown Document"),
                "section": chunk.section,
                "subsection": chunk.metadata.get("subsection", ""),
                "chunk_id": chunk.chunk_id,
                "text_excerpt": chunk.text[:200] + "..." if len(chunk.text) > 200 else chunk.text,
                "relevance_score": chunk.relevance_score or 0.0,
                "rule_strength": chunk.metadata.get("rule_strength", "informational"),
                "effective_date": chunk.metadata.get("effective_date", "2026-01-01"),
                "version": chunk.metadata.get("version", "v0.1")
            }
            citations.append(citation)
        
        return citations
    
    def create_decision_object(self, structured_decision: StructuredDecision) -> Decision:
        """Convert structured decision to Decision object"""
        return Decision(
            decision=structured_decision.decision_type,
            reason=structured_decision.primary_reason,
            confidence=structured_decision.confidence_score,
            required_questions=structured_decision.required_questions,
            referral_triggers=structured_decision.referral_triggers,
            conditions=structured_decision.conditions
        )


# Global instance
_composer_instance = None

def get_decision_composer() -> DecisionComposer:
    """Get or create global decision composer instance"""
    global _composer_instance
    if _composer_instance is None:
        _composer_instance = DecisionComposer()
    return _composer_instance
