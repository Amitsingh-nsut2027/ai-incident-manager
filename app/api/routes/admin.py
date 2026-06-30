"""Admin routes: list users and change their roles (admin-only)."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserResponse

router = APIRouter(tags=["admin"])
_STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "static"

VALID_ROLES = {"viewer", "engineer", "admin"}


class RoleUpdate(BaseModel):
    role: str


@router.get("/admin/users", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    admin: User = Depends(require_role("admin")),
):
    """List all users (admin only)."""
    return list(db.scalars(select(User).order_by(User.id)).all())


@router.patch("/admin/users/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: int,
    body: RoleUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role("admin")),
):
    """Change a user's role (admin only)."""
    if body.role not in VALID_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role must be one of {sorted(VALID_ROLES)}",
        )
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.role = body.role
    db.commit()
    db.refresh(user)
    return user


@router.get("/admin")
def admin_page():
    """Serve the admin web page."""
    return FileResponse(_STATIC_DIR / "admin.html")
