"""
Refactored FastAPI Main Application with Async I/O Optimization
Clean architecture with proper separation of concerns and high-performance async operations
"""

from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi import Depends
from typing import Optional, Dict, Any, Union
import logging
from datetime import datetime
import os

# Import routers
from app.routers import (
    auth_router,
    signals_router,
    users_router,
    admin_router,
    api_router,
)
from app.routers.async_health import router as health_router
from app.routers.performance_dashboard import router as performance_router, add_performance_middleware
from app.routers.enhanced_auth_router import router as enhanced_auth_router
from app.routers.enhanced_signals_router import router as enhanced_signals_router

# Import unified configuration
from config.settings import settings

# Import configuration system
from config.config_system import config_manager
from config.startup_validator import validate_application_startup

# Import async database setup
from app.core.async_database import async_db_manager, init_async_database, cleanup_async_database, get_async_db
from database import engine, check_database_health
from models import Base

# Import enhanced OpenAPI documentation
from app.core.openapi_docs import custom_openapi, TAGS_METADATA, EXAMPLES
from app.core.api_versioning import APIVersioningMiddleware
from app.core.error_handling import error_handler, HTTP_STATUS_DOCUMENTATION, ERROR_RESPONSE_EXAMPLES
from app.core.documentation_generator import DocumentationGenerator
from app.core.openapi_tags import ENHANCED_TAGS_METADATA, get_openapi_extensions
from app.core.swagger_config import SwaggerUIEnhancer
from app.core.documentation_website import DocumentationWebsiteGenerator
from app.core.openapi_validation import validation_router, ValidationMiddleware
from app.core.api_testing import testing_router
from app.core.test_runner import test_runner_router

# Import optimized async services
from app.services.cache_service import init_cache, cleanup_cache, cache_service
from app.services.cache_warming import start_cache_warming, stop_cache_warming
from app.services.async_http_client import init_http_clients, cleanup_http_clients
from app.services.async_file_service import file_service, init_file_service
from app.services.async_task_scheduler import init_task_scheduler, cleanup_task_scheduler
from app.services.async_logging_service import init_logging_service, cleanup_logging_service, LogCategory
from app.dependencies.async_services import init_dependency_injection, cleanup_dependency_injection
from app.core.async_error_handling import init_error_handling, cleanup_error_handling

# Import Sentry error tracking and monitoring
from app.core.sentry_config import sentry_config
from app.middleware.error_tracking_middleware import ErrorTrackingMiddleware
from app.utils.performance_monitor import performance_monitor
from app.utils.alerting_system import alert_manager, AlertSeverity, AlertCategory
from app.utils.release_tracker import release_tracker
from app.utils.sla_monitor import sla_monitor
from app.utils.error_debugger import error_debugger

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize and validate configuration system
logger.info("Initializing configuration system...")
try:
    # Validate configuration at startup
    health_report = validate_application_startup(config_manager)
    logger.info(f"Configuration validation completed: {health_report.overall_status}")

    # Enable hot-reloading in development
    if config_manager.get('environment', 'development') == 'development':
        logger.info("Enabling configuration hot-reloading...")
        config_manager.enable_hot_reload([
            "config/*.yaml",
            ".env"
        ])
    else:
        logger.info("Configuration hot-reloading disabled in production")

except Exception as e:
    logger.error(f"Failed to initialize configuration system: {e}")
    raise

# Create database tables (sync fallback)
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app with enhanced configuration
app = FastAPI(
    title="AI Cash Revolution Trading API",
    description="""Professional AI-powered trading signals platform with OANDA integration and real-time market analysis.

## Features

### 🚀 AI-Powered Trading Signals
- Real-time signal generation using advanced AI algorithms
- Multi-timeframe technical analysis
- Risk management with dynamic position sizing
- Market sentiment analysis and pattern recognition

### 📊 Comprehensive Market Data
- Live OANDA market data integration
- Historical price data and analytics
- Technical indicators and volatility metrics
- Session-aware trading recommendations

### 🔒 Enterprise-Grade Security
- JWT token authentication
- API key management
- OAuth2 flows for third-party integration
- Comprehensive rate limiting and DDoS protection

### 📈 Performance Analytics
- Signal performance tracking
- Risk/reward ratio optimization
- Backtesting capabilities
- Real-time performance monitoring

### 🛠️ Developer Tools
- Interactive API documentation
- SDK generation for multiple languages
- Comprehensive error handling
- Webhook support for real-time updates

### 🔍 OpenAPI Validation & Testing
- Automated OpenAPI specification validation
- Real-time API testing and monitoring
- Compliance scoring and quality metrics
- Security vulnerability testing
- Load testing and performance benchmarking
- Interactive test dashboard with WebSocket support
- CI/CD integration capabilities

### 📋 Comprehensive Documentation
- Enhanced OpenAPI 3.0 specification
- Multi-language SDK generation (Python, JavaScript, Java)
- Interactive documentation website
- API versioning and migration guides
- Code examples and integration tutorials
""",
    version="2.0.1",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    openapi_tags=ENHANCED_TAGS_METADATA,
    contact={
        "name": "API Support",
        "email": "support@cash-revolution.com",
        "url": "https://www.cash-revolution.com/support"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    },
    servers=[
        {"url": "https://api.cash-revolution.com/v2", "description": "Production server"},
        {"url": "https://staging-api.cash-revolution.com/v2", "description": "Staging server"},
        {"url": "http://localhost:8000", "description": "Local development server"}
    ]
)

# Set custom OpenAPI schema
app.openapi = lambda: custom_openapi(app)

# Add API versioning middleware
app.add_middleware(APIVersioningMiddleware)

# Add validation middleware for real-time monitoring
app.add_middleware(ValidationMiddleware)

# Add comprehensive error tracking middleware
app.add_middleware(ErrorTrackingMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=settings.api.cors_allow_credentials,
    allow_methods=settings.api.cors_allow_methods,
    allow_headers=settings.api.cors_allow_headers,
)

# Performance tracking middleware
@app.middleware("http")
async def performance_tracking_middleware(request: Request, call_next):
    """Track performance metrics for all requests"""
    return await add_performance_middleware(request, call_next)

# Include routers
app.include_router(auth_router.router)
app.include_router(signals_router.router)
app.include_router(users_router.router)
app.include_router(admin_router.router)
app.include_router(api_router.router)
app.include_router(health_router)
app.include_router(performance_router)

# Include enhanced routers for comprehensive OpenAPI documentation
app.include_router(enhanced_auth_router, prefix="/api/v2", tags=["Enhanced Authentication"])
app.include_router(enhanced_signals_router, prefix="/api/v2", tags=["Enhanced Signals"])

# Include validation and testing routers
app.include_router(validation_router, tags=["OpenAPI Validation"])
app.include_router(testing_router, tags=["API Testing"])
app.include_router(test_runner_router, tags=["Test Runner"])

# Include comprehensive logging management router
app.include_router(logging_router, tags=["Logging Management"])

# Initialize enhanced Swagger UI
swagger_enhancer = SwaggerUIEnhancer(app)
swagger_enhancer.add_custom_routes()

# Initialize documentation website
website_generator = DocumentationWebsiteGenerator(app)
website_generator.add_website_routes()

# Static files
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except Exception as e:
    logger.warning(f"Could not mount static files: {e}")


# Utility function for serving HTML files
async def serve_html_file(filename: str, title: Optional[str] = None) -> HTMLResponse:
    """Serve HTML file with async error handling

    Args:
        filename: Path to the HTML file to serve
        title: Optional title for the page (not used in current implementation)

    Returns:
        HTMLResponse: The HTML content response

    Raises:
        HTTPException: If file is not found or error occurs
    """
    try:
        # Use async file service for better performance
        result = await file_service.read_file(filename, use_cache=True)
        if result.success:
            content = result.metadata.get("content")
            return HTMLResponse(content=content)
        else:
            raise FileNotFoundError(f"File not found: {filename}")
    except FileNotFoundError:
        logger.error(f"HTML file not found: {filename}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Page not found: {filename}"
        )
    except Exception as e:
        logger.error(f"Error serving HTML file {filename}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error serving page",
        )


