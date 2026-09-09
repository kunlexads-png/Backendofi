from datetime import datetime, timedelta
from typing import Optional, Any
from passlib.context import CryptContext
from jose import jwt, JWTError
from app.config import settings

# Setup password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against the hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hashes a password with bcrypt."""
    return pwd_context.hash(password)


def create_access_token(subject: str, role: str, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a signed JWT access token containing subject (user id or username) and role."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode: dict[str, Any] = {
        "sub": str(subject),
        "role": str(role),
        "exp": expire,
        "iat": datetime.utcnow()
    }
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_password_reset_token(email: str) -> str:
    """Generates a temporary token for password reset flows."""
    expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode = {"sub": email, "type": "password_reset", "exp": expire}
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def verify_password_reset_token(token: str) -> Optional[str]:
    """Verifies a password reset token and returns the email if valid."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "password_reset":
            return None
        return payload.get("sub")
    except JWTError:
        return None
