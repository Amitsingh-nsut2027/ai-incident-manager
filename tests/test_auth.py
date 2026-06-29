"""Integration/API tests for authentication."""


def test_register_returns_safe_user(client):
    res = client.post(
        "/auth/register", json={"email": "a@b.com", "password": "password123"}
    )
    assert res.status_code == 201
    body = res.json()
    assert body["email"] == "a@b.com"
    assert body["role"] == "viewer"  # never admin on self-register
    assert "password" not in body and "password_hash" not in body  # no secrets leak


def test_login_success(client):
    client.post("/auth/register", json={"email": "a@b.com", "password": "password123"})
    res = client.post(
        "/auth/login", data={"username": "a@b.com", "password": "password123"}
    )
    assert res.status_code == 200
    assert "access_token" in res.json()


def test_login_wrong_password(client):
    client.post("/auth/register", json={"email": "a@b.com", "password": "password123"})
    res = client.post(
        "/auth/login", data={"username": "a@b.com", "password": "WRONG"}
    )
    assert res.status_code == 401


def test_duplicate_email_rejected(client):
    client.post("/auth/register", json={"email": "a@b.com", "password": "password123"})
    res = client.post(
        "/auth/register", json={"email": "a@b.com", "password": "password123"}
    )
    assert res.status_code == 400


def test_me_requires_auth(client):
    assert client.get("/auth/me").status_code == 401
