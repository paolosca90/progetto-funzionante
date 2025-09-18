"""
Secure Headers and CSP Policies Module

Provides comprehensive security headers and Content Security Policy implementation including:
- Security headers middleware
- Content Security Policy (CSP) generation
- CORS configuration
- HSTS implementation
- XSS protection
- Clickjacking protection
- MIME type sniffing prevention
- Referrer policy
- Feature policy
- Permissions policy
- Dynamic CSP generation
- Security header validation
- Browser compatibility optimization

"""

import re
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
import logging
from fastapi import Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)

class SecurityHeader(Enum):
    """Security header types"""
    CONTENT_SECURITY_POLICY = "Content-Security-Policy"
    CONTENT_SECURITY_POLICY_REPORT_ONLY = "Content-Security-Policy-Report-Only"
    STRICT_TRANSPORT_SECURITY = "Strict-Transport-Security"
    X_CONTENT_TYPE_OPTIONS = "X-Content-Type-Options"
    X_FRAME_OPTIONS = "X-Frame-Options"
    X_XSS_PROTECTION = "X-XSS-Protection"
    REFERRER_POLICY = "Referrer-Policy"
    PERMISSIONS_POLICY = "Permissions-Policy"
    CACHE_CONTROL = "Cache-Control"
    PRAGMA = "Pragma"
    EXPIRES = "Expires"
    X_PERMITTED_CROSS_DOMAIN_POLICIES = "X-Permitted-Cross-Domain-Policies"
    X_DOWNLOAD_OPTIONS = "X-Download-Options"
    X_CONTENT_SECURITY_POLICY_REPORT_ONLY = "X-Content-Security-Policy-Report-Only"

class CSPDirective(Enum):
    """Content Security Policy directives"""
    DEFAULT_SRC = "default-src"
    SCRIPT_SRC = "script-src"
    STYLE_SRC = "style-src"
    IMG_SRC = "img-src"
    CONNECT_SRC = "connect-src"
    FONT_SRC = "font-src"
    OBJECT_SRC = "object-src"
    MEDIA_SRC = "media-src"
    FRAME_SRC = "frame-src"
    FRAME_ANCESTORS = "frame-ancestors"
    FORM_ACTION = "form-action"
    BASE_URI = "base-uri"
    MANIFEST_SRC = "manifest-src"
    REPORT_URI = "report-uri"
    REPORT_TO = "report-to"
    WORKER_SRC = "worker-src"
    CHILD_SRC = "child-src"
    PREFETCH_SRC = "prefetch-src"
    NAVIGATE_TO = "navigate-to"

class CSPKeyword(Enum):
    """CSP keywords"""
    SELF = "'self'"
    NONE = "'none'"
    UNSAFE_INLINE = "'unsafe-inline'"
    UNSAFE_EVAL = "'unsafe-eval'"
    STRICT_DYNAMIC = "'strict-dynamic'"
    REPORT_SAMPLE = "'report-sample'"
    UNSAFE_HASHES = "'unsafe-hashes'"

@dataclass
class CSPSource:
    """CSP source configuration"""
    source: str
    scheme: Optional[str] = None
    host: Optional[str] = None
    port: Optional[str] = None
    path: Optional[str] = None
    is_wildcard: bool = False
    is_nonce: bool = False
    is_hash: bool = False
    hash_algorithm: Optional[str] = None
    hash_value: Optional[str] = None

@dataclass
class CSPPolicy:
    """Content Security Policy configuration"""
    version: str = "3"
    report_only: bool = False
    enable_reporting: bool = True
    report_endpoint: Optional[str] = None
    report_to: Optional[str] = None
    block_all_mixed_content: bool = True
    upgrade_insecure_requests: bool = True
    directives: Dict[CSPDirective, List[Union[str, CSPKeyword, CSPSource]]] = field(default_factory=dict)
    nonces: Dict[str, str] = field(default_factory=dict)
    hashes: Dict[str, List[str]] = field(default_factory=dict)
    sandbox: Optional[str] = None
    require_trusted_types_for: Optional[str] = None

