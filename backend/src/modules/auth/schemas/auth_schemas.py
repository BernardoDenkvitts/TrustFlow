"""Auth module schemas."""

from pydantic import BaseModel


class GoogleLoginData(BaseModel):
    """Data received from Google Login (code)."""

    code: str



class Token(BaseModel):
    """JWT Token response."""

    access_token: str
    expires_in: int
