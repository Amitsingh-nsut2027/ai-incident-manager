"""Business logic for incidents.

Routes stay thin (just HTTP concerns); the real work lives here. This separation
makes the logic reusable and easy to unit-test without spinning up a web server.
"""

import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.graph import incident_graph
from app.core.metrics import (
    analyses_total,
    analysis_duration_seconds,
    incidents_created_total,
)
from app.models.incident import Incident
from app.models.log import Log
from app.models.report import Report
from app.pipeline.processor import process_raw_logs
from app.schemas.incident import IncidentCreate


def create_incident(
    db: Session, payload: IncidentCreate, user_id: int | None = None
) -> Incident:
    """Create an incident and store its raw log as the first Log row.

    Both inserts happen in ONE transaction: either both succeed or both roll
    back (Phase 6's Atomicity in action). `user_id` links the incident to its
    creator (the logged-in user, Phase 8).
    """
    incident = Incident(
        service=payload.service,
        severity=payload.severity,
        status="received",
        user_id=user_id,
    )
    db.add(incident)
    db.flush()  # sends the INSERT so incident.id is populated, but doesn't commit yet

    # Run the processing pipeline: raw text -> structured log lines (Phase 9).
    # One Log row is created per parsed line.
    parsed_lines = process_raw_logs(payload.raw_log, default_service=payload.service)
    for entry in parsed_lines:
        db.add(
            Log(
                incident_id=incident.id,
                timestamp=entry.timestamp,
                level=entry.level,
                message=entry.message,
                service=entry.service,
                request_id=entry.request_id,
                trace_id=entry.trace_id,
            )
        )

    db.commit()       # commit incident + all log rows together (one transaction)
    db.refresh(incident)  # reload with DB-generated values (id, created_at)
    incidents_created_total.inc()  # Prometheus metric (Phase 17)
    return incident


def get_incident(db: Session, incident_id: int) -> Incident | None:
    """Fetch one incident by primary key (returns None if not found)."""
    return db.get(Incident, incident_id)


def get_incident_logs(db: Session, incident_id: int) -> list[Log]:
    """Return all parsed log lines for an incident, in insertion order."""
    stmt = select(Log).where(Log.incident_id == incident_id).order_by(Log.id)
    return list(db.scalars(stmt).all())


def analyze_incident(db: Session, incident_id: int) -> dict | None:
    """Aggregate the parsed logs into a structured analysis (Phase 10).

    This is a pre-AI summary: level counts, services involved, error count, and
    logs grouped by correlation id. The AI agents (next phases) build on this.
    """
    incident = db.get(Incident, incident_id)
    if incident is None:
        return None

    logs = get_incident_logs(db, incident_id)

    level_counts: dict[str, int] = {}
    services: set[str] = set()
    correlation_groups: dict[str, list[str]] = {}
    error_messages: list[str] = []

    for log in logs:
        key = log.level or "UNKNOWN"
        level_counts[key] = level_counts.get(key, 0) + 1

        if log.service:
            services.add(log.service)

        corr_id = log.request_id or log.trace_id
        if corr_id:
            correlation_groups.setdefault(corr_id, []).append(log.message)

        if log.level in ("ERROR", "CRITICAL"):
            error_messages.append(log.message)

    return {
        "incident_id": incident_id,
        "total_lines": len(logs),
        "level_counts": level_counts,
        "services": sorted(services),
        "error_count": len(error_messages),
        "error_messages": error_messages[:20],  # cap to keep the payload sane
        "correlation_groups": correlation_groups,
    }


def list_incidents(
    db: Session, service: str | None = None, limit: int = 20
) -> list[Incident]:
    """List incidents, newest first, optionally filtered by service."""
    stmt = select(Incident).order_by(Incident.created_at.desc()).limit(limit)
    if service:
        stmt = stmt.where(Incident.service == service)
    return list(db.scalars(stmt).all())


def get_report(db: Session, incident_id: int) -> Report | None:
    """Return the saved AI report for an incident, if one exists."""
    return db.scalar(select(Report).where(Report.incident_id == incident_id))


def run_full_analysis(db: Session, incident_id: int) -> Report | None:
    """Run the 7-agent graph on an incident and persist the resulting report.

    Steps: build the Phase 10 analysis -> run the LangGraph multi-agent graph ->
    save a Report row -> update the incident's severity/status.
    NOTE: this runs 7 sequential LLM calls and can take a while. In production
    you'd run it in a background worker (Celery) — a later phase.
    """
    analysis = analyze_incident(db, incident_id)
    if analysis is None:
        return None

    # Run the multi-agent graph (Phase 13/14), timing it for Prometheus.
    analyses_total.inc()
    _start = time.perf_counter()
    result = incident_graph.invoke({"incident_id": incident_id, "analysis": analysis})
    analysis_duration_seconds.observe(time.perf_counter() - _start)

    # Replace any previous report (incident_id is unique).
    existing = get_report(db, incident_id)
    if existing is not None:
        db.delete(existing)
        db.flush()

    report = Report(
        incident_id=incident_id,
        log_summary=result.get("log_summary"),
        anomalies=result.get("anomalies"),
        root_cause=result.get("root_cause"),
        severity_assessment=f"SEV-{result.get('severity')}: {result.get('severity_reason', '')}",
        recommended_fix=result.get("recommended_fix"),
        recovery_plan=result.get("recovery_plan"),
        post_mortem=result.get("report"),
        confidence_score=result.get("confidence"),
    )
    db.add(report)

    incident = db.get(Incident, incident_id)
    if incident is not None:
        incident.severity = result.get("severity")
        incident.status = "analyzed"

    db.commit()
    db.refresh(report)
    return report


def delete_incident(db: Session, incident_id: int) -> bool:
    """Delete an incident (and its logs/report via cascade). Returns success."""
    incident = db.get(Incident, incident_id)
    if incident is None:
        return False
    db.delete(incident)
    db.commit()
    return True
