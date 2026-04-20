from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.tenant import Tenant
from app.schemas.tenant import TenantCreate


def create_tenant(db: Session, payload: TenantCreate) -> Tenant:
    tenant = Tenant(**payload.model_dump())
    db.add(tenant)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("A tenant with this name already exists.") from exc

    db.refresh(tenant)
    return tenant


def list_tenants(db: Session) -> list[Tenant]:
    return list(db.scalars(select(Tenant).order_by(Tenant.name)))


def delete_tenant(db: Session, tenant_id: int) -> None:
    tenant = db.get(Tenant, tenant_id)
    if tenant is None:
        raise KeyError(f"Tenant {tenant_id} not found.")
    db.delete(tenant)
    db.commit()
