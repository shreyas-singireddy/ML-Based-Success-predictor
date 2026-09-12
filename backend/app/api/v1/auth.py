from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.core.security import verify_password, create_access_token, create_refresh_token, decode_token
from backend.app.core.deps import get_current_user
from backend.app.models.user import User
from backend.app.schemas.auth import LoginRequest, Token, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(User)
        .where(User.email == login_data.email.lower().strip())
        .options(
            selectinload(User.student_profile),
            selectinload(User.faculty_profile)
        )
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )

    access_token = create_access_token(subject=user.id, role=user.role.value)
    refresh_token = create_refresh_token(subject=user.id, role=user.role.value)

    # Set secure HttpOnly cookie for refresh token
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # Set True in production with TLS
        samesite="lax",
        max_age=7 * 24 * 3600
    )

    profile_id = None
    if user.student_profile:
        profile_id = user.student_profile.id
    elif user.faculty_profile:
        profile_id = user.faculty_profile.id

    user_resp = UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        is_verified=user.is_verified,
        profile_id=profile_id
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=3600,
        user=user_resp
    )


@router.post("/refresh")
async def refresh_token_endpoint(
    response: Response,
    refresh_token: str = Cookie(None),
    db: AsyncSession = Depends(get_db)
):
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing"
        )

    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    user_id = payload.get("sub")
    user = await db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer active"
        )

    new_access_token = create_access_token(subject=user.id, role=user.role.value)
    return {"access_token": new_access_token, "token_type": "bearer", "expires_in": 3600}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    profile_id = None
    if current_user.student_profile:
        profile_id = current_user.student_profile.id
    elif current_user.faculty_profile:
        profile_id = current_user.faculty_profile.id

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        profile_id=profile_id
    )
