"""
HITL Workflow Automation
Automates HITL tasks for low-risk cases with configurable rules.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class AutomationRule:
    """Automation rule for HITL tasks."""
    
    def __init__(
        self,
        rule_id: str,
        name: str,
        conditions: Dict[str, Any],
        action: str,
        confidence_threshold: float = 0.9
    ):
        self.rule_id = rule_id
        self.name = name
        self.conditions = conditions
        self.action = action
        self.confidence_threshold = confidence_threshold
        self.enabled = True
        self.execution_count = 0


class HITLAutomation:
    """
    HITL workflow automation for low-risk cases.
    
    Automatically approves or processes HITL tasks based on configurable rules.
    """
    
    def __init__(self):
        """Initialize HITL automation."""
        self.enabled = os.getenv("HITL_AUTO_APPROVE_ENABLED", "false").lower() == "true"
        self.approval_threshold = float(os.getenv("HITL_AUTO_APPROVE_THRESHOLD", "0.9"))
        
        # Automation rules
        self.rules = []
        
        # Load default rules
        self._load_default_rules()
        
        logger.info(f"HITL automation initialized (enabled={self.enabled}, threshold={self.approval_threshold})")
    
    def _load_default_rules(self):
        """Load default automation rules."""
        # Rule: Auto-approve low-risk cases with high confidence
        self.rules.append(AutomationRule(
            rule_id="auto_approve_low_risk",
            name="Auto-approve low-risk cases",
            conditions={
                "eligibility_score": {"min": 0.9},
                "confidence": {"min": 0.85},
                "risk_factors_count": {"max": 1}
            },
            action="approve",
            confidence_threshold=0.9
        ))
        
        # Rule: Auto-refer high-risk cases
        self.rules.append(AutomationRule(
            rule_id="auto_refer_high_risk",
            name="Auto-refer high-risk cases",
            conditions={
                "eligibility_score": {"max": 0.3},
                "risk_factors_count": {"min": 3}
            },
            action="refer",
            confidence_threshold=0.8
        ))
        
        # Rule: Auto-approve condos and townhouses
        self.rules.append(AutomationRule(
            rule_id="auto_approve_condos",
            name="Auto-approve condos and townhouses",
            conditions={
                "dwelling_type": ["condo", "townhouse"],
                "eligibility_score": {"min": 0.8}
            },
            action="approve",
            confidence_threshold=0.85
        ))
    
    def evaluate_task(
        self,
        task_data: Dict[str, Any],
        assessment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate if a HITL task can be automated.
        
        Args:
            task_data: Task data
            assessment: Assessment data
            
        Returns:
            Automation result
        """
        if not self.enabled:
            return {
                "automation_enabled": False,
                "can_automate": False,
                "reason": "Automation disabled"
            }
        
        # Check overall confidence threshold
        confidence = assessment.get("confidence", 0.5)
        if confidence < self.approval_threshold:
            return {
                "automation_enabled": True,
                "can_automate": False,
                "reason": f"Confidence {confidence} below threshold {self.approval_threshold}"
            }
        
        # Evaluate rules
        for rule in self.rules:
            if not rule.enabled:
                continue
            
            if self._evaluate_rule(rule, task_data, assessment):
                rule.execution_count += 1
                
                return {
                    "automation_enabled": True,
                    "can_automate": True,
                    "action": rule.action,
                    "rule_id": rule.rule_id,
                    "rule_name": rule.name,
                    "reason": f"Rule '{rule.name}' matched"
                }
        
        return {
            "automation_enabled": True,
            "can_automate": False,
            "reason": "No automation rules matched"
        }
    
    def _evaluate_rule(
        self,
        rule: AutomationRule,
        task_data: Dict[str, Any],
        assessment: Dict[str, Any]
    ) -> bool:
        """
        Evaluate if a rule matches.
        
        Args:
            rule: Automation rule
            task_data: Task data
            assessment: Assessment data
            
        Returns:
            True if rule matches
        """
        conditions = rule.conditions
        all_match = True
        
        # Check eligibility score
        if "eligibility_score" in conditions:
            score = assessment.get("eligibility_score", 0)
            if "min" in conditions["eligibility_score"] and score < conditions["eligibility_score"]["min"]:
                all_match = False
            if "max" in conditions["eligibility_score"] and score > conditions["eligibility_score"]["max"]:
                all_match = False
        
        # Check confidence
        if "confidence" in conditions and all_match:
            conf = assessment.get("confidence", 0)
            if "min" in conditions["confidence"] and conf < conditions["confidence"]["min"]:
                all_match = False
        
        # Check risk factors count
        if "risk_factors_count" in conditions and all_match:
            count = len(assessment.get("risk_factors", []))
            if "min" in conditions["risk_factors_count"] and count < conditions["risk_factors_count"]["min"]:
                all_match = False
            if "max" in conditions["risk_factors_count"] and count > conditions["risk_factors_count"]["max"]:
                all_match = False
        
        # Check dwelling type
        if "dwelling_type" in conditions and all_match:
            property_profile = task_data.get("property_profile", {})
            dwelling_type = property_profile.get("dwelling_type", "")
            if dwelling_type not in conditions["dwelling_type"]:
                all_match = False
        
        return all_match
    
    def add_rule(
        self,
        rule_id: str,
        name: str,
        conditions: Dict[str, Any],
        action: str,
        confidence_threshold: float = 0.9
    ):
        """
        Add a custom automation rule.
        
        Args:
            rule_id: Unique rule identifier
            name: Rule name
            conditions: Rule conditions
            action: Action to take
            confidence_threshold: Confidence threshold
        """
        rule = AutomationRule(
            rule_id=rule_id,
            name=name,
            conditions=conditions,
            action=action,
            confidence_threshold=confidence_threshold
        )
        self.rules.append(rule)
        logger.info(f"Added automation rule: {rule_id}")
    
    def disable_rule(self, rule_id: str):
        """
        Disable an automation rule.
        
        Args:
            rule_id: Rule ID
        """
        for rule in self.rules:
            if rule.rule_id == rule_id:
                rule.enabled = False
                logger.info(f"Disabled automation rule: {rule_id}")
    
    def enable_rule(self, rule_id: str):
        """
        Enable an automation rule.
        
        Args:
            rule_id: Rule ID
        """
        for rule in self.rules:
            if rule.rule_id == rule_id:
                rule.enabled = True
                logger.info(f"Enabled automation rule: {rule_id}")
    
    def get_automation_stats(self) -> Dict[str, Any]:
        """
        Get automation statistics.
        
        Returns:
            Dictionary with automation statistics
        """
        if not self.enabled:
            return {"enabled": False}
        
        return {
            "enabled": True,
            "approval_threshold": self.approval_threshold,
            "total_rules": len(self.rules),
            "enabled_rules": sum(1 for r in self.rules if r.enabled),
            "rule_executions": {r.rule_id: r.execution_count for r in self.rules}
        }


# Global HITL automation instance
_global_automation: Optional[HITLAutomation] = None


def get_hitl_automation() -> HITLAutomation:
    """
    Get global HITL automation instance (singleton pattern).
    
    Returns:
        HITLAutomation instance
    """
    global _global_automation
    if _global_automation is None:
        _global_automation = HITLAutomation()
    return _global_automation
