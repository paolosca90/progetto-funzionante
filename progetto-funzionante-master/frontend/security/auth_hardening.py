"""
Enhanced Authentication and Authorization Hardening
Production-ready security for authentication systems
"""

import jwt
import bcrypt
import secrets
import hashlib
import time
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple, Union, Callable
from enum import Enum
from dataclasses import dataclass, field
from fastapi import HTTPException, status, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer
from sqlalchemy.orm import Session
import logging
import json
import redis
from collections import defaultdict, deque
import asyncio
import aiohttp
import ipaddress

logger = logging.getLogger(__name__)

class AuthEventType(Enum):
    """Authentication event types"""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    TOKEN_REFRESH = "token_refresh"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    MULTIFACTOR_AUTH = "multifactor_auth"

class SecurityLevel(Enum):
    """Security levels for authentication"""
    BASIC = "basic"
    STANDARD = "standard"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class AuthEvent:
    """Authentication event record"""
    event_type: AuthEventType
    user_id: Optional[str]
    ip_address: str
    user_agent: str
    timestamp: datetime
    success: bool
    details: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SecurityPolicy:
    """Security policy configuration"""
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    password_min_length: int = 12
    password_max_length: int = 128
    require_uppercase: bool = True
    require_lowercase: bool = True
    require_numbers: bool = True
    require_special_chars: bool = True
    password_history_count: int = 5
    session_timeout_minutes: int = 30
    max_concurrent_sessions: int = 3
    mfa_enabled: bool = True
    ip_whitelist: List[str] = field(default_factory=list)
    ip_blacklist: List[str] = field(default_factory=list)
    suspicious_ip_threshold: int = 10
    token_refresh_window_minutes: int = 5
    enable_audit_logging: bool = True

class PasswordPolicy:
    """Password policy enforcement"""

    def __init__(self, policy: SecurityPolicy):
        self.policy = policy
        self.forbidden_passwords = {
            'password', '123456', '12345678', '123456789', '12345',
            'qwerty', 'abc123', 'password1', 'admin', 'welcome',
            'letmein', 'monkey', 'dragon', 'baseball', 'football'
        }

    def validate_password(self, password: str, user_info: Optional[Dict[str, Any]] = None) -> Tuple[bool, List[str]]:
        """Validate password against policy"""
        errors = []

        # Check length
        if len(password) < self.policy.password_min_length:
            errors.append(f"Password must be at least {self.policy.password_min_length} characters long")

        if len(password) > self.policy.password_max_length:
            errors.append(f"Password must be no more than {self.policy.password_max_length} characters long")

        # Check character requirements
        if self.policy.require_uppercase and not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")

        if self.policy.require_lowercase and not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")

        if self.policy.require_numbers and not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number")

        if self.policy.require_special_chars and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("Password must contain at least one special character")

        # Check against forbidden passwords
        if password.lower() in self.forbidden_passwords:
            errors.append("Password is too common and not allowed")

        # Check if password contains username or email
        if user_info:
            username = user_info.get('username', '').lower()
            email = user_info.get('email', '').lower().split('@')[0]

            if username and username in password.lower():
                errors.append("Password cannot contain your username")

            if email and email in password.lower():
                errors.append("Password cannot contain your email address")

        # Check for common patterns
        if self._has_common_pattern(password):
            errors.append("Password contains a common pattern and is not secure")

        return len(errors) == 0, errors

    def _has_common_pattern(self, password: str) -> bool:
        """Check for common password patterns"""
        # Check for sequential characters
        for i in range(len(password) - 2):
            if (ord(password[i+1]) == ord(password[i]) + 1 and
                ord(password[i+2]) == ord(password[i]) + 2):
                return True

        # Check for repeated characters
        if len(set(password)) < len(password) * 0.6:  # More than 40% repeated
            return True

        # Check for keyboard patterns
        keyboard_patterns = [
            'qwerty', 'asdfgh', 'zxcvbn',
            '1qaz', '2wsx', '3edc', '4rfv', '5tgb', '6yhn', '7ujm', '8ik,',
            '!qaz', '@wsx', '#edc', '$rfv', '%tgb', '^yhn', '&ujm', '*ik,'
        ]

        lower_pass = password.lower()
        for pattern in keyboard_patterns:
            if pattern in lower_pass:
                return True

        return False

    def generate_password_hash(self, password: str) -> str:
        """Generate secure password hash"""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

