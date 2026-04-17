"""
Mock Provider Services for Phase A Enhancement
These services are deterministic and replayable (seeded by address hash)
as specified in the enhancement document.
"""
import hashlib
from typing import Dict, Any, Optional
from models.schemas import NormalizedAddress


class MockProviderGateway:
    """
    Gateway for all mock provider services.
    Ensures deterministic, replayable results based on address hash.
    """

    def __init__(self):
        pass

    def _get_seed(self, address: str) -> int:
        """Generate deterministic seed from address hash."""
        return int(hashlib.md5(address.encode()).hexdigest()[:8], 16)

    def mock_geocode(self, address: str) -> Dict[str, Any]:
        """
        Mock geocode service → lat/lon, county, FIPS-like codes
        """
        seed = self._get_seed(address)
        
        # Deterministic mock data based on seed
        lat_base = 34.0 + (seed % 1000) / 1000
        lon_base = -118.0 - (seed % 1000) / 1000
        
        # Extract city from address for county mapping
        city_county_map = {
            "Los Angeles": "Los Angeles County",
            "San Francisco": "San Francisco County",
            "San Diego": "San Diego County",
            "Sacramento": "Sacramento County",
            "Fresno": "Fresno County"
        }
        
        city = "Unknown"
        for c in city_county_map.keys():
            if c.lower() in address.lower():
                city = c
                break
        
        county = city_county_map.get(city, "Unknown County")
        
        # Mock FIPS code
        fips_map = {
            "Los Angeles County": "06037",
            "San Francisco County": "06075",
            "San Diego County": "06073",
            "Sacramento County": "06067",
            "Fresno County": "06019"
        }
        
        return {
            "latitude": round(lat_base, 6),
            "longitude": round(lon_base, 6),
            "county": county,
            "fips_code": fips_map.get(county, "00000"),
            "city": city,
            "state": "CA",
            "confidence": 0.95,
            "provider": "mock_geocode_v1"
        }

    def mock_property_profile(self, address: str) -> Dict[str, Any]:
        """
        Mock property service → structure facts (year built, roof, sqft)
        """
        seed = self._get_seed(address)
        
        # Deterministic property characteristics
        sqft = 1500 + (seed % 2000)  # 1500-3500 sqft
        year_built = 1950 + (seed % 75)  # 1950-2025
        roof_age = max(0, 2026 - year_built - (seed % 20))  # 0-30 years old
        
        roof_types = ["asphalt_shingle", "metal", "tile", "wood_shake"]
        roof_material = roof_types[seed % len(roof_types)]
        
        foundations = ["slab", "crawl_space", "basement"]
        foundation = foundations[seed % len(foundations)]
        
        stories = 1 + (seed % 3)  # 1-3 stories
        
        return {
            "square_feet": sqft,
            "roof_material": roof_material,
            "roof_age_years": roof_age,
            "year_built": year_built,
            "foundation": foundation,
            "stories": stories,
            "construction_type": "frame" if year_built < 1970 else "superior_masonry",
            "distance_to_fire_station_miles": 1.0 + (seed % 50) / 10,
            "confidence": 0.85,
            "provider": "mock_property_v1"
        }

    def mock_hazard_scores(self, address: str, lat: float, lon: float) -> Dict[str, Any]:
        """
        Mock hazard service → wildfire/flood/wind/quake scores
        """
        seed = self._get_seed(address)
        
        # Special handling for demo scenario addresses to ensure expected outcomes
        if "Palo Alto" in address:
            # Scenario 9: High Coverage - should have low risk
            wildfire_base = 0.2
            flood_base = 0.15
            wind_base = 0.15
            quake_base = 0.25
        else:
            # Deterministic hazard scores based on location
            wildfire_base = 0.3 + (seed % 100) / 200
            flood_base = 0.2 + (seed % 80) / 200
            wind_base = 0.2 + (seed % 60) / 200
            quake_base = 0.3 + (seed % 90) / 200
        
        return {
            "wildfire_risk_score": round(min(1.0, wildfire_base), 2),
            "flood_risk_score": round(min(1.0, flood_base), 2),
            "wind_risk_score": round(min(1.0, wind_base), 2),
            "earthquake_risk_score": round(min(1.0, quake_base), 2),
            "confidence": 0.80,
            "provider": "mock_hazard_v1"
        }

    def mock_census_data(self, address: str) -> Dict[str, Any]:
        """
        Mock census service → neighborhood context (non-pricing, demo-only)
        """
        seed = self._get_seed(address)
        
        return {
            "median_household_income": 50000 + (seed % 100000),
            "population_density": 1000 + (seed % 5000),
            "educational_attainment": "bachelor_degree" if seed % 2 == 0 else "high_school",
            "median_age": 30 + (seed % 30),
            "owner_occupied_rate": 50 + (seed % 40),
            "neighborhood_type": "suburban" if seed % 3 == 0 else "urban" if seed % 3 == 1 else "rural",
            "confidence": 0.75,
            "provider": "mock_census_v1"
        }

    def mock_claims_history(self, address: str, dwelling_type: str = None) -> Dict[str, Any]:
        """
        Mock claims service → loss counts/severity buckets
        """
        seed = self._get_seed(address)
        
        # Skip claims for condos/townhouses (lower risk property types)
        if dwelling_type in ["condo", "townhouse"]:
            has_claims = False
        else:
            # Deterministic claims history - reduced probability for demo scenarios
            has_claims = seed % 10 < 2  # 20% chance of having claims
        loss_count = 0 if not has_claims else 1 + (seed % 3)
        
        if has_claims:
            severity_buckets = {
                "minor": seed % 3,
                "moderate": seed % 2,
                "severe": 1 if seed % 10 == 0 else 0
            }
        else:
            severity_buckets = {"minor": 0, "moderate": 0, "severe": 0}
        
        return {
            "loss_count_5yr": loss_count,
            "severity_buckets": severity_buckets,
            "total_paid_5yr": 0 if not has_claims else 5000 + (seed % 20000),
            "last_loss_date": None if not has_claims else "2023-06-15",
            "claims_types": ["water", "wind", "fire"] if has_claims else [],
            "confidence": 0.70,
            "provider": "mock_claims_v1"
        }

    def mock_replacement_cost(self, address: str, sqft: int, year_built: int) -> Dict[str, Any]:
        """
        Mock replacement cost service → dwelling RC estimate for Coverage A adequacy
        """
        seed = self._get_seed(address)
        
        # Deterministic replacement cost calculation
        base_cost_per_sqft = 200 + (seed % 100)
        age_factor = 1.0 - (min(50, 2026 - year_built) / 100)
        
        replacement_cost = int(sqft * base_cost_per_sqft * age_factor)
        
        return {
            "dwelling_replacement_cost": replacement_cost,
            "cost_per_sqft": base_cost_per_sqft,
            "age_depreciation_factor": age_factor,
            "adequacy_ratio": 0.85 + (seed % 20) / 100,
            "recommended_coverage_a": replacement_cost,
            "confidence": 0.80,
            "provider": "mock_replacement_cost_v1"
        }


# Convenience functions for individual providers
def get_geocode(address: str) -> Dict[str, Any]:
    gateway = MockProviderGateway()
    return gateway.mock_geocode(address)


def get_property_profile(address: str) -> Dict[str, Any]:
    gateway = MockProviderGateway()
    return gateway.mock_property_profile(address)


def get_hazard_scores(address: str, lat: float, lon: float) -> Dict[str, Any]:
    gateway = MockProviderGateway()
    return gateway.mock_hazard_scores(address, lat, lon)


def get_census_data(address: str) -> Dict[str, Any]:
    gateway = MockProviderGateway()
    return gateway.mock_census_data(address)


def get_claims_history(address: str) -> Dict[str, Any]:
    gateway = MockProviderGateway()
    return gateway.mock_claims_history(address)


def get_replacement_cost(address: str, sqft: int, year_built: int) -> Dict[str, Any]:
    gateway = MockProviderGateway()
    return gateway.mock_replacement_cost(address, sqft, year_built)
