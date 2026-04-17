"""
Provider Gateway
Gateway that switches between mock and real providers based on configuration.
"""

import os
import logging
from typing import Dict, Any
from tools.mock_providers import MockProviderGateway

logger = logging.getLogger(__name__)


class ProviderGateway:
    """
    Gateway that switches between mock and real providers based on configuration.
    
    Controlled by USE_REAL_PROVIDERS environment variable.
    """
    
    def __init__(self):
        """
        Initialize Provider Gateway.
        """
        self.use_real_providers = os.getenv("USE_REAL_PROVIDERS", "false").lower() == "true"
        
        if self.use_real_providers:
            logger.info("Initializing Provider Gateway with REAL providers")
            try:
                from providers.google_geocoding import GoogleGeocodingProvider
                from providers.property_data_provider import PropertyDataProvider
                from providers.hazard_data_provider import HazardDataProvider
                from providers.claims_data_provider import ClaimsDataProvider
                
                self.geocoding_provider = GoogleGeocodingProvider()
                self.property_provider = PropertyDataProvider()
                self.hazard_provider = HazardDataProvider()
                self.claims_provider = ClaimsDataProvider()
                
                logger.info("Real providers initialized successfully")
            except ImportError as e:
                logger.warning(f"Failed to import real providers: {e}. Falling back to mock providers.")
                self.use_real_providers = False
                self._init_mock_providers()
        else:
            logger.info("Initializing Provider Gateway with MOCK providers")
            self._init_mock_providers()
    
    def _init_mock_providers(self):
        """Initialize mock providers."""
        self.mock_gateway = MockProviderGateway()
    
    def geocode(self, address: str) -> Dict[str, Any]:
        """
        Geocode an address using configured provider.
        
        Args:
            address: The address to geocode
            
        Returns:
            Dict containing normalized address, coordinates, and metadata (mock-compatible format)
        """
        if self.use_real_providers:
            result = self.geocoding_provider.geocode(address)
            # Transform real provider format to mock-compatible format
            components = result.get("metadata", {}).get("address_components", {})
            return {
                "normalized_address": result.get("normalized_address"),
                "latitude": result.get("latitude"),
                "longitude": result.get("longitude"),
                "county": components.get("administrative_area_level_2", "Unknown"),
                "state": components.get("administrative_area_level_1", "CA"),
                "confidence": result.get("confidence", 0.5),
                "warnings": result.get("warnings", []),
                "metadata": result.get("metadata", {})
            }
        else:
            result = self.mock_gateway.mock_geocode(address)
            logger.debug(f"Mock geocoding result for {address}")
            return result
    
    def get_property_profile(self, address: str) -> Dict[str, Any]:
        """
        Get property profile using configured provider.
        
        Args:
            address: The property address
            
        Returns:
            Dict containing property data (mock-compatible format)
        """
        if self.use_real_providers:
            result = self.property_provider.get_property_profile(address)
            # Transform to mock-compatible format
            return {
                "address": result.get("address"),
                "year_built": result.get("year_built"),
                "square_feet": result.get("square_footage"),
                "roof_type": result.get("roof_type"),
                "roof_age_years": result.get("roof_age_years"),
                "construction_type": result.get("construction_type"),
                "confidence": result.get("confidence", 0.5),
                "warnings": result.get("warnings", []),
                "metadata": result.get("metadata", {})
            }
        else:
            result = self.mock_gateway.mock_property_profile(address)
            logger.debug(f"Mock property profile for {address}")
            return result
    
    def get_hazard_scores(self, county: str, state: str = "CA") -> Dict[str, Any]:
        """
        Get hazard scores using configured provider.
        
        Args:
            county: The county name
            state: The state code
            
        Returns:
            Dict containing hazard scores (mock-compatible format)
        """
        if self.use_real_providers:
            result = self.hazard_provider.get_hazard_scores(county, state)
            # Transform to mock-compatible format
            return {
                "county": result.get("county"),
                "state": result.get("state"),
                "wildfire": result.get("wildfire", {}),
                "flood": result.get("flood", {}),
                "wind": result.get("wind", {}),
                "earthquake": result.get("earthquake", {}),
                "confidence": result.get("confidence", 0.5),
                "warnings": result.get("warnings", []),
                "metadata": result.get("metadata", {})
            }
        else:
            result = self.mock_gateway.mock_hazard_scores(county)
            logger.debug(f"Mock hazard scores for {county}")
            return result
    
    def get_claims_history(self, address: str, dwelling_type: str = "single_family") -> Dict[str, Any]:
        """
        Get claims history using configured provider.
        
        Args:
            address: The property address
            dwelling_type: Type of dwelling
            
        Returns:
            Dict containing claims history (mock-compatible format)
        """
        if self.use_real_providers:
            result = self.claims_provider.get_claims_history(address, dwelling_type)
            # Transform to mock-compatible format
            return {
                "address": result.get("address"),
                "dwelling_type": result.get("dwelling_type"),
                "loss_count_5yr": result.get("loss_count_5yr", 0),
                "total_paid_5yr": result.get("total_paid_5yr", 0),
                "claims": result.get("claims", []),
                "confidence": result.get("confidence", 0.5),
                "warnings": result.get("warnings", []),
                "metadata": result.get("metadata", {})
            }
        else:
            result = self.mock_gateway.mock_claims_history(address, dwelling_type)
            logger.debug(f"Mock claims history for {address}")
            return result
    
    def get_provider_status(self) -> Dict[str, Any]:
        """
        Get status of configured providers.
        
        Returns:
            Dict containing provider status information
        """
        return {
            "use_real_providers": self.use_real_providers,
            "providers": {
                "geocoding": "real" if self.use_real_providers else "mock",
                "property_data": "real" if self.use_real_providers else "mock",
                "hazard_data": "real" if self.use_real_providers else "mock",
                "claims_data": "real" if self.use_real_providers else "mock"
            },
            "configuration": {
                "USE_REAL_PROVIDERS": os.getenv("USE_REAL_PROVIDERS", "false"),
                "GOOGLE_MAPS_API_KEY": "configured" if os.getenv("GOOGLE_MAPS_API_KEY") else "not configured",
                "PROPERTY_DATA_API_KEY": "configured" if os.getenv("PROPERTY_DATA_API_KEY") else "not configured",
                "HAZARD_DATA_API_KEY": "configured" if os.getenv("HAZARD_DATA_API_KEY") else "not configured",
                "CLUE_API_KEY": "configured" if os.getenv("CLUE_API_KEY") else "not configured"
            }
        }
