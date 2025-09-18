import os
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User

# Import unified configuration
from config.settings import settings

# Configuration from unified settings
SECRET_KEY = settings.security.jwt_secret_key
ALGORITHM = settings.security.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.security.jwt_access_token_expire_minutes
REFRESH_TOKEN_EXPIRE_DAYS = settings.security.jwt_refresh_token_expire_days

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def hash_password(password: str) -> str:
    """Hash password with bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password"""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    """Create refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user_by_username_or_email(db: Session, username_or_email: str):
    """Get user by username OR email (supporta entrambi)"""
    return db.query(User).filter(
        (User.username == username_or_email) | (User.email == username_or_email)
    ).first()

def get_user_by_username(db: Session, username: str):
    """Get user by username (mantenuto per compatibilità)"""
    return db.query(User).filter(User.username == username).first()

def authenticate_user(db: Session, username_or_email: str, password: str):
    """Authenticate user - supports login with username or email"""
    print(f"[AUTH] Tentativo login per: {username_or_email}")
    
    user = get_user_by_username_or_email(db, username_or_email)
    if not user:
        print(f"[AUTH] Utente NON trovato: {username_or_email}")
        return False
    
    print(f"[AUTH] Utente trovato - ID: {user.id}, Username: {user.username}, Email: {user.email}")
    print(f"[AUTH] Hash salvato: {user.hashed_password[:20]}...")
    
    if not verify_password(password, user.hashed_password):
        print(f"[AUTH] Password ERRATA per {username_or_email}")
        return False
    
    print(f"[AUTH] Login RIUSCITO per {user.username}")
    return user

def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current user from token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        token_type: str = payload.get("type")
        if username is None or token_type != "access":
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Get database session
    db = SessionLocal()
    try:
        user = get_user_by_username(db, username=username)
        if user is None:
            raise credentials_exception
        return user
    finally:
        db.close()

def get_current_active_user(current_user: User = Depends(get_current_user)):
    """Get current active user"""
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
