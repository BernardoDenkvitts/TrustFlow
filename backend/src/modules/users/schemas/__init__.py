"""Users module schemas (DTOs for request/response)."""

from src.modules.users.schemas.user_schemas import (
    UpdateWalletRequest,
    UserResponse,
)

__all__ = [
    "UserResponse",
    "UpdateWalletRequest",
]
