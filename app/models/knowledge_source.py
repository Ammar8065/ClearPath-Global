from datetime import datetime
import enum

from sqlalchemy import DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models._timestamps import utcnow


class SourceType(str, enum.Enum):
    government_guidance = "government_guidance"
    legislation = "legislation"
    guidance = "guidance"
    treaty = "treaty"
    commentary = "commentary"


class KnowledgeSource(Base):
    __tablename__ = "knowledge_sources"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    jurisdiction: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    source_type: Mapped[SourceType] = mapped_column(Enum(SourceType), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    rules: Mapped[list["Rule"]] = relationship(back_populates="source")
