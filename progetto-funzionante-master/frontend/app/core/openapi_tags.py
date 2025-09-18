"""
Enhanced OpenAPI Tags and Endpoint Organization

This module provides comprehensive OpenAPI tag definitions with detailed metadata
for organizing and categorizing API endpoints in the documentation.
"""

from typing import Dict, List, Any

# Enhanced Tags Metadata with comprehensive documentation
ENHANCED_TAGS_METADATA = [
    {
        "name": "Enhanced Authentication",
        "description": "Comprehensive user authentication and authorization system with JWT tokens, API keys, and OAuth2 flows. Includes user registration, login, password management, and security features.",
        "externalDocs": {
            "description": "Authentication Guide",
            "url": "https://docs.cash-revolution.com/api/authentication"
        }
    },
    {
        "name": "Enhanced Signals",
        "description": "Advanced trading signals management with AI-powered analysis, real-time market data integration, and comprehensive signal lifecycle management. Includes signal creation, validation, execution, and performance tracking.",
        "externalDocs": {
            "description": "Signals API Guide",
            "url": "https://docs.cash-revolution.com/api/signals"
        }
    },
    {
        "name": "Market Data",
        "description": "Real-time market data endpoints providing access to OANDA market feeds, historical data, technical indicators, and market sentiment analysis.",
        "externalDocs": {
            "description": "Market Data Documentation",
            "url": "https://docs.cash-revolution.com/api/market-data"
        }
    },
    {
        "name": "User Management",
        "description": "User profile management, account settings, subscription management, and user preferences configuration.",
        "externalDocs": {
            "description": "User Management Guide",
            "url": "https://docs.cash-revolution.com/api/users"
        }
    },
    {
        "name": "Administrative",
        "description": "Administrative endpoints for system management, database operations, user administration, and system monitoring.",
        "externalDocs": {
            "description": "Admin Guide",
            "url": "https://docs.cash-revolution.com/api/admin"
        }
    },
    {
        "name": "System Health",
        "description": "System health monitoring, performance metrics, cache management, and operational status endpoints.",
        "externalDocs": {
            "description": "Health Monitoring Guide",
            "url": "https://docs.cash-revolution.com/api/health"
        }
    },
    {
        "name": "API Documentation",
        "description": "Interactive API documentation generation, OpenAPI specification access, and SDK generation capabilities.",
        "externalDocs": {
            "description": "API Documentation Guide",
            "url": "https://docs.cash-revolution.com/api/documentation"
        }
    },
    {
        "name": "Error Documentation",
        "description": "Comprehensive error code documentation, error response examples, and troubleshooting guides.",
        "externalDocs": {
            "description": "Error Handling Guide",
            "url": "https://docs.cash-revolution.com/api/errors"
        }
    },
    {
        "name": "Security",
        "description": "Security-related endpoints including rate limiting, authentication status, security headers, and vulnerability reporting.",
        "externalDocs": {
            "description": "Security Guide",
            "url": "https://docs.cash-revolution.com/api/security"
        }
    },
    {
        "name": "Configuration",
        "description": "Configuration management, system settings, environment information, and feature flags.",
        "externalDocs": {
            "description": "Configuration Guide",
            "url": "https://docs.cash-revolution.com/api/configuration"
        }
    }
]

# Endpoint Organization Groups
ENDPOINT_GROUPS = {
    "authentication": {
        "public": [
            "/api/v2/auth/register",
            "/api/v2/auth/login",
            "/api/v2/auth/forgot-password",
            "/api/v2/auth/reset-password",
            "/api/v2/auth/verify-email"
        ],
        "protected": [
            "/api/v2/auth/logout",
            "/api/v2/auth/refresh-token",
            "/api/v2/auth/change-password",
            "/api/v2/auth/profile",
            "/api/v2/auth/update-profile",
            "/api/v2/auth/delete-account"
        ],
        "admin": [
            "/api/v2/auth/users",
            "/api/v2/auth/users/{user_id}",
            "/api/v2/auth/users/{user_id}/suspend",
            "/api/v2/auth/users/{user_id}/activate"
        ]
    },
    "signals": {
        "public": [
            "/api/v2/signals/public/latest",
            "/api/v2/signals/public/search",
            "/api/v2/signals/public/statistics"
        ],
        "protected": [
            "/api/v2/signals/create",
            "/api/v2/signals/my-signals",
            "/api/v2/signals/{signal_id}",
            "/api/v2/signals/{signal_id}/update",
            "/api/v2/signals/{signal_id}/delete",
            "/api/v2/signals/{signal_id}/execute",
            "/api/v2/signals/{signal_id}/performance"
        ],
        "premium": [
            "/api/v2/signals/premium/stream",
            "/api/v2/signals/premium/analysis",
            "/api/v2/signals/premium/backtest",
            "/api/v2/signals/premium/optimization"
        ],
        "admin": [
            "/api/v2/signals/admin/all",
            "/api/v2/signals/admin/statistics",
            "/api/v2/signals/admin/approve",
            "/api/v2/signals/admin/reject"
        ]
    },
    "market_data": {
        "public": [
            "/api/v2/market/symbols",
            "/api/v2/market/symbols/{symbol}/info",
            "/api/v2/market/symbols/{symbol}/price",
            "/api/v2/market/symbols/{symbol}/history"
        ],
        "protected": [
            "/api/v2/market/stream",
            "/api/v2/market/technical-indicators",
            "/api/v2/market/sentiment-analysis",
            "/api/v2/market/volatility-index"
        ],
        "premium": [
            "/api/v2/market/real-time-analytics",
            "/api/v2/market/pattern-recognition",
            "/api/v2/market/ai-insights"
        ]
    },
    "system": {
        "public": [
            "/health",
            "/config/validate",
            "/config/info",
            "/api/docs/preview"
        ],
        "protected": [
            "/cache/health",
            "/cache/metrics",
            "/ml-system/status",
            "/api/errors/status-codes",
            "/api/errors/examples"
        ],
        "admin": [
            "/cache/invalidate",
            "/cache/warming/metrics",
            "/cache/warming/trigger",
            "/api/docs/generate"
        ]
    }
}

