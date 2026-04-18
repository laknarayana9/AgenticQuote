"""
Adaptive Learning System with Continuous Improvement
Implements sophisticated learning capabilities that demonstrate:

- Continuous learning from decision outcomes
- Performance-based strategy adaptation
- Pattern recognition and model updating
- Feedback loop integration
- Knowledge base evolution
- Predictive performance optimization
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import uuid
import json
import statistics
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class LearningType(Enum):
    """Types of learning mechanisms"""
    SUPERVISED = "supervised"           # Learning from labeled outcomes
    REINFORCEMENT = "reinforcement"     # Learning from rewards/penalties
    UNSUPERVISED = "unsupervised"       # Learning from patterns
    TRANSFER = "transfer"               # Transfer learning from similar cases
    META_LEARNING = "meta_learning"     # Learning how to learn


class FeedbackType(Enum):
    """Types of feedback for learning"""
    EXPLICIT = "explicit"               # Direct human feedback
    IMPLICIT = "implicit"               # Inferred from outcomes
    PERFORMANCE = "performance"         # Based on performance metrics
    DOMAIN = "domain"                   # Domain expert feedback


class AdaptationStrategy(Enum):
    """Strategy for adapting behavior"""
    CONSERVATIVE = "conservative"       # Slow, careful adaptation
    AGGRESSIVE = "aggressive"           # Fast, bold adaptation
    BALANCED = "balanced"               # Moderate adaptation
    SITUATIONAL = "situational"        # Context-dependent adaptation


@dataclass
class LearningExample:
    """Single learning example with feedback"""
    example_id: str
    input_data: Dict[str, Any]
    prediction: Dict[str, Any]
    actual_outcome: Dict[str, Any]
    feedback: Dict[str, Any]
    feedback_type: FeedbackType
    confidence: float
    timestamp: datetime
    learning_value: float = 0.0  # Calculated learning value
    domain_context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceMetrics:
    """Performance metrics for learning evaluation"""
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    confidence_calibration: float = 0.0
    processing_efficiency: float = 0.0
    adaptation_rate: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class LearningPattern:
    """Discovered learning pattern"""
    pattern_id: str
    pattern_type: str
    description: str
    confidence: float
    frequency: int
    last_observed: datetime
    predictive_power: float = 0.0
    action_recommendations: List[str] = field(default_factory=list)


@dataclass
class AdaptationRecord:
    """Record of system adaptation"""
    adaptation_id: str
    timestamp: datetime
    adaptation_type: str
    trigger: str
    old_behavior: Dict[str, Any]
    new_behavior: Dict[str, Any]
    expected_improvement: float
    actual_improvement: Optional[float] = None
    success: Optional[bool] = None


class LearningAlgorithm(ABC):
    """Abstract base class for learning algorithms"""
    
    @abstractmethod
    def learn(self, examples: List[LearningExample]) -> Dict[str, Any]:
        """Learn from examples and return updated model"""
        pass
    
    @abstractmethod
    def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Make prediction based on learned model"""
        pass
    
    @abstractmethod
    def evaluate(self, examples: List[LearningExample]) -> PerformanceMetrics:
        """Evaluate model performance"""
        pass


