"""Log ORM model -> the `logs` table.

One incident has many log lines (1:N). Keeping logs in their own table (instead
of one big text blob on `incidents`) lets us query/filter individual lines.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.incident import Incident


class Log(Base):
    __tablename__ = "logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    incident_id: Mapped[int] = mapped_column(
        ForeignKey("incidents.id", ondelete="CASCADE"), index=True, nullable=False
    )
    timestamp: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    service: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Correlation IDs (Phase 10): link log lines belonging to the same request/trace.
    request_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    trace_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    incident: Mapped[Incident] = relationship(back_populates="logs")
