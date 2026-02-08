"""Exception handlers for disputes module.

Converts domain exceptions to appropriate HTTP responses.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.modules.disputes.core.exceptions import (
    DisputeAlreadyExistsError,
    DisputeAlreadyResolvedError,
    DisputeNotFoundError,
    UnauthorizedArbitratorError,
    UnauthorizedDisputeAccessError,
)


def register_disputes_exception_handlers(app: FastAPI) -> None:
    """Register exception handlers for the disputes module.

    Args:
        app: The FastAPI application instance.
    """

    @app.exception_handler(DisputeNotFoundError)
    async def dispute_not_found_handler(
        request: Request, exc: DisputeNotFoundError
    ) -> JSONResponse:
        """Handle DisputeNotFoundError exceptions."""
        return JSONResponse(
            status_code=404,
            content={
                "detail": str(exc),
                "error_code": "DISPUTE_NOT_FOUND",
            },
        )

    @app.exception_handler(DisputeAlreadyExistsError)
    async def dispute_already_exists_handler(
        request: Request, exc: DisputeAlreadyExistsError
    ) -> JSONResponse:
        """Handle DisputeAlreadyExistsError exceptions."""
        return JSONResponse(
            status_code=409,
            content={
                "detail": str(exc),
                "error_code": "DISPUTE_ALREADY_EXISTS",
            },
        )

    @app.exception_handler(DisputeAlreadyResolvedError)
    async def dispute_already_resolved_handler(
        request: Request, exc: DisputeAlreadyResolvedError
    ) -> JSONResponse:
        """Handle DisputeAlreadyResolvedError exceptions."""
        return JSONResponse(
            status_code=400,
            content={
                "detail": str(exc),
                "error_code": "DISPUTE_ALREADY_RESOLVED",
            },
        )

    @app.exception_handler(UnauthorizedDisputeAccessError)
    async def unauthorized_dispute_access_handler(
        request: Request, exc: UnauthorizedDisputeAccessError
    ) -> JSONResponse:
        """Handle UnauthorizedDisputeAccessError exceptions."""
        return JSONResponse(
            status_code=403,
            content={
                "detail": str(exc),
                "error_code": "UNAUTHORIZED_DISPUTE_ACCESS",
            },
        )

    @app.exception_handler(UnauthorizedArbitratorError)
    async def unauthorized_arbitrator_handler(
        request: Request, exc: UnauthorizedArbitratorError
    ) -> JSONResponse:
        """Handle UnauthorizedArbitratorError exceptions."""
        return JSONResponse(
            status_code=403,
            content={
                "detail": str(exc),
                "error_code": "UNAUTHORIZED_ARBITRATOR",
            },
        )