class SupervisedLearningAlgorithm(LearningAlgorithm):
    """Supervised learning from labeled outcomes"""
    
    def __init__(self):
        self.model_weights = {}
        self.feature_importance = {}
        self.learning_rate = 0.1
        self.decision_thresholds = {}
        
    def learn(self, examples: List[LearningExample]) -> Dict[str, Any]:
        """Learn from labeled examples"""
        
        if not examples:
            return {"model_updated": False, "reason": "No examples provided"}
        
        # Extract features and outcomes
        features, outcomes = self._extract_features_and_outcomes(examples)
        
        # Update model weights using gradient descent
        weight_updates = self._calculate_weight_updates(features, outcomes)
        
        # Apply updates with learning rate
        for feature, update in weight_updates.items():
            self.model_weights[feature] = self.model_weights.get(feature, 0.0) + (self.learning_rate * update)
        
        # Update feature importance
        self._update_feature_importance(features, outcomes)
        
        # Update decision thresholds
        self._update_decision_thresholds(examples)
        
        return {
            "model_updated": True,
            "weights_updated": len(weight_updates),
            "feature_importance_updated": len(self.feature_importance),
            "learning_rate": self.learning_rate,
            "examples_processed": len(examples)
        }
    
    def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Make prediction using learned model"""
        
        # Extract features from input
        features = self._extract_features(input_data)
        
        # Calculate prediction score
        prediction_score = 0.0
        for feature, value in features.items():
            weight = self.model_weights.get(feature, 0.0)
            prediction_score += weight * value
        
        # Apply decision thresholds
        decision = self._apply_thresholds(prediction_score, features)
        
        # Calculate confidence
        confidence = self._calculate_prediction_confidence(features, prediction_score)
        
        return {
            "prediction": decision,
            "score": prediction_score,
            "confidence": confidence,
            "features_used": list(features.keys()),
            "model_confidence": self._get_model_confidence()
        }
    
    def evaluate(self, examples: List[LearningExample]) -> PerformanceMetrics:
        """Evaluate model performance"""
        
        if not examples:
            return PerformanceMetrics()
        
        predictions = []
        actuals = []
        confidences = []
        
        for example in examples:
            prediction = self.predict(example.input_data)
            predictions.append(prediction["prediction"])
            actuals.append(example.actual_outcome.get("decision", "UNKNOWN"))
            confidences.append(prediction["confidence"])
        
        # Calculate metrics
        accuracy = self._calculate_accuracy(predictions, actuals)
        precision = self._calculate_precision(predictions, actuals)
        recall = self._calculate_recall(predictions, actuals)
        f1_score = self._calculate_f1_score(precision, recall)
        confidence_calibration = self._calculate_confidence_calibration(confidences, predictions, actuals)
        
        return PerformanceMetrics(
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            confidence_calibration=confidence_calibration,
            processing_efficiency=0.8,  # Mock metric
            adaptation_rate=self.learning_rate
        )
    
    def _extract_features_and_outcomes(self, examples: List[LearningExample]) -> Tuple[List[Dict[str, float]], List[str]]:
        """Extract features and outcomes from examples"""
        features = []
        outcomes = []
        
        for example in examples:
            feature_dict = self._extract_features(example.input_data)
            features.append(feature_dict)
            outcomes.append(example.actual_outcome.get("decision", "UNKNOWN"))
        
        return features, outcomes
    
    def _extract_features(self, input_data: Dict[str, Any]) -> Dict[str, float]:
        """Extract numerical features from input data"""
        features = {}
        
        # Basic numerical features
        if "coverage_amount" in input_data:
            features["coverage_normalized"] = min(1.0, input_data["coverage_amount"] / 1000000)
        
        if "construction_year" in input_data:
            features["property_age"] = max(0, 2024 - input_data["construction_year"]) / 100
        
        # Categorical features (one-hot encoding)
        if "property_type" in input_data:
            property_type = input_data["property_type"]
            features[f"property_type_{property_type}"] = 1.0
        
        if "state" in input_data:
            state = input_data["state"]
            features[f"state_{state}"] = 1.0
        
        # Risk features
        if "hazard_scores" in input_data:
            hazards = input_data["hazard_scores"]
            for hazard_type, score in hazards.items():
                features[f"hazard_{hazard_type}"] = score
        
        # Default features if none found
        if not features:
            features["default"] = 1.0
        
        return features
    
    def _calculate_weight_updates(self, features: List[Dict[str, float]], outcomes: List[str]) -> Dict[str, float]:
        """Calculate weight updates using gradient descent"""
        weight_updates = {}
        
        # Simple gradient descent calculation
        for i, (feature_dict, outcome) in enumerate(zip(features, outcomes)):
            prediction_score = sum(self.model_weights.get(f, 0.0) * v for f, v in feature_dict.items())
            expected_score = 1.0 if outcome == "ACCEPT" else 0.0 if outcome == "DECLINE" else 0.5
            error = expected_score - prediction_score
            
            for feature, value in feature_dict.items():
                if feature not in weight_updates:
                    weight_updates[feature] = 0.0
                weight_updates[feature] += error * value
        
        # Average updates
        for feature in weight_updates:
            weight_updates[feature] /= len(features)
        
        return weight_updates
    
    def _update_feature_importance(self, features: List[Dict[str, float]], outcomes: List[str]):
        """Update feature importance based on predictive power"""
        
        # Calculate feature importance using correlation with outcomes
        feature_values = {}
        for feature_dict in features:
            for feature, value in feature_dict.items():
                if feature not in feature_values:
                    feature_values[feature] = []
                feature_values[feature].append(value)
        
        # Simple importance calculation (absolute correlation)
        for feature, values in feature_values.items():
            if len(set(values)) > 1:  # Feature has variation
                importance = len(set(values)) / len(values)  # Simple proxy for importance
                self.feature_importance[feature] = importance
    
    def _update_decision_thresholds(self, examples: List[LearningExample]):
        """Update decision thresholds based on recent examples"""
        
        # Calculate optimal thresholds based on recent performance
        accept_scores = []
        decline_scores = []
        
        for example in examples:
            features = self._extract_features(example.input_data)
            score = sum(self.model_weights.get(f, 0.0) * v for f, v in features.items())
            
            if example.actual_outcome.get("decision") == "ACCEPT":
                accept_scores.append(score)
            elif example.actual_outcome.get("decision") == "DECLINE":
                decline_scores.append(score)
        
        if accept_scores and decline_scores:
            # Set threshold as midpoint between accept and decline scores
            accept_avg = statistics.mean(accept_scores)
            decline_avg = statistics.mean(decline_scores)
            self.decision_thresholds["accept_threshold"] = (accept_avg + decline_avg) / 2
    
    def _apply_thresholds(self, score: float, features: Dict[str, float]) -> str:
        """Apply decision thresholds to score"""
        
        accept_threshold = self.decision_thresholds.get("accept_threshold", 0.5)
        
        if score > accept_threshold:
            return "ACCEPT"
        elif score < accept_threshold - 0.2:
            return "DECLINE"
        else:
            return "REFER"
    
    def _calculate_prediction_confidence(self, features: Dict[str, float], score: float) -> float:
        """Calculate confidence in prediction"""
        
        # Base confidence on feature coverage
        feature_coverage = len(features) / max(len(self.feature_importance), 1)
        
        # Adjust based on distance from threshold
        threshold = self.decision_thresholds.get("accept_threshold", 0.5)
        distance_from_threshold = abs(score - threshold)
        confidence_from_distance = min(1.0, distance_from_threshold * 2)
        
        # Combine factors
        confidence = (feature_coverage + confidence_from_distance) / 2
        
        return max(0.1, min(0.95, confidence))
    
    def _get_model_confidence(self) -> float:
        """Get overall model confidence based on training"""
        if not self.feature_importance:
            return 0.5
        
        # Model confidence based on feature importance distribution
        importance_values = list(self.feature_importance.values())
        if not importance_values:
            return 0.5
        
        # Higher confidence when features have clear importance differences
        importance_std = statistics.stdev(importance_values) if len(importance_values) > 1 else 0.0
        model_confidence = min(1.0, importance_std * 2)
        
        return max(0.3, model_confidence)
    
    def _calculate_accuracy(self, predictions: List[str], actuals: List[str]) -> float:
        """Calculate prediction accuracy"""
        if not predictions or not actuals or len(predictions) != len(actuals):
            return 0.0
        
        correct = sum(1 for pred, actual in zip(predictions, actuals) if pred == actual)
        return correct / len(predictions)
    
    def _calculate_precision(self, predictions: List[str], actuals: List[str]) -> float:
        """Calculate precision for positive class (ACCEPT)"""
        if not predictions or not actuals:
            return 0.0
        
        true_positives = sum(1 for pred, actual in zip(predictions, actuals) if pred == "ACCEPT" and actual == "ACCEPT")
        false_positives = sum(1 for pred, actual in zip(predictions, actuals) if pred == "ACCEPT" and actual != "ACCEPT")
        
        if true_positives + false_positives == 0:
            return 0.0
        
        return true_positives / (true_positives + false_positives)
    
    def _calculate_recall(self, predictions: List[str], actuals: List[str]) -> float:
        """Calculate recall for positive class (ACCEPT)"""
        if not predictions or not actuals:
            return 0.0
        
        true_positives = sum(1 for pred, actual in zip(predictions, actuals) if pred == "ACCEPT" and actual == "ACCEPT")
        false_negatives = sum(1 for pred, actual in zip(predictions, actuals) if pred != "ACCEPT" and actual == "ACCEPT")
        
        if true_positives + false_negatives == 0:
            return 0.0
        
        return true_positives / (true_positives + false_negatives)
    
    def _calculate_f1_score(self, precision: float, recall: float) -> float:
        """Calculate F1 score"""
        if precision + recall == 0:
            return 0.0
        
        return 2 * (precision * recall) / (precision + recall)
    
    def _calculate_confidence_calibration(self, confidences: List[float], predictions: List[str], actuals: List[str]) -> float:
        """Calculate confidence calibration"""
        if not confidences or not predictions or not actuals:
            return 0.0
        
        # Simple calibration: correlation between confidence and correctness
        correct_confidences = []
        incorrect_confidences = []
        
        for conf, pred, actual in zip(confidences, predictions, actuals):
            if pred == actual:
                correct_confidences.append(conf)
            else:
                incorrect_confidences.append(conf)
        
        if not correct_confidences or not incorrect_confidences:
            return 0.5
        
        avg_correct_conf = statistics.mean(correct_confidences)
        avg_incorrect_conf = statistics.mean(incorrect_confidences)
        
        # Better calibration when correct predictions have higher confidence
        calibration_score = max(0.0, avg_correct_conf - avg_incorrect_conf)
        
        return min(1.0, calibration_score + 0.5)  # Scale to 0-1


class ReinforcementLearningAlgorithm(LearningAlgorithm):
    """Reinforcement learning from rewards and penalties"""
    
    def __init__(self):
        self.q_table = {}  # State-action value table
        self.learning_rate = 0.1
        self.discount_factor = 0.9
        self.exploration_rate = 0.1
        self.reward_history = []
        
    def learn(self, examples: List[LearningExample]) -> Dict[str, Any]:
        """Learn using reinforcement learning"""
        
        if not examples:
            return {"model_updated": False, "reason": "No examples provided"}
        
        total_reward = 0.0
        states_updated = 0
        
        for example in examples:
            # Extract state and action
            state = self._extract_state(example.input_data)
            action = self._extract_action(example.prediction)
            reward = self._calculate_reward(example)
            
            # Update Q-table
            old_value = self.q_table.get((state, action), 0.0)
            new_value = old_value + self.learning_rate * (reward - old_value)
            self.q_table[(state, action)] = new_value
            
            total_reward += reward
            states_updated += 1
        
        # Update exploration rate
        self._update_exploration_rate()
        
        # Store reward history
        self.reward_history.append(total_reward / len(examples))
        
        return {
            "model_updated": True,
            "states_updated": states_updated,
            "average_reward": total_reward / len(examples),
            "learning_rate": self.learning_rate,
            "exploration_rate": self.exploration_rate
        }
    
    def predict(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Make prediction using Q-values"""
        
        state = self._extract_state(input_data)
        
        # Get Q-values for all possible actions
        possible_actions = ["ACCEPT", "REFER", "DECLINE"]
        q_values = {}
        
        for action in possible_actions:
            q_values[action] = self.q_table.get((state, action), 0.0)
        
        # Select action (epsilon-greedy)
        import random
        if random.random() < self.exploration_rate:
            # Explore: random action
            selected_action = random.choice(possible_actions)
            exploration = True
        else:
            # Exploit: best action
            selected_action = max(q_values, key=q_values.get)
            exploration = False
        
        # Calculate confidence based on Q-value advantage
        max_q = max(q_values.values())
        min_q = min(q_values.values())
        confidence = (max_q - min_q) / (max_q - min_q + 1.0)  # Normalized confidence
        
        return {
            "prediction": selected_action,
            "q_values": q_values,
            "confidence": confidence,
            "exploration": exploration,
            "state": state
        }
    
    def evaluate(self, examples: List[LearningExample]) -> PerformanceMetrics:
        """Evaluate reinforcement learning performance"""
        
        if not examples:
            return PerformanceMetrics()
        
        predictions = []
        actuals = []
        confidences = []
        total_reward = 0.0
        
        for example in examples:
            prediction = self.predict(example.input_data)
            predictions.append(prediction["prediction"])
            actuals.append(example.actual_outcome.get("decision", "UNKNOWN"))
            confidences.append(prediction["confidence"])
            
            reward = self._calculate_reward(example)
            total_reward += reward
        
        # Calculate metrics
        accuracy = self._calculate_accuracy(predictions, actuals)
        
        # RL-specific metrics
        average_reward = total_reward / len(examples)
        learning_stability = self._calculate_learning_stability()
        
        return PerformanceMetrics(
            accuracy=accuracy,
            precision=0.7,  # Mock values
            recall=0.7,
            f1_score=0.7,
            confidence_calibration=statistics.mean(confidences) if confidences else 0.5,
            processing_efficiency=0.8,
            adaptation_rate=self.learning_rate
        )
    
    def _extract_state(self, input_data: Dict[str, Any]) -> str:
        """Extract state representation from input"""
        
        # Discretize continuous features for state representation
        state_parts = []
        
        # Coverage amount ranges
        coverage = input_data.get("coverage_amount", 0)
        if coverage < 200000:
            state_parts.append("low_coverage")
        elif coverage < 500000:
            state_parts.append("medium_coverage")
        else:
            state_parts.append("high_coverage")
        
        # Property age
        year = input_data.get("construction_year", 2000)
        age = 2024 - year
        if age < 10:
            state_parts.append("new_property")
        elif age < 30:
            state_parts.append("mid_property")
        else:
            state_parts.append("old_property")
        
        # State
        state = input_data.get("state", "Unknown")
        state_parts.append(f"state_{state}")
        
        # Property type
        property_type = input_data.get("property_type", "Unknown")
        state_parts.append(f"type_{property_type}")
        
        return "_".join(state_parts)
    
    def _extract_action(self, prediction: Dict[str, Any]) -> str:
        """Extract action from prediction"""
        return prediction.get("prediction", "REFER")
    
    def _calculate_reward(self, example: LearningExample) -> float:
        """Calculate reward for learning example"""
        
        predicted_decision = example.prediction.get("prediction", "REFER")
        actual_decision = example.actual_outcome.get("decision", "REFER")
        
        # Base reward for correct prediction
        if predicted_decision == actual_decision:
            base_reward = 1.0
        else:
            base_reward = -1.0
        
        # Adjust based on confidence
        confidence = example.prediction.get("confidence", 0.5)
        confidence_bonus = confidence if base_reward > 0 else -confidence
        
        # Adjust based on feedback
        feedback_bonus = 0.0
        if example.feedback_type == FeedbackType.EXPLICIT:
            feedback_score = example.feedback.get("score", 0.0)
            feedback_bonus = feedback_score * 0.5
        
        total_reward = base_reward + confidence_bonus + feedback_bonus
        
        return max(-2.0, min(2.0, total_reward))  # Clamp reward
    
    def _update_exploration_rate(self):
        """Update exploration rate (decay over time)"""
        self.exploration_rate *= 0.995  # Decay factor
        self.exploration_rate = max(0.01, self.exploration_rate)  # Minimum exploration
    
    def _calculate_learning_stability(self) -> float:
        """Calculate learning stability from reward history"""
        if len(self.reward_history) < 10:
            return 0.5
        
        # Calculate variance in recent rewards
        recent_rewards = self.reward_history[-10:]
        if len(recent_rewards) < 2:
            return 0.5
        
        reward_variance = statistics.variance(recent_rewards)
        stability = max(0.0, 1.0 - reward_variance)  # Lower variance = higher stability
        
        return stability
    
    def _calculate_accuracy(self, predictions: List[str], actuals: List[str]) -> float:
        """Calculate prediction accuracy"""
        if not predictions or not actuals or len(predictions) != len(actuals):
            return 0.0
        
        correct = sum(1 for pred, actual in zip(predictions, actuals) if pred == actual)
        return correct / len(predictions)


