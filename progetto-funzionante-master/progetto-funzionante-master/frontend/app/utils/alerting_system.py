"""
Comprehensive Alerting System for FastAPI Applications
Multi-channel notifications, intelligent alert classification, and escalation policies
"""

import asyncio
import json
import smtplib
from datetime import datetime, UTC, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import logging
import threading
import time
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod

import aiohttp
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from app.core.sentry_config import sentry_config, ErrorSeverity, ErrorCategory
from app.utils.performance_monitor import performance_monitor
from config.settings import settings


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertCategory(Enum):
    """Alert categories"""
    SYSTEM = "system"
    PERFORMANCE = "performance"
    SECURITY = "security"
    BUSINESS = "business"
    DEPLOYMENT = "deployment"
    EXTERNAL_SERVICE = "external_service"


@dataclass
class Alert:
    """Alert data structure"""
    id: str
    title: str
    message: str
    severity: AlertSeverity
    category: AlertCategory
    timestamp: str
    source: str
    tags: Dict[str, str]
    metadata: Dict[str, Any]
    resolved: bool = False
    resolved_at: Optional[str] = None
    resolved_by: Optional[str] = None
    escalation_count: int = 0
    notifications_sent: List[str] = None

    def __post_init__(self):
        if self.notifications_sent is None:
            self.notifications_sent = []