# Root and page routes
@app.get("/", response_class=HTMLResponse)
async def serve_homepage():
    """Serve the homepage"""
    return serve_html_file("index.html", "AI Cash-Revolution - Homepage")


@app.get("/dashboard.html", response_class=HTMLResponse)
async def serve_dashboard_page():
    """Serve the dashboard page"""
    return serve_html_file("dashboard.html", "Dashboard - AI Cash-Revolution")


@app.get("/signals.html", response_class=HTMLResponse)
async def serve_signals_page():
    """Serve the signals page"""
    return serve_html_file("signals.html", "Signals - AI Cash-Revolution")


@app.get("/profile.html", response_class=HTMLResponse)
async def serve_profile_page():
    """Serve the profile page"""
    return serve_html_file("profile.html", "Profilo - AI Cash-Revolution")


@app.get("/test-integration.html", response_class=HTMLResponse)
async def serve_test_integration_page():
    """Serve the test integration page"""
    return serve_html_file(
        "test-integration.html", "Test Integration - AI Cash-Revolution"
    )


@app.get("/testing-dashboard.html", response_class=HTMLResponse)
async def serve_testing_dashboard_page():
    """Serve the testing dashboard page"""
    return serve_html_file(
        "static/testing-dashboard.html", "API Testing Dashboard - AI Cash-Revolution"
    )


@app.get("/error-dashboard.html", response_class=HTMLResponse)
async def serve_error_dashboard_page():
    """Serve the error tracking dashboard page"""
    return serve_html_file("static/error-dashboard.html", "Error Tracking Dashboard - AI Cash-Revolution")


# Favicon
@app.get("/favicon.ico")
async def get_favicon():
    """Serve favicon"""
    try:
        # Use async file service for favicon
        result = await file_service.read_file("favicon.ico", use_cache=True)
        if result.success:
            from fastapi.responses import Response
            content = result.metadata.get("content")
            return Response(content=content.encode('utf-8') if isinstance(content, str) else content, media_type="image/x-icon")
        else:
            return HTMLResponse(status_code=204)
    except Exception:
        # Return a 204 No Content if favicon doesn't exist
        return HTMLResponse(status_code=204)


# Health check endpoints
@app.get("/health")
def health_check() -> Dict[str, Any]:
    """Basic health check endpoint

    Returns:
        Dict[str, Any]: Health status information including database connectivity
    """
    try:
        # Check database connectivity
        db_healthy: bool = check_database_health()

        return {
            "status": "healthy" if db_healthy else "degraded",
            "timestamp": datetime.utcnow(),
            "version": settings.VERSION,
            "database": "connected" if db_healthy else "disconnected",
            "environment": "production" if settings.is_production else "development",
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "timestamp": datetime.utcnow(), "error": str(e)}


@app.get("/cache/health")
async def cache_health_check() -> Dict[str, Any]:
    """Cache health check endpoint

    Returns:
        Dict[str, Any]: Cache health status and performance metrics
    """
    try:
        cache_health = await cache_service.health_check()
        cache_info = await cache_service.get_cache_info()

        return {
            "status": cache_health.get("status", "unknown"),
            "timestamp": datetime.utcnow(),
            "cache_health": cache_health,
            "cache_info": cache_info,
            "version": settings.VERSION,
        }
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        return {"status": "unhealthy", "timestamp": datetime.utcnow(), "error": str(e)}


@app.get("/cache/metrics")
async def cache_metrics() -> Dict[str, Any]:
    """Cache performance metrics endpoint

    Returns:
        Dict[str, Any]: Cache performance metrics and statistics
    """
    try:
        metrics = cache_service.get_metrics()

        return {
            "status": "success",
            "timestamp": datetime.utcnow(),
            "metrics": {
                "hit_rate": round(metrics.hit_rate, 2),
                "error_rate": round(metrics.error_rate, 2),
                "total_operations": metrics.total_operations,
                "hits": metrics.hits,
                "misses": metrics.misses,
                "errors": metrics.errors,
                "average_response_time_ms": round(
                    metrics.average_response_time * 1000, 2
                ),
                "last_health_check": (
                    metrics.last_health_check.isoformat()
                    if metrics.last_health_check
                    else None
                ),
            },
            "version": settings.VERSION,
        }
    except Exception as e:
        logger.error(f"Cache metrics retrieval failed: {e}")
        return {"status": "error", "timestamp": datetime.utcnow(), "error": str(e)}


@app.post("/cache/invalidate")
async def invalidate_cache(pattern: Optional[str] = None) -> Dict[str, Any]:
    """Cache invalidation endpoint

    Args:
        pattern: Cache key pattern to invalidate (invalidates all if None)

    Returns:
        Dict[str, Any]: Invalidation results
    """
    try:
        if pattern:
            deleted_count = await cache_service.invalidate_pattern(pattern)
            message = f"Invalidated cache entries matching pattern: {pattern}"
        else:
            # Invalidate all cache entries by clearing each prefix separately
            total_deleted = 0
            total_deleted += await cache_service.invalidate_pattern(
                f"{settings.cache.cache_prefix_signals}*"
            )
            total_deleted += await cache_service.invalidate_pattern(
                f"{settings.cache.cache_prefix_users}*"
            )
            total_deleted += await cache_service.invalidate_pattern(
                f"{settings.cache.cache_prefix_market_data}*"
            )
            total_deleted += await cache_service.invalidate_pattern(
                f"{settings.cache.cache_prefix_api}*"
            )
            deleted_count = total_deleted
            message = "Invalidated all cache entries"

        logger.info(message)

        return {
            "status": "success",
            "timestamp": datetime.utcnow(),
            "message": message,
            "deleted_count": deleted_count,
            "version": settings.VERSION,
        }
    except Exception as e:
        logger.error(f"Cache invalidation failed: {e}")
        return {
            "status": "error",
            "timestamp": datetime.utcnow(),
            "error": str(e),
            "deleted_count": 0,
        }


@app.get("/cache/warming/metrics")
async def cache_warming_metrics() -> Dict[str, Any]:
    """Cache warming metrics endpoint

    Returns:
        Dict[str, Any]: Cache warming performance metrics
    """
    try:
        from app.services.cache_warming import get_cache_warming_metrics

        warming_metrics = get_cache_warming_metrics()

        return {
            "status": "success",
            "timestamp": datetime.utcnow(),
            "warming_metrics": warming_metrics,
            "version": settings.VERSION,
        }
    except Exception as e:
        logger.error(f"Cache warming metrics retrieval failed: {e}")
        return {"status": "error", "timestamp": datetime.utcnow(), "error": str(e)}


@app.post("/cache/warming/trigger")
async def trigger_cache_warming() -> Dict[str, Any]:
    """Trigger manual cache warming

    Returns:
        Dict[str, Any]: Cache warming results
    """
    try:
        from app.services.cache_warming import cache_warming_service

        results = await cache_warming_service.warm_all_strategies()

        # Process results for response
        summary = {
            "total_strategies": len(results),
            "successful": sum(1 for r in results.values() if r.success),
            "failed": sum(1 for r in results.values() if not r.success),
            "total_items_processed": sum(r.items_processed for r in results.values()),
            "total_execution_time": sum(
                r.execution_time_seconds for r in results.values()
            ),
            "strategies": {
                name: {
                    "success": result.success,
                    "items_processed": result.items_processed,
                    "execution_time_seconds": result.execution_time_seconds,
                    "error_message": result.error_message,
                }
                for name, result in results.items()
            },
        }

        logger.info(
            f"Manual cache warming completed: {summary['successful']}/{summary['total_strategies']} successful"
        )

        return {
            "status": "success",
            "timestamp": datetime.utcnow(),
            "summary": summary,
            "version": settings.VERSION,
        }
    except Exception as e:
        logger.error(f"Manual cache warming failed: {e}")
        return {"status": "error", "timestamp": datetime.utcnow(), "error": str(e)}


