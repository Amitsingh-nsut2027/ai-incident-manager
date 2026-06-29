"""A friendly end-to-end demo of the Incident Manager.

Run it with:   python demo.py
It shows, step by step, the whole system working in plain text — no web pages.
"""

from app.db.session import SessionLocal
from app.schemas.incident import IncidentCreate
from app.services import incident_service

SAMPLE_LOG = "\n".join(
    [
        "2026-06-30T02:00:00 INFO [gateway] request_id=req-9 start checkout",
        "2026-06-30T02:00:01 ERROR [checkout] request_id=req-9 timeout connecting to db after 30s",
        "2026-06-30T02:00:01 ERROR [checkout] request_id=req-9 connection pool exhausted (max=20)",
        "2026-06-30T02:00:02 CRITICAL [payment] request_id=req-9 payment failed",
        "2026-06-30T02:00:03 WARN [db] high connection count 198/200",
    ]
)


def line(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def main():
    db = SessionLocal()

    line("STEP 1 — Upload raw logs and create an incident")
    incident = incident_service.create_incident(
        db, IncidentCreate(service="checkout", raw_log=SAMPLE_LOG, severity=None)
    )
    print(f"Created incident #{incident.id} for service '{incident.service}'.")

    line("STEP 2 — The pipeline parsed each raw line into structured data")
    for log in incident_service.get_incident_logs(db, incident.id):
        ts = log.timestamp.strftime("%H:%M:%S") if log.timestamp else "--:--:--"
        print(f"  {ts} | {str(log.level):8} | {log.service:8} | {log.message}")

    line("STEP 3 — Analysis (counts, services, correlated request flow)")
    analysis = incident_service.analyze_incident(db, incident.id)
    print(f"  Total lines : {analysis['total_lines']}")
    print(f"  Errors      : {analysis['error_count']}")
    print(f"  Services    : {', '.join(analysis['services'])}")
    print(f"  Levels      : {analysis['level_counts']}")

    line("STEP 4 — Running the 7 AI agents (this takes ~1 minute)...")
    print("  Please wait — the local LLM is thinking...")
    report = incident_service.run_full_analysis(db, incident.id)

    line("STEP 5 — The AI's diagnosis")
    print(f"\nSEVERITY:\n  {report.severity_assessment}\n")
    print(f"ROOT CAUSE:\n  {report.root_cause}\n")
    print(f"RECOMMENDED FIX:\n  {report.recommended_fix}\n")
    print(f"CONFIDENCE: {report.confidence_score}")
    print(f"\n(The full recovery plan + post-mortem are saved to the database.)")

    print("\nDone! Your AI incident manager analyzed a real incident. 🎉")
    db.close()


if __name__ == "__main__":
    main()
