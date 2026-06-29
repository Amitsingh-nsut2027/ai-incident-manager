"""Reusable API dependencies for authentication & authorization.

These are FastAPI dependencies (Phase 5 DI). Endpoints declare them to require
a logged-in user (`get_current_user`) or a specific role (`require_role`).
"""

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User
from app.services import user_service

# Tells FastAPI to look for "Authorization: Bearer <token>". The tokenUrl makes
# the "Authorize" button in /docs work (it points at our login endpoint).
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Decode the access token and load the corresponding user (AuthN)."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":  # refresh tokens can't access the API
            raise credentials_exception
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    user = user_service.get_user_by_id(db, int(user_id))
    if user is None:
        raise credentials_exception
    return user


def require_role(*allowed_roles: str):
    """Factory that builds a dependency enforcing role membership (AuthZ).

    Usage:  user = Depends(require_role("admin"))
    """

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return current_user

    return role_checker
