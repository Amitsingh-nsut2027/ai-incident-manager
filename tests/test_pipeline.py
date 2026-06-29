"""Unit tests for the log processing pipeline (no DB, no LLM — fast)."""

from app.pipeline.normalizer import normalize_level, parse_timestamp
from app.pipeline.parser import parse_line
from app.pipeline.processor import process_raw_logs


def test_normalize_level_synonyms():
    assert normalize_level("err") == "ERROR"
    assert normalize_level("WARNING") == "WARN"
    assert normalize_level("fatal") == "CRITICAL"
    assert normalize_level(None) is None


def test_parse_timestamp_handles_formats():
    assert parse_timestamp("2026-06-29T10:00:00") is not None
    assert parse_timestamp("2026-06-29 10:00:01,123") is not None
    assert parse_timestamp("not a timestamp") is None


def test_parse_line_extracts_fields_any_order():
    # level BEFORE timestamp (the bug we fixed in Phase 10)
    r = parse_line("ERROR 2026-06-29T10:00:00 timeout", default_service="db")
    assert r.level == "ERROR"
    assert r.timestamp is not None
    assert "timeout" in r.message
    assert r.service == "db"


def test_parse_line_is_robust_on_garbage():
    r = parse_line("a totally unstructured line")
    assert r.level is None
    assert r.timestamp is None
    assert r.message == "a totally unstructured line"


def test_parse_line_extracts_correlation_id():
    r = parse_line("INFO request_id=req-42 starting")
    assert r.request_id == "req-42"


def test_process_raw_logs_skips_blank_lines():
    parsed = process_raw_logs("line one\n\n   \nline two")
    assert len(parsed) == 2
