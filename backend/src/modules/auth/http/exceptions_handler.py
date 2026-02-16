"""Exception handlers for auth module."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.modules.auth.core.exceptions import (
    InvalidGoogleCodeError,
    SessionAlreadyExistsError,
    SessionNotFoundError,
    ExpiredTokenError,
    InvalidTokenError,
)


def register_auth_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(ExpiredTokenError)
    async def expired_token_error_handler(
        request: Request, exc: ExpiredTokenError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            content={"detail": str(exc), "error_code": "EXPIRED_TOKEN"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(InvalidTokenError)
    async def invalid_token_error_handler(
        request: Request, exc: InvalidTokenError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            content={"detail": str(exc), "error_code": "INVALID_TOKEN"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(InvalidGoogleCodeError)
    async def invalid_google_code_handler(
        request: Request, exc: InvalidGoogleCodeError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            content={"detail": str(exc), "error_code": "INVALID_GOOGLE_CODE"},
        )

    @app.exception_handler(SessionNotFoundError)
    async def session_not_found_handler(
        request: Request, exc: SessionNotFoundError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            content={"detail": str(exc), "error_code": "SESSION_NOT_FOUND"},
        )

    @app.exception_handler(SessionAlreadyExistsError)
    async def session_already_exists_handler(
        request: Request, exc: SessionAlreadyExistsError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={"detail": str(exc), "error_code": "SESSION_ALREADY_EXISTS"},
        )

