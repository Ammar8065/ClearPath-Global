from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.config import privacy_mode_enabled
from app.database.session import get_db
from app.schemas.client import ClientCreate, ClientRead
from app.services.clients import create_client, list_clients, soft_delete_client

router = APIRouter(prefix="/clients", tags=["Clients"])


def _ensure_client_storage_allowed() -> None:
    if privacy_mode_enabled():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Client storage is disabled in privacy-first mode. Use the private assessment workflow instead.",
        )


@router.post("", response_model=ClientRead, status_code=status.HTTP_201_CREATED)
def create_client_endpoint(payload: ClientCreate, db: Session = Depends(get_db)) -> ClientRead:
    _ensure_client_storage_allowed()
    return create_client(db, payload)


@router.get("", response_model=list[ClientRead])
def list_clients_endpoint(
    tenant_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[ClientRead]:
    _ensure_client_storage_allowed()
    return list_clients(db, tenant_id=tenant_id)


@router.delete("/{client_id}", response_model=ClientRead)
def soft_delete_client_endpoint(client_id: int, db: Session = Depends(get_db)) -> ClientRead:
    _ensure_client_storage_allowed()
    return soft_delete_client(db, client_id)
