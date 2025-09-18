"""
Security Monitoring and Logging Module

Provides comprehensive security event monitoring and logging including:
- Structured security logging
- Real-time event monitoring
- Alert generation
- Security metrics collection
- Anomaly detection
- Log aggregation and analysis
- Compliance reporting
- Incident response workflows

"""

import logging
import json
import time
import asyncio
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque
import hashlib
import psutil
import socket
import uuid
from pathlib import Path
import aiofiles
from fastapi import Request, Response, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class SecurityEventType(Enum):
    """Security event types"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    INPUT_VALIDATION = "input_validation"
    RATE_LIMITING = "rate_limiting"
    FILE_ACCESS = "file_access"
    DATABASE_ACCESS = "database_access"
    NETWORK_SECURITY = "network_security"
    MALWARE_DETECTION = "malware_detection"
    INTEGRITY_VIOLATION = "integrity_violation"
    SESSION_MANAGEMENT = "session_management"
    CONFIGURATION_CHANGE = "configuration_change"
    SYSTEM_ERROR = "system_error"
    SECURITY_POLICY_VIOLATION = "security_policy_violation"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    INCIDENT = "incident"

class SecuritySeverity(Enum):
    """Security event severity levels"""
    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    INFO = 4

class AlertStatus(Enum):
    """Alert status"""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"

@dataclass
class SecurityEvent:
    """Security event data structure"""
    event_id: str
    event_type: SecurityEventType
    severity: SecuritySeverity
    timestamp: datetime
    source_ip: str
    user_agent: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None
    description: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    investigation_notes: List[str] = field(default_factory=list)

@dataclass
class SecurityAlert:
    """Security alert data structure"""
    alert_id: str
    event_id: str
    alert_type: str
    severity: SecuritySeverity
    status: AlertStatus
    created_at: datetime
    updated_at: datetime
    description: str
    details: Dict[str, Any] = field(default_factory=dict)
    assigned_to: Optional[str] = None
    resolution_notes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SecurityMetrics:
    """Security metrics data structure"""
    timestamp: datetime
    total_events: int
    events_by_type: Dict[SecurityEventType, int]
    events_by_severity: Dict[SecuritySeverity, int]
    unique_sources: int
    blocked_requests: int
    failed_authentications: int
    successful_authentications: int
    rate_limit_violations: int
    malware_detections: int
    integrity_violations: int
    system_load: float
    memory_usage: float
    response_times: List[float]

class AnomalyDetector:
    """Anomaly detection for security events"""

    def __init__(self):
        self.event_history = deque(maxlen=10000)
        self.ip_patterns = defaultdict(list)
        self.user_patterns = defaultdict(list)
        self.resource_patterns = defaultdict(list)
        self.time_windows = defaultdict(list)
        self.baseline_metrics = {}
        self.anomaly_thresholds = {
            'failed_auth_rate': 0.1,  # 10% failed auth rate
            'request_rate': 100,  # requests per minute
            'error_rate': 0.05,  # 5% error rate
            'unique_ips_per_minute': 50,
            'payload_size_anomaly': 10.0  # standard deviations
        }

    def add_event(self, event: SecurityEvent):
        """Add event to anomaly detection"""
        self.event_history.append(event)
        self._update_patterns(event)
        self._check_anomalies(event)

    def _update_patterns(self, event: SecurityEvent):
        """Update pattern tracking"""
        # IP patterns
        self.ip_patterns[event.source_ip].append(event)

        # User patterns
        if event.user_id:
            self.user_patterns[event.user_id].append(event)

        # Resource patterns
        if event.resource:
            self.resource_patterns[event.resource].append(event)

        # Time window patterns
        time_window = event.timestamp.replace(second=0, microsecond=0)
        self.time_windows[time_window].append(event)

    def _check_anomalies(self, event: SecurityEvent):
        """Check for anomalies in current event"""
        anomalies = []

        # Check authentication failure rate
        if event.event_type == SecurityEventType.AUTHENTICATION:
            auth_events = [e for e in self.event_history if e.event_type == SecurityEventType.AUTHENTICATION]
            recent_auths = [e for e in auth_events if (event.timestamp - e.timestamp).seconds < 300]

            failed_count = sum(1 for e in recent_auths if 'failed' in e.description.lower())
            if len(recent_auths) > 0 and failed_count / len(recent_auths) > self.anomaly_thresholds['failed_auth_rate']:
                anomalies.append(f"High authentication failure rate: {failed_count}/{len(recent_auths)}")

        # Check request rate
        time_window = event.timestamp.replace(second=0, microsecond=0)
        window_events = self.time_windows.get(time_window, [])
        if len(window_events) > self.anomaly_thresholds['request_rate']:
            anomalies.append(f"High request rate: {len(window_events)} requests per minute")

        # Check for unusual IPs
        recent_events = [e for e in self.event_history if (event.timestamp - e.timestamp).seconds < 60]
        unique_ips = set(e.source_ip for e in recent_events)
        if len(unique_ips) > self.anomaly_thresholds['unique_ips_per_minute']:
            anomalies.append(f"Unusual number of unique IPs: {len(unique_ips)}")

        return anomalies

    def get_anomalies(self) -> List[Dict[str, Any]]:
        """Get current anomalies"""
        anomalies = []

        # Check for recent unusual patterns
        current_time = datetime.utcnow()

        # IP-based anomalies
        for ip, events in self.ip_patterns.items():
            recent_events = [e for e in events if (current_time - e.timestamp).seconds < 300]
            if len(recent_events) > 100:  # More than 100 events in 5 minutes
                anomalies.append({
                    'type': 'high_activity_ip',
                    'ip': ip,
                    'event_count': len(recent_events),
                    'time_window': '5 minutes'
                })

        # User-based anomalies
        for user_id, events in self.user_patterns.items():
            recent_events = [e for e in events if (current_time - e.timestamp).seconds < 300]
            if len(recent_events) > 50:  # More than 50 events in 5 minutes
                anomalies.append({
                    'type': 'high_activity_user',
                    'user_id': user_id,
                    'event_count': len(recent_events),
                    'time_window': '5 minutes'
                })

        return anomalies

class SecurityEventLogger:
    """Structured security event logger"""

    def __init__(self, log_file: str = "security_events.log"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        # Configure structured logging
        self.logger = logging.getLogger('security_events')
        self.logger.setLevel(logging.INFO)

        # File handler
        handler = logging.FileHandler(self.log_file)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        # Event buffer for real-time processing
        self.event_buffer = deque(maxlen=1000)
        self.event_callbacks = []

    def log_event(self, event: SecurityEvent):
        """Log security event"""
        # Add to buffer
        self.event_buffer.append(event)

        # Log to file
        log_entry = {
            'event_id': event.event_id,
            'event_type': event.event_type.value,
            'severity': event.severity.name,
            'timestamp': event.timestamp.isoformat(),
            'source_ip': event.source_ip,
            'user_id': event.user_id,
            'resource': event.resource,
            'action': event.action,
            'description': event.description,
            'details': event.details,
            'tags': event.tags
        }

        self.logger.info(json.dumps(log_entry))

        # Trigger callbacks
        for callback in self.event_callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Error in event callback: {e}")

    def add_event_callback(self, callback: Callable[[SecurityEvent], None]):
        """Add callback for event processing"""
        self.event_callbacks.append(callback)

    def get_recent_events(self, minutes: int = 60) -> List[SecurityEvent]:
        """Get recent events"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        return [event for event in self.event_buffer if event.timestamp > cutoff_time]