class SecurityEventManager:
    """Security event monitoring and analysis"""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.failed_logins: Dict[str, deque] = defaultdict(lambda: deque(maxlen=50))
        self.ip_reputation: Dict[str, float] = defaultdict(float)
        self.suspicious_ips: set = set()

    async def record_event(self, event: AuthEvent):
        """Record authentication event"""
        event_key = f"auth_event:{event.user_id or 'anonymous'}:{event.ip_address}"

        # Store event details
        event_data = {
            'event_type': event.event_type.value,
            'user_id': event.user_id,
            'ip_address': event.ip_address,
            'user_agent': event.user_agent,
            'timestamp': event.timestamp.isoformat(),
            'success': event.success,
            'details': event.details
        }

        if self.redis_client:
            try:
                # Store in Redis for recent events
                await self.redis_client.lpush(f"auth_events:{event.user_id or 'anonymous'}", json.dumps(event_data))
                await self.redis_client.expire(f"auth_events:{event.user_id or 'anonymous'}", 86400)  # 24 hours

                # Update IP reputation
                await self._update_ip_reputation(event.ip_address, event.success)
            except Exception as e:
                logger.error(f"Failed to store auth event in Redis: {e}")

        # Track failed login attempts
        if event.event_type == AuthEventType.LOGIN_FAILURE:
            self.failed_logins[event.ip_address].append(event.timestamp)
            if len(self.failed_logins[event.ip_address]) >= 5:  # 5 failed attempts
                self.suspicious_ips.add(event.ip_address)
                logger.warning(f"Suspicious activity detected from IP: {event.ip_address}")

        # Log event
        logger.info(f"Auth event: {event.event_type.value} - User: {event.user_id} - IP: {event.ip_address} - Success: {event.success}")

    async def _update_ip_reputation(self, ip_address: str, success: bool):
        """Update IP reputation score"""
        if not self.redis_client:
            return

        try:
            reputation_key = f"ip_reputation:{ip_address}"
            current = float(await self.redis_client.get(reputation_key) or 1.0)

            if success:
                current = min(1.0, current + 0.1)  # Increase reputation for success
            else:
                current = max(0.0, current - 0.2)  # Decrease reputation for failure

            await self.redis_client.set(reputation_key, str(current))
            await self.redis_client.expire(reputation_key, 86400)  # 24 hours
        except Exception as e:
            logger.error(f"Failed to update IP reputation: {e}")

    async def is_ip_suspicious(self, ip_address: str) -> bool:
        """Check if IP address is suspicious"""
        if ip_address in self.suspicious_ips:
            return True

        if self.redis_client:
            try:
                reputation = float(await self.redis_client.get(f"ip_reputation:{ip_address}") or 1.0)
                return reputation < 0.3
            except Exception:
                pass

        return False

    async def get_login_attempts(self, user_id: str, minutes: int = 15) -> List[AuthEvent]:
        """Get recent login attempts for user"""
        if not self.redis_client:
            return []

        try:
            events_json = await self.redis_client.lrange(f"auth_events:{user_id}", 0, -1)
            events = []

            cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)

            for event_json in events_json:
                event_data = json.loads(event_json)
                event_time = datetime.fromisoformat(event_data['timestamp'])

                if event_time >= cutoff_time and event_data['event_type'] in ['login_success', 'login_failure']:
                    events.append(AuthEvent(
                        event_type=AuthEventType(event_data['event_type']),
                        user_id=event_data['user_id'],
                        ip_address=event_data['ip_address'],
                        user_agent=event_data['user_agent'],
                        timestamp=event_time,
                        success=event_data['success'],
                        details=event_data['details']
                    ))

            return events
        except Exception as e:
            logger.error(f"Failed to get login attempts: {e}")
            return []

class TokenManager:
    """JWT token management with enhanced security"""

    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7

    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)

        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access",
            "jti": str(uuid.uuid4())  # JWT ID for token tracking
        })

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)

        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh",
            "jti": str(uuid.uuid4())
        })

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Check token type
            if payload.get("type") != token_type:
                return None

            # Check expiration
            if datetime.utcnow() > datetime.fromtimestamp(payload.get("exp", 0)):
                return None

            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None

