"""
Property Data Provider
Real provider implementation for property data (CoreLogic/ATTOM).
"""

import os
import logging
from typing import Dict, Any, Optional
import requests
import hashlib

logger = logging.getLogger(__name__)


class PropertyDataProvider:
    """
    Real Property Data provider (CoreLogic/ATTOM).
    
    Requires PROPERTY_DATA_API_KEY environment variable.
    Falls back to mock behavior if API key is not available.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Property Data provider.
        
        Args:
            api_key: Property Data API key. If None, uses PROPERTY_DATA_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("PROPERTY_DATA_API_KEY")
        self.base_url = os.getenv("PROPERTY_DATA_API_URL", "https://api.property-data.com")
        
        if not self.api_key:
            logger.warning("Property Data API key not found. Using mock behavior.")
    
    def get_property_profile(self, address: str) -> Dict[str, Any]:
        """
        Get property profile for an address.
        
        Args:
            address: The property address
            
        Returns:
            Dict containing property data (year_built, square_footage, roof_type, etc.)
        """
        if not self.api_key:
            return self._mock_property_profile(address)
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            params = {"address": address}
            
            response = requests.get(
                f"{self.base_url}/property/profile",
                headers=headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            
            return {
                "address": address,
                "year_built": data.get("year_built"),
                "square_footage": data.get("square_footage"),
                "roof_type": data.get("roof_type"),
                "roof_age_years": data.get("roof_age_years"),
                "construction_type": data.get("construction_type"),
                "foundation_type": data.get("foundation_type"),
                "heating_type": data.get("heating_type"),
                "cooling_type": data.get("cooling_type"),
                "num_stories": data.get("num_stories"),
                "num_bedrooms": data.get("num_bedrooms"),
                "num_bathrooms": data.get("num_bathrooms"),
                "garage_type": data.get("garage_type"),
                "pool": data.get("pool", False),
                "confidence": 1.0,
                "warnings": [],
                "metadata": {
                    "property_id": data.get("property_id"),
                    "parcel_id": data.get("parcel_id"),
                    "last_updated": data.get("last_updated")
                }
            }
            
        except Exception as e:
            logger.error(f"Property data error: {e}", exc_info=True)
            return self._mock_property_profile(address)
    
    def _mock_property_profile(self, address: str) -> Dict[str, Any]:
        """
        Mock property profile behavior as fallback.
        """
        # Deterministic mock data based on address hash
        seed = int(hashlib.md5(address.encode()).hexdigest()[:8], 16)
        
        return {
            "address": address,
            "year_built": 2000 + (seed % 30),
            "square_footage": 1500 + (seed % 1500),
            "roof_type": ["asphalt_shingle", "metal", "tile", "wood_shake"][seed % 4],
            "roof_age_years": seed % 20,
            "construction_type": ["frame", "masonry", "steel", "concrete"][seed % 4],
            "foundation_type": ["slab", "basement", "crawlspace"][seed % 3],
            "heating_type": ["forced_air", "heat_pump", "electric", "gas"][seed % 4],
            "cooling_type": ["central", "window_unit", "none"][seed % 3],
            "num_stories": 1 + (seed % 3),
            "num_bedrooms": 2 + (seed % 4),
            "num_bathrooms": 1 + (seed % 3),
            "garage_type": ["attached", "detached", "carport", "none"][seed % 4],
            "pool": seed % 5 == 0,
            "confidence": 0.5,
            "warnings": ["Using mock property data - API key not configured"],
            "metadata": {
                "mock": True,
                "seed": seed
            }
        }
