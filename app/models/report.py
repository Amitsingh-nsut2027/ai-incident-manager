"""Report ORM model -> the `reports` table.

The AI-generated post-mortem for an incident. One incident has one report (1:1),
enforced by the `unique=True` on `incident_id`.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.incident import Incident


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    incident_id: Mapped[int] = mapped_column(
        ForeignKey("incidents.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )
    log_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    anomalies: Mapped[str | None] = mapped_column(Text, nullable=True)
    root_cause: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity_assessment: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommended_fix: Mapped[str | None] = mapped_column(Text, nullable=True)
    recovery_plan: Mapped[str | None] = mapped_column(Text, nullable=True)
    post_mortem: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    incident: Mapped[Incident] = relationship(back_populates="report")
