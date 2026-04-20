import os


def privacy_mode_enabled() -> bool:
    value = os.getenv("PRIVACY_MODE", "1").strip().lower()
    return value not in {"0", "false", "no", "off"}
