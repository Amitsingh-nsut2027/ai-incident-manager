"""The pipeline orchestrator: raw text -> list of structured log lines.

This is the public entry point other code uses (e.g. incident_service).
"""

from __future__ import annotations

from app.pipeline.parser import ParsedLogLine, parse_line


def process_raw_logs(
    raw_text: str, default_service: str | None = None
) -> list[ParsedLogLine]:
    """Split raw text into non-empty lines and parse each one.

    Uses a generator-style comprehension; for truly huge files you'd stream
    line-by-line (Phase 1) instead of materializing a list.
    """
    return [
        parse_line(line, default_service=default_service)
        for line in raw_text.splitlines()
        if line.strip()  # skip blank lines
    ]


def summarize_levels(parsed: list[ParsedLogLine]) -> dict[str, int]:
    """Count how many lines fall under each level (a tiny anomaly signal)."""
    counts: dict[str, int] = {}
    for entry in parsed:
        key = entry.level or "UNKNOWN"
        counts[key] = counts.get(key, 0) + 1
    return counts
