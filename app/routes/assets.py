from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.config import privacy_mode_enabled
from app.database.session import get_db
from app.schemas.asset import AssetCreate, AssetRead
from app.services.assets import create_asset, list_assets

router = APIRouter(prefix="/assets", tags=["Assets"])


def _ensure_asset_storage_allowed() -> None:
    if privacy_mode_enabled():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Asset storage is disabled in privacy-first mode. Use the private assessment workflow instead.",
        )


@router.post("", response_model=AssetRead, status_code=status.HTTP_201_CREATED)
def create_asset_endpoint(payload: AssetCreate, db: Session = Depends(get_db)) -> AssetRead:
    _ensure_asset_storage_allowed()
    try:
        return create_asset(db, payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("", response_model=list[AssetRead])
def list_assets_endpoint(
    tenant_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[AssetRead]:
    _ensure_asset_storage_allowed()
    return list_assets(db, tenant_id=tenant_id)
