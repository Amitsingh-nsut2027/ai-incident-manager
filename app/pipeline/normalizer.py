"""Normalization helpers: turn inconsistent log data into canonical forms.

Real logs are messy — different services write 'ERR', 'Error', 'ERROR' and use
different timestamp formats. We map every variant to ONE canonical value so that
later filtering/counting ("how many ERRORs?") is reliable.
"""

from __future__ import annotations

from datetime import datetime

# Map many synonyms -> a small canonical set of levels.
_LEVEL_MAP = {
    "TRACE": "TRACE",
    "DEBUG": "DEBUG",
    "INFO": "INFO",
    "INFORMATION": "INFO",
    "NOTICE": "INFO",
    "WARN": "WARN",
    "WARNING": "WARN",
    "ERROR": "ERROR",
    "ERR": "ERROR",
    "CRITICAL": "CRITICAL",
    "CRIT": "CRITICAL",
    "FATAL": "CRITICAL",
    "EMERGENCY": "CRITICAL",
}

# Timestamp formats we try (in addition to ISO 8601 via fromisoformat).
_TS_FORMATS = (
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M:%S.%f",
    "%Y/%m/%d %H:%M:%S",
    "%d/%b/%Y:%H:%M:%S %z",  # common web-server (Apache/Nginx) format
)


def normalize_level(level: str | None) -> str | None:
    """Map a raw level string to a canonical level, or None if absent."""
    if not level:
        return None
    cleaned = level.strip().upper()
    return _LEVEL_MAP.get(cleaned, cleaned)


def parse_timestamp(value: str | None) -> datetime | None:
    """Best-effort parse of a timestamp string into a datetime.

    Returns None if nothing matches — we NEVER raise, so one weird line can't
    break the whole pipeline (robustness, Phase 1 exceptions lesson).
    """
    if not value:
        return None
    text = value.strip().replace(",", ".")  # some logs use a comma for millis

    # Try ISO 8601 first (handles 'T', 'Z', offsets, fractional seconds).
    iso_candidate = text.replace(" ", "T", 1) if "T" not in text else text
    try:
        return datetime.fromisoformat(iso_candidate)
    except ValueError:
        pass

    for fmt in _TS_FORMATS:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None
