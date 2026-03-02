"""
Evidence Verifier for Underwriting Decisions

Implements evidence quality assessment, rule language detection,
and confidence scoring for evidence-first underwriting.
"""

import re
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

from models.schemas import RetrievalChunk


class EvidenceQuality(Enum):
    """Evidence quality levels"""
    STRONG = "strong_evidence"
    MODERATE = "moderate_evidence" 
    WEAK = "weak_evidence"
    INSUFFICIENT = "insufficient_evidence"


class RuleStrength(Enum):
    """Rule strength levels"""
    MANDATORY = "mandatory"      # MUST, MUST NOT
    REQUIRED = "required"       # SHALL, SHALL NOT  
    RECOMMENDED = "recommended"  # SHOULD, SHOULD NOT
    PERMISSIVE = "permissive"   # MAY, MAY NOT
    INFORMATIONAL = "informational"


@dataclass
class EvidenceAssessment:
    """Evidence quality assessment results"""
    quality: EvidenceQuality
    confidence_score: float
    rule_strength: RuleStrength
    has_thresholds: bool
    has_conditions: bool
    cross_reference_count: int
    recommendations: List[str]
    verification_details: Dict[str, Any]


class EvidenceVerifier:
    """
    Verifies evidence quality for underwriting decisions
    
    Features:
    - Rule language detection (MUST/SHALL/SHOULD/MAY)
    - Threshold identification (age limits, coverage amounts)
    - Cross-reference validation
    - Confidence scoring
    """
    
    def __init__(self):
        # Rule language patterns
        self.rule_patterns = {
            RuleStrength.MANDATORY: [
                r'\bMUST\b', r'\bMUST NOT\b', r'\bREQUIRED\b', r'\bMANDATORY\b'
            ],
            RuleStrength.REQUIRED: [
                r'\bSHALL\b', r'\bSHALL NOT\b', r'\bOBLIGATED\b'
            ],
            RuleStrength.RECOMMENDED: [
                r'\bSHOULD\b', r'\bSHOULD NOT\b', r'\bRECOMMENDED\b', r'\bADVISED\b'
            ],
            RuleStrength.PERMISSIVE: [
                r'\bMAY\b', r'\bMAY NOT\b', r'\bPERMITTED\b', r'\bALLOWED\b'
            ]
        }
        
        # Threshold patterns
        self.threshold_patterns = [
            r'\b(>\s*\d+|\d+\s*<|\d+\s*-\s*\d+)\s*(years?|months?|\$|percent|%)',
            r'\b(over|under|above|below)\s*\d+\s*(years?|months?|\$)',
            r'\b(between\s*\d+\s*and\s*\d+|\d+\s*to\s*\d+)\s*(years?|months?|\$)',
            r'\b(maximum|minimum)\s*(of\s*)?\d+\s*(years?|months?|\$)'
        ]
        
        # Cross-reference patterns
        self.cross_ref_patterns = [
            r'(?:see|refer to|reference)\s+§?\s*[\d\.]+',
            r'(?:according to|per|as per)\s+[\w\s]+§?\s*[\d\.]+',
            r'\b(?:section|sec\.|paragraph|para\.)\s*[\d\.]+',
            r'\([\d\.\s]*\)'  # Citation numbers
        ]
    
    def verify_evidence(self, chunks: List[RetrievalChunk], query_type: str) -> EvidenceAssessment:
        """
        Verify evidence quality for a set of chunks
        
        Args:
            chunks: Retrieved evidence chunks
            query_type: Type of underwriting query
            
        Returns:
            Evidence assessment with quality metrics
        """
        if not chunks:
            return EvidenceAssessment(
                quality=EvidenceQuality.INSUFFICIENT,
                confidence_score=0.0,
                rule_strength=RuleStrength.INFORMATIONAL,
                has_thresholds=False,
                has_conditions=False,
                cross_reference_count=0,
                recommendations=["No evidence found - requires manual review"],
                verification_details={"reason": "no_chunks"}
            )
        
        # Analyze each chunk
        chunk_analyses = []
        for chunk in chunks:
            analysis = self._analyze_chunk(chunk)
            chunk_analyses.append(analysis)
        
        # Aggregate analysis
        assessment = self._aggregate_analysis(chunk_analyses, query_type)
        
        return assessment
    
    def _analyze_chunk(self, chunk: RetrievalChunk) -> Dict[str, Any]:
        """Analyze individual chunk for evidence quality"""
        text = chunk.text.upper()
        
        # Detect rule strength
        rule_strength = self._detect_rule_strength(text)
        
        # Check for thresholds
        has_thresholds = self._has_thresholds(text)
        
        # Check for conditions
        has_conditions = self._has_conditions(text)
        
        # Count cross-references
        cross_refs = self._count_cross_references(chunk.text)
        
        # Calculate chunk quality score
        quality_score = self._calculate_chunk_score(
            rule_strength, has_thresholds, has_conditions, cross_refs,
            chunk.relevance_score or 0.0
        )
        
        return {
            "chunk_id": chunk.chunk_id,
            "rule_strength": rule_strength,
            "has_thresholds": has_thresholds,
            "has_conditions": has_conditions,
            "cross_reference_count": cross_refs,
            "quality_score": quality_score,
            "relevance_score": chunk.relevance_score or 0.0
        }
    
    def _detect_rule_strength(self, text: str) -> RuleStrength:
        """Detect rule strength from text"""
        for strength, patterns in self.rule_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return strength
        return RuleStrength.INFORMATIONAL
    
    def _has_thresholds(self, text: str) -> bool:
        """Check if text contains numeric thresholds"""
        for pattern in self.threshold_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _has_conditions(self, text: str) -> bool:
        """Check if text contains conditional logic"""
        condition_patterns = [
            r'\b(if|when|where|provided that|subject to)\b',
            r'\b(unless|except|excluding)\b',
            r'\b(and|or|but)\s+(?:if|when|where)\b',
            r'\b(?:requires|needs|depends on)\s+\w+'
        ]
        
        for pattern in condition_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _count_cross_references(self, text: str) -> int:
        """Count cross-references to other sections"""
        count = 0
        for pattern in self.cross_ref_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            count += len(matches)
        return count
    
    def _calculate_chunk_score(self, rule_strength: RuleStrength, has_thresholds: bool,
                              has_conditions: bool, cross_refs: int, relevance_score: float) -> float:
        """Calculate quality score for individual chunk"""
        # Base scores for different factors
        strength_scores = {
            RuleStrength.MANDATORY: 1.0,
            RuleStrength.REQUIRED: 0.9,
            RuleStrength.RECOMMENDED: 0.7,
            RuleStrength.PERMISSIVE: 0.5,
            RuleStrength.INFORMATIONAL: 0.3
        }
        
        score = strength_scores[rule_strength] * 0.4  # 40% weight for rule strength
        score += (1.0 if has_thresholds else 0.0) * 0.2  # 20% weight for thresholds
        score += (1.0 if has_conditions else 0.0) * 0.1  # 10% weight for conditions
        score += min(cross_refs / 3.0, 1.0) * 0.1  # 10% weight for cross-refs
        score += relevance_score * 0.2  # 20% weight for relevance
        
        return min(score, 1.0)
    
    def _aggregate_analysis(self, chunk_analyses: List[Dict[str, Any]], query_type: str) -> EvidenceAssessment:
        """Aggregate chunk analyses into overall assessment"""
        # Calculate average scores
        avg_quality = sum(a["quality_score"] for a in chunk_analyses) / len(chunk_analyses)
        avg_relevance = sum(a["relevance_score"] for a in chunk_analyses) / len(chunk_analyses)
        
        # Determine overall rule strength (use strongest)
        strength_values = {
            RuleStrength.MANDATORY: 5,
            RuleStrength.REQUIRED: 4,
            RuleStrength.RECOMMENDED: 3,
            RuleStrength.PERMISSIVE: 2,
            RuleStrength.INFORMATIONAL: 1
        }
        
        strongest_strength = max(
            chunk_analyses, 
            key=lambda x: strength_values[x["rule_strength"]]
        )["rule_strength"]
        
        # Check if any chunks have thresholds/conditions
        has_thresholds = any(a["has_thresholds"] for a in chunk_analyses)
        has_conditions = any(a["has_conditions"] for a in chunk_analyses)
        total_cross_refs = sum(a["cross_reference_count"] for a in chunk_analyses)
        
        # Calculate overall confidence
        confidence_score = (avg_quality * 0.7) + (avg_relevance * 0.3)
        
        # Determine evidence quality
        if confidence_score >= 0.8 and strongest_strength in [RuleStrength.MANDATORY, RuleStrength.REQUIRED]:
            quality = EvidenceQuality.STRONG
        elif confidence_score >= 0.6 and strongest_strength in [RuleStrength.REQUIRED, RuleStrength.RECOMMENDED]:
            quality = EvidenceQuality.MODERATE
        elif confidence_score >= 0.4:
            quality = EvidenceQuality.WEAK
        else:
            quality = EvidenceQuality.INSUFFICIENT
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            quality, confidence_score, strongest_strength, has_thresholds, total_cross_refs
        )
        
        # Verification details
        verification_details = {
            "chunk_count": len(chunk_analyses),
            "avg_chunk_quality": avg_quality,
            "avg_relevance": avg_relevance,
            "strongest_rule_strength": strongest_strength.value,
            "chunks_with_thresholds": sum(1 for a in chunk_analyses if a["has_thresholds"]),
            "chunks_with_conditions": sum(1 for a in chunk_analyses if a["has_conditions"]),
            "total_cross_references": total_cross_refs
        }
        
        return EvidenceAssessment(
            quality=quality,
            confidence_score=confidence_score,
            rule_strength=strongest_strength,
            has_thresholds=has_thresholds,
            has_conditions=has_conditions,
            cross_reference_count=total_cross_refs,
            recommendations=recommendations,
            verification_details=verification_details
        )
    
    def _generate_recommendations(self, quality: EvidenceQuality, confidence: float,
                                strength: RuleStrength, has_thresholds: bool, cross_refs: int) -> List[str]:
        """Generate recommendations based on evidence assessment"""
        recommendations = []
        
        if quality == EvidenceQuality.INSUFFICIENT:
            recommendations.append("Insufficient evidence - requires manual underwriter review")
            recommendations.append("Consider expanding search query for broader results")
        elif quality == EvidenceQuality.WEAK:
            recommendations.append("Weak evidence - recommend additional verification")
            if strength == RuleStrength.INFORMATIONAL:
                recommendations.append("Look for stronger rule language (MUST/SHALL)")
        elif quality == EvidenceQuality.MODERATE:
            recommendations.append("Moderate evidence - acceptable for standard decisions")
            if not has_thresholds:
                recommendations.append("Consider if specific thresholds should be applied")
        else:  # STRONG
            recommendations.append("Strong evidence - suitable for automated decisions")
        
        if confidence < 0.7:
            recommendations.append("Low confidence score - consider human review")
        
        if cross_refs == 0:
            recommendations.append("No cross-references found - verify against other guidelines")
        
        return recommendations
    
    def extract_thresholds(self, chunks: List[RetrievalChunk]) -> List[Dict[str, Any]]:
        """Extract specific thresholds from evidence chunks"""
        thresholds = []
        
        for chunk in chunks:
            text = chunk.text
            
            # Find all threshold matches
            for pattern in self.threshold_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    threshold_text = match.group()
                    
                    # Parse the threshold value
                    value = self._parse_threshold_value(threshold_text)
                    if value:
                        thresholds.append({
                            "chunk_id": chunk.chunk_id,
                            "text": threshold_text,
                            "value": value,
                            "context": text[max(0, match.start()-50):match.end()+50]
                        })
        
        return thresholds
    
    def _parse_threshold_value(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse numeric value from threshold text"""
        # Extract numbers and units
        number_pattern = r'(\d+(?:,\d+)*)'
        unit_pattern = r'(years?|months?|\$|percent|%)'
        
        numbers = re.findall(number_pattern, text)
        units = re.findall(unit_pattern, text, re.IGNORECASE)
        
        if numbers:
            return {
                "raw_text": text,
                "numbers": [int(n.replace(',', '')) for n in numbers],
                "unit": units[0] if units else "unknown"
            }
        
        return None


# Global instance
_verifier_instance = None

def get_evidence_verifier() -> EvidenceVerifier:
    """Get or create global evidence verifier instance"""
    global _verifier_instance
    if _verifier_instance is None:
        _verifier_instance = EvidenceVerifier()
    return _verifier_instance
