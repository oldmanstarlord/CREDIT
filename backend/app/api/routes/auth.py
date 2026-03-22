"""Authentication routes: user registration, login, token refresh."""

from __future__ import annotations

import uuid
from datetime import datetime

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    TokenData,
    create_access_token,
    create_refresh_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.models.models import User, UserCategory, UserRole
from app.services.audit_service import AuditService
from app.schemas import TokenResponse, UserLoginRequest, UserRegisterRequest, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _uuid_or_400(value: str, field_name: str) -> uuid.UUID:
    try:
        return uuid.UUID(str(value))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid UUID for {field_name}",
        ) from exc


def _to_user_response(user: User) -> UserResponse:
    return UserResponse(
        id=str(user.id),
        email=user.email,
        phone_number=user.phone_number,
        full_name=user.full_name,
        role=user.role.value if user.role else None,
        date_of_birth=user.date_of_birth,
        gender=user.gender,
        aadhaar_number=user.aadhaar_number,
        user_category=user.user_category.value if user.user_category else None,
        is_verified=bool(user.is_verified),
        created_at=user.created_at,
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(request: UserRegisterRequest, db: Session = Depends(get_db)):
    """Register a borrower/admin account and issue JWT tokens."""
    existing = (
        db.query(User)
        .filter(or_(User.email == request.email, User.phone_number == request.phone_number))
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with same email or phone already exists",
        )

    category = None
    if request.user_category:
        try:
            category = UserCategory(request.user_category)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid user_category: {request.user_category}",
            ) from exc

    user = User(
        id=uuid.uuid4(),
        email=request.email,
        phone_number=request.phone_number,
        password_hash=hash_password(request.password),
        full_name=request.full_name,
        date_of_birth=request.date_of_birth,
        aadhaar_number=request.aadhaar_number,
        role=UserRole.BORROWER,
        user_category=category,
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    audit = AuditService(db)
    audit.log_event(
        "auth_register",
        user_id=user.id,
        actor_id=user.id,
        input_snapshot={"email": user.email, "role": user.role.value},
    )
    db.commit()

    access_token = create_access_token(str(user.id), user.email, user.role.value)
    refresh_token = create_refresh_token(str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: UserLoginRequest, db: Session = Depends(get_db)):
    """Authenticate user via email or phone and issue JWT tokens."""
    if not request.email and not request.phone_number:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Either email or phone_number is required",
        )

    user = (
        db.query(User)
        .filter(
            or_(
                User.email == request.email if request.email else False,
                User.phone_number == request.phone_number if request.phone_number else False,
            )
        )
        .first()
    )

    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    access_token = create_access_token(str(user.id), user.email, user.role.value)
    refresh_token = create_refresh_token(str(user.id))

    audit = AuditService(db)
    audit.log_event(
        "auth_login",
        user_id=user.id,
        actor_id=user.id,
        input_snapshot={"email": user.email},
    )
    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: dict, db: Session = Depends(get_db)):
    """Issue a fresh access token from a valid refresh token."""
    refresh_token_str = request.get("refresh_token")
    if not refresh_token_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="refresh_token required",
        )

    try:
        payload = jwt.decode(
            refresh_token_str,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        ) from exc

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token type",
        )

    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token payload",
        )

    user_uuid = _uuid_or_400(str(user_id), "refresh_token.user_id")

    user = db.query(User).filter(User.id == user_uuid).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    access_token = create_access_token(str(user.id), user.email, user.role.value)
    new_refresh_token = create_refresh_token(str(user.id))

    audit = AuditService(db)
    audit.log_event(
        "auth_refresh",
        user_id=user.id,
        actor_id=user.id,
        input_snapshot={"email": user.email},
    )
    db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/logout")
async def logout(current_user: TokenData = Depends(get_current_user), db: Session = Depends(get_db)):
    """Logout current user. Token blacklist integration can be added later."""
    user_id = _uuid_or_400(current_user.user_id, "current_user.user_id")
    audit = AuditService(db)
    audit.log_event("auth_logout", user_id=user_id, actor_id=user_id)
    db.commit()
    return {"message": f"Successfully logged out user {current_user.user_id}"}


@router.post("/verify-email/{token}")
async def verify_email(token: str):
    """Email verification placeholder endpoint."""
    if not token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="token required")
    return {"message": "Email verification accepted"}


@router.post("/request-password-reset")
async def request_password_reset(email: str, db: Session = Depends(get_db)):
    """Password reset request endpoint with non-enumerating response."""
    _ = db.query(User).filter(User.email == email).first()
    return {"message": "If email exists, reset link has been sent"}


@router.post("/reset-password/{token}")
async def reset_password(token: str, new_password: str, db: Session = Depends(get_db)):
    """Password reset placeholder endpoint."""
    if not token or not new_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="token and password required")
    return {"message": "Password reset accepted"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: TokenData = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get profile for current authenticated user."""
    user_uuid = _uuid_or_400(current_user.user_id, "current_user.user_id")
    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    audit = AuditService(db)
    audit.log_event("auth_me", user_id=user_uuid, actor_id=user_uuid)
    db.commit()

    return _to_user_response(user)
