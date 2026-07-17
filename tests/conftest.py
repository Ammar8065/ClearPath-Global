from pathlib import Path
import sys

import pytest


ROOT_DIR = Path(__file__).resolve().parent.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


@pytest.fixture(autouse=True)
def _auth_disabled(monkeypatch):
    """Run the suite in open mode regardless of the developer's local .env.

    app.config loads .env at import time, so a configured CLERK_SECRET_KEY
    would otherwise flip every unauthenticated request in these tests to 401.
    Auth-specific tests opt back in by setting the vars explicitly.
    """
    for var in ("CLERK_SECRET_KEY", "CLERK_PUBLISHABLE_KEY", "ADMIN_USER_ID"):
        monkeypatch.delenv(var, raising=False)
