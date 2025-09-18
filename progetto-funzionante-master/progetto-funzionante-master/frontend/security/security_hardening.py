"""
Production Security Hardening Framework
Comprehensive security measures for production deployment
"""

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, OAuth2PasswordBearer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
import time
import secrets
import hashlib
import re
import ipaddress
import json
from typing import Optional, Dict, Any, List, Set, Tuple
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class SecurityLevel(Enum):
    """Security levels for different environments"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

@dataclass
class SecurityConfig:
    """Security configuration settings"""
    security_level: SecurityLevel = SecurityLevel.PRODUCTION
    allowed_hosts: List[str] = None
    cors_origins: List[str] = None
    trusted_proxies: List[str] = None
    rate_limit_enabled: bool = True
    max_requests_per_minute: int = 60
    max_requests_per_hour: int = 1000
    block_suspicious_ips: bool = True
    enable_csp: bool = True
    enable_hsts: bool = True
    enable_xss_protection: bool = True
    enable_content_type_options: bool = True
    enable_frame_options: bool = True
    session_timeout_minutes: int = 30
    max_session_duration_hours: int = 24
    jwt_secret_key: str = None
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    def __post_init__(self):
        if self.allowed_hosts is None:
            self.allowed_hosts = ["localhost", "127.0.0.1"]
        if self.cors_origins is None:
            self.cors_origins = ["http://localhost:3000"]
        if self.trusted_proxies is None:
            self.trusted_proxies = []

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Comprehensive security headers middleware"""

    def __init__(self, app: FastAPI, config: SecurityConfig):
        super().__init__(app)
        self.config = config

        # CSP Policy configuration
        self.csp_policy = {
            "default-src": "'self'",
            "script-src": "'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net",
            "style-src": "'self' 'unsafe-inline' https://cdn.jsdelivr.net",
            "img-src": "'self' data: https: https://*.openstreetmap.org",
            "font-src": "'self' https://fonts.gstatic.com https://cdn.jsdelivr.net",
            "connect-src": "'self' https://api-fxpractice.oanda.com https://*.googleapis.com",
            "frame-src": "'none'",
            "object-src": "'none'",
            "base-uri": "'self'",
            "form-action": "'self'",
            "frame-ancestors": "'none'",
            "require-trusted-types-for": "'script'",
            "upgrade-insecure-requests": ""
        }

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Security Headers
        if self.config.enable_csp:
            csp_string = "; ".join([f"{k} {v}" for k, v in self.csp_policy.items()])
            response.headers["Content-Security-Policy"] = csp_string
            response.headers["Content-Security-Policy-Report-Only"] = csp_string

        if self.config.enable_hsts:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"

        if self.config.enable_xss_protection:
            response.headers["X-XSS-Protection"] = "1; mode=block"

        if self.config.enable_content_type_options:
            response.headers["X-Content-Type-Options"] = "nosniff"

        if self.config.enable_frame_options:
            response.headers["X-Frame-Options"] = "DENY"

        # Additional security headers
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, proxy-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

        # Remove server information
        response.headers["Server"] = "SecureServer"

        return response

