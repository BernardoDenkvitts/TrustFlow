"""Tests for JwtService."""

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from jose import jwt

from src.modules.auth.core.exceptions import ExpiredTokenError, InvalidTokenError
from src.modules.auth.core.services.jwt_service import JwtService


@pytest.fixture
def jwt_service():
    return JwtService()


@pytest.fixture
def mock_settings():
    with patch("src.modules.auth.core.services.jwt_service.settings") as mock:
        mock.access_token_expire_minutes = 30
        mock.jwt_secret_key = "test-secret"
        mock.jwt_algorithm = "HS256"
        yield mock


def test_create_access_token(jwt_service, mock_settings):
    subject = "user-123"
    token = jwt_service.create_access_token(subject)
    
    assert token.access_token is not None

    decoded = jwt.decode(
        token.access_token,
        mock_settings.jwt_secret_key,
        algorithms=[mock_settings.jwt_algorithm],
    )
    assert decoded["sub"] == subject


def test_decode_token_success(jwt_service, mock_settings):
    subject = "user-123"
    token_str = jwt.encode(
        {"sub": subject},
        mock_settings.jwt_secret_key,
        algorithm=mock_settings.jwt_algorithm,
    )
    
    decoded = jwt_service.decode_token(token_str)
    assert decoded["sub"] == subject


def test_decode_token_expired(jwt_service, mock_settings):
    # Create expired token
    expire = datetime.now(UTC) - timedelta(minutes=1)
    token_str = jwt.encode(
        {"sub": "user-123", "exp": expire},
        mock_settings.jwt_secret_key,
        algorithm=mock_settings.jwt_algorithm,
    )
    
    with pytest.raises(ExpiredTokenError):
        jwt_service.decode_token(token_str)


def test_decode_token_invalid(jwt_service, mock_settings):
    with pytest.raises(InvalidTokenError):
        jwt_service.decode_token("invalid-token")
