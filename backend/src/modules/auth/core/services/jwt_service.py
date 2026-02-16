"""JWT service."""

from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt

from src.config import settings
from src.modules.auth.core.exceptions import ExpiredTokenError, InvalidTokenError
from src.modules.auth.schemas import Token


class JwtService:
    """Service for handling JWT tokens."""

    def create_access_token(self, subject: str | Any) -> Token:
        """Create access token."""
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.access_token_expire_minutes
        )
        to_encode = {"sub": str(subject), "exp": expire}
        encoded_jwt = jwt.encode(
            to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
        )
        return Token(
            access_token=encoded_jwt,
            expires_in=settings.access_token_expire_minutes * 60
        )

    def decode_token(self, token: str) -> dict[str, Any]:
        """Decode and verify token.
        
        Args:
            token: The JWT token string.
            
        Returns:
            The decoded token payload.
            
        Raises:
            ExpiredTokenError: If token is expired.
            InvalidTokenError: If token is invalid.
        """
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
            )
            return payload
        except jwt.ExpiredSignatureError as e:
            raise ExpiredTokenError() from e
        except JWTError as e:
            raise InvalidTokenError() from e
