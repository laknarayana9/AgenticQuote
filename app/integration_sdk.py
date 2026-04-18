"""
Third-Party Integration SDK
Provides a Python SDK for partners to integrate with AgenticQuote API
"""

import requests
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class IntegrationConfig:
    """Integration configuration"""
    api_key: str
    base_url: str = "https://api.agenticquote.com"
    api_version: str = "v1"
    timeout: int = 30


class AgenticQuoteSDK:
    """AgenticQuote Integration SDK"""
    
    def __init__(self, config: IntegrationConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
            "X-API-Version": config.api_version
        })
    
    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an API request"""
        url = f"{self.config.base_url}/api/{self.config.api_version}{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=self.config.timeout
            )
            
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.HTTPError as e:
            error_data = response.json() if response.content else {}
            raise APIError(
                status_code=response.status_code,
                message=error_data.get("detail", str(e)),
                error_code=error_data.get("error_code")
            )
        except requests.exceptions.RequestException as e:
            raise APIError(
                status_code=None,
                message=f"Request failed: {str(e)}",
                error_code="REQUEST_ERROR"
            )
    
    def create_case(
        self,
        property_address: str,
        property_value: float,
        coverage_amount: float,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new underwriting case"""
        data = {
            "property_address": property_address,
            "property_value": property_value,
            "coverage_amount": coverage_amount
        }
        
        if additional_data:
            data.update(additional_data)
        
        return self._request("POST", "/cases", data=data)
    
    def get_case(self, case_id: str) -> Dict[str, Any]:
        """Get case details by ID"""
        return self._request("GET", f"/cases/{case_id}")
    
    def list_cases(
        self,
        page: int = 1,
        limit: int = 10,
        status: Optional[str] = None,
        risk_level: Optional[str] = None
    ) -> Dict[str, Any]:
        """List cases with optional filters"""
        params = {"page": page, "limit": limit}
        
        if status:
            params["status"] = status
        
        if risk_level:
            params["risk_level"] = risk_level
        
        return self._request("GET", "/cases", params=params)
    
    def update_case(
        self,
        case_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update case details"""
        return self._request("PATCH", f"/cases/{case_id}", data=updates)
    
    def submit_case(self, case_id: str) -> Dict[str, Any]:
        """Submit a case for processing"""
        return self._request("POST", f"/cases/{case_id}/submit")
    
    def approve_case(
        self,
        case_id: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Approve a case"""
        data = {}
        if notes:
            data["notes"] = notes
        
        return self._request("POST", f"/cases/{case_id}/approve", data=data)
    
    def reject_case(
        self,
        case_id: str,
        reason: str,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Reject a case"""
        data = {"reason": reason}
        if notes:
            data["notes"] = notes
        
        return self._request("POST", f"/cases/{case_id}/reject", data=data)
    
    def get_case_status(self, case_id: str) -> Dict[str, Any]:
        """Get case status"""
        return self._request("GET", f"/cases/{case_id}/status")
    
    def get_case_documents(self, case_id: str) -> Dict[str, Any]:
        """Get documents for a case"""
        return self._request("GET", f"/cases/{case_id}/documents")
    
    def upload_document(
        self,
        case_id: str,
        document_type: str,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Upload a document for a case"""
        # This would need multipart/form-data support
        data = {
            "document_type": document_type,
            "metadata": metadata or {}
        }
        
        # For file upload, would need to use files parameter
        return self._request("POST", f"/cases/{case_id}/documents", data=data)
    
    def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """Get agent status"""
        return self._request("GET", f"/agents/{agent_id}")
    
    def list_agents(
        self,
        status: Optional[str] = None,
        expertise: Optional[str] = None
    ) -> Dict[str, Any]:
        """List agents with optional filters"""
        params = {}
        
        if status:
            params["status"] = status
        
        if expertise:
            params["expertise"] = expertise
        
        return self._request("GET", "/agents", params=params)
    
    def register_webhook(
        self,
        url: str,
        events: List[str],
        secret: Optional[str] = None
    ) -> Dict[str, Any]:
        """Register a webhook"""
        data = {
            "url": url,
            "events": events
        }
        
        if secret:
            data["secret"] = secret
        
        return self._request("POST", "/webhooks", data=data)
    
    def list_webhooks(self) -> Dict[str, Any]:
        """List registered webhooks"""
        return self._request("GET", "/webhooks")
    
    def delete_webhook(self, webhook_id: str) -> Dict[str, Any]:
        """Delete a webhook"""
        return self._request("DELETE", f"/webhooks/{webhook_id}")
    
    def get_webhook_deliveries(
        self,
        webhook_id: str,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get webhook delivery history"""
        params = {"limit": limit}
        return self._request("GET", f"/webhooks/{webhook_id}/deliveries", params=params)
    
    def get_metrics(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get API metrics"""
        params = {}
        
        if start_date:
            params["start_date"] = start_date
        
        if end_date:
            params["end_date"] = end_date
        
        return self._request("GET", "/metrics", params=params)
    
    def get_rate_limits(self) -> Dict[str, Any]:
        """Get current rate limit status"""
        return self._request("GET", "/rate-limits")


class APIError(Exception):
    """API error exception"""
    
    def __init__(
        self,
        status_code: Optional[int],
        message: str,
        error_code: Optional[str] = None
    ):
        self.status_code = status_code
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class AsyncAgenticQuoteSDK:
    """Async version of AgenticQuote SDK using httpx"""
    
    def __init__(self, config: IntegrationConfig):
        self.config = config
        import httpx
        self.client = httpx.AsyncClient(
            base_url=f"{config.base_url}/api/{config.api_version}",
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json",
                "X-API-Version": config.api_version
            },
            timeout=config.timeout
        )
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make an async API request"""
        try:
            response = await self.client.request(
                method=method,
                url=endpoint,
                json=data,
                params=params
            )
            
            response.raise_for_status()
            return response.json()
        
        except httpx.HTTPStatusError as e:
            error_data = response.json() if response.content else {}
            raise APIError(
                status_code=response.status_code,
                message=error_data.get("detail", str(e)),
                error_code=error_data.get("error_code")
            )
        except httpx.RequestError as e:
            raise APIError(
                status_code=None,
                message=f"Request failed: {str(e)}",
                error_code="REQUEST_ERROR"
            )
    
    async def create_case(
        self,
        property_address: str,
        property_value: float,
        coverage_amount: float,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new underwriting case (async)"""
        data = {
            "property_address": property_address,
            "property_value": property_value,
            "coverage_amount": coverage_amount
        }
        
        if additional_data:
            data.update(additional_data)
        
        return await self._request("POST", "/cases", data=data)
    
    async def get_case(self, case_id: str) -> Dict[str, Any]:
        """Get case details by ID (async)"""
        return await self._request("GET", f"/cases/{case_id}")
    
    async def list_cases(
        self,
        page: int = 1,
        limit: int = 10,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """List cases with optional filters (async)"""
        params = {"page": page, "limit": limit}
        
        if status:
            params["status"] = status
        
        return await self._request("GET", "/cases", params=params)


def create_sdk(api_key: str, base_url: str = "https://api.agenticquote.com") -> AgenticQuoteSDK:
    """Convenience function to create an SDK instance"""
    config = IntegrationConfig(api_key=api_key, base_url=base_url)
    return AgenticQuoteSDK(config)


def create_async_sdk(
    api_key: str,
    base_url: str = "https://api.agenticquote.com"
) -> AsyncAgenticQuoteSDK:
    """Convenience function to create an async SDK instance"""
    config = IntegrationConfig(api_key=api_key, base_url=base_url)
    return AsyncAgenticQuoteSDK(config)
