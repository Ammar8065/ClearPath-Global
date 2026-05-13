from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.client import Client
from app.models.tenant import Tenant
from app.schemas.client import ClientCreate


def create_client(db: Session, payload: ClientCreate) -> Client:
    tenant = db.get(Tenant, payload.tenant_id)
    if tenant is None:
        raise LookupError("Tenant not found.")

    client = Client(**payload.model_dump())
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


def list_clients(db: Session, tenant_id: int | None = None) -> list[Client]:
    statement = select(Client).where(Client.is_deleted.is_(False)).order_by(Client.id)

    if tenant_id is not None:
        statement = statement.where(Client.tenant_id == tenant_id)

    return list(db.scalars(statement))


def soft_delete_client(db: Session, client_id: int) -> Client:
    client = db.get(Client, client_id)
    if client is None or client.is_deleted:
        raise LookupError("Client not found.")

    client.is_deleted = True
    db.commit()
    db.refresh(client)
    return client
