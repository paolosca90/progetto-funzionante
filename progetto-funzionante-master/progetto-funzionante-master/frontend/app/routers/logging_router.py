"""
Comprehensive Logging Management API
Provides endpoints for log management, monitoring, and analytics.
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import asyncio

from ..core.logging_integration import get_logging_system, logging_health_check
from ..core.logging_config import get_logging_config, LoggingConfig
from ..core.logging_performance import get_performance_monitor
from ..core.logging_tracing import get_tracer
from ..core.logging_rotation import get_log_rotator, get_retention_manager
from ..core.logging_structured import get_logger, log_context

router = APIRouter(prefix="/api/logging", tags=["Logging Management"])
logger = get_logger(__name__)


@router.get("/health")
async def logging_health():
    """Logging system health check"""
    return await logging_health_check()


@router.get("/status")
async def logging_status():
    """Get comprehensive logging system status"""
    logging_system = get_logging_system()
    if not logging_system:
        raise HTTPException(status_code=503, detail="Logging system not initialized")

    return logging_system.get_system_status()


@router.get("/config")
async def get_logging_config_endpoint():
    """Get current logging configuration"""
    config = get_logging_config()
    return {
        "config": config.to_dict(),
        "timestamp": datetime.now().isoformat()
    }


@router.post("/config/reload")
async def reload_logging_config():
    """Reload logging configuration"""
    try:
        # This would reload configuration from environment or file
        config = get_logging_config()
        return {
            "status": "success",
            "message": "Logging configuration reloaded",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to reload logging config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_logging_metrics(
    hours: int = Query(24, description="Time range in hours"),
    category: Optional[str] = Query(None, description="Filter by category")
):
    """Get logging metrics and analytics"""
    try:
        monitor = get_performance_monitor()
        if not monitor:
            raise HTTPException(status_code=503, detail="Performance monitor not available")

        report = monitor.get_performance_report(hours)

        if category:
            # Filter metrics by category
            filtered_metrics = {}
            for metric_type, metrics in report["metrics_summary"].items():
                if isinstance(metrics, dict):
                    filtered_metrics[metric_type] = {
                        k: v for k, v in metrics.items()
                        if category.lower() in k.lower()
                    }

            report["metrics_summary"] = filtered_metrics

        return {
            "status": "success",
            "report": report,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get logging metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts")
async def get_logging_alerts(
    limit: int = Query(100, description="Maximum number of alerts"),
    severity: Optional[str] = Query(None, description="Filter by severity")
):
    """Get logging alerts and notifications"""
    try:
        monitor = get_performance_monitor()
        if not monitor:
            raise HTTPException(status_code=503, detail="Performance monitor not available")

        alerts = monitor.get_alert_history(limit)

        if severity:
            alerts = [alert for alert in alerts if alert.get("severity") == severity]

        return {
            "status": "success",
            "alerts": alerts,
            "total": len(alerts),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get logging alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rotate")
async def rotate_log_files(
    force: bool = Query(False, description="Force rotation even if not needed"),
    background_tasks: BackgroundTasks = None
):
    """Rotate log files"""
    try:
        logging_system = get_logging_system()
        if not logging_system:
            raise HTTPException(status_code=503, detail="Logging system not initialized")

        results = logging_system.rotate_all_logs(force)

        return {
            "status": "success",
            "results": results,
            "rotated_count": sum(1 for success in results.values() if success),
            "total_files": len(results),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to rotate log files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/cleanup")
async def cleanup_old_logs(background_tasks: BackgroundTasks = None):
    """Clean up old log files"""
    try:
        logging_system = get_logging_system()
        if not logging_system:
            raise HTTPException(status_code=503, detail="Logging system not initialized")

        result = logging_system.cleanup_old_logs()

        return {
            "status": "success",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to cleanup old logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search")
async def search_logs(
    query: str = Query(..., description="Search query"),
    start_time: Optional[datetime] = Query(None, description="Start time"),
    end_time: Optional[datetime] = Query(None, description="End time"),
    level: Optional[str] = Query(None, description="Log level filter"),
    limit: int = Query(100, description="Maximum results"),
    offset: int = Query(0, description="Offset for pagination")
):
    """Search logs (placeholder - would integrate with Elasticsearch)"""
    try:
        # This is a placeholder implementation
        # In a real implementation, this would query Elasticsearch or log database

        search_results = {
            "query": query,
            "results": [],
            "total": 0,
            "limit": limit,
            "offset": offset,
            "filters": {
                "start_time": start_time.isoformat() if start_time else None,
                "end_time": end_time.isoformat() if end_time else None,
                "level": level
            },
            "timestamp": datetime.now().isoformat()
        }

        return {
            "status": "success",
            "search": search_results,
            "message": "Log search requires Elasticsearch integration"
        }

    except Exception as e:
        logger.error(f"Failed to search logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/errors")
async def get_error_analytics(
    hours: int = Query(24, description="Time range in hours"),
    group_by: str = Query("type", description="Group by field (type, endpoint, user)")
):
    """Get error analytics and statistics"""
    try:
        monitor = get_performance_monitor()
        if not monitor:
            raise HTTPException(status_code=503, detail="Performance monitor not available")

        report = monitor.get_performance_report(hours)

        # Extract error-related metrics
        error_metrics = {}
        for category, metrics in report["metrics_summary"].items():
            if isinstance(metrics, dict):
                error_metrics[category] = {
                    k: v for k, v in metrics.items()
                    if "error" in k.lower() or "exception" in k.lower()
                }

        # Analyze error patterns
        error_patterns = []
        for insight in report.get("insights", []):
            if insight.get("type") == "error_analysis":
                error_patterns.append(insight)

        return {
            "status": "success",
            "time_range_hours": hours,
            "error_metrics": error_metrics,
            "error_patterns": error_patterns,
            "total_insights": len(error_patterns),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get error analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/performance")
async def get_performance_analytics(
    hours: int = Query(24, description="Time range in hours"),
    endpoint: Optional[str] = Query(None, description="Filter by endpoint")
):
    """Get performance analytics and statistics"""
    try:
        monitor = get_performance_monitor()
        if not monitor:
            raise HTTPException(status_code=503, detail="Performance monitor not available")

        report = monitor.get_performance_report(hours)

        # Filter by endpoint if specified
        if endpoint:
            filtered_insights = []
            for insight in report.get("insights", []):
                if endpoint.lower() in str(insight).lower():
                    filtered_insights.append(insight)
            report["insights"] = filtered_insights

        return {
            "status": "success",
            "time_range_hours": hours,
            "analytics": report,
            "endpoint_filter": endpoint,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get performance analytics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tracing/active")
async def get_active_traces():
    """Get currently active traces"""
    try:
        tracer = get_tracer()
        if not tracer:
            raise HTTPException(status_code=503, detail="Tracer not available")

        active_spans = tracer.get_active_spans()

        return {
            "status": "success",
            "active_spans": [span.to_dict() for span in active_spans],
            "active_count": len(active_spans),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get active traces: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tracing/stats")
async def get_tracing_stats():
    """Get tracing statistics"""
    try:
        tracer = get_tracer()
        if not tracer:
            raise HTTPException(status_code=503, detail="Tracer not available")

        stats = tracer.get_trace_stats()

        return {
            "status": "success",
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get tracing stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test/event")
async def log_test_event(
    event_type: str = Query("info", description="Event type"),
    message: str = Query("Test log event", description="Log message"),
    include_traceback: bool = Query(False, description="Include test exception")
):
    """Log a test event for debugging"""
    try:
        test_logger = get_logger("test")

        extra_data = {
            "test_event": True,
            "timestamp": datetime.now().isoformat(),
            "correlation_id": log_context.get_correlation_id()
        }

        if include_traceback:
            # Simulate an exception
            try:
                raise ValueError("This is a test exception")
            except Exception as e:
                test_logger.error(
                    message,
                    extra=extra_data,
                    exc_info=True
                )
        else:
            getattr(test_logger, event_type, test_logger.info)(message, extra=extra_data)

        return {
            "status": "success",
            "message": f"Test {event_type} event logged",
            "event_type": event_type,
            "include_traceback": include_traceback,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to log test event: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export")
async def export_logs(
    format: str = Query("json", description="Export format (json, csv)"),
    hours: int = Query(24, description="Time range in hours"),
    level: Optional[str] = Query(None, description="Log level filter")
):
    """Export logs (placeholder implementation)"""
    try:
        # This is a placeholder implementation
        # In a real implementation, this would query logs and export them

        export_info = {
            "format": format,
            "time_range_hours": hours,
            "level_filter": level,
            "estimated_size": "Unknown - requires log storage integration",
            "timestamp": datetime.now().isoformat()
        }

        return {
            "status": "success",
            "export": export_info,
            "message": "Log export requires log storage integration (Elasticsearch/Database)"
        }

    except Exception as e:
        logger.error(f"Failed to export logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard/summary")
async def get_dashboard_summary():
    """Get summary data for logging dashboard"""
    try:
        monitor = get_performance_monitor()
        tracer = get_tracer()
        rotator = get_log_rotator()

        # Get current metrics summary
        metrics_summary = {}
        if monitor:
            metrics_summary = monitor.get_performance_report(1)["metrics_summary"]

        # Get tracing stats
        tracing_stats = {}
        if tracer:
            tracing_stats = tracer.get_trace_stats()

        # Get rotation stats
        rotation_stats = {}
        if rotator:
            rotation_stats = rotator.get_stats().__dict__

        # Calculate health score
        health_score = self._calculate_health_score(metrics_summary, tracing_stats, rotation_stats)

        return {
            "status": "success",
            "dashboard": {
                "health_score": health_score,
                "metrics_summary": metrics_summary,
                "tracing_stats": tracing_stats,
                "rotation_stats": rotation_stats,
                "system_status": {
                    "logging_initialized": bool(get_logging_system()),
                    "performance_monitoring": bool(monitor),
                    "tracing_enabled": bool(tracer),
                    "log_rotation": bool(rotator)
                }
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get dashboard summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    def _calculate_health_score(self, metrics: Dict, tracing: Dict, rotation: Dict) -> float:
        """Calculate overall system health score"""
        score = 100.0

        # Deduct for error rates
        if metrics.get("counters", {}).get("http.errors_total", 0) > 0:
            score -= min(20, metrics["counters"]["http.errors_total"])

        # Deduct for slow requests
        slow_requests = metrics.get("timers", {}).get("http.request_duration", {}).get("count", 0)
        if slow_requests > 0:
            score -= min(15, slow_requests * 2)

        # Deduct for memory usage
        system_metrics = metrics.get("system_metrics", {})
        memory_usage = system_metrics.get("memory_usage_percent", 0)
        if memory_usage > 80:
            score -= min(10, (memory_usage - 80) / 2)

        # Deduct for CPU usage
        cpu_usage = system_metrics.get("cpu_usage_percent", 0)
        if cpu_usage > 70:
            score -= min(10, (cpu_usage - 70) / 3)

        # Add bonus for active tracing
        if tracing.get("active_spans", 0) > 0:
            score += 5

        return max(0, min(100, score))


@router.get("/compliance/audit")
async def get_compliance_audit_log(
    hours: int = Query(24, description="Time range in hours"),
    event_type: Optional[str] = Query(None, description="Filter by event type")
):
    """Get compliance and audit log entries"""
    try:
        config = get_logging_config()
        if not config.compliance.enabled:
            return {
                "status": "info",
                "message": "Compliance logging is not enabled",
                "timestamp": datetime.now().isoformat()
            }

        # This is a placeholder implementation
        # In a real implementation, this would query the audit log files or database

        audit_entries = []
        # Simulate some audit entries for demonstration
        for i in range(5):
            audit_entries.append({
                "timestamp": (datetime.now() - timedelta(hours=i)).isoformat(),
                "event_type": f"test_event_{i}",
                "user_id": "test_user",
                "action": f"test_action_{i}",
                "resource": f"/api/test/{i}",
                "result": "success",
                "ip_address": "127.0.0.1",
                "correlation_id": f"test_correlation_{i}"
            })

        if event_type:
            audit_entries = [entry for entry in audit_entries if event_type.lower() in entry["event_type"].lower()]

        return {
            "status": "success",
            "audit_entries": audit_entries,
            "total": len(audit_entries),
            "time_range_hours": hours,
            "event_type_filter": event_type,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Failed to get compliance audit log: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compliance/export")
async def export_compliance_logs(
    start_date: datetime = Query(..., description="Start date"),
    end_date: datetime = Query(..., description="End date"),
    format: str = Query("json", description="Export format")
):
    """Export compliance logs for auditing purposes"""
    try:
        config = get_logging_config()
        if not config.compliance.enabled:
            raise HTTPException(status_code=400, detail="Compliance logging is not enabled")

        # Validate date range
        if end_date < start_date:
            raise HTTPException(status_code=400, detail="End date must be after start date")

        # Validate date range is not too large (max 1 year)
        if (end_date - start_date).days > 365:
            raise HTTPException(status_code=400, detail="Date range cannot exceed 1 year")

        # This is a placeholder implementation
        export_info = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "format": format,
            "estimated_records": "Unknown - requires log storage integration",
            "compliance_fields": config.compliance.required_fields,
            "timestamp": datetime.now().isoformat()
        }

        return {
            "status": "success",
            "export": export_info,
            "message": "Compliance log export requires log storage integration"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export compliance logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))