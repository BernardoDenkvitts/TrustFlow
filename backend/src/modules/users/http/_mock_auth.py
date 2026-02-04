"""Mocked authentication.

This module provides temporary authentication mocking until
real Supabase JWT validation is implemented
"""

import uuid

# Mocked user ID for development/testing
# This constant is used across the application for testing purposes
MOCKED_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def get_mock_current_user_id() -> uuid.UUID:
    """Get the mocked current user ID.

    Returns:
        A constant UUID for testing purposes.

    Note:
        This will be replaced with real JWT token validation.
    """
    return MOCKED_USER_ID
