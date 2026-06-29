"""Parse a single raw log line into structured fields.

Real logs have NO universal format — fields appear in different orders. Rather
than demand a fixed layout, we extract each field independently:
  1. find a timestamp anywhere in the line (timestamps have a distinctive shape)
  2. find the first log-level keyword
  3. find a leading [service] tag
  4. whatever remains is the message
Every step is best-effort and NEVER raises, so malformed lines degrade
gracefully instead of crashing the pipeline.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime

from app.pipeline.normalizer import normalize_level, parse_timestamp


@dataclass
class ParsedLogLine:
    """One structured log line (the output of parsing)."""

    raw: str
    timestamp: datetime | None
    level: str | None
    service: str | None
    message: str
    request_id: str | None = None
    trace_id: str | None = None


# A timestamp like 2026-06-29T10:00:00.123Z or 2026/06/29 10:00:00 — matched
# ANYWHERE in the line, so field order doesn't matter.
_TIMESTAMP_RE = re.compile(
    r"\d{4}[-/]\d{2}[-/]\d{2}[ T]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?(?:Z|[+-]\d{2}:?\d{2})?"
)

# A log-level keyword anywhere (first match wins).
_LEVEL_RE = re.compile(
    r"\b(TRACE|DEBUG|INFO|INFORMATION|NOTICE|WARN|WARNING|ERROR|ERR|CRITICAL|CRIT|FATAL|EMERGENCY)\b",
    re.IGNORECASE,
)

# A [service] tag — only honored when it's at the START of the remaining text,
# so a bracketed word inside a message (e.g. "cache miss in [redis]") is left alone.
_SERVICE_RE = re.compile(r"^\[(?P<service>[^\]]+)\]")

# Correlation IDs like: request_id=abc-123, req-id: "xyz", trace_id=9f8e...
_REQUEST_ID_RE = re.compile(
    r"(?:request[_-]?id|req[_-]?id)['\"]?\s*[:=]\s*['\"]?([A-Za-z0-9._-]+)", re.IGNORECASE
)
_TRACE_ID_RE = re.compile(
    r"(?:trace[_-]?id)['\"]?\s*[:=]\s*['\"]?([A-Za-z0-9._-]+)", re.IGNORECASE
)


def _extract(pattern: re.Pattern[str], text: str) -> str | None:
    match = pattern.search(text)
    return match.group(1) if match else None


def _cut(text: str, start: int, end: int) -> str:
    """Remove text[start:end] and tidy up whitespace."""
    return (text[:start] + " " + text[end:]).strip()


def parse_line(line: str, default_service: str | None = None) -> ParsedLogLine:
    """Parse one line into a ParsedLogLine. Never raises."""
    remainder = line.strip()

    # 1. Timestamp — searched anywhere, then removed from the remainder.
    timestamp: datetime | None = None
    ts_match = _TIMESTAMP_RE.search(remainder)
    if ts_match:
        timestamp = parse_timestamp(ts_match.group(0))
        remainder = _cut(remainder, ts_match.start(), ts_match.end())

    # 2. Level — first keyword, then removed.
    level: str | None = None
    level_match = _LEVEL_RE.search(remainder)
    if level_match:
        level = normalize_level(level_match.group(1))
        remainder = _cut(remainder, level_match.start(), level_match.end())

    # 3. Service — only a LEADING [tag] counts.
    service: str | None = None
    service_match = _SERVICE_RE.match(remainder)
    if service_match:
        service = service_match.group("service")
        remainder = remainder[service_match.end():].strip()

    # 4. Correlation IDs — searched in the ORIGINAL line (we keep them in the
    #    message too, for human readability).
    request_id = _extract(_REQUEST_ID_RE, line)
    trace_id = _extract(_TRACE_ID_RE, line)

    # 5. Whatever's left is the message (fall back to the raw line if empty).
    message = remainder or line.strip()

    return ParsedLogLine(
        raw=line,
        timestamp=timestamp,
        level=level,
        service=service or default_service,
        message=message,
        request_id=request_id,
        trace_id=trace_id,
    )
