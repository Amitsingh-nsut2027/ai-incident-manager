"""Pydantic schemas for users and authentication tokens."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Registration payload. Note: we do NOT let clients pick their role here —
    everyone registers as 'viewer'. Promotion to engineer/admin is a separate,
    privileged action (otherwise anyone could register as admin!)."""

    email: EmailStr  # EmailStr validates the format automatically
    password: str = Field(min_length=8, examples=["supersecret123"])


class UserResponse(BaseModel):
    """Safe public view of a user — note password_hash is NEVER included."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    role: str
    created_at: datetime


class Token(BaseModel):
    """Returned on successful login/refresh."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str
