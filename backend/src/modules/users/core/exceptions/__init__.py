"""Users module domain exceptions."""

from src.modules.users.core.exceptions.user_exceptions import (
    InvalidWalletAddressError,
    UserAlreadyExistsError,
    UserNotFoundError,
)

__all__ = [
    "UserAlreadyExistsError",
    "UserNotFoundError",
    "InvalidWalletAddressError",
]
