from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Response, Form, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List, Union

from schemas import UserCreate, Token, UserResponse, APIResponse
from models import User
from app.dependencies.database import get_db
from app.dependencies.services import get_auth_service
from app.dependencies.auth import get_current_active_user_dependency
from app.services.auth_service import AuthService

# Rate limiting for security
from collections import defaultdict
from datetime import datetime, timedelta

# Simple rate limiter
class RateLimiter:
    """Rate limiting implementation for security"""

    def __init__(self, max_attempts: int = 5, window_minutes: int = 15) -> None:
        """Initialize rate limiter

        Args:
            max_attempts: Maximum number of attempts allowed
            window_minutes: Time window in minutes
        """
        self.max_attempts = max_attempts
        self.window_minutes = window_minutes
        self.attempts: Dict[str, List[datetime]] = defaultdict(list)

    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed based on rate limit

        Args:
            key: Identifier for rate limiting (e.g., IP address)

        Returns:
            bool: True if request is allowed, False if rate limited
        """
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=self.window_minutes)

        # Clean old attempts
        self.attempts[key] = [attempt for attempt in self.attempts[key] if attempt > window_start]

        # Check if under limit
        if len(self.attempts[key]) < self.max_attempts:
            self.attempts[key].append(now)
            return True

        return False

# Rate limiters
password_reset_limiter = RateLimiter(max_attempts=3, window_minutes=15)
login_limiter = RateLimiter(max_attempts=10, window_minutes=15)

router = APIRouter(
    prefix="",
    tags=["authentication"],
    responses={404: {"description": "Not found"}},
)


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def register_user(
    user: UserCreate,
    background_tasks: BackgroundTasks,
    auth_service: AuthService = Depends(get_auth_service)
) -> UserResponse:
    """Register new user with automatic trial subscription and welcome email (background)

    Args:
        user: User creation data
        background_tasks: FastAPI background tasks for email sending
        auth_service: Authentication service dependency

    Returns:
        UserResponse: Created user data

    Raises:
        HTTPException: If registration fails due to validation or server errors
    """
    try:
        print(f"Registrazione in corso per: {user.username} ({user.email})")

        # Create user using auth service
        created_user = await auth_service.register_user(user)

        print(f"Utente registrato con successo: {created_user.username} (ID: {created_user.id})")

        return UserResponse(
            id=created_user.id,
            username=created_user.username,
            email=created_user.email,
            full_name=created_user.full_name,
            is_active=created_user.is_active,
            created_at=created_user.created_at,
            subscription_active=created_user.subscription_active
        )

    except ValueError as e:
        print(f"Errore registrazione: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        print(f"Errore imprevisto durante registrazione: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Errore interno del server durante la registrazione"
        )


@router.post("/token", response_model=Token)
def login_user(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
) -> Token:
    """Login user and return JWT tokens - SUPPORTA USERNAME E EMAIL

    Args:
        request: FastAPI request object for rate limiting
        response: FastAPI response object for CORS headers
        form_data: OAuth2 form data with username and password
        auth_service: Authentication service dependency

    Returns:
        Token: JWT access and refresh tokens

    Raises:
        HTTPException: If authentication fails or rate limited
    """
    print(f"Tentativo login da frontend per: {form_data.username}")

    # Rate limiting check
    client_ip: str = request.client.host
    if not login_limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Troppi tentativi di login. Riprova più tardi."
        )

    # Authenticate user
    token: Optional[Token] = auth_service.login_user(form_data.username, form_data.password)

    if not token:
        print(f"Login fallito per: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username/email o password non corretti",
            headers={"WWW-Authenticate": "Bearer"},
        )

    print(f"Login riuscito per: {form_data.username}")

    # Add CORS headers
    response.headers["Access-Control-Allow-Origin"] = "https://www.cash-revolution.com"
    response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Credentials"] = "true"

    return token


@router.post("/logout")
def logout_user(response: Response) -> Dict[str, str]:
    """Logout endpoint - token invalidation handled client-side

    Args:
        response: FastAPI response object for CORS headers

    Returns:
        Dict[str, str]: Success message
    """
    # Add consistent CORS headers for logout
    response.headers["Access-Control-Allow-Origin"] = "https://www.cash-revolution.com"
    response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Credentials"] = "true"

    return {"message": "Logout effettuato con successo"}


@router.get("/logout")
def logout_user_get(response: Response) -> Dict[str, str]:
    """Logout endpoint GET - fallback for direct access

    Args:
        response: FastAPI response object for CORS headers

    Returns:
        Dict[str, str]: Success message
    """
    # Add consistent CORS headers for logout
    response.headers["Access-Control-Allow-Origin"] = "https://www.cash-revolution.com"
    response.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Credentials"] = "true"

    return {"message": "Logout effettuato con successo (GET)"}


@router.post("/forgot-password")
async def request_password_reset(
    request: Request,
    email: str = Form(...),
    auth_service: AuthService = Depends(get_auth_service)
) -> Dict[str, Union[str, bool]]:
    """Request password reset - send reset email

    Args:
        request: FastAPI request object for rate limiting
        email: Email address to send reset link to
        auth_service: Authentication service dependency

    Returns:
        Dict[str, Union[str, bool]]: Response message with email

    Raises:
        HTTPException: If rate limited
    """
    # SECURITY: Rate limiting check
    client_ip: str = request.client.host
    if not password_reset_limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Troppi tentativi di reset password. Riprova più tardi."
        )

    try:
        # Send password reset email
        success: bool = await auth_service.forgot_password(email)

        # Always return success message for security
        return {
            "message": "Se l'email esiste nel nostro sistema, riceverai un link per il reset della password.",
            "email": email
        }

    except Exception as e:
        print(f"Errore durante reset password: {e}")
        # Don't reveal internal errors
        return {
            "message": "Se l'email esiste nel nostro sistema, riceverai un link per il reset della password.",
            "email": email
        }


@router.post("/reset-password")
def reset_password(
    request: Request,
    token: str = Form(...),
    new_password: str = Form(...),
    auth_service: AuthService = Depends(get_auth_service)
) -> Dict[str, str]:
    """Reset password using token

    Args:
        request: FastAPI request object for rate limiting
        token: Password reset token
        new_password: New password to set
        auth_service: Authentication service dependency

    Returns:
        Dict[str, str]: Success message

    Raises:
        HTTPException: If rate limited, validation fails, or token is invalid
    """
    # SECURITY: Rate limiting check
    client_ip: str = request.client.host
    if not password_reset_limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Troppi tentativi di reset password. Riprova più tardi."
        )

    # Validate password strength
    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La password deve essere lunga almeno 8 caratteri"
        )

    # Reset password
    success: bool = auth_service.reset_password(token, new_password)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token di reset non valido o scaduto"
        )

    return {"message": "Password aggiornata con successo"}


@router.post("/change-password")
def change_password(
    current_password: str = Form(...),
    new_password: str = Form(...),
    current_user: User = Depends(get_current_active_user_dependency),
    auth_service: AuthService = Depends(get_auth_service)
) -> Dict[str, str]:
    """Change user password

    Args:
        current_password: Current password for verification
        new_password: New password to set
        current_user: Currently authenticated user
        auth_service: Authentication service dependency

    Returns:
        Dict[str, str]: Success message

    Raises:
        HTTPException: If validation fails or current password is incorrect
    """
    # Validate password strength
    if len(new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La password deve essere lunga almeno 8 caratteri"
        )

    # Change password
    success: bool = auth_service.change_password(current_user, current_password, new_password)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password corrente non corretta"
        )

    return {"message": "Password cambiata con successo"}


# HTML page routes (for backward compatibility)
@router.get("/login.html", response_class=HTMLResponse)
async def serve_login_page() -> HTMLResponse:
    """Serve the login page

    Returns:
        HTMLResponse: Login page content

    Raises:
        HTTPException: If login page file is not found
    """
    try:
        with open("login.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Login page not found")


@router.get("/register.html", response_class=HTMLResponse)
async def serve_register_page() -> HTMLResponse:
    """Serve the registration page

    Returns:
        HTMLResponse: Registration page content

    Raises:
        HTTPException: If registration page file is not found
    """
    try:
        with open("register.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Register page not found")


@router.get("/forgot-password.html", response_class=HTMLResponse)
async def serve_forgot_password_page() -> HTMLResponse:
    """Serve the forgot password page

    Returns:
        HTMLResponse: Forgot password page content

    Raises:
        HTTPException: If forgot password page file is not found
    """
    try:
        with open("forgot-password.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Forgot password page not found")


@router.get("/reset-password.html", response_class=HTMLResponse)
async def serve_reset_password_page() -> HTMLResponse:
    """Serve the reset password page

    Returns:
        HTMLResponse: Reset password page content

    Raises:
        HTTPException: If reset password page file is not found
    """
    try:
        with open("reset-password.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Reset password page not found")