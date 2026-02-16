"""Auth domain exceptions."""


class InvalidTokenError(Exception):
    """Raised when JWT token is invalid."""

    def __init__(self, message: str = "Invalid token") -> None:
        self.message = message
        super().__init__(message)


class ExpiredTokenError(Exception):
    """Raised when JWT token is expired."""

    def __init__(self, message: str = "Token expired") -> None:
        self.message = message
        super().__init__(message)


class InvalidGoogleCodeError(Exception):
    """Raised when Google code exchange fails (Invalid Code)."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class SessionAlreadyExistsError(Exception):
    """Raised when trying to create a session that already exists."""

    def __init__(self, message: str = "Session already exists") -> None:
        self.message = message
        super().__init__(message)


class SessionNotFoundError(Exception):
    """Raised when session is not found."""

    def __init__(self, message: str = "Session not found") -> None:
        self.message = message
        super().__init__(message)

