import argparse
from datetime import date  # noqa: F401  (kept for backwards-compat imports)

from sqlalchemy import delete, select

from app.database.base import Base
from app.database.init_db import init_db
from app.database.session import SessionLocal, engine
from app.models.knowledge_source import KnowledgeSource
from app.models.rule import Rule

from seed_sources import SOURCE_FIXTURES
from seed_rules import (
    RULE_FIXTURES,
    all_conditions,     # noqa: F401  (re-exported helper)
    any_conditions,     # noqa: F401  (re-exported helper)
    simple_condition,   # noqa: F401  (re-exported helper)
)


# ── Upsert logic ──────────────────────────────────────────────────────────────
def upsert_sources() -> dict[str, int]:
    """Insert or update all knowledge sources. Returns {source_key: source_id}."""
    with SessionLocal() as db:
        source_ids: dict[str, int] = {}

        for payload in SOURCE_FIXTURES:
            key = payload["key"]
            data = {k: v for k, v in payload.items() if k != "key"}

            source = db.scalar(
                select(KnowledgeSource).where(KnowledgeSource.url == data["url"])
            )

            if source is None:
                source = KnowledgeSource(**data)
                db.add(source)
                db.flush()
            else:
                source.jurisdiction = data["jurisdiction"]
                source.title = data["title"]
                source.url = data["url"]
                source.source_type = data["source_type"]

            source_ids[key] = source.id

        db.commit()
        return source_ids


def upsert_rules(source_ids: dict[str, int]) -> None:
    """Insert or update all rules, mapping each rule's source_key to its source_id."""
    with SessionLocal() as db:
        for payload in RULE_FIXTURES:
            source_key = payload["source_key"]
            source_id = source_ids[source_key]

            rule_values = {k: v for k, v in payload.items() if k != "source_key"}

            rule = db.scalar(
                select(Rule).where(
                    Rule.rule_code == payload["rule_code"],
                    Rule.version == payload["version"],
                )
            )

            if rule is None:
                db.add(Rule(source_id=source_id, **rule_values))
                continue

            rule.jurisdiction = rule_values["jurisdiction"]
            rule.category = rule_values["category"]
            rule.condition_expression = rule_values["condition_expression"]
            rule.description = rule_values["description"]
            rule.risk_level = rule_values["risk_level"]
            rule.confidence_level = rule_values["confidence_level"]
            rule.section_reference = rule_values.get("section_reference")
            rule.source_id = source_id

        db.commit()


def reset_seed_data() -> None:
    with SessionLocal() as db:
        db.execute(delete(Rule))
        db.execute(delete(KnowledgeSource))
        db.commit()


def recreate_schema() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def seed(reset: bool = False, recreate: bool = False) -> None:
    if recreate:
        recreate_schema()
    else:
        init_db()

    if reset:
        reset_seed_data()

    source_ids = upsert_sources()
    upsert_rules(source_ids)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the ClearPath Global knowledge base.")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing rules and sources before reseeding.",
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Drop and recreate all tables before seeding. Use after schema changes.",
    )
    args = parser.parse_args()
    seed(reset=args.reset, recreate=args.recreate)
