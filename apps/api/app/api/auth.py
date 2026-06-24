import hashlib
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthError, ConflictError, TokenExpiredError
from app.core.input_sanitizer import sanitize_string
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.database import get_db
from app.models import User
from app.models.refresh_token import RefreshToken
from app.schemas import RefreshTokenRequest, TokenRefreshResponse, TokenResponse, UserCreate, UserLogin, UserResponse

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    sanitized_email = sanitize_string(data.email, 255)

    existing = await db.execute(select(User).where((User.email == sanitized_email) | (User.username == data.username)))
    if existing.scalar_one_or_none():
        raise ConflictError("Email or username already exists")

    user = User(
        email=sanitized_email,
        username=sanitize_string(data.username, 100),
        full_name=sanitize_string(data.full_name, 255),
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    access_token = create_access_token({"sub": str(user.id), "role": user.role.value})
    raw_refresh, hashed_refresh = create_refresh_token()
    refresh_record = RefreshToken(
        token_hash=hashed_refresh,
        user_id=user.id,
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    db.add(refresh_record)
    await db.commit()

    return TokenResponse(access_token=access_token, refresh_token=raw_refresh, user=UserResponse.model_validate(user))


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == sanitize_string(data.email, 255)))
    user = result.scalar_one_or_none()
    if not user or not verify_password(data.password, user.hashed_password):
        raise AuthError("Invalid email or password")

    access_token = create_access_token({"sub": str(user.id), "role": user.role.value})
    raw_refresh, hashed_refresh = create_refresh_token()
    refresh_record = RefreshToken(
        token_hash=hashed_refresh,
        user_id=user.id,
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    db.add(refresh_record)
    await db.commit()

    return TokenResponse(access_token=access_token, refresh_token=raw_refresh, user=UserResponse.model_validate(user))


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    hashed = hashlib.sha256(data.refresh_token.encode()).hexdigest()

    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == hashed,
            ~RefreshToken.is_revoked,
            RefreshToken.expires_at > datetime.now(UTC),
        )
    )
    token_record = result.scalar_one_or_none()
    if not token_record:
        raise TokenExpiredError("Refresh token is invalid or expired")

    token_record.is_revoked = True
    token_record.revoked_at = datetime.now(UTC)

    user_result = await db.execute(select(User).where(User.id == token_record.user_id))
    user = user_result.scalar_one_or_none()
    if not user or not user.is_active:
        raise AuthError("User not found or inactive")

    access_token = create_access_token({"sub": str(user.id), "role": user.role.value})
    raw_refresh, hashed_refresh = create_refresh_token()
    new_record = RefreshToken(
        token_hash=hashed_refresh,
        user_id=user.id,
        expires_at=datetime.now(UTC) + timedelta(days=7),
    )
    db.add(new_record)
    await db.commit()

    return TokenRefreshResponse(access_token=access_token, refresh_token=raw_refresh)


@router.post("/revoke", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_token(data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    hashed = hashlib.sha256(data.refresh_token.encode()).hexdigest()

    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == hashed,
            ~RefreshToken.is_revoked,
        )
    )
    token_record = result.scalar_one_or_none()
    if not token_record:
        raise TokenExpiredError("Refresh token is invalid or already revoked")

    token_record.is_revoked = True
    token_record.revoked_at = datetime.now(UTC)
    await db.commit()


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)