class PatternRecognitionSystem:
    """System for recognizing and learning patterns"""
    
    def __init__(self):
        self.patterns: List[LearningPattern] = []
        self.pattern_frequency = {}
        self.pattern_confidence = {}
        
    def discover_patterns(self, examples: List[LearningExample]) -> List[LearningPattern]:
        """Discover patterns from learning examples"""
        
        new_patterns = []
        
        # Pattern 1: High coverage + old property = REFER
        high_coverage_old_property = self._discover_high_coverage_old_property_pattern(examples)
        if high_coverage_old_property:
            new_patterns.append(high_coverage_old_property)
        
        # Pattern 2: California + high wildfire risk = enhanced review
        california_wildfire = self._discover_california_wildfire_pattern(examples)
        if california_wildfire:
            new_patterns.append(california_wildfire)
        
        # Pattern 3: Missing roof information = REFER
        missing_roof_info = self._discover_missing_roof_pattern(examples)
        if missing_roof_info:
            new_patterns.append(missing_roof_info)
        
        # Update pattern storage
        for pattern in new_patterns:
            self._update_pattern_storage(pattern)
        
        return new_patterns
    
    def _discover_high_coverage_old_property_pattern(self, examples: List[LearningExample]) -> Optional[LearningPattern]:
        """Discover pattern for high coverage + old property"""
        
        matching_examples = []
        
        for example in examples:
            input_data = example.input_data
            coverage = input_data.get("coverage_amount", 0)
            year = input_data.get("construction_year", 2024)
            age = 2024 - year
            actual_decision = example.actual_outcome.get("decision", "")
            
            if coverage > 500000 and age > 30 and actual_decision == "REFER":
                matching_examples.append(example)
        
        if len(matching_examples) >= 3:  # Minimum pattern threshold
            return LearningPattern(
                pattern_id=str(uuid.uuid4()),
                pattern_type="risk_correlation",
                description="High coverage + old property frequently results in REFER",
                confidence=len(matching_examples) / len(examples),
                frequency=len(matching_examples),
                last_observed=datetime.now(),
                predictive_power=0.8,
                action_recommendations=[
                    "Enhanced risk assessment for old properties with high coverage",
                    "Consider additional documentation requirements",
                    "Manual review recommended"
                ]
            )
        
        return None
    
    def _discover_california_wildfire_pattern(self, examples: List[LearningExample]) -> Optional[LearningPattern]:
        """Discover pattern for California wildfire risk"""
        
        matching_examples = []
        
        for example in examples:
            input_data = example.input_data
            state = input_data.get("state", "")
            hazard_scores = input_data.get("hazard_scores", {})
            wildfire_risk = hazard_scores.get("wildfire_risk", 0.0)
            actual_decision = example.actual_outcome.get("decision", "")
            
            if state == "CA" and wildfire_risk > 0.5 and actual_decision in ["REFER", "DECLINE"]:
                matching_examples.append(example)
        
        if len(matching_examples) >= 3:
            return LearningPattern(
                pattern_id=str(uuid.uuid4()),
                pattern_type="geographic_risk",
                description="California properties with high wildfire risk frequently result in REFER/DECLINE",
                confidence=len(matching_examples) / len(examples),
                frequency=len(matching_examples),
                last_observed=datetime.now(),
                predictive_power=0.9,
                action_recommendations=[
                    "Mandatory wildfire risk assessment for CA properties",
                    "Require mitigation documentation",
                    "Consider location-based underwriting guidelines"
                ]
            )
        
        return None
    
    def _discover_missing_roof_pattern(self, examples: List[LearningExample]) -> Optional[LearningPattern]:
        """Discover pattern for missing roof information"""
        
        matching_examples = []
        
        for example in examples:
            input_data = example.input_data
            roof_age = input_data.get("roof_age")
            roof_material = input_data.get("roof_material")
            actual_decision = example.actual_outcome.get("decision", "")
            
            if (roof_age is None or roof_material is None) and actual_decision == "REFER":
                matching_examples.append(example)
        
        if len(matching_examples) >= 3:
            return LearningPattern(
                pattern_id=str(uuid.uuid4()),
                pattern_type="data_completeness",
                description="Missing roof information frequently results in REFER",
                confidence=len(matching_examples) / len(examples),
                frequency=len(matching_examples),
                last_observed=datetime.now(),
                predictive_power=0.7,
                action_recommendations=[
                    "Require roof information for complete assessment",
                    "Generate specific questions for missing roof data",
                    "Consider conditional underwriting with roof assumptions"
                ]
            )
        
        return None
    
    def _update_pattern_storage(self, pattern: LearningPattern):
        """Update pattern storage with new pattern"""
        
        # Check if pattern already exists
        existing_pattern = None
        for existing in self.patterns:
            if existing.description == pattern.description:
                existing_pattern = existing
                break
        
        if existing_pattern:
            # Update existing pattern
            existing_pattern.frequency += pattern.frequency
            existing_pattern.confidence = (existing_pattern.confidence + pattern.confidence) / 2
            existing_pattern.last_observed = pattern.last_observed
            existing_pattern.predictive_power = (existing_pattern.predictive_power + pattern.predictive_power) / 2
        else:
            # Add new pattern
            self.patterns.append(pattern)
        
        # Update frequency tracking
        pattern_key = pattern.description
        self.pattern_frequency[pattern_key] = self.pattern_frequency.get(pattern_key, 0) + pattern.frequency
        self.pattern_confidence[pattern_key] = pattern.confidence
    
    def get_applicable_patterns(self, input_data: Dict[str, Any]) -> List[LearningPattern]:
        """Get patterns applicable to current input"""
        
        applicable_patterns = []
        
        for pattern in self.patterns:
            if self._is_pattern_applicable(pattern, input_data):
                applicable_patterns.append(pattern)
        
        # Sort by predictive power
        applicable_patterns.sort(key=lambda p: p.predictive_power, reverse=True)
        
        return applicable_patterns
    
    def _is_pattern_applicable(self, pattern: LearningPattern, input_data: Dict[str, Any]) -> bool:
        """Check if pattern is applicable to input data"""
        
        if pattern.pattern_type == "risk_correlation":
            coverage = input_data.get("coverage_amount", 0)
            year = input_data.get("construction_year", 2024)
            age = 2024 - year
            return coverage > 500000 and age > 30
        
        elif pattern.pattern_type == "geographic_risk":
            state = input_data.get("state", "")
            hazard_scores = input_data.get("hazard_scores", {})
            wildfire_risk = hazard_scores.get("wildfire_risk", 0.0)
            return state == "CA" and wildfire_risk > 0.5
        
        elif pattern.pattern_type == "data_completeness":
            roof_age = input_data.get("roof_age")
            roof_material = input_data.get("roof_material")
            return roof_age is None or roof_material is None
        
        return False


