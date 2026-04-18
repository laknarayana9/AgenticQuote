"""
Webhook System Module
Handles webhook registration, delivery, and retry logic
"""

import time
import json
import hashlib
import hmac
import asyncio
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import httpx


class WebhookEventType(Enum):
    """Webhook event types"""
    CASE_CREATED = "case.created"
    CASE_UPDATED = "case.updated"
    CASE_APPROVED = "case.approved"
    CASE_REJECTED = "case.rejected"
    AGENT_COMPLETED = "agent.completed"
    HITL_ASSIGNED = "hitl.assigned"
    HITL_COMPLETED = "hitl.completed"


@dataclass
class Webhook:
    """Webhook configuration"""
    id: str
    url: str
    events: List[str] = field(default_factory=list)
    secret: Optional[str] = None
    is_active: bool = True
    retry_count: int = 3
    timeout: int = 30
    created_at: datetime = field(default_factory=datetime.now)
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0
    success_count: int = 0
    failure_count: int = 0


@dataclass
class WebhookDelivery:
    """Webhook delivery attempt"""
    webhook_id: str
    event_type: str
    payload: Dict[str, Any]
    status: str
    response_code: Optional[int] = None
    response_body: Optional[str] = None
    attempt_number: int = 1
    delivered_at: datetime = field(default_factory=datetime.now)


class WebhookSystem:
    """Webhook management and delivery system"""
    
    def __init__(self):
        self.webhooks: Dict[str, Webhook] = {}
        self.deliveries: List[WebhookDelivery] = []
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    def register_webhook(
        self,
        url: str,
        events: List[str],
        secret: Optional[str] = None,
        retry_count: int = 3,
        timeout: int = 30
    ) -> Webhook:
        """Register a new webhook"""
        webhook_id = self._generate_webhook_id()
        
        webhook = Webhook(
            id=webhook_id,
            url=url,
            events=events,
            secret=secret,
            retry_count=retry_count,
            timeout=timeout
        )
        
        self.webhooks[webhook_id] = webhook
        return webhook
    
    def unregister_webhook(self, webhook_id: str) -> bool:
        """Unregister a webhook"""
        if webhook_id in self.webhooks:
            del self.webhooks[webhook_id]
            return True
        return False
    
    def get_webhook(self, webhook_id: str) -> Optional[Webhook]:
        """Get a webhook by ID"""
        return self.webhooks.get(webhook_id)
    
    def get_all_webhooks(self) -> List[Webhook]:
        """Get all registered webhooks"""
        return list(self.webhooks.values())
    
    def activate_webhook(self, webhook_id: str) -> bool:
        """Activate a webhook"""
        webhook = self.webhooks.get(webhook_id)
        if webhook:
            webhook.is_active = True
            return True
        return False
    
    def deactivate_webhook(self, webhook_id: str) -> bool:
        """Deactivate a webhook"""
        webhook = self.webhooks.get(webhook_id)
        if webhook:
            webhook.is_active = False
            return True
        return False
    
    async def trigger_event(
        self,
        event_type: str,
        payload: Dict[str, Any]
    ) -> List[WebhookDelivery]:
        """Trigger an event to all matching webhooks"""
        matching_webhooks = [
            webhook for webhook in self.webhooks.values()
            if webhook.is_active and event_type in webhook.events
        ]
        
        deliveries = []
        
        for webhook in matching_webhooks:
            delivery = await self._deliver_webhook(webhook, event_type, payload)
            deliveries.append(delivery)
        
        return deliveries
    
    async def _deliver_webhook(
        self,
        webhook: Webhook,
        event_type: str,
        payload: Dict[str, Any]
    ) -> WebhookDelivery:
        """Deliver a webhook with retry logic"""
        webhook.last_triggered = datetime.now()
        webhook.trigger_count += 1
        
        # Prepare payload
        event_payload = {
            "event": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": payload
        }
        
        # Sign payload if secret is provided
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-ID": webhook.id,
            "X-Event-Type": event_type
        }
        
        if webhook.secret:
            signature = self._generate_signature(event_payload, webhook.secret)
            headers["X-Webhook-Signature"] = signature
        
        # Deliver with retry logic
        last_error = None
        success = False
        
        for attempt in range(1, webhook.retry_count + 1):
            try:
                response = await self.http_client.post(
                    webhook.url,
                    json=event_payload,
                    headers=headers,
                    timeout=webhook.timeout
                )
                
                if response.status_code >= 200 and response.status_code < 300:
                    success = True
                    webhook.success_count += 1
                    
                    delivery = WebhookDelivery(
                        webhook_id=webhook.id,
                        event_type=event_type,
                        payload=event_payload,
                        status="success",
                        response_code=response.status_code,
                        response_body=response.text,
                        attempt_number=attempt
                    )
                    break
                else:
                    last_error = f"HTTP {response.status_code}"
                    
            except Exception as e:
                last_error = str(e)
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        if not success:
            webhook.failure_count += 1
            delivery = WebhookDelivery(
                webhook_id=webhook.id,
                event_type=event_type,
                payload=event_payload,
                status="failed",
                response_code=None,
                response_body=last_error,
                attempt_number=webhook.retry_count
            )
        
        self.deliveries.append(delivery)
        return delivery
    
    def get_deliveries(
        self,
        webhook_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[WebhookDelivery]:
        """Get webhook delivery history"""
        deliveries = self.deliveries
        
        if webhook_id:
            deliveries = [d for d in deliveries if d.webhook_id == webhook_id]
        
        if event_type:
            deliveries = [d for d in deliveries if d.event_type == event_type]
        
        return deliveries[-limit:]
    
    def get_webhook_stats(self, webhook_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a webhook"""
        webhook = self.webhooks.get(webhook_id)
        if not webhook:
            return None
        
        deliveries = self.get_deliveries(webhook_id)
        success_deliveries = [d for d in deliveries if d.status == "success"]
        failed_deliveries = [d for d in deliveries if d.status == "failed"]
        
        return {
            "webhook_id": webhook.id,
            "url": webhook.url,
            "is_active": webhook.is_active,
            "trigger_count": webhook.trigger_count,
            "success_count": webhook.success_count,
            "failure_count": webhook.failure_count,
            "total_deliveries": len(deliveries),
            "successful_deliveries": len(success_deliveries),
            "failed_deliveries": len(failed_deliveries),
            "success_rate": len(success_deliveries) / len(deliveries) if deliveries else 0
        }
    
    def verify_signature(
        self,
        payload: Dict[str, Any],
        signature: str,
        secret: str
    ) -> bool:
        """Verify a webhook signature"""
        expected_signature = self._generate_signature(payload, secret)
        return hmac.compare_digest(expected_signature, signature)
    
    def _generate_signature(self, payload: Dict[str, Any], secret: str) -> str:
        """Generate HMAC signature for webhook payload"""
        payload_str = json.dumps(payload, separators=(',', ':'))
        signature = hmac.new(
            secret.encode(),
            payload_str.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"
    
    def _generate_webhook_id(self) -> str:
        """Generate a unique webhook ID"""
        timestamp = str(time.time()).encode()
        hash_obj = hashlib.sha256(timestamp)
        return f"wh_{hash_obj.hexdigest()[:32]}"
    
    async def close(self):
        """Close the HTTP client"""
        await self.http_client.aclose()


# Global webhook system instance
webhook_system = WebhookSystem()