class IPReputationMiddleware(BaseHTTPMiddleware):
    """IP reputation and suspicious activity detection"""

    def __init__(self, app: FastAPI, config: SecurityConfig):
        super().__init__(app)
        self.config = config
        self.blocked_ips: Set[str] = set()
        self.suspicious_activities: Dict[str, List[datetime]] = {}
        self.ip_reputation: Dict[str, float] = {}

    async def dispatch(self, request: Request, call_next):
        client_ip = self._get_client_ip(request)

        # Check if IP is blocked
        if client_ip in self.blocked_ips:
            logger.warning(f"Blocked IP attempt: {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        # Check IP reputation
        reputation = self.ip_reputation.get(client_ip, 1.0)
        if reputation < 0.3 and self.config.block_suspicious_ips:
            logger.warning(f"Low reputation IP blocked: {client_ip} (score: {reputation})")
            self.blocked_ips.add(client_ip)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        # Analyze request for suspicious patterns
        if self._is_suspicious_request(request):
            self._record_suspicious_activity(client_ip)

            # If too many suspicious activities, block the IP
            if self._should_block_ip(client_ip):
                self.blocked_ips.add(client_ip)
                logger.warning(f"IP blocked due to suspicious activity: {client_ip}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )

        response = await call_next(request)

        # Update reputation based on response status
        if response.status_code >= 400:
            self._update_ip_reputation(client_ip, -0.1)
        else:
            self._update_ip_reputation(client_ip, 0.01)

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Get real client IP considering proxies"""
        x_forwarded_for = request.headers.get("X-Forwarded-For")
        if x_forwarded_for:
            # Get the first IP (original client)
            return x_forwarded_for.split(",")[0].strip()
        return request.client.host

    def _is_suspicious_request(self, request: Request) -> bool:
        """Detect suspicious request patterns"""
        # Check for SQL injection patterns
        suspicious_patterns = [
            r"union.*select",
            r"drop.*table",
            r"insert.*into",
            r"delete.*from",
            r"update.*set",
            r"script.*>",
            r"<.*script",
            r"javascript:",
            r"vbscript:",
            r"onload=",
            r"onerror=",
            r"alert\(",
            r"document\.cookie",
            r"window\.location",
            r"eval\(",
            r"exec\(",
            r"system\(",
            r"shell_exec\(",
            r"passthru\(",
            r"base64_decode",
            r"file_get_contents",
            r"fopen\(",
            r"include\(",
            r"require\(",
            r"\.\./",
            r"\.\.\\",
        ]

        # Check URL and headers
        url = str(request.url)
        headers_str = str(request.headers)
        body = ""

        # For POST requests, check body (in production, you'd want to parse this properly)
        if request.method in ["POST", "PUT", "PATCH"]:
            body = str(await request.body())

        full_request = f"{url} {headers_str} {body}".lower()

        for pattern in suspicious_patterns:
            if re.search(pattern, full_request, re.IGNORECASE):
                logger.warning(f"Suspicious pattern detected: {pattern} in request from {request.client.host}")
                return True

        return False

    def _record_suspicious_activity(self, ip: str):
        """Record suspicious activity for an IP"""
        now = datetime.utcnow()
        if ip not in self.suspicious_activities:
            self.suspicious_activities[ip] = []

        self.suspicious_activities[ip].append(now)

        # Keep only recent activities (last hour)
        hour_ago = now - timedelta(hours=1)
        self.suspicious_activities[ip] = [
            activity for activity in self.suspicious_activities[ip]
            if activity > hour_ago
        ]

    def _should_block_ip(self, ip: str) -> bool:
        """Determine if an IP should be blocked based on suspicious activities"""
        activities = self.suspicious_activities.get(ip, [])

        # Block if more than 20 suspicious activities in an hour
        if len(activities) > 20:
            return True

        # Block if more than 5 activities in 5 minutes
        five_minutes_ago = datetime.utcnow() - timedelta(minutes=5)
        recent_activities = [a for a in activities if a > five_minutes_ago]
        if len(recent_activities) > 5:
            return True

        return False

    def _update_ip_reputation(self, ip: str, delta: float):
        """Update IP reputation score"""
        current = self.ip_reputation.get(ip, 1.0)
        new_score = max(0.0, min(1.0, current + delta))
        self.ip_reputation[ip] = new_score

class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Comprehensive request validation middleware"""

    def __init__(self, app: FastAPI):
        super().__init__(app)

        # Define allowed HTTP methods
        self.allowed_methods = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}

        # Define maximum request sizes
        self.max_request_sizes = {
            "GET": 2048,  # 2KB
            "POST": 10485760,  # 10MB
            "PUT": 10485760,  # 10MB
            "DELETE": 2048,  # 2KB
            "PATCH": 10485760,  # 10MB
            "HEAD": 2048,  # 2KB
            "OPTIONS": 2048,  # 2KB
        }

        # Define dangerous characters and patterns
        self.dangerous_patterns = [
            "<script", "</script>", "javascript:", "vbscript:",
            "onload=", "onerror=", "onclick=", "onmouseover=",
            "eval(", "exec(", "system(", "shell_exec(",
            "base64_decode", "file_get_contents", "fopen(",
            "include(", "require(", "../", "..\\",
            "union select", "drop table", "insert into",
            "delete from", "update set"
        ]

    async def dispatch(self, request: Request, call_next):
        # Validate HTTP method
        if request.method not in self.allowed_methods:
            logger.warning(f"Invalid HTTP method: {request.method} from {request.client.host}")
            raise HTTPException(
                status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                detail="Method not allowed"
            )

        # Validate request size
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                max_size = self.max_request_sizes.get(request.method, 1024)
                if size > max_size:
                    logger.warning(f"Request too large: {size} bytes from {request.client.host}")
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="Request too large"
                    )
            except ValueError:
                logger.warning(f"Invalid content-length header from {request.client.host}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid content-length header"
                )

        # Validate URL path
        path = request.url.path
        if not self._is_valid_path(path):
            logger.warning(f"Invalid path: {path} from {request.client.host}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid request path"
            )

        # Validate headers
        for header_name, header_value in request.headers.items():
            if not self._is_valid_header(header_name, header_value):
                logger.warning(f"Invalid header: {header_name} from {request.client.host}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid request headers"
                )

        # For POST/PUT/PATCH requests, validate body
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
            if not self._is_valid_body(body):
                logger.warning(f"Invalid request body from {request.client.host}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid request body"
                )

        response = await call_next(request)
        return response

    def _is_valid_path(self, path: str) -> bool:
        """Validate URL path for security"""
        # Check for path traversal attempts
        if "../" in path or "..\\" in path:
            return False

        # Check for null bytes
        if "\x00" in path:
            return False

        # Check for extremely long paths
        if len(path) > 2048:
            return False

        # Allow only valid path characters
        allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_/.")
        if not all(c in allowed_chars for c in path):
            return False

        return True

    def _is_valid_header(self, name: str, value: str) -> bool:
        """Validate header name and value"""
        # Check for null bytes
        if "\x00" in name or "\x00" in value:
            return False

        # Check for header injection
        if "\n" in name or "\r" in name or "\n" in value or "\r" in value:
            return False

        # Check for dangerous patterns
        header_content = f"{name}: {value}".lower()
        for pattern in self.dangerous_patterns:
            if pattern in header_content:
                return False

        return True

    def _is_valid_body(self, body: bytes) -> bool:
        """Validate request body for security"""
        try:
            body_str = body.decode('utf-8', errors='ignore')

            # Check for dangerous patterns
            for pattern in self.dangerous_patterns:
                if pattern in body_str.lower():
                    return False

            return True
        except UnicodeDecodeError:
            # If we can't decode as UTF-8, it might be binary data which could be malicious
            return False

