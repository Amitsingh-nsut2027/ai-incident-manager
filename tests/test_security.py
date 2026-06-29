"""Unit tests for password hashing and JWT (no DB)."""

from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_password_hash_roundtrip():
    h = hash_password("supersecret")
    assert h != "supersecret"  # never store plaintext
    assert verify_password("supersecret", h) is True
    assert verify_password("wrong", h) is False


def test_password_hashes_are_salted():
    # same password -> different hashes (random salt)
    assert hash_password("same") != hash_password("same")


def test_jwt_roundtrip():
    token = create_access_token(user_id=7, role="admin")
    payload = decode_token(token)
    assert payload["sub"] == "7"
    assert payload["role"] == "admin"
    assert payload["type"] == "access"
