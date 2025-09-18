"""
SLA (Service Level Agreement) Monitoring System
Monitor service levels, track compliance, and generate SLA reports
"""

import time
import threading
from datetime import datetime, UTC, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import json

from app.core.sentry_config import sentry_config, ErrorSeverity, ErrorCategory
from app.utils.performance_monitor import performance_monitor
from app.utils.alerting_system import alert_manager, AlertSeverity, AlertCategory
from config.settings import settings


class SLAMetricType(Enum):
    """SLA metric types"""
    UPTIME = "uptime"
    RESPONSE_TIME = "response_time"
    ERROR_RATE = "error_rate"
    AVAILABILITY = "availability"
    THROUGHPUT = "throughput"
    SATISFACTION = "satisfaction"


class SLAStatus(Enum):
    """SLA status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    VIOLATED = "violated"


@dataclass
class SLATarget:
    """SLA target definition"""
    metric_type: SLAMetricType
    target_value: float
    warning_threshold: float
    critical_threshold: float
    time_window: int  # in seconds
    description: str


@dataclass
class SLAMeasurement:
    """SLA measurement data"""
    timestamp: str
    metric_type: SLAMetricType
    value: float
    status: SLAStatus
    target_met: bool
    violation_reason: Optional[str] = None


@dataclass
class SLAReport:
    """SLA compliance report"""
    period_start: str
    period_end: str
    overall_compliance: float
    metrics_compliance: Dict[str, float]
    violations: List[Dict[str, Any]]
    recommendations: List[str]


class SLAMonitor:
    """
    Comprehensive SLA monitoring system
    - Real-time SLA compliance tracking
    - Automatic violation detection
    - SLA reporting and analytics
    - Performance against service level objectives
    """

    def __init__(self):
        self.targets: Dict[str, SLATarget] = {}
        self.measurements: List[SLAMeasurement] = []
        self.violations: List[Dict[str, Any]] = []
        self.compliance_history: List[Dict[str, Any]] = []
        self.lock = threading.Lock()
        self.monitoring_interval = 60  # seconds
        self.running = False

        # Define default SLA targets
        self._setup_default_targets()

    def _setup_default_targets(self) -> None:
        """Setup default SLA targets"""
        self.targets = {
            "uptime": SLATarget(
                metric_type=SLAMetricType.UPTIME,
                target_value=99.9,
                warning_threshold=99.5,
                critical_threshold=99.0,
                time_window=86400,  # 24 hours
                description="System uptime percentage"
            ),
            "response_time": SLATarget(
                metric_type=SLAMetricType.RESPONSE_TIME,
                target_value=0.5,  # 500ms
                warning_threshold=1.0,  # 1s
                critical_threshold=2.0,  # 2s
                time_window=300,  # 5 minutes
                description="Average response time"
            ),
            "error_rate": SLATarget(
                metric_type=SLAMetricType.ERROR_RATE,
                target_value=0.01,  # 1%
                warning_threshold=0.05,  # 5%
                critical_threshold=0.10,  # 10%
                time_window=3600,  # 1 hour
                description="Error rate percentage"
            ),
            "availability": SLATarget(
                metric_type=SLAMetricType.AVAILABILITY,
                target_value=99.5,
                warning_threshold=99.0,
                critical_threshold=98.0,
                time_window=86400,  # 24 hours
                description="Service availability percentage"
            ),
            "throughput": SLATarget(
                metric_type=SLAMetricType.THROUGHPUT,
                target_value=1000,  # requests per minute
                warning_threshold=800,
                critical_threshold=500,
                time_window=300,  # 5 minutes
                description="Requests per minute"
            )
        }

    def start_monitoring(self) -> None:
        """Start SLA monitoring"""
        if self.running:
            return

        self.running = True
        self._monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._monitoring_thread.start()

        logging.info("SLA monitoring started")

    def stop_monitoring(self) -> None:
        """Stop SLA monitoring"""
        self.running = False
        logging.info("SLA monitoring stopped")

    def _monitoring_loop(self) -> None:
        """Main monitoring loop"""
        while self.running:
            try:
                self._collect_measurements()
                self._check_violations()
                time.sleep(self.monitoring_interval)
            except Exception as e:
                logging.error(f"Error in SLA monitoring loop: {e}")
                time.sleep(self.monitoring_interval)

    def _collect_measurements(self) -> None:
        """Collect SLA measurements"""
        try:
            # Collect uptime measurement
            uptime = self._calculate_uptime()
            self._add_measurement("uptime", uptime)

            # Collect response time measurement
            response_time = self._get_average_response_time()
            self._add_measurement("response_time", response_time)

            # Collect error rate measurement
            error_rate = self._get_error_rate()
            self._add_measurement("error_rate", error_rate)

            # Collect availability measurement
            availability = self._calculate_availability()
            self._add_measurement("availability", availability)

            # Collect throughput measurement
            throughput = self._get_throughput()
            self._add_measurement("throughput", throughput)

        except Exception as e:
            logging.error(f"Error collecting SLA measurements: {e}")

    def _add_measurement(self, metric_name: str, value: float) -> None:
        """Add SLA measurement"""
        target = self.targets.get(metric_name)
        if not target:
            return

        # Determine status
        status = SLAStatus.HEALTHY
        violation_reason = None

        if value >= target.target_value:
            status = SLAStatus.HEALTHY
        elif value >= target.warning_threshold:
            status = SLAStatus.WARNING
            violation_reason = f"Warning: {metric_name} {value} below target {target.target_value}"
        elif value >= target.critical_threshold:
            status = SLAStatus.CRITICAL
            violation_reason = f"Critical: {metric_name} {value} below critical threshold {target.critical_threshold}"
        else:
            status = SLAStatus.VIOLATED
            violation_reason = f"SLA Violation: {metric_name} {value} below minimum {target.critical_threshold}"

        measurement = SLAMeasurement(
            timestamp=datetime.now(UTC).isoformat(),
            metric_type=target.metric_type,
            value=value,
            status=status,
            target_met=value >= target.target_value,
            violation_reason=violation_reason
        )

        with self.lock:
            self.measurements.append(measurement)
            # Keep only last 1000 measurements
            if len(self.measurements) > 1000:
                self.measurements = self.measurements[-1000:]

    def _calculate_uptime(self) -> float:
        """Calculate system uptime"""
        # This is a simplified version - in production, you'd track actual uptime
        return 99.95

    def _get_average_response_time(self) -> float:
        """Get average response time"""
        try:
            metrics = performance_monitor.get_performance_summary()
            return metrics.get("summary", {}).get("avg_response_time", 0.5)
        except Exception:
            return 0.5

    def _get_error_rate(self) -> float:
        """Get current error rate"""
        try:
            metrics = performance_monitor.get_performance_summary()
            error_rate = metrics.get("summary", {}).get("error_rate", 0.01)
            return error_rate * 100  # Convert to percentage
        except Exception:
            return 0.01

    def _calculate_availability(self) -> float:
        """Calculate service availability"""
        # This is a simplified version - in production, you'd track actual availability
        return 99.8

    def _get_throughput(self) -> float:
        """Get current throughput"""
        try:
            metrics = performance_monitor.get_performance_summary()
            # This would need to be calculated based on actual request counts
            return 950.0  # requests per minute
        except Exception:
            return 950.0

    def _check_violations(self) -> None:
        """Check for SLA violations and create alerts"""
        recent_measurements = [
            m for m in self.measurements
            if datetime.fromisoformat(m.timestamp) > datetime.now(UTC) - timedelta(minutes=5)
        ]

        for measurement in recent_measurements:
            if measurement.status in [SLAStatus.CRITICAL, SLAStatus.VIOLATED]:
                violation = {
                    "timestamp": measurement.timestamp,
                    "metric_type": measurement.metric_type.value,
                    "value": measurement.value,
                    "status": measurement.status.value,
                    "reason": measurement.violation_reason,
                    "notified": False
                }

                with self.lock:
                    # Check if this violation was already processed
                    existing_violation = next(
                        (v for v in self.violations if
                         v["metric_type"] == violation["metric_type"] and
                         v["status"] == violation["status"] and
                         datetime.fromisoformat(v["timestamp"]) > datetime.now(UTC) - timedelta(hours=1)),
                        None
                    )

                    if not existing_violation:
                        self.violations.append(violation)
                        self._send_violation_alert(violation)

    def _send_violation_alert(self, violation: Dict[str, Any]) -> None:
        """Send alert for SLA violation"""
        try:
            alert_manager.create_alert(
                title=f"SLA Violation - {violation['metric_type'].upper()}",
                message=f"SLA violation detected: {violation['reason']}",
                severity=AlertSeverity.ERROR if violation['status'] == 'violated' else AlertSeverity.WARNING,
                category=AlertCategory.SYSTEM,
                source="sla_monitor",
                tags={
                    "sla_violation": "true",
                    "metric_type": violation['metric_type'],
                    "violation_status": violation['status']
                },
                metadata=violation
            )

            # Mark as notified
            violation["notified"] = True

            # Send to Sentry
            if sentry_config.initialized:
                sentry_config.capture_message(
                    f"SLA Violation: {violation['metric_type']} - {violation['reason']}",
                    level=ErrorSeverity.ERROR,
                    category=ErrorCategory.SYSTEM,
                    tags={"sla_violation": "true", "metric_type": violation['metric_type']},
                    extra_data=violation
                )

        except Exception as e:
            logging.error(f"Failed to send SLA violation alert: {e}")

    def get_sla_status(self) -> Dict[str, Any]:
        """Get current SLA status"""
        with self.lock:
            recent_measurements = [
                m for m in self.measurements
                if datetime.fromisoformat(m.timestamp) > datetime.now(UTC) - timedelta(minutes=15)
            ]

            status_summary = {}
            overall_healthy = True

            for metric_name, target in self.targets.items():
                metric_measurements = [m for m in recent_measurements if m.metric_type == target.metric_type]
                if metric_measurements:
                    latest = metric_measurements[-1]
                    status_summary[metric_name] = {
                        "current_value": latest.value,
                        "status": latest.status.value,
                        "target": target.target_value,
                        "warning_threshold": target.warning_threshold,
                        "critical_threshold": target.critical_threshold,
                        "target_met": latest.target_met,
                        "violation_reason": latest.violation_reason
                    }

                    if latest.status in [SLAStatus.CRITICAL, SLAStatus.VIOLATED]:
                        overall_healthy = False

            return {
                "overall_status": "healthy" if overall_healthy else "degraded",
                "last_updated": datetime.now(UTC).isoformat(),
                "metrics": status_summary,
                "active_violations": len([v for v in self.violations if not v.get("resolved", False)]),
                "total_violations": len(self.violations)
            }

    def generate_sla_report(self, period_days: int = 30) -> SLAReport:
        """Generate SLA compliance report"""
        period_start = datetime.now(UTC) - timedelta(days=period_days)
        period_end = datetime.now(UTC)

        with self.lock:
            period_measurements = [
                m for m in self.measurements
                if period_start <= datetime.fromisoformat(m.timestamp) <= period_end
            ]

        # Calculate compliance for each metric
        metrics_compliance = {}
        for metric_name, target in self.targets.items():
            metric_measurements = [m for m in period_measurements if m.metric_type == target.metric_type]
            if metric_measurements:
                compliant_measurements = [m for m in metric_measurements if m.target_met]
                compliance_rate = len(compliant_measurements) / len(metric_measurements) * 100
                metrics_compliance[metric_name] = compliance_rate
            else:
                metrics_compliance[metric_name] = 0.0

        # Calculate overall compliance
        if metrics_compliance:
            overall_compliance = sum(metrics_compliance.values()) / len(metrics_compliance)
        else:
            overall_compliance = 0.0

        # Get violations in the period
        period_violations = [
            v for v in self.violations
            if period_start <= datetime.fromisoformat(v["timestamp"]) <= period_end
        ]

        # Generate recommendations
        recommendations = self._generate_recommendations(metrics_compliance, period_violations)

        return SLAReport(
            period_start=period_start.isoformat(),
            period_end=period_end.isoformat(),
            overall_compliance=overall_compliance,
            metrics_compliance=metrics_compliance,
            violations=period_violations,
            recommendations=recommendations
        )

    def _generate_recommendations(self, compliance: Dict[str, float], violations: List[Dict[str, Any]]) -> List[str]:
        """Generate SLA improvement recommendations"""
        recommendations = []

        # Check for low compliance metrics
        for metric, compliance_rate in compliance.items():
            if compliance_rate < 95:
                recommendations.append(f"Improve {metric} performance - current compliance: {compliance_rate:.1f}%")

        # Check for frequent violations
        violation_counts = {}
        for violation in violations:
            metric_type = violation['metric_type']
            violation_counts[metric_type] = violation_counts.get(metric_type, 0) + 1

        for metric_type, count in violation_counts.items():
            if count > 5:  # More than 5 violations in the period
                recommendations.append(f"Investigate frequent {metric_type} violations ({count} incidents)")

        # General recommendations
        if not recommendations:
            recommendations.append("SLA performance is good - continue monitoring")
        else:
            recommendations.append("Consider implementing automated alerts for SLA thresholds")

        return recommendations

    def resolve_violation(self, violation_id: str) -> bool:
        """Mark SLA violation as resolved"""
        with self.lock:
            for violation in self.violations:
                if violation.get("id") == violation_id:
                    violation["resolved"] = True
                    violation["resolved_at"] = datetime.now(UTC).isoformat()
                    return True
        return False

    def get_sla_targets(self) -> Dict[str, Any]:
        """Get current SLA targets"""
        return {
            metric_name: {
                "target_value": target.target_value,
                "warning_threshold": target.warning_threshold,
                "critical_threshold": target.critical_threshold,
                "time_window": target.time_window,
                "description": target.description
            }
            for metric_name, target in self.targets.items()
        }

    def update_sla_target(self, metric_name: str, target_value: float, warning_threshold: float, critical_threshold: float) -> bool:
        """Update SLA target"""
        if metric_name not in self.targets:
            return False

        self.targets[metric_name].target_value = target_value
        self.targets[metric_name].warning_threshold = warning_threshold
        self.targets[metric_name].critical_threshold = critical_threshold

        # Log the change
        if sentry_config.initialized:
            sentry_config.capture_message(
                f"SLA target updated: {metric_name}",
                level=ErrorSeverity.INFO,
                category=ErrorCategory.SYSTEM,
                tags={"sla_target_update": "true", "metric_name": metric_name},
                extra_data={
                    "metric_name": metric_name,
                    "new_target": target_value,
                    "new_warning": warning_threshold,
                    "new_critical": critical_threshold
                }
            )

        return True


# Global SLA monitor instance
sla_monitor = SLAMonitor()