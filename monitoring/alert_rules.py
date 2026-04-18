"""
Custom alert rules configuration for Phase D.2
Provides flexible alert rule management with dynamic thresholds and conditions.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from enum import Enum
import re

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertCondition(Enum):
    """Alert condition operators."""
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_THAN_OR_EQUAL = ">="
    LESS_THAN_OR_EQUAL = "<="
    EQUAL = "=="
    NOT_EQUAL = "!="
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    REGEX = "regex"


@dataclass
class AlertRule:
    """Alert rule configuration."""
    id: str
    name: str
    metric: str
    condition: str
    threshold: float
    duration: int = 60
    severity: str = "warning"
    enabled: bool = True
    message: str = ""
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            **asdict(self),
            "created_at": self.created_at.isoformat()
        }


class AlertRuleManager:
    """Manage custom alert rules."""
    
    def __init__(self):
        self.enabled = os.getenv("CUSTOM_ALERT_RULES_ENABLED", "false").lower() == "true"
        self.rules: Dict[str, AlertRule] = {}
        self.rule_history: List[Dict] = []
        self._load_default_rules()
        
        logger.info(f"Alert rule manager initialized (enabled={self.enabled})")
    
    def _load_default_rules(self) -> None:
        """Load default alert rules."""
        default_rules = [
            AlertRule(
                id="api_error_rate",
                name="API Error Rate",
                metric="error_rate",
                condition=">",
                threshold=5.0,
                duration=60,
                severity="critical",
                message="API error rate exceeded 5%"
            ),
            AlertRule(
                id="api_latency_p95",
                name="API Latency P95",
                metric="response_time_p95",
                condition=">",
                threshold=1000,
                duration=60,
                severity="warning",
                message="API latency P95 exceeded 1000ms"
            ),
            AlertRule(
                id="api_latency_p99",
                name="API Latency P99",
                metric="response_time_p99",
                condition=">",
                threshold=2000,
                duration=60,
                severity="error",
                message="API latency P99 exceeded 2000ms"
            ),
            AlertRule(
                id="success_rate",
                name="Success Rate",
                metric="success_rate",
                condition="<",
                threshold=95.0,
                duration=300,
                severity="critical",
                message="Success rate dropped below 95%"
            ),
            AlertRule(
                id="cpu_usage",
                name="CPU Usage",
                metric="cpu_usage",
                condition=">",
                threshold=80.0,
                duration=300,
                severity="warning",
                message="CPU usage exceeded 80%"
            ),
            AlertRule(
                id="memory_usage",
                name="Memory Usage",
                metric="memory_usage",
                condition=">",
                threshold=85.0,
                duration=300,
                severity="warning",
                message="Memory usage exceeded 85%"
            ),
            AlertRule(
                id="disk_usage",
                name="Disk Usage",
                metric="disk_usage",
                condition=">",
                threshold=90.0,
                duration=600,
                severity="critical",
                message="Disk usage exceeded 90%"
            ),
            AlertRule(
                id="database_connections",
                name="Database Connections",
                metric="db_connections",
                condition=">",
                threshold=80.0,
                duration=60,
                severity="warning",
                message="Database connection pool exhausted"
            ),
            AlertRule(
                id="cache_hit_rate",
                name="Cache Hit Rate",
                metric="cache_hit_rate",
                condition="<",
                threshold=80.0,
                duration=300,
                severity="warning",
                message="Cache hit rate dropped below 80%"
            ),
            AlertRule(
                id="provider_latency",
                name="Provider Latency",
                metric="provider_latency",
                condition=">",
                threshold=5000,
                duration=120,
                severity="error",
                message="External provider latency exceeded 5s"
            )
        ]
        
        for rule in default_rules:
            self.add_rule(rule)
    
    def add_rule(self, rule: AlertRule) -> None:
        """Add an alert rule."""
        self.rules[rule.id] = rule
        self.rule_history.append({
            "action": "add",
            "rule_id": rule.id,
            "timestamp": datetime.now().isoformat()
        })
        logger.info(f"Alert rule added: {rule.id}")
    
    def update_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing alert rule."""
        if rule_id not in self.rules:
            logger.warning(f"Rule not found: {rule_id}")
            return False
        
        rule = self.rules[rule_id]
        
        for key, value in updates.items():
            if hasattr(rule, key):
                setattr(rule, key, value)
        
        self.rule_history.append({
            "action": "update",
            "rule_id": rule_id,
            "updates": updates,
            "timestamp": datetime.now().isoformat()
        })
        logger.info(f"Alert rule updated: {rule_id}")
        return True
    
    def delete_rule(self, rule_id: str) -> bool:
        """Delete an alert rule."""
        if rule_id not in self.rules:
            logger.warning(f"Rule not found: {rule_id}")
            return False
        
        del self.rules[rule_id]
        self.rule_history.append({
            "action": "delete",
            "rule_id": rule_id,
            "timestamp": datetime.now().isoformat()
        })
        logger.info(f"Alert rule deleted: {rule_id}")
        return True
    
    def enable_rule(self, rule_id: str) -> bool:
        """Enable an alert rule."""
        return self.update_rule(rule_id, {"enabled": True})
    
    def disable_rule(self, rule_id: str) -> bool:
        """Disable an alert rule."""
        return self.update_rule(rule_id, {"enabled": False})
    
    def get_rule(self, rule_id: str) -> Optional[AlertRule]:
        """Get a specific alert rule."""
        return self.rules.get(rule_id)
    
    def get_all_rules(self, enabled_only: bool = False) -> List[AlertRule]:
        """Get all alert rules."""
        rules = list(self.rules.values())
        if enabled_only:
            rules = [r for r in rules if r.enabled]
        return rules
    
    def get_rules_by_metric(self, metric: str) -> List[AlertRule]:
        """Get rules for a specific metric."""
        return [r for r in self.rules.values() if r.metric == metric and r.enabled]
    
    def get_rules_by_severity(self, severity: str) -> List[AlertRule]:
        """Get rules by severity."""
        return [r for r in self.rules.values() if r.severity == severity and r.enabled]
    
    def evaluate_rule(self, rule: AlertRule, value: float) -> bool:
        """Evaluate an alert rule against a value."""
        if not rule.enabled:
            return False
        
        condition = AlertCondition(rule.condition)
        threshold = rule.threshold
        
        if condition == AlertCondition.GREATER_THAN:
            return value > threshold
        elif condition == AlertCondition.LESS_THAN:
            return value < threshold
        elif condition == AlertCondition.GREATER_THAN_OR_EQUAL:
            return value >= threshold
        elif condition == AlertCondition.LESS_THAN_OR_EQUAL:
            return value <= threshold
        elif condition == AlertCondition.EQUAL:
            return value == threshold
        elif condition == AlertCondition.NOT_EQUAL:
            return value != threshold
        else:
            logger.warning(f"Unsupported condition: {condition}")
            return False
    
    def validate_rule(self, rule: AlertRule) -> List[str]:
        """Validate an alert rule configuration."""
        errors = []
        
        # Validate ID
        if not rule.id or not re.match(r'^[a-zA-Z0-9_-]+$', rule.id):
            errors.append("Invalid rule ID (must be alphanumeric with hyphens/underscores)")
        
        # Validate metric name
        if not rule.metric:
            errors.append("Metric name is required")
        
        # Validate condition
        try:
            AlertCondition(rule.condition)
        except ValueError:
            errors.append(f"Invalid condition: {rule.condition}")
        
        # Validate threshold
        if not isinstance(rule.threshold, (int, float)):
            errors.append("Threshold must be a number")
        
        # Validate duration
        if rule.duration < 0:
            errors.append("Duration must be non-negative")
        
        # Validate severity
        try:
            AlertSeverity(rule.severity)
        except ValueError:
            errors.append(f"Invalid severity: {rule.severity}")
        
        return errors
    
    def import_rules(self, rules: List[Dict]) -> Dict[str, Any]:
        """Import alert rules from a list of dictionaries."""
        results = {
            "imported": 0,
            "failed": 0,
            "errors": []
        }
        
        for rule_dict in rules:
            try:
                rule = AlertRule(**rule_dict)
                errors = self.validate_rule(rule)
                
                if errors:
                    results["failed"] += 1
                    results["errors"].append({
                        "rule_id": rule.id,
                        "errors": errors
                    })
                else:
                    self.add_rule(rule)
                    results["imported"] += 1
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "rule": rule_dict,
                    "error": str(e)
                })
        
        return results
    
    def export_rules(self) -> List[Dict]:
        """Export all rules as dictionaries."""
        return [rule.to_dict() for rule in self.rules.values()]
    
    def get_rule_history(self, limit: int = 100) -> List[Dict]:
        """Get rule change history."""
        return self.rule_history[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get rule manager statistics."""
        rules = list(self.rules.values())
        return {
            "enabled": self.enabled,
            "total_rules": len(rules),
            "enabled_rules": len([r for r in rules if r.enabled]),
            "disabled_rules": len([r for r in rules if not r.enabled]),
            "by_severity": {
                severity.value: len([r for r in rules if r.severity == severity.value])
                for severity in AlertSeverity
            },
            "history_entries": len(self.rule_history)
        }


# Global alert rule manager instance
_global_rule_manager: Optional[AlertRuleManager] = None


def get_alert_rule_manager() -> AlertRuleManager:
    """Get the global alert rule manager instance."""
    global _global_rule_manager
    if _global_rule_manager is None:
        _global_rule_manager = AlertRuleManager()
    return _global_rule_manager
