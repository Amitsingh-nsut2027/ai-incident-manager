"""Shared pytest fixtures.

The key trick: we run tests against an in-memory SQLite database (fast, isolated)
by OVERRIDING the get_db dependency. The real Postgres is never touched. This is
only possible because the app uses dependency injection (Phase 5).
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401  -- ensures all models are registered on Base
from app.db.base import Base
from app.db.session import get_db
from app.main import app


@pytest.fixture
def db_session():
    """A fresh in-memory SQLite database per test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # one shared in-memory connection
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    """A TestClient whose get_db dependency points at the test database."""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    """Register + log in a user, returning Authorization headers."""
    client.post(
        "/auth/register", json={"email": "t@example.com", "password": "password123"}
    )
    res = client.post(
        "/auth/login", data={"username": "t@example.com", "password": "password123"}
    )
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
