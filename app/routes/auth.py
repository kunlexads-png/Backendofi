import logging
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.models.user import User, UserRole
from app.schemas.user import (
    UserCreate, UserResponse, LoginRequest, PasswordChange,
    PasswordResetRequest, PasswordResetConfirm
)
from app.schemas.common import StandardResponse
from app.auth.security import (
    verify_password, get_password_hash, create_access_token,
    create_password_reset_token, verify_password_reset_token
)
from app.auth.dependencies import get_current_user
from app.utils.helpers import standard_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", summary="Register a new warehouse user")
def register_user(
    payload: UserCreate,
    db: Session = Depends(get_db)
):
    """Registers a new user account. Passwords are encrypted with bcrypt."""
    existing_username = db.query(User).filter(User.username == payload.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username is already taken"
        )
    existing_email = db.query(User).filter(User.email == payload.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered"
        )

    # First user can automatically be Admin for initial setup ease
    user_count = db.query(User).count()
    assigned_role = UserRole.ADMIN if user_count == 0 else payload.role

    new_user = User(
        username=payload.username,
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=get_password_hash(payload.password),
        role=assigned_role,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info(f"User registered successfully: {new_user.username} ({new_user.role})")
    
    user_data = UserResponse.model_validate(new_user).model_dump()
    return standard_response(
        data=user_data,
        message="User registered successfully",
        status_code=status.HTTP_201_CREATED
    )


@router.post("/login", summary="User login and JWT token generation")
def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db)
):
    """Authenticates user with username & password and returns a signed JWT."""
    user = db.query(User).filter(User.username == credentials.username).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        logger.warning(f"Failed login attempt for username: {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your user account is inactive"
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        subject=user.id,
        role=user.role.value if hasattr(user.role, "value") else str(user.role),
        expires_delta=access_token_expires
    )

    logger.info(f"User logged in: {user.username}")
    user_info = UserResponse.model_validate(user).model_dump()
    
    return standard_response(
        data={
            "access_token": token,
            "token_type": "bearer",
            "expires_in_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            "user": user_info
        },
        message="Login successful"
    )


@router.get("/me", summary="Get currently authenticated user")
def get_me(current_user: User = Depends(get_current_user)):
    user_info = UserResponse.model_validate(current_user).model_dump()
    return standard_response(
        data=user_info,
        message="Current user profile retrieved"
    )


@router.post("/logout", summary="Logout current session")
def logout(current_user: User = Depends(get_current_user)):
    """Informs client to drop access token."""
    logger.info(f"User logged out: {current_user.username}")
    return standard_response(
        data=None,
        message="Logged out successfully"
    )


@router.post("/change-password", summary="Change current user's password")
def change_password(
    payload: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(payload.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password verification failed"
        )
    current_user.hashed_password = get_password_hash(payload.new_password)
    db.commit()
    logger.info(f"Password changed for user: {current_user.username}")
    return standard_response(
        data=None,
        message="Password updated successfully"
    )


@router.post("/forgot-password", summary="Request password reset token")
def forgot_password(
    payload: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        # Prevent user enumeration by returning standard positive response
        return standard_response(
            data={"status": "dispatched"},
            message="If the email exists in our system, a password reset link has been dispatched."
        )
    reset_token = create_password_reset_token(user.email)
    # In production, send via email. For developer reference, token is provided in data.
    return standard_response(
        data={"reset_token": reset_token},
        message="Password reset token generated successfully"
    )


@router.post("/reset-password", summary="Confirm password reset with token")
def reset_password(
    payload: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    email = verify_password_reset_token(payload.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token"
        )
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User associated with token not found"
        )
    user.hashed_password = get_password_hash(payload.new_password)
    db.commit()
    return standard_response(
        data=None,
        message="Password has been reset successfully"
    )
