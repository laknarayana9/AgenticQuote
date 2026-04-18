"""
Multi-Modal Reasoning System
Implements sophisticated reasoning across different data modalities:

- Text reasoning (natural language processing)
- Structured data reasoning (numerical analysis)
- Rule-based reasoning (logic and constraints)
- Cross-modal synthesis (integrating different reasoning types)
- Context-aware reasoning selection
- Uncertainty management across modalities
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import json
import re
import statistics
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class ModalityType(Enum):
    """Types of reasoning modalities"""
    TEXT = "text"
    STRUCTURED = "structured"
    RULES = "rules"
    VISUAL = "visual"
    TEMPORAL = "temporal"
    SPATIAL = "spatial"


class ReasoningStrategy(Enum):
    """Strategies for multi-modal reasoning"""
    WEIGHTED_FUSION = "weighted_fusion"
    HIERARCHICAL = "hierarchical"
    CONSENSUS_BASED = "consensus_based"
    UNCERTAINTY_AWARE = "uncertainty_aware"
    ADAPTIVE_SELECTION = "adaptive_selection"


class ConfidenceLevel(Enum):
    """Confidence levels for reasoning"""
    VERY_LOW = 0.1
    LOW = 0.3
    MEDIUM = 0.5
    HIGH = 0.7
    VERY_HIGH = 0.9


@dataclass
class ReasoningResult:
    """Result from reasoning modality"""
    modality: ModalityType
    conclusion: str
    confidence: float
    evidence: List[str]
    reasoning_steps: List[str]
    uncertainty_factors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "modality": self.modality.value,
            "conclusion": self.conclusion,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "reasoning_steps": self.reasoning_steps,
            "uncertainty_factors": self.uncertainty_factors,
            "metadata": self.metadata
        }


@dataclass
class MultiModalContext:
    """Context for multi-modal reasoning"""
    query: str
    text_data: Optional[str] = None
    structured_data: Optional[Dict[str, Any]] = None
    rule_set: Optional[Dict[str, Any]] = None
    domain_constraints: Dict[str, Any] = field(default_factory=dict)
    reasoning_history: List[ReasoningResult] = field(default_factory=list)
    uncertainty_threshold: float = 0.3


class ReasoningModality(ABC):
    """Abstract base class for reasoning modalities"""
    
    @abstractmethod
    def reason(self, context: MultiModalContext) -> ReasoningResult:
        """Perform reasoning for this modality"""
        pass
    
    @abstractmethod
    def get_confidence(self, result: ReasoningResult) -> float:
        """Get confidence in reasoning result"""
        pass
    
    @abstractmethod
    def get_uncertainty_factors(self, result: ReasoningResult) -> List[str]:
        """Identify uncertainty factors"""
        pass


class TextReasoningModality(ReasoningModality):
    """Text-based reasoning using NLP techniques"""
    
    def __init__(self):
        self.keyword_patterns = {
            "risk": ["risk", "danger", "hazard", "threat", "exposure"],
            "eligibility": ["eligible", "qualified", "suitable", "appropriate"],
            "compliance": ["compliant", "regulation", "requirement", "mandate"],
            "recommendation": ["recommend", "suggest", "advise", "propose"]
        }
        
        self.sentiment_indicators = {
            "positive": ["accept", "approve", "eligible", "qualified", "suitable"],
            "negative": ["decline", "reject", "ineligible", "unsuitable", "risk"],
            "neutral": ["review", "assess", "evaluate", "consider", "refer"]
        }
    
    def reason(self, context: MultiModalContext) -> ReasoningResult:
        """Perform text-based reasoning"""
        
        if not context.text_data:
            return ReasoningResult(
                modality=ModalityType.TEXT,
                conclusion="No text data available for reasoning",
                confidence=0.0,
                evidence=[],
                reasoning_steps=["No text input provided"]
            )
        
        reasoning_steps = []
        evidence = []
        
        # Step 1: Extract key concepts
        key_concepts = self._extract_key_concepts(context.text_data)
        reasoning_steps.append(f"Extracted key concepts: {', '.join(key_concepts)}")
        evidence.extend(key_concepts)
        
        # Step 2: Analyze sentiment and intent
        sentiment, intent = self._analyze_sentiment_and_intent(context.text_data)
        reasoning_steps.append(f"Detected sentiment: {sentiment}, intent: {intent}")
        evidence.append(f"Sentiment analysis: {sentiment}")
        
        # Step 3: Identify domain-specific patterns
        domain_patterns = self._identify_domain_patterns(context.text_data)
        reasoning_steps.append(f"Domain patterns identified: {', '.join(domain_patterns)}")
        evidence.extend(domain_patterns)
        
        # Step 4: Generate conclusion
        conclusion = self._generate_text_conclusion(sentiment, intent, key_concepts, domain_patterns)
        reasoning_steps.append(f"Text-based conclusion: {conclusion}")
        
        # Calculate confidence
        confidence = self._calculate_text_confidence(key_concepts, sentiment, domain_patterns)
        
        # Identify uncertainty factors
        uncertainty_factors = self._get_text_uncertainty_factors(context.text_data, key_concepts)
        
        return ReasoningResult(
            modality=ModalityType.TEXT,
            conclusion=conclusion,
            confidence=confidence,
            evidence=evidence,
            reasoning_steps=reasoning_steps,
            uncertainty_factors=uncertainty_factors,
            metadata={
                "key_concepts": key_concepts,
                "sentiment": sentiment,
                "intent": intent,
                "domain_patterns": domain_patterns
            }
        )
    
    def get_confidence(self, result: ReasoningResult) -> float:
        """Get confidence in text reasoning result"""
        return result.confidence
    
    def get_uncertainty_factors(self, result: ReasoningResult) -> List[str]:
        """Get uncertainty factors for text reasoning"""
        return result.uncertainty_factors
    
    def _extract_key_concepts(self, text: str) -> List[str]:
        """Extract key concepts from text"""
        
        concepts = []
        text_lower = text.lower()
        
        # Extract based on keyword patterns
        for category, keywords in self.keyword_patterns.items():
            for keyword in keywords:
                if keyword in text_lower:
                    concepts.append(f"{category}:{keyword}")
        
        # Extract numbers and measurements
        numbers = re.findall(r'\$?\d{1,3}(?:,\d{3})*(?:\.\d+)?', text)
        for number in numbers:
            concepts.append(f"numerical:{number}")
        
        # Extract years
        years = re.findall(r'\b(19|20)\d{2}\b', text)
        for year in years:
            concepts.append(f"year:{year}")
        
        return list(set(concepts))  # Remove duplicates
    
    def _analyze_sentiment_and_intent(self, text: str) -> Tuple[str, str]:
        """Analyze sentiment and intent from text"""
        
        text_lower = text.lower()
        
        # Sentiment analysis
        sentiment_scores = {"positive": 0, "negative": 0, "neutral": 0}
        for sentiment, indicators in self.sentiment_indicators.items():
            for indicator in indicators:
                if indicator in text_lower:
                    sentiment_scores[sentiment] += 1
        
        dominant_sentiment = max(sentiment_scores, key=sentiment_scores.get)
        
        # Intent analysis
        if any(word in text_lower for word in ["underwrite", "assess", "evaluate"]):
            intent = "assessment"
        elif any(word in text_lower for word in ["approve", "accept", "recommend"]):
            intent = "approval"
        elif any(word in text_lower for word in ["decline", "reject", "deny"]):
            intent = "rejection"
        elif any(word in text_lower for word in ["review", "refer", "investigate"]):
            intent = "review"
        else:
            intent = "general"
        
        return dominant_sentiment, intent
    
    def _identify_domain_patterns(self, text: str) -> List[str]:
        """Identify domain-specific patterns"""
        
        patterns = []
        text_lower = text.lower()
        
        # Insurance domain patterns
        if "coverage" in text_lower and "limit" in text_lower:
            patterns.append("coverage_limit_discussion")
        
        if "deductible" in text_lower:
            patterns.append("deductible_mentioned")
        
        if "premium" in text_lower:
            patterns.append("premium_discussion")
        
        if "risk" in text_lower and any(word in text_lower for word in ["high", "low", "moderate"]):
            patterns.append("risk_assessment")
        
        if "property" in text_lower and any(word in text_lower for word in ["age", "condition", "type"]):
            patterns.append("property_analysis")
        
        if "california" in text_lower or "ca" in text_lower:
            patterns.append("california_context")
        
        if "wildfire" in text_lower:
            patterns.append("wildfire_risk")
        
        return patterns
    
    def _generate_text_conclusion(self, sentiment: str, intent: str, concepts: List[str], patterns: List[str]) -> str:
        """Generate conclusion from text analysis"""
        
        conclusion_parts = []
        
        # Base conclusion on sentiment
        if sentiment == "positive":
            conclusion_parts.append("Text analysis indicates positive factors")
        elif sentiment == "negative":
            conclusion_parts.append("Text analysis indicates concerning factors")
        else:
            conclusion_parts.append("Text analysis indicates neutral/mixed factors")
        
        # Add intent context
        if intent == "assessment":
            conclusion_parts.append("requiring detailed evaluation")
        elif intent == "approval":
            conclusion_parts.append("supporting approval consideration")
        elif intent == "rejection":
            conclusion_parts.append("indicating potential rejection")
        else:
            conclusion_parts.append("requiring further clarification")
        
        # Add pattern insights
        if patterns:
            if "risk_assessment" in patterns:
                conclusion_parts.append("with notable risk factors")
            if "california_context" in patterns and "wildfire_risk" in patterns:
                conclusion_parts.append("and California wildfire considerations")
        
        return " ".join(conclusion_parts)
    
    def _calculate_text_confidence(self, concepts: List[str], sentiment: str, patterns: List[str]) -> float:
        """Calculate confidence in text reasoning"""
        
        base_confidence = 0.5
        
        # Adjust based on concept richness
        concept_factor = min(1.0, len(concepts) / 5.0)
        
        # Adjust based on sentiment clarity
        sentiment_factor = 0.8 if sentiment != "neutral" else 0.5
        
        # Adjust based on pattern specificity
        pattern_factor = min(1.0, len(patterns) / 3.0)
        
        confidence = base_confidence * concept_factor * sentiment_factor * pattern_factor
        
        return max(0.1, min(0.95, confidence))
    
    def _get_text_uncertainty_factors(self, text: str, concepts: List[str]) -> List[str]:
        """Identify uncertainty factors in text reasoning"""
        
        uncertainty_factors = []
        
        # Check for ambiguous language
        ambiguous_words = ["maybe", "perhaps", "possibly", "might", "could", "unclear", "uncertain"]
        text_lower = text.lower()
        
        for word in ambiguous_words:
            if word in text_lower:
                uncertainty_factors.append(f"Ambiguous language detected: '{word}'")
        
        # Check for contradictions
        if "accept" in text_lower and "decline" in text_lower:
            uncertainty_factors.append("Contradictory terms detected")
        
        # Check for lack of specific data
        if not any(concept.startswith("numerical:") for concept in concepts):
            uncertainty_factors.append("No specific numerical data found")
        
        # Check for vague descriptions
        vague_descriptors = ["some", "several", "many", "few", "various"]
        for descriptor in vague_descriptors:
            if descriptor in text_lower:
                uncertainty_factors.append(f"Vague descriptor used: '{descriptor}'")
        
        return uncertainty_factors


class StructuredReasoningModality(ReasoningModality):
    """Structured data reasoning using numerical analysis"""
    
    def __init__(self):
        self.numerical_thresholds = {
            "high_coverage": 500000,
            "old_property": 30,  # years
            "high_deductible": 2000,
            "risk_score_high": 0.7,
            "risk_score_medium": 0.4
        }
        
        self.comparison_operators = {
            "greater_than": lambda a, b: a > b,
            "less_than": lambda a, b: a < b,
            "equal_to": lambda a, b: a == b,
            "between": lambda a, b, c: b <= a <= c
        }
    
    def reason(self, context: MultiModalContext) -> ReasoningResult:
        """Perform structured data reasoning"""
        
        if not context.structured_data:
            return ReasoningResult(
                modality=ModalityType.STRUCTURED,
                conclusion="No structured data available for reasoning",
                confidence=0.0,
                evidence=[],
                reasoning_steps=["No structured input provided"]
            )
        
        reasoning_steps = []
        evidence = []
        
        # Step 1: Extract numerical features
        numerical_features = self._extract_numerical_features(context.structured_data)
        reasoning_steps.append(f"Extracted {len(numerical_features)} numerical features")
        evidence.extend([f"{feature}: {value}" for feature, value in numerical_features.items()])
        
        # Step 2: Apply threshold analysis
        threshold_analysis = self._apply_threshold_analysis(numerical_features)
        reasoning_steps.append("Applied threshold analysis to numerical features")
        evidence.extend([f"Threshold: {analysis}" for analysis in threshold_analysis])
        
        # Step 3: Perform statistical analysis
        statistical_analysis = self._perform_statistical_analysis(numerical_features)
        reasoning_steps.append("Performed statistical analysis")
        evidence.extend([f"Stat: {stat}" for stat in statistical_analysis])
        
        # Step 4: Risk scoring
        risk_score = self._calculate_risk_score(numerical_features, threshold_analysis)
        reasoning_steps.append(f"Calculated risk score: {risk_score:.3f}")
        evidence.append(f"Risk score: {risk_score:.3f}")
        
        # Step 5: Generate conclusion
        conclusion = self._generate_structured_conclusion(risk_score, threshold_analysis, statistical_analysis)
        reasoning_steps.append(f"Structured conclusion: {conclusion}")
        
        # Calculate confidence
        confidence = self._calculate_structured_confidence(numerical_features, risk_score)
        
        # Identify uncertainty factors
        uncertainty_factors = self._get_structured_uncertainty_factors(context.structured_data, numerical_features)
        
        return ReasoningResult(
            modality=ModalityType.STRUCTURED,
            conclusion=conclusion,
            confidence=confidence,
            evidence=evidence,
            reasoning_steps=reasoning_steps,
            uncertainty_factors=uncertainty_factors,
            metadata={
                "numerical_features": numerical_features,
                "threshold_analysis": threshold_analysis,
                "statistical_analysis": statistical_analysis,
                "risk_score": risk_score
            }
        )
    
    def get_confidence(self, result: ReasoningResult) -> float:
        """Get confidence in structured reasoning"""
        return result.confidence
    
    def get_uncertainty_factors(self, result: ReasoningResult) -> List[str]:
        """Get uncertainty factors for structured reasoning"""
        return result.uncertainty_factors
    
    def _extract_numerical_features(self, data: Dict[str, Any]) -> Dict[str, float]:
        """Extract numerical features from structured data"""
        
        numerical_features = {}
        
        # Direct numerical fields
        numerical_fields = ["coverage_amount", "deductible", "construction_year", "square_footage", "roof_age"]
        for field in numerical_fields:
            if field in data and isinstance(data[field], (int, float)):
                numerical_features[field] = float(data[field])
        
        # Derived features
        if "construction_year" in numerical_features:
            numerical_features["property_age"] = 2024 - numerical_features["construction_year"]
        
        if "coverage_amount" in numerical_features and "square_footage" in numerical_features:
            numerical_features["coverage_per_sqft"] = numerical_features["coverage_amount"] / max(1, numerical_features["square_footage"])
        
        # Hazard scores
        if "hazard_scores" in data and isinstance(data["hazard_scores"], dict):
            for hazard_type, score in data["hazard_scores"].items():
                if isinstance(score, (int, float)):
                    numerical_features[f"hazard_{hazard_type}"] = float(score)
        
        return numerical_features
    
    def _apply_threshold_analysis(self, features: Dict[str, float]) -> List[str]:
        """Apply threshold analysis to numerical features"""
        
        analysis_results = []
        
        # Coverage analysis
        if "coverage_amount" in features:
            coverage = features["coverage_amount"]
            if coverage > self.numerical_thresholds["high_coverage"]:
                analysis_results.append(f"High coverage amount: ${coverage:,.0f}")
            else:
                analysis_results.append(f"Standard coverage amount: ${coverage:,.0f}")
        
        # Property age analysis
        if "property_age" in features:
            age = features["property_age"]
            if age > self.numerical_thresholds["old_property"]:
                analysis_results.append(f"Old property: {age:.0f} years")
            else:
                analysis_results.append(f"Modern property: {age:.0f} years")
        
        # Deductible analysis
        if "deductible" in features:
            deductible = features["deductible"]
            if deductible > self.numerical_thresholds["high_deductible"]:
                analysis_results.append(f"High deductible: ${deductible:,}")
            else:
                analysis_results.append(f"Standard deductible: ${deductible:,}")
        
        # Risk score analysis
        for feature, value in features.items():
            if feature.startswith("hazard_") and isinstance(value, (int, float)):
                if value > self.numerical_thresholds["risk_score_high"]:
                    analysis_results.append(f"High {feature.replace('_', ' ')} risk: {value:.3f}")
                elif value > self.numerical_thresholds["risk_score_medium"]:
                    analysis_results.append(f"Moderate {feature.replace('_', ' ')} risk: {value:.3f}")
                else:
                    analysis_results.append(f"Low {feature.replace('_', ' ')} risk: {value:.3f}")
        
        return analysis_results
    
    def _perform_statistical_analysis(self, features: Dict[str, float]) -> List[str]:
        """Perform statistical analysis on features"""
        
        if not features:
            return ["No numerical features for statistical analysis"]
        
        statistical_results = []
        
        # Basic statistics
        values = list(features.values())
        mean_value = statistics.mean(values)
        median_value = statistics.median(values)
        std_dev = statistics.stdev(values) if len(values) > 1 else 0.0
        
        statistical_results.append(f"Mean value: {mean_value:.2f}")
        statistical_results.append(f"Median value: {median_value:.2f}")
        statistical_results.append(f"Standard deviation: {std_dev:.2f}")
        
        # Distribution analysis
        if len(values) > 1:
            q1 = statistics.quantiles(values, n=4)[0]
            q3 = statistics.quantiles(values, n=4)[2]
            iqr = q3 - q1
            
            statistical_results.append(f"Interquartile range: {iqr:.2f}")
            
            # Outlier detection
            outliers = [v for v in values if v < q1 - 1.5 * iqr or v > q3 + 1.5 * iqr]
            if outliers:
                statistical_results.append(f"Outliers detected: {len(outliers)} values")
            else:
                statistical_results.append("No significant outliers detected")
        
        return statistical_results
    
    def _calculate_risk_score(self, features: Dict[str, float], threshold_analysis: List[str]) -> float:
        """Calculate overall risk score"""
        
        risk_factors = 0.0
        total_factors = 0.0
        
        # Coverage risk
        if "coverage_amount" in features:
            coverage = features["coverage_amount"]
            coverage_risk = min(1.0, coverage / 1000000)  # Normalize to 0-1
            risk_factors += coverage_risk
            total_factors += 1.0
        
        # Property age risk
        if "property_age" in features:
            age = features["property_age"]
            age_risk = min(1.0, age / 50)  # Normalize to 0-1 (50 years = max risk)
            risk_factors += age_risk
            total_factors += 1.0
        
        # Hazard risks
        hazard_features = [f for f in features.keys() if f.startswith("hazard_")]
        for hazard_feature in hazard_features:
            hazard_value = features[hazard_feature]
            risk_factors += hazard_value
            total_factors += 1.0
        
        # Calculate average risk score
        if total_factors > 0:
            risk_score = risk_factors / total_factors
        else:
            risk_score = 0.3  # Default moderate risk
        
        return risk_score
    
    def _generate_structured_conclusion(self, risk_score: float, threshold_analysis: List[str], statistical_analysis: List[str]) -> str:
        """Generate conclusion from structured analysis"""
        
        conclusion_parts = []
        
        # Risk-based conclusion
        if risk_score > 0.7:
            conclusion_parts.append("High numerical risk profile detected")
        elif risk_score > 0.4:
            conclusion_parts.append("Moderate numerical risk profile")
        else:
            conclusion_parts.append("Low numerical risk profile")
        
        # Add key findings from threshold analysis
        high_risk_indicators = [analysis for analysis in threshold_analysis if "High" in analysis]
        if high_risk_indicators:
            conclusion_parts.append(f"with {len(high_risk_indicators)} high-risk indicators")
        
        # Add statistical insights
        if "Outliers detected" in " ".join(statistical_analysis):
            conclusion_parts.append("and statistical anomalies present")
        
        return " ".join(conclusion_parts)
    
    def _calculate_structured_confidence(self, features: Dict[str, float], risk_score: float) -> float:
        """Calculate confidence in structured reasoning"""
        
        base_confidence = 0.7  # Structured data generally provides higher confidence
        
        # Adjust based on feature completeness
        feature_factor = min(1.0, len(features) / 8.0)  # 8 is a good number of features
        
        # Adjust based on data quality (no outliers, reasonable ranges)
        quality_factor = 0.8  # Assume good quality for structured data
        
        # Adjust based on risk score clarity
        risk_factor = 0.9 if risk_score not in [0.3, 0.5, 0.7] else 0.6  # Non-standard scores show more nuance
        
        confidence = base_confidence * feature_factor * quality_factor * risk_factor
        
        return max(0.1, min(0.95, confidence))
    
    def _get_structured_uncertainty_factors(self, data: Dict[str, Any], features: Dict[str, float]) -> List[str]:
        """Identify uncertainty factors in structured reasoning"""
        
        uncertainty_factors = []
        
        # Check for missing critical fields
        critical_fields = ["coverage_amount", "construction_year"]
        for field in critical_fields:
            if field not in data:
                uncertainty_factors.append(f"Missing critical field: {field}")
        
        # Check for unusual values
        if "coverage_amount" in features and features["coverage_amount"] > 2000000:
            uncertainty_factors.append("Unusually high coverage amount")
        
        if "property_age" in features and features["property_age"] > 100:
            uncertainty_factors.append("Unusually old property age")
        
        # Check for inconsistent data
        if "construction_year" in data and "roof_age" in data:
            construction_year = data["construction_year"]
            roof_age = data["roof_age"]
            property_age = 2024 - construction_year
            if roof_age > property_age:
                uncertainty_factors.append("Roof age exceeds property age - data inconsistency")
        
        # Check for missing hazard data
        hazard_features = [f for f in features.keys() if f.startswith("hazard_")]
        if not hazard_features:
            uncertainty_factors.append("No hazard risk data available")
        
        return uncertainty_factors


class RuleBasedReasoningModality(ReasoningModality):
    """Rule-based reasoning using logic and constraints"""
    
    def __init__(self):
        self.rule_categories = {
            "eligibility": self._eligibility_rules,
            "risk_assessment": self._risk_assessment_rules,
            "compliance": self._compliance_rules,
            "business_logic": self._business_logic_rules
        }
        
        self.logical_operators = {
            "AND": all,
            "OR": any,
            "NOT": lambda x: not x
        }
    
    def reason(self, context: MultiModalContext) -> ReasoningResult:
        """Perform rule-based reasoning"""
        
        if not context.rule_set:
            return ReasoningResult(
                modality=ModalityType.RULES,
                conclusion="No rules available for reasoning",
                confidence=0.0,
                evidence=[],
                reasoning_steps=["No rule set provided"]
            )
        
        reasoning_steps = []
        evidence = []
        
        # Step 1: Parse and organize rules
        organized_rules = self._organize_rules(context.rule_set)
        reasoning_steps.append(f"Organized {len(organized_rules)} rule categories")
        
        # Step 2: Apply eligibility rules
        eligibility_results = self._apply_rule_category("eligibility", organized_rules, context)
        reasoning_steps.append("Applied eligibility rules")
        evidence.extend(eligibility_results["evidence"])
        
        # Step 3: Apply risk assessment rules
        risk_results = self._apply_rule_category("risk_assessment", organized_rules, context)
        reasoning_steps.append("Applied risk assessment rules")
        evidence.extend(risk_results["evidence"])
        
        # Step 4: Apply compliance rules
        compliance_results = self._apply_rule_category("compliance", organized_rules, context)
        reasoning_steps.append("Applied compliance rules")
        evidence.extend(compliance_results["evidence"])
        
        # Step 5: Apply business logic rules
        business_results = self._apply_rule_category("business_logic", organized_rules, context)
        reasoning_steps.append("Applied business logic rules")
        evidence.extend(business_results["evidence"])
        
        # Step 6: Synthesize rule-based conclusion
        conclusion = self._synthesize_rule_conclusion(eligibility_results, risk_results, compliance_results, business_results)
        reasoning_steps.append(f"Rule-based conclusion: {conclusion}")
        
        # Calculate confidence
        confidence = self._calculate_rule_confidence(eligibility_results, risk_results, compliance_results, business_results)
        
        # Identify uncertainty factors
        uncertainty_factors = self._get_rule_uncertainty_factors(organized_rules, context)
        
        return ReasoningResult(
            modality=ModalityType.RULES,
            conclusion=conclusion,
            confidence=confidence,
            evidence=evidence,
            reasoning_steps=reasoning_steps,
            uncertainty_factors=uncertainty_factors,
            metadata={
                "eligibility_results": eligibility_results,
                "risk_results": risk_results,
                "compliance_results": compliance_results,
                "business_results": business_results
            }
        )
    
    def get_confidence(self, result: ReasoningResult) -> float:
        """Get confidence in rule-based reasoning"""
        return result.confidence
    
    def get_uncertainty_factors(self, result: ReasoningResult) -> List[str]:
        """Get uncertainty factors for rule-based reasoning"""
        return result.uncertainty_factors
    
    def _organize_rules(self, rule_set: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Organize rules by category"""
        
        organized = {}
        
        for category in self.rule_categories.keys():
            organized[category] = []
        
        # Categorize rules
        for rule_name, rule_definition in rule_set.items():
            rule_category = self._categorize_rule(rule_name, rule_definition)
            if rule_category in organized:
                organized[rule_category].append({
                    "name": rule_name,
                    "definition": rule_definition
                })
        
        return organized
    
    def _categorize_rule(self, rule_name: str, rule_definition: Dict[str, Any]) -> str:
        """Categorize a rule"""
        
        name_lower = rule_name.lower()
        
        if "eligible" in name_lower or "qualification" in name_lower:
            return "eligibility"
        elif "risk" in name_lower or "hazard" in name_lower:
            return "risk_assessment"
        elif "compliance" in name_lower or "regulation" in name_lower:
            return "compliance"
        else:
            return "business_logic"
    
    def _apply_rule_category(self, category: str, organized_rules: Dict[str, List[Dict[str, Any]]], context: MultiModalContext) -> Dict[str, Any]:
        """Apply rules from a specific category"""
        
        rules = organized_rules.get(category, [])
        results = {
            "rules_applied": len(rules),
            "rules_passed": 0,
            "rules_failed": 0,
            "evidence": [],
            "findings": []
        }
        
        if category in self.rule_categories:
            rule_function = self.rule_categories[category]
            for rule in rules:
                rule_result = rule_function(rule, context)
                results["evidence"].extend(rule_result["evidence"])
                results["findings"].append(rule_result["finding"])
                
                if rule_result["passed"]:
                    results["rules_passed"] += 1
                else:
                    results["rules_failed"] += 1
        
        return results
    
    def _eligibility_rules(self, rule: Dict[str, Any], context: MultiModalContext) -> Dict[str, Any]:
        """Apply eligibility rules"""
        
        rule_name = rule["name"]
        rule_def = rule["definition"]
        evidence = []
        finding = ""
        passed = False
        
        # Coverage eligibility rule
        if "coverage" in rule_name.lower():
            if context.structured_data and "coverage_amount" in context.structured_data:
                coverage = context.structured_data["coverage_amount"]
                min_coverage = rule_def.get("minimum", 0)
                max_coverage = rule_def.get("maximum", 10000000)
                
                passed = min_coverage <= coverage <= max_coverage
                evidence.append(f"Coverage amount: ${coverage:,}")
                evidence.append(f"Required range: ${min_coverage:,} - ${max_coverage:,}")
                
                if passed:
                    finding = f"Coverage eligibility rule passed: ${coverage:,} within range"
                else:
                    finding = f"Coverage eligibility rule failed: ${coverage:,} outside range"
            else:
                evidence.append("Coverage amount not available")
                finding = "Coverage eligibility rule inconclusive: missing data"
        
        # Property type eligibility rule
        elif "property_type" in rule_name.lower():
            if context.structured_data and "property_type" in context.structured_data:
                property_type = context.structured_data["property_type"]
                allowed_types = rule_def.get("allowed_types", ["single_family", "condo", "townhouse"])
                
                passed = property_type in allowed_types
                evidence.append(f"Property type: {property_type}")
                evidence.append(f"Allowed types: {', '.join(allowed_types)}")
                
                if passed:
                    finding = f"Property type eligibility passed: {property_type} is allowed"
                else:
                    finding = f"Property type eligibility failed: {property_type} not allowed"
            else:
                evidence.append("Property type not available")
                finding = "Property type eligibility rule inconclusive: missing data"
        
        return {
            "evidence": evidence,
            "finding": finding,
            "passed": passed
        }
    
    def _risk_assessment_rules(self, rule: Dict[str, Any], context: MultiModalContext) -> Dict[str, Any]:
        """Apply risk assessment rules"""
        
        rule_name = rule["name"]
        rule_def = rule["definition"]
        evidence = []
        finding = ""
        passed = False
        
        # Wildfire risk rule
        if "wildfire" in rule_name.lower():
            if context.structured_data and "hazard_scores" in context.structured_data:
                hazard_scores = context.structured_data["hazard_scores"]
                wildfire_risk = hazard_scores.get("wildfire_risk", 0.0)
                max_risk = rule_def.get("maximum_risk", 0.7)
                
                passed = wildfire_risk <= max_risk
                evidence.append(f"Wildfire risk score: {wildfire_risk:.3f}")
                evidence.append(f"Maximum acceptable risk: {max_risk:.3f}")
                
                if passed:
                    finding = f"Wildfire risk assessment passed: {wildfire_risk:.3f} <= {max_risk:.3f}"
                else:
                    finding = f"Wildfire risk assessment failed: {wildfire_risk:.3f} > {max_risk:.3f}"
            else:
                evidence.append("Wildfire risk score not available")
                finding = "Wildfire risk assessment inconclusive: missing data"
        
        # Property age risk rule
        elif "property_age" in rule_name.lower():
            if context.structured_data and "construction_year" in context.structured_data:
                construction_year = context.structured_data["construction_year"]
                property_age = 2024 - construction_year
                max_age = rule_def.get("maximum_age", 50)
                
                passed = property_age <= max_age
                evidence.append(f"Property age: {property_age} years")
                evidence.append(f"Maximum acceptable age: {max_age} years")
                
                if passed:
                    finding = f"Property age risk assessment passed: {property_age} <= {max_age}"
                else:
                    finding = f"Property age risk assessment failed: {property_age} > {max_age}"
            else:
                evidence.append("Property age not available")
                finding = "Property age risk assessment inconclusive: missing data"
        
        return {
            "evidence": evidence,
            "finding": finding,
            "passed": passed
        }
    
    def _compliance_rules(self, rule: Dict[str, Any], context: MultiModalContext) -> Dict[str, Any]:
        """Apply compliance rules"""
        
        rule_name = rule["name"]
        rule_def = rule["definition"]
        evidence = []
        finding = ""
        passed = False
        
        # State compliance rule
        if "state" in rule_name.lower():
            if context.structured_data and "state" in context.structured_data:
                state = context.structured_data["state"]
                restricted_states = rule_def.get("restricted_states", [])
                
                passed = state not in restricted_states
                evidence.append(f"Property state: {state}")
                evidence.append(f"Restricted states: {', '.join(restricted_states)}")
                
                if passed:
                    finding = f"State compliance passed: {state} not restricted"
                else:
                    finding = f"State compliance failed: {state} is restricted"
            else:
                evidence.append("State not available")
                finding = "State compliance rule inconclusive: missing data"
        
        # Documentation compliance rule
        elif "documentation" in rule_name.lower():
            required_docs = rule_def.get("required_documents", [])
            available_docs = context.domain_constraints.get("available_documents", [])
            
            missing_docs = [doc for doc in required_docs if doc not in available_docs]
            passed = len(missing_docs) == 0
            
            evidence.append(f"Required documents: {', '.join(required_docs)}")
            evidence.append(f"Available documents: {', '.join(available_docs)}")
            
            if passed:
                finding = "Documentation compliance passed: all required documents available"
            else:
                finding = f"Documentation compliance failed: missing {', '.join(missing_docs)}"
        
        return {
            "evidence": evidence,
            "finding": finding,
            "passed": passed
        }
    
    def _business_logic_rules(self, rule: Dict[str, Any], context: MultiModalContext) -> Dict[str, Any]:
        """Apply business logic rules"""
        
        rule_name = rule["name"]
        rule_def = rule["definition"]
        evidence = []
        finding = ""
        passed = False
        
        # California business rule
        if "california" in rule_name.lower():
            if context.structured_data and "state" in context.structured_data:
                state = context.structured_data["state"]
                is_california = state == "CA"
                
                if is_california:
                    # California-specific requirements
                    required_wildfire_doc = rule_def.get("requires_wildfire_documentation", False)
                    has_wildfire_doc = context.domain_constraints.get("wildfire_documentation", False)
                    
                    if required_wildfire_doc:
                        passed = has_wildfire_doc
                        evidence.append("California property requires wildfire documentation")
                        evidence.append(f"Wildfire documentation available: {has_wildfire_doc}")
                        
                        if passed:
                            finding = "California business rule passed: wildfire documentation available"
                        else:
                            finding = "California business rule failed: wildfire documentation missing"
                    else:
                        passed = True
                        evidence.append("California property with no special documentation requirements")
                        finding = "California business rule passed: no special requirements"
                else:
                    passed = True
                    evidence.append(f"Non-California property: {state}")
                    finding = "California business rule not applicable"
            else:
                evidence.append("State not available")
                finding = "California business rule inconclusive: missing data"
        
        return {
            "evidence": evidence,
            "finding": finding,
            "passed": passed
        }
    
    def _synthesize_rule_conclusion(self, eligibility: Dict[str, Any], risk: Dict[str, Any], compliance: Dict[str, Any], business: Dict[str, Any]) -> str:
        """Synthesize conclusion from all rule categories"""
        
        conclusion_parts = []
        
        # Count total rules and failures
        total_rules = eligibility["rules_applied"] + risk["rules_applied"] + compliance["rules_applied"] + business["rules_applied"]
        total_failures = eligibility["rules_failed"] + risk["rules_failed"] + compliance["rules_failed"] + business["rules_failed"]
        
        if total_failures == 0:
            conclusion_parts.append("All rules passed")
        elif total_failures <= total_rules * 0.2:  # Less than 20% failure
            conclusion_parts.append("Most rules passed with minor exceptions")
        elif total_failures <= total_rules * 0.5:  # Less than 50% failure
            conclusion_parts.append("Significant rule failures detected")
        else:
            conclusion_parts.append("Major rule compliance issues")
        
        # Add specific category insights
        if eligibility["rules_failed"] > 0:
            conclusion_parts.append("including eligibility issues")
        
        if risk["rules_failed"] > 0:
            conclusion_parts.append("and risk assessment concerns")
        
        if compliance["rules_failed"] > 0:
            conclusion_parts.append("with compliance violations")
        
        return " ".join(conclusion_parts)
    
    def _calculate_rule_confidence(self, eligibility: Dict[str, Any], risk: Dict[str, Any], compliance: Dict[str, Any], business: Dict[str, Any]) -> float:
        """Calculate confidence in rule-based reasoning"""
        
        base_confidence = 0.8  # Rules generally provide high confidence
        
        # Calculate rule pass rate
        total_rules = eligibility["rules_applied"] + risk["rules_applied"] + compliance["rules_applied"] + business["rules_applied"]
        total_passed = eligibility["rules_passed"] + risk["rules_passed"] + compliance["rules_passed"] + business["rules_passed"]
        
        if total_rules > 0:
            pass_rate = total_passed / total_rules
        else:
            pass_rate = 0.5
        
        # Adjust confidence based on rule coverage
        coverage_factor = min(1.0, total_rules / 10.0)  # 10 rules is good coverage
        
        # Adjust confidence based on consistency
        consistency_factor = pass_rate  # Higher pass rate = more consistent
        
        confidence = base_confidence * coverage_factor * consistency_factor
        
        return max(0.1, min(0.95, confidence))
    
    def _get_rule_uncertainty_factors(self, organized_rules: Dict[str, List[Dict[str, Any]]], context: MultiModalContext) -> List[str]:
        """Identify uncertainty factors in rule-based reasoning"""
        
        uncertainty_factors = []
        
        # Check for missing rule categories
        for category, rules in organized_rules.items():
            if not rules:
                uncertainty_factors.append(f"No rules defined for {category}")
        
        # Check for missing data required by rules
        if not context.structured_data:
            uncertainty_factors.append("No structured data available for rule evaluation")
        
        # Check for ambiguous rule definitions
        for category, rules in organized_rules.items():
            for rule in rules:
                rule_def = rule["definition"]
                if not rule_def or isinstance(rule_def, dict) and len(rule_def) == 0:
                    uncertainty_factors.append(f"Ambiguous rule definition: {rule['name']}")
        
        return uncertainty_factors


