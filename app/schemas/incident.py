"""Pydantic schemas for the Incident resource.

IMPORTANT distinction:
- These (Pydantic) define the API contract -> what travels over HTTP as JSON.
- The ORM models in app/models/ define how data is STORED in the database.
Keeping them separate means we control exactly what we accept and expose.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class IncidentCreate(BaseModel):
    """What a client must send to create an incident (POST body)."""

    service: str = Field(..., min_length=1, max_length=255, examples=["checkout"])
    # max_length caps payload size — prevents DoS and LLM token blowup (Phase 21).
    raw_log: str = Field(
        ...,
        min_length=1,
        max_length=200_000,
        examples=["ERROR 2026-06-29T10:00:00 timeout connecting to db"],
    )
    # Optional. If provided, must be 1 (critical) .. 4 (minor).
    severity: int | None = Field(default=None, ge=1, le=4)


class IncidentResponse(BaseModel):
    """What we send back to the client. Note: no internal-only fields leak here."""

    # Lets Pydantic build this model directly from an ORM object's attributes.
    model_config = ConfigDict(from_attributes=True)

    id: int
    service: str
    severity: int | None
    status: str
    created_at: datetime
