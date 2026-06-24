"""Unit tests for AuthService."""

import pytest

from src.services.auth_service import AuthService


@pytest.fixture
def auth_service():
    return AuthService()


def test_create_user_then_login(auth_service):
    auth_service.create_user("a@example.com", "hunter2")
    token = auth_service.authenticate_user("a@example.com", "hunter2")
    assert token is not None
    assert auth_service.jwt_helper.validate_token(token)


def test_login_with_wrong_password_raises(auth_service):
    auth_service.create_user("b@example.com", "correct-password")
    with pytest.raises(ValueError):
        auth_service.authenticate_user("b@example.com", "wrong-password")


def test_login_unknown_user_raises(auth_service):
    with pytest.raises(ValueError):
        auth_service.authenticate_user("ghost@example.com", "whatever")


def test_refresh_token_round_trip(auth_service):
    user = auth_service.create_user("c@example.com", "pw")
    token = auth_service.authenticate_user("c@example.com", "pw")
    refreshed = auth_service.refresh_jwt_token(token)
    payload = auth_service.jwt_helper.decode_token(refreshed)
    assert payload["user_id"] == user["id"]
