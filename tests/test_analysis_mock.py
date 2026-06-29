"""Test the AI analysis flow WITHOUT calling the real LLM.

We replace the LangGraph agent graph with a fake that returns a fixed result.
This is how you test AI code reliably: don't assert on the model's words (they
vary) — assert that YOUR code correctly stores/handles the structured output.
"""

from app.services import incident_service


class FakeGraph:
    """Stand-in for the compiled LangGraph — returns a deterministic state."""

    def invoke(self, state):
        return {
            "log_summary": "summary",
            "anomalies": "anomalies",
            "root_cause": "connection pool exhaustion",
            "severity": 2,
            "severity_reason": "major degradation",
            "recommended_fix": "raise pool size",
            "recovery_plan": "1. mitigate 2. fix",
            "report": "post-mortem text",
            "confidence": 0.8,
        }


def test_run_full_analysis_saves_report(client, auth_headers, db_session, monkeypatch):
    # Create an incident through the API (lands in the test DB).
    res = client.post(
        "/incidents",
        json={"service": "checkout", "raw_log": "ERROR db timeout"},
        headers=auth_headers,
    )
    incident_id = res.json()["id"]

    # Swap the real (slow, nondeterministic) graph for our fake one.
    monkeypatch.setattr(incident_service, "incident_graph", FakeGraph())

    report = incident_service.run_full_analysis(db_session, incident_id)

    assert report is not None
    assert report.root_cause == "connection pool exhaustion"
    assert report.severity_assessment.startswith("SEV-2")
    assert report.post_mortem == "post-mortem text"
    assert report.confidence_score == 0.8


def test_analyze_missing_incident_returns_none(db_session):
    assert incident_service.run_full_analysis(db_session, 9999) is None
