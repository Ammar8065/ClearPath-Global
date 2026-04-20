from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.knowledge_source import KnowledgeSource
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
