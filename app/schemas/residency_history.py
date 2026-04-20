from datetime import date

from pydantic import BaseModel, ConfigDict


class ResidencyHistoryBase(BaseModel):
    client_id: int
    country: str
    start_date: date
    end_date: date | None = None


class ResidencyHistoryCreate(ResidencyHistoryBase):
    pass


class ResidencyHistoryRead(ResidencyHistoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