# Version-specific endpoint mappings
VERSION_MAPPINGS = {
    "v1": {
        "deprecated": True,
        "sunset_date": "2024-12-31",
        "endpoints": [
            "/auth/*",
            "/api/*",
            "/signals/*",
            "/users/*",
            "/admin/*"
        ]
    },
    "v2": {
        "deprecated": False,
        "stable": True,
        "endpoints": [
            "/api/v2/*",
            "/api/docs/*",
            "/api/errors/*"
        ]
    }
}

# Rate limiting configurations by endpoint group
RATE_LIMITING_CONFIGS = {
    "authentication": {
        "requests_per_minute": 5,
        "burst_limit": 2,
        "window_size": 60
    },
    "signals": {
        "requests_per_minute": 100,
        "burst_limit": 10,
        "window_size": 60
    },
    "market_data": {
        "requests_per_minute": 60,
        "burst_limit": 5,
        "window_size": 60
    },
    "system": {
        "requests_per_minute": 30,
        "burst_limit": 3,
        "window_size": 60
    },
    "admin": {
        "requests_per_minute": 10,
        "burst_limit": 1,
        "window_size": 60
    }
}

# Security requirements by endpoint group
SECURITY_REQUIREMENTS_BY_GROUP = {
    "authentication": {
        "public": [],
        "protected": ["bearerAuth"],
        "admin": ["bearerAuth"]
    },
    "signals": {
        "public": [],
        "protected": ["bearerAuth"],
        "premium": ["bearerAuth"],
        "admin": ["bearerAuth"]
    },
    "market_data": {
        "public": [],
        "protected": ["bearerAuth"],
        "premium": ["bearerAuth"]
    },
    "system": {
        "public": [],
        "protected": ["bearerAuth"],
        "admin": ["bearerAuth"]
    }
}

# OpenAPI extensions for enhanced documentation
OPENAPI_EXTENSIONS = {
    "x-tag-groups": [
        {
            "name": "Core Features",
            "tags": ["Enhanced Authentication", "Enhanced Signals", "Market Data"]
        },
        {
            "name": "System Operations",
            "tags": ["System Health", "Configuration", "Security"]
        },
        {
            "name": "Developer Tools",
            "tags": ["API Documentation", "Error Documentation"]
        },
        {
            "name": "Administration",
            "tags": ["Administrative", "User Management"]
        }
    ],
    "x-endpoint-groups": ENDPOINT_GROUPS,
    "x-rate-limiting": RATE_LIMITING_CONFIGS,
    "x-version-mappings": VERSION_MAPPINGS,
    "x-security-requirements": SECURITY_REQUIREMENTS_BY_GROUP
}

def get_tags_metadata() -> List[Dict[str, Any]]:
    """Get enhanced tags metadata for OpenAPI documentation

    Returns:
        List[Dict[str, Any]]: Enhanced tags metadata
    """
    return ENHANCED_TAGS_METADATA

def get_endpoint_groups() -> Dict[str, Dict[str, List[str]]]:
    """Get endpoint organization groups

    Returns:
        Dict[str, Dict[str, List[str]]]: Endpoint groups by category
    """
    return ENDPOINT_GROUPS

def get_openapi_extensions() -> Dict[str, Any]:
    """Get OpenAPI extensions for enhanced documentation

    Returns:
        Dict[str, Any]: OpenAPI extensions
    """
    return OPENAPI_EXTENSIONS

def get_security_requirements_for_group(group: str, access_level: str = "public") -> List[Dict[str, List[str]]]:
    """Get security requirements for a specific endpoint group and access level

    Args:
        group: Endpoint group name
        access_level: Access level (public, protected, premium, admin)

    Returns:
        List[Dict[str, List[str]]]: Security requirements
    """
    return SECURITY_REQUIREMENTS_BY_GROUP.get(group, {}).get(access_level, [])

def get_rate_limiting_config(group: str) -> Dict[str, int]:
    """Get rate limiting configuration for an endpoint group

    Args:
        group: Endpoint group name

    Returns:
        Dict[str, int]: Rate limiting configuration
    """
    return RATE_LIMITING_CONFIGS.get(group, RATE_LIMITING_CONFIGS["system"])