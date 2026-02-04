"""Exception handlers for users module.

Converts domain exceptions to appropriate HTTP responses.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.modules.users.core.exceptions import (
    InvalidWalletAddressError,
    UserAlreadyExistsError,
    UserNotFoundError,
)


def register_users_exception_handlers(app: FastAPI) -> None:
    """Register exception handlers for the users module.

    Args:
        app: The FastAPI application instance.
    """

    @app.exception_handler(UserNotFoundError)
    async def user_not_found_handler(
        request: Request, exc: UserNotFoundError
    ) -> JSONResponse:
        """Handle UserNotFoundError exceptions."""
        return JSONResponse(
            status_code=404,
            content={
                "detail": str(exc),
                "error_code": "USER_NOT_FOUND",
            },
        )

    @app.exception_handler(UserAlreadyExistsError)
    async def user_already_exists_handler(
        request: Request, exc: UserAlreadyExistsError
    ) -> JSONResponse:
        """Handle UserAlreadyExistsError exceptions."""
        return JSONResponse(
            status_code=409,
            content={
                "detail": str(exc),
                "error_code": "USER_ALREADY_EXISTS",
                "field": exc.field,
            },
        )

    @app.exception_handler(InvalidWalletAddressError)
    async def invalid_wallet_address_handler(
        request: Request, exc: InvalidWalletAddressError
    ) -> JSONResponse:
        """Handle InvalidWalletAddressError exceptions."""
        return JSONResponse(
            status_code=400,
            content={
                "detail": str(exc),
                "error_code": "INVALID_WALLET_ADDRESS",
            },
        )
