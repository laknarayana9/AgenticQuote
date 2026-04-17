"""
Predictive Analytics
Provides predictive insights for risk assessment and decision-making.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

logger = logging.getLogger(__name__)


class PredictiveModel:
    """Simple predictive model for risk assessment."""
    
    def __init__(self):
        """Initialize predictive model."""
        self.features = {}
        self.trained = False
    
    def train(self, training_data: List[Dict[str, Any]]):
        """Train the model on historical data."""
        if not training_data:
            return
        
        # Simple feature extraction (mean values)
        for record in training_data:
            for key, value in record.items():
                if isinstance(value, (int, float)):
                    if key not in self.features:
                        self.features[key] = []
                    self.features[key].append(value)
        
        # Calculate means
        for key in self.features:
            self.features[key] = statistics.mean(self.features[key])
        
        self.trained = True
        logger.info(f"Predictive model trained on {len(training_data)} records")
    
    def predict(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Make a prediction based on features."""
        if not self.trained:
            return {
                "prediction": None,
                "confidence": 0.0,
                "reason": "Model not trained"
            }
        
        # Simple prediction based on feature similarity
        score = 0.0
        for key, value in features.items():
            if isinstance(value, (int, float)) and key in self.features:
                # Normalize and add to score
                normalized = min(value / self.features[key], 2.0)
                score += normalized
        
        score = score / len(features) if features else 0
        
        return {
            "prediction": "high_risk" if score > 1.0 else "low_risk",
            "confidence": min(score / 2, 1.0),
            "risk_score": score
        }


class PredictiveAnalytics:
    """
    Predictive analytics for risk assessment and decision-making.
    
    Provides predictive insights based on historical patterns.
    """
    
    def __init__(self):
        """Initialize predictive analytics."""
        self.enabled = os.getenv("PREDICTIVE_ANALYTICS_ENABLED", "false").lower() == "true"
        
        # Predictive models
        self.risk_model = PredictiveModel()
        self.decision_model = PredictiveModel()
        
        # Historical data
        self.historical_decisions = []
        self.historical_risks = []
        
        logger.info(f"Predictive analytics initialized (enabled={self.enabled})")
    
    def record_decision(self, case_data: Dict[str, Any], decision: str):
        """
        Record a decision for training predictive models.
        
        Args:
            case_data: Case data
            decision: Decision made
        """
        if not self.enabled:
            return
        
        record = {
            **case_data,
            "decision": 1 if decision == "accept" else 0,
            "timestamp": datetime.now()
        }
        
        self.historical_decisions.append(record)
        
        # Re-train periodically
        if len(self.historical_decisions) % 100 == 0:
            self._train_models()
    
    def record_risk(self, risk_factors: Dict[str, Any], actual_loss: float):
        """
        Record risk data for training.
        
        Args:
            risk_factors: Risk factors
            actual_loss: Actual loss amount
        """
        if not self.enabled:
            return
        
        record = {
            **risk_factors,
            "actual_loss": actual_loss,
            "timestamp": datetime.now()
        }
        
        self.historical_risks.append(record)
    
    def predict_decision(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict the likely decision for a case.
        
        Args:
            case_data: Case data
            
        Returns:
            Prediction result
        """
        if not self.enabled:
            return {
                "predictive_analytics_enabled": False,
                "prediction": None,
                "reason": "Predictive analytics disabled"
            }
        
        if not self.decision_model.trained:
            return {
                "predictive_analytics_enabled": True,
                "prediction": None,
                "reason": "Model not trained yet"
            }
        
        # Extract numeric features
        features = {}
        for key, value in case_data.items():
            if isinstance(value, (int, float)):
                features[key] = value
        
        prediction = self.decision_model.predict(features)
        
        return {
            "predictive_analytics_enabled": True,
            "prediction": prediction["prediction"],
            "confidence": prediction["confidence"],
            "risk_score": prediction.get("risk_score", 0)
        }
    
    def predict_loss(self, risk_factors: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict potential loss based on risk factors.
        
        Args:
            risk_factors: Risk factors
            
        Returns:
            Loss prediction
        """
        if not self.enabled:
            return {
                "predictive_analytics_enabled": False,
                "predicted_loss": None,
                "reason": "Predictive analytics disabled"
            }
        
        if not self.risk_model.trained:
            return {
                "predictive_analytics_enabled": True,
                "predicted_loss": None,
                "reason": "Risk model not trained yet"
            }
        
        prediction = self.risk_model.predict(risk_factors)
        
        return {
            "predictive_analytics_enabled": True,
            "predicted_loss": prediction.get("risk_score", 0) * 10000,  # Scale to dollars
            "confidence": prediction["confidence"]
        }
    
    def get_anomaly_detection(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Detect anomalies in recent decisions.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of anomalies
        """
        if not self.enabled:
            return []
        
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_decisions = [
            d for d in self.historical_decisions
            if d["timestamp"] >= cutoff
        ]
        
        if len(recent_decisions) < 10:
            return []
        
        anomalies = []
        
        # Check for decision anomalies
        decisions = [d["decision"] for d in recent_decisions]
        if statistics.stdev(decisions) > 0.4:  # High variance
            anomalies.append({
                "type": "high_decision_variance",
                "std_dev": statistics.stdev(decisions),
                "timestamp": datetime.now().isoformat()
            })
        
        return anomalies
    
    def _train_models(self):
        """Train predictive models on historical data."""
        if len(self.historical_decisions) > 50:
            self.decision_model.train(self.historical_decisions)
        
        if len(self.historical_risks) > 50:
            self.risk_model.train(self.historical_risks)
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get predictive analytics summary.
        
        Returns:
            Summary data
        """
        if not self.enabled:
            return {"enabled": False}
        
        return {
            "enabled": True,
            "historical_decisions": len(self.historical_decisions),
            "historical_risks": len(self.historical_risks),
            "decision_model_trained": self.decision_model.trained,
            "risk_model_trained": self.risk_model.trained
        }


# Global predictive analytics instance
_global_predictive_analytics: Optional[PredictiveAnalytics] = None


def get_predictive_analytics() -> PredictiveAnalytics:
    """
    Get global predictive analytics instance (singleton pattern).
    
    Returns:
        PredictiveAnalytics instance
    """
    global _global_predictive_analytics
    if _global_predictive_analytics is None:
        _global_predictive_analytics = PredictiveAnalytics()
    return _global_predictive_analytics
