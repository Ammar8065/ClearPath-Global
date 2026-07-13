"""Curated relationships between rules that can both legitimately trigger
together but where one materially changes the other's real-world effect.

Two types, deliberately narrow so the set stays defensible against the
legislation actually cited by each rule (see seed_rule_interactions.py):

    relief     the related rule describes an election or claim that, if made,
               reduces or eliminates the primary rule's exposure (the client
               has to act — e.g. electing UAE Small Business Relief).
    exception  the related rule's own facts are an automatic carve-out from
               the primary rule — no election needed, e.g. Hong Kong's
               60-day visitor exemption.

Rules are referenced by rule_code (not a FK to a specific Rule row/version) —
an interaction is a conceptual relationship between two rule *codes* that
should hold across versions, the same way citations key off rule_code
elsewhere in the engine.
"""
from datetime import datetime
import enum

from sqlalchemy import DateTime, Enum, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models._timestamps import utcnow


class InteractionType(str, enum.Enum):
    relief = "relief"
    exception = "exception"


class RuleInteraction(Base):
    __tablename__ = "rule_interactions"
    __table_args__ = (
        UniqueConstraint("primary_rule_code", "related_rule_code", name="uq_rule_interaction_pair"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    primary_rule_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    related_rule_code: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    interaction_type: Mapped[InteractionType] = mapped_column(Enum(InteractionType), nullable=False, index=True)
    note: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
