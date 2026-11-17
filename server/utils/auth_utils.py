from datetime import datetime, timedelta
from typing import Optional, Union, Dict, Any
import os
from jose import jwt, JWTError
from passlib.context import CryptContext
import uuid
import secrets
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from utils.email_service import send_verification_email, send_password_reset_email, should_skip_verification

# Load environment variables
load_dotenv()

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
if not SECRET_KEY or len(SECRET_KEY.encode("utf-8")) < 32:
    raise RuntimeError("JWT_SECRET_KEY must be configured with at least 32 bytes.")
if ALGORITHM not in {"HS256", "HS384", "HS512"}:
    raise RuntimeError("JWT_ALGORITHM must be one of HS256, HS384, or HS512.")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

# Email Provider
EMAIL_PROVIDER = os.getenv("EMAIL_PROVIDER", "smtp").lower()
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Development Configuration
SKIP_EMAIL_VERIFICATION = os.getenv("SKIP_EMAIL_VERIFICATION", "false").lower() == "true"

# OAuth2 scheme for token-based authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Password context for hashing and verifying passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Functions for password hashing and verification
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)

# Functions for JWT token generation and verification
def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get the current user from the JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check if token is refresh token
        if payload.get("type") == "refresh":
            raise credentials_exception
            
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return {"user_id": user_id, "payload": payload}
    except JWTError:
        raise credentials_exception

# Functions for token generation
def generate_verification_token() -> str:
    """Generate a token for email verification."""
    return secrets.token_urlsafe(32)

def generate_password_reset_token() -> str:
    """Generate a token for password reset."""
    return secrets.token_urlsafe(32)

# Email sending functionality
def send_verification_email(email: str, token: str, user_name: str = None) -> bool:
    """Send verification email to user.
    
    Args:
        email: The recipient's email address
        token: The verification token
        user_name: Optional name of the user
        
    Returns:
        bool: True if the email was sent successfully, False otherwise
    """
    # Use the new email service implementation
    from utils.email_service import send_verification_email as send_verification_email_service
    return send_verification_email_service(email, token, user_name)

def send_password_reset_email(email: str, token: str, user_name: str = None) -> bool:
    """Send password reset email to user.
    
    Args:
        email: The recipient's email address
        token: The password reset token
        user_name: Optional name of the user
        
    Returns:
        bool: True if the email was sent successfully, False otherwise
    """
    # Use the new email service implementation
    from utils.email_service import send_password_reset_email as send_password_reset_email_service
    return send_password_reset_email_service(email, token, user_name)

def should_skip_verification() -> bool:
    """Check if email verification should be skipped."""
    return SKIP_EMAIL_VERIFICATION