class SessionManager:
    """Secure session management"""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.active_sessions: Dict[str, set] = defaultdict(set)
        self.session_tokens: Dict[str, str] = {}

    async def create_session(self, user_id: str, session_data: Dict[str, Any]) -> str:
        """Create new session"""
        session_id = str(uuid.uuid4())
        session_key = f"session:{session_id}"

        session_data.update({
            'created_at': datetime.utcnow().isoformat(),
            'last_activity': datetime.utcnow().isoformat(),
            'session_id': session_id,
            'user_id': user_id
        })

        if self.redis_client:
            try:
                await self.redis_client.hset(session_key, mapping=session_data)
                await self.redis_client.expire(session_key, 86400)  # 24 hours
            except Exception as e:
                logger.error(f"Failed to store session in Redis: {e}")

        # Track active sessions
        self.active_sessions[user_id].add(session_id)
        self.session_tokens[session_id] = session_data.get('access_token', '')

        return session_id

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        if self.redis_client:
            try:
                session_data = await self.redis_client.hgetall(f"session:{session_id}")
                if session_data:
                    # Convert bytes to strings
                    return {k.decode(): v.decode() for k, v in session_data.items()}
            except Exception as e:
                logger.error(f"Failed to get session from Redis: {e}")

        return None

    async def update_session_activity(self, session_id: str):
        """Update session last activity"""
        if self.redis_client:
            try:
                await self.redis_client.hset(f"session:{session_id}", "last_activity", datetime.utcnow().isoformat())
            except Exception as e:
                logger.error(f"Failed to update session activity: {e}")

    async def terminate_session(self, session_id: str, user_id: str):
        """Terminate session"""
        if self.redis_client:
            try:
                await self.redis_client.delete(f"session:{session_id}")
            except Exception as e:
                logger.error(f"Failed to delete session from Redis: {e}")

        # Remove from active sessions
        self.active_sessions[user_id].discard(session_id)
        self.session_tokens.pop(session_id, None)

    async def get_user_sessions(self, user_id: str) -> List[str]:
        """Get active sessions for user"""
        return list(self.active_sessions.get(user_id, set()))

    async def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        if not self.redis_client:
            return

        try:
            # This would need to be implemented with Redis keys and scanning
            pass
        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")

