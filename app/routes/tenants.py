from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.tenant import TenantCreate, TenantRead
from app.services.tenants import create_tenant, delete_tenant, list_tenants

router = APIRouter(prefix="/tenants", tags=["Tenants"])


@router.post("", response_model=TenantRead, status_code=status.HTTP_201_CREATED)
def create_tenant_endpoint(payload: TenantCreate, db: Session = Depends(get_db)) -> TenantRead:
    try:
        return create_tenant(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("", response_model=list[TenantRead])
def list_tenants_endpoint(db: Session = Depends(get_db)) -> list[TenantRead]:
    return list_tenants(db)


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tenant_endpoint(tenant_id: int, db: Session = Depends(get_db)) -> None:
    try:
        delete_tenant(db, tenant_id)
    except KeyError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