class SecurityMetricsCollector:
    """Security metrics collection"""

    def __init__(self):
        self.metrics_history = deque(maxlen=1000)
        self.current_metrics = None
        self.collection_interval = 60  # seconds

    def collect_metrics(self, events: List[SecurityEvent]) -> SecurityMetrics:
        """Collect security metrics"""
        current_time = datetime.utcnow()

        # Count events by type
        events_by_type = defaultdict(int)
        events_by_severity = defaultdict(int)

        for event in events:
            events_by_type[event.event_type] += 1
            events_by_severity[event.severity] += 1

        # Get system metrics
        system_metrics = self._get_system_metrics()

        # Create metrics object
        metrics = SecurityMetrics(
            timestamp=current_time,
            total_events=len(events),
            events_by_type=dict(events_by_type),
            events_by_severity=dict(events_by_severity),
            unique_sources=len(set(event.source_ip for event in events)),
            blocked_requests=events_by_type.get(SecurityEventType.RATE_LIMITING, 0),
            failed_authentications=sum(
                1 for event in events
                if event.event_type == SecurityEventType.AUTHENTICATION and 'failed' in event.description.lower()
            ),
            successful_authentications=sum(
                1 for event in events
                if event.event_type == SecurityEventType.AUTHENTICATION and 'success' in event.description.lower()
            ),
            rate_limit_violations=events_by_type.get(SecurityEventType.RATE_LIMITING, 0),
            malware_detections=events_by_type.get(SecurityEventType.MALWARE_DETECTION, 0),
            integrity_violations=events_by_type.get(SecurityEventType.INTEGRITY_VIOLATION, 0),
            system_load=system_metrics['cpu_percent'],
            memory_usage=system_metrics['memory_percent'],
            response_times=[]  # Will be populated from request tracking
        )

        self.metrics_history.append(metrics)
        self.current_metrics = metrics

        return metrics

    def _get_system_metrics(self) -> Dict[str, float]:
        """Get system metrics"""
        try:
            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'network_sent': psutil.net_io_counters().bytes_sent,
                'network_recv': psutil.net_io_counters().bytes_recv
            }
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {
                'cpu_percent': 0.0,
                'memory_percent': 0.0,
                'disk_percent': 0.0,
                'network_sent': 0,
                'network_recv': 0
            }

    def get_metrics_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get metrics summary for specified time period"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        relevant_metrics = [m for m in self.metrics_history if m.timestamp > cutoff_time]

        if not relevant_metrics:
            return {}

        summary = {
            'time_period_hours': hours,
            'total_events': sum(m.total_events for m in relevant_metrics),
            'avg_system_load': sum(m.system_load for m in relevant_metrics) / len(relevant_metrics),
            'avg_memory_usage': sum(m.memory_usage for m in relevant_metrics) / len(relevant_metrics),
            'peak_system_load': max(m.system_load for m in relevant_metrics),
            'peak_memory_usage': max(m.memory_usage for m in relevant_metrics),
            'total_blocked_requests': sum(m.blocked_requests for m in relevant_metrics),
            'total_failed_authentications': sum(m.failed_authentications for m in relevant_metrics),
            'total_malware_detections': sum(m.malware_detections for m in relevant_metrics),
            'total_integrity_violations': sum(m.integrity_violations for m in relevant_metrics),
            'unique_sources': len(set(event.source_ip for m in relevant_metrics for event in m.events_by_type)),
            'event_types': {}
        }

        # Aggregate event types
        for metrics in relevant_metrics:
            for event_type, count in metrics.events_by_type.items():
                summary['event_types'][event_type.value] = summary['event_types'].get(event_type.value, 0) + count

        return summary

