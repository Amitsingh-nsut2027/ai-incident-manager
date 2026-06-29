"""Dashboard aggregation logic (Phase 16).

Uses SQL GROUP BY to compute summary metrics in the database — far more
efficient than pulling every row into Python and counting.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.incident import Incident
from app.models.log import Log
from app.models.report import Report


def _grouped(db: Session, column) -> dict[str, int]:
    """Return {value: count} for a GROUP BY over the incidents table."""
    rows = db.execute(
        select(column, func.count(Incident.id)).group_by(column)
    ).all()
    out: dict[str, int] = {}
    for key, count in rows:
        out[str(key) if key is not None else "unassigned"] = count
    return out


def get_stats(db: Session) -> dict:
    """Compute all dashboard metrics."""
    total_incidents = db.scalar(select(func.count(Incident.id))) or 0
    total_logs = db.scalar(select(func.count(Log.id))) or 0
    total_reports = db.scalar(select(func.count(Report.id))) or 0
    error_logs = db.scalar(
        select(func.count(Log.id)).where(Log.level.in_(["ERROR", "CRITICAL"]))
    ) or 0

    recent = db.scalars(
        select(Incident).order_by(Incident.created_at.desc()).limit(10)
    ).all()

    return {
        "total_incidents": total_incidents,
        "total_logs": total_logs,
        "total_reports": total_reports,
        "error_logs": error_logs,
        "by_severity": _grouped(db, Incident.severity),
        "by_status": _grouped(db, Incident.status),
        "by_service": _grouped(db, Incident.service),
        "recent_incidents": list(recent),
    }
