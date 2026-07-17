from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.knowledge_source import KnowledgeSourceCreate, KnowledgeSourceRead
from app.services.auth import require_admin
from app.services.sources import create_source, delete_source, list_sources

router = APIRouter(prefix="/sources", tags=["Knowledge Sources"])


@router.post(
    "",
    response_model=KnowledgeSourceRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
def create_source_endpoint(
    payload: KnowledgeSourceCreate,
    db: Session = Depends(get_db),
) -> KnowledgeSourceRead:
    try:
        return create_source(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("", response_model=list[KnowledgeSourceRead])
def list_sources_endpoint(db: Session = Depends(get_db)) -> list[KnowledgeSourceRead]:
    return list_sources(db)


@router.delete(
    "/{source_id}",
    response_model=KnowledgeSourceRead,
    dependencies=[Depends(require_admin)],
)
def delete_source_endpoint(source_id: int, db: Session = Depends(get_db)) -> KnowledgeSourceRead:
    try:
        return delete_source(db, source_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
