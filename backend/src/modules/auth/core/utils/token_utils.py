"""Token utility functions."""

import hashlib
import secrets


def generate_refresh_token() -> str:
    """Generate a secure random refresh token.

    Returns:
        A URL-safe random string.
    """
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    """Hash a token using SHA-256.

    Args:
        token: The token string to hash.

    Returns:
        The hexadecimal representation of the hash.
    """
    return hashlib.sha256(token.encode()).hexdigest()
