from fastapi import APIRouter, Request

from app.config import auth_enabled, clerk_publishable_key
from app.schemas.auth import AuthStatusResponse
from app.services.auth import verify_request

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.get("/status", response_model=AuthStatusResponse)
def auth_status(request: Request) -> AuthStatusResponse:
    """Open endpoint the frontend boots from.

    Serves the Clerk publishable key (public by design) so the static
    frontend needs no per-environment build, and reports the caller's role
    when a valid session token is attached. Sign-in/out themselves happen in
    the browser against Clerk, not here.
    """
    if not auth_enabled():
        return AuthStatusResponse(
            auth_enabled=False,
            authenticated=True,
            user_id="dev",
            role="admin",
        )

    session = verify_request(request)
    if session is None:
        return AuthStatusResponse(
            auth_enabled=True,
            authenticated=False,
            publishable_key=clerk_publishable_key(),
        )
    return AuthStatusResponse(
        auth_enabled=True,
        authenticated=True,
        user_id=session.user_id,
        role=session.role,
        publishable_key=clerk_publishable_key(),
    )
