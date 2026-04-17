"""
Google Maps Geocoding Provider
Real provider implementation for address geocoding.
"""

import os
import logging
from typing import Dict, Any, Optional
import requests

logger = logging.getLogger(__name__)


class GoogleGeocodingProvider:
    """
    Real Google Maps Geocoding API provider.
    
    Requires GOOGLE_MAPS_API_KEY environment variable.
    Falls back to mock behavior if API key is not available.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Google Maps Geocoding provider.
        
        Args:
            api_key: Google Maps API key. If None, uses GOOGLE_MAPS_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("GOOGLE_MAPS_API_KEY")
        self.base_url = "https://maps.googleapis.com/maps/api/geocode/json"
        
        if not self.api_key:
            logger.warning("Google Maps API key not found. Using mock behavior.")
    
    def geocode(self, address: str) -> Dict[str, Any]:
        """
        Geocode an address to get normalized address and coordinates.
        
        Args:
            address: The address to geocode
            
        Returns:
            Dict containing normalized address, coordinates, and metadata
        """
        if not self.api_key:
            # Fallback to mock behavior
            return self._mock_geocode(address)
        
        try:
            params = {
                "address": address,
                "key": self.api_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data["status"] != "OK":
                logger.error(f"Geocoding failed: {data['status']} - {data.get('error_message', '')}")
                return self._mock_geocode(address)
            
            result = data["results"][0]
            components = {comp["types"][0]: comp["long_name"] for comp in result["address_components"]}
            
            return {
                "normalized_address": result["formatted_address"],
                "latitude": result["geometry"]["location"]["lat"],
                "longitude": result["geometry"]["location"]["lng"],
                "confidence": 1.0,
                "warnings": [],
                "metadata": {
                    "place_id": result.get("place_id"),
                    "address_components": components,
                    "geometry_type": result["geometry"]["geometry_type"],
                    "partial_match": result.get("partial_match", False)
                }
            }
            
        except Exception as e:
            logger.error(f"Geocoding error: {e}", exc_info=True)
            # Fallback to mock behavior on error
            return self._mock_geocode(address)
    
    def reverse_geocode(self, lat: float, lng: float) -> Dict[str, Any]:
        """
        Reverse geocode coordinates to get an address.
        
        Args:
            lat: Latitude
            lng: Longitude
            
        Returns:
            Dict containing address and metadata
        """
        if not self.api_key:
            return self._mock_reverse_geocode(lat, lng)
        
        try:
            params = {
                "latlng": f"{lat},{lng}",
                "key": self.api_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data["status"] != "OK":
                logger.error(f"Reverse geocoding failed: {data['status']}")
                return self._mock_reverse_geocode(lat, lng)
            
            result = data["results"][0]
            
            return {
                "address": result["formatted_address"],
                "confidence": 1.0,
                "metadata": {
                    "place_id": result.get("place_id"),
                    "address_components": result["address_components"]
                }
            }
            
        except Exception as e:
            logger.error(f"Reverse geocoding error: {e}", exc_info=True)
            return self._mock_reverse_geocode(lat, lng)
    
    def _mock_geocode(self, address: str) -> Dict[str, Any]:
        """
        Mock geocoding behavior as fallback.
        """
        # Simple parsing for mock behavior
        parts = address.split(",")
        city = parts[1].strip() if len(parts) > 1 else "Unknown"
        state = parts[2].strip() if len(parts) > 2 else "Unknown"
        
        return {
            "normalized_address": address,
            "latitude": 37.7749,  # Default to San Francisco
            "longitude": -122.4194,
            "confidence": 0.5,
            "warnings": ["Using mock geocoding - API key not configured"],
            "metadata": {
                "mock": True,
                "city": city,
                "state": state
            }
        }
    
    def _mock_reverse_geocode(self, lat: float, lng: float) -> Dict[str, Any]:
        """
        Mock reverse geocoding behavior as fallback.
        """
        return {
            "address": f"{lat}, {lng}",
            "confidence": 0.5,
            "warnings": ["Using mock reverse geocoding - API key not configured"],
            "metadata": {
                "mock": True,
                "latitude": lat,
                "longitude": lng
            }
        }
