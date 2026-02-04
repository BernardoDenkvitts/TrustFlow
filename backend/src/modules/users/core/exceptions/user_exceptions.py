"""User domain exceptions."""


class UserNotFoundError(Exception):
    """Raised when a user is not found."""

    def __init__(self, identifier: str) -> None:
        self.identifier = identifier
        super().__init__(f"User not found: {identifier}")


class UserAlreadyExistsError(Exception):
    """Raised when attempting to create a user that already exists."""

    def __init__(self, field: str, value: str) -> None:
        self.field = field
        self.value = value
        super().__init__(f"User with {field}='{value}' already exists")


class InvalidWalletAddressError(Exception):
    """Raised when a wallet address has an invalid format."""

    def __init__(self, wallet_address: str) -> None:
        self.wallet_address = wallet_address
        super().__init__(
            f"Invalid wallet address format: {wallet_address}. "
            "Expected format: 0x followed by 40 lowercase hex characters"
        )