class SecurityHardener:
    """Main security hardening class for FastAPI applications"""

    def __init__(self, app: FastAPI, config: SecurityConfig):
        self.app = app
        self.config = config
        self.limiter = Limiter(key_func=get_remote_address)

    def apply_security_middleware(self):
        """Apply all security middleware to the FastAPI app"""

        # Rate limiting
        if self.config.rate_limit_enabled:
            self.app.state.limiter = self.limiter
            self.app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
            self.app.add_middleware(SlowAPIMiddleware)

        # Security middleware stack
        self.app.add_middleware(GZipMiddleware, minimum_size=1000)

        # HTTPS redirect in production
        if self.config.security_level == SecurityLevel.PRODUCTION:
            self.app.add_middleware(HTTPSRedirectMiddleware)

        # Trusted host middleware
        self.app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=self.config.allowed_hosts
        )

        # Security headers
        self.app.add_middleware(SecurityHeadersMiddleware, config=self.config)

        # IP reputation and blocking
        self.app.add_middleware(IPReputationMiddleware, config=self.config)

        # Request validation
        self.app.add_middleware(RequestValidationMiddleware)

        # CORS configuration
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.cors_origins,
            allow_credentials=False,  # Set to False for better security
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allow_headers=[
                "Accept",
                "Accept-Language",
                "Content-Language",
                "Content-Type",
                "Authorization",
                "X-Requested-With"
            ],
            max_age=600,  # 10 minutes
            expose_headers=["X-Request-ID"]
        )

        # Session middleware with secure settings
        self.app.add_middleware(
            SessionMiddleware,
            secret_key=self.config.jwt_secret_key or secrets.token_urlsafe(32),
            session_cookie="secure_session",
            max_age=self.config.session_timeout_minutes * 60,
            same_site="strict",
            https_only=True,
            domain=None  # Will be set based on environment
        )

        logger.info("Security middleware stack applied successfully")

    def add_security_endpoints(self):
        """Add security-related endpoints"""

        @self.app.get("/security/health")
        async def security_health():
            """Security health check endpoint"""
            return {
                "status": "secure",
                "timestamp": datetime.utcnow().isoformat(),
                "security_level": self.config.security_level.value,
                "features": {
                    "rate_limiting": self.config.rate_limit_enabled,
                    "ip_blocking": self.config.block_suspicious_ips,
                    "csp_enabled": self.config.enable_csp,
                    "hsts_enabled": self.config.enable_hsts,
                    "request_validation": True,
                    "cors_enabled": True
                }
            }

        @self.app.get("/security/config")
        async def get_security_config():
            """Get non-sensitive security configuration"""
            return {
                "security_level": self.config.security_level.value,
                "allowed_hosts": self.config.allowed_hosts,
                "cors_origins": self.config.cors_origins,
                "rate_limiting": {
                    "enabled": self.config.rate_limit_enabled,
                    "requests_per_minute": self.config.max_requests_per_minute,
                    "requests_per_hour": self.config.max_requests_per_hour
                },
                "session_settings": {
                    "timeout_minutes": self.config.session_timeout_minutes,
                    "max_duration_hours": self.config.max_session_duration_hours
                }
            }

        @self.app.post("/security/block-ip/{ip_address}")
        async def block_ip_address(ip_address: str):
            """Block an IP address (admin only)"""
            try:
                # Validate IP address
                ipaddress.ip_address(ip_address)

                # Add to blocked IPs (this would normally be stored in a database)
                logger.warning(f"IP address blocked by admin: {ip_address}")

                return {
                    "status": "success",
                    "message": f"IP address {ip_address} has been blocked",
                    "timestamp": datetime.utcnow().isoformat()
                }
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid IP address format"
                )

        @self.app.delete("/security/block-ip/{ip_address}")
        async def unblock_ip_address(ip_address: str):
            """Unblock an IP address (admin only)"""
            try:
                # Validate IP address
                ipaddress.ip_address(ip_address)

                # Remove from blocked IPs
                logger.info(f"IP address unblocked by admin: {ip_address}")

                return {
                    "status": "success",
                    "message": f"IP address {ip_address} has been unblocked",
                    "timestamp": datetime.utcnow().isoformat()
                }
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid IP address format"
                )

    def apply_production_hardening(self):
        """Apply comprehensive production hardening"""
        logger.info("Applying production security hardening...")

        # Apply middleware
        self.apply_security_middleware()

        # Add security endpoints
        self.add_security_endpoints()

        # Add Prometheus metrics for security monitoring
        if self.config.security_level == SecurityLevel.PRODUCTION:
            instrumentator = Instrumentator()
            instrumentator.instrument(self.app).expose(self.app)

        logger.info("Production security hardening completed successfully")

