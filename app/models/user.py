"""User ORM model -> the `users` table.

Demonstrates the modern SQLAlchemy 2.0 typed style: each column is a
`Mapped[<python type>]` annotated with `mapped_column(...)`.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    # Imported only for type checkers, not at runtime -> avoids circular imports.
    from app.models.incident import Incident


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    # We store a HASH of the password, never the password itself (Phase 8).
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="viewer", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # One user has many incidents (1:N). `back_populates` links both sides.
    incidents: Mapped[list[Incident]] = relationship(back_populates="user")