@app.get("/ml-system/status")
def ml_system_status() -> Dict[str, Union[str, datetime]]:
    """ML system status endpoint for backward compatibility

    Returns:
        Dict[str, Union[str, datetime]]: ML system status information
    """
    return {
        "status": "operational",
        "message": "OANDA AI system operational",
        "timestamp": datetime.utcnow(),
        "version": "2.0.1",
    }


# Error tracking endpoints
@app.get("/error-tracking/status")
async def error_tracking_status() -> Dict[str, Any]:
    """Error tracking system status endpoint

    Returns:
        Dict[str, Any]: Error tracking system status and configuration
    """
    try:
        return {
            "status": "enabled" if sentry_config.initialized else "disabled",
            "sentry_configured": bool(settings.sentry.sentry_dsn),
            "performance_monitoring": settings.sentry.enable_performance_monitoring,
            "error_classification": settings.sentry.enable_error_classification,
            "custom_metrics": settings.sentry.enable_custom_metrics,
            "environment": settings.environment.value,
            "timestamp": datetime.utcnow(),
            "version": settings.version,
        }
    except Exception as e:
        logger.error(f"Error tracking status check failed: {e}")
        return {"status": "error", "timestamp": datetime.utcnow(), "error": str(e)}


@app.get("/error-tracking/metrics")
async def error_tracking_metrics() -> Dict[str, Any]:
    """Error tracking metrics endpoint

    Returns:
        Dict[str, Any]: Error tracking metrics and statistics
    """
    try:
        if sentry_config.metrics_aggregator:
            metrics = sentry_config.metrics_aggregator.get_summary()
        else:
            metrics = {}

        if sentry_config.performance_monitor:
            perf_metrics = sentry_config.performance_monitor.get_performance_summary()
        else:
            perf_metrics = {}

        return {
            "status": "success",
            "timestamp": datetime.utcnow(),
            "metrics": metrics,
            "performance": perf_metrics,
            "version": settings.version,
        }
    except Exception as e:
        logger.error(f"Error tracking metrics retrieval failed: {e}")
        return {"status": "error", "timestamp": datetime.utcnow(), "error": str(e)}


@app.post("/error-tracking/test")
async def test_error_tracking() -> Dict[str, Any]:
    """Test error tracking by sending a test error

    Returns:
        Dict[str, Any]: Test results
    """
    try:
        # Send test exception
        test_error = ValueError("This is a test error for Sentry")
        event_id = sentry_config.capture_error(
            error=test_error,
            level=ErrorSeverity.INFO,
            category=ErrorCategory.SYSTEM,
            tags={"test": "true", "endpoint": "/error-tracking/test"},
            extra_data={"test_message": "This is a test error for Sentry error tracking"}
        )

        return {
            "status": "success",
            "message": "Test error sent to Sentry",
            "event_id": event_id,
            "timestamp": datetime.utcnow(),
            "version": settings.version,
        }
    except Exception as e:
        logger.error(f"Error tracking test failed: {e}")
        return {"status": "error", "timestamp": datetime.utcnow(), "error": str(e)}


# Performance monitoring endpoints
@app.get("/performance/metrics")
async def performance_metrics() -> Dict[str, Any]:
    """Performance metrics endpoint

    Returns:
        Dict[str, Any]: Performance metrics and system statistics
    """
    try:
        metrics = performance_monitor.get_performance_summary()

        return {
            "status": "success",
            "timestamp": datetime.utcnow(),
            "metrics": metrics,
            "version": settings.version,
        }
    except Exception as e:
        logger.error(f"Performance metrics retrieval failed: {e}")
        return {"status": "error", "timestamp": datetime.utcnow(), "error": str(e)}


@app.get("/performance/prometheus")
async def prometheus_metrics() -> Response:
    """Prometheus metrics endpoint

    Returns:
        Response: Prometheus metrics in text format
    """
    try:
        from fastapi.responses import Response
        metrics_data = performance_monitor.get_prometheus_metrics()
        return Response(content=metrics_data, media_type="text/plain")
    except Exception as e:
        logger.error(f"Prometheus metrics retrieval failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "timestamp": datetime.utcnow(), "error": str(e)}
        )


# Alerting endpoints
@app.get("/alerts/active")
async def get_active_alerts() -> Dict[str, Any]:
    """Get active alerts endpoint

    Returns:
        Dict[str, Any]: List of active alerts
    """
    try:
        alerts = alert_manager.get_active_alerts()
        summary = alert_manager.get_alert_summary()

        return {
            "status": "success",
            "timestamp": datetime.utcnow(),
            "alerts": [asdict(alert) for alert in alerts],
            "summary": summary,
            "version": settings.version,
        }
    except Exception as e:
        logger.error(f"Active alerts retrieval failed: {e}")
        return {"status": "error", "timestamp": datetime.utcnow(), "error": str(e)}


@app.post("/alerts/test")
async def test_alerting() -> Dict[str, Any]:
    """Test alerting system

    Returns:
        Dict[str, Any]: Test results
    """
    try:
        # Create test alert
        test_alert = alert_manager.create_alert(
            title="Test Alert from Trading System",
            message="This is a test alert to verify the alerting system is working correctly",
            severity=AlertSeverity.INFO,
            category=AlertCategory.SYSTEM,
            source="alerting_system",
            tags={"test": "true", "endpoint": "/alerts/test"},
            metadata={"test_message": "Alerting system test"}
        )

        return {
            "status": "success",
            "message": "Test alert created successfully",
            "alert_id": test_alert.id,
            "timestamp": datetime.utcnow(),
            "version": settings.version,
        }
    except Exception as e:
        logger.error(f"Alerting test failed: {e}")
        return {"status": "error", "timestamp": datetime.utcnow(), "error": str(e)}


@app.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str, resolved_by: str = "system") -> Dict[str, Any]:
    """Resolve an alert

    Args:
        alert_id: ID of the alert to resolve
        resolved_by: Who resolved the alert

    Returns:
        Dict[str, Any]: Resolution results
    """
    try:
        success = alert_manager.resolve_alert(alert_id, resolved_by)

        if success:
            return {
                "status": "success",
                "message": f"Alert {alert_id} resolved successfully",
                "alert_id": alert_id,
                "resolved_by": resolved_by,
                "timestamp": datetime.utcnow(),
                "version": settings.version,
            }
        else:
            return {
                "status": "error",
                "message": f"Alert {alert_id} not found",
                "timestamp": datetime.utcnow(),
                "version": settings.version,
            }
    except Exception as e:
        logger.error(f"Alert resolution failed: {e}")
        return {"status": "error", "timestamp": datetime.utcnow(), "error": str(e)}


# Release tracking endpoints
@app.get("/release/status")
async def get_release_status() -> Dict[str, Any]:
    """Get release tracking status

    Returns:
        Dict[str, Any]: Release information and status
    """
    try:
        summary = release_tracker.get_release_summary()

        return {
            "status": "success",
            "timestamp": datetime.utcnow(),
            "release_info": summary,
            "version": settings.version,
        }
    except Exception as e:
        logger.error(f"Release status retrieval failed: {e}")
        return {"status": "error", "timestamp": datetime.utcnow(), "error": str(e)}


