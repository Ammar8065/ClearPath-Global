from datetime import date

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.models.knowledge_source import KnowledgeSource
from app.models.rule import Rule
from app.schemas.rule import RuleCreate


def _check_version_overlap(db: Session, payload: RuleCreate) -> None:
    """Reject a new rule version if it would create an active date overlap.

    Two versions of the same rule_code overlap when their effective date
    ranges intersect and neither is soft-deleted.  The logic mirrors a
    standard interval-overlap test:
        A.start <= B.end  AND  B.start <= A.end
    where a null effective_to means "open-ended / no upper bound".
    """
    new_from: date = payload.effective_from
    new_to: date | None = payload.effective_to

    # Build overlap condition against existing active versions
    # existing.effective_from <= new_to  (or new_to is None → always True)
    if new_to is not None:
        existing_starts_before_new_ends = Rule.effective_from <= new_to
    else:
        existing_starts_before_new_ends = True  # open-ended new range always overlaps

    # new_from <= existing.effective_to  (or existing.effective_to is None → always True)
    new_starts_before_existing_ends = or_(
        Rule.effective_to.is_(None),
        Rule.effective_to >= new_from,
    )

    conflicting = db.scalars(
        select(Rule).where(
            Rule.rule_code == payload.rule_code,
            Rule.is_deleted.is_(False),
            existing_starts_before_new_ends,
            new_starts_before_existing_ends,
        )
    ).first()

    if conflicting is not None:
        raise ValueError(
            f"Rule '{payload.rule_code}' already has an active version "
            f"(v{conflicting.version}) whose effective date range overlaps "
            f"with the requested range. Soft-delete the existing version first."
        )


def create_rule(db: Session, payload: RuleCreate) -> Rule:
    source = db.get(KnowledgeSource, payload.source_id)
    if source is None:
        raise LookupError("Knowledge source not found.")

    _check_version_overlap(db, payload)

    rule = Rule(**payload.model_dump())
    db.add(rule)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("A rule with this rule_code and version already exists.") from exc

    db.refresh(rule)
    return rule


def list_rules(db: Session) -> list[Rule]:
    statement = (
        select(Rule)
        .options(joinedload(Rule.source))
        .order_by(Rule.rule_code, Rule.version.desc(), Rule.id.desc())
    )
    return list(db.scalars(statement).unique())


def get_rule_versions(db: Session, rule_code: str) -> list[Rule]:
    """Return all versions (including deleted) for a given rule_code."""
    statement = (
        select(Rule)
        .where(Rule.rule_code == rule_code)
        .order_by(Rule.version.desc())
    )
    return list(db.scalars(statement))


def soft_delete_rule(db: Session, rule_id: int) -> Rule:
    rule = db.get(Rule, rule_id)
    if rule is None or rule.is_deleted:
        raise LookupError("Rule not found.")

    rule.is_deleted = True
    db.commit()
    db.refresh(rule)
    return rule
