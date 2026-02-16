"""Auth service."""

import logging
import uuid
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

import httpx
from google.auth.transport import requests
from google.oauth2 import id_token as google_id_token

from src.config import settings
from src.modules.auth.core.exceptions import (
    InvalidGoogleCodeError,
    SessionNotFoundError,
)
from src.modules.auth.core.services.jwt_service import JwtService
from src.modules.auth.core.utils.token_utils import generate_refresh_token, hash_token
from src.modules.auth.persistence.session_repository import SessionRepository
from src.modules.auth.schemas import Token
from src.modules.users.core.enums.user_enums import OAuthProvider
from src.modules.users.core.services import UserService

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service."""

    def __init__(
        self,
        user_service: UserService,
        jwt_service: JwtService,
        session_repository: SessionRepository,
    ):
        self.user_service = user_service
        self.jwt_service = jwt_service
        self.session_repository = session_repository

    async def get_google_auth_url(self) -> str:
        """Get Google OAuth URL."""
        params = {
            "client_id": settings.google_client_id,
            "response_type": "code",
            "scope": "openid email profile",
            "redirect_uri": settings.google_redirect_uri,
            "access_type": "offline",
            "prompt": "consent",
        }

        return "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)

    async def login_with_google(self, code: str) -> tuple[Token, str]:
        """Login with Google code."""
        # Exchange code for access token
        async with httpx.AsyncClient() as client:
            token_url = "https://oauth2.googleapis.com/token"
            redirect_uri = settings.google_redirect_uri

            payload = {
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            }

            try:
                response = await client.post(token_url, data=payload)
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                logger.error(f"Google Token Exchange Failed: {e.response.text}")
                raise InvalidGoogleCodeError("Invalid Google Code") from e

            token_data = response.json()

            user_info = await self._verify_google_id_token(token_data.get("id_token"))
            google_id = user_info.get("sub")
            email = user_info.get("email")
  
            user = await self.user_service.get_user_by_oauth(
                OAuthProvider.GOOGLE, google_id
            )
            
            if not user:
                user = await self.user_service.create_user_oauth(
                    email=email,
                    oauth_provider=OAuthProvider.GOOGLE,
                    oauth_id=google_id,
                )

            # Create session
            await self.session_repository.enforce_session_limit(
                user.id, settings.max_sessions_per_user
            )

            refresh_token = generate_refresh_token()
            refresh_token_hash = hash_token(refresh_token)
            expires_at = datetime.now(UTC) + timedelta(days=30)

            await self.session_repository.create(
                user_id=user.id,
                refresh_token_hash=refresh_token_hash,
                expires_at=expires_at,
            )

            token = self.jwt_service.create_access_token(user.id)
            return token, refresh_token

    async def _verify_google_id_token(self, id_token: str) -> dict:
        """Validate Google token ID using google-auth lib."""
        try:
            idinfo = google_id_token.verify_oauth2_token(
                id_token, 
                requests.Request(), 
                settings.google_client_id,
                clock_skew_in_seconds=10
            )
            return idinfo
        except Exception as e:
            logger.error(f"ID Token validation failed: {e}")
            raise InvalidGoogleCodeError("Invalid ID token") from e

    async def get_session(self, refresh_token: str) -> Token:
        """Get access token from valid session without rotation."""
        refresh_token_hash = hash_token(refresh_token)
        session = await self.session_repository.get_by_hash(refresh_token_hash)

        if not session:
            raise SessionNotFoundError()

        if session.revoked_at:
             raise SessionNotFoundError("Session revoked")

        if session.expires_at < datetime.now(UTC):
            raise SessionNotFoundError("Session expired")

        return self.jwt_service.create_access_token(session.user_id)

    async def refresh_session(self, refresh_token: str) -> tuple[Token, str]:
        """Rotate refresh token and return new access token."""
        refresh_token_hash = hash_token(refresh_token)
        session = await self.session_repository.get_by_hash(refresh_token_hash)

        if not session:
            logger.warning("Session not found or invalid token during refresh")
            raise SessionNotFoundError()

        if session.revoked_at:
            logger.warning(f"Attempt to usage revoked session: {session.id}")
            # Token reuse detection could be implemented here
            raise SessionNotFoundError("Session revoked")

        now = datetime.now(UTC)

        if session.expires_at < now:
            logger.info(f"Session expired: {session.id}")
            raise SessionNotFoundError("Session expired")

        # Rotation
        new_refresh_token = generate_refresh_token()
        new_refresh_token_hash = hash_token(new_refresh_token)

        await self.session_repository.update_rotation(
            session_id=session.id, new_hash=new_refresh_token_hash, last_used_at=now
        )

        access_token = self.jwt_service.create_access_token(session.user_id)
        return access_token, new_refresh_token

    async def logout(self, refresh_token: str) -> None:
        """Revoke the current session."""
        refresh_token_hash = hash_token(refresh_token)
        session = await self.session_repository.get_by_hash(refresh_token_hash)
        if session:
            await self.session_repository.revoke(session.id)

    async def logout_all(self, user_id: uuid.UUID) -> None:
        """Revoke all sessions for a user."""
        await self.session_repository.revoke_all_for_user(user_id)
