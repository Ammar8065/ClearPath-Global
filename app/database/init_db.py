import os

from sqlalchemy import inspect

from app.database.base import Base
from app.database.session import engine
from app.models import asset  # noqa: F401
from app.models import client  # noqa: F401
from app.models import knowledge_source  # noqa: F401
from app.models import residency_history  # noqa: F401
from app.models import rule  # noqa: F401
from app.models import tenant  # noqa: F401

_AUTO_CREATE_ENV_VARS = {"1", "true", "yes", "on"}


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def should_auto_create_schema() -> bool:
    return os.getenv("AUTO_CREATE_SCHEMA", "").strip().lower() in _AUTO_CREATE_ENV_VARS


def ensure_schema_ready() -> None:
    required_tables = {table.name for table in Base.metadata.sorted_tables}
    existing_tables = set(inspect(engine).get_table_names())
    missing_tables = sorted(required_tables - existing_tables)

    if not missing_tables:
        return

    raise RuntimeError(
        "Database schema is not initialized. "
        "Run `alembic upgrade head` before starting the app. "
        f"Missing tables: {', '.join(missing_tables)}. "
        "Set AUTO_CREATE_SCHEMA=1 only if you explicitly want startup to call create_all()."
    )
