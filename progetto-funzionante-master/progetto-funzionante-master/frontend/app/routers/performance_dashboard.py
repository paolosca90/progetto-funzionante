"""
Performance Monitoring Dashboard
Provides real-time performance metrics and monitoring for all async services
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi import Request
import psutil
import json

from app.core.async_database import database_manager
from app.services.async_http_client import HttpClientMetrics
from app.services.async_file_service import file_service
from app.services.async_task_scheduler import task_scheduler
from app.services.async_logging_service import logging_service
from app.dependencies.async_services import service_container
from app.core.async_error_handling import error_handler, retry_handler, cancellation_manager

router = APIRouter(tags=["performance"])

class PerformanceMetrics:
    """Container for performance metrics"""

    def __init__(self):
        self.start_time = time.time()
        self.request_count = 0
        self.response_times = []
        self.error_count = 0

    def add_request(self, response_time: float, is_error: bool = False):
        """Add a request to metrics"""
        self.request_count += 1
        self.response_times.append(response_time)
        if is_error:
            self.error_count += 1

        # Keep only last 1000 response times
        if len(self.response_times) > 1000:
            self.response_times = self.response_times[-1000:]

    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        if not self.response_times:
            return {
                "total_requests": self.request_count,
                "avg_response_time": 0,
                "min_response_time": 0,
                "max_response_time": 0,
                "p95_response_time": 0,
                "p99_response_time": 0,
                "error_rate": 0,
                "uptime_seconds": time.time() - self.start_time
            }

        sorted_times = sorted(self.response_times)
        p95_idx = int(len(sorted_times) * 0.95)
        p99_idx = int(len(sorted_times) * 0.99)

        return {
            "total_requests": self.request_count,
            "avg_response_time": sum(self.response_times) / len(self.response_times),
            "min_response_time": min(self.response_times),
            "max_response_time": max(self.response_times),
            "p95_response_time": sorted_times[p95_idx] if p95_idx < len(sorted_times) else sorted_times[-1],
            "p99_response_time": sorted_times[p99_idx] if p99_idx < len(sorted_times) else sorted_times[-1],
            "error_rate": self.error_count / self.request_count if self.request_count > 0 else 0,
            "uptime_seconds": time.time() - self.start_time
        }

# Global metrics instance
performance_metrics = PerformanceMetrics()

@router.get("/performance", response_class=HTMLResponse)
async def performance_dashboard():
    """Performance monitoring dashboard HTML page"""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Performance Dashboard - AI Trading System</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .metric-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .metric-title {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
            color: #333;
        }
        .metric-value {
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
        }
        .status-healthy { color: #28a745; }
        .status-degraded { color: #ffc107; }
        .status-unhealthy { color: #dc3545; }
        .chart-container {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .refresh-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin: 10px 0;
        }
        .refresh-btn:hover {
            background: #5a6fd8;
        }
        .log-entry {
            padding: 8px;
            margin: 4px 0;
            border-left: 3px solid #667eea;
            background: #f8f9fa;
            border-radius: 3px;
        }
        .log-error { border-left-color: #dc3545; }
        .log-warn { border-left-color: #ffc107; }
        .log-info { border-left-color: #17a2b8; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Performance Dashboard</h1>
        <p>Real-time monitoring of AI Trading System performance metrics</p>
        <button class="refresh-btn" onclick="refreshDashboard()">Refresh Dashboard</button>
        <span id="last-update">Last updated: Never</span>
    </div>

    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-title">System Status</div>
            <div id="system-status" class="metric-value status-healthy">Healthy</div>
        </div>
        <div class="metric-card">
            <div class="metric-title">Uptime</div>
            <div id="uptime" class="metric-value">0s</div>
        </div>
        <div class="metric-card">
            <div class="metric-title">Total Requests</div>
            <div id="total-requests" class="metric-value">0</div>
        </div>
        <div class="metric-card">
            <div class="metric-title">Avg Response Time</div>
            <div id="avg-response-time" class="metric-value">0ms</div>
        </div>
        <div class="metric-card">
            <div class="metric-title">Error Rate</div>
            <div id="error-rate" class="metric-value">0%</div>
        </div>
        <div class="metric-card">
            <div class="metric-title">CPU Usage</div>
            <div id="cpu-usage" class="metric-value">0%</div>
        </div>
        <div class="metric-card">
            <div class="metric-title">Memory Usage</div>
            <div id="memory-usage" class="metric-value">0%</div>
        </div>
        <div class="metric-card">
            <div class="metric-title">Active Tasks</div>
            <div id="active-tasks" class="metric-value">0</div>
        </div>
    </div>

    <div class="chart-container">
        <h3>Response Time Trend</h3>
        <canvas id="responseTimeChart" width="400" height="200"></canvas>
    </div>

    <div class="chart-container">
        <h3>System Resources</h3>
        <canvas id="resourcesChart" width="400" height="200"></canvas>
    </div>

    <div class="chart-container">
        <h3>Service Health</h3>
        <canvas id="healthChart" width="400" height="200"></canvas>
    </div>

    <div class="metric-card">
        <div class="metric-title">Recent Logs</div>
        <div id="recent-logs"></div>
    </div>

    <script>
        let responseTimeChart, resourcesChart, healthChart;
        let responseTimeData = [];
        let resourcesData = [];

        function initCharts() {
            // Response Time Chart
            const rtCtx = document.getElementById('responseTimeChart').getContext('2d');
            responseTimeChart = new Chart(rtCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Response Time (ms)',
                        data: [],
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });

            // Resources Chart
            const resCtx = document.getElementById('resourcesChart').getContext('2d');
            resourcesChart = new Chart(resCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'CPU %',
                        data: [],
                        borderColor: '#28a745',
                        backgroundColor: 'rgba(40, 167, 69, 0.1)',
                        tension: 0.4
                    }, {
                        label: 'Memory %',
                        data: [],
                        borderColor: '#ffc107',
                        backgroundColor: 'rgba(255, 193, 7, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100
                        }
                    }
                }
            });

            // Health Chart
            const healthCtx = document.getElementById('healthChart').getContext('2d');
            healthChart = new Chart(healthCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Healthy', 'Degraded', 'Unhealthy'],
                    datasets: [{
                        data: [0, 0, 0],
                        backgroundColor: ['#28a745', '#ffc107', '#dc3545']
                    }]
                },
                options: {
                    responsive: true
                }
            });
        }

        async function refreshDashboard() {
            try {
                const response = await fetch('/performance/metrics');
                const data = await response.json();

                updateMetrics(data);
                updateCharts(data);
                updateLastUpdateTime();
            } catch (error) {
                console.error('Error refreshing dashboard:', error);
            }
        }

        function updateMetrics(data) {
            document.getElementById('system-status').textContent = data.overall_status;
            document.getElementById('system-status').className = `metric-value status-${data.overall_status}`;

            document.getElementById('uptime').textContent = formatUptime(data.application.uptime_seconds);
            document.getElementById('total-requests').textContent = data.application.total_requests;
            document.getElementById('avg-response-time').textContent = `${data.application.avg_response_time.toFixed(2)}ms`;
            document.getElementById('error-rate').textContent = `${(data.application.error_rate * 100).toFixed(2)}%`;
            document.getElementById('cpu-usage').textContent = `${data.system.cpu_percent.toFixed(1)}%`;
            document.getElementById('memory-usage').textContent = `${data.system.memory_percent.toFixed(1)}%`;
            document.getElementById('active-tasks').textContent = data.scheduler.active_tasks;
        }

        function updateCharts(data) {
            const now = new Date().toLocaleTimeString();

            // Update response time chart
            if (responseTimeChart.data.labels.length > 20) {
                responseTimeChart.data.labels.shift();
                responseTimeChart.data.datasets[0].data.shift();
            }
            responseTimeChart.data.labels.push(now);
            responseTimeChart.data.datasets[0].data.push(data.application.avg_response_time);
            responseTimeChart.update();

            // Update resources chart
            if (resourcesChart.data.labels.length > 20) {
                resourcesChart.data.labels.shift();
                resourcesChart.data.datasets[0].data.shift();
                resourcesChart.data.datasets[1].data.shift();
            }
            resourcesChart.data.labels.push(now);
            resourcesChart.data.datasets[0].data.push(data.system.cpu_percent);
            resourcesChart.data.datasets[1].data.push(data.system.memory_percent);
            resourcesChart.update();

            // Update health chart
            const healthCounts = data.services.health_counts;
            healthChart.data.datasets[0].data = [
                healthCounts.healthy || 0,
                healthCounts.degraded || 0,
                healthCounts.unhealthy || 0
            ];
            healthChart.update();
        }

        function formatUptime(seconds) {
            const days = Math.floor(seconds / 86400);
            const hours = Math.floor((seconds % 86400) / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            const secs = seconds % 60;

            if (days > 0) return `${days}d ${hours}h ${minutes}m`;
            if (hours > 0) return `${hours}h ${minutes}m ${secs}s`;
            if (minutes > 0) return `${minutes}m ${secs}s`;
            return `${secs}s`;
        }

        function updateLastUpdateTime() {
            document.getElementById('last-update').textContent = `Last updated: ${new Date().toLocaleTimeString()}`;
        }

        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {
            initCharts();
            refreshDashboard();

            // Auto-refresh every 30 seconds
            setInterval(refreshDashboard, 30000);
        });
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

@router.get("/performance/metrics")
async def get_performance_metrics(
    period: str = Query("1h", description="Time period: 1h, 6h, 24h, 7d")
) -> Dict[str, Any]:
    """Get comprehensive performance metrics"""

    # Parse time period
    now = datetime.utcnow()
    if period == "1h":
        start_time = now - timedelta(hours=1)
    elif period == "6h":
        start_time = now - timedelta(hours=6)
    elif period == "24h":
        start_time = now - timedelta(days=1)
    elif period == "7d":
        start_time = now - timedelta(days=7)
    else:
        start_time = now - timedelta(hours=1)

    # Collect all metrics in parallel
    metrics_tasks = [
        _get_application_metrics(),
        _get_database_metrics(),
        _get_http_client_metrics(),
        _get_file_service_metrics(),
        _get_task_scheduler_metrics(),
        _get_logging_metrics(),
        _get_system_metrics(),
        _get_service_health_metrics(),
        _get_error_handling_metrics()
    ]

    metrics_results = await asyncio.gather(*metrics_tasks, return_exceptions=True)

    # Process results
    metrics = {}
    metric_names = [
        "application", "database", "http_client", "file_service",
        "task_scheduler", "logging", "system", "services", "error_handling"
    ]

    for i, result in enumerate(metrics_results):
        name = metric_names[i]
        if isinstance(result, Exception):
            metrics[name] = {"error": str(result)}
        else:
            metrics[name] = result

    # Calculate overall status
    overall_status = _calculate_overall_status(metrics)

    return {
        "timestamp": now.isoformat(),
        "period": period,
        "start_time": start_time.isoformat(),
        "overall_status": overall_status,
        "metrics": metrics,
        "health_counts": _calculate_health_counts(metrics)
    }

@router.get("/performance/application")
async def get_application_metrics() -> Dict[str, Any]:
    """Get application-specific performance metrics"""
    return await _get_application_metrics()

@router.get("/performance/database")
async def get_database_performance_metrics() -> Dict[str, Any]:
    """Get database performance metrics"""
    return await _get_database_metrics()

@router.get("/performance/http-client")
async def get_http_client_performance_metrics() -> Dict[str, Any]:
    """Get HTTP client performance metrics"""
    return await _get_http_client_metrics()

@router.get("/performance/system")
async def get_system_performance_metrics() -> Dict[str, Any]:
    """Get system performance metrics"""
    return await _get_system_metrics()

@router.get("/performance/alerts")
async def get_performance_alerts(
    severity: str = Query("medium", description="Alert severity: low, medium, high, critical")
) -> Dict[str, Any]:
    """Get performance alerts"""
    try:
        alerts = await logging_service.get_alerts(severity=severity)
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "severity": severity,
            "alerts": alerts,
            "count": len(alerts)
        }
    except Exception as e:
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "alerts": []
        }

@router.post("/performance/clear-metrics")
async def clear_performance_metrics() -> Dict[str, Any]:
    """Clear performance metrics (for testing)"""
    try:
        global performance_metrics
        performance_metrics = PerformanceMetrics()

        # Clear service-specific metrics
        HttpClientMetrics.clear_global_metrics()

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success",
            "message": "Performance metrics cleared"
        }
    except Exception as e:
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "error",
            "error": str(e)
        }

# Helper functions for collecting metrics
async def _get_application_metrics() -> Dict[str, Any]:
    """Get application-level metrics"""
    app_stats = performance_metrics.get_stats()

    return {
        "uptime_seconds": app_stats["uptime_seconds"],
        "total_requests": app_stats["total_requests"],
        "avg_response_time": app_stats["avg_response_time"],
        "min_response_time": app_stats["min_response_time"],
        "max_response_time": app_stats["max_response_time"],
        "p95_response_time": app_stats["p95_response_time"],
        "p99_response_time": app_stats["p99_response_time"],
        "error_rate": app_stats["error_rate"],
        "timestamp": datetime.utcnow().isoformat()
    }

async def _get_database_metrics() -> Dict[str, Any]:
    """Get database performance metrics"""
    try:
        db_health = database_manager.get_health_info()

        return {
            "healthy": db_health["healthy"],
            "pool_size": db_health["pool_size"],
            "active_connections": db_health["active_connections"],
            "idle_connections": db_health["idle_connections"],
            "connection_wait_time": db_health.get("connection_wait_time", 0),
            "total_queries": db_health.get("total_queries", 0),
            "slow_queries": db_health.get("slow_queries", 0),
            "avg_query_time": db_health.get("avg_query_time", 0),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {"error": str(e), "healthy": False}

async def _get_http_client_metrics() -> Dict[str, Any]:
    """Get HTTP client performance metrics"""
    try:
        metrics = HttpClientMetrics.get_global_metrics()

        return {
            "total_requests": metrics["total_requests"],
            "successful_requests": metrics["successful_requests"],
            "failed_requests": metrics["failed_requests"],
            "success_rate": metrics["success_rate"],
            "average_response_time_ms": metrics["average_response_time_ms"],
            "min_response_time_ms": metrics["min_response_time_ms"],
            "max_response_time_ms": metrics["max_response_time_ms"],
            "active_connections": metrics["active_connections"],
            "connection_pool_size": metrics["connection_pool_size"],
            "circuit_breaker_trips": metrics.get("circuit_breaker_trips", 0),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}

async def _get_file_service_metrics() -> Dict[str, Any]:
    """Get file service performance metrics"""
    try:
        cache_info = {
            "cache_size": len(file_service._cache),
            "cache_hits": file_service._cache_hits,
            "cache_misses": file_service._cache_misses,
            "hit_rate": file_service._cache_hits / (file_service._cache_hits + file_service._cache_misses) if (file_service._cache_hits + file_service._cache_misses) > 0 else 0
        }

        return {
            "cache": cache_info,
            "total_operations": file_service._cache_hits + file_service._cache_misses,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}

async def _get_task_scheduler_metrics() -> Dict[str, Any]:
    """Get task scheduler performance metrics"""
    try:
        metrics = task_scheduler.get_metrics()

        return {
            "active_tasks": metrics["active_tasks"],
            "completed_tasks": metrics["completed_tasks"],
            "failed_tasks": metrics["failed_tasks"],
            "queue_size": metrics["queue_size"],
            "scheduler_running": task_scheduler.is_running(),
            "avg_task_execution_time": metrics.get("avg_task_execution_time", 0),
            "max_task_execution_time": metrics.get("max_task_execution_time", 0),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}

async def _get_logging_metrics() -> Dict[str, Any]:
    """Get logging performance metrics"""
    try:
        metrics = logging_service.get_metrics()

        return {
            "events_logged": metrics["events_logged"],
            "errors_logged": metrics["errors_logged"],
            "alerts_triggered": metrics["alerts_triggered"],
            "buffer_size": metrics["buffer_size"],
            "avg_log_processing_time": metrics.get("avg_log_processing_time", 0),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}

async def _get_system_metrics() -> Dict[str, Any]:
    """Get system performance metrics"""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        return {
            "cpu_percent": cpu_percent,
            "cpu_count": psutil.cpu_count(),
            "memory_percent": memory.percent,
            "memory_used": memory.used,
            "memory_total": memory.total,
            "disk_percent": disk.percent,
            "disk_used": disk.used,
            "disk_total": disk.total,
            "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None,
            "network_io": psutil.net_io_counters()._asdict() if psutil.net_io_counters() else None,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}

async def _get_service_health_metrics() -> Dict[str, Any]:
    """Get service health metrics"""
    try:
        service_health = await service_container.get_services_info()

        return {
            "total_services": service_health["total_services"],
            "singleton_instances": service_health["singleton_instances"],
            "active_scopes": service_health["active_scopes"],
            "services": service_health["services"],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}

async def _get_error_handling_metrics() -> Dict[str, Any]:
    """Get error handling metrics"""
    try:
        error_stats = error_handler.get_error_stats()

        return {
            "error_categories": len(error_stats),
            "total_errors": sum(stats["count"] for stats in error_stats.values()),
            "circuit_breakers": len(error_handler.circuit_breakers),
            "active_operations": len(cancellation_manager.active_operations),
            "retry_attempts": sum(
                config.get("max_retries", 0) for config in retry_handler.retry_configs.values()
            ),
            "error_distribution": error_stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}

def _calculate_overall_status(metrics: Dict[str, Any]) -> str:
    """Calculate overall system status"""
    unhealthy_count = 0
    total_services = 0

    for component, data in metrics.items():
        if isinstance(data, dict) and "error" not in data:
            total_services += 1
            if component == "database" and not data.get("healthy", True):
                unhealthy_count += 1
            elif component == "system" and data.get("cpu_percent", 0) > 90:
                unhealthy_count += 1
            elif component == "system" and data.get("memory_percent", 0) > 90:
                unhealthy_count += 1

    if unhealthy_count == 0:
        return "healthy"
    elif unhealthy_count <= total_services * 0.3:
        return "degraded"
    else:
        return "unhealthy"

def _calculate_health_counts(metrics: Dict[str, Any]) -> Dict[str, int]:
    """Calculate health counts for dashboard"""
    counts = {"healthy": 0, "degraded": 0, "unhealthy": 0}

    for component, data in metrics.items():
        if isinstance(data, dict) and "error" not in data:
            if component == "database":
                counts["healthy" if data.get("healthy", True) else "unhealthy"] += 1
            elif component == "system":
                cpu = data.get("cpu_percent", 0)
                memory = data.get("memory_percent", 0)
                if cpu > 90 or memory > 90:
                    counts["degraded"] += 1
                else:
                    counts["healthy"] += 1
            else:
                counts["healthy"] += 1

    return counts

# Middleware for performance tracking
async def add_performance_middleware(request: Request, call_next):
    """Middleware to track performance metrics"""
    start_time = time.time()

    try:
        response = await call_next(request)
        response_time = time.time() - start_time

        # Add to performance metrics
        performance_metrics.add_request(
            response_time * 1000,  # Convert to milliseconds
            is_error=response.status_code >= 400
        )

        return response
    except Exception as e:
        response_time = time.time() - start_time
        performance_metrics.add_request(response_time * 1000, is_error=True)
        raise