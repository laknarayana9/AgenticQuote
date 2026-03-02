"""
PDF Parser for California Property Risk Summary
Extracts property data including addresses and Replacement Cost Estimates (RCE)
Caches data on app startup for fast access
"""

import pdfplumber
import re
import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class PropertyRecord:
    """Property record extracted from PDF"""
    address: str
    property_type: str
    year_built: int
    square_footage: int
    replacement_cost_estimate: float
    wildfire_risk: str
    flood_risk: str

class PropertyDataCache:
    """Cache for property data extracted from PDF"""
    
    def __init__(self, pdf_path: str = None):
        from config import settings
        self.pdf_path = pdf_path or getattr(settings, 'pdf_path', 'app/externaldata/California_Property_Risk_Summary_With_RCE.pdf')
        self.properties: List[PropertyRecord] = []
        self.address_index: Dict[str, PropertyRecord] = {}
        self.is_loaded = False
        
    def load_pdf_data(self) -> bool:
        """
        Load and parse PDF data, cache property records
        Returns True if successful, False otherwise
        """
        try:
            if not os.path.exists(self.pdf_path):
                logger.warning(f"PDF file not found: {self.pdf_path}")
                return False
                
            logger.info(f"Loading property data from PDF: {self.pdf_path}")
            
            with pdfplumber.open(self.pdf_path) as pdf:
                all_text = ""
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        all_text += text + "\n"
            
            if not all_text:
                logger.warning("No text extracted from PDF")
                return False
                
            self._extract_properties_from_text(all_text)
            self._build_address_index()
            
            logger.info(f"Successfully loaded {len(self.properties)} properties")
            self.is_loaded = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to load PDF data: {e}")
            return False
    
    def _extract_properties_from_text(self, text: str):
        """Extract property data from PDF text"""
        # Mock property extraction - in real implementation, this would parse the actual PDF
        # For demo purposes, we'll create some sample properties
        
        sample_properties = [
            PropertyRecord(
                address="2231 Watermarke Pl, Irvine, CA 92612",
                property_type="single_family",
                year_built=2018,
                square_footage=2200,
                replacement_cost_estimate=645200,
                wildfire_risk="moderate",
                flood_risk="low"
            ),
            PropertyRecord(
                address="1234 Main St, Newport Beach, CA 92663",
                property_type="condo",
                year_built=2015,
                square_footage=1500,
                replacement_cost_estimate=425000,
                wildfire_risk="low",
                flood_risk="moderate"
            ),
            PropertyRecord(
                address="5678 Oak Ave, Huntington Beach, CA 92649",
                property_type="townhome",
                year_built=2012,
                square_footage=1800,
                replacement_cost_estimate=525000,
                wildfire_risk="high",
                flood_risk="low"
            ),
            PropertyRecord(
                address="9012 Pacific Coast Hwy, Laguna Beach, CA 92651",
                property_type="single_family",
                year_built=2020,
                square_footage=2800,
                replacement_cost_estimate=850000,
                wildfire_risk="moderate",
                flood_risk="high"
            )
        ]
        
        self.properties = sample_properties
    
    def _build_address_index(self):
        """Build address lookup index"""
        self.address_index = {prop.address.lower(): prop for prop in self.properties}
    
    def find_property_by_address(self, address: str) -> Optional[PropertyRecord]:
        """Find property by address (case-insensitive)"""
        return self.address_index.get(address.lower())
    
    def get_property_count(self) -> int:
        """Get total number of properties"""
        return len(self.properties)
    
    def get_all_properties(self) -> List[PropertyRecord]:
        """Get all properties"""
        return self.properties

# Property cache instance - will be initialized on first use
_property_cache_instance: Optional[PropertyDataCache] = None

def get_property_cache() -> PropertyDataCache:
    """Get or create property cache instance (lazy initialization)"""
    global _property_cache_instance
    if _property_cache_instance is None:
        _property_cache_instance = PropertyDataCache()
    return _property_cache_instance

def initialize_property_cache() -> bool:
    """Initialize property cache on app startup"""
    cache = get_property_cache()
    return cache.load_pdf_data()
