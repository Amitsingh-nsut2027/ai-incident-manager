"""Integration/API tests for incident endpoints."""


def test_create_incident_requires_auth(client):
    res = client.post("/incidents", json={"service": "x", "raw_log": "ERROR boom"})
    assert res.status_code == 401


def test_create_and_fetch_incident(client, auth_headers):
    res = client.post(
        "/incidents",
        json={"service": "checkout", "raw_log": "ERROR 2026-06-29T10:00:00 boom", "severity": 1},
        headers=auth_headers,
    )
    assert res.status_code == 201
    incident_id = res.json()["id"]

    got = client.get(f"/incidents/{incident_id}", headers=auth_headers)
    assert got.status_code == 200
    assert got.json()["service"] == "checkout"


def test_incident_logs_are_parsed(client, auth_headers):
    res = client.post(
        "/incidents",
        json={"service": "x", "raw_log": "ERROR 2026-06-29T10:00:00 boom\nINFO ok"},
        headers=auth_headers,
    )
    incident_id = res.json()["id"]
    logs = client.get(f"/incidents/{incident_id}/logs", headers=auth_headers)
    assert logs.status_code == 200
    assert len(logs.json()) == 2  # two lines parsed into two Log rows


def test_missing_incident_returns_404(client, auth_headers):
    assert client.get("/incidents/9999", headers=auth_headers).status_code == 404


def test_analysis_aggregates_logs(client, auth_headers):
    res = client.post(
        "/incidents",
        json={"service": "x", "raw_log": "ERROR a\nERROR b\nINFO c"},
        headers=auth_headers,
    )
    incident_id = res.json()["id"]
    analysis = client.get(f"/incidents/{incident_id}/analysis", headers=auth_headers)
    assert analysis.status_code == 200
    body = analysis.json()
    assert body["total_lines"] == 3
    assert body["error_count"] == 2
