"""
Alert notification channels for Phase D.2
Supports multiple notification channels: Slack, PagerDuty, Email, Webhooks.
"""

import os
import json
import logging
import requests
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class NotificationChannel(Enum):
    """Notification channel types."""
    SLACK = "slack"
    PAGERDUTY = "pagerduty"
    EMAIL = "email"
    WEBHOOK = "webhook"
    SMS = "sms"


@dataclass
class Notification:
    """Alert notification."""
    id: str
    alert_id: str
    alert_name: str
    severity: str
    message: str
    labels: Dict[str, str]
    timestamp: datetime
    channel: str
    status: str = "pending"
    sent_at: Optional[datetime] = None
    error: Optional[str] = None


class NotificationChannelBase(ABC):
    """Base class for notification channels."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.enabled = config.get("enabled", True)
        self.channel_type = config.get("type")
        
    @abstractmethod
    def send(self, notification: Notification) -> bool:
        """Send a notification."""
        pass
    
    def format_message(self, notification: Notification) -> str:
        """Format notification message."""
        severity_emoji = {
            "critical": "🚨",
            "error": "❌",
            "warning": "⚠️",
            "info": "ℹ️"
        }.get(notification.severity, "📢")
        
        return f"{severity_emoji} **{notification.alert_name}**\n\n{notification.message}"


class SlackChannel(NotificationChannelBase):
    """Slack notification channel."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.webhook_url = config.get("webhook_url")
        self.channel = config.get("channel", "#alerts")
        self.username = config.get("username", "AgenticQuote Alerts")
        
    def send(self, notification: Notification) -> bool:
        """Send notification to Slack."""
        if not self.enabled or not self.webhook_url:
            logger.warning("Slack channel disabled or not configured")
            return False
        
        try:
            payload = {
                "channel": self.channel,
                "username": self.username,
                "text": self.format_message(notification),
                "attachments": [
                    {
                        "color": self._get_color(notification.severity),
                        "fields": [
                            {
                                "title": "Severity",
                                "value": notification.severity,
                                "short": True
                            },
                            {
                                "title": "Timestamp",
                                "value": notification.timestamp.isoformat(),
                                "short": True
                            }
                        ]
                    }
                ]
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            
            success = response.status_code == 200
            if not success:
                logger.error(f"Slack notification failed: {response.text}")
            
            return success
        except Exception as e:
            logger.error(f"Error sending Slack notification: {e}")
            return False
    
    def _get_color(self, severity: str) -> str:
        """Get Slack color based on severity."""
        colors = {
            "critical": "#ff0000",
            "error": "#ff6600",
            "warning": "#ffcc00",
            "info": "#36a64f"
        }
        return colors.get(severity, "#36a64f")


class PagerDutyChannel(NotificationChannelBase):
    """PagerDuty notification channel."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.integration_key = config.get("integration_key")
        self.api_key = config.get("api_key")
        self.service_key = config.get("service_key")
        
    def send(self, notification: Notification) -> bool:
        """Send notification to PagerDuty."""
        if not self.enabled or not self.integration_key:
            logger.warning("PagerDuty channel disabled or not configured")
            return False
        
        try:
            payload = {
                "routing_key": self.integration_key,
                "event_action": "trigger",
                "payload": {
                    "summary": f"{notification.alert_name}: {notification.message}",
                    "severity": self._map_severity(notification.severity),
                    "source": "agenticquote",
                    "custom_details": {
                        "alert_id": notification.alert_id,
                        "labels": notification.labels,
                        "timestamp": notification.timestamp.isoformat()
                    }
                }
            }
            
            response = requests.post(
                "https://events.pagerduty.com/v2/enqueue",
                json=payload,
                timeout=10
            )
            
            success = response.status_code == 202
            if not success:
                logger.error(f"PagerDuty notification failed: {response.text}")
            
            return success
        except Exception as e:
            logger.error(f"Error sending PagerDuty notification: {e}")
            return False
    
    def _map_severity(self, severity: str) -> str:
        """Map severity to PagerDuty severity."""
        mapping = {
            "critical": "critical",
            "error": "error",
            "warning": "warning",
            "info": "info"
        }
        return mapping.get(severity, "info")


class EmailChannel(NotificationChannelBase):
    """Email notification channel."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.smtp_server = config.get("smtp_server", "smtp.gmail.com")
        self.smtp_port = config.get("smtp_port", 587)
        self.smtp_username = config.get("smtp_username")
        self.smtp_password = config.get("smtp_password")
        self.from_address = config.get("from_address", "alerts@agenticquote.com")
        self.to_addresses = config.get("to_addresses", [])
        
    def send(self, notification: Notification) -> bool:
        """Send notification via email."""
        if not self.enabled or not self.to_addresses:
            logger.warning("Email channel disabled or no recipients")
            return False
        
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart()
            msg['From'] = self.from_address
            msg['To'] = ', '.join(self.to_addresses)
            msg['Subject'] = f"[{notification.severity.upper()}] {notification.alert_name}"
            
            body = self.format_message(notification)
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email notification sent to {len(self.to_addresses)} recipients")
            return True
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
            return False


class WebhookChannel(NotificationChannelBase):
    """Webhook notification channel."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.url = config.get("url")
        self.method = config.get("method", "POST")
        self.headers = config.get("headers", {})
        
    def send(self, notification: Notification) -> bool:
        """Send notification via webhook."""
        if not self.enabled or not self.url:
            logger.warning("Webhook channel disabled or not configured")
            return False
        
        try:
            payload = {
                "id": notification.id,
                "alert_id": notification.alert_id,
                "alert_name": notification.alert_name,
                "severity": notification.severity,
                "message": notification.message,
                "labels": notification.labels,
                "timestamp": notification.timestamp.isoformat(),
                "channel": notification.channel
            }
            
            response = requests.request(
                self.method,
                self.url,
                json=payload,
                headers=self.headers,
                timeout=10
            )
            
            success = response.status_code in [200, 201, 202, 204]
            if not success:
                logger.error(f"Webhook notification failed: {response.text}")
            
            return success
        except Exception as e:
            logger.error(f"Error sending webhook notification: {e}")
            return False


class NotificationManager:
    """Manage notification channels and send notifications."""
    
    def __init__(self):
        self.enabled = os.getenv("NOTIFICATION_CHANNELS_ENABLED", "false").lower() == "true"
        self.channels: Dict[str, NotificationChannelBase] = {}
        self.notification_history: List[Notification] = []
        self._load_default_channels()
        
        logger.info(f"Notification manager initialized (enabled={self.enabled})")
    
    def _load_default_channels(self) -> None:
        """Load default notification channels."""
        # Channels would be configured via environment variables or config
        pass
    
    def add_channel(self, channel_id: str, channel: NotificationChannelBase) -> None:
        """Add a notification channel."""
        self.channels[channel_id] = channel
        logger.info(f"Notification channel added: {channel_id}")
    
    def remove_channel(self, channel_id: str) -> bool:
        """Remove a notification channel."""
        if channel_id in self.channels:
            del self.channels[channel_id]
            logger.info(f"Notification channel removed: {channel_id}")
            return True
        return False
    
    def send_notification(self, notification: Notification, channel_ids: List[str] = None) -> Dict[str, bool]:
        """Send notification through specified channels."""
        if not self.enabled:
            logger.warning("Notification manager disabled")
            return {}
        
        if channel_ids is None:
            channel_ids = list(self.channels.keys())
        
        results = {}
        
        for channel_id in channel_ids:
            if channel_id not in self.channels:
                logger.warning(f"Channel not found: {channel_id}")
                results[channel_id] = False
                continue
            
            channel = self.channels[channel_id]
            success = channel.send(notification)
            results[channel_id] = success
            
            if success:
                notification.sent_at = datetime.now()
                notification.status = "sent"
            else:
                notification.status = "failed"
        
        self.notification_history.append(notification)
        return results
    
    def send_to_all_channels(self, notification: Notification) -> Dict[str, bool]:
        """Send notification to all enabled channels."""
        return self.send_notification(notification)
    
    def get_notification_history(self, limit: int = 100) -> List[Notification]:
        """Get notification history."""
        return self.notification_history[-limit:]
    
    def get_channel_stats(self) -> Dict[str, Any]:
        """Get channel statistics."""
        stats = {}
        
        for channel_id, channel in self.channels.items():
            history = [n for n in self.notification_history if n.channel == channel_id]
            stats[channel_id] = {
                "enabled": channel.enabled,
                "type": channel.channel_type,
                "total_sent": len([n for n in history if n.status == "sent"]),
                "total_failed": len([n for n in history if n.status == "failed"])
            }
        
        return stats
    
    def get_stats(self) -> Dict[str, Any]:
        """Get notification manager statistics."""
        return {
            "enabled": self.enabled,
            "total_channels": len(self.channels),
            "total_notifications": len(self.notification_history),
            "successful_notifications": len([n for n in self.notification_history if n.status == "sent"]),
            "failed_notifications": len([n for n in self.notification_history if n.status == "failed"]),
            "channel_stats": self.get_channel_stats()
        }


# Global notification manager instance
_global_notification_manager: Optional[NotificationManager] = None


def get_notification_manager() -> NotificationManager:
    """Get the global notification manager instance."""
    global _global_notification_manager
    if _global_notification_manager is None:
        _global_notification_manager = NotificationManager()
    return _global_notification_manager
