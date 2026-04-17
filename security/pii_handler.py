"""
PII Handler
Handles Personally Identifiable Information (PII) detection and redaction.
"""

import os
import logging
from typing import Dict, Any, List, Optional
import re

logger = logging.getLogger(__name__)


class PIIType(Enum):
    """Types of PII."""
    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    ADDRESS = "address"
    NAME = "name"
    CREDIT_CARD = "credit_card"
    IP_ADDRESS = "ip_address"


class PIIHandler:
    """
    PII handler for detection and redaction.
    
    Detects and redacts personally identifiable information from text.
    """
    
    def __init__(self):
        """Initialize PII handler."""
        self.enabled = os.getenv("PII_HANDLING_ENABLED", "false").lower() == "true"
        
        # PII patterns
        self.patterns = {
            PIIType.EMAIL: r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            PIIType.PHONE: r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            PIIType.SSN: r'\b\d{3}-\d{2}-\d{4}\b',
            PIIType.CREDIT_CARD: r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',
            PIIType.IP_ADDRESS: r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
        }
        
        logger.info(f"PII handler initialized (enabled={self.enabled})")
    
    def detect_pii(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect PII in text.
        
        Args:
            text: Text to scan
            
        Returns:
            List of detected PII items
        """
        if not self.enabled:
            return []
        
        detected_pii = []
        
        for pii_type, pattern in self.patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                detected_pii.append({
                    "type": pii_type.value,
                    "value": match.group(),
                    "start": match.start(),
                    "end": match.end()
                })
        
        return detected_pii
    
    def redact_pii(self, text: str, mask_char: str = "*") -> str:
        """
        Redact PII from text.
        
        Args:
            text: Text to redact
            mask_char: Character to use for masking
            
        Returns:
            Redacted text
        """
        if not self.enabled:
            return text
        
        pii_items = self.detect_pii(text)
        
        # Sort by start position in reverse order to avoid index shifting
        pii_items.sort(key=lambda x: x["start"], reverse=True)
        
        redacted_text = text
        for pii in pii_items:
            start = pii["start"]
            end = pii["end"]
            redacted_text = redacted_text[:start] + mask_char * (end - start) + redacted_text[end:]
        
        return redacted_text
    
    def redact_dict(self, data: Dict[str, Any], fields: List[str] = None) -> Dict[str, Any]:
        """
        Redact PII from dictionary fields.
        
        Args:
            data: Dictionary with data
            fields: List of field names to redact (all if None)
            
        Returns:
            Dictionary with redacted fields
        """
        if not self.enabled:
            return data
        
        redacted_data = data.copy()
        
        if fields is None:
            fields = list(redacted_data.keys())
        
        for field in fields:
            if field in redacted_data and isinstance(redacted_data[field], str):
                redacted_data[field] = self.redact_pii(redacted_data[field])
        
        return redacted_data
    
    def has_pii(self, text: str) -> bool:
        """
        Check if text contains PII.
        
        Args:
            text: Text to check
            
        Returns:
            True if PII detected
        """
        return len(self.detect_pii(text)) > 0
    
    def get_pii_summary(self, text: str) -> Dict[str, Any]:
        """
        Get summary of PII in text.
        
        Args:
            text: Text to analyze
            
        Returns:
            PII summary
        """
        if not self.enabled:
            return {"enabled": False}
        
        detected_pii = self.detect_pii(text)
        
        # Count by type
        type_counts = {}
        for pii in detected_pii:
            pii_type = pii["type"]
            type_counts[pii_type] = type_counts.get(pii_type, 0) + 1
        
        return {
            "enabled": True,
            "has_pii": len(detected_pii) > 0,
            "total_pii_count": len(detected_pii),
            "pii_by_type": type_counts
        }


# Global PII handler instance
_global_pii_handler: Optional[PIIHandler] = None


def get_pii_handler() -> PIIHandler:
    """
    Get global PII handler instance (singleton pattern).
    
    Returns:
        PIIHandler instance
    """
    global _global_pii_handler
    if _global_pii_handler is None:
        _global_pii_handler = PIIHandler()
    return _global_pii_handler
