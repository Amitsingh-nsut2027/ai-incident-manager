"""Incident API routes (the REST endpoints from Phase 4's design).

Notice these are `def`, not `async def`. We use SYNCHRONOUS SQLAlchemy here, so
FastAPI runs each endpoint in a worker thread -> it won't block the event loop.
Mixing `async def` with blocking DB calls is a classic beginner bug; this avoids
it while keeping the code simple. (Async SQLAlchemy is a later, advanced option.)

As of Phase 8, these endpoints require authentication.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.core.limiter import limiter
from app.db.session import get_db
from app.models.user import User
from app.schemas.analysis import IncidentAnalysis
from app.schemas.incident import IncidentCreate, IncidentResponse
from app.schemas.log import LogResponse
from app.schemas.qa import AskRequest, AskResponse
from app.schemas.report import ReportResponse
from app.services import incident_service

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.post("", response_model=IncidentResponse, status_code=status.HTTP_201_CREATED)
def create_incident(
    payload: IncidentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  # must be logged in
):
    """Create an incident from an uploaded raw log (owned by the current user)."""
    return incident_service.create_incident(db, payload, user_id=current_user.id)


@router.get("", response_model=list[IncidentResponse])
def list_incidents(
    service: str | None = None,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  # any logged-in user
):
    """List incidents, optionally filtered by `?service=` (query params, Phase 4)."""
    return incident_service.list_incidents(db, service=service, limit=limit)


@router.get("/{incident_id}", response_model=IncidentResponse)
def get_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch a single incident, or 404 if it doesn't exist."""
    incident = incident_service.get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found"
        )
    return incident


@router.get("/{incident_id}/logs", response_model=list[LogResponse])
def get_incident_logs(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the structured (parsed) log lines for an incident."""
    if incident_service.get_incident(db, incident_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found"
        )
    return incident_service.get_incident_logs(db, incident_id)


@router.get("/{incident_id}/analysis", response_model=IncidentAnalysis)
def get_incident_analysis(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return an aggregated analysis of the incident's logs (Phase 10)."""
    analysis = incident_service.analyze_incident(db, incident_id)
    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found"
        )
    return analysis


@router.post("/{incident_id}/analyze", response_model=ReportResponse)
@limiter.limit("10/minute")  # the AI analysis is expensive — protect it (Phase 21)
def analyze_incident(
    request: Request,  # required by the rate limiter
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run the 7-agent AI analysis on an incident and return the saved report.

    Heads up: this triggers 7 sequential LLM calls and may take 30-90s locally.
    """
    report = incident_service.run_full_analysis(db, incident_id)
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found"
        )
    return report


@router.get("/{incident_id}/report", response_model=ReportResponse)
def get_incident_report(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fetch a previously generated AI report for an incident."""
    report = incident_service.get_report(db, incident_id)
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No report yet — run POST /incidents/{id}/analyze first",
        )
    return report


@router.post("/{incident_id}/ask", response_model=AskResponse)
@limiter.limit("20/minute")
def ask_incident(
    request: Request,
    incident_id: int,
    body: AskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ask a follow-up question about an analyzed incident (grounded in its report)."""
    answer = incident_service.ask_about_incident(db, incident_id, body.question)
    if answer is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No report yet — analyze the incident first",
        )
    return AskResponse(answer=answer)


@router.delete("/{incident_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),  # RBAC: admins only
):
    """Delete an incident (and cascade to its logs/report). Admin-only."""
    deleted = incident_service.delete_incident(db, incident_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found"
        )
    # 204 No Content -> return nothing.
