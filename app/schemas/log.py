"""Pydantic schema for returning parsed log lines over the API."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    timestamp: datetime | None
    level: str | None
    service: str | None
    message: str
