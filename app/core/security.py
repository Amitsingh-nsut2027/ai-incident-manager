"""Security primitives: password hashing and JWT creation/decoding.

This module is the ONLY place that knows how passwords are hashed and how tokens
are signed. Centralizing it means we can change the algorithm in one spot.
"""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import settings


# ---------------------------------------------------------------------------
# Password hashing (bcrypt) — we store the HASH, never the plaintext password.
# ---------------------------------------------------------------------------
def hash_password(password: str) -> str:
    """Hash a plaintext password with a random per-password salt."""
    # bcrypt works on bytes; we store the result as a UTF-8 string.
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Return True if the plaintext matches the stored hash."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))


# ---------------------------------------------------------------------------
# JWT creation & decoding
# ---------------------------------------------------------------------------
def _create_token(payload: dict, expires_delta: timedelta) -> str:
    """Sign a JWT with our secret key and an expiry."""
    to_encode = payload.copy()
    to_encode["exp"] = datetime.now(timezone.utc) + expires_delta
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(user_id: int, role: str) -> str:
    """Short-lived token sent on every request. Carries identity + role."""
    payload = {"sub": str(user_id), "role": role, "type": "access"}
    return _create_token(payload, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))


def create_refresh_token(user_id: int) -> str:
    """Long-lived token used only to obtain new access tokens."""
    payload = {"sub": str(user_id), "type": "refresh"}
    return _create_token(payload, timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))


def decode_token(token: str) -> dict:
    """Verify the signature + expiry and return the payload.

    Raises jwt.PyJWTError (or a subclass like ExpiredSignatureError) if the
    token is invalid, tampered, or expired.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