class SecurityAlertManager:
    """Security alert management"""

    def __init__(self):
        self.alerts = {}
        self.alert_rules = self._load_alert_rules()
        self.alert_callbacks = []

    def _load_alert_rules(self) -> List[Dict[str, Any]]:
        """Load alert rules"""
        return [
            {
                'name': 'High Failed Authentication Rate',
                'condition': lambda events: self._check_failed_auth_rate(events),
                'severity': SecuritySeverity.HIGH,
                'threshold': 10,  # 10 failed auths in 5 minutes
                'time_window': 300  # 5 minutes
            },
            {
                'name': 'Multiple Rate Limit Violations',
                'condition': lambda events: self._check_rate_limit_violations(events),
                'severity': SecuritySeverity.MEDIUM,
                'threshold': 50,  # 50 rate limit violations in 10 minutes
                'time_window': 600  # 10 minutes
            },
            {
                'name': 'Malware Detection',
                'condition': lambda events: self._check_malware_detections(events),
                'severity': SecuritySeverity.CRITICAL,
                'threshold': 1,  # Any malware detection
                'time_window': 3600  # 1 hour
            },
            {
                'name': 'Integrity Violation',
                'condition': lambda events: self._check_integrity_violations(events),
                'severity': SecuritySeverity.CRITICAL,
                'threshold': 1,  # Any integrity violation
                'time_window': 3600  # 1 hour
            },
            {
                'name': 'Unusual IP Activity',
                'condition': lambda events: self._check_unusual_ip_activity(events),
                'severity': SecuritySeverity.MEDIUM,
                'threshold': 100,  # 100 events from single IP in 5 minutes
                'time_window': 300  # 5 minutes
            }
        ]

    def _check_failed_auth_rate(self, events: List[SecurityEvent]) -> bool:
        """Check for high failed authentication rate"""
        current_time = datetime.utcnow()
        recent_events = [
            e for e in events
            if (current_time - e.timestamp).seconds < 300 and
            e.event_type == SecurityEventType.AUTHENTICATION and
            'failed' in e.description.lower()
        ]
        return len(recent_events) >= 10

    def _check_rate_limit_violations(self, events: List[SecurityEvent]) -> bool:
        """Check for multiple rate limit violations"""
        current_time = datetime.utcnow()
        recent_events = [
            e for e in events
            if (current_time - e.timestamp).seconds < 600 and
            e.event_type == SecurityEventType.RATE_LIMITING
        ]
        return len(recent_events) >= 50

    def _check_malware_detections(self, events: List[SecurityEvent]) -> bool:
        """Check for malware detections"""
        current_time = datetime.utcnow()
        recent_events = [
            e for e in events
            if (current_time - e.timestamp).seconds < 3600 and
            e.event_type == SecurityEventType.MALWARE_DETECTION
        ]
        return len(recent_events) >= 1

    def _check_integrity_violations(self, events: List[SecurityEvent]) -> bool:
        """Check for integrity violations"""
        current_time = datetime.utcnow()
        recent_events = [
            e for e in events
            if (current_time - e.timestamp).seconds < 3600 and
            e.event_type == SecurityEventType.INTEGRITY_VIOLATION
        ]
        return len(recent_events) >= 1

    def _check_unusual_ip_activity(self, events: List[SecurityEvent]) -> bool:
        """Check for unusual IP activity"""
        current_time = datetime.utcnow()
        recent_events = [
            e for e in events
            if (current_time - e.timestamp).seconds < 300
        ]

        ip_counts = defaultdict(int)
        for event in recent_events:
            ip_counts[event.source_ip] += 1

        return any(count >= 100 for count in ip_counts.values())

    def process_events(self, events: List[SecurityEvent]) -> List[SecurityAlert]:
        """Process events and generate alerts"""
        alerts = []

        for rule in self.alert_rules:
            if rule['condition'](events):
                alert = self._create_alert(rule, events)
                alerts.append(alert)
                self.alerts[alert.alert_id] = alert

                # Trigger alert callbacks
                for callback in self.alert_callbacks:
                    try:
                        callback(alert)
                    except Exception as e:
                        logger.error(f"Error in alert callback: {e}")

        return alerts

    def _create_alert(self, rule: Dict[str, Any], events: List[SecurityEvent]) -> SecurityAlert:
        """Create alert from rule"""
        alert_id = f"alert_{uuid.uuid4().hex[:8]}"
        current_time = datetime.utcnow()

        return SecurityAlert(
            alert_id=alert_id,
            event_id=events[0].event_id if events else "",
            alert_type=rule['name'],
            severity=rule['severity'],
            status=AlertStatus.ACTIVE,
            created_at=current_time,
            updated_at=current_time,
            description=f"Alert triggered: {rule['name']}",
            details={
                'rule': rule['name'],
                'threshold': rule.get('threshold', 0),
                'time_window': rule.get('time_window', 0),
                'triggering_events': len([e for e in events if (current_time - e.timestamp).seconds < rule.get('time_window', 3600)])
            }
        )

    def add_alert_callback(self, callback: Callable[[SecurityAlert], None]):
        """Add callback for alert processing"""
        self.alert_callbacks.append(callback)

    def get_active_alerts(self) -> List[SecurityAlert]:
        """Get active alerts"""
        return [alert for alert in self.alerts.values() if alert.status == AlertStatus.ACTIVE]

    def acknowledge_alert(self, alert_id: str, user_id: str) -> bool:
        """Acknowledge alert"""
        if alert_id in self.alerts:
            self.alerts[alert_id].status = AlertStatus.ACKNOWLEDGED
            self.alerts[alert_id].updated_at = datetime.utcnow()
            self.alerts[alert_id].assigned_to = user_id
            return True
        return False

    def resolve_alert(self, alert_id: str, resolution_notes: str) -> bool:
        """Resolve alert"""
        if alert_id in self.alerts:
            self.alerts[alert_id].status = AlertStatus.RESOLVED
            self.alerts[alert_id].updated_at = datetime.utcnow()
            self.alerts[alert_id].resolution_notes.append(resolution_notes)
            return True
        return False