class MultiModalReasoningSystem:
    """Main multi-modal reasoning system that orchestrates all modalities"""
    
    def __init__(self):
        """Initialize multi-modal reasoning system"""
        
        # Initialize reasoning modalities
        self.text_modality = TextReasoningModality()
        self.structured_modality = StructuredReasoningModality()
        self.rules_modality = RuleBasedReasoningModality()
        
        # Reasoning strategies
        self.reasoning_strategies = {
            ReasoningStrategy.WEIGHTED_FUSION: self._weighted_fusion_strategy,
            ReasoningStrategy.HIERARCHICAL: self._hierarchical_strategy,
            ReasoningStrategy.CONSENSUS_BASED: self._consensus_based_strategy,
            ReasoningStrategy.UNCERTAINTY_AWARE: self._uncertainty_aware_strategy,
            ReasoningStrategy.ADAPTIVE_SELECTION: self._adaptive_selection_strategy
        }
        
        # Performance tracking
        self.reasoning_history: List[Dict[str, Any]] = []
        self.modality_performance = {
            ModalityType.TEXT: {"confidence_sum": 0.0, "usage_count": 0},
            ModalityType.STRUCTURED: {"confidence_sum": 0.0, "usage_count": 0},
            ModalityType.RULES: {"confidence_sum": 0.0, "usage_count": 0}
        }
        
        logger.info("Multi-Modal Reasoning System initialized with all modalities")
    
    def reason_multi_modal(
        self,
        query: str,
        text_data: Optional[str] = None,
        structured_data: Optional[Dict[str, Any]] = None,
        rule_set: Optional[Dict[str, Any]] = None,
        strategy: ReasoningStrategy = ReasoningStrategy.WEIGHTED_FUSION,
        domain_constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Perform multi-modal reasoning using specified strategy"""
        
        logger.info(f"Starting multi-modal reasoning with strategy: {strategy.value}")
        
        # Create reasoning context
        context = MultiModalContext(
            query=query,
            text_data=text_data,
            structured_data=structured_data,
            rule_set=rule_set,
            domain_constraints=domain_constraints or {}
        )
        
        # Perform reasoning for each modality
        modality_results = {}
        
        if text_data:
            text_result = self.text_modality.reason(context)
            modality_results[ModalityType.TEXT] = text_result
            self._update_modality_performance(ModalityType.TEXT, text_result)
        
        if structured_data:
            structured_result = self.structured_modality.reason(context)
            modality_results[ModalityType.STRUCTURED] = structured_result
            self._update_modality_performance(ModalityType.STRUCTURED, structured_result)
        
        if rule_set:
            rules_result = self.rules_modality.reason(context)
            modality_results[ModalityType.RULES] = rules_result
            self._update_modality_performance(ModalityType.RULES, rules_result)
        
        # Apply reasoning strategy
        strategy_function = self.reasoning_strategies[strategy]
        final_result = strategy_function(modality_results, context)
        
        # Record reasoning session
        reasoning_session = {
            "timestamp": datetime.now(),
            "query": query,
            "strategy": strategy.value,
            "modality_results": {modality.value: result.to_dict() for modality, result in modality_results.items()},
            "final_result": final_result,
            "modality_count": len(modality_results)
        }
        self.reasoning_history.append(reasoning_session)
        
        logger.info(f"Multi-modal reasoning completed: {final_result['conclusion']} (confidence: {final_result['confidence']:.3f})")
        
        return final_result
    
    def _weighted_fusion_strategy(self, modality_results: Dict[ModalityType, ReasoningResult], context: MultiModalContext) -> Dict[str, Any]:
        """Weighted fusion strategy combining all modalities"""
        
        if not modality_results:
            return {
                "conclusion": "No modality results available",
                "confidence": 0.0,
                "reasoning": "No reasoning performed",
                "modality_contributions": {}
            }
        
        # Calculate weights based on confidence and historical performance
        weights = {}
        total_weight = 0.0
        
        for modality, result in modality_results.items():
            # Base weight from current confidence
            base_weight = result.confidence
            
            # Adjust based on historical performance
            perf = self.modality_performance[modality]
            historical_confidence = perf["confidence_sum"] / perf["usage_count"] if perf["usage_count"] > 0 else 0.5
            performance_adjustment = historical_confidence
            
            # Final weight
            final_weight = base_weight * performance_adjustment
            weights[modality] = final_weight
            total_weight += final_weight
        
        # Normalize weights
        if total_weight > 0:
            weights = {modality: weight / total_weight for modality, weight in weights.items()}
        
        # Synthesize conclusion
        conclusion_parts = []
        confidence_sum = 0.0
        all_evidence = []
        all_uncertainty = []
        
        for modality, result in modality_results.items():
            weight = weights[modality]
            conclusion_parts.append(f"{modality.value} analysis ({weight:.2f}): {result.conclusion}")
            confidence_sum += result.confidence * weight
            all_evidence.extend(result.evidence)
            all_uncertainty.extend(result.uncertainty_factors)
        
        final_conclusion = " | ".join(conclusion_parts)
        final_confidence = confidence_sum
        
        # Remove duplicate evidence
        unique_evidence = list(set(all_evidence))
        unique_uncertainty = list(set(all_uncertainty))
        
        return {
            "conclusion": final_conclusion,
            "confidence": final_confidence,
            "reasoning": f"Weighted fusion of {len(modality_results)} modalities",
            "modality_contributions": {
                modality.value: {
                    "weight": weights[modality],
                    "confidence": result.confidence,
                    "conclusion": result.conclusion
                }
                for modality, result in modality_results.items()
            },
            "evidence": unique_evidence,
            "uncertainty_factors": unique_uncertainty,
            "strategy_used": "weighted_fusion"
        }
    
    def _hierarchical_strategy(self, modality_results: Dict[ModalityType, ReasoningResult], context: MultiModalContext) -> Dict[str, Any]:
        """Hierarchical strategy prioritizing certain modalities"""
        
        # Define modality hierarchy: Rules > Structured > Text
        modality_hierarchy = [ModalityType.RULES, ModalityType.STRUCTURED, ModalityType.TEXT]
        
        # Find highest priority modality with results
        primary_modality = None
        primary_result = None
        
        for modality in modality_hierarchy:
            if modality in modality_results:
                primary_modality = modality
                primary_result = modality_results[modality]
                break
        
        if not primary_modality:
            return {
                "conclusion": "No modality results available for hierarchical reasoning",
                "confidence": 0.0,
                "reasoning": "No reasoning performed",
                "modality_contributions": {}
            }
        
        # Use primary modality as base, enhance with others
        conclusion = f"Primary ({primary_modality.value}): {primary_result.conclusion}"
        confidence = primary_result.confidence
        evidence = primary_result.evidence.copy()
        uncertainty = primary_result.uncertainty_factors.copy()
        
        # Enhance with secondary modalities
        secondary_contributions = {}
        for modality, result in modality_results.items():
            if modality != primary_modality:
                # Add supporting evidence
                evidence.extend(result.evidence)
                uncertainty.extend(result.uncertainty_factors)
                
                secondary_contributions[modality.value] = {
                    "conclusion": result.conclusion,
                    "confidence": result.confidence,
                    "role": "supporting"
                }
                
                # Adjust confidence slightly based on supporting evidence
                if result.confidence > 0.7:
                    confidence += 0.05
        
        confidence = min(0.95, confidence)  # Cap confidence
        
        return {
            "conclusion": conclusion,
            "confidence": confidence,
            "reasoning": f"Hierarchical reasoning with primary modality: {primary_modality.value}",
            "modality_contributions": {
                "primary": {
                    "modality": primary_modality.value,
                    "conclusion": primary_result.conclusion,
                    "confidence": primary_result.confidence
                },
                "secondary": secondary_contributions
            },
            "evidence": list(set(evidence)),
            "uncertainty_factors": list(set(uncertainty)),
            "strategy_used": "hierarchical"
        }
    
    def _consensus_based_strategy(self, modality_results: Dict[ModalityType, ReasoningResult], context: MultiModalContext) -> Dict[str, Any]:
        """Consensus-based strategy seeking agreement between modalities"""
        
        if not modality_results:
            return {
                "conclusion": "No modality results available for consensus reasoning",
                "confidence": 0.0,
                "reasoning": "No reasoning performed",
                "modality_contributions": {}
            }
        
        # Extract key themes from conclusions
        conclusion_themes = {}
        for modality, result in modality_results.items():
            themes = self._extract_conclusion_themes(result.conclusion)
            for theme in themes:
                if theme not in conclusion_themes:
                    conclusion_themes[theme] = []
                conclusion_themes[theme].append(modality)
        
        # Find consensus themes (appearing in multiple modalities)
        consensus_themes = [theme for theme, modalities in conclusion_themes.items() if len(modalities) > 1]
        
        # Calculate consensus strength
        if consensus_themes:
            consensus_strength = len(consensus_themes) / len(modality_results)
        else:
            consensus_strength = 0.0
        
        # Build consensus conclusion
        if consensus_themes:
            conclusion_parts = [f"Consensus on: {', '.join(consensus_themes)}"]
            confidence = 0.5 + (consensus_strength * 0.4)  # Base 0.5 + up to 0.4 for consensus
        else:
            conclusion_parts = ["No clear consensus between modalities"]
            confidence = 0.3  # Low confidence without consensus
        
        # Add individual modality insights
        modality_insights = {}
        for modality, result in modality_results.items():
            modality_insights[modality.value] = {
                "conclusion": result.conclusion,
                "confidence": result.confidence,
                "themes": self._extract_conclusion_themes(result.conclusion)
            }
        
        # Combine all evidence
        all_evidence = []
        all_uncertainty = []
        for result in modality_results.values():
            all_evidence.extend(result.evidence)
            all_uncertainty.extend(result.uncertainty_factors)
        
        return {
            "conclusion": " | ".join(conclusion_parts),
            "confidence": confidence,
            "reasoning": f"Consensus-based reasoning with {len(consensus_themes)} consensus themes",
            "modality_contributions": modality_insights,
            "consensus_themes": consensus_themes,
            "consensus_strength": consensus_strength,
            "evidence": list(set(all_evidence)),
            "uncertainty_factors": list(set(all_uncertainty)),
            "strategy_used": "consensus_based"
        }
    
    def _uncertainty_aware_strategy(self, modality_results: Dict[ModalityType, ReasoningResult], context: MultiModalContext) -> Dict[str, Any]:
        """Uncertainty-aware strategy that considers uncertainty factors"""
        
        if not modality_results:
            return {
                "conclusion": "No modality results available for uncertainty-aware reasoning",
                "confidence": 0.0,
                "reasoning": "No reasoning performed",
                "modality_contributions": {}
            }
        
        # Calculate uncertainty-adjusted confidences
        adjusted_results = {}
        for modality, result in modality_results.items():
            uncertainty_penalty = len(result.uncertainty_factors) * 0.1  # 0.1 penalty per uncertainty factor
            adjusted_confidence = max(0.1, result.confidence - uncertainty_penalty)
            
            adjusted_results[modality] = {
                "original_result": result,
                "adjusted_confidence": adjusted_confidence,
                "uncertainty_count": len(result.uncertainty_factors),
                "uncertainty_penalty": uncertainty_penalty
            }
        
        # Select modality with highest adjusted confidence
        best_modality = max(adjusted_results, key=lambda m: adjusted_results[m]["adjusted_confidence"])
        best_result = adjusted_results[best_modality]
        
        # Build conclusion
        original_result = best_result["original_result"]
        conclusion = f"Uncertainty-adjusted ({best_modality.value}): {original_result.conclusion}"
        confidence = best_result["adjusted_confidence"]
        
        # Add uncertainty analysis
        uncertainty_analysis = {
            "selected_modality": best_modality.value,
            "uncertainty_factors": original_result.uncertainty_factors,
            "uncertainty_penalty": best_result["uncertainty_penalty"],
            "original_confidence": original_result.confidence,
            "adjusted_confidence": confidence
        }
        
        # Add other modalities as supporting
        supporting_modalities = {}
        for modality, result in modality_results.items():
            if modality != best_modality:
                supporting_modalities[modality.value] = {
                    "conclusion": result.conclusion,
                    "original_confidence": result.confidence,
                    "adjusted_confidence": adjusted_results[modality]["adjusted_confidence"],
                    "role": "supporting"
                }
        
        return {
            "conclusion": conclusion,
            "confidence": confidence,
            "reasoning": f"Uncertainty-aware reasoning selecting {best_modality.value} as most reliable",
            "modality_contributions": {
                "primary": uncertainty_analysis,
                "supporting": supporting_modalities
            },
            "evidence": original_result.evidence,
            "uncertainty_factors": original_result.uncertainty_factors,
            "strategy_used": "uncertainty_aware"
        }
    
    def _adaptive_selection_strategy(self, modality_results: Dict[ModalityType, ReasoningResult], context: MultiModalContext) -> Dict[str, Any]:
        """Adaptive selection strategy that chooses best approach based on context"""
        
        if not modality_results:
            return {
                "conclusion": "No modality results available for adaptive reasoning",
                "confidence": 0.0,
                "reasoning": "No reasoning performed",
                "modality_contributions": {}
            }
        
        # Analyze context to determine best strategy
        context_analysis = self._analyze_context_for_adaptation(context, modality_results)
        
        # Select appropriate sub-strategy
        if context_analysis["has_high_quality_structured_data"]:
            return self._weighted_fusion_strategy(modality_results, context)
        elif context_analysis["has_strong_rules"]:
            return self._hierarchical_strategy(modality_results, context)
        elif context_analysis["has_consensus_potential"]:
            return self._consensus_based_strategy(modality_results, context)
        else:
            return self._uncertainty_aware_strategy(modality_results, context)
    
    def _extract_conclusion_themes(self, conclusion: str) -> List[str]:
        """Extract key themes from conclusion"""
        
        themes = []
        conclusion_lower = conclusion.lower()
        
        # Risk themes
        if any(word in conclusion_lower for word in ["risk", "hazard", "danger"]):
            themes.append("risk")
        
        # Eligibility themes
        if any(word in conclusion_lower for word in ["eligible", "qualified", "suitable"]):
            themes.append("eligibility")
        
        # Compliance themes
        if any(word in conclusion_lower for word in ["compliant", "regulation", "requirement"]):
            themes.append("compliance")
        
        # Decision themes
        if any(word in conclusion_lower for word in ["accept", "approve", "positive"]):
            themes.append("positive_decision")
        elif any(word in conclusion_lower for word in ["decline", "reject", "negative"]):
            themes.append("negative_decision")
        elif any(word in conclusion_lower for word in ["refer", "review", "neutral"]):
            themes.append("neutral_decision")
        
        return themes
    
    def _analyze_context_for_adaptation(self, context: MultiModalContext, modality_results: Dict[ModalityType, ReasoningResult]) -> Dict[str, Any]:
        """Analyze context to determine best adaptive strategy"""
        
        analysis = {
            "has_high_quality_structured_data": False,
            "has_strong_rules": False,
            "has_consensus_potential": False
        }
        
        # Check structured data quality
        if context.structured_data:
            structured_keys = len(context.structured_data)
            analysis["has_high_quality_structured_data"] = structured_keys >= 5
        
        # Check rules strength
        if context.rule_set:
            rule_count = len(context.rule_set)
            analysis["has_strong_rules"] = rule_count >= 3
        
        # Check consensus potential
        if len(modality_results) >= 2:
            # Check if modalities have similar confidence levels
            confidences = [result.confidence for result in modality_results.values()]
            confidence_variance = statistics.variance(confidences) if len(confidences) > 1 else 0.0
            analysis["has_consensus_potential"] = confidence_variance < 0.1  # Low variance = potential consensus
        
        return analysis
    
    def _update_modality_performance(self, modality: ModalityType, result: ReasoningResult):
        """Update performance tracking for modality"""
        
        perf = self.modality_performance[modality]
        perf["confidence_sum"] += result.confidence
        perf["usage_count"] += 1
    
    def get_reasoning_summary(self) -> Dict[str, Any]:
        """Get comprehensive reasoning system summary"""
        
        return {
            "system_statistics": {
                "total_reasoning_sessions": len(self.reasoning_history),
                "modality_usage": {
                    modality.value: perf["usage_count"]
                    for modality, perf in self.modality_performance.items()
                },
                "average_confidence_by_modality": {
                    modality.value: (perf["confidence_sum"] / perf["usage_count"]) if perf["usage_count"] > 0 else 0.0
                    for modality, perf in self.modality_performance.items()
                }
            },
            "available_modalities": [modality.value for modality in ModalityType],
            "available_strategies": [strategy.value for strategy in ReasoningStrategy],
            "recent_sessions": [
                {
                    "timestamp": session["timestamp"].isoformat(),
                    "query": session["query"],
                    "strategy": session["strategy"],
                    "modality_count": session["modality_count"],
                    "confidence": session["final_result"]["confidence"]
                }
                for session in self.reasoning_history[-5:]
            ]
        }


# Global multi-modal reasoning system instance
_global_multimodal_system: Optional[MultiModalReasoningSystem] = None


def get_multimodal_reasoning_system() -> MultiModalReasoningSystem:
    """Get global multi-modal reasoning system instance"""
    global _global_multimodal_system
    if _global_multimodal_system is None:
        _global_multimodal_system = MultiModalReasoningSystem()
    return _global_multimodal_system
