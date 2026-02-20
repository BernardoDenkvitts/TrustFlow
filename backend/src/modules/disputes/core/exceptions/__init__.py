"""Dispute exceptions module."""

from src.modules.disputes.core.exceptions.dispute_exceptions import (
    DisputeAlreadyExistsError,
    DisputeAlreadyResolvedError,
    DisputeNotFoundError,
    DisputeNotYetResolvedError,
    UnauthorizedArbitratorError,
    UnauthorizedDisputeAccessError,
)

__all__ = [
    "DisputeAlreadyExistsError",
    "DisputeAlreadyResolvedError",
    "DisputeNotFoundError",
    "DisputeNotYetResolvedError",
    "UnauthorizedArbitratorError",
    "UnauthorizedDisputeAccessError",
]