class NotificationChannel(ABC):
    """Abstract base class for notification channels"""

    @abstractmethod
    async def send_alert(self, alert: Alert) -> bool:
        """Send alert through this channel"""
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test connection to notification channel"""
        pass


class EmailNotificationChannel(NotificationChannel):
    """Email notification channel"""

    def __init__(self, smtp_host: str, smtp_port: int, username: str, password: str,
                 use_tls: bool = True, recipients: List[str] = None):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.recipients = recipients or []

    async def send_alert(self, alert: Alert) -> bool:
        """Send alert via email"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = ', '.join(self.recipients)
            msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.title}"

            # Create HTML body
            html_content = self._create_html_email(alert)
            msg.attach(MIMEText(html_content, 'html'))

            # Send email
            await self._send_email(msg)
            return True
        except Exception as e:
            logging.error(f"Failed to send email alert: {e}")
            return False

    def _create_html_email(self, alert: Alert) -> str:
        """Create HTML email content"""
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; margin: 20px;">
            <div style="background-color: {'#ff4444' if alert.severity == AlertSeverity.CRITICAL else '#ffaa00' if alert.severity == AlertSeverity.ERROR else '#ffaa00' if alert.severity == AlertSeverity.WARNING else '#4444ff'}; color: white; padding: 10px; border-radius: 5px;">
                <h2 style="margin: 0;">{alert.title}</h2>
                <p style="margin: 5px 0;"><strong>Severity:</strong> {alert.severity.value.upper()}</p>
                <p style="margin: 5px 0;"><strong>Category:</strong> {alert.category.value.replace('_', ' ').title()}</p>
                <p style="margin: 5px 0;"><strong>Time:</strong> {alert.timestamp}</p>
            </div>

            <div style="margin: 20px 0;">
                <h3>Message</h3>
                <p>{alert.message}</p>
            </div>

            <div style="margin: 20px 0;">
                <h3>Details</h3>
                <table style="border-collapse: collapse; width: 100%;">
                    <tr style="background-color: #f2f2f2;">
                        <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Source</th>
                        <td style="padding: 8px; border: 1px solid #ddd;">{alert.source}</td>
                    </tr>
                    <tr>
                        <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Alert ID</th>
                        <td style="padding: 8px; border: 1px solid #ddd;">{alert.id}</td>
                    </tr>
                </table>
            </div>

            {self._render_tags(alert.tags)}
            {self._render_metadata(alert.metadata)}

            <div style="margin-top: 20px; padding: 10px; background-color: #f9f9f9; border-left: 4px solid #007bff;">
                <p><em>This alert was generated by the Trading Signals System monitoring.</em></p>
            </div>
        </body>
        </html>
        """

    def _render_tags(self, tags: Dict[str, str]) -> str:
        """Render tags in email"""
        if not tags:
            return ""

        return f"""
        <div style="margin: 20px 0;">
            <h3>Tags</h3>
            <div>
                {' '.join(f'<span style="background-color: #e9ecef; padding: 4px 8px; margin: 2px; border-radius: 3px; font-size: 12px;">{k}: {v}</span>' for k, v in tags.items())}
            </div>
        </div>
        """

    def _render_metadata(self, metadata: Dict[str, Any]) -> str:
        """Render metadata in email"""
        if not metadata:
            return ""

        return f"""
        <div style="margin: 20px 0;">
            <h3>Additional Information</h3>
            <pre style="background-color: #f8f9fa; padding: 10px; border-radius: 3px; font-size: 12px;">{json.dumps(metadata, indent=2, default=str)}</pre>
        </div>
        """

    async def _send_email(self, msg: MIMEMultipart) -> None:
        """Send email using SMTP"""
        # This would need to be implemented with async SMTP
        # For now, using synchronous SMTP in a thread executor
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._send_sync_email, msg)

    def _send_sync_email(self, msg: MIMEMultipart) -> None:
        """Send email synchronously"""
        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            if self.use_tls:
                server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)

    async def test_connection(self) -> bool:
        """Test email connection"""
        try:
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
            return True
        except Exception as e:
            logging.error(f"Email connection test failed: {e}")
            return False


class SlackNotificationChannel(NotificationChannel):
    """Slack notification channel"""

    def __init__(self, slack_token: str, channel: str):
        self.client = WebClient(token=slack_token)
        self.channel = channel

    async def send_alert(self, alert: Alert) -> bool:
        """Send alert to Slack"""
        try:
            # Determine color based on severity
            color = {
                AlertSeverity.CRITICAL: "#ff0000",
                AlertSeverity.ERROR: "#ff4444",
                AlertSeverity.WARNING: "#ffaa00",
                AlertSeverity.INFO: "#36a64f"
            }.get(alert.severity, "#36a64f")

            # Create blocks for rich message
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🚨 {alert.title}",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Severity:* {alert.severity.value.upper()}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Category:* {alert.category.value.replace('_', ' ').title()}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Time:* <!date^{int(datetime.fromisoformat(alert.timestamp.replace('Z', '+00:00')).timestamp())}^{alert.timestamp}|{alert.timestamp}>"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Source:* {alert.source}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Message:*\n{alert.message}"
                    }
                }
            ]

            # Add tags if present
            if alert.tags:
                tags_text = "\n".join(f"• {k}: {v}" for k, v in alert.tags.items())
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Tags:*\n{tags_text}"
                    }
                })

            # Add metadata if present
            if alert.metadata:
                metadata_text = f"```{json.dumps(alert.metadata, indent=2, default=str)}```"
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Additional Info:*\n{metadata_text}"
                    }
                })

            # Send message
            response = self.client.chat_postMessage(
                channel=self.channel,
                text=alert.title,  # Fallback text
                blocks=blocks,
                attachments=[
                    {
                        "color": color,
                        "footer": f"Alert ID: {alert.id}",
                        "ts": int(datetime.fromisoformat(alert.timestamp.replace('Z', '+00:00')).timestamp())
                    }
                ]
            )

            return response["ok"]
        except SlackApiError as e:
            logging.error(f"Failed to send Slack alert: {e}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error sending Slack alert: {e}")
            return False

    async def test_connection(self) -> bool:
        """Test Slack connection"""
        try:
            response = self.client.auth_test()
            return response["ok"]
        except Exception as e:
            logging.error(f"Slack connection test failed: {e}")
            return False


class AlertManager:
    """
    Comprehensive alert management system
    - Intelligent alert classification and routing
    - Escalation policies
    - Alert aggregation and deduplication
    - Multi-channel notifications
    """

    def __init__(self):
        self.alerts: Dict[str, Alert] = {}
        self.channels: Dict[str, NotificationChannel] = {}
        self.rules: List[AlertRule] = []
        self.escalation_policies: Dict[str, EscalationPolicy] = {}
        self.alert_history: List[Alert] = []
        self.lock = threading.Lock()
        self.running = False

    def add_channel(self, name: str, channel: NotificationChannel) -> None:
        """Add notification channel"""
        self.channels[name] = channel

    def add_rule(self, rule: 'AlertRule') -> None:
        """Add alert rule"""
        self.rules.append(rule)

    def add_escalation_policy(self, name: str, policy: 'EscalationPolicy') -> None:
        """Add escalation policy"""
        self.escalation_policies[name] = policy

    def create_alert(self, title: str, message: str, severity: AlertSeverity,
                    category: AlertCategory, source: str, tags: Dict[str, str] = None,
                    metadata: Dict[str, Any] = None) -> Alert:
        """Create new alert"""
        alert_id = f"alert_{int(time.time() * 1000)}_{hash(title + message) % 10000}"

        alert = Alert(
            id=alert_id,
            title=title,
            message=message,
            severity=severity,
            category=category,
            timestamp=datetime.now(UTC).isoformat(),
            source=source,
            tags=tags or {},
            metadata=metadata or {}
        )

        with self.lock:
            self.alerts[alert_id] = alert
            self.alert_history.append(alert)

        # Process alert
        asyncio.create_task(self._process_alert(alert))

        return alert

    async def _process_alert(self, alert: Alert) -> None:
        """Process alert through rules and send notifications"""
        try:
            # Check for duplicate alerts
            if self._is_duplicate_alert(alert):
                logging.info(f"Duplicate alert detected: {alert.id}")
                return

            # Apply alert rules
            for rule in self.rules:
                if rule.matches(alert):
                    await rule.apply(alert)

            # Send notifications
            await self._send_notifications(alert)

            # Check for escalation
            await self._check_escalation(alert)

            # Log to Sentry
            sentry_config.capture_message(
                f"Alert: {alert.title}",
                level=ErrorSeverity.WARNING if alert.severity in [AlertSeverity.WARNING, AlertSeverity.INFO] else ErrorSeverity.ERROR,
                category=ErrorCategory.SYSTEM,
                tags={"alert_id": alert.id, "alert_severity": alert.severity.value},
                extra_data=asdict(alert)
            )

        except Exception as e:
            logging.error(f"Error processing alert {alert.id}: {e}")

    def _is_duplicate_alert(self, alert: Alert) -> bool:
        """Check if alert is a duplicate"""
        # Simple duplicate detection based on title and recent time
        recent_time = datetime.now(UTC) - timedelta(minutes=5)
        recent_alerts = [a for a in self.alert_history if datetime.fromisoformat(a.timestamp.replace('Z', '+00:00')) > recent_time]

        return any(
            a.title == alert.title and
            a.message == alert.message and
            a.severity == alert.severity
            for a in recent_alerts
        )

    async def _send_notifications(self, alert: Alert) -> None:
        """Send alert through configured channels"""
        for channel_name, channel in self.channels.items():
            try:
                success = await channel.send_alert(alert)
                if success:
                    alert.notifications_sent.append(channel_name)
                    logging.info(f"Alert {alert.id} sent to {channel_name}")
                else:
                    logging.error(f"Failed to send alert {alert.id} to {channel_name}")
            except Exception as e:
                logging.error(f"Error sending alert {alert.id} to {channel_name}: {e}")

    async def _check_escalation(self, alert: Alert) -> None:
        """Check if alert needs escalation"""
        # This would implement escalation logic based on time, severity, etc.
        # For now, just a placeholder
        pass

    def resolve_alert(self, alert_id: str, resolved_by: str) -> bool:
        """Resolve an alert"""
        with self.lock:
            if alert_id not in self.alerts:
                return False

            alert = self.alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.now(UTC).isoformat()
            alert.resolved_by = resolved_by

            # Send resolution notification
            asyncio.create_task(self._send_resolution_notification(alert))

            return True

    async def _send_resolution_notification(self, alert: Alert) -> None:
        """Send alert resolution notification"""
        resolution_alert = Alert(
            id=f"{alert.id}_resolved",
            title=f"RESOLVED: {alert.title}",
            message=f"Alert resolved by {alert.resolved_by}",
            severity=AlertSeverity.INFO,
            category=AlertCategory.SYSTEM,
            timestamp=datetime.now(UTC).isoformat(),
            source="alert_manager",
            tags={"original_alert_id": alert.id, "status": "resolved"},
            metadata={"original_alert": asdict(alert)}
        )

        await self._send_notifications(resolution_alert)

    def get_active_alerts(self) -> List[Alert]:
        """Get all active (unresolved) alerts"""
        with self.lock:
            return [alert for alert in self.alerts.values() if not alert.resolved]

    def get_alert_summary(self) -> Dict[str, Any]:
        """Get alert summary for dashboard"""
        with self.lock:
            active_alerts = self.get_active_alerts()

            return {
                "total_alerts": len(self.alerts),
                "active_alerts": len(active_alerts),
                "resolved_alerts": len(self.alerts) - len(active_alerts),
                "alerts_by_severity": self._count_by_severity(active_alerts),
                "alerts_by_category": self._count_by_category(active_alerts),
                "recent_alerts": sorted(active_alerts, key=lambda x: x.timestamp, reverse=True)[:10]
            }

    def _count_by_severity(self, alerts: List[Alert]) -> Dict[str, int]:
        """Count alerts by severity"""
        counts = {severity.value: 0 for severity in AlertSeverity}
        for alert in alerts:
            counts[alert.severity.value] += 1
        return counts

    def _count_by_category(self, alerts: List[Alert]) -> Dict[str, int]:
        """Count alerts by category"""
        counts = {category.value: 0 for category in AlertCategory}
        for alert in alerts:
            counts[alert.category.value] += 1
        return counts


class AlertRule:
    """Alert rule for processing and modifying alerts"""

    def __init__(self, name: str, condition: Callable[[Alert], bool],
                 actions: List[Callable[[Alert], None]] = None):
        self.name = name
        self.condition = condition
        self.actions = actions or []

    def matches(self, alert: Alert) -> bool:
        """Check if rule matches alert"""
        return self.condition(alert)

    async def apply(self, alert: Alert) -> None:
        """Apply rule actions to alert"""
        for action in self.actions:
            try:
                if asyncio.iscoroutinefunction(action):
                    await action(alert)
                else:
                    action(alert)
            except Exception as e:
                logging.error(f"Error applying rule {self.name} action: {e}")


class EscalationPolicy:
    """Escalation policy for alerts"""

    def __init__(self, name: str, levels: List[Dict[str, Any]]):
        self.name = name
        self.levels = levels

    def should_escalate(self, alert: Alert) -> bool:
        """Check if alert should be escalated"""
        # Implement escalation logic
        return False

    def get_next_level(self, alert: Alert) -> Dict[str, Any]:
        """Get next escalation level"""
        # Implement escalation level logic
        return {}


# Global alert manager instance
alert_manager = AlertManager()