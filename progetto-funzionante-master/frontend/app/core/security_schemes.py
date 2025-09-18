"""
Comprehensive Security Schemes and Authentication Documentation

This module provides detailed security documentation including:
- Authentication methods
- Authorization schemes
- Security requirements
- OAuth2 flows
- API key management
- Rate limiting
- Security best practices
"""

from typing import Dict, Any, List, Optional
from fastapi import Security, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm, APIKeyHeader
from fastapi.openapi.models import OAuthFlows, OAuthFlowPassword, SecuritySchemeType
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Enhanced OAuth2 Password Bearer Scheme
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/token",
    scheme_name="bearerAuth",
    description="JWT token obtained from /auth/token endpoint. Include 'Bearer ' prefix in Authorization header.",
    auto_error=True
)

# API Key Header for alternative authentication
api_key_scheme = APIKeyHeader(
    name="X-API-Key",
    scheme_name="apiKeyAuth",
    description="API key for programmatic access (alternative to JWT)",
    auto_error=False
)

class TokenResponse(BaseModel):
    """Enhanced token response with security information"""
    access_token: str = Field(
        ...,
        description="JWT access token for API authentication",
        example="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    )
    refresh_token: str = Field(
        ...,
        description="JWT refresh token for obtaining new access tokens",
        example="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    )
    token_type: str = Field(
        "bearer",
        description="Token type for Authorization header",
        example="bearer"
    )
    expires_in: int = Field(
        900,
        description="Access token expiration time in seconds (15 minutes)",
        example=900
    )
    refresh_expires_in: int = Field(
        604800,
        description="Refresh token expiration time in seconds (7 days)",
        example=604800
    )
    scope: str = Field(
        "read write",
        description="Token scope permissions",
        example="read write"
    )
    user_info: Dict[str, Any] = Field(
        ...,
        description="Basic user information for client applications",
        example={
            "user_id": 12345,
            "username": "trader_pro",
            "email": "trader@example.com",
            "subscription_active": True,
            "is_admin": False
        }
    )

class SecurityConfig(BaseModel):
    """Security configuration and settings"""
    jwt_algorithm: str = "HS256"
    jwt_secret_key: str = Field(..., description="JWT secret key for token signing")
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7
    password_min_length: int = 8
    password_max_length: int = 128
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_numbers: bool = True
    password_require_special: bool = True
    max_login_attempts: int = 5
    login_lockout_minutes: int = 15
    api_key_prefix: str = "cr_"
    rate_limit_default: int = 100
    rate_limit_burst: int = 10

# Enhanced Security Schemes for OpenAPI
SECURITY_SCHEMES = {
    "bearerAuth": {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": """
        JWT (JSON Web Token) authentication using Bearer scheme.

        **How to use:**
        1. Obtain token from `/auth/token` endpoint
        2. Include in Authorization header: `Authorization: Bearer <token>`
        3. Token expires after 15 minutes
        4. Use refresh token to obtain new access tokens

        **Token Structure:**
        - Header: Algorithm and token type
        - Payload: User information and claims
        - Signature: Cryptographic signature

        **Security Features:**
        - Cryptographic signing with HS256
        - Expiration time validation
        - User ID and role claims
        - Audience and issuer validation

        **Rate Limits:**
        - Authentication endpoints: 5 requests per minute
        - API endpoints: 100 requests per minute (authenticated)
        - Signal generation: 10 requests per hour
        """
    },
    "apiKeyAuth": {
        "type": "apiKey",
        "in": "header",
        "name": "X-API-Key",
        "description": """
        API Key authentication for programmatic access.

        **How to use:**
        1. Generate API key from user dashboard
        2. Include in request header: `X-API-Key: <your-api-key>`
        3. API keys have specific scopes and permissions
        4. Keys can be rotated and revoked

        **Key Features:**
        - Unique per user
        - Configurable scopes and permissions
        - Rate limiting per key
        - Activity logging and monitoring
        - Key rotation support

        **Security Best Practices:**
        - Keep keys secure and never expose in client-side code
        - Use environment variables for key storage
        - Regularly rotate keys for enhanced security
        - Monitor usage patterns and revoke suspicious keys
        - Use key-specific rate limiting

        **Rate Limits:**
        - Default: 100 requests per minute per key
        - Burst: 10 requests per second per key
        - Custom limits available for enterprise plans
        """
    },
    "oauth2": {
        "type": "oauth2",
        "flows": {
            "password": {
                "tokenUrl": "/auth/token",
                "refreshUrl": "/auth/refresh",
                "scopes": {
                    "read": "Read access to signals and market data",
                    "write": "Create signals and manage account",
                    "signals:read": "Access trading signals",
                    "signals:write": "Create and manage signals",
                    "market:read": "Access market data",
                    "account:read": "Read account information",
                    "account:write": "Manage account settings",
                    "admin": "Administrative access"
                }
            }
        },
        "description": """
        OAuth2 Password Flow for third-party application integration.

        **Flow Process:**
        1. User authenticates with username/password
        2. Application receives access and refresh tokens
        3. Use access token for API calls
        4. Refresh access token using refresh token

        **Security Features:**
        - PKCE (Proof Key for Code Exchange) support
        - State parameter for CSRF protection
        - Scope-based access control
        - Token introspection endpoint
        - Revocation endpoint support

        **Integration Requirements:**
        - Registered application with client ID
        - Secure storage of client credentials
        - Proper token management and refresh
        - User consent handling
        - Error handling and retry logic
        """
    }
}

# Security Requirements for Different Endpoint Types
SECURITY_REQUIREMENTS = {
    "public": [],
    "user": [{"bearerAuth": []}],
    "premium": [{"bearerAuth": []}],
    "admin": [{"bearerAuth": []}],
    "api_key": [{"apiKeyAuth": []}],
    "multi_auth": [{"bearerAuth": []}, {"apiKeyAuth": []}]
}

class SecurityMiddleware:
    """Enhanced security middleware for comprehensive protection"""

    def __init__(self, security_config: SecurityConfig):
        self.config = security_config
        self.failed_attempts = {}
        self.locked_accounts = {}

    def check_rate_limit(self, identifier: str, endpoint_type: str = "default") -> bool:
        """
        Check if request is within rate limits

        Args:
            identifier: Unique identifier (IP address, user ID, or API key)
            endpoint_type: Type of endpoint for different rate limits

        Returns:
            bool: True if within limits, False if rate limited
        """
        current_time = datetime.utcnow()
        window_start = current_time - timedelta(minutes=1)

        # Get or initialize rate limit data
        if identifier not in self.failed_attempts:
            self.failed_attempts[identifier] = []

        # Clean old attempts
        self.failed_attempts[identifier] = [
            attempt for attempt in self.failed_attempts[identifier]
            if attempt > window_start
        ]

        # Check rate limit based on endpoint type
        limits = {
            "auth": 5,        # Authentication endpoints
            "signals": 100,   # Signal endpoints
            "market": 60,     # Market data endpoints
            "admin": 10,      # Admin endpoints
            "default": self.config.rate_limit_default
        }

        limit = limits.get(endpoint_type, self.config.rate_limit_default)
        current_attempts = len(self.failed_attempts[identifier])

        return current_attempts < limit

    def check_login_attempts(self, username: str) -> bool:
        """
        Check if user has exceeded maximum login attempts

        Args:
            username: Username to check

        Returns:
            bool: True if login attempts are within limits
        """
        current_time = datetime.utcnow()
        lockout_window = current_time - timedelta(minutes=self.config.login_lockout_minutes)

        # Check if account is locked
        if username in self.locked_accounts:
            if self.locked_accounts[username] > current_time:
                return False
            else:
                # Lockout expired, remove from locked accounts
                del self.locked_accounts[username]

        # Check recent failed attempts
        if username not in self.failed_attempts:
            return True

        recent_attempts = [
            attempt for attempt in self.failed_attempts[username]
            if attempt > lockout_window
        ]

        if len(recent_attempts) >= self.config.max_login_attempts:
            # Lock account
            lockout_until = current_time + timedelta(minutes=self.config.login_lockout_minutes)
            self.locked_accounts[username] = lockout_until
            return False

        return True

    def record_failed_attempt(self, username: str):
        """Record a failed login attempt"""
        current_time = datetime.utcnow()
        if username not in self.failed_attempts:
            self.failed_attempts[username] = []
        self.failed_attempts[username].append(current_time)

class SecurityHeaders:
    """Security headers for enhanced protection"""

    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """
        Get recommended security headers for API responses

        Returns:
            Dict[str, str]: Security headers and their values
        """
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' https:; font-src 'self' data:; object-src 'none';",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
            "X-API-Version": "2.0.1",
            "X-Request-ID": "",  # Should be populated with unique request ID
            "X-RateLimit-Limit": "100",  # Should be populated with actual limit
            "X-RateLimit-Remaining": "99",  # Should be populated with remaining
            "X-RateLimit-Reset": ""  # Should be populated with reset timestamp
        }

class SecurityValidator:
    """Security validation utilities"""

    @staticmethod
    def validate_password_strength(password: str, config: SecurityConfig) -> List[str]:
        """
        Validate password strength against security requirements

        Args:
            password: Password to validate
            config: Security configuration with requirements

        Returns:
            List[str]: List of validation errors (empty if valid)
        """
        errors = []

        # Length validation
        if len(password) < config.password_min_length:
            errors.append(f"Password must be at least {config.password_min_length} characters long")
        if len(password) > config.password_max_length:
            errors.append(f"Password must be no more than {config.password_max_length} characters long")

        # Character requirements
        if config.password_require_uppercase and not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")

        if config.password_require_lowercase and not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")

        if config.password_require_numbers and not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number")

        if config.password_require_special and not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?`~' for c in password):
            errors.append("Password must contain at least one special character")

        # Common password patterns
        common_patterns = [
            r'^123456$', r'^password$', r'^qwerty$', r'^letmein$',
            r'^admin$', r'^welcome$', r'^monkey$', r'^password123$'
        ]

        import re
        for pattern in common_patterns:
            if re.match(pattern, password, re.IGNORECASE):
                errors.append("Password is too common or easily guessable")
                break

        return errors

    @staticmethod
    def validate_api_key_format(api_key: str, config: SecurityConfig) -> bool:
        """
        Validate API key format and structure

        Args:
            api_key: API key to validate
            config: Security configuration

        Returns:
            bool: True if API key format is valid
        """
        # Check prefix
        if not api_key.startswith(config.api_key_prefix):
            return False

        # Check length (typical API key is 32-64 characters)
        if not (32 <= len(api_key) <= 64):
            return False

        # Check character set (alphanumeric and some special characters)
        import re
        if not re.match(r'^[a-zA-Z0-9\-_]+$', api_key):
            return False

        return True

# Security Documentation for OpenAPI
SECURITY_DOCUMENTATION = """
# API Security Guide

## Authentication Methods

### 1. JWT Bearer Token (Recommended)
- **Endpoint**: `/auth/token`
- **Method**: POST with form data
- **Response**: Access token (15 min) + Refresh token (7 days)
- **Usage**: `Authorization: Bearer <token>`
- **Best for**: Web applications, mobile apps, automated systems

### 2. API Key Authentication
- **Generation**: User dashboard or admin panel
- **Usage**: `X-API-Key: <your-api-key>`
- **Features**: Rate limiting, scope control, activity monitoring
- **Best for**: Programmatic access, third-party integrations

### 3. OAuth2 Password Flow
- **Standard**: RFC 6749 compliant
- **Scopes**: Fine-grained permission control
- **Features**: Token refresh, revocation, introspection
- **Best for**: Third-party applications, enterprise integration

## Security Features

### Rate Limiting
- **Authentication endpoints**: 5 requests per minute
- **API endpoints**: 100 requests per minute
- **Signal generation**: 10 requests per hour
- **Market data**: 60 requests per minute
- **Admin endpoints**: 10 requests per minute

### Password Security
- **Minimum length**: 8 characters
- **Complexity requirements**: Uppercase, lowercase, numbers, special characters
- **Hashing**: bcrypt with salt
- **Storage**: Secure database encryption
- **Reset**: Secure token-based reset process

### Token Security
- **Algorithm**: HS256 (HMAC-SHA256)
- **Expiration**: 15 minutes (access), 7 days (refresh)
- **Claims**: User ID, roles, expiration, audience
- **Validation**: Signature, expiration, issuer, audience
- **Refresh**: Secure token refresh mechanism

### Data Protection
- **Encryption**: TLS 1.3 for all communications
- **Headers**: Security headers for XSS and CSRF protection
- **Validation**: Input validation and sanitization
- **Logging**: Security event logging and monitoring
- **Audit**: Complete audit trail for all actions

## Best Practices

### For Application Developers
1. **Token Storage**: Store tokens securely (HttpOnly cookies, secure storage)
2. **HTTPS**: Always use HTTPS in production
3. **Error Handling**: Never expose sensitive information in error messages
4. **Rate Limiting**: Implement client-side rate limiting
5. **Input Validation**: Validate all inputs on both client and server

### For API Key Users
1. **Key Security**: Keep API keys secure and never expose in client-side code
2. **Environment Variables**: Use environment variables for key storage
3. **Rotation**: Regularly rotate API keys
4. **Monitoring**: Monitor usage patterns and revoke suspicious keys
5. **Scopes**: Use minimum required scopes for each key

### For Security Administrators
1. **Monitoring**: Regular security audits and penetration testing
2. **Updates**: Keep dependencies and security patches up to date
3. **Logging**: Comprehensive security event logging
4. **Backup**: Regular security configuration backups
5. **Training**: Security awareness training for development team

## Common Security Issues and Prevention

### 1. Token Theft
- **Issue**: Access tokens stolen through XSS or MITM attacks
- **Prevention**: Use HttpOnly cookies, implement CORS properly, use HTTPS
- **Detection**: Monitor for unusual token usage patterns
- **Response**: Immediate token revocation and user notification

### 2. Brute Force Attacks
- **Issue**: Automated attempts to guess passwords or API keys
- **Prevention**: Rate limiting, account lockout, CAPTCHA
- **Detection**: Monitor failed authentication attempts
- **Response**: IP blocking, account lockout, user notification

### 3. API Key Exposure
- **Issue**: API keys accidentally committed to code repositories
- **Prevention**: Use environment variables, secrets management
- **Detection**: Regular code scanning, secret detection
- **Response**: Immediate key rotation, repository cleanup

### 4. XSS Vulnerabilities
- **Issue**: Cross-site scripting attacks through user input
- **Prevention**: Input validation, output encoding, CSP headers
- **Detection**: Security scanning, penetration testing
- **Response**: Patch vulnerabilities, user notification

## Support and Reporting

### Security Issues
- **Email**: security@cash-revolution.com
- **Response Time**: 24 hours for critical issues
- **Information**: Detailed reproduction steps, impact assessment
- **Confidentiality**: Secure communication channels for sensitive information

### Documentation
- **API Documentation**: https://docs.cash-revolution.com/api/security
- **Best Practices**: https://docs.cash-revolution.com/security/best-practices
- **Troubleshooting**: https://docs.cash-revolution.com/security/troubleshooting

### Compliance
- **GDPR**: EU General Data Protection Regulation compliant
- **CCPA**: California Consumer Privacy Act compliant
- **SOC 2**: Service Organization Control 2 compliant
- **ISO 27001**: Information Security Management System certified
"""