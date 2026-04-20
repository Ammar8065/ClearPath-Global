from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.database.base import Base
from app.models._timestamps import utcnow


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    citizenships: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    current_residency: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    tenant: Mapped["Tenant"] = relationship(back_populates="clients")
    residency_history: Mapped[list["ResidencyHistory"]] = relationship(
        back_populates="client",
        cascade="all, delete-orphan",
    )
    assets: Mapped[list["Asset"]] = relationship(
        back_populates="client",
        cascade="all, delete-orphan",
    )
