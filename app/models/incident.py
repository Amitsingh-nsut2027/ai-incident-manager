"""Incident ORM model -> the `incidents` table (the core resource)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.log import Log
    from app.models.report import Report
    from app.models.user import User


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Nullable for now: until auth exists (Phase 8), incidents can be ownerless.
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    service: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    severity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="received", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user: Mapped[User | None] = relationship(back_populates="incidents")
    # cascade: deleting an incident deletes its logs/report too.
    logs: Mapped[list[Log]] = relationship(
        back_populates="incident", cascade="all, delete-orphan"
    )
    report: Mapped[Report | None] = relationship(
        back_populates="incident", cascade="all, delete-orphan", uselist=False
    )
