"""
Claims Data Provider
Real provider implementation for claims history (CLUE/LexisNexis).
"""

import os
import logging
from typing import Dict, Any, Optional
import requests
import hashlib

logger = logging.getLogger(__name__)


class ClaimsDataProvider:
    """
    Real Claims Data provider (CLUE/LexisNexis).
    
    Requires CLUE_API_KEY environment variable.
    Falls back to mock behavior if API key is not available.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Claims Data provider.
        
        Args:
            api_key: Claims Data API key. If None, uses CLUE_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("CLUE_API_KEY")
        self.base_url = os.getenv("CLUE_API_URL", "https://api.clue-data.com")
        
        if not self.api_key:
            logger.warning("CLUE API key not found. Using mock behavior.")
    
    def get_claims_history(self, address: str, dwelling_type: str = "single_family") -> Dict[str, Any]:
        """
        Get claims history for an address.
        
        Args:
            address: The property address
            dwelling_type: Type of dwelling (single_family, condo, townhouse)
            
        Returns:
            Dict containing claims history (loss_count, total_paid, claims_details)
        """
        if not self.api_key:
            return self._mock_claims_history(address, dwelling_type)
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            params = {
                "address": address,
                "dwelling_type": dwelling_type
            }
            
            response = requests.get(
                f"{self.base_url}/claims/history",
                headers=headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            
            return {
                "address": address,
                "dwelling_type": dwelling_type,
                "loss_count_5yr": data.get("loss_count_5yr", 0),
                "total_paid_5yr": data.get("total_paid_5yr", 0),
                "claims": data.get("claims", []),
                "confidence": 1.0,
                "warnings": [],
                "metadata": {
                    "report_id": data.get("report_id"),
                    "report_date": data.get("report_date"),
                    "data_source": data.get("data_source")
                }
            }
            
        except Exception as e:
            logger.error(f"Claims data error: {e}", exc_info=True)
            return self._mock_claims_history(address, dwelling_type)
    
    def _mock_claims_history(self, address: str, dwelling_type: str = "single_family") -> Dict[str, Any]:
        """
        Mock claims history behavior as fallback.
        """
        # Deterministic mock data based on address hash
        seed = int(hashlib.md5(address.encode()).hexdigest()[:8], 16)
        
        # Condos and townhouses typically have fewer claims (HOA handles some)
        if dwelling_type in ["condo", "townhouse"]:
            loss_count = seed % 2  # 0 or 1 claims
            total_paid = loss_count * 5000
        else:
            loss_count = seed % 5  # 0 to 4 claims
            total_paid = loss_count * 10000
        
        claims = []
        for i in range(loss_count):
            claim_types = ["water", "fire", "wind", "theft", "liability"]
            claim_type = claim_types[(seed + i) % len(claim_types)]
            claims.append({
                "claim_id": f"CLM-{seed}-{i}",
                "date": f"20{18 + (i % 5)}-{(seed % 12) + 1:02d}-15",
                "type": claim_type,
                "amount_paid": 5000 + (seed % 10000),
                "status": "closed"
            })
        
        return {
            "address": address,
            "dwelling_type": dwelling_type,
            "loss_count_5yr": loss_count,
            "total_paid_5yr": total_paid,
            "claims": claims,
            "confidence": 0.5,
            "warnings": ["Using mock claims data - API key not configured"],
            "metadata": {
                "mock": True,
                "seed": seed
            }
        }
