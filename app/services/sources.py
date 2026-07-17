from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.knowledge_source import KnowledgeSource
from app.models.rule import Rule
from app.schemas.knowledge_source import KnowledgeSourceCreate


def create_source(db: Session, payload: KnowledgeSourceCreate) -> KnowledgeSource:
    source = KnowledgeSource(**payload.model_dump(mode="json"))
    db.add(source)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("A knowledge source with this URL already exists.") from exc

    db.refresh(source)
    return source


def list_sources(db: Session) -> list[KnowledgeSource]:
    return list(db.scalars(select(KnowledgeSource).order_by(KnowledgeSource.id)))


def delete_source(db: Session, source_id: int) -> KnowledgeSource:
    """Hard-delete a source, refusing while any rule still references it.

    Rules (including soft-deleted ones) keep their source_id for citation
    integrity, so the referencing rules must be reassigned or removed first.
    """
    source = db.get(KnowledgeSource, source_id)
    if source is None:
        raise LookupError(f"Knowledge source {source_id} not found.")

    referencing = db.scalar(select(func.count(Rule.id)).where(Rule.source_id == source_id)) or 0
    if referencing:
        raise ValueError(
            f"Source {source_id} is referenced by {referencing} rule(s). "
            "Delete or reassign those rules first."
        )

    db.delete(source)
    db.commit()
    return source
