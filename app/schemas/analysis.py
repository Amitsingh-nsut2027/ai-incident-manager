"""Pydantic schema for an incident's pre-AI log analysis (Phase 10)."""

from pydantic import BaseModel


class IncidentAnalysis(BaseModel):
    incident_id: int
    total_lines: int
    level_counts: dict[str, int]
    services: list[str]
    error_count: int
    error_messages: list[str]
    # correlation id -> the messages logged under that id (one request's journey)
    correlation_groups: dict[str, list[str]]
