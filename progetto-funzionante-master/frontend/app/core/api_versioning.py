"""
API Versioning Strategy and Management

This module implements a comprehensive API versioning strategy including:
- Version header validation
- Deprecation warnings
- Backward compatibility
- Migration guides
- Version discovery
"""

from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.middleware import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class APIVersion(str, Enum):
    """Supported API versions"""
    V1 = "v1"
    V2 = "v2"
    CURRENT = V2

class VersionStatus(str, Enum):
    """API version status"""
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    SUNSET = "sunset"

# Version configuration
VERSION_CONFIG = {
    APIVersion.V1: {
        "status": VersionStatus.DEPRECATED,
        "release_date": datetime(2023, 1, 1),
        "deprecation_date": datetime(2024, 1, 1),
        "sunset_date": datetime(2024, 6, 1),
        "description": "Initial API version with basic functionality",
        "breaking_changes": [
            "Authentication method changed from Basic Auth to JWT",
            "Signal schema updated with new risk assessment fields",
            "Response format standardized"
        ],
        "migration_guide": "https://docs.cash-revolution.com/migration/v1-to-v2"
    },
    APIVersion.V2: {
        "status": VersionStatus.ACTIVE,
        "release_date": datetime(2024, 1, 1),
        "deprecation_date": None,
        "sunset_date": None,
        "description": "Current API version with enhanced features",
        "new_features": [
            "Enhanced AI analysis with Gemini integration",
            "Real-time market data streaming",
            "Advanced risk management",
            "Portfolio management endpoints",
            "Improved caching and performance"
        ],
        "documentation": "https://docs.cash-revolution.com/api/v2"
    }
}

class APIVersioningMiddleware(BaseHTTPMiddleware):
    """Middleware for API version handling"""

    def __init__(self, app: FastAPI):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        """Process request with version handling"""

        # Get requested version
        version = self._get_requested_version(request)

        # Validate version
        if not version:
            return self._no_version_response()

        if version not in VERSION_CONFIG:
            return self._unsupported_version_response(version)

        # Check version status
        version_info = VERSION_CONFIG[version]

        if version_info["status"] == VersionStatus.SUNSET:
            return self._version_sunset_response(version)

        # Add version info to request state
        request.state.api_version = version
        request.state.version_info = version_info

        # Add deprecation warnings if needed
        if version_info["status"] == VersionStatus.DEPRECATED:
            response = await call_next(request)
            return self._add_deprecation_headers(response, version)

        # Process normally
        response = await call_next(request)

        # Add version headers
        self._add_version_headers(response, version)

        return response

    def _get_requested_version(self, request: Request) -> Optional[str]:
        """Extract API version from request"""

        # Try version header first
        version = request.headers.get("X-API-Version")
        if version:
            return version.lower()

        # Try Accept header
        accept = request.headers.get("Accept", "")
        if "application/vnd.cash-revolution." in accept:
            # Extract version from Accept header
            for part in accept.split(","):
                part = part.strip()
                if part.startswith("application/vnd.cash-revolution."):
                    version = part.split(".")[-1].replace("+json", "")
                    return version.lower()

        # Try URL path
        path_parts = request.url.path.split("/")
        if len(path_parts) >= 2 and path_parts[1].startswith("v"):
            return path_parts[1].lower()

        # Default to current version
        return APIVersion.CURRENT.value

    def _add_version_headers(self, response: Response, version: str):
        """Add version information to response headers"""
        response.headers["X-API-Version"] = version
        response.headers["X-API-Current-Version"] = APIVersion.CURRENT.value

        version_info = VERSION_CONFIG.get(version, {})
        if version_info:
            response.headers["X-API-Version-Status"] = version_info["status"]

    def _add_deprecation_headers(self, response: Response, version: str) -> Response:
        """Add deprecation warning headers"""
        version_info = VERSION_CONFIG[version]

        response.headers["X-API-Deprecated"] = "true"
        response.headers["X-API-Sunset-Date"] = version_info["sunset_date"].isoformat()
        response.headers["Link"] = f'<{version_info["migration_guide"]}>; rel="deprecation"'

        return response

    def _no_version_response(self) -> JSONResponse:
        """Return response for no version specified"""
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "MissingAPIVersion",
                "message": "API version is required. Please specify X-API-Version header",
                "supported_versions": list(VERSION_CONFIG.keys()),
                "current_version": APIVersion.CURRENT.value,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    def _unsupported_version_response(self, version: str) -> JSONResponse:
        """Return response for unsupported version"""
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "UnsupportedAPIVersion",
                "message": f"API version '{version}' is not supported",
                "supported_versions": list(VERSION_CONFIG.keys()),
                "current_version": APIVersion.CURRENT.value,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    def _version_sunset_response(self, version: str) -> JSONResponse:
        """Return response for sunset version"""
        version_info = VERSION_CONFIG[version]
        return JSONResponse(
            status_code=status.HTTP_410_GONE,
            content={
                "error": "APISunset",
                "message": f"API version '{version}' has been retired",
                "sunset_date": version_info["sunset_date"].isoformat(),
                "migration_guide": version_info["migration_guide"],
                "current_version": APIVersion.CURRENT.value,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

def get_version_info(version: str) -> Dict[str, Any]:
    """Get detailed information about an API version"""
    if version not in VERSION_CONFIG:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API version '{version}' not found"
        )

    info = VERSION_CONFIG[version].copy()
    info["version"] = version
    info["is_current"] = version == APIVersion.CURRENT.value

    return info

def get_all_versions() -> List[Dict[str, Any]]:
    """Get information about all API versions"""
    versions = []
    for version, config in VERSION_CONFIG.items():
        version_info = config.copy()
        version_info["version"] = version
        version_info["is_current"] = version == APIVersion.CURRENT.value
        versions.append(version_info)

    # Sort by release date (newest first)
    versions.sort(key=lambda x: x["release_date"], reverse=True)

    return versions

def check_version_compatibility(requested_version: str, required_version: str = None) -> bool:
    """Check if requested version is compatible with requirements"""
    if not required_version:
        return True

    if requested_version == required_version:
        return True

    # For now, only exact version matching
    # Future: Implement semantic versioning compatibility
    return False

def create_version_response(version: str, data: Any) -> Dict[str, Any]:
    """Create a versioned API response"""
    return {
        "data": data,
        "meta": {
            "api_version": version,
            "timestamp": datetime.utcnow().isoformat(),
            "version_info": VERSION_CONFIG.get(version, {})
        }
    }