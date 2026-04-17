# Provider Architecture: Mock vs Real Providers

This document describes the architecture for switching between mock and real provider integrations in production.

## Overview

The system uses a mock provider pattern for testing and development, with the ability to switch to real provider integrations in production via configuration.

## Provider Types

### Current Mock Providers

1. **Geocoding Provider** (`MockProviderGateway.mock_geocode`)
   - Deterministic mock based on address hash
   - Returns lat/lon, county, FIPS-like codes
   - Location: `tools/mock_providers.py`

2. **Property Profile Provider** (`MockProviderGateway.mock_property_profile`)
   - Mock property data (year_built, square_footage, roof_type, etc.)
   - Deterministic based on address
   - Location: `tools/mock_providers.py`

3. **Hazard Scores Provider** (`MockProviderGateway.mock_hazard_scores`)
   - Mock hazard scores (wildfire, flood, wind, earthquake)
   - Deterministic based on county
   - Location: `tools/mock_providers.py`

4. **Claims History Provider** (`MockProviderGateway.mock_claims_history`)
   - Mock claims data (loss_count_5yr, total_paid)
   - Deterministic based on address
   - Location: `tools/mock_providers.py`

## Switching to Real Providers

### Configuration

Set environment variables to enable real providers:

```bash
# Enable real providers (default: false)
export USE_REAL_PROVIDERS=true

# Provider-specific API keys
export GOOGLE_MAPS_API_KEY=your_api_key
export PROPERTY_DATA_API_KEY=your_api_key
export HAZARD_DATA_API_KEY=your_api_key
export CLUE_API_KEY=your_api_key
```

### Implementation Pattern

```python
class ProviderGateway:
    """
    Gateway that switches between mock and real providers based on configuration.
    """
    
    def __init__(self):
        self.use_real_providers = os.getenv("USE_REAL_PROVIDERS", "false").lower() == "true"
        
        if self.use_real_providers:
            self.geocoding_provider = GoogleGeocodingProvider()
            self.property_provider = RealPropertyDataProvider()
            self.hazard_provider = RealHazardDataProvider()
            self.claims_provider = RealClaimsDataProvider()
        else:
            self.geocoding_provider = MockProviderGateway()
            self.property_provider = MockProviderGateway()
            self.hazard_provider = MockProviderGateway()
            self.claims_provider = MockProviderGateway()
    
    def geocode(self, address: str):
        """Geocode using configured provider."""
        return self.geocoding_provider.mock_geocode(address)
```

## Real Provider Implementations

### Google Maps Geocoding

When `USE_REAL_PROVIDERS=true` and `GOOGLE_MAPS_API_KEY` is set:

```python
from tools.google_geocoding import GoogleGeocodingProvider

class GoogleGeocodingProvider:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://maps.googleapis.com/maps/api/geocode/json"
    
    def geocode(self, address: str) -> Dict[str, Any]:
        # Call Google Maps API
        response = requests.get(self.base_url, params={
            "address": address,
            "key": self.api_key
        })
        return self._parse_response(response.json())
```

### Property Data Provider

Real property data providers (e.g., CoreLogic, ATTOM Data):

```python
class RealPropertyDataProvider:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.property-data.com"
    
    def get_property_profile(self, address: str) -> Dict[str, Any]:
        # Call real property data API
        pass
```

### Hazard Data Provider

Real hazard data providers (e.g., FEMA, FEMA NFIP, RiskFactor):

```python
class RealHazardDataProvider:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.hazard-data.com"
    
    def get_hazard_scores(self, address: str) -> Dict[str, Any]:
        # Call real hazard data API
        pass
```

### Claims History Provider

Real claims data providers (e.g., LexisNexis CLUE, ISO A-PLUS):

```python
class RealClaimsDataProvider:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.clue-data.com"
    
    def get_claims_history(self, address: str) -> Dict[str, Any]:
        # Call real claims data API
        pass
```

## Agent Integration

Agents in `workflows/agents.py` use the provider gateway:

```python
class EnrichmentAgent:
    def __init__(self):
        self.provider_gateway = ProviderGateway()
    
    def enrich(self, submission: HO3Submission) -> Dict[str, Any]:
        # Geocode
        geocoding_result = self.provider_gateway.geocode(
            submission.risk.property_address
        )
        
        # Property profile
        property_profile = self.provider_gateway.get_property_profile(
            submission.risk.property_address
        )
        
        # Hazard scores
        hazard_scores = self.provider_gateway.get_hazard_scores(
            geocoding_result["county"]
        )
        
        # Claims history
        claims_history = self.provider_gateway.get_claims_history(
            submission.risk.property_address
        )
        
        return {
            "geocoding": geocoding_result,
            "property_profile": property_profile,
            "hazard_profile": hazard_scores,
            "claims_history": claims_history
        }
```

## Testing Strategy

### Development/Testing (Default)
- `USE_REAL_PROVIDERS=false` (or not set)
- Uses mock providers
- Deterministic, fast, no external dependencies
- All tests pass consistently

### Production
- `USE_REAL_PROVIDERS=true`
- Uses real providers
- Requires API keys
- May have rate limits and costs

### Hybrid Testing
- Can test real provider integration locally with API keys
- Can test with mock providers in CI/CD
- Provider-specific tests can be run separately

## Migration Path

1. **Phase 1: Mock Providers** (Current)
   - All providers use deterministic mocks
   - Fast, reliable testing

2. **Phase 2: Provider Interface** (Next)
   - Create abstract provider interface
   - Implement real provider classes
   - Add configuration switch

3. **Phase 3: Production Deployment**
   - Set `USE_REAL_PROVIDERS=true`
   - Configure API keys
   - Monitor real provider performance

## Monitoring

When using real providers, add monitoring:

- Provider API call latency
- Provider API error rates
- Provider API costs
- Cache hit rates (if caching is implemented)

## Caching Strategy

Consider caching provider responses to reduce API calls:

```python
class CachedProviderGateway:
    def __init__(self):
        self.cache = {}
        self.ttl = 3600  # 1 hour TTL
    
    def geocode(self, address: str):
        cache_key = f"geocode:{address}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        result = self.provider.geocode(address)
        self.cache[cache_key] = result
        return result
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `USE_REAL_PROVIDERS` | Enable real provider integrations | `false` |
| `GOOGLE_MAPS_API_KEY` | Google Maps API key | Required if using real geocoding |
| `PROPERTY_DATA_API_KEY` | Property data API key | Required if using real property data |
| `HAZARD_DATA_API_KEY` | Hazard data API key | Required if using real hazard data |
| `CLUE_API_KEY` | CLUE/insurance API key | Required if using real claims data |
