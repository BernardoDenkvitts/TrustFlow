"""Tests for AuthService."""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from httpx import Request, Response

from src.modules.auth.core.exceptions import SessionNotFoundError
from src.modules.auth.core.models.session import Session
from src.modules.auth.core.services.auth_service import AuthService
from src.modules.auth.core.services.jwt_service import JwtService
from src.modules.auth.persistence.session_repository import SessionRepository
from src.modules.auth.schemas import Token
from src.modules.users.core.enums.user_enums import OAuthProvider
from src.modules.users.core.models import User
from src.modules.users.core.services import UserService


GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"


@pytest.fixture
def mock_user_service():
    return AsyncMock(spec=UserService)


@pytest.fixture
def mock_jwt_service():
    return AsyncMock(spec=JwtService)


@pytest.fixture
def mock_session_repository():
    return AsyncMock(spec=SessionRepository)


@pytest.fixture
def auth_service(mock_user_service, mock_jwt_service, mock_session_repository):
    return AuthService(
        user_service=mock_user_service,
        jwt_service=mock_jwt_service,
        session_repository=mock_session_repository,
    )


@pytest.fixture
def mock_settings():
    with patch("src.modules.auth.core.services.auth_service.settings") as mock:
        mock.google_client_id = "test-client-id"
        mock.google_client_secret = "test-client-secret"
        mock.frontend_url = "http://localhost:3000"
        mock.access_token_expire_minutes = 30
        mock.jwt_secret_key = "test-secret"
        mock.jwt_algorithm = "HS256"
        mock.google_redirect_uri = "http://localhost:8000/auth/callback/google"
        yield mock


@pytest.fixture
def mock_google_oauth():
    """Mock Google OAuth flow including httpx client and token verification."""
    def _mock_google_oauth(google_id: str, email: str, id_token: str = "test-id-token"):
        mock_client = AsyncMock()

        mock_client.post.return_value = Response(
            200,
            json={
                "access_token": "test-access-token",
                "id_token": id_token
            },
            request=Request("POST", GOOGLE_TOKEN_URL)
        )

        mock_verify_data = {
            "sub": google_id,
            "email": email
        }
        
        return mock_client, mock_verify_data
    
    return _mock_google_oauth


@pytest.mark.asyncio
async def test_login_with_google_success_existing_user(
    auth_service, mock_user_service, mock_jwt_service,
    mock_session_repository, mock_settings, mock_google_oauth
):
    code = "test-code"
    mock_user_id = uuid.uuid4()
    mock_user = User(id=mock_user_id, email="test@example.com")
    
    mock_user_service.get_user_by_oauth.return_value = mock_user
    mock_jwt_service.create_access_token.return_value = Token(access_token="test-jwt", expires_in=3600)
    
    mock_client, mock_verify_data = mock_google_oauth("google-id-123", "test@example.com")
    
    with patch("httpx.AsyncClient") as mock_client_cls, \
         patch("src.modules.auth.core.services.auth_service.google_id_token.verify_oauth2_token") as mock_verify:
        
        mock_client_cls.return_value.__aenter__.return_value = mock_client
        mock_verify.return_value = mock_verify_data
        
        token, refresh_token = await auth_service.login_with_google(code)
    
    assert token.access_token == "test-jwt"
    assert isinstance(refresh_token, str)
    assert len(refresh_token) > 0
    
    mock_user_service.get_user_by_oauth.assert_called_once_with(
        OAuthProvider.GOOGLE, "google-id-123"
    )
    mock_jwt_service.create_access_token.assert_called_once_with(mock_user_id)
    mock_session_repository.create.assert_called_once()
    call_args = mock_session_repository.create.call_args[1]
    assert call_args["user_id"] == mock_user_id
    assert "refresh_token_hash" in call_args
    assert "expires_at" in call_args


@pytest.mark.asyncio
async def test_get_session_success(
    auth_service, mock_session_repository, mock_jwt_service
):
    refresh_token = "valid-refresh-token"
    mock_user_id = uuid.uuid4()
    session = Session(
        id=uuid.uuid4(),
        user_id=mock_user_id,
        refresh_token_hash="hashed-token",
        expires_at=datetime.now(UTC) + timedelta(days=1),
        revoked_at=None
    )
    
    mock_session_repository.get_by_hash.return_value = session
    mock_jwt_service.create_access_token.return_value = Token(
        access_token="new-access-token",
        expires_in=3600
    )
    
    token = await auth_service.get_session(refresh_token)
    
    assert token.access_token == "new-access-token"
    mock_session_repository.get_by_hash.assert_called_once()


@pytest.mark.asyncio
async def test_get_session_not_found(
    auth_service, mock_session_repository
):
    mock_session_repository.get_by_hash.return_value = None
    
    with pytest.raises(SessionNotFoundError):
        await auth_service.get_session("invalid-token")


@pytest.mark.asyncio
async def test_refresh_session_success(
    auth_service, mock_session_repository, mock_jwt_service
):
    refresh_token = "valid-refresh-token"
    mock_user_id = uuid.uuid4()
    session = Session(
        id=uuid.uuid4(),
        user_id=mock_user_id,
        refresh_token_hash="hashed-token",
        expires_at=datetime.now(UTC) + timedelta(days=1),
        revoked_at=None
    )
    
    mock_session_repository.get_by_hash.return_value = session
    mock_jwt_service.create_access_token.return_value = Token(
        access_token="rotated-access-token",
        expires_in=3600
    )
    
    token, new_refresh_token = await auth_service.refresh_session(refresh_token)
    
    assert token.access_token == "rotated-access-token"
    assert new_refresh_token != refresh_token
    mock_session_repository.update_rotation.assert_called_once()


@pytest.mark.asyncio
async def test_logout_success(
    auth_service, mock_session_repository
):
    refresh_token = "valid-refresh-token"
    session = Session(id=uuid.uuid4(), refresh_token_hash="hash")
    mock_session_repository.get_by_hash.return_value = session
    
    await auth_service.logout(refresh_token)
    
    mock_session_repository.revoke.assert_called_once_with(session.id)
