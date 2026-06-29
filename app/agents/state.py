"""The shared state that flows through the incident-analysis graph.

This is the incident's "chart": it enters with the raw analysis, and each agent
(node) ADDS its findings as it runs. By the END, it holds the full diagnosis.

We use a TypedDict (LangGraph's default state type). `total=False` means every
field is optional — early nodes fill the first fields, later nodes the rest.
"""

from __future__ import annotations

from typing import TypedDict


class IncidentState(TypedDict, total=False):
    # --- inputs (set before the graph runs) ---
    incident_id: int
    analysis: dict  # the Phase 10 analysis (level counts, services, errors, ...)

    # --- filled in by each agent/node as the graph executes ---
    log_summary: str        # Log Analyzer
    anomalies: str          # Monitoring
    retrieved_context: str  # RAG: relevant runbooks / past incidents (Phase 15)
    root_cause: str         # Root Cause
    severity: int           # Severity Assessment
    severity_reason: str
    recommended_fix: str    # Fix Recommendation
    recovery_plan: str      # Recovery Planner
    report: str             # Report Generator
    confidence: float
