"""Exception handlers for agreements module.

Converts domain exceptions to appropriate HTTP responses.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.modules.agreements.core.exceptions import (
    AgreementNotFoundError,
    InvalidArbitrationPolicyError,
    InvalidStateTransitionError,
    SelfDealError,
    UnauthorizedAgreementAccessError,
)


def register_agreements_exception_handlers(app: FastAPI) -> None:
    """Register exception handlers for the agreements module.

    Args:
        app: The FastAPI application instance.
    """

    @app.exception_handler(AgreementNotFoundError)
    async def agreement_not_found_handler(
        request: Request, exc: AgreementNotFoundError
    ) -> JSONResponse:
        """Handle AgreementNotFoundError exceptions."""
        return JSONResponse(
            status_code=404,
            content={
                "detail": str(exc),
                "error_code": "AGREEMENT_NOT_FOUND",
            },
        )

    @app.exception_handler(InvalidStateTransitionError)
    async def invalid_state_transition_handler(
        request: Request, exc: InvalidStateTransitionError
    ) -> JSONResponse:
        """Handle InvalidStateTransitionError exceptions."""
        return JSONResponse(
            status_code=400,
            content={
                "detail": str(exc),
                "error_code": "INVALID_STATE_TRANSITION",
                "current_status": exc.current_status.value,
                "target_status": exc.target_status.value,
            },
        )

    @app.exception_handler(SelfDealError)
    async def self_deal_handler(
        request: Request, exc: SelfDealError
    ) -> JSONResponse:
        """Handle SelfDealError exceptions."""
        return JSONResponse(
            status_code=400,
            content={
                "detail": str(exc),
                "error_code": "SELF_DEAL",
            },
        )

    @app.exception_handler(InvalidArbitrationPolicyError)
    async def invalid_arbitration_policy_handler(
        request: Request, exc: InvalidArbitrationPolicyError
    ) -> JSONResponse:
        """Handle InvalidArbitrationPolicyError exceptions."""
        return JSONResponse(
            status_code=400,
            content={
                "detail": str(exc),
                "error_code": "INVALID_ARBITRATION_POLICY",
                "policy": exc.policy.value,
            },
        )

    @app.exception_handler(UnauthorizedAgreementAccessError)
    async def unauthorized_agreement_access_handler(
        request: Request, exc: UnauthorizedAgreementAccessError
    ) -> JSONResponse:
        """Handle UnauthorizedAgreementAccessError exceptions."""
        return JSONResponse(
            status_code=403,
            content={
                "detail": str(exc),
                "error_code": "UNAUTHORIZED_AGREEMENT_ACCESS",
            },
        )