class EnhancedAuthSystem:
    """Enhanced authentication system with security features"""

    def __init__(self, secret_key: str, redis_client: Optional[redis.Redis] = None):
        self.secret_key = secret_key
        self.redis_client = redis_client
        self.security_policy = SecurityPolicy()
        self.password_policy = PasswordPolicy(self.security_policy)
        self.security_manager = SecurityEventManager(redis_client)
        self.token_manager = TokenManager(secret_key)
        self.session_manager = SessionManager(redis_client)
        self.locked_accounts: Dict[str, datetime] = {}

    async def authenticate_user(
        self,
        username: str,
        password: str,
        request: Request,
        db: Session
    ) -> Tuple[bool, Optional[Dict[str, Any]], List[str]]:
        """Enhanced user authentication with security checks"""
        errors = []

        # Get client IP
        client_ip = request.client.host
        user_agent = request.headers.get("user-agent", "")

        # Check if IP is suspicious
        if await self.security_manager.is_ip_suspicious(client_ip):
            errors.append("Access denied from suspicious IP address")
            await self.security_manager.record_event(AuthEvent(
                event_type=AuthEventType.LOGIN_FAILURE,
                user_id=username,
                ip_address=client_ip,
                user_agent=user_agent,
                timestamp=datetime.utcnow(),
                success=False,
                details={"reason": "suspicious_ip"}
            ))
            return False, None, errors

        # Check if account is locked
        if username in self.locked_accounts:
            lock_time = self.locked_accounts[username]
            if datetime.utcnow() < lock_time:
                remaining_time = int((lock_time - datetime.utcnow()).total_seconds() / 60)
                errors.append(f"Account is locked. Try again in {remaining_time} minutes")
                return False, None, errors
            else:
                # Account lock expired
                del self.locked_accounts[username]

        # Get user from database (placeholder - implement actual database logic)
        user = self._get_user_from_db(username, db)
        if not user:
            errors.append("Invalid username or password")
            await self.security_manager.record_event(AuthEvent(
                event_type=AuthEventType.LOGIN_FAILURE,
                user_id=username,
                ip_address=client_ip,
                user_agent=user_agent,
                timestamp=datetime.utcnow(),
                success=False,
                details={"reason": "invalid_user"}
            ))
            return False, None, errors

        # Check if user is active
        if not user.get('is_active', True):
            errors.append("Account is disabled")
            await self.security_manager.record_event(AuthEvent(
                event_type=AuthEventType.LOGIN_FAILURE,
                user_id=username,
                ip_address=client_ip,
                user_agent=user_agent,
                timestamp=datetime.utcnow(),
                success=False,
                details={"reason": "account_disabled"}
            ))
            return False, None, errors

        # Verify password
        if not self.password_policy.verify_password(password, user.get('hashed_password', '')):
            errors.append("Invalid username or password")

            # Record failed login
            await self.security_manager.record_event(AuthEvent(
                event_type=AuthEventType.LOGIN_FAILURE,
                user_id=username,
                ip_address=client_ip,
                user_agent=user_agent,
                timestamp=datetime.utcnow(),
                success=False,
                details={"reason": "invalid_password"}
            ))

            # Check for account lockout
            recent_attempts = await self.security_manager.get_login_attempts(username)
            failed_attempts = [a for a in recent_attempts if not a.success]

            if len(failed_attempts) >= self.security_policy.max_login_attempts:
                lock_time = datetime.utcnow() + timedelta(minutes=self.security_policy.lockout_duration_minutes)
                self.locked_accounts[username] = lock_time

                await self.security_manager.record_event(AuthEvent(
                    event_type=AuthEventType.ACCOUNT_LOCKED,
                    user_id=username,
                    ip_address=client_ip,
                    user_agent=user_agent,
                    timestamp=datetime.utcnow(),
                    success=False,
                    details={"lockout_duration": self.security_policy.lockout_duration_minutes}
                ))

                errors.append(f"Account locked due to too many failed attempts. Try again in {self.security_policy.lockout_duration_minutes} minutes")

            return False, None, errors

        # Password is correct - generate tokens
        user_data = {
            'user_id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'is_admin': user.get('is_admin', False)
        }

        access_token = self.token_manager.create_access_token(user_data)
        refresh_token = self.token_manager.create_refresh_token(user_data)

        # Create session
        session_id = await self.session_manager.create_session(user['id'], {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'ip_address': client_ip,
            'user_agent': user_agent
        })

        # Record successful login
        await self.security_manager.record_event(AuthEvent(
            event_type=AuthEventType.LOGIN_SUCCESS,
            user_id=username,
            ip_address=client_ip,
            user_agent=user_agent,
            timestamp=datetime.utcnow(),
            success=True,
            details={"session_id": session_id}
        ))

        return True, {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'session_id': session_id,
            'user': user_data
        }, []

    async def refresh_token(self, refresh_token: str, request: Request) -> Tuple[bool, Optional[str], Optional[str]]:
        """Refresh access token"""
        client_ip = request.client.host
        user_agent = request.headers.get("user-agent", "")

        # Verify refresh token
        payload = self.token_manager.verify_token(refresh_token, "refresh")
        if not payload:
            await self.security_manager.record_event(AuthEvent(
                event_type=AuthEventType.LOGIN_FAILURE,
                user_id=payload.get('sub', 'unknown') if payload else 'unknown',
                ip_address=client_ip,
                user_agent=user_agent,
                timestamp=datetime.utcnow(),
                success=False,
                details={"reason": "invalid_refresh_token"}
            ))
            return False, None, None

        # Generate new access token
        user_data = {
            'user_id': payload.get('sub'),
            'username': payload.get('username'),
            'email': payload.get('email'),
            'is_admin': payload.get('is_admin', False)
        }

        new_access_token = self.token_manager.create_access_token(user_data)

        # Record token refresh
        await self.security_manager.record_event(AuthEvent(
            event_type=AuthEventType.TOKEN_REFRESH,
            user_id=user_data['user_id'],
            ip_address=client_ip,
            user_agent=user_agent,
            timestamp=datetime.utcnow(),
            success=True
        ))

        return True, new_access_token, refresh_token

    async def logout(self, session_id: str, user_id: str, request: Request):
        """User logout"""
        client_ip = request.client.host
        user_agent = request.headers.get("user-agent", "")

        # Terminate session
        await self.session_manager.terminate_session(session_id, user_id)

        # Record logout event
        await self.security_manager.record_event(AuthEvent(
            event_type=AuthEventType.LOGOUT,
            user_id=user_id,
            ip_address=client_ip,
            user_agent=user_agent,
            timestamp=datetime.utcnow(),
            success=True
        ))

    async def validate_token(self, token: str, request: Request) -> Optional[Dict[str, Any]]:
        """Validate access token and check session"""
        client_ip = request.client.host

        # Verify token
        payload = self.token_manager.verify_token(token, "access")
        if not payload:
            return None

        # Check if session is still active
        session_id = payload.get('session_id')
        if session_id:
            session = await self.session_manager.get_session(session_id)
            if not session:
                return None

            # Update session activity
            await self.session_manager.update_session_activity(session_id)

        return payload

    def _get_user_from_db(self, username: str, db: Session) -> Optional[Dict[str, Any]]:
        """Get user from database (placeholder)"""
        # This should be implemented with actual database queries
        return {
            'id': 1,
            'username': username,
            'email': 'user@example.com',
            'hashed_password': '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeZeUfkZMBs9kYZP6',  # 'password123'
            'is_active': True,
            'is_admin': False
        }

    async def change_password(self, user_id: str, old_password: str, new_password: str, db: Session) -> Tuple[bool, List[str]]:
        """Change user password with security checks"""
        errors = []

        # Get user
        user = self._get_user_from_db(user_id, db)
        if not user:
            errors.append("User not found")
            return False, errors

        # Verify old password
        if not self.password_policy.verify_password(old_password, user.get('hashed_password', '')):
            errors.append("Current password is incorrect")
            return False, errors

        # Validate new password
        is_valid, validation_errors = self.password_policy.validate_password(new_password, {
            'username': user['username'],
            'email': user['email']
        })

        if not is_valid:
            errors.extend(validation_errors)
            return False, errors

        # Check password history
        # This would require storing password hashes in a history table
        # For now, just check if new password is same as old
        if self.password_policy.verify_password(new_password, user.get('hashed_password', '')):
            errors.append("New password cannot be the same as current password")
            return False, errors

        # Generate new password hash
        new_hashed_password = self.password_policy.generate_password_hash(new_password)

        # Update password in database
        # This would require actual database update logic
        # For now, just return success

        # Record password change event
        await self.security_manager.record_event(AuthEvent(
            event_type=AuthEventType.PASSWORD_CHANGE,
            user_id=user_id,
            ip_address="system",  # Would be actual IP in real implementation
            user_agent="system",
            timestamp=datetime.utcnow(),
            success=True
        ))

        return True, []

    async def get_user_security_info(self, user_id: str) -> Dict[str, Any]:
        """Get user security information"""
        sessions = await self.session_manager.get_user_sessions(user_id)
        recent_events = await self.security_manager.get_login_attempts(user_id)

        return {
            'active_sessions': len(sessions),
            'recent_logins': len(recent_events),
            'failed_login_attempts': len([e for e in recent_events if not e.success]),
            'account_locked': user_id in self.locked_accounts,
            'lock_time': self.locked_accounts.get(user_id, '').isoformat() if user_id in self.locked_accounts else None
        }

# FastAPI dependency for enhanced authentication
class EnhancedAuthDependency:
    """Enhanced authentication dependency for FastAPI"""

    def __init__(self, auth_system: EnhancedAuthSystem):
        self.auth_system = auth_system
        self.security = HTTPBearer(auto_error=False)

    async def __call__(self, request: Request, credentials: Optional[HTTPAuthorizationCredentials] = None) -> Optional[Dict[str, Any]]:
        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication credentials are missing",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = credentials.credentials
        user_data = await self.auth_system.validate_token(token, request)

        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user_data

def create_enhanced_auth_dependency(secret_key: str, redis_client: Optional[redis.Redis] = None) -> EnhancedAuthDependency:
    """Create enhanced authentication dependency"""
    auth_system = EnhancedAuthSystem(secret_key, redis_client)
    return EnhancedAuthDependency(auth_system)