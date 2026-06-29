"""Custom Prometheus metrics (Phase 17).

These are business/AI metrics that the auto HTTP instrumentation can't know
about. They're exposed on /metrics alongside the standard request metrics and
scraped by Prometheus.
"""

from prometheus_client import Counter, Histogram

# Counters only ever increase.
incidents_created_total = Counter(
    "incidents_created_total", "Total number of incidents created"
)
analyses_total = Counter(
    "analyses_total", "Total number of full AI analyses run"
)
llm_calls_total = Counter(
    "llm_calls_total", "Total number of LLM calls made by agents"
)

# Histogram captures the distribution of analysis durations.
analysis_duration_seconds = Histogram(
    "analysis_duration_seconds",
    "Wall-clock duration of a full 7-agent analysis",
    buckets=(5, 10, 20, 30, 45, 60, 90, 120, 180, 300),
)
