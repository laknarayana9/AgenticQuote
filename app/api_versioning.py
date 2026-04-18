"""
API Versioning Module
Handles API versioning strategy and backward compatibility
"""

from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass
from functools import wraps
import re


@dataclass
class APIVersion:
    """API version configuration"""
    version: str
    status: str  # active, deprecated, sunset
    sunset_date: Optional[str] = None
    deprecation_date: Optional[str] = None
    migration_guide: Optional[str] = None


class APIVersionManager:
    """Manages API versions and version routing"""
    
    def __init__(self):
        self.versions: Dict[str, APIVersion] = {}
        self.current_version: str = "v1"
        self.version_headers = ["X-API-Version", "Accept-Version"]
        
        # Initialize default versions
        self._initialize_default_versions()
    
    def _initialize_default_versions(self):
        """Initialize default API versions"""
        self.versions["v1"] = APIVersion(
            version="v1",
            status="active"
        )
        self.versions["v2"] = APIVersion(
            version="v2",
            status="active"
        )
    
    def register_version(
        self,
        version: str,
        status: str = "active",
        sunset_date: Optional[str] = None,
        deprecation_date: Optional[str] = None,
        migration_guide: Optional[str] = None
    ):
        """Register a new API version"""
        self.versions[version] = APIVersion(
            version=version,
            status=status,
            sunset_date=sunset_date,
            deprecation_date=deprecation_date,
            migration_guide=migration_guide
        )
    
    def set_current_version(self, version: str):
        """Set the current API version"""
        if version not in self.versions:
            raise ValueError(f"Version {version} not registered")
        self.current_version = version
    
    def get_version(self, version: str) -> Optional[APIVersion]:
        """Get version information"""
        return self.versions.get(version)
    
    def is_version_active(self, version: str) -> bool:
        """Check if a version is active"""
        api_version = self.versions.get(version)
        return api_version and api_version.status == "active"
    
    def is_version_deprecated(self, version: str) -> bool:
        """Check if a version is deprecated"""
        api_version = self.versions.get(version)
        return api_version and api_version.status == "deprecated"
    
    def get_all_versions(self) -> Dict[str, APIVersion]:
        """Get all registered versions"""
        return self.versions.copy()
    
    def deprecate_version(
        self,
        version: str,
        deprecation_date: str,
        sunset_date: str,
        migration_guide: Optional[str] = None
    ):
        """Deprecate an API version"""
        if version not in self.versions:
            raise ValueError(f"Version {version} not registered")
        
        self.versions[version].status = "deprecated"
        self.versions[version].deprecation_date = deprecation_date
        self.versions[version].sunset_date = sunset_date
        self.versions[version].migration_guide = migration_guide
    
    def sunset_version(self, version: str):
        """Sunset an API version"""
        if version not in self.versions:
            raise ValueError(f"Version {version} not registered")
        
        self.versions[version].status = "sunset"
    
    def extract_version_from_path(self, path: str) -> Optional[str]:
        """Extract version from URL path"""
        # Pattern: /api/v1/... or /api/v2/...
        match = re.match(r'/api/(v\d+)/', path)
        if match:
            return match.group(1)
        return None
    
    def extract_version_from_header(self, headers: Dict[str, str]) -> Optional[str]:
        """Extract version from headers"""
        for header in self.version_headers:
            if header in headers:
                version = headers[header]
                if version.startswith('v'):
                    return version
        return None
    
    def resolve_version(
        self,
        path: str,
        headers: Optional[Dict[str, str]] = None
    ) -> str:
        """Resolve the API version from path or headers"""
        # Try path first
        version = self.extract_version_from_path(path)
        if version:
            return version
        
        # Try headers
        if headers:
            version = self.extract_version_from_header(headers)
            if version:
                return version
        
        # Default to current version
        return self.current_version
    
    def add_version_headers(
        self,
        headers: Dict[str, str],
        version: str
    ) -> Dict[str, str]:
        """Add version-related headers to response"""
        api_version = self.get_version(version)
        
        if not api_version:
            return headers
        
        headers = headers.copy()
        headers["X-API-Version"] = version
        headers["X-API-Status"] = api_version.status
        
        if api_version.deprecation_date:
            headers["X-API-Deprecation-Date"] = api_version.deprecation_date
        
        if api_version.sunset_date:
            headers["X-API-Sunset-Date"] = api_version.sunset_date
        
        if api_version.migration_guide:
            headers["X-API-Migration-Guide"] = api_version.migration_guide
        
        return headers


def versioned(versions: list = None):
    """Decorator for versioned API endpoints"""
    if versions is None:
        versions = ["v1"]
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Version checking logic would be applied here
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Global version manager instance
version_manager = APIVersionManager()
