from pydantic import BaseModel


class AuthStatusResponse(BaseModel):
    auth_enabled: bool
    authenticated: bool
    user_id: str | None = None
    role: str | None = None
    publishable_key: str | None = None
