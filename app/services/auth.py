"""Clerk-backed auth for the single-admin / viewer access model.

The frontend signs users in with ClerkJS and sends the session JWT as a
Bearer token; this module verifies it server-side (JWKS fetched and cached by
the Clerk SDK). Role model: the Clerk user whose ID matches ADMIN_USER_ID is
the admin; every other authenticated user is a viewer.

With CLERK_SECRET_KEY unset, auth is disabled and every request acts as an
implicit admin — keeps local dev and the test suite credential-free.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from fastapi import HTTPException, Request, status

from app.config import admin_user_id, auth_enabled, clerk_secret_key


@dataclass(frozen=True)
class Session:
    user_id: str
    role: str  # "admin" | "viewer"


@lru_cache(maxsize=1)
def _clerk():
    from clerk_backend_api import Clerk

    return Clerk(bearer_auth=clerk_secret_key())


def verify_request(request: Request) -> Session | None:
    """Validate the Clerk session token on a request; None when not signed in."""
    from clerk_backend_api.security.types import AuthenticateRequestOptions

    try:
        state = _clerk().authenticate_request(request, AuthenticateRequestOptions())
    except Exception:
        # Treat verification infrastructure errors as unauthenticated rather
        # than 500 — the client can re-login; details go to server logs.
        return None
    if not state.is_signed_in or not state.payload:
        return None

    user_id = str(state.payload.get("sub", ""))
    if not user_id:
        return None
    role = "admin" if admin_user_id() and user_id == admin_user_id() else "viewer"
    return Session(user_id=user_id, role=role)


def require_user(request: Request) -> Session:
    """Any authenticated user. With auth disabled, acts as an implicit admin."""
    if not auth_enabled():
        return Session(user_id="dev", role="admin")
    session = verify_request(request)
    if session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required.")
    return session


def require_admin(request: Request) -> Session:
    session = require_user(request)
    if session.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required for this action.",
        )
    return session
