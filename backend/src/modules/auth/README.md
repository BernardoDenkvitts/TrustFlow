# Auth Module

This module handles authentication and session management for TrustFlow.

## Overview

TrustFlow uses a secure, cookie-based authentication system with **short-lived JWT access tokens** and **rotating refresh tokens**. Currently, **Google OAuth** is the only supported login method.

## Authentication Flow

1.  **Initiate Login**: User requests Google OAuth URL via `GET /auth/google`.
2.  **Google Login**: User authenticates with Google.
3.  **Callback**: Google redirects to the application, which calls `GET /auth/callback/google`.
    *   Server exchanges code for Google ID token.
    *   Verifies ID token.
    *   Creates or retrieves the user.
    *   Creates a new **Session** (stored in DB).
    *   Sets a secure, HTTP-only `refresh_token` cookie.
4.  **Get Access Token**: Frontend calls `GET /auth/session` to retrieve the initial JWT access token.
5.  **Token Refresh**: When the access token expires, frontend calls `POST /auth/refresh` to rotate the refresh token and get a new access token.

## Endpoints

| Method | Path | Description |
| :--- | :--- | :--- |
| GET | `/auth/google` | Get Google OAuth redirect URL |
| GET | `/auth/callback/google` | Handle OAuth callback, create session, set cookie |
| GET | `/auth/session` | Get access token using valid refresh cookie |
| POST | `/auth/refresh` | Rotate refresh token and get new access token |
| POST | `/auth/logout` | Revoke current session and clear cookie |
| POST | `/auth/logout-all` | Revoke all sessions for the current user |

## Database Models

### Session
Tracks active refresh tokens.
*   `refresh_token_hash`: Hashed version of the refresh token (security best practice).
*   `user_id`: Link to the user.
*   `expires_at`: When the session expires (default 30 days).
*   `revoked_at`: Timestamp if session was explicitly revoked.
*   `last_used_at`: Timestamp of last usage (rotation).

## Security Features

*   **HttpOnly Cookies**: Refresh tokens are inaccessible to JavaScript, preventing XSS attacks.
*   **Token Rotation**: Refresh tokens are rotated on every use, detecting token theft.
*   **Token Hashing**: Refresh tokens are hashed in the database, protecting against database leaks.

## Example Usage

```bash
# 1) Start Google Login (BROWSER)
# Open this URL in your browser:
# http://localhost:8000/api/auth/google


# 2. After login you will be redirect to http://localhost:3000/auth/success
# Copy the refresh_token from the browser cookies


# 3. Get Session (access token)
curl -i http://localhost:8000/api/auth/session \
  -b "refresh_token=PASTE_HERE"

# 4. Refresh Session
curl -X POST http://localhost:8000/api/auth/refresh \
  -b "refresh_token=PASTE_HERE" \
  -c cookie_jar.txt
```
