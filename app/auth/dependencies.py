from typing import List, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.models.user import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login", auto_error=False)


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Extracts and validates the current user from the Authorization bearer token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception

    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account"
        )
    return user


def require_roles(allowed_roles: List[UserRole]):
    """
    Role-based authorization dependency factory.
    Admins always have full access. Other roles are checked against allowed_roles.
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role == UserRole.ADMIN:
            return current_user
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[r.value for r in allowed_roles]}, your role: {current_user.role.value}"
            )
        return current_user
    return role_checker


# Convenient role shortcut dependencies
require_admin = require_roles([UserRole.ADMIN])

require_manager = require_roles([
    UserRole.ADMIN, 
    UserRole.WAREHOUSE_MANAGER
])

require_supervisor = require_roles([
    UserRole.ADMIN, 
    UserRole.WAREHOUSE_MANAGER, 
    UserRole.SUPERVISOR
])

require_officer = require_roles([
    UserRole.ADMIN, 
    UserRole.WAREHOUSE_MANAGER, 
    UserRole.SUPERVISOR, 
    UserRole.WAREHOUSE_OFFICER
])

require_any_authenticated = get_current_user