class SecurityMonitoringSystem:
    """
    Comprehensive security monitoring system

    Features:
    - Real-time event monitoring
    - Anomaly detection
    - Alert generation
    - Metrics collection
    - Compliance reporting
    - Incident response
    """

    def __init__(self):
        self.event_logger = SecurityEventLogger()
        self.anomaly_detector = AnomalyDetector()
        self.metrics_collector = SecurityMetricsCollector()
        self.alert_manager = SecurityAlertManager()

        # Monitoring state
        self.is_monitoring = False
        self.monitoring_thread = None
        self.monitoring_interval = 30  # seconds

        # Setup callbacks
        self._setup_callbacks()

        logger.info("SecurityMonitoringSystem initialized")

    def _setup_callbacks(self):
        """Setup event and alert callbacks"""
        # Event callback for anomaly detection
        self.event_logger.add_event_callback(self.anomaly_detector.add_event)

        # Event callback for metrics collection
        self.event_logger.add_event_callback(self._process_event_for_metrics)

        # Alert callback for notification
        self.alert_manager.add_alert_callback(self._handle_alert)

    def _process_event_for_metrics(self, event: SecurityEvent):
        """Process event for metrics collection"""
        # This will be processed during metrics collection interval
        pass

    def _handle_alert(self, alert: SecurityAlert):
        """Handle security alert"""
        logger.warning(f"Security alert generated: {alert.alert_type} - {alert.description}")

        # Send notification (could be extended with email, Slack, etc.)
        self._send_alert_notification(alert)

    def _send_alert_notification(self, alert: SecurityAlert):
        """Send alert notification"""
        # This is a placeholder - in production, integrate with notification services
        notification = {
            'type': 'security_alert',
            'alert_id': alert.alert_id,
            'severity': alert.severity.name,
            'message': alert.description,
            'timestamp': alert.created_at.isoformat()
        }

        logger.warning(f"Alert notification: {notification}")

    def log_security_event(self, event_type: SecurityEventType, severity: SecuritySeverity,
                          source_ip: str, description: str, **kwargs) -> str:
        """
        Log security event

        Args:
            event_type: Event type
            severity: Event severity
            source_ip: Source IP address
            description: Event description
            **kwargs: Additional event data

        Returns:
            str: Event ID
        """
        event_id = f"evt_{uuid.uuid4().hex[:8]}"

        event = SecurityEvent(
            event_id=event_id,
            event_type=event_type,
            severity=severity,
            timestamp=datetime.utcnow(),
            source_ip=source_ip,
            user_agent=kwargs.get('user_agent', ''),
            user_id=kwargs.get('user_id'),
            session_id=kwargs.get('session_id'),
            request_id=kwargs.get('request_id'),
            resource=kwargs.get('resource'),
            action=kwargs.get('action'),
            description=description,
            details=kwargs.get('details', {}),
            tags=kwargs.get('tags', []),
            metadata=kwargs.get('metadata', {})
        )

        self.event_logger.log_event(event)
        return event_id

    def start_monitoring(self):
        """Start security monitoring"""
        if self.is_monitoring:
            return

        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()

        logger.info("Security monitoring started")

    def stop_monitoring(self):
        """Stop security monitoring"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join()

        logger.info("Security monitoring stopped")

    def _monitoring_loop(self):
        """Monitoring loop"""
        while self.is_monitoring:
            try:
                # Collect recent events
                recent_events = self.event_logger.get_recent_events(minutes=5)

                # Process for alerts
                alerts = self.alert_manager.process_events(recent_events)

                # Collect metrics
                metrics = self.metrics_collector.collect_metrics(recent_events)

                # Check for anomalies
                anomalies = self.anomaly_detector.get_anomalies()

                # Sleep for interval
                time.sleep(self.monitoring_interval)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.monitoring_interval)

    def get_security_status(self) -> Dict[str, Any]:
        """Get current security status"""
        recent_events = self.event_logger.get_recent_events(minutes=60)
        active_alerts = self.alert_manager.get_active_alerts()
        anomalies = self.anomaly_detector.get_anomalies()
        current_metrics = self.metrics_collector.current_metrics

        return {
            'timestamp': datetime.utcnow().isoformat(),
            'monitoring_active': self.is_monitoring,
            'recent_events': len(recent_events),
            'active_alerts': len(active_alerts),
            'anomalies': len(anomalies),
            'current_metrics': asdict(current_metrics) if current_metrics else {},
            'system_health': self._get_system_health(),
            'recommendations': self._generate_recommendations()
        }

    def _get_system_health(self) -> Dict[str, Any]:
        """Get system health status"""
        try:
            return {
                'cpu_usage': psutil.cpu_percent(),
                'memory_usage': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent,
                'network_connections': len(psutil.net_connections()),
                'process_count': len(psutil.pids()),
                'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
            }
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return {}

    def _generate_recommendations(self) -> List[str]:
        """Generate security recommendations"""
        recommendations = []

        # Check for active alerts
        active_alerts = self.alert_manager.get_active_alerts()
        if active_alerts:
            recommendations.append(f"Address {len(active_alerts)} active security alerts")

        # Check for anomalies
        anomalies = self.anomaly_detector.get_anomalies()
        if anomalies:
            recommendations.append(f"Investigate {len(anomalies)} detected anomalies")

        # Check system resources
        current_metrics = self.metrics_collector.current_metrics
        if current_metrics:
            if current_metrics.system_load > 80:
                recommendations.append("High system load detected - consider scaling")
            if current_metrics.memory_usage > 80:
                recommendations.append("High memory usage detected - investigate memory leaks")

        # Check event rates
        recent_events = self.event_logger.get_recent_events(minutes=60)
        if len(recent_events) > 1000:
            recommendations.append("High event rate detected - review security policies")

        return recommendations

    def generate_compliance_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate compliance report"""
        metrics_summary = self.metrics_collector.get_metrics_summary(hours)
        recent_events = self.event_logger.get_recent_events(minutes=hours * 60)

        return {
            'report_period_hours': hours,
            'generated_at': datetime.utcnow().isoformat(),
            'summary': metrics_summary,
            'security_events': {
                'total': len(recent_events),
                'by_type': self._count_events_by_type(recent_events),
                'by_severity': self._count_events_by_severity(recent_events),
                'top_sources': self._get_top_sources(recent_events),
                'hourly_distribution': self._get_hourly_distribution(recent_events)
            },
            'compliance_status': self._check_compliance_status(recent_events),
            'recommendations': self._generate_compliance_recommendations(recent_events)
        }

    def _count_events_by_type(self, events: List[SecurityEvent]) -> Dict[str, int]:
        """Count events by type"""
        counts = defaultdict(int)
        for event in events:
            counts[event.event_type.value] += 1
        return dict(counts)

    def _count_events_by_severity(self, events: List[SecurityEvent]) -> Dict[str, int]:
        """Count events by severity"""
        counts = defaultdict(int)
        for event in events:
            counts[event.severity.name] += 1
        return dict(counts)

    def _get_top_sources(self, events: List[SecurityEvent]) -> List[Dict[str, Any]]:
        """Get top event sources"""
        source_counts = defaultdict(int)
        for event in events:
            source_counts[event.source_ip] += 1

        return [
            {'source': source, 'count': count}
            for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        ]

    def _get_hourly_distribution(self, events: List[SecurityEvent]) -> Dict[str, int]:
        """Get hourly distribution of events"""
        hourly_counts = defaultdict(int)
        for event in events:
            hour = event.timestamp.hour
            hourly_counts[f"{hour:02d}:00"] += 1
        return dict(hourly_counts)

    def _check_compliance_status(self, events: List[SecurityEvent]) -> Dict[str, Any]:
        """Check compliance status"""
        critical_events = [e for e in events if e.severity == SecuritySeverity.CRITICAL]
        high_events = [e for e in events if e.severity == SecuritySeverity.HIGH]

        return {
            'critical_events': len(critical_events),
            'high_events': len(high_events),
            'compliance_score': max(0, 100 - len(critical_events) * 10 - len(high_events) * 5),
            'issues_found': len(critical_events) + len(high_events),
            'passed_checks': len(events) - len(critical_events) - len(high_events)
        }

    def _generate_compliance_recommendations(self, events: List[SecurityEvent]) -> List[str]:
        """Generate compliance recommendations"""
        recommendations = []

        critical_events = [e for e in events if e.severity == SecuritySeverity.CRITICAL]
        if critical_events:
            recommendations.append(f"Address {len(critical_events)} critical security events")

        # Check for missing monitoring
        auth_events = [e for e in events if e.event_type == SecurityEventType.AUTHENTICATION]
        if not auth_events:
            recommendations.append("Enable authentication monitoring")

        # Check for rate limiting
        rate_limit_events = [e for e in events if e.event_type == SecurityEventType.RATE_LIMITING]
        if len(rate_limit_events) > 100:
            recommendations.append("Review rate limiting policies due to high violation count")

        return recommendations

