import enum

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class AssetType(str, enum.Enum):
    property = "property"
    company = "company"
    cash = "cash"
    investment = "investment"


class OwnershipStructure(str, enum.Enum):
    individual = "individual"
    trust = "trust"
    company = "company"


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False, index=True)
    type: Mapped[AssetType] = mapped_column(Enum(AssetType), nullable=False, index=True)
    location: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    ownership_structure: Mapped[OwnershipStructure] = mapped_column(
        Enum(OwnershipStructure),
        nullable=False,
        index=True,
    )

    client: Mapped["Client"] = relationship(back_populates="assets")
