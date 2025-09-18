"""
Async Health Check Endpoints
Provides comprehensive health monitoring for all async services
and components in the application.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
import psutil
import socket

from app.core.async_database import get_async_db, AsyncSession, database_manager
from app.services.async_http_client import get_http_client, HttpClientMetrics
from app.services.async_file_service import file_service
from app.services.async_task_scheduler import task_scheduler
from app.services.async_logging_service import logging_service
from app.dependencies.async_services import service_container, check_service_health
from app.core.async_error_handling import (
    error_handler, retry_handler, cancellation_manager,
    get_error_handling_health
)

router = APIRouter(tags=["health"])

class HealthStatus:
    """Health status constants"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

@router.get("/health")
async def basic_health_check() -> Dict[str, Any]:
    """Basic health check endpoint"""
    return {
        "status": HealthStatus.HEALTHY,
        "timestamp": datetime.utcnow().isoformat(),
        "service": "trading-signals-frontend",
        "version": "1.0.0"
    }

@router.get("/health/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """Detailed health check for all components"""
    start_time = time.time()

    # Check all components in parallel
    health_checks = await asyncio.gather(
        _check_database_health(),
        _check_http_client_health(),
        _check_file_service_health(),
        _check_task_scheduler_health(),
        _check_logging_service_health(),
        _check_dependency_injection_health(),
        _check_error_handling_health(),
        _check_system_health(),
        return_exceptions=True
    )

    # Process results
    component_health = {}
    overall_status = HealthStatus.HEALTHY

    for i, result in enumerate(health_checks):
        component_name = [
            "database", "http_client", "file_service", "task_scheduler",
            "logging_service", "dependency_injection", "error_handling", "system"
        ][i]

        if isinstance(result, Exception):
            component_health[component_name] = {
                "status": HealthStatus.UNHEALTHY,
                "error": str(result)
            }
            overall_status = HealthStatus.UNHEALTHY
        else:
            component_health[component_name] = result
            if result["status"] == HealthStatus.UNHEALTHY:
                overall_status = HealthStatus.UNHEALTHY
            elif result["status"] == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                overall_status = HealthStatus.DEGRADED

    response_time = time.time() - start_time

    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat(),
        "response_time_ms": round(response_time * 1000, 2),
        "components": component_health,
        "summary": {
            "total_components": len(component_health),
            "healthy_components": sum(1 for c in component_health.values() if c["status"] == HealthStatus.HEALTHY),
            "degraded_components": sum(1 for c in component_health.values() if c["status"] == HealthStatus.DEGRADED),
            "unhealthy_components": sum(1 for c in component_health.values() if c["status"] == HealthStatus.UNHEALTHY)
        }
    }

@router.get("/health/database")
async def database_health_check() -> Dict[str, Any]:
    """Database health check"""
    return await _check_database_health()

@router.get("/health/http-client")
async def http_client_health_check() -> Dict[str, Any]:
    """HTTP client health check"""
    return await _check_http_client_health()

@router.get("/health/file-service")
async def file_service_health_check() -> Dict[str, Any]:
    """File service health check"""
    return await _check_file_service_health()

@router.get("/health/task-scheduler")
async def task_scheduler_health_check() -> Dict[str, Any]:
    """Task scheduler health check"""
    return await _check_task_scheduler_health()

@router.get("/health/logging-service")
async def logging_service_health_check() -> Dict[str, Any]:
    """Logging service health check"""
    return await _check_logging_service_health()

@router.get("/health/dependency-injection")
async def dependency_injection_health_check() -> Dict[str, Any]:
    """Dependency injection health check"""
    return await _check_dependency_injection_health()

@router.get("/health/error-handling")
async def error_handling_health_check() -> Dict[str, Any]:
    """Error handling health check"""
    return await _check_error_handling_health()

@router.get("/health/system")
async def system_health_check() -> Dict[str, Any]:
    """System health check"""
    return await _check_system_health()

@router.get("/health/metrics")
async def health_metrics() -> Dict[str, Any]:
    """Get health metrics over time"""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "metrics": {
            "database": await _get_database_metrics(),
            "http_client": await _get_http_client_metrics(),
            "task_scheduler": await _get_task_scheduler_metrics(),
            "error_handling": await _get_error_handling_metrics(),
            "system": await _get_system_metrics()
        }
    }

@router.get("/health/ready")
async def readiness_check() -> Dict[str, Any]:
    """Readiness check - is the application ready to serve traffic?"""
    start_time = time.time()

    # Check critical components
    critical_checks = await asyncio.gather(
        _check_database_health(),
        _check_dependency_injection_health(),
        return_exceptions=True
    )

    ready = all(
        not isinstance(check, Exception) and check["status"] == HealthStatus.HEALTHY
        for check in critical_checks
    )

    response_time = time.time() - start_time

    return {
        "ready": ready,
        "timestamp": datetime.utcnow().isoformat(),
        "response_time_ms": round(response_time * 1000, 2),
        "checks": {
            "database": critical_checks[0] if not isinstance(critical_checks[0], Exception) else {"status": HealthStatus.UNHEALTHY},
            "dependency_injection": critical_checks[1] if not isinstance(critical_checks[1], Exception) else {"status": HealthStatus.UNHEALTHY}
        }
    }

@router.get("/health/live")
async def liveness_check() -> Dict[str, Any]:
    """Liveness check - is the application running?"""
    return {
        "alive": True,
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": int(time.time() - psutil.boot_time())
    }

# Health check implementations
async def _check_database_health() -> Dict[str, Any]:
    """Check database health"""
    start_time = time.time()

    try:
        # Test database connection
        async with get_async_db() as db:
            result = await db.execute("SELECT 1")
            await db.commit()

        # Get database manager health
        db_health = database_manager.get_health_info()

        response_time = time.time() - start_time

        return {
            "status": HealthStatus.HEALTHY if db_health["healthy"] else HealthStatus.DEGRADED,
            "response_time_ms": round(response_time * 1000, 2),
            "details": db_health
        }

    except Exception as e:
        return {
            "status": HealthStatus.UNHEALTHY,
            "error": str(e),
            "response_time_ms": round((time.time() - start_time) * 1000, 2)
        }

async def _check_http_client_health() -> Dict[str, Any]:
    """Check HTTP client health"""
    start_time = time.time()

    try:
        # Get HTTP client metrics
        metrics = HttpClientMetrics.get_global_metrics()

        # Test HTTP client with a simple request
        client = get_http_client("health_check")
        response = await client.get("https://httpbin.org/get", timeout=5.0)

        response_time = time.time() - start_time

        return {
            "status": HealthStatus.HEALTHY,
            "response_time_ms": round(response_time * 1000, 2),
            "details": {
                "total_requests": metrics["total_requests"],
                "success_rate": metrics["success_rate"],
                "average_response_time": metrics["average_response_time_ms"],
                "active_connections": metrics["active_connections"]
            }
        }

    except Exception as e:
        return {
            "status": HealthStatus.UNHEALTHY,
            "error": str(e),
            "response_time_ms": round((time.time() - start_time) * 1000, 2)
        }

async def _check_file_service_health() -> Dict[str, Any]:
    """Check file service health"""
    start_time = time.time()

    try:
        # Test file service operations
        test_content = "Health check test content"
        test_file = "/tmp/health_check.txt"

        # Test write
        write_result = await file_service.write_file(test_file, test_content)

        # Test read
        read_result = await file_service.read_file(test_file)

        # Test delete
        delete_result = await file_service.delete_file(test_file)

        response_time = time.time() - start_time

        return {
            "status": HealthStatus.HEALTHY,
            "response_time_ms": round(response_time * 1000, 2),
            "details": {
                "cache_size": len(file_service._cache),
                "cache_hits": file_service._cache_hits,
                "cache_misses": file_service._cache_misses,
                "operations_successful": all([
                    write_result.success,
                    read_result.success,
                    delete_result.success
                ])
            }
        }

    except Exception as e:
        return {
            "status": HealthStatus.UNHEALTHY,
            "error": str(e),
            "response_time_ms": round((time.time() - start_time) * 1000, 2)
        }

async def _check_task_scheduler_health() -> Dict[str, Any]:
    """Check task scheduler health"""
    start_time = time.time()

    try:
        # Get scheduler metrics
        metrics = task_scheduler.get_metrics()

        # Test scheduling a simple task
        test_task = await task_scheduler.schedule_task(
            "health_check_test",
            lambda: "test_result",
            priority=10,
            schedule_immediately=True
        )

        # Wait for task completion
        await asyncio.sleep(0.1)

        response_time = time.time() - start_time

        return {
            "status": HealthStatus.HEALTHY,
            "response_time_ms": round(response_time * 1000, 2),
            "details": {
                "active_tasks": metrics["active_tasks"],
                "completed_tasks": metrics["completed_tasks"],
                "failed_tasks": metrics["failed_tasks"],
                "queue_size": metrics["queue_size"],
                "scheduler_running": task_scheduler.is_running()
            }
        }

    except Exception as e:
        return {
            "status": HealthStatus.UNHEALTHY,
            "error": str(e),
            "response_time_ms": round((time.time() - start_time) * 1000, 2)
        }

async def _check_logging_service_health() -> Dict[str, Any]:
    """Check logging service health"""
    start_time = time.time()

    try:
        # Test logging service
        await logging_service.log_event("health_check_test", {"status": "testing"})

        # Get metrics
        metrics = logging_service.get_metrics()

        response_time = time.time() - start_time

        return {
            "status": HealthStatus.HEALTHY,
            "response_time_ms": round(response_time * 1000, 2),
            "details": {
                "events_logged": metrics["events_logged"],
                "errors_logged": metrics["errors_logged"],
                "alerts_triggered": metrics["alerts_triggered"],
                "buffer_size": metrics["buffer_size"]
            }
        }

    except Exception as e:
        return {
            "status": HealthStatus.UNHEALTHY,
            "error": str(e),
            "response_time_ms": round((time.time() - start_time) * 1000, 2)
        }

async def _check_dependency_injection_health() -> Dict[str, Any]:
    """Check dependency injection health"""
    start_time = time.time()

    try:
        # Get service health
        service_health = await check_service_health()

        response_time = time.time() - start_time

        return {
            "status": HealthStatus.HEALTHY if service_health["container_healthy"] else HealthStatus.DEGRADED,
            "response_time_ms": round(response_time * 1000, 2),
            "details": service_health
        }

    except Exception as e:
        return {
            "status": HealthStatus.UNHEALTHY,
            "error": str(e),
            "response_time_ms": round((time.time() - start_time) * 1000, 2)
        }

async def _check_error_handling_health() -> Dict[str, Any]:
    """Check error handling health"""
    start_time = time.time()

    try:
        # Get error handling health
        error_health = await get_error_handling_health()

        response_time = time.time() - start_time

        return {
            "status": HealthStatus.HEALTHY,
            "response_time_ms": round(response_time * 1000, 2),
            "details": error_health
        }

    except Exception as e:
        return {
            "status": HealthStatus.UNHEALTHY,
            "error": str(e),
            "response_time_ms": round((time.time() - start_time) * 1000, 2)
        }

async def _check_system_health() -> Dict[str, Any]:
    """Check system health"""
    start_time = time.time()

    try:
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        response_time = time.time() - start_time

        # Determine status based on resource usage
        if cpu_percent > 90 or memory.percent > 90 or disk.percent > 90:
            status = HealthStatus.DEGRADED
        else:
            status = HealthStatus.HEALTHY

        return {
            "status": status,
            "response_time_ms": round(response_time * 1000, 2),
            "details": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None,
                "process_count": len(psutil.pids()),
                "network_connections": len(psutil.net_connections())
            }
        }

    except Exception as e:
        return {
            "status": HealthStatus.UNHEALTHY,
            "error": str(e),
            "response_time_ms": round((time.time() - start_time) * 1000, 2)
        }

# Metrics collection implementations
async def _get_database_metrics() -> Dict[str, Any]:
    """Get database metrics"""
    try:
        db_health = database_manager.get_health_info()
        return {
            "connection_pool_size": db_health.get("pool_size", 0),
            "active_connections": db_health.get("active_connections", 0),
            "healthy": db_health.get("healthy", False)
        }
    except Exception:
        return {"error": "Unable to get database metrics"}

async def _get_http_client_metrics() -> Dict[str, Any]:
    """Get HTTP client metrics"""
    try:
        metrics = HttpClientMetrics.get_global_metrics()
        return {
            "total_requests": metrics["total_requests"],
            "success_rate": metrics["success_rate"],
            "average_response_time_ms": metrics["average_response_time_ms"],
            "active_connections": metrics["active_connections"]
        }
    except Exception:
        return {"error": "Unable to get HTTP client metrics"}

async def _get_task_scheduler_metrics() -> Dict[str, Any]:
    """Get task scheduler metrics"""
    try:
        metrics = task_scheduler.get_metrics()
        return {
            "active_tasks": metrics["active_tasks"],
            "completed_tasks": metrics["completed_tasks"],
            "failed_tasks": metrics["failed_tasks"],
            "queue_size": metrics["queue_size"]
        }
    except Exception:
        return {"error": "Unable to get task scheduler metrics"}

async def _get_error_handling_metrics() -> Dict[str, Any]:
    """Get error handling metrics"""
    try:
        error_stats = error_handler.get_error_stats()
        return {
            "total_errors": sum(stats["count"] for stats in error_stats.values()),
            "error_categories": len(error_stats),
            "circuit_breakers": len(error_handler.circuit_breakers),
            "active_operations": len(cancellation_manager.active_operations)
        }
    except Exception:
        return {"error": "Unable to get error handling metrics"}

async def _get_system_metrics() -> Dict[str, Any]:
    """Get system metrics"""
    try:
        return {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None,
            "network_io": psutil.net_io_counters()._asdict() if psutil.net_io_counters() else None,
            "disk_io": psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else None
        }
    except Exception:
        return {"error": "Unable to get system metrics"}

# Health check utilities
def get_health_status_overview(component_health: Dict[str, Any]) -> str:
    """Get overall health status from component health"""
    statuses = [health["status"] for health in component_health.values()]

    if HealthStatus.UNHEALTHY in statuses:
        return HealthStatus.UNHEALTHY
    elif HealthStatus.DEGRADED in statuses:
        return HealthStatus.DEGRADED
    elif HealthStatus.HEALTHY in statuses:
        return HealthStatus.HEALTHY
    else:
        return HealthStatus.UNKNOWN

def format_health_response(health_data: Dict[str, Any]) -> Dict[str, Any]:
    """Format health response for consistent output"""
    return {
        "status": health_data["status"],
        "timestamp": health_data["timestamp"],
        "response_time_ms": health_data.get("response_time_ms", 0),
        "details": health_data.get("details", {}),
        "checks": health_data.get("checks", {})
    }