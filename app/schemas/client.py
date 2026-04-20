from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ClientBase(BaseModel):
    citizenships: list[str] = Field(..., min_length=1)
    current_residency: str
    tenant_id: int


class ClientCreate(ClientBase):
    pass


class ClientRead(ClientBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_deleted: bool
    created_at: datetime
