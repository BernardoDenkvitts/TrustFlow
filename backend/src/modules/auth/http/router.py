"""Auth API router."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from fastapi.responses import RedirectResponse

from src.config import settings
from src.modules.auth.core.services.auth_service import AuthService
from src.modules.auth.module import get_auth_service, get_current_user_id
from src.modules.auth.schemas import Token

router = APIRouter(prefix="/auth", tags=["auth"])


def get_valid_refresh_token(
    refresh_token: Annotated[str | None, Cookie(alias=settings.refresh_cookie_name)] = None
) -> str:
    """Dependency to retrieve and validate refresh token from cookie."""
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )
    return refresh_token


@router.get(
    "/google",
    summary="Google OAuth",
    description="Get the URL to redirect the user to Google for authentication.",
)
async def get_google_auth_url(
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> RedirectResponse:
    """Get Google OAuth URL."""
    return RedirectResponse(await service.get_google_auth_url())


@router.get(
    "/callback/google",
    summary="Google OAuth Callback",
    description="Handle Google OAuth callback and create session.",
)
async def login_with_google(
    code: str,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> RedirectResponse:
    """Login with Google."""
    _, refresh_token = await service.login_with_google(code)

    response = RedirectResponse(
        url=f"{settings.frontend_url}/auth/success",
        status_code=status.HTTP_302_FOUND,
    )
    print("refresh ", refresh_token)
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        path=settings.refresh_cookie_path,
        max_age=settings.refresh_token_duration
    )
    
    return response


@router.get(
    "/session",
    response_model=Token,
    summary="Get Session Access Token",
    description="Get a new access token using the refresh token cookie. (Swagger doesn't support cookies)",
)
async def get_session(
    service: Annotated[AuthService, Depends(get_auth_service)],
    refresh_token: Annotated[str, Depends(get_valid_refresh_token)],
) -> Token:
    """Get access token from session."""
    return await service.get_session(refresh_token)


@router.post(
    "/refresh",
    response_model=Token,
    summary="Refresh Session",
    description="Rotate refresh token and get a new access token. (Swagger doesn't support cookies)",
)
async def refresh_session(
    response: Response,
    service: Annotated[AuthService, Depends(get_auth_service)],
    refresh_token: Annotated[str, Depends(get_valid_refresh_token)],
) -> Token:
    """Refresh session and rotate token."""
    access_token, new_refresh_token = await service.refresh_session(refresh_token)

    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=new_refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        path=settings.refresh_cookie_path,
        max_age=settings.refresh_token_duration
    )

    return access_token


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout",
    description="Revoke session and clear refresh token cookie.",
)
async def logout(
    response: Response,
    service: Annotated[AuthService, Depends(get_auth_service)],
    refresh_token: Annotated[str, Depends(get_valid_refresh_token)],
) -> None:
    """Logout."""
    if refresh_token:
        await service.logout(refresh_token)
    
    response.delete_cookie(key=settings.refresh_cookie_name, path=settings.refresh_cookie_path)


@router.post(
    "/logout-all",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout All",
    description="Revoke all sessions for the current user.",
)
async def logout_all(
    response: Response,
    service: Annotated[AuthService, Depends(get_auth_service)],
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> None:
    """Logout all sessions."""
    await service.logout_all(user_id)
    response.delete_cookie(key=settings.refresh_cookie_name, path=settings.refresh_cookie_path)