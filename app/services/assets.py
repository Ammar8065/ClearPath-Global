from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.asset import Asset
from app.models.client import Client
from app.schemas.asset import AssetCreate


def _get_active_client(db: Session, client_id: int) -> Client:
    client = db.get(Client, client_id)
    if client is None or client.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found.",
        )
    return client


def create_asset(db: Session, payload: AssetCreate) -> Asset:
    _get_active_client(db, payload.client_id)

    asset = Asset(**payload.model_dump())
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


def list_assets(db: Session, tenant_id: int | None = None) -> list[Asset]:
    statement = (
        select(Asset)
        .join(Client)
        .where(Client.is_deleted.is_(False))
        .order_by(Asset.id)
    )

    if tenant_id is not None:
        statement = statement.where(Client.tenant_id == tenant_id)

    return list(db.scalars(statement))
