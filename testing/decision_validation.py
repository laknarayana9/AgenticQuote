"""
Decision Validation
Validates decisions against business rules and guidelines.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ValidationRule(Enum):
    """Validation rule types."""
    ELIGIBILITY = "eligibility"
    RISK_THRESHOLD = "risk_threshold"
    CONFIDENCE_THRESHOLD = "confidence_threshold"
    DATA_COMPLETENESS = "data_completeness"
    COMPLIANCE = "compliance"


class ValidationResult:
    """Validation result."""
    
    def __init__(
        self,
        rule: str,
        passed: bool,
        message: str,
        details: Dict[str, Any] = None
    ):
        self.rule = rule
        self.passed = passed
        self.message = message
        self.details = details or {}


class DecisionValidator:
    """
    Decision validation system.
    
    Validates decisions against business rules and guidelines.
    """
    
    def __init__(self):
        """Initialize decision validator."""
        self.enabled = os.getenv("DECISION_VALIDATION_ENABLED", "false").lower() == "true"
        
        # Validation rules
        self.rules = {}
        
        # Validation history
        self.validation_history = []
        
        logger.info(f"Decision validator initialized (enabled={self.enabled})")
    
    def add_rule(
        self,
        rule_id: str,
        rule_type: str,
        check_func: callable,
        description: str
    ):
        """
        Add a validation rule.
        
        Args:
            rule_id: Rule ID
            rule_type: Rule type
            check_func: Function to check the rule
            description: Rule description
        """
        self.rules[rule_id] = {
            "rule_type": rule_type,
            "check_func": check_func,
            "description": description
        }
        logger.debug(f"Added validation rule: {rule_id}")
    
    def validate_decision(
        self,
        decision: str,
        case_data: Dict[str, Any],
        assessment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate a decision against all rules.
        
        Args:
            decision: Decision made
            case_data: Case data
            assessment: Assessment data
            
        Returns:
            Validation result
        """
        if not self.enabled:
            return {
                "decision_validation_enabled": False,
                "validation_passed": True,
                "reason": "Decision validation disabled"
            }
        
        results = []
        all_passed = True
        
        for rule_id, rule in self.rules.items():
            try:
                passed, message, details = rule["check_func"](
                    decision, case_data, assessment
                )
                result = ValidationResult(rule_id, passed, message, details)
                results.append(result)
                
                if not passed:
                    all_passed = False
                    
            except Exception as e:
                logger.error(f"Error running rule {rule_id}: {e}")
                result = ValidationResult(rule_id, False, f"Rule error: {e}")
                results.append(result)
                all_passed = False
        
        # Record validation
        self.validation_history.append({
            "decision": decision,
            "all_passed": all_passed,
            "results": [{"rule": r.rule, "passed": r.passed} for r in results],
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "decision_validation_enabled": True,
            "validation_passed": all_passed,
            "total_rules": len(results),
            "passed_rules": sum(1 for r in results if r.passed),
            "failed_rules": sum(1 for r in results if not r.passed),
            "results": [
                {
                    "rule": r.rule,
                    "passed": r.passed,
                    "message": r.message,
                    "details": r.details
                }
                for r in results
            ]
        }
    
    def get_validation_summary(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get validation summary for a time window.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Validation summary
        """
        if not self.enabled:
            return {"enabled": False}
        
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_validations = [
            v for v in self.validation_history
            if datetime.fromisoformat(v["timestamp"]) >= cutoff
        ]
        
        passed = sum(1 for v in recent_validations if v["all_passed"])
        total = len(recent_validations)
        
        return {
            "enabled": True,
            "time_window_hours": hours,
            "total_validations": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": passed / total if total > 0 else 0
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get validation summary.
        
        Returns:
            Summary data
        """
        if not self.enabled:
            return {"enabled": False}
        
        return {
            "enabled": True,
            "total_rules": len(self.rules),
            "total_validations": len(self.validation_history)
        }


# Global decision validator instance
_global_decision_validator: Optional[DecisionValidator] = None


def get_decision_validator() -> DecisionValidator:
    """
    Get global decision validator instance (singleton pattern).
    
    Returns:
        DecisionValidator instance
    """
    global _global_decision_validator
    if _global_decision_validator is None:
        _global_decision_validator = DecisionValidator()
    return _global_decision_validator
