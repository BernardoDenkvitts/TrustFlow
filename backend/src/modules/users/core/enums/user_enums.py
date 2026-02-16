"""User module enums."""

from enum import Enum


class OAuthProvider(str, Enum):
    """OAuth providers supported by the system.

    Values:
        GOOGLE: Google OAuth provider.
    """

    GOOGLE = "GOOGLE"
