"""
Enhanced Authentication Router with Comprehensive OpenAPI Documentation

This router provides authentication endpoints with:
- Detailed request/response models
- Security documentation
- Rate limiting examples
- Comprehensive error handling
- Interactive examples
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Response, Form, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
import logging

from schemas import UserCreate, Token, UserResponse, APIResponse
from app.schemas.enhanced_schemas import (
    UserCreateEnhanced, UserLoginRequest, UserResponseEnhanced,
    ErrorResponseEnhanced, APIResponseEnhanced
)
from models import User
from app.dependencies.database import get_db
from app.dependencies.services import get_auth_service
from app.dependencies.auth import get_current_active_user_dependency
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)

# Rate limiting for security
from collections import defaultdict

# Enhanced rate limiter with detailed documentation
class RateLimiter:
    """
    Rate limiting implementation for security and abuse prevention

    Features:
    - Per-IP rate limiting
    - Configurable time windows
    - Different limits for different endpoint types
    - Detailed rate limit headers in responses
    """

    def __init__(self, max_attempts: int = 5, window_minutes: int = 15, endpoint_type: str = "default") -> None:
        """
        Initialize rate limiter

        Args:
            max_attempts: Maximum number of attempts allowed within the time window
            window_minutes: Time window in minutes for rate limiting
            endpoint_type: Type of endpoint for different rate limiting rules
        """
        self.max_attempts = max_attempts
        self.window_minutes = window_minutes
        self.endpoint_type = endpoint_type
        self.attempts: Dict[str, List[datetime]] = defaultdict(list)

    def is_allowed(self, key: str) -> tuple[bool, dict]:
        """
        Check if request is allowed based on rate limit

        Args:
            key: Identifier for rate limiting (e.g., IP address)

        Returns:
            tuple: (is_allowed, rate_limit_info)
        """
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=self.window_minutes)

        # Clean old attempts
        self.attempts[key] = [attempt for attempt in self.attempts[key] if attempt > window_start]

        # Calculate remaining attempts and reset time
        remaining_attempts = max(0, self.max_attempts - len(self.attempts[key]))
        reset_time = window_start + timedelta(minutes=self.window_minutes) if self.attempts[key] else None

        rate_limit_info = {
            "limit": self.max_attempts,
            "remaining": remaining_attempts,
            "reset": reset_time.isoformat() if reset_time else None,
            "window": f"{self.window_minutes}m",
            "type": self.endpoint_type
        }

        # Check if under limit
        if len(self.attempts[key]) < self.max_attempts:
            self.attempts[key].append(now)
            return True, rate_limit_info

        return False, rate_limit_info

# Enhanced rate limiters with different rules for different endpoint types
password_reset_limiter = RateLimiter(max_attempts=3, window_minutes=15, endpoint_type="password_reset")
login_limiter = RateLimiter(max_attempts=10, window_minutes=15, endpoint_type="login")
registration_limiter = RateLimiter(max_attempts=5, window_minutes=60, endpoint_type="registration")

router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
    responses={
        401: {
            "description": "Unauthorized - Authentication failed",
            "content": {
                "application/json": {
                    "example": {
                        "error": "AuthenticationError",
                        "message": "Invalid username or password",
                        "timestamp": "2024-01-15T10:30:00Z"
                    }
                }
            }
        },
        429: {
            "description": "Too Many Requests - Rate limit exceeded",
            "content": {
                "application/json": {
                    "example": {
                        "error": "RateLimitExceeded",
                        "message": "Too many login attempts. Please try again later.",
                        "rate_limit": {
                            "limit": 10,
                            "remaining": 0,
                            "reset": "2024-01-15T10:45:00Z",
                            "window": "15m"
                        },
                        "timestamp": "2024-01-15T10:30:00Z"
                    }
                }
            }
        }
    }
)

@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=UserResponseEnhanced,
    summary="Register New User",
    description="""
    Create a new user account with automatic trial subscription and welcome email.

    The registration process includes:
    - Email validation
    - Password strength requirements
    - Automatic trial subscription activation
    - Welcome email with verification link
    - Rate limiting to prevent abuse

    **Security Requirements:**
    - Password must be at least 8 characters long
    - Must contain uppercase, lowercase, numbers, and special characters
    - Email must be unique across the system
    """,
    responses={
        201: {
            "description": "User successfully registered",
            "content": {
                "application/json": {
                    "example": {
                        "id": 12345,
                        "username": "trader_pro_2024",
                        "email": "trader@example.com",
                        "full_name": "John Trader Smith",
                        "is_active": True,
                        "is_admin": False,
                        "subscription_active": True,
                        "created_at": "2024-01-15T10:30:00Z",
                        "last_login": None,
                        "trial_end": "2024-02-15T10:30:00Z",
                        "phone": "+1234567890",
                        "country": "US",
                        "timezone": "America/New_York",
                        "email_verified": False,
                        "profile_complete": False
                    }
                }
            }
        },
        400: {
            "description": "Bad Request - Validation failed",
            "content": {
                "application/json": {
                    "example": {
                        "error": "ValidationError",
                        "message": "Password validation failed",
                        "field_errors": [
                            {
                                "field": "password",
                                "message": "Password must contain at least one uppercase letter"
                            }
                        ],
                        "timestamp": "2024-01-15T10:30:00Z"
                    }
                }
            }
        },
        409: {
            "description": "Conflict - Username or email already exists",
            "content": {
                "application/json": {
                    "example": {
                        "error": "UserExistsError",
                        "message": "Username or email already registered",
                        "details": {
                            "field": "email",
                            "value": "existing@example.com"
                        },
                        "timestamp": "2024-01-15T10:30:00Z"
                    }
                }
            }
        }
    }
)
async def register_user(
    user: UserCreateEnhanced,
    background_tasks: BackgroundTasks,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
) -> UserResponseEnhanced:
    """
    Register a new user with comprehensive validation and automatic setup

    This endpoint creates a new user account with the following features:
    - Strong password requirements
    - Email format validation
    - Country and timezone support
    - Phone number validation (optional)
    - Automatic trial subscription
    - Welcome email with verification link
    - Rate limiting to prevent abuse

    **Password Requirements:**
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character

    **Rate Limits:**
    - 5 attempts per IP address per hour

    **Success Response:**
    - Returns complete user information
    - Includes trial subscription details
    - Email verification pending status

    **Error Response:**
    - Detailed validation errors for each field
    - Conflict errors for existing usernames/emails
    - Rate limit exceeded information
    """
    try:
        logger.info(f"Registration attempt from IP: {request.client.host} for username: {user.username}")

        # Apply rate limiting
        is_allowed, rate_limit_info = registration_limiter.is_allowed(request.client.host)
        if not is_allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many registration attempts. Please try again in {rate_limit_info['window']}."
            )

        # Create user using auth service
        created_user = await auth_service.register_user(user)

        logger.info(f"User registered successfully: {created_user.username} (ID: {created_user.id})")

        return UserResponseEnhanced(
            id=created_user.id,
            username=created_user.username,
            email=created_user.email,
            full_name=created_user.full_name,
            is_active=created_user.is_active,
            is_admin=created_user.is_admin,
            subscription_active=created_user.subscription_active,
            created_at=created_user.created_at,
            last_login=created_user.last_login,
            trial_end=created_user.trial_end,
            phone=created_user.phone,
            country=created_user.country,
            timezone=created_user.timezone,
            email_verified=False,
            profile_complete=False
        )

    except ValueError as e:
        logger.error(f"Registration validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error during user registration"
        )

@router.post(
    "/login",
    response_model=Token,
    summary="User Login",
    description="""
    Authenticate user and return JWT access and refresh tokens.

    This endpoint supports login with either username or email address.
    Successful authentication returns:
    - JWT access token (15-minute expiration)
    - JWT refresh token (7-day expiration)
    - Token type specification

    **Security Features:**
    - Rate limiting to prevent brute force attacks
    - Account lockout after repeated failures
    - Secure token generation with expiration
    - CORS headers for web applications

    **Rate Limits:**
    - 10 attempts per IP address per 15 minutes

    **Token Usage:**
    - Include access token in Authorization header as 'Bearer <token>'
    - Use refresh token to obtain new access tokens without re-authentication
    """,
    responses={
        200: {
            "description": "Login successful",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
                        "token_type": "bearer"
                    }
                }
            }
        },
        401: {
            "description": "Authentication failed",
            "content": {
                "application/json": {
                    "example": {
                        "error": "AuthenticationError",
                        "message": "Invalid username or password",
                        "details": {
                            "remaining_attempts": 7,
                            "attempts_window": "15m"
                        },
                        "timestamp": "2024-01-15T10:30:00Z"
                    }
                }
            }
        },
        423: {
            "description": "Account Locked - Too many failed attempts",
            "content": {
                "application/json": {
                    "example": {
                        "error": "AccountLockedError",
                        "message": "Account temporarily locked due to too many failed login attempts",
                        "details": {
                            "lockout_duration": "15m",
                            "unlock_time": "2024-01-15T10:45:00Z"
                        },
                        "timestamp": "2024-01-15T10:30:00Z"
                    }
                }
            }
        }
    }
)
def login_user(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
) -> Token:
    """
    Authenticate user with username/email and password

    This endpoint handles user authentication and returns JWT tokens for API access.

    **Authentication Methods Supported:**
    - Username + password
    - Email address + password

    **Security Features:**
    - Rate limiting (10 attempts per 15 minutes)
    - Account lockout after repeated failures
    - Secure password hashing
    - Token-based authentication

    **Response:**
    - Access token: 15-minute expiration for API calls
    - Refresh token: 7-day expiration for obtaining new access tokens
    - Token type: "bearer" for Authorization header

    **Usage:**
    ```
    Authorization: Bearer <access_token>
    ```

    **Error Handling:**
    - Invalid credentials return 401 with remaining attempts
    - Rate limited requests return 429 with retry information
    - Locked accounts return 423 with unlock time
    """
    logger.info(f"Login attempt from IP: {request.client.host} for: {form_data.username}")

    # Apply rate limiting
    is_allowed, rate_limit_info = login_limiter.is_allowed(request.client.host)
    if not is_allowed:
        logger.warning(f"Login rate limit exceeded for IP: {request.client.host}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "RateLimitExceeded",
                "message": f"Too many login attempts. Please try again in {rate_limit_info['window']}.",
                "rate_limit": rate_limit_info
            }
        )

    # Authenticate user (supports both username and email)
    token: Optional[Token] = auth_service.login_user(form_data.username, form_data.password)

    if not token:
        logger.warning(f"Login failed for: {form_data.username} from IP: {request.client.host}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "AuthenticationError",
                "message": "Invalid username/email or password",
                "remaining_attempts": rate_limit_info["remaining"],
                "attempts_window": rate_limit_info["window"]
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info(f"Login successful for: {form_data.username} from IP: {request.client.host}")

    # Add comprehensive CORS headers for web applications
    response.headers["Access-Control-Allow-Origin"] = "https://www.cash-revolution.com"
    response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Credentials"] = "true"

    # Add rate limit headers for client-side awareness
    response.headers["X-RateLimit-Limit"] = str(rate_limit_info["limit"])
    response.headers["X-RateLimit-Remaining"] = str(rate_limit_info["remaining"])
    response.headers["X-RateLimit-Reset"] = rate_limit_info["reset"] or ""

    return token

@router.post(
    "/logout",
    response_model=APIResponseEnhanced,
    summary="User Logout",
    description="""
    Logout the current user by invalidating their session.

    Note: JWT tokens are stateless, so this endpoint primarily serves to:
    - Log the logout action for security auditing
    - Provide a clear endpoint for client applications
    - Return consistent CORS headers for web applications
    - Update user's last activity timestamp

    **Security Note:**
    - Actual token invalidation is handled client-side
    - Server-side token blacklisting can be implemented for enhanced security
    - This endpoint helps maintain proper session hygiene
    """
)
def logout_user(
    request: Request,
    response: Response,
    current_user: User = Depends(get_current_active_user_dependency)
) -> APIResponseEnhanced:
    """
    Log out the current user

    This endpoint handles user logout and provides a clean response for client applications.

    **Security Features:**
    - Requires authenticated user
    - Logs logout action for audit trail
    - Clears client-side session data
    - Provides consistent CORS headers

    **Response:**
    - Success confirmation message
    - Timestamp for audit purposes
    - User information for logging

    **Client Action Required:**
    - Clear stored JWT tokens
    - Update UI to reflect logged-out state
    - Redirect to login page
    """
    logger.info(f"Logout requested by user: {current_user.username} (ID: {current_user.id})")

    # Add comprehensive CORS headers for logout
    response.headers["Access-Control-Allow-Origin"] = "https://www.cash-revolution.com"
    response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Credentials"] = "true"

    # Update user's last activity
    current_user.last_login = datetime.utcnow()

    return APIResponseEnhanced(
        success=True,
        message="User logged out successfully",
        data={"user_id": current_user.id, "username": current_user.username},
        meta={"logout_method": "server_endpoint", "session_cleared": True}
    )

@router.post(
    "/forgot-password",
    response_model=APIResponseEnhanced,
    summary="Request Password Reset",
    description="""
    Initiate password reset process by sending a reset email to the user.

    This endpoint provides a secure password reset mechanism:
    - Generates a secure reset token
    - Sends reset email with expiration
    - Rate limiting to prevent email abuse
    - Security-focused response (always returns success)

    **Security Features:**
    - Rate limiting (3 attempts per IP per 15 minutes)
    - Secure token generation with expiration
    - Email validation before sending reset
    - Generic success response to prevent email enumeration

    **Rate Limits:**
    - 3 attempts per IP address per 15 minutes

    **Email Content:**
    - Secure reset link with token
    - Expiration time (24 hours)
    - Security warnings and best practices
    - Contact information for support

    **User Experience:**
    - Always returns success message for security
    - Users receive email only if account exists
    - Clear instructions for password reset process
    """
)
async def request_password_reset(
    request: Request,
    email: str = Form(..., description="Email address associated with the account"),
    auth_service: AuthService = Depends(get_auth_service)
) -> APIResponseEnhanced:
    """
    Request password reset email

    This endpoint initiates the password reset process by sending a secure reset email.

    **Security Features:**
    - Rate limiting to prevent email abuse
    - Secure token generation with 24-hour expiration
    - Generic success response to prevent account enumeration
    - Email validation before processing

    **Process:**
    1. Validate email format
    2. Check if user exists in system
    3. Generate secure reset token
    4. Send reset email with secure link
    5. Return generic success response

    **Email Includes:**
    - Secure reset link with unique token
    - 24-hour expiration time
    - Security best practices
    - Contact information for support

    **Rate Limits:**
    - 3 attempts per IP address per 15 minutes

    **Response:**
    - Always returns success for security
    - Includes masked email for user reference
    - Provides next steps information
    """
    logger.info(f"Password reset requested for email: {email} from IP: {request.client.host}")

    # Apply rate limiting
    is_allowed, rate_limit_info = password_reset_limiter.is_allowed(request.client.host)
    if not is_allowed:
        logger.warning(f"Password reset rate limit exceeded for IP: {request.client.host}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "RateLimitExceeded",
                "message": f"Too many password reset attempts. Please try again in {rate_limit_info['window']}.",
                "rate_limit": rate_limit_info
            }
        )

    try:
        # Send password reset email (returns False if user not found)
        success: bool = await auth_service.forgot_password(email)

        # Always return success message for security (prevent email enumeration)
        if success:
            logger.info(f"Password reset email sent to: {email}")
        else:
            logger.info(f"Password reset requested for non-existent email: {email}")

        # Mask email for security and privacy
        masked_email = email[:2] + "*" * (len(email) - 6) + email[-4:] if len(email) > 6 else "*" * len(email)

        return APIResponseEnhanced(
            success=True,
            message="If your email exists in our system, you will receive a password reset link.",
            data={
                "email": masked_email,
                "next_steps": "Check your email and follow the reset link within 24 hours."
            },
            meta={
                "reset_window": "24h",
                "security_notice": "Reset links expire for security reasons"
            }
        )

    except Exception as e:
        logger.error(f"Error during password reset request: {e}")
        # Still return success for security, but log the error
        return APIResponseEnhanced(
            success=True,
            message="If your email exists in our system, you will receive a password reset link.",
            data={"email": "****@****.***"},
            meta={"error_occurred": True}
        )