@app.post("/release/deploy/start")
async def start_deployment(environment: str = None) -> Dict[str, Any]:
    """Start deployment tracking

    Args:
        environment: Target environment (optional)

    Returns:
        Dict[str, Any]: Deployment tracking information
    """
    try:
        deployment = release_tracker.start_deployment(environment)

        return {
            "status": "success",
            "message": "Deployment tracking started",
            "deployment_id": deployment.deployment_id,
            "deployment": asdict(deployment),
            "timestamp": datetime.utcnow(),
            "version": settings.version,
        }
    except Exception as e:
        logger.error(f"Deployment start failed: {e}")
        return {"status": "error", "timestamp": datetime.utcnow(), "error": str(e)}


@app.post("/release/deploy/{deployment_id}/complete")
async def complete_deployment(deployment_id: str, success: bool = True, error_message: str = None) -> Dict[str, Any]:
    """Complete deployment tracking

    Args:
        deployment_id: Deployment ID
        success: Whether deployment was successful
        error_message: Error message if failed

    Returns:
        Dict[str, Any]: Completion results
    """
    try:
        success = release_tracker.complete_deployment(deployment_id, success, error_message)

        if success:
            return {
                "status": "success",
                "message": "Deployment tracking completed",
                "deployment_id": deployment_id,
                "timestamp": datetime.utcnow(),
                "version": settings.version,
            }
        else:
            return {
                "status": "error",
                "message": f"Deployment {deployment_id} not found",
                "timestamp": datetime.utcnow(),
                "version": settings.version,
            }
    except Exception as e:
        logger.error(f"Deployment completion failed: {e}")
        return {"status": "error", "timestamp": datetime.utcnow(), "error": str(e)}


@app.get("/release/notes/{version}")
async def get_release_notes(version: str) -> Dict[str, Any]:
    """Get release notes for a version

    Args:
        version: Version number

    Returns:
        Dict[str, Any]: Release notes
    """
    try:
        notes = release_tracker.generate_release_notes(version)

        return {
            "status": "success",
            "release_notes": notes,
            "version": version,
            "timestamp": datetime.utcnow(),
        }
    except Exception as e:
        logger.error(f"Release notes generation failed: {e}")
        return {"status": "error", "timestamp": datetime.utcnow(), "error": str(e)}


# SLA monitoring endpoints
@app.get("/sla/status")
async def get_sla_status() -> Dict[str, Any]:
    """Get SLA monitoring status

    Returns:
        Dict[str, Any]: SLA compliance status
    """
    try:
        status = sla_monitor.get_sla_status()

        return {
            "status": "success",
            "timestamp": datetime.utcnow(),
            "sla_status": status,
            "version": settings.version,
        }
    except Exception as e:
        logger.error(f"SLA status retrieval failed: {e}")
        return {"status": "error", "timestamp": datetime.utcnow(), "error": str(e)}


@app.get("/sla/targets")
async def get_sla_targets() -> Dict[str, Any]:
    """Get SLA targets

    Returns:
        Dict[str, Any]: SLA target definitions
    """
    try:
        targets = sla_monitor.get_sla_targets()

        return {
            "status": "success",
            "timestamp": datetime.utcnow(),
            "targets": targets,
            "version": settings.version,
        }
    except Exception as e:
        logger.error(f"SLA targets retrieval failed: {e}")
        return {"status": "error", "timestamp": datetime.utcnow(), "error": str(e)}


@app.get("/sla/report")
async def get_sla_report(period_days: int = 30) -> Dict[str, Any]:
    """Generate SLA compliance report

    Args:
        period_days: Number of days for report period

    Returns:
        Dict[str, Any]: SLA compliance report
    """
    try:
        report = sla_monitor.generate_sla_report(period_days)

        return {
            "status": "success",
            "timestamp": datetime.utcnow(),
            "report": asdict(report),
            "period_days": period_days,
            "version": settings.version,
        }
    except Exception as e:
        logger.error(f"SLA report generation failed: {e}")
        return {"status": "error", "timestamp": datetime.utcnow(), "error": str(e)}


@app.post("/sla/targets/{metric_name}/update")
async def update_sla_target(metric_name: str, target_value: float, warning_threshold: float, critical_threshold: float) -> Dict[str, Any]:
    """Update SLA target

    Args:
        metric_name: Name of the metric
        target_value: New target value
        warning_threshold: New warning threshold
        critical_threshold: New critical threshold

    Returns:
        Dict[str, Any]: Update result
    """
    try:
        success = sla_monitor.update_sla_target(metric_name, target_value, warning_threshold, critical_threshold)

        if success:
            return {
                "status": "success",
                "message": f"SLA target {metric_name} updated successfully",
                "metric_name": metric_name,
                "new_target": target_value,
                "timestamp": datetime.utcnow(),
                "version": settings.version,
            }
        else:
            return {
                "status": "error",
                "message": f"SLA target {metric_name} not found",
                "timestamp": datetime.utcnow(),
                "version": settings.version,
            }
    except Exception as e:
        logger.error(f"SLA target update failed: {e}")
        return {"status": "error", "timestamp": datetime.utcnow(), "error": str(e)}


