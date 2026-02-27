"""Tests for JWT encode/decode, blocklist, and auth middleware."""
import pytest
from core.auth.jwt_handler import encode_jwt, decode_jwt, make_token_pair
from core.exceptions import AuthenticationError


@pytest.fixture(autouse=True)
def _set_env(mock_settings):
    pass


def test_encode_decode_access_token():
    token = encode_jwt("user-1", ["admin"], "access")
    payload = decode_jwt(token)
    assert payload["sub"] == "user-1"
    assert payload["roles"] == ["admin"]
    assert payload["type"] == "access"
    assert "jti" in payload


def test_encode_decode_refresh_token():
    token = encode_jwt("user-1", ["viewer"], "refresh")
    payload = decode_jwt(token)
    assert payload["type"] == "refresh"


def test_make_token_pair():
    pair = make_token_pair("user-2", ["operator"])
    assert "access_token"  in pair
    assert "refresh_token" in pair
    assert pair["token_type"] == "bearer"


def test_invalid_token_raises():
    with pytest.raises(AuthenticationError):
        decode_jwt("not.a.valid.token")


def test_tampered_token_raises():
    token = encode_jwt("user-1", ["admin"], "access")
    tampered = token[:-5] + "XXXXX"
    with pytest.raises(AuthenticationError):
        decode_jwt(tampered)
