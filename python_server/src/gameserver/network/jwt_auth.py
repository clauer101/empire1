"""JWT token creation and verification for REST API authentication.

Provides helper functions to create and verify JWT tokens, and a
FastAPI dependency (``get_current_uid``) to protect endpoints.

Usage::

    from gameserver.network.jwt_auth import create_token, get_current_uid

    # In login endpoint:
    token = create_token(uid)

    # In protected endpoint:
    @app.get("/api/empire/summary")
    async def summary(uid: int = Depends(get_current_uid)):
        ...
"""

from __future__ import annotations

import logging
import os
import time
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

log = logging.getLogger(__name__)

# Secret key — read from env or use a default (fine for dev/local game server)
JWT_SECRET: str = os.environ.get("JWT_SECRET", "e3-game-server-secret-key-change-in-prod")
JWT_ALGORITHM: str = "HS256"
JWT_EXPIRY_SECONDS: int = 86400  # 24 hours

_bearer_scheme = HTTPBearer(auto_error=False)


def create_token(uid: int) -> str:
    """Create a signed JWT token for a given user ID.

    Args:
        uid: The authenticated user's ID.

    Returns:
        Encoded JWT string.
    """
    payload = {
        "uid": uid,
        "iat": int(time.time()),
        "exp": int(time.time()) + JWT_EXPIRY_SECONDS,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> int:
    """Verify a JWT token and return the user ID.

    Args:
        token: Encoded JWT string.

    Returns:
        The user's UID from the token payload.

    Raises:
        ValueError: If the token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        uid = payload.get("uid")
        if uid is None:
            raise ValueError("Token missing uid claim")
        return int(uid)
    except jwt.ExpiredSignatureError:
        raise ValueError("Token expired")
    except jwt.InvalidTokenError as e:
        raise ValueError(f"Invalid token: {e}")


async def get_current_uid(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> int:
    """FastAPI dependency that extracts the UID from the Authorization header.

    Usage::

        @app.get("/api/protected")
        async def protected(uid: int = Depends(get_current_uid)):
            ...

    Raises:
        HTTPException(401): If token is missing, invalid, or expired.
    """
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authorization header required")
    try:
        return verify_token(credentials.credentials)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
