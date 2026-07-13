from datetime import date, datetime
import enum

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.database.base import Base
from app.models._timestamps import utcnow


class RuleCategory(str, enum.Enum):
    residency = "residency"
    tax = "tax"
    cross_border = "cross_border"
    structure = "structure"


class RiskLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class ConfidenceLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class ReviewStatus(str, enum.Enum):
    verified_current = "verified_current"
    needs_update = "needs_update"
    unsupported_or_wrong_source = "unsupported_or_wrong_source"


class Rule(Base):
    __tablename__ = "rules"
    __table_args__ = (UniqueConstraint("rule_code", "version", name="uq_rule_code_version"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    rule_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    jurisdiction: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    category: Mapped[RuleCategory] = mapped_column(Enum(RuleCategory), nullable=False, index=True)
    condition_expression: Mapped[dict] = mapped_column(JSON, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    risk_level: Mapped[RiskLevel] = mapped_column(Enum(RiskLevel), nullable=False, index=True)
    confidence_level: Mapped[ConfidenceLevel] = mapped_column(
        Enum(ConfidenceLevel),
        nullable=False,
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False, index=True)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("knowledge_sources.id"), nullable=False, index=True)
    section_reference: Mapped[str | None] = mapped_column(String(200), nullable=True)
    # Conservative default: a rule nobody has explicitly verified is
    # needs_update. Matches the API schema default in app/schemas/rule.py;
    # the seeder marks its fact-checked fixtures verified_current explicitly.
    review_status: Mapped[ReviewStatus] = mapped_column(
        Enum(ReviewStatus),
        nullable=False,
        default=ReviewStatus.needs_update,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    source: Mapped["KnowledgeSource"] = relationship(back_populates="rules")