class AdaptiveLearningSystem:
    """Main adaptive learning system that orchestrates all learning components"""
    
    def __init__(self):
        """Initialize adaptive learning system"""
        self.supervised_learner = SupervisedLearningAlgorithm()
        self.reinforcement_learner = ReinforcementLearningAlgorithm()
        self.pattern_recognition = PatternRecognitionSystem()
        
        # Learning history
        self.learning_examples: List[LearningExample] = []
        self.adaptation_history: List[AdaptationRecord] = []
        self.performance_history: List[PerformanceMetrics] = []
        
        # Configuration
        self.adaptation_strategy = AdaptationStrategy.BALANCED
        self.learning_threshold = 5  # Minimum examples for learning
        self.performance_window = 50  # Examples for performance evaluation
        
        logger.info("Adaptive Learning System initialized with multiple learning algorithms")
    
    def add_learning_example(
        self,
        input_data: Dict[str, Any],
        prediction: Dict[str, Any],
        actual_outcome: Dict[str, Any],
        feedback: Dict[str, Any],
        feedback_type: FeedbackType = FeedbackType.IMPLICIT
    ) -> str:
        """Add a learning example to the system"""
        
        example = LearningExample(
            example_id=str(uuid.uuid4()),
            input_data=input_data,
            prediction=prediction,
            actual_outcome=actual_outcome,
            feedback=feedback,
            feedback_type=feedback_type,
            confidence=prediction.get("confidence", 0.5),
            timestamp=datetime.now()
        )
        
        # Calculate learning value
        example.learning_value = self._calculate_learning_value(example)
        
        self.learning_examples.append(example)
        
        logger.info(f"Added learning example: {example.example_id} with learning value {example.learning_value:.3f}")
        
        return example.example_id
    
    def learn_and_adapt(self) -> Dict[str, Any]:
        """Perform learning and adaptation based on accumulated examples"""
        
        if len(self.learning_examples) < self.learning_threshold:
            return {"status": "insufficient_examples", "examples_needed": self.learning_threshold}
        
        logger.info(f"Starting adaptive learning with {len(self.learning_examples)} examples")
        
        adaptation_results = {}
        
        # Supervised learning
        recent_examples = self.learning_examples[-self.performance_window:]
        supervised_result = self.supervised_learner.learn(recent_examples)
        adaptation_results["supervised_learning"] = supervised_result
        
        # Reinforcement learning
        reinforcement_result = self.reinforcement_learner.learn(recent_examples)
        adaptation_results["reinforcement_learning"] = reinforcement_result
        
        # Pattern recognition
        new_patterns = self.pattern_recognition.discover_patterns(recent_examples)
        adaptation_results["pattern_recognition"] = {
            "new_patterns_discovered": len(new_patterns),
            "patterns": [p.description for p in new_patterns]
        }
        
        # Create adaptation record
        adaptation_record = AdaptationRecord(
            adaptation_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            adaptation_type="comprehensive_learning",
            trigger="scheduled_adaptation",
            old_behavior={"performance": self._get_current_performance()},
            new_behavior={"learning_results": adaptation_results},
            expected_improvement=0.1
        )
        self.adaptation_history.append(adaptation_record)
        
        # Evaluate performance after adaptation
        new_performance = self.evaluate_performance()
        self.performance_history.append(new_performance)
        
        # Calculate actual improvement
        if len(self.performance_history) >= 2:
            old_performance = self.performance_history[-2]
            actual_improvement = new_performance.accuracy - old_performance.accuracy
            adaptation_record.actual_improvement = actual_improvement
            adaptation_record.success = actual_improvement > 0
        
        logger.info(f"Adaptive learning completed: {adaptation_results}")
        
        return {
            "status": "completed",
            "adaptation_id": adaptation_record.adaptation_id,
            "results": adaptation_results,
            "performance_improvement": adaptation_record.actual_improvement
        }
    
    def make_adaptive_prediction(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Make prediction using adaptive learning"""
        
        # Get applicable patterns
        applicable_patterns = self.pattern_recognition.get_applicable_patterns(input_data)
        
        # Get predictions from both learners
        supervised_prediction = self.supervised_learner.predict(input_data)
        reinforcement_prediction = self.reinforcement_learner.predict(input_data)
        
        # Ensemble prediction with pattern influence
        ensemble_prediction = self._ensemble_predictions(
            supervised_prediction, 
            reinforcement_prediction, 
            applicable_patterns
        )
        
        # Add pattern-based recommendations
        pattern_recommendations = [p.action_recommendations for p in applicable_patterns]
        
        return {
            "prediction": ensemble_prediction["decision"],
            "confidence": ensemble_prediction["confidence"],
            "reasoning": {
                "supervised_contribution": supervised_prediction["confidence"],
                "reinforcement_contribution": reinforcement_prediction["confidence"],
                "pattern_influence": len(applicable_patterns),
                "applicable_patterns": [p.description for p in applicable_patterns],
                "pattern_recommendations": pattern_recommendations
            },
            "adaptive_features": {
                "learning_examples_used": len(self.learning_examples),
                "adaptations_performed": len(self.adaptation_history),
                "current_performance": self._get_current_performance()
            }
        }
    
    def evaluate_performance(self) -> PerformanceMetrics:
        """Evaluate current system performance"""
        
        if len(self.learning_examples) < 10:
            return PerformanceMetrics()
        
        recent_examples = self.learning_examples[-self.performance_window:]
        
        # Evaluate supervised learner
        supervised_metrics = self.supervised_learner.evaluate(recent_examples)
        
        # Evaluate reinforcement learner
        reinforcement_metrics = self.reinforcement_learner.evaluate(recent_examples)
        
        # Combine metrics
        combined_metrics = PerformanceMetrics(
            accuracy=(supervised_metrics.accuracy + reinforcement_metrics.accuracy) / 2,
            precision=(supervised_metrics.precision + reinforcement_metrics.precision) / 2,
            recall=(supervised_metrics.recall + reinforcement_metrics.recall) / 2,
            f1_score=(supervised_metrics.f1_score + reinforcement_metrics.f1_score) / 2,
            confidence_calibration=(supervised_metrics.confidence_calibration + reinforcement_metrics.confidence_calibration) / 2,
            processing_efficiency=0.8,
            adaptation_rate=len(self.adaptation_history) / max(1, len(self.learning_examples))
        )
        
        return combined_metrics
    
    def _calculate_learning_value(self, example: LearningExample) -> float:
        """Calculate learning value of an example"""
        
        base_value = 0.5
        
        # Adjust based on prediction accuracy
        predicted = example.prediction.get("prediction", "")
        actual = example.actual_outcome.get("decision", "")
        accuracy_bonus = 1.0 if predicted == actual else 0.0
        
        # Adjust based on feedback type
        feedback_multipliers = {
            FeedbackType.EXPLICIT: 1.5,
            FeedbackType.PERFORMANCE: 1.2,
            FeedbackType.DOMAIN: 1.3,
            FeedbackType.IMPLICIT: 1.0
        }
        feedback_multiplier = feedback_multipliers.get(example.feedback_type, 1.0)
        
        # Adjust based on confidence
        confidence_factor = example.confidence
        
        # Calculate final learning value
        learning_value = base_value + (accuracy_bonus * 0.3) + (confidence_factor * 0.2)
        learning_value *= feedback_multiplier
        
        return max(0.1, min(1.0, learning_value))
    
    def _ensemble_predictions(
        self,
        supervised: Dict[str, Any],
        reinforcement: Dict[str, Any],
        patterns: List[LearningPattern]
    ) -> Dict[str, Any]:
        """Ensemble predictions from multiple sources"""
        
        # Weight predictions by confidence
        supervised_weight = supervised["confidence"]
        reinforcement_weight = reinforcement["confidence"]
        pattern_weight = len(patterns) * 0.1  # Pattern influence
        
        total_weight = supervised_weight + reinforcement_weight + pattern_weight
        
        if total_weight == 0:
            return {"decision": "REFER", "confidence": 0.5}
        
        # Weighted voting
        decisions = {"ACCEPT": 0, "REFER": 0, "DECLINE": 0}
        
        decisions[supervised["prediction"]] += supervised_weight
        decisions[reinforcement["prediction"]] += reinforcement_weight
        
        # Add pattern influence
        for pattern in patterns:
            # Patterns typically suggest REFER for risk mitigation
            decisions["REFER"] += pattern_weight * pattern.predictive_power
        
        # Select decision with highest weighted score
        best_decision = max(decisions, key=decisions.get)
        
        # Calculate ensemble confidence
        ensemble_confidence = decisions[best_decision] / total_weight
        
        return {"decision": best_decision, "confidence": ensemble_confidence}
    
    def _get_current_performance(self) -> Dict[str, float]:
        """Get current performance metrics"""
        
        if not self.performance_history:
            return {"accuracy": 0.0, "confidence": 0.0}
        
        latest_performance = self.performance_history[-1]
        return {
            "accuracy": latest_performance.accuracy,
            "precision": latest_performance.precision,
            "recall": latest_performance.recall,
            "f1_score": latest_performance.f1_score,
            "confidence": latest_performance.confidence_calibration
        }
    
    def get_learning_summary(self) -> Dict[str, Any]:
        """Get comprehensive learning summary"""
        
        return {
            "learning_statistics": {
                "total_examples": len(self.learning_examples),
                "adaptations_performed": len(self.adaptation_history),
                "patterns_discovered": len(self.pattern_recognition.patterns),
                "average_learning_value": sum(e.learning_value for e in self.learning_examples) / len(self.learning_examples) if self.learning_examples else 0.0
            },
            "current_performance": self._get_current_performance(),
            "recent_adaptations": [
                {
                    "adaptation_id": record.adaptation_id,
                    "timestamp": record.timestamp.isoformat(),
                    "type": record.adaptation_type,
                    "improvement": record.actual_improvement
                }
                for record in self.adaptation_history[-5:]
            ],
            "active_patterns": [
                {
                    "description": pattern.description,
                    "confidence": pattern.confidence,
                    "frequency": pattern.frequency,
                    "predictive_power": pattern.predictive_power
                }
                for pattern in self.pattern_recognition.patterns
            ],
            "learning_effectiveness": {
                "accuracy_trend": self._calculate_accuracy_trend(),
                "adaptation_success_rate": sum(1 for record in self.adaptation_history if record.success) / len(self.adaptation_history) if self.adaptation_history else 0.0,
                "pattern_utilization_rate": len(self.pattern_recognition.patterns) / max(1, len(self.learning_examples))
            }
        }
    
    def _calculate_accuracy_trend(self) -> float:
        """Calculate accuracy trend over time"""
        
        if len(self.performance_history) < 5:
            return 0.0
        
        # Calculate trend using linear regression on recent accuracy
        recent_performances = self.performance_history[-10:]
        accuracies = [p.accuracy for p in recent_performances]
        
        # Simple trend calculation
        if len(accuracies) >= 2:
            recent_avg = statistics.mean(accuracies[-3:])
            older_avg = statistics.mean(accuracies[:3])
            trend = recent_avg - older_avg
            return trend
        
        return 0.0


# Global adaptive learning system instance
_global_adaptive_learning_system: Optional[AdaptiveLearningSystem] = None


def get_adaptive_learning_system() -> AdaptiveLearningSystem:
    """Get global adaptive learning system instance"""
    global _global_adaptive_learning_system
    if _global_adaptive_learning_system is None:
        _global_adaptive_learning_system = AdaptiveLearningSystem()
    return _global_adaptive_learning_system
