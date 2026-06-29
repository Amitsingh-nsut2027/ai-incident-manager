"""Dashboard routes: stats API, health check, and the HTML page (Phase 16)."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.llm import is_available
from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.dashboard import DashboardStats
from app.services import dashboard_service

router = APIRouter(tags=["dashboard"])

_STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "static"


@router.get("/dashboard/stats", response_model=DashboardStats)
def dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Aggregated metrics for the dashboard (requires login)."""
    return dashboard_service.get_stats(db)


@router.get("/dashboard/health")
def dashboard_health(db: Session = Depends(get_db)):
    """System health: is the database reachable, is the LLM up?"""
    db_ok = True
    try:
        db.execute(select(1))
    except Exception:
        db_ok = False
    return {"database": db_ok, "llm": is_available()}


@router.get("/dashboard")
def dashboard_page():
    """Serve the dashboard web page."""
    return FileResponse(_STATIC_DIR / "dashboard.html")


@router.get("/analyze")
def analyze_page():
    """Serve the simple 'paste logs -> get diagnosis' web page."""
    return FileResponse(_STATIC_DIR / "analyze.html")
