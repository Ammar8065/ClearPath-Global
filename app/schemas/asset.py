from pydantic import BaseModel, ConfigDict

from app.models.asset import AssetType, OwnershipStructure


class AssetBase(BaseModel):
    client_id: int
    type: AssetType
    location: str
    ownership_structure: OwnershipStructure


class AssetCreate(AssetBase):
    pass


class AssetRead(AssetBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
