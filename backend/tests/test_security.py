"""Unit tests for password hashing + JWT round-trip."""
from app.core import security


def test_password_hash_roundtrip():
    h = security.hash_password("s3cret!")
    assert h != "s3cret!"
    assert security.verify_password("s3cret!", h)
    assert not security.verify_password("wrong", h)


def test_jwt_roundtrip():
    token = security.create_access_token(42, extra={"role": "admin"})
    payload = security.decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "42"
    assert payload["role"] == "admin"


def test_jwt_invalid_token():
    assert security.decode_access_token("garbage.token.here") is None