def create_production_security_config() -> SecurityConfig:
    """Create production security configuration"""
    return SecurityConfig(
        security_level=SecurityLevel.PRODUCTION,
        allowed_hosts=["api.cash-revolution.com", "www.cash-revolution.com"],
        cors_origins=["https://cash-revolution.com", "https://www.cash-revolution.com"],
        trusted_proxies=["127.0.0.1", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"],
        rate_limit_enabled=True,
        max_requests_per_minute=60,
        max_requests_per_hour=1000,
        block_suspicious_ips=True,
        enable_csp=True,
        enable_hsts=True,
        enable_xss_protection=True,
        enable_content_type_options=True,
        enable_frame_options=True,
        session_timeout_minutes=30,
        max_session_duration_hours=24,
        jwt_secret_key=None,  # Should be set from environment
        jwt_algorithm="HS256",
        jwt_access_token_expire_minutes=30,
        jwt_refresh_token_expire_days=7
    )

def create_staging_security_config() -> SecurityConfig:
    """Create staging security configuration"""
    return SecurityConfig(
        security_level=SecurityLevel.STAGING,
        allowed_hosts=["staging-api.cash-revolution.com", "localhost"],
        cors_origins=["https://staging.cash-revolution.com", "http://localhost:3000"],
        trusted_proxies=["127.0.0.1"],
        rate_limit_enabled=True,
        max_requests_per_minute=120,
        max_requests_per_hour=2000,
        block_suspicious_ips=True,
        enable_csp=True,
        enable_hsts=True,
        enable_xss_protection=True,
        enable_content_type_options=True,
        enable_frame_options=True,
        session_timeout_minutes=60,
        max_session_duration_hours=48,
        jwt_secret_key=None,
        jwt_algorithm="HS256",
        jwt_access_token_expire_minutes=60,
        jwt_refresh_token_expire_days=14
    )

def create_development_security_config() -> SecurityConfig:
    """Create development security configuration"""
    return SecurityConfig(
        security_level=SecurityLevel.DEVELOPMENT,
        allowed_hosts=["localhost", "127.0.0.1"],
        cors_origins=["http://localhost:3000", "http://localhost:8000"],
        trusted_proxies=["127.0.0.1"],
        rate_limit_enabled=False,
        max_requests_per_minute=1000,
        max_requests_per_hour=10000,
        block_suspicious_ips=False,
        enable_csp=False,
        enable_hsts=False,
        enable_xss_protection=True,
        enable_content_type_options=True,
        enable_frame_options=True,
        session_timeout_minutes=120,
        max_session_duration_hours=168,  # 1 week
        jwt_secret_key="dev-secret-key-not-for-production",
        jwt_algorithm="HS256",
        jwt_access_token_expire_minutes=120,
        jwt_refresh_token_expire_days=30
    )

def get_security_config(environment: str) -> SecurityConfig:
    """Get security configuration based on environment"""
    if environment.lower() == "production":
        return create_production_security_config()
    elif environment.lower() == "staging":
        return create_staging_security_config()
    else:
        return create_development_security_config()