@dataclass
class SecurityHeaderConfig:
    """Security header configuration"""
    enable_hsts: bool = True
    hsts_max_age: int = 31536000  # 1 year
    hsts_include_subdomains: bool = True
    hsts_preload: bool = True
    enable_csp: bool = True
    enable_csp_report_only: bool = False
    enable_xss_protection: bool = True
    enable_content_type_options: bool = True
    enable_frame_options: bool = True
    frame_options_value: str = "DENY"
    enable_referrer_policy: bool = True
    referrer_policy_value: str = "strict-origin-when-cross-origin"
    enable_permissions_policy: bool = True
    enable_cache_control: bool = True
    cache_control_value: str = "no-store, no-cache, must-revalidate, proxy-revalidate"
    enable_corp: bool = True
    corp_value: str = "same-origin"
    enable_coop: bool = True
    coop_value: str = "same-origin"
    enable_coep: bool = True
    trusted_hosts: List[str] = field(default_factory=list)
    allowed_origins: List[str] = field(default_factory=list)
    allowed_methods: List[str] = field(default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    allowed_headers: List[str] = field(default_factory=lambda: ["Content-Type", "Authorization", "X-Requested-With"])
    allow_credentials: bool = False
    allow_origin_regex: Optional[str] = None

class CSPViolationReporter:
    """CSP violation reporting handler"""

    def __init__(self, report_endpoint: str = "/api/security/csp-report"):
        self.report_endpoint = report_endpoint
        self.violation_logs = []
        self.violation_patterns = {}

    def log_violation(self, violation_data: Dict[str, Any], client_ip: str):
        """Log CSP violation"""
        violation = {
            'timestamp': datetime.utcnow().isoformat(),
            'client_ip': client_ip,
            'user_agent': violation_data.get('user-agent', ''),
            'document_uri': violation_data.get('document-uri', ''),
            'violated_directive': violation_data.get('violated-directive', ''),
            'effective_directive': violation_data.get('effective-directive', ''),
            'original_policy': violation_data.get('original-policy', ''),
            'disposition': violation_data.get('disposition', ''),
            'blocked_uri': violation_data.get('blocked-uri', ''),
            'line_number': violation_data.get('line-number'),
            'column_number': violation_data.get('column-number'),
            'source_file': violation_data.get('source-file'),
            'status_code': violation_data.get('status-code'),
            'script_sample': violation_data.get('script-sample')
        }

        self.violation_logs.append(violation)

        # Analyze violation patterns
        self._analyze_violation_patterns(violation)

        # Log violation
        logger.warning(f"CSP violation detected: {violation['violated_directive']} from {client_ip}")

    def _analyze_violation_patterns(self, violation: Dict[str, Any]):
        """Analyze violation patterns for potential attacks"""
        directive = violation.get('violated_directive', '')
        blocked_uri = violation.get('blocked_uri', '')

        if not directive:
            return

        # Initialize pattern tracking
        if directive not in self.violation_patterns:
            self.violation_patterns[directive] = {
                'count': 0,
                'blocked_uris': set(),
                'client_ips': set(),
                'first_seen': violation['timestamp'],
                'last_seen': violation['timestamp']
            }

        pattern = self.violation_patterns[directive]
        pattern['count'] += 1
        pattern['blocked_uris'].add(blocked_uri)
        pattern['client_ips'].add(violation['client_ip'])
        pattern['last_seen'] = violation['timestamp']

        # Check for suspicious patterns
        if pattern['count'] > 100:  # High violation count
            logger.warning(f"Suspicious CSP violation pattern detected: {directive} - {pattern['count']} violations")

    def get_violation_summary(self) -> Dict[str, Any]:
        """Get violation summary"""
        return {
            'total_violations': len(self.violation_logs),
            'violations_by_directive': {
                directive: patterns['count']
                for directive, patterns in self.violation_patterns.items()
            },
            'unique_blocked_uris': len(set(
                v['blocked_uri'] for v in self.violation_logs if v['blocked_uri']
            )),
            'unique_client_ips': len(set(v['client_ip'] for v in self.violation_logs)),
            'recent_violations': len([
                v for v in self.violation_logs
                if (datetime.utcnow() - datetime.fromisoformat(v['timestamp'])).seconds < 3600
            ])
        }

class CSPGenerator:
    """Content Security Policy generator"""

    def __init__(self, config: SecurityHeaderConfig):
        self.config = config
        self.csp_violation_reporter = CSPViolationReporter()

    def generate_csp_policy(self, request: Request) -> CSPPolicy:
        """Generate CSP policy based on request context"""
        policy = CSPPolicy(
            version="3",
            report_only=self.config.enable_csp_report_only,
            enable_reporting=True,
            report_endpoint="/api/security/csp-report" if self.config.enable_csp_report_only else None
        )

        # Generate directive values
        self._generate_default_directives(policy)
        self._generate_script_directives(policy, request)
        self._generate_style_directives(policy, request)
        self._generate_media_directives(policy)
        self._generate_frame_directives(policy)
        self._generate_connect_directives(policy, request)
        self._generate_font_directives(policy)
        self._generate_other_directives(policy)

        return policy

    def _generate_default_directives(self, policy: CSPPolicy):
        """Generate default-src directive"""
        policy.directives[CSPDirective.DEFAULT_SRC] = [CSPKeyword.SELF]

        if self.config.block_all_mixed_content:
            policy.directives[CSPDirective.DEFAULT_SRC].append("https:")

    def _generate_script_directives(self, policy: CSPPolicy, request: Request):
        """Generate script-src directive"""
        script_sources = [CSPKeyword.SELF]

        # Add unsafe-inline for development (consider removing in production)
        if self._is_development_environment(request):
            script_sources.append(CSPKeyword.UNSAFE_INLINE)
            script_sources.append(CSPKeyword.UNSAFE_EVAL)

        # Add specific script sources
        script_sources.extend([
            "https://cdn.jsdelivr.net",
            "https://unpkg.com",
            "https://cdnjs.cloudflare.com"
        ])

        policy.directives[CSPDirective.SCRIPT_SRC] = script_sources

    def _generate_style_directives(self, policy: CSPPolicy, request: Request):
        """Generate style-src directive"""
        style_sources = [CSPKeyword.SELF]

        # Add unsafe-inline for development
        if self._is_development_environment(request):
            style_sources.append(CSPKeyword.UNSAFE_INLINE)

        # Add specific style sources
        style_sources.extend([
            "https://cdn.jsdelivr.net",
            "https://unpkg.com",
            "https://cdnjs.cloudflare.com"
        ])

        policy.directives[CSPDirective.STYLE_SRC] = style_sources

    def _generate_media_directives(self, policy: CSPPolicy):
        """Generate media and image directives"""
        policy.directives[CSPDirective.IMG_SRC] = [
            CSPKeyword.SELF,
            "data:",
            "https:",
            "blob:"
        ]

        policy.directives[CSPDirective.MEDIA_SRC] = [
            CSPKeyword.SELF,
            "data:",
            "https:"
        ]

        policy.directives[CSPDirective.FONT_SRC] = [
            CSPKeyword.SELF,
            "https://cdn.jsdelivr.net",
            "https://unpkg.com",
            "https://cdnjs.cloudflare.com"
        ]

    def _generate_frame_directives(self, policy: CSPPolicy):
        """Generate frame-related directives"""
        policy.directives[CSPDirective.FRAME_SRC] = [CSPKeyword.SELF]
        policy.directives[CSPDirective.FRAME_ANCESTORS] = [CSPKeyword.SELF]

    def _generate_connect_directives(self, policy: CSPPolicy, request: Request):
        """Generate connect-src directive"""
        connect_sources = [CSPKeyword.SELF]

        # Add API endpoints
        host = request.url.hostname
        if host:
            connect_sources.extend([
                f"wss://{host}",
                f"https://{host}"
            ])

        # Add external API endpoints
        connect_sources.extend([
            "https://api.oanda.com",
            "https://generativelanguage.googleapis.com"
        ])

        policy.directives[CSPDirective.CONNECT_SRC] = connect_sources

    def _generate_font_directives(self, policy: CSPPolicy):
        """Generate font-src directive"""
        policy.directives[CSPDirective.FONT_SRC] = [
            CSPKeyword.SELF,
            "https://cdn.jsdelivr.net",
            "https://unpkg.com",
            "https://cdnjs.cloudflare.com",
            "data:"
        ]

    def _generate_other_directives(self, policy: CSPPolicy):
        """Generate other security directives"""
        policy.directives[CSPDirective.OBJECT_SRC] = [CSPKeyword.NONE]
        policy.directives[CSPDirective.BASE_URI] = [CSPKeyword.SELF]
        policy.directives[CSPDirective.FORM_ACTION] = [CSPKeyword.SELF]

        # Add report-uri if reporting is enabled
        if policy.enable_reporting and policy.report_endpoint:
            policy.directives[CSPDirective.REPORT_URI] = [policy.report_endpoint]

        # Add upgrade-insecure-requests if enabled
        if self.config.upgrade_insecure_requests:
            policy.directives[CSPDirective.UPGRADE_INSECURE_REQUESTS] = []  # Empty list means directive is present

        # Add block-all-mixed-content if enabled
        if self.config.block_all_mixed_content:
            policy.directives[CSPDirective.BLOCK_ALL_MIXED_CONTENT] = []  # Empty list means directive is present

    def _is_development_environment(self, request: Request) -> bool:
        """Check if running in development environment"""
        # Simple check - in production, use environment variables
        return "localhost" in request.url.hostname or "127.0.0.1" in request.url.hostname

    def generate_csp_header(self, policy: CSPPolicy) -> str:
        """Generate CSP header string from policy"""
        directives = []

        for directive, sources in policy.directives.items():
            if sources:
                source_strings = []
                for source in sources:
                    if isinstance(source, CSPKeyword):
                        source_strings.append(source.value)
                    elif isinstance(source, CSPSource):
                        source_strings.append(self._format_csp_source(source))
                    else:
                        source_strings.append(str(source))

                directives.append(f"{directive.value} {' '.join(source_strings)}")

        return "; ".join(directives)

    def _format_csp_source(self, source: CSPSource) -> str:
        """Format CSP source for header"""
        parts = []

        if source.scheme:
            parts.append(source.scheme + ":")

        if source.is_wildcard:
            parts.append("*")
        elif source.host:
            parts.append(source.host)

        if source.port:
            parts.append(":" + source.port)

        if source.path:
            parts.append(source.path)

        return "".join(parts)

    def generate_nonce(self) -> str:
        """Generate CSP nonce"""
        return secrets.token_urlsafe(16)

    def generate_hash(self, content: str, algorithm: str = "sha256") -> str:
        """Generate CSP hash for inline content"""
        if algorithm == "sha256":
            hash_obj = hashlib.sha256(content.encode('utf-8'))
        elif algorithm == "sha384":
            hash_obj = hashlib.sha384(content.encode('utf-8'))
        elif algorithm == "sha512":
            hash_obj = hashlib.sha512(content.encode('utf-8'))
        else:
            raise ValueError(f"Unsupported hash algorithm: {algorithm}")

        return f"'{algorithm}-{hash_obj.hexdigest()}'"

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Security headers middleware"""

    def __init__(self, app, config: SecurityHeaderConfig):
        super().__init__(app)
        self.config = config
        self.csp_generator = CSPGenerator(config)
        self.csp_violation_reporter = CSPViolationReporter()

    async def dispatch(self, request: Request, call_next):
        """Apply security headers to response"""
        response = await call_next(request)

        # Apply security headers
        self._apply_security_headers(response, request)

        return response

    def _apply_security_headers(self, response: Response, request: Request):
        """Apply security headers to response"""
        # Content Security Policy
        if self.config.enable_csp:
            csp_policy = self.csp_generator.generate_csp_policy(request)
            csp_header = self.csp_generator.generate_csp_header(csp_policy)

            if self.config.enable_csp_report_only:
                response.headers[SecurityHeader.CONTENT_SECURITY_POLICY_REPORT_ONLY.value] = csp_header
            else:
                response.headers[SecurityHeader.CONTENT_SECURITY_POLICY.value] = csp_header

        # Strict Transport Security
        if self.config.enable_hsts:
            hsts_value = f"max-age={self.config.hsts_max_age}"
            if self.config.hsts_include_subdomains:
                hsts_value += "; includeSubDomains"
            if self.config.hsts_preload:
                hsts_value += "; preload"
            response.headers[SecurityHeader.STRICT_TRANSPORT_SECURITY.value] = hsts_value

        # X-Content-Type-Options
        if self.config.enable_content_type_options:
            response.headers[SecurityHeader.X_CONTENT_TYPE_OPTIONS.value] = "nosniff"

        # X-Frame-Options
        if self.config.enable_frame_options:
            response.headers[SecurityHeader.X_FRAME_OPTIONS.value] = self.config.frame_options_value

        # X-XSS-Protection
        if self.config.enable_xss_protection:
            response.headers[SecurityHeader.X_XSS_PROTECTION.value] = "1; mode=block"

        # Referrer Policy
        if self.config.enable_referrer_policy:
            response.headers[SecurityHeader.REFERRER_POLICY.value] = self.config.referrer_policy_value

        # Permissions Policy
        if self.config.enable_permissions_policy:
            permissions_policy = self._generate_permissions_policy()
            response.headers[SecurityHeader.PERMISSIONS_POLICY.value] = permissions_policy

        # Cache Control
        if self.config.enable_cache_control:
            response.headers[SecurityHeader.CACHE_CONTROL.value] = self.config.cache_control_value
            response.headers[SecurityHeader.PRAGMA.value] = "no-cache"
            response.headers[SecurityHeader.EXPIRES.value] = "0"

        # Cross-Origin policies
        if self.config.enable_corp:
            response.headers["Cross-Origin-Resource-Policy"] = self.config.corp_value

        if self.config.enable_coop:
            response.headers["Cross-Origin-Opener-Policy"] = self.config.coop_value

        if self.config.enable_coep:
            response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"

        # Remove server information
        if "Server" in response.headers:
            del response.headers["Server"]

        # Remove X-Powered-By
        if "X-Powered-By" in response.headers:
            del response.headers["X-Powered-By"]

    def _generate_permissions_policy(self) -> str:
        """Generate Permissions Policy header"""
        permissions = [
            "camera=()",
            "microphone=()",
            "geolocation=()",
            "payment=()",
            "usb=()",
            "magnetometer=()",
            "gyroscope=()",
            "accelerometer=()",
            "fullscreen=(self)",
            "payment=(self)",
            "sync-xhr=(self)",
            "document-domain=(self)"
        ]

        return ", ".join(permissions)

class SecurityHeadersManager:
    """Security headers management system"""

    def __init__(self, config: Optional[SecurityHeaderConfig] = None):
        self.config = config or SecurityHeaderConfig()
        self.csp_generator = CSPGenerator(self.config)
        self.csp_violation_reporter = CSPViolationReporter()
        self.header_validation_results = {}

    def get_current_config(self) -> Dict[str, Any]:
        """Get current security headers configuration"""
        return {
            'hsts_enabled': self.config.enable_hsts,
            'hsts_max_age': self.config.hsts_max_age,
            'hsts_include_subdomains': self.config.hsts_include_subdomains,
            'hsts_preload': self.config.hsts_preload,
            'csp_enabled': self.config.enable_csp,
            'csp_report_only': self.config.enable_csp_report_only,
            'xss_protection_enabled': self.config.enable_xss_protection,
            'content_type_options_enabled': self.config.enable_content_type_options,
            'frame_options_enabled': self.config.enable_frame_options,
            'referrer_policy_enabled': self.config.enable_referrer_policy,
            'permissions_policy_enabled': self.config.enable_permissions_policy,
            'cache_control_enabled': self.config.enable_cache_control,
            'trusted_hosts': self.config.trusted_hosts,
            'allowed_origins': self.config.allowed_origins
        }

    def validate_security_headers(self, response_headers: Dict[str, str]) -> Dict[str, Any]:
        """Validate security headers in response"""
        validation_results = {
            'valid_headers': [],
            'missing_headers': [],
            'invalid_headers': [],
            'recommendations': [],
            'security_score': 0.0
        }

        # Check required headers
        required_headers = [
            (SecurityHeader.CONTENT_SECURITY_POLICY.value, self.config.enable_csp),
            (SecurityHeader.STRICT_TRANSPORT_SECURITY.value, self.config.enable_hsts),
            (SecurityHeader.X_CONTENT_TYPE_OPTIONS.value, self.config.enable_content_type_options),
            (SecurityHeader.X_FRAME_OPTIONS.value, self.config.enable_frame_options),
            (SecurityHeader.X_XSS_PROTECTION.value, self.config.enable_xss_protection),
            (SecurityHeader.REFERRER_POLICY.value, self.config.enable_referrer_policy),
            (SecurityHeader.PERMISSIONS_POLICY.value, self.config.enable_permissions_policy),
        ]

        for header_name, is_enabled in required_headers:
            if is_enabled:
                if header_name in response_headers:
                    validation_results['valid_headers'].append(header_name)
                    # Validate header value
                    if header_name == SecurityHeader.STRICT_TRANSPORT_SECURITY.value:
                        self._validate_hsts_header(response_headers[header_name], validation_results)
                    elif header_name == SecurityHeader.CONTENT_SECURITY_POLICY.value:
                        self._validate_csp_header(response_headers[header_name], validation_results)
                else:
                    validation_results['missing_headers'].append(header_name)
                    validation_results['recommendations'].append(f"Add {header_name} header")

        # Calculate security score
        total_headers = len([h for h, enabled in required_headers if enabled])
        valid_headers = len(validation_results['valid_headers'])
        validation_results['security_score'] = (valid_headers / total_headers * 100) if total_headers > 0 else 0

        return validation_results

    def _validate_hsts_header(self, hsts_value: str, results: Dict[str, Any]):
        """Validate HSTS header value"""
        try:
            parts = hsts_value.split(';')
            max_age_part = parts[0].strip()

            if max_age_part.startswith('max-age='):
                max_age = int(max_age_part.split('=')[1])
                if max_age < 31536000:  # Less than 1 year
                    results['recommendations'].append("Consider increasing HSTS max-age to at least 1 year")
            else:
                results['invalid_headers'].append("Invalid HSTS header format")

        except Exception as e:
            results['invalid_headers'].append(f"Invalid HSTS header: {e}")

    def _validate_csp_header(self, csp_value: str, results: Dict[str, Any]):
        """Validate CSP header value"""
        try:
            directives = csp_value.split(';')
            has_default_src = any('default-src' in directive for directive in directives)
            has_script_src = any('script-src' in directive for directive in directives)

            if not has_default_src:
                results['recommendations'].append("Consider adding default-src directive to CSP")

            if not has_script_src:
                results['recommendations'].append("Consider adding script-src directive to CSP")

            # Check for unsafe directives
            if "'unsafe-inline'" in csp_value:
                results['recommendations'].append("Consider removing 'unsafe-inline' from CSP for better security")

            if "'unsafe-eval'" in csp_value:
                results['recommendations'].append("Consider removing 'unsafe-eval' from CSP for better security")

        except Exception as e:
            results['invalid_headers'].append(f"Invalid CSP header: {e}")

    def generate_security_report(self) -> Dict[str, Any]:
        """Generate security headers report"""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'configuration': self.get_current_config(),
            'csp_violations': self.csp_violation_reporter.get_violation_summary(),
            'header_recommendations': self._generate_header_recommendations(),
            'security_score': self._calculate_overall_security_score()
        }

    def _generate_header_recommendations(self) -> List[str]:
        """Generate header recommendations"""
        recommendations = []

        if not self.config.enable_hsts:
            recommendations.append("Enable HSTS for HTTPS enforcement")

        if not self.config.enable_csp:
            recommendations.append("Enable Content Security Policy for XSS protection")

        if self.config.enable_csp_report_only:
            recommendations.append("Consider switching from CSP report-only to enforcement mode")

        if self.config.hsts_max_age < 31536000:
            recommendations.append("Increase HSTS max-age to at least 1 year")

        if not self.config.hsts_preload:
            recommendations.append("Consider enabling HSTS preload")

        if not self.config.enable_permissions_policy:
            recommendations.append("Enable Permissions Policy for browser feature control")

        return recommendations

    def _calculate_overall_security_score(self) -> float:
        """Calculate overall security score"""
        score_factors = {
            'hsts_enabled': 15 if self.config.enable_hsts else 0,
            'csp_enabled': 20 if self.config.enable_csp else 0,
            'csp_enforcement': 10 if self.config.enable_csp and not self.config.enable_csp_report_only else 0,
            'xss_protection': 10 if self.config.enable_xss_protection else 0,
            'content_type_options': 10 if self.config.enable_content_type_options else 0,
            'frame_options': 10 if self.config.enable_frame_options else 0,
            'referrer_policy': 10 if self.config.enable_referrer_policy else 0,
            'permissions_policy': 15 if self.config.enable_permissions_policy else 0
        }

        return sum(score_factors.values())

    def update_config(self, **kwargs):
        """Update security headers configuration"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
                logger.info(f"Updated security header config: {key} = {value}")

    def get_csp_violation_report(self, hours: int = 24) -> Dict[str, Any]:
        """Get CSP violation report"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_violations = [
            v for v in self.csp_violation_reporter.violation_logs
            if datetime.fromisoformat(v['timestamp']) > cutoff_time
        ]

        return {
            'report_period_hours': hours,
            'total_violations': len(recent_violations),
            'violations_by_directive': self._count_violations_by_directive(recent_violations),
            'top_blocked_uris': self._get_top_blocked_uris(recent_violations),
            'top_client_ips': self._get_top_client_ips(recent_violations),
            'recent_violations': recent_violations[-10:]  # Last 10 violations
        }

    def _count_violations_by_directive(self, violations: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count violations by directive"""
        counts = {}
        for violation in violations:
            directive = violation.get('violated_directive', 'unknown')
            counts[directive] = counts.get(directive, 0) + 1
        return counts

    def _get_top_blocked_uris(self, violations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get top blocked URIs"""
        uri_counts = {}
        for violation in violations:
            uri = violation.get('blocked_uri', 'unknown')
            uri_counts[uri] = uri_counts.get(uri, 0) + 1

        return [
            {'uri': uri, 'count': count}
            for uri, count in sorted(uri_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        ]

    def _get_top_client_ips(self, violations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get top client IPs"""
        ip_counts = {}
        for violation in violations:
            ip = violation.get('client_ip', 'unknown')
            ip_counts[ip] = ip_counts.get(ip, 0) + 1

        return [
            {'ip': ip, 'count': count}
            for ip, count in sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        ]

# Security header validation endpoint models
class CSPViolationReport(BaseModel):
    """CSP violation report model"""
    document_uri: str
    referrer: str
    violated_directive: str
    effective_directive: str
    original_policy: str
    disposition: str
    blocked_uri: str
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    source_file: Optional[str] = None
    status_code: Optional[int] = None
    script_sample: Optional[str] = None

class SecurityValidationRequest(BaseModel):
    """Security validation request model"""
    url: str
    headers: Dict[str, str]

class SecurityValidationResponse(BaseModel):
    """Security validation response model"""
    valid: bool
    score: float
    recommendations: List[str]
    missing_headers: List[str]
    invalid_headers: List[str]

# Initialize global security headers manager
security_headers_config = SecurityHeaderConfig(
    enable_hsts=True,
    hsts_max_age=31536000,
    hsts_include_subdomains=True,
    hsts_preload=True,
    enable_csp=True,
    enable_csp_report_only=False,
    enable_xss_protection=True,
    enable_content_type_options=True,
    enable_frame_options=True,
    enable_referrer_policy=True,
    enable_permissions_policy=True,
    enable_cache_control=True,
    trusted_hosts=["localhost", "127.0.0.1"],
    allowed_origins=["http://localhost:8000", "https://localhost:8000"]
)

security_headers_manager = SecurityHeadersManager(security_headers_config)

# Example usage
if __name__ == "__main__":
    # Create security headers manager
    config = SecurityHeaderConfig(
        enable_hsts=True,
        enable_csp=True,
        enable_permissions_policy=True
    )

    manager = SecurityHeadersManager(config)

    # Generate security report
    report = manager.generate_security_report()
    print(f"Security Headers Report: {report}")

    # Get current configuration
    current_config = manager.get_current_config()
    print(f"Current Configuration: {current_config}")

    print("Security headers system initialized")