"""Authentication routes: register, login, refresh, and 'who am I'."""

import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.limiter import limiter
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import RefreshRequest, Token, UserCreate, UserResponse
from app.services import user_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    """Create a new account (role = viewer)."""
    if user_service.get_user_by_email(db, payload.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )
    return user_service.create_user(db, payload)


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")  # brute-force protection (Phase 21)
def login(
    request: Request,  # required by the rate limiter
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Log in with email + password, receive access & refresh tokens.

    OAuth2PasswordRequestForm expects form fields 'username' and 'password'.
    We use the email as the 'username'.
    """
    user = user_service.authenticate_user(db, form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(
        access_token=create_access_token(user.id, user.role),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/refresh", response_model=Token)
def refresh(body: RefreshRequest, db: Session = Depends(get_db)):
    """Exchange a valid refresh token for a fresh pair of tokens."""
    invalid = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
    )
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise invalid
        user_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise invalid

    user = user_service.get_user_by_id(db, user_id)
    if user is None:
        raise invalid
    return Token(
        access_token=create_access_token(user.id, user.role),
        refresh_token=create_refresh_token(user.id),
    )


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user (proves your token works)."""
    return current_user
