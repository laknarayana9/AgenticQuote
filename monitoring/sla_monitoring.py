"""
SLA monitoring and reporting for Phase D.2
Tracks Service Level Agreement compliance and generates reports.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum

logger = logging.getLogger(__name__)


class SLAStatus(Enum):
    """SLA status."""
    COMPLIANT = "compliant"
    WARNING = "warning"
    VIOLATION = "violation"


@dataclass
class SLATarget:
    """SLA target definition."""
    id: str
    name: str
    metric: str
    target_value: float
    operator: str  # ">", "<", ">=", "<="
    period: str  # "daily", "weekly", "monthly"
    severity: str
    description: str


@dataclass
class SLAMeasurement:
    """SLA measurement."""
    id: str
    target_id: str
    value: float
    status: str
    timestamp: datetime
    period_start: datetime
    period_end: datetime
    deviation: float


class SLAMonitor:
    """Monitor SLA compliance."""
    
    def __init__(self):
        self.enabled = os.getenv("SLA_MONITORING_ENABLED", "false").lower() == "true"
        self.targets: Dict[str, SLATarget] = {}
        self.measurements: List[SLAMeasurement] = []
        self._load_default_targets()
        
        logger.info(f"SLA monitor initialized (enabled={self.enabled})")
    
    def _load_default_targets(self) -> None:
        """Load default SLA targets."""
        default_targets = [
            SLATarget(
                id="sla_uptime",
                name="Uptime SLA",
                metric="uptime_percentage",
                target_value=99.9,
                operator=">=",
                period="monthly",
                severity="critical",
                description="System uptime must be at least 99.9%"
            ),
            SLATarget(
                id="sla_response_time",
                name="Response Time SLA",
                metric="response_time_p95",
                target_value=1000,
                operator="<=",
                period="daily",
                severity="warning",
                description="P95 response time must be <= 1000ms"
            ),
            SLATarget(
                id="sla_error_rate",
                name="Error Rate SLA",
                metric="error_rate",
                target_value=0.5,
                operator="<=",
                period="daily",
                severity="critical",
                description="Error rate must be <= 0.5%"
            ),
            SLATarget(
                id="sla_success_rate",
                name="Success Rate SLA",
                metric="success_rate",
                target_value=99.5,
                operator=">=",
                period="daily",
                severity="critical",
                description="Success rate must be >= 99.5%"
            ),
            SLATarget(
                id="sla_availability",
                name="Availability SLA",
                metric="availability_percentage",
                target_value=99.5,
                operator=">=",
                period="monthly",
                severity="critical",
                description="Service availability must be >= 99.5%"
            )
        ]
        
        for target in default_targets:
            self.add_target(target)
    
    def add_target(self, target: SLATarget) -> None:
        """Add an SLA target."""
        self.targets[target.id] = target
        logger.info(f"SLA target added: {target.id}")
    
    def remove_target(self, target_id: str) -> bool:
        """Remove an SLA target."""
        if target_id in self.targets:
            del self.targets[target_id]
            logger.info(f"SLA target removed: {target_id}")
            return True
        return False
    
    def measure_target(self, target_id: str, value: float, period_start: datetime, period_end: datetime) -> SLAMeasurement:
        """Measure SLA compliance for a target."""
        target = self.targets.get(target_id)
        if not target:
            raise ValueError(f"Target not found: {target_id}")
        
        # Check compliance
        compliant = self._check_compliance(target, value)
        status = SLAStatus.COMPLIANT.value if compliant else SLAStatus.VIOLATION.value
        
        # Calculate deviation
        deviation = (value - target.target_value) / target.target_value if target.target_value != 0 else 0
        
        measurement = SLAMeasurement(
            id=f"{target_id}-{int(datetime.now().timestamp())}",
            target_id=target_id,
            value=value,
            status=status,
            timestamp=datetime.now(),
            period_start=period_start,
            period_end=period_end,
            deviation=deviation
        )
        
        self.measurements.append(measurement)
        
        if not compliant:
            logger.warning(f"SLA violation: {target.name} - value {value} vs target {target.target_value}")
        
        return measurement
    
    def _check_compliance(self, target: SLATarget, value: float) -> bool:
        """Check if a value meets the SLA target."""
        if target.operator == ">":
            return value > target.target_value
        elif target.operator == "<":
            return value < target.target_value
        elif target.operator == ">=":
            return value >= target.target_value
        elif target.operator == "<=":
            return value <= target.target_value
        elif target.operator == "==":
            return value == target.target_value
        return False
    
    def get_target_status(self, target_id: str) -> Dict[str, Any]:
        """Get current status of a target."""
        target = self.targets.get(target_id)
        if not target:
            return {"error": "Target not found"}
        
        # Get latest measurement
        measurements = [m for m in self.measurements if m.target_id == target_id]
        latest = measurements[-1] if measurements else None
        
        return {
            "target": asdict(target),
            "latest_measurement": asdict(latest) if latest else None,
            "compliant": latest.status == SLAStatus.COMPLIANT.value if latest else None
        }
    
    def get_all_status(self) -> Dict[str, Any]:
        """Get status of all SLA targets."""
        status = {}
        
        for target_id in self.targets:
            status[target_id] = self.get_target_status(target_id)
        
        return status
    
    def get_compliance_report(self, period: str = "daily", days: int = 7) -> Dict[str, Any]:
        """Generate SLA compliance report."""
        cutoff = datetime.now() - timedelta(days=days)
        recent_measurements = [m for m in self.measurements if m.timestamp >= cutoff]
        
        # Group by target
        by_target = defaultdict(list)
        for m in recent_measurements:
            by_target[m.target_id].append(m)
        
        report = {
            "period": period,
            "days": days,
            "generated_at": datetime.now().isoformat(),
            "overall_compliance": 0.0,
            "targets": {}
        }
        
        total_compliant = 0
        total_measurements = 0
        
        for target_id, measurements in by_target.items():
            target = self.targets.get(target_id)
            compliant_count = len([m for m in measurements if m.status == SLAStatus.COMPLIANT.value])
            compliance_rate = compliant_count / len(measurements) if measurements else 0
            
            report["targets"][target_id] = {
                "name": target.name if target else target_id,
                "target_value": target.target_value if target else 0,
                "compliance_rate": compliance_rate * 100,
                "total_measurements": len(measurements),
                "compliant_measurements": compliant_count,
                "violations": len(measurements) - compliant_count,
                "latest_value": measurements[-1].value if measurements else None,
                "latest_status": measurements[-1].status if measurements else None
            }
            
            total_compliant += compliant_count
            total_measurements += len(measurements)
        
        if total_measurements > 0:
            report["overall_compliance"] = (total_compliant / total_measurements) * 100
        
        return report
    
    def get_violations(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get SLA violations."""
        cutoff = datetime.now() - timedelta(days=days)
        violations = [m for m in self.measurements if m.timestamp >= cutoff and m.status == SLAStatus.VIOLATION.value]
        
        return [
            {
                "target_id": m.target_id,
                "target_name": self.targets[m.target_id].name if m.target_id in self.targets else m.target_id,
                "value": m.value,
                "target_value": self.targets[m.target_id].target_value if m.target_id in self.targets else 0,
                "deviation": m.deviation,
                "timestamp": m.timestamp.isoformat(),
                "period": f"{m.period_start.isoformat()} to {m.period_end.isoformat()}"
            }
            for m in violations
        ]
    
    def clear_old_measurements(self, days: int = 30) -> int:
        """Clear measurements older than specified days."""
        cutoff = datetime.now() - timedelta(days=days)
        old_count = len(self.measurements)
        self.measurements = [m for m in self.measurements if m.timestamp >= cutoff]
        cleared = old_count - len(self.measurements)
        logger.info(f"Cleared {cleared} old SLA measurements")
        return cleared
    
    def get_stats(self) -> Dict[str, Any]:
        """Get SLA monitor statistics."""
        return {
            "enabled": self.enabled,
            "total_targets": len(self.targets),
            "total_measurements": len(self.measurements),
            "recent_violations": len(self.get_violations(days=1)),
            "compliance_rate": self.get_compliance_report(days=1)["overall_compliance"]
        }


# Global SLA monitor instance
_global_sla_monitor: Optional[SLAMonitor] = None


def get_sla_monitor() -> SLAMonitor:
    """Get the global SLA monitor instance."""
    global _global_sla_monitor
    if _global_sla_monitor is None:
        _global_sla_monitor = SLAMonitor()
    return _global_sla_monitor
