"""Pydantic schema for returning an AI-generated incident report."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    incident_id: int
    log_summary: str | None
    anomalies: str | None
    root_cause: str | None
    severity_assessment: str | None
    recommended_fix: str | None
    recovery_plan: str | None
    post_mortem: str | None
    confidence_score: float | None
    generated_at: datetime
