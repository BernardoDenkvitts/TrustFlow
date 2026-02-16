"""Auth module wiring and dependency injection."""

import uuid
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.auth.core.exceptions import ExpiredTokenError, InvalidTokenError
from src.modules.auth.core.services.auth_service import AuthService
from src.modules.auth.core.services.jwt_service import JwtService
from src.modules.auth.persistence.session_repository import SessionRepository
from src.modules.users.core.services import UserService
from src.modules.users.module import get_user_service
from src.shared.database.session import get_session


async def get_jwt_service() -> AsyncGenerator[JwtService, None]:
    yield JwtService()


async def get_session_repository(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AsyncGenerator[SessionRepository, None]:
    yield SessionRepository(session)


async def get_auth_service(
    user_service: Annotated[UserService, Depends(get_user_service)],
    jwt_service: Annotated[JwtService, Depends(get_jwt_service)],
    session_repository: Annotated[SessionRepository, Depends(get_session_repository)],
) -> AsyncGenerator[AuthService, None]:
    yield AuthService(user_service, jwt_service, session_repository)


security = HTTPBearer()


async def get_current_user_id(
    token: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    jwt_service: Annotated[JwtService, Depends(get_jwt_service)],
) -> uuid.UUID:
    """Get the current authenticated user ID from the JWT token.

    Args:
        token: The JWT access token.
        jwt_service: The JWT service to decode and verify the token.

    Returns:
        The UUID of the authenticated user.

    Raises:
        ExpiredTokenError: If the token is expired.
        InvalidTokenError: If the token is invalid.
    """
    payload = jwt_service.decode_token(token.credentials)
    user_id_str = payload.get("sub")
    return uuid.UUID(str(user_id_str))