# Error debugging endpoints
@app.post("/debug/capture")
async def capture_error_context(
    error_type: str,
    error_message: str,
    request_data: Dict[str, Any] = None,
    user_context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Capture error context for debugging

    Args:
        error_type: Type of error
        error_message: Error message
        request_data: Request data context
        user_context: User context

    Returns:
        Dict[str, Any]: Capture result
    """
    try:
        # Create mock exception for context capture
        mock_exception = Exception(error_message)
        mock_exception.__class__.__name__ = error_type

        error_id = await error_debugger.capture_error_context(mock_exception, request_data, user_context)

        return {
            "status": "success",
            "message": "Error context captured successfully",
            "error_id": error_id,
            "timestamp": datetime.utcnow(),
            "version": settings.version,
        }
    except Exception as e:
        logger.error(f"Error context capture failed: {e}")
        return {"status": "error", "timestamp": datetime.utcnow(), "error": str(e)}


@app.post("/debug/session/{error_id}")
async def create_debug_session(error_id: str) -> Dict[str, Any]:
    """Create debug session for error

    Args:
        error_id: Error ID to debug

    Returns:
        Dict[str, Any]: Debug session information
    """
    try:
        session_id = await error_debugger.create_debug_session(error_id)

        return {
            "status": "success",
            "message": "Debug session created successfully",
            "session_id": session_id,
            "error_id": error_id,
            "timestamp": datetime.utcnow(),
            "version": settings.version,
        }
    except Exception as e:
        logger.error(f"Debug session creation failed: {e}")
        return {"status": "error", "timestamp": datetime.utcnow(), "error": str(e)}


@app.get("/debug/session/{session_id}")
async def get_debug_session(session_id: str) -> Dict[str, Any]:
    """Get debug session information

    Args:
        session_id: Debug session ID

    Returns:
        Dict[str, Any]: Debug session data
    """
    try:
        session = await error_debugger.get_debug_session(session_id)

        if session:
            return {
                "status": "success",
                "session": session,
                "timestamp": datetime.utcnow(),
                "version": settings.version,
            }
        else:
            return {
                "status": "error",
                "message": "Debug session not found",
                "timestamp": datetime.utcnow(),
                "version": settings.version,
            }
    except Exception as e:
        logger.error(f"Debug session retrieval failed: {e}")
        return {"status": "error", "timestamp": datetime.utcnow(), "error": str(e)}


@app.post("/debug/session/{session_id}/replay")
async def replay_request(session_id: str, modifications: Dict[str, Any] = None) -> Dict[str, Any]:
    """Replay request in debug session

    Args:
        session_id: Debug session ID
        modifications: Request modifications

    Returns:
        Dict[str, Any]: Replay results
    """
    try:
        result = await error_debugger.replay_request(session_id, modifications)

        return {
            "status": "success",
            "message": "Request replay completed",
            "replay_result": result,
            "timestamp": datetime.utcnow(),
            "version": settings.version,
        }
    except Exception as e:
        logger.error(f"Request replay failed: {e}")
        return {"status": "error", "timestamp": datetime.utcnow(), "error": str(e)}


@app.post("/debug/session/{session_id}/simulate")
async def simulate_error(session_id: str, error_type: str, error_message: str) -> Dict[str, Any]:
    """Simulate error in debug session

    Args:
        session_id: Debug session ID
        error_type: Type of error to simulate
        error_message: Error message

    Returns:
        Dict[str, Any]: Simulation results
    """
    try:
        result = await error_debugger.simulate_error(session_id, error_type, error_message)

        return {
            "status": "success",
            "message": "Error simulation completed",
            "simulation_result": result,
            "timestamp": datetime.utcnow(),
            "version": settings.version,
        }
    except Exception as e:
        logger.error(f"Error simulation failed: {e}")
        return {"status": "error", "timestamp": datetime.utcnow(), "error": str(e)}


@app.get("/debug/sessions")
async def list_debug_sessions(limit: int = 50) -> Dict[str, Any]:
    """List debug sessions

    Args:
        limit: Maximum number of sessions to return

    Returns:
        Dict[str, Any]: List of debug sessions
    """
    try:
        sessions = await error_debugger.list_debug_sessions(limit)

        return {
            "status": "success",
            "sessions": sessions,
            "limit": limit,
            "timestamp": datetime.utcnow(),
            "version": settings.version,
        }
    except Exception as e:
        logger.error(f"Debug session listing failed: {e}")
        return {"status": "error", "timestamp": datetime.utcnow(), "error": str(e)}


@app.post("/debug/session/{session_id}/close")
async def close_debug_session(session_id: str) -> Dict[str, Any]:
    """Close debug session

    Args:
        session_id: Debug session ID to close

    Returns:
        Dict[str, Any]: Close result
    """
    try:
        success = await error_debugger.close_debug_session(session_id)

        if success:
            return {
                "status": "success",
                "message": "Debug session closed successfully",
                "session_id": session_id,
                "timestamp": datetime.utcnow(),
                "version": settings.version,
            }
        else:
            return {
                "status": "error",
                "message": "Debug session not found",
                "timestamp": datetime.utcnow(),
                "version": settings.version,
            }
    except Exception as e:
        logger.error(f"Debug session close failed: {e}")
        return {"status": "error", "timestamp": datetime.utcnow(), "error": str(e)}


# CORS test endpoint
@app.get("/cors-test")
def cors_test() -> Dict[str, Union[str, datetime, list]]:
    """Test CORS configuration

    Returns:
        Dict[str, Union[str, datetime, list]]: CORS configuration test results
    """
    return {
        "message": "CORS working correctly",
        "timestamp": datetime.utcnow(),
        "allowed_origins": settings.ALLOWED_ORIGINS,
    }


# Emergency endpoints (for backward compatibility)
@app.get("/emergency-migrate")
def emergency_migrate() -> Dict[str, Union[str, datetime]]:
    """Emergency migration endpoint

    Returns:
        Dict[str, Union[str, datetime]]: Migration endpoint information
    """
    return {
        "message": "Emergency migration endpoint - use admin routes instead",
        "redirect": "/admin/migrate-database",
        "timestamp": datetime.utcnow(),
    }


@app.post("/emergency/database-migrate")
def emergency_database_migrate() -> Dict[str, Union[str, datetime]]:
    """Emergency database migration

    Returns:
        Dict[str, Union[str, datetime]]: Database migration information
    """
    return {
        "message": "Emergency migration - use admin routes instead",
        "redirect": "/admin/migrate-database",
        "timestamp": datetime.utcnow(),
    }


@app.post("/emergency/database-reset")
def emergency_database_reset(
    token: Optional[str] = None,
) -> Dict[str, Union[str, datetime]]:
    """Emergency database reset endpoint

    Args:
        token: Optional reset token

    Returns:
        Dict[str, Union[str, datetime]]: Database reset information
    """
    return {
        "message": "Emergency reset - use admin routes instead",
        "redirect": "/admin/reset-database",
        "timestamp": datetime.utcnow(),
    }


# Payment endpoints (placeholder for future implementation)
@app.post("/api/payments/create-demo-payment")
def create_demo_payment() -> Dict[str, Union[str, datetime, None]]:
    """Create demo payment (placeholder)

    Returns:
        Dict[str, Union[str, datetime, None]]: Demo payment information
    """
    return {
        "message": "Demo payment created",
        "payment_id": "demo_payment_123",
        "status": "completed",
        "timestamp": datetime.utcnow(),
    }


@app.get("/api/payments/subscription-status")
def get_subscription_status() -> Dict[str, Union[str, datetime, None]]:
    """Get subscription status (placeholder)

    Returns:
        Dict[str, Union[str, datetime, None]]: Subscription status information
    """
    return {
        "status": "active",
        "plan": "demo",
        "expires_at": None,
        "timestamp": datetime.utcnow(),
    }


# Signal execution endpoints (placeholder)
@app.post("/api/signals/execute")
def execute_signal() -> Dict[str, Union[str, datetime]]:
    """Execute signal (placeholder)

    Returns:
        Dict[str, Union[str, datetime]]: Signal execution status
    """
    return {
        "message": "Signal execution endpoint - not implemented",
        "status": "placeholder",
        "timestamp": datetime.utcnow(),
    }


# OpenAPI validation endpoints
@app.get("/api/validation/quick-scan")
async def quick_validation_scan() -> Dict[str, Any]:
    """Quick OpenAPI validation scan

    Returns:
        Dict[str, Any]: Quick validation results and compliance score
    """
    try:
        from app.core.openapi_validation import OpenAPIValidator
        validator = OpenAPIValidator(app)
        report = await validator.run_comprehensive_validation()

        return {
            "status": "success",
            "timestamp": datetime.utcnow(),
            "compliance_score": report.openapi_compliance_score,
            "total_tests": report.total_tests,
            "passed_tests": report.passed_tests,
            "failed_tests": report.failed_tests,
            "critical_issues": len([r for r in report.results if r.level.value == "critical"]),
            "recommendations": report.recommendations[:3],  # Top 3 recommendations
            "version": "2.0.1"
        }
    except Exception as e:
        logger.error(f"Quick validation scan failed: {e}")
        return {
            "status": "error",
            "timestamp": datetime.utcnow(),
            "error": str(e)
        }

@app.get("/api/testing/health-check")
async def api_health_check() -> Dict[str, Any]:
    """Comprehensive API health check with testing

    Returns:
        Dict[str, Any]: Health check with testing results
    """
    try:
        from app.core.api_testing import APITestFramework
        framework = APITestFramework(app)

        # Run basic health tests
        basic_results = await framework.run_unit_tests()

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow(),
            "basic_tests": {
                "total": basic_results.total_tests,
                "passed": basic_results.passed_tests,
                "failed": basic_results.failed_tests,
                "success_rate": basic_results.success_rate
            },
            "database": "connected" if check_database_health() else "disconnected",
            "cache": await cache_service.health_check(),
            "version": "2.0.1"
        }
    except Exception as e:
        logger.error(f"API health check failed: {e}")
        return {
            "status": "degraded",
            "timestamp": datetime.utcnow(),
            "error": str(e)
        }

# Error documentation endpoints
@app.get("/api/errors/status-codes")
def get_error_status_codes() -> Dict[str, Any]:
    """Get comprehensive error status code documentation

    Returns:
        Dict[str, Any]: Complete HTTP status code documentation
    """
    return {
        "status": "success",
        "timestamp": datetime.utcnow(),
        "version": "2.0.1",
        "error_codes": HTTP_STATUS_DOCUMENTATION
    }


@app.get("/api/errors/examples")
def get_error_examples() -> Dict[str, Any]:
    """Get error response examples for documentation

    Returns:
        Dict[str, Any]: Error response examples
    """
    return {
        "status": "success",
        "timestamp": datetime.utcnow(),
        "version": "2.0.1",
        "examples": ERROR_RESPONSE_EXAMPLES
    }


# API versioning documentation endpoints
@app.get("/api/versioning/info")
def get_versioning_info() -> Dict[str, Any]:
    """Get comprehensive API versioning information

    Returns:
        Dict[str, Any]: API versioning strategy and documentation
    """
    from app.core.api_versioning import VERSION_CONFIG, APIVersion, VersionStatus

    version_info = {}
    for version, config in VERSION_CONFIG.items():
        version_info[version.value] = {
            "status": config["status"].value,
            "release_date": config["release_date"].isoformat(),
            "description": config["description"],
            "breaking_changes": config.get("breaking_changes", []),
            "migration_guide": config.get("migration_guide"),
        }

        if "deprecation_date" in config:
            version_info[version.value]["deprecation_date"] = config["deprecation_date"].isoformat()
        if "sunset_date" in config:
            version_info[version.value]["sunset_date"] = config["sunset_date"].isoformat()

    return {
        "status": "success",
        "timestamp": datetime.utcnow(),
        "current_version": APIVersion.CURRENT.value,
        "supported_versions": [v.value for v in APIVersion],
        "version_info": version_info,
        "versioning_strategy": {
            "header_based": True,
            "header_name": "X-API-Version",
            "url_path_based": True,
            "query_parameter_based": True,
            "default_version": APIVersion.CURRENT.value
        }
    }


@app.get("/api/versioning/migration-guide")
def get_migration_guide(from_version: str, to_version: str = "v2") -> Dict[str, Any]:
    """Get migration guide between API versions

    Args:
        from_version: Source version to migrate from
        to_version: Target version to migrate to

    Returns:
        Dict[str, Any]: Migration guide and compatibility information
    """
    from app.core.api_versioning import VERSION_CONFIG, APIVersion

    if from_version not in [v.value for v in APIVersion]:
        return {
            "status": "error",
            "timestamp": datetime.utcnow(),
            "error": f"Unsupported source version: {from_version}"
        }

    if to_version not in [v.value for v in APIVersion]:
        return {
            "status": "error",
            "timestamp": datetime.utcnow(),
            "error": f"Unsupported target version: {to_version}"
        }

    from_config = VERSION_CONFIG[APIVersion(from_version)]
    to_config = VERSION_CONFIG[APIVersion(to_version)]

    return {
        "status": "success",
        "timestamp": datetime.utcnow(),
        "migration": {
            "from_version": from_version,
            "to_version": to_version,
            "from_status": from_config["status"].value,
            "to_status": to_config["status"].value,
            "breaking_changes": from_config.get("breaking_changes", []),
            "migration_guide": from_config.get("migration_guide"),
            "compatibility": "compatible" if from_version == "v1" and to_version == "v2" else "unknown",
            "estimated_effort": "Low" if from_version == "v1" and to_version == "v2" else "Unknown"
        }
    }


# VPS endpoints (legacy, for backward compatibility)
@app.post("/api/vps/heartbeat")
def vps_heartbeat() -> Dict[str, Union[str, datetime]]:
    """VPS heartbeat endpoint (legacy)

    Returns:
        Dict[str, Union[str, datetime]]: VPS heartbeat response
    """
    return {
        "message": "VPS heartbeat - legacy endpoint",
        "status": "deprecated",
        "timestamp": datetime.utcnow(),
    }


@app.get("/api/vps/status")
def vps_status() -> Dict[str, Union[str, datetime]]:
    """VPS status endpoint (legacy)

    Returns:
        Dict[str, Union[str, datetime]]: VPS status information
    """
    return {
        "status": "deprecated",
        "message": "VPS functionality replaced with OANDA API",
        "timestamp": datetime.utcnow(),
    }


# Exception handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Custom 404 handler

    Args:
        request: The incoming request
        exc: The HTTP exception

    Returns:
        JSONResponse: Formatted error response
    """
    return JSONResponse(
        status_code=404,
        content={
            "error": "Endpoint not found",
            "path": str(request.url.path),
            "timestamp": datetime.utcnow(),
        },
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Custom 500 handler

    Args:
        request: The incoming request
        exc: The exception that occurred

    Returns:
        JSONResponse: Formatted error response
    """
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "timestamp": datetime.utcnow(),
        },
    )


# Configuration validation endpoint
@app.get("/config/validate")
def validate_config() -> Dict[str, Any]:
    """Validate configuration and return results

    Returns:
        Dict[str, Any]: Configuration validation results
    """
    try:
        validation_result = settings.validate_configuration()

        return {
            "status": "success",
            "timestamp": datetime.utcnow(),
            "validation": validation_result,
            "version": settings.version,
        }
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        return {
            "status": "error",
            "timestamp": datetime.utcnow(),
            "error": str(e),
            "valid": False,
        }

# Configuration endpoint (safe, without sensitive data)
@app.get("/config/info")
def get_config_info() -> Dict[str, Any]:
    """Get configuration information without sensitive data

    Returns:
        Dict[str, Any]: Safe configuration information
    """
    try:
        safe_settings = settings.get_safe_settings()

        return {
            "status": "success",
            "timestamp": datetime.utcnow(),
            "config": safe_settings,
            "version": settings.version,
        }
    except Exception as e:
        logger.error(f"Failed to get config info: {e}")
        return {
            "status": "error",
            "timestamp": datetime.utcnow(),
            "error": str(e),
        }

# Enhanced configuration management endpoints
@app.get("/config/health")
def get_config_health() -> Dict[str, Any]:
    """Get comprehensive configuration health report

    Returns:
        Dict[str, Any]: Configuration health report with validation results
    """
    try:
        from config.startup_validator import ConfigurationValidator
        validator = ConfigurationValidator(config_manager)
        health_report = validator.validate_configuration()

        return {
            "status": "success",
            "timestamp": datetime.utcnow(),
            "health_report": {
                "overall_status": health_report.overall_status,
                "can_start": health_report.can_start,
                "critical_issues": health_report.critical_issues,
                "error_issues": health_report.error_issues,
                "warning_issues": health_report.warning_issues,
                "info_messages": health_report.info_messages,
                "environment": health_report.environment,
                "validation_results": [
                    {
                        "key": r.key,
                        "level": r.level.value,
                        "message": r.message,
                        "suggestion": r.suggestion,
                        "required": r.required
                    }
                    for r in health_report.validation_results
                ]
            }
        }
    except Exception as e:
        logger.error(f"Failed to get config health: {e}")
        return {
            "status": "error",
            "timestamp": datetime.utcnow(),
            "error": str(e)
        }

@app.get("/config/feature-flags")
def get_feature_flags(environment: str = None, tag: str = None) -> Dict[str, Any]:
    """Get feature flags with optional filtering

    Args:
        environment: Filter by environment
        tag: Filter by tag

    Returns:
        Dict[str, Any]: Feature flags list
    """
    try:
        flags = config_manager.list_feature_flags(environment=environment, tag=tag)

        return {
            "status": "success",
            "timestamp": datetime.utcnow(),
            "flags": [
                {
                    "name": flag.name,
                    "enabled": flag.enabled,
                    "description": flag.description,
                    "environment": flag.environment,
                    "rollout_percentage": flag.rollout_percentage,
                    "conditions": flag.conditions,
                    "tags": flag.tags,
                    "created_at": flag.created_at.isoformat(),
                    "modified_at": flag.modified_at.isoformat(),
                    "created_by": flag.created_by
                }
                for flag in flags
            ],
            "stats": config_manager.get_feature_flag_stats()
        }
    except Exception as e:
        logger.error(f"Failed to get feature flags: {e}")
        return {
            "status": "error",
            "timestamp": datetime.utcnow(),
            "error": str(e)
        }

@app.post("/config/feature-flags/{flag_name}")
def set_feature_flag(
    flag_name: str,
    enabled: bool,
    description: str = None,
    environment: str = None,
    rollout_percentage: int = 100,
    conditions: Dict[str, Any] = None,
    tags: List[str] = None
) -> Dict[str, Any]:
    """Set or update a feature flag

    Args:
        flag_name: Name of the feature flag
        enabled: Whether the flag is enabled
        description: Flag description
        environment: Target environment
        rollout_percentage: Rollout percentage (0-100)
        conditions: Conditional logic for flag evaluation
        tags: Tags for categorization

    Returns:
        Dict[str, Any]: Operation result
    """
    try:
        success = config_manager.set_feature_flag(
            flag_name=flag_name,
            enabled=enabled,
            description=description,
            environment=environment,
            rollout_percentage=rollout_percentage,
            conditions=conditions,
            tags=tags
        )

        if success:
            return {
                "status": "success",
                "timestamp": datetime.utcnow(),
                "message": f"Feature flag '{flag_name}' updated successfully"
            }
        else:
            return {
                "status": "error",
                "timestamp": datetime.utcnow(),
                "message": f"Failed to update feature flag '{flag_name}'"
            }
    except Exception as e:
        logger.error(f"Failed to set feature flag: {e}")
        return {
            "status": "error",
            "timestamp": datetime.utcnow(),
            "error": str(e)
        }

@app.delete("/config/feature-flags/{flag_name}")
def delete_feature_flag(flag_name: str) -> Dict[str, Any]:
    """Delete a feature flag

    Args:
        flag_name: Name of the feature flag to delete

    Returns:
        Dict[str, Any]: Operation result
    """
    try:
        success = config_manager.delete_feature_flag(flag_name)

        if success:
            return {
                "status": "success",
                "timestamp": datetime.utcnow(),
                "message": f"Feature flag '{flag_name}' deleted successfully"
            }
        else:
            return {
                "status": "error",
                "timestamp": datetime.utcnow(),
                "message": f"Failed to delete feature flag '{flag_name}'"
            }
    except Exception as e:
        logger.error(f"Failed to delete feature flag: {e}")
        return {
            "status": "error",
            "timestamp": datetime.utcnow(),
            "error": str(e)
        }

@app.post("/config/backup")
def create_config_backup() -> Dict[str, Any]:
    """Create a configuration backup

    Returns:
        Dict[str, Any]: Backup operation result
    """
    try:
        from pathlib import Path
        import datetime

        timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_path = Path(f"./backups/config_backup_{timestamp}")

        success = config_manager.backup_configuration(backup_path)

        if success:
            return {
                "status": "success",
                "timestamp": datetime.utcnow(),
                "message": "Configuration backup created successfully",
                "backup_path": str(backup_path)
            }
        else:
            return {
                "status": "error",
                "timestamp": datetime.utcnow(),
                "message": "Failed to create configuration backup"
            }
    except Exception as e:
        logger.error(f"Failed to create config backup: {e}")
        return {
            "status": "error",
            "timestamp": datetime.utcnow(),
            "error": str(e)
        }

@app.post("/config/restore")
def restore_config_backup(backup_path: str) -> Dict[str, Any]:
    """Restore configuration from backup

    Args:
        backup_path: Path to backup directory

    Returns:
        Dict[str, Any]: Restore operation result
    """
    try:
        from pathlib import Path

        success = config_manager.restore_configuration(Path(backup_path))

        if success:
            return {
                "status": "success",
                "timestamp": datetime.utcnow(),
                "message": "Configuration restored successfully"
            }
        else:
            return {
                "status": "error",
                "timestamp": datetime.utcnow(),
                "message": "Failed to restore configuration"
            }
    except Exception as e:
        logger.error(f"Failed to restore config backup: {e}")
        return {
            "status": "error",
            "timestamp": datetime.utcnow(),
            "error": str(e)
        }

@app.get("/config/versions")
def get_config_versions(limit: int = 10) -> Dict[str, Any]:
    """Get configuration version history

    Args:
        limit: Maximum number of versions to return

    Returns:
        Dict[str, Any]: Configuration versions
    """
    try:
        versions = config_manager.list_config_versions(limit=limit)

        return {
            "status": "success",
            "timestamp": datetime.utcnow(),
            "versions": [
                {
                    "version": v.version,
                    "environment": v.environment,
                    "created_at": v.created_at.isoformat(),
                    "created_by": v.created_by,
                    "checksum": v.checksum,
                    "changes": v.changes,
                    "rollback_available": v.rollback_available
                }
                for v in versions
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get config versions: {e}")
        return {
            "status": "error",
            "timestamp": datetime.utcnow(),
            "error": str(e)
        }

@app.post("/config/versions/{version}/rollback")
def rollback_config_version(version: str) -> Dict[str, Any]:
    """Rollback configuration to a specific version

    Args:
        version: Version to rollback to

    Returns:
        Dict[str, Any]: Rollback operation result
    """
    try:
        success = config_manager.rollback_to_version(version)

        if success:
            return {
                "status": "success",
                "timestamp": datetime.utcnow(),
                "message": f"Configuration rolled back to version {version}"
            }
        else:
            return {
                "status": "error",
                "timestamp": datetime.utcnow(),
                "message": f"Failed to rollback to version {version}"
            }
    except Exception as e:
        logger.error(f"Failed to rollback config version: {e}")
        return {
            "status": "error",
            "timestamp": datetime.utcnow(),
            "error": str(e)
        }

@app.get("/config/summary")
def get_config_summary() -> Dict[str, Any]:
    """Get configuration system summary

    Returns:
        Dict[str, Any]: Configuration summary
    """
    try:
        summary = config_manager.get_config_summary()

        return {
            "status": "success",
            "timestamp": datetime.utcnow(),
            "summary": summary
        }
    except Exception as e:
        logger.error(f"Failed to get config summary: {e}")
        return {
            "status": "error",
            "timestamp": datetime.utcnow(),
            "error": str(e)
        }


# Documentation generation endpoints
@app.get("/api/docs/generate")
async def generate_documentation(format: str = "all") -> Dict[str, Any]:
    """Generate API documentation in various formats

    Args:
        format: Documentation format (all, json, yaml, html, python_sdk, javascript_sdk)

    Returns:
        Dict[str, Any]: Generated documentation files and metadata
    """
    try:
        doc_generator = DocumentationGenerator(app)

        if format == "all":
            generated_files = await doc_generator.generate_all_documentation()
        elif format == "json":
            generated_files = {"openapi_json": await doc_generator.generate_openapi_json()}
        elif format == "yaml":
            generated_files = {"openapi_yaml": await doc_generator.generate_openapi_yaml()}
        elif format == "html":
            generated_files = {"html_docs": await doc_generator.generate_html_documentation()}
        elif format == "python_sdk":
            generated_files = {"python_sdk": await doc_generator.generate_python_sdk()}
        elif format == "javascript_sdk":
            generated_files = {"javascript_sdk": await doc_generator.generate_javascript_sdk()}
        elif format == "postman":
            generated_files = {"postman_collection": await doc_generator.generate_postman_collection()}
        else:
            return {
                "status": "error",
                "timestamp": datetime.utcnow(),
                "error": f"Unsupported format: {format}. Supported formats: all, json, yaml, html, python_sdk, javascript_sdk, postman"
            }

        return {
            "status": "success",
            "timestamp": datetime.utcnow(),
            "format": format,
            "generated_files": list(generated_files.keys()),
            "file_sizes": {k: len(v) for k, v in generated_files.items()},
            "version": settings.version,
        }

    except Exception as e:
        logger.error(f"Documentation generation failed: {e}")
        return {
            "status": "error",
            "timestamp": datetime.utcnow(),
            "error": str(e),
        }


@app.get("/api/docs/preview")
async def preview_documentation() -> Dict[str, Any]:
    """Preview the OpenAPI specification

    Returns:
        Dict[str, Any]: OpenAPI specification preview
    """
    try:
        openapi_spec = app.openapi()

        return {
            "status": "success",
            "timestamp": datetime.utcnow(),
            "specification": {
                "openapi": openapi_spec.get("openapi"),
                "info": openapi_spec.get("info"),
                "servers": openapi_spec.get("servers"),
                "paths_count": len(openapi_spec.get("paths", {})),
                "components_count": len(openapi_spec.get("components", {}).get("schemas", {})),
                "tags_count": len(openapi_spec.get("tags", [])),
                "security_schemes_count": len(openapi_spec.get("components", {}).get("securitySchemes", {})),
            },
            "version": settings.version,
        }

    except Exception as e:
        logger.error(f"Documentation preview failed: {e}")
        return {
            "status": "error",
            "timestamp": datetime.utcnow(),
            "error": str(e),
        }

# Startup event
@app.on_event("startup")
async def startup_event() -> None:
    """Application startup tasks

    Performs initialization tasks including configuration validation,
    database health check, cache initialization, async services, and service availability verification.
    """
    logger.info(f"Starting {settings.project_name} v{settings.version}")
    logger.info(
        f"Environment: {settings.environment.value.upper()}"
    )

    # Validate configuration first
    try:
        validation_result = settings.validate_configuration()
        if not validation_result["valid"]:
            logger.error(f"Configuration validation failed: {validation_result['errors']}")
            if settings.is_production:
                # In production, fail fast on configuration errors
                raise RuntimeError(f"Configuration validation failed: {validation_result['errors']}")
        else:
            logger.info(f"Configuration validated successfully ({validation_result['settings_count']} settings)")
    except Exception as e:
        logger.error(f"Configuration validation error: {e}")
        if settings.is_production:
            raise

    # Initialize Sentry error tracking
    try:
        sentry_config.initialize()
        logger.info("Sentry error tracking initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Sentry error tracking: {e}")

    # Initialize performance monitoring
    try:
        performance_monitor.start_monitoring()
        logger.info("Performance monitoring started successfully")
    except Exception as e:
        logger.error(f"Failed to start performance monitoring: {e}")

    # Initialize release tracking
    try:
        release_tracker.initialize()
        logger.info("Release tracking initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize release tracking: {e}")

    # Initialize SLA monitoring
    try:
        sla_monitor.start_monitoring()
        logger.info("SLA monitoring started successfully")
    except Exception as e:
        logger.error(f"Failed to start SLA monitoring: {e}")

    # Initialize async logging service first
    try:
        logging_success = await init_logging_service()
        if logging_success:
            logger.info("Async logging service initialized successfully")
        else:
            logger.warning("Async logging service initialization failed")
    except Exception as e:
        logger.error(f"Failed to initialize async logging service: {e}")

    # Initialize async database system
    try:
        db_success = await init_async_database()
        if db_success:
            logger.info("Async database system initialized successfully")
        else:
            logger.warning("Async database system initialization failed, using sync fallback")
    except Exception as e:
        logger.error(f"Failed to initialize async database: {e}")

    # Initialize cache system
    try:
        cache_success = await init_cache()
        if cache_success:
            logger.info("Cache system initialized successfully")

            # Start cache warming service
            try:
                await start_cache_warming()
                logger.info("Cache warming service started successfully")
            except Exception as e:
                logger.warning(f"Failed to start cache warming service: {e}")
        else:
            logger.warning("Cache system initialization failed, fallback cache enabled")
    except Exception as e:
        logger.error(f"Failed to initialize cache system: {e}")

    # Initialize async HTTP clients
    try:
        http_success = await init_http_clients()
        if http_success:
            logger.info("Async HTTP clients initialized successfully")
        else:
            logger.warning("Async HTTP clients initialization failed")
    except Exception as e:
        logger.error(f"Failed to initialize async HTTP clients: {e}")

    # Initialize async file service
    try:
        file_success = await init_file_service(".")
        if file_success:
            logger.info("Async file service initialized successfully")
        else:
            logger.warning("Async file service initialization failed")
    except Exception as e:
        logger.error(f"Failed to initialize async file service: {e}")

    # Initialize async task scheduler
    try:
        scheduler_success = await init_task_scheduler()
        if scheduler_success:
            logger.info("Async task scheduler initialized successfully")
        else:
            logger.warning("Async task scheduler initialization failed")
    except Exception as e:
        logger.error(f"Failed to initialize async task scheduler: {e}")

    # Initialize async dependency injection
    try:
        di_success = await init_dependency_injection()
        if di_success:
            logger.info("Async dependency injection initialized successfully")
        else:
            logger.warning("Async dependency injection initialization failed")
    except Exception as e:
        logger.error(f"Failed to initialize async dependency injection: {e}")

    # Initialize async error handling
    try:
        error_handling_success = await init_error_handling()
        if error_handling_success:
            logger.info("Async error handling initialized successfully")
        else:
            logger.warning("Async error handling initialization failed")
    except Exception as e:
        logger.error(f"Failed to initialize async error handling: {e}")

    # Check database health (fallback sync check)
    try:
        db_healthy: bool = check_database_health()
        if db_healthy:
            logger.info("Database connection established")
        else:
            logger.error("Database connection failed")
    except Exception as e:
        logger.error(f"Database health check failed: {e}")

    # Initialize OANDA if available
    try:
        from app.services.oanda_service import OANDAService
        from app.dependencies.database import get_db
        logger.info("OANDA service available")
    except ImportError:
        logger.warning("OANDA service not available")

    logger.info("Application startup completed with async optimizations")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Application shutdown tasks

    Performs cleanup tasks during application shutdown.
    """
    logger.info("Shutting down application with async cleanup...")

    # Stop performance monitoring
    try:
        performance_monitor.stop_monitoring()
        logger.info("Performance monitoring stopped successfully")
    except Exception as e:
        logger.error(f"Error stopping performance monitoring: {e}")

    # Stop SLA monitoring
    try:
        sla_monitor.stop_monitoring()
        logger.info("SLA monitoring stopped successfully")
    except Exception as e:
        logger.error(f"Error stopping SLA monitoring: {e}")

    # Stop cache warming service
    try:
        await stop_cache_warming()
        logger.info("Cache warming service stopped successfully")
    except Exception as e:
        logger.error(f"Error stopping cache warming service: {e}")

    # Cleanup cache system
    try:
        await cleanup_cache()
        logger.info("Cache system cleaned up successfully")
    except Exception as e:
        logger.error(f"Error cleaning up cache system: {e}")

    # Cleanup async HTTP clients
    try:
        await cleanup_http_clients()
        logger.info("HTTP clients cleaned up successfully")
    except Exception as e:
        logger.error(f"Error cleaning up HTTP clients: {e}")

    # Cleanup async database system
    try:
        await cleanup_async_database()
        logger.info("Async database system cleaned up successfully")
    except Exception as e:
        logger.error(f"Error cleaning up async database: {e}")

    # Cleanup async task scheduler
    try:
        await cleanup_task_scheduler()
        logger.info("Async task scheduler cleaned up successfully")
    except Exception as e:
        logger.error(f"Error cleaning up task scheduler: {e}")

    # Cleanup async logging service
    try:
        await cleanup_logging_service()
        logger.info("Async logging service cleaned up successfully")
    except Exception as e:
        logger.error(f"Error cleaning up async logging service: {e}")

    # Cleanup async dependency injection
    try:
        await cleanup_dependency_injection()
        logger.info("Async dependency injection cleaned up successfully")
    except Exception as e:
        logger.error(f"Error cleaning up async dependency injection: {e}")

    # Cleanup async error handling
    try:
        await cleanup_error_handling()
        logger.info("Async error handling cleaned up successfully")
    except Exception as e:
        logger.error(f"Error cleaning up async error handling: {e}")

    logger.info("Application shutdown completed with async cleanup")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=settings.server.reload
    )
