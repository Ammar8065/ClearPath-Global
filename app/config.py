import os
from pathlib import Path

from dotenv import load_dotenv

# Load the project-root .env once at import time so ANTHROPIC_API_KEY etc.
# work without a manual shell export. Real environment variables always win
# (load_dotenv never overrides existing values).
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

DEFAULT_AI_MODEL = "claude-sonnet-4-6"


def privacy_mode_enabled() -> bool:
    value = os.getenv("PRIVACY_MODE", "1").strip().lower()
    return value not in {"0", "false", "no", "off"}


def ai_enabled() -> bool:
    return bool(os.getenv("ANTHROPIC_API_KEY", "").strip())


def ai_model() -> str:
    return os.getenv("AI_MODEL", "").strip() or DEFAULT_AI_MODEL


def cors_allow_origins() -> list[str]:
    """Comma-separated list of allowed CORS origins.

    Empty (the default) means no cross-origin access is granted — the SPA is
    served same-origin by FastAPI and needs none. Set this only when a
    separately hosted frontend must call the API.
    """
    raw = os.getenv("CORS_ALLOW_ORIGINS", "").strip()
    return [origin.strip() for origin in raw.split(",") if origin.strip()]