class SecurityMonitoringMiddleware:
    """
    FastAPI middleware for security monitoring
    """

    def __init__(self, app, monitoring_system: SecurityMonitoringSystem):
        self.app = app
        self.monitoring_system = monitoring_system

        # Add middleware to FastAPI app
        self.app.middleware("http")(self.security_monitoring_middleware)

    async def security_monitoring_middleware(self, request: Request, call_next):
        """Security monitoring middleware"""
        start_time = time.time()
        request_id = f"req_{uuid.uuid4().hex[:8]}"

        # Extract request information
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        authorization = request.headers.get("authorization", "")

        # Log request start
        self.monitoring_system.log_security_event(
            event_type=SecurityEventType.NETWORK_SECURITY,
            severity=SecuritySeverity.INFO,
            source_ip=client_ip,
            description=f"Request started: {request.method} {request.url.path}",
            user_agent=user_agent,
            request_id=request_id,
            details={
                'method': request.method,
                'path': request.url.path,
                'query_params': dict(request.query_params),
                'has_authorization': bool(authorization)
            }
        )

        try:
            # Process request
            response = await call_next(request)

            # Calculate request duration
            duration = time.time() - start_time

            # Log request completion
            self.monitoring_system.log_security_event(
                event_type=SecurityEventType.NETWORK_SECURITY,
                severity=SecuritySeverity.INFO,
                source_ip=client_ip,
                description=f"Request completed: {request.method} {request.url.path}",
                user_agent=user_agent,
                request_id=request_id,
                details={
                    'method': request.method,
                    'path': request.url.path,
                    'status_code': response.status_code,
                    'duration_ms': round(duration * 1000, 2),
                    'response_size': len(response.body) if hasattr(response, 'body') else 0
                }
            )

            # Add security headers
            response.headers["X-Security-Monitoring"] = "enabled"
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration:.3f}s"

            return response

        except HTTPException as e:
            # Log HTTP exception
            self.monitoring_system.log_security_event(
                event_type=SecurityEventType.SYSTEM_ERROR,
                severity=SecuritySeverity.MEDIUM,
                source_ip=client_ip,
                description=f"HTTP Exception: {e.status_code} {e.detail}",
                user_agent=user_agent,
                request_id=request_id,
                details={
                    'status_code': e.status_code,
                    'error_detail': e.detail,
                    'duration_ms': round((time.time() - start_time) * 1000, 2)
                }
            )
            raise

        except Exception as e:
            # Log unexpected error
            self.monitoring_system.log_security_event(
                event_type=SecurityEventType.SYSTEM_ERROR,
                severity=SecuritySeverity.HIGH,
                source_ip=client_ip,
                description=f"Unexpected error: {str(e)}",
                user_agent=user_agent,
                request_id=request_id,
                details={
                    'error_type': type(e).__name__,
                    'error_message': str(e),
                    'duration_ms': round((time.time() - start_time) * 1000, 2)
                }
            )
            raise

# Initialize global monitoring system
security_monitoring_system = SecurityMonitoringSystem()

# Example usage
if __name__ == "__main__":
    # Create monitoring system
    monitoring = SecurityMonitoringSystem()

    # Start monitoring
    monitoring.start_monitoring()

    # Log some test events
    monitoring.log_security_event(
        event_type=SecurityEventType.AUTHENTICATION,
        severity=SecuritySeverity.INFO,
        source_ip="192.168.1.1",
        description="User login successful",
        user_id="user123",
        details={'username': 'testuser'}
    )

    monitoring.log_security_event(
        event_type=SecurityEventType.RATE_LIMITING,
        severity=SecuritySeverity.MEDIUM,
        source_ip="192.168.1.2",
        description="Rate limit exceeded",
        details={'endpoint': '/api/login', 'limit': '100/hour'}
    )

    # Get security status
    status = monitoring.get_security_status()
    print(f"Security Status: {status}")

    # Generate compliance report
    report = monitoring.generate_compliance_report(hours=24)
    print(f"Compliance Report: {report}")

    print("Security monitoring system initialized")