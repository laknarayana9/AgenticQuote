"""
Hazard Data Provider
Real provider implementation for hazard scores (FEMA/RiskFactor).
"""

import os
import logging
from typing import Dict, Any, Optional
import requests

logger = logging.getLogger(__name__)


class HazardDataProvider:
    """
    Real Hazard Data provider (FEMA/RiskFactor).
    
    Requires HAZARD_DATA_API_KEY environment variable.
    Falls back to mock behavior if API key is not available.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Hazard Data provider.
        
        Args:
            api_key: Hazard Data API key. If None, uses HAZARD_DATA_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("HAZARD_DATA_API_KEY")
        self.base_url = os.getenv("HAZARD_DATA_API_URL", "https://api.hazard-data.com")
        
        if not self.api_key:
            logger.warning("Hazard Data API key not found. Using mock behavior.")
    
    def get_hazard_scores(self, county: str, state: str = "CA") -> Dict[str, Any]:
        """
        Get hazard scores for a county.
        
        Args:
            county: The county name
            state: The state code (default: CA)
            
        Returns:
            Dict containing hazard scores (wildfire, flood, wind, earthquake)
        """
        if not self.api_key:
            return self._mock_hazard_scores(county, state)
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            params = {
                "county": county,
                "state": state
            }
            
            response = requests.get(
                f"{self.base_url}/hazard/scores",
                headers=headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            
            return {
                "county": county,
                "state": state,
                "wildfire": {
                    "score": data.get("wildfire_score", 0),
                    "risk_level": data.get("wildfire_risk_level", "Low"),
                    "fire_district": data.get("fire_district"),
                    "vegetation_type": data.get("vegetation_type"),
                    "topography": data.get("topography")
                },
                "flood": {
                    "score": data.get("flood_score", 0),
                    "risk_level": data.get("flood_risk_level", "Low"),
                    "fema_zone": data.get("fema_zone"),
                    "base_flood_elevation": data.get("base_flood_elevation"),
                    "distance_to_water": data.get("distance_to_water")
                },
                "wind": {
                    "score": data.get("wind_score", 0),
                    "risk_level": data.get("wind_risk_level", "Low"),
                    "wind_zone": data.get("wind_zone"),
                    "design_wind_speed": data.get("design_wind_speed")
                },
                "earthquake": {
                    "score": data.get("earthquake_score", 0),
                    "risk_level": data.get("earthquake_risk_level", "Low"),
                    "seismic_zone": data.get("seismic_zone"),
                    "peak_ground_acceleration": data.get("peak_ground_acceleration")
                },
                "confidence": 1.0,
                "warnings": [],
                "metadata": {
                    "data_source": data.get("data_source"),
                    "last_updated": data.get("last_updated")
                }
            }
            
        except Exception as e:
            logger.error(f"Hazard data error: {e}", exc_info=True)
            return self._mock_hazard_scores(county, state)
    
    def _mock_hazard_scores(self, county: str, state: str = "CA") -> Dict[str, Any]:
        """
        Mock hazard scores behavior as fallback.
        """
        # Deterministic mock data based on county
        county_lower = county.lower()
        
        # High wildfire risk counties
        wildfire_high = ["los angeles", "ventura", "santa barbara", "san diego", "riverside", "san bernardino"]
        # High flood risk counties
        flood_high = ["sacramento", "yolo", "san joaquin", "contra costa", "alameda"]
        
        wildfire_score = 80 if any(c in county_lower for c in wildfire_high) else 20
        flood_score = 80 if any(c in county_lower for c in flood_high) else 20
        wind_score = 40
        earthquake_score = 60 if state == "CA" else 20
        
        return {
            "county": county,
            "state": state,
            "wildfire": {
                "score": wildfire_score,
                "risk_level": "High" if wildfire_score >= 70 else "Low",
                "fire_district": f"{county} Fire District",
                "vegetation_type": "Mixed" if wildfire_score >= 70 else "Low",
                "topography": "Hilly" if wildfire_score >= 70 else "Flat"
            },
            "flood": {
                "score": flood_score,
                "risk_level": "High" if flood_score >= 70 else "Low",
                "fema_zone": "AE" if flood_score >= 70 else "X",
                "base_flood_elevation": 10 if flood_score >= 70 else None,
                "distance_to_water": 500 if flood_score >= 70 else 5000
            },
            "wind": {
                "score": wind_score,
                "risk_level": "Moderate",
                "wind_zone": "II",
                "design_wind_speed": 110
            },
            "earthquake": {
                "score": earthquake_score,
                "risk_level": "High" if earthquake_score >= 70 else "Low",
                "seismic_zone": "4" if earthquake_score >= 70 else "2",
                "peak_ground_acceleration": 0.4 if earthquake_score >= 70 else 0.2
            },
            "confidence": 0.5,
            "warnings": ["Using mock hazard data - API key not configured"],
            "metadata": {
                "mock": True
            }
        }
