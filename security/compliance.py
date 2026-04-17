"""
Compliance Reporting
Generates compliance reports for regulatory requirements.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class ComplianceFramework(Enum):
    """Compliance frameworks."""
    GDPR = "gdpr"
    CCPA = "ccpa"
    SOX = "sox"
    HIPAA = "hipaa"


class ComplianceReporter:
    """
    Compliance reporting system.
    
    Generates reports for regulatory compliance requirements.
    """
    
    def __init__(self):
        """Initialize compliance reporter."""
        self.enabled = os.getenv("COMPLIANCE_REPORTING_ENABLED", "false").lower() == "true"
        
        # Compliance data
        self.compliance_events = []
        
        logger.info(f"Compliance reporter initialized (enabled={self.enabled})")
    
    def record_access_event(
        self,
        user_id: str,
        data_type: str,
        purpose: str,
        legal_basis: str = None
    ):
        """
        Record a data access event for compliance.
        
        Args:
            user_id: User ID
            data_type: Type of data accessed
            purpose: Purpose of access
            legal_basis: Legal basis for access (GDPR)
        """
        if not self.enabled:
            return
        
        event = {
            "event_type": "data_access",
            "user_id": user_id,
            "data_type": data_type,
            "purpose": purpose,
            "legal_basis": legal_basis,
            "timestamp": datetime.now().isoformat()
        }
        
        self.compliance_events.append(event)
        logger.debug(f"Recorded compliance access event for user {user_id}")
    
    def record_consent(
        self,
        user_id: str,
        consent_type: str,
        consent_given: bool,
        consent_date: datetime = None
    ):
        """
        Record a consent event.
        
        Args:
            user_id: User ID
            consent_type: Type of consent
            consent_given: Whether consent was given
            consent_date: Date of consent
        """
        if not self.enabled:
            return
        
        event = {
            "event_type": "consent",
            "user_id": user_id,
            "consent_type": consent_type,
            "consent_given": consent_given,
            "consent_date": (consent_date or datetime.now()).isoformat(),
            "timestamp": datetime.now().isoformat()
        }
        
        self.compliance_events.append(event)
    
    def record_data_deletion(
        self,
        user_id: str,
        data_type: str,
        deletion_requested_by: str
    ):
        """
        Record a data deletion request (GDPR right to be forgotten).
        
        Args:
            user_id: User ID
            data_type: Type of data deleted
            deletion_requested_by: Who requested deletion
        """
        if not self.enabled:
            return
        
        event = {
            "event_type": "data_deletion",
            "user_id": user_id,
            "data_type": data_type,
            "deletion_requested_by": deletion_requested_by,
            "timestamp": datetime.now().isoformat()
        }
        
        self.compliance_events.append(event)
    
    def generate_report(
        self,
        framework: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Generate a compliance report for a framework.
        
        Args:
            framework: Compliance framework
            start_date: Report start date
            end_date: Report end date
            
        Returns:
            Compliance report
        """
        if not self.enabled:
            return {
                "compliance_reporting_enabled": False,
                "framework": framework,
                "reason": "Compliance reporting disabled"
            }
        
        try:
            framework_enum = ComplianceFramework(framework.lower())
        except ValueError:
            return {
                "compliance_reporting_enabled": True,
                "framework": framework,
                "reason": "Unknown compliance framework"
            }
        
        # Filter events by date range
        filtered_events = [
            e for e in self.compliance_events
            if start_date <= datetime.fromisoformat(e["timestamp"]) <= end_date
        ]
        
        # Generate report based on framework
        if framework_enum == ComplianceFramework.GDPR:
            return self._generate_gdpr_report(filtered_events, start_date, end_date)
        elif framework_enum == ComplianceFramework.CCPA:
            return self._generate_ccpa_report(filtered_events, start_date, end_date)
        elif framework_enum == ComplianceFramework.SOX:
            return self._generate_sox_report(filtered_events, start_date, end_date)
        elif framework_enum == ComplianceFramework.HIPAA:
            return self._generate_hipaa_report(filtered_events, start_date, end_date)
        else:
            return {
                "compliance_reporting_enabled": True,
                "framework": framework,
                "reason": "Framework not implemented"
            }
    
    def _generate_gdpr_report(
        self,
        events: List[Dict[str, Any]],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate GDPR compliance report."""
        data_access_events = [e for e in events if e["event_type"] == "data_access"]
        consent_events = [e for e in events if e["event_type"] == "consent"]
        deletion_events = [e for e in events if e["event_type"] == "data_deletion"]
        
        return {
            "framework": "GDPR",
            "report_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "data_access_count": len(data_access_events),
            "consent_count": len(consent_events),
            "consent_given_count": sum(1 for e in consent_events if e["consent_given"]),
            "deletion_requests": len(deletion_events),
            "legal_basis_compliance": self._check_legal_basis_compliance(data_access_events)
        }
    
    def _generate_ccpa_report(
        self,
        events: List[Dict[str, Any]],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate CCPA compliance report."""
        return {
            "framework": "CCPA",
            "report_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "total_events": len(events),
            "note": "CCPA report implementation pending"
        }
    
    def _generate_sox_report(
        self,
        events: List[Dict[str, Any]],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate SOX compliance report."""
        return {
            "framework": "SOX",
            "report_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "total_events": len(events),
            "note": "SOX report implementation pending"
        }
    
    def _generate_hipaa_report(
        self,
        events: List[Dict[str, Any]],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate HIPAA compliance report."""
        return {
            "framework": "HIPAA",
            "report_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "total_events": len(events),
            "note": "HIPAA report implementation pending"
        }
    
    def _check_legal_basis_compliance(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check legal basis compliance for GDPR."""
        events_with_basis = [e for e in events if e.get("legal_basis")]
        return {
            "total_access_events": len(events),
            "events_with_legal_basis": len(events_with_basis),
            "compliance_rate": len(events_with_basis) / len(events) if events else 0
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get compliance summary.
        
        Returns:
            Summary data
        """
        if not self.enabled:
            return {"enabled": False}
        
        return {
            "enabled": True,
            "total_events": len(self.compliance_events),
            "event_types": {
                event_type: sum(1 for e in self.compliance_events if e["event_type"] == event_type)
                for event_type in ["data_access", "consent", "data_deletion"]
            }
        }


# Global compliance reporter instance
_global_compliance_reporter: Optional[ComplianceReporter] = None


def get_compliance_reporter() -> ComplianceReporter:
    """
    Get global compliance reporter instance (singleton pattern).
    
    Returns:
        ComplianceReporter instance
    """
    global _global_compliance_reporter
    if _global_compliance_reporter is None:
        _global_compliance_reporter = ComplianceReporter()
    return _global_compliance_reporter
