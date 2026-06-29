"""Pydantic schemas for the dashboard."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RecentIncident(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    service: str
    severity: int | None
    status: str
    created_at: datetime


class DashboardStats(BaseModel):
    total_incidents: int
    total_logs: int
    total_reports: int
    error_logs: int
    by_severity: dict[str, int]
    by_status: dict[str, int]
    by_service: dict[str, int]
    recent_incidents: list[RecentIncident]
