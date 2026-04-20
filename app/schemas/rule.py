from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator

from app.models.rule import ConfidenceLevel, RiskLevel, RuleCategory
from app.schemas.knowledge_source import KnowledgeSourceRead

# Operators supported by app/engine/conditions.py
VALID_OPERATORS: set[str] = {
    ">=", "<=", "==", "!=", ">", "<",
    "in", "not_in",
    "contains", "starts_with",
    "is_empty", "not_empty",
}


def _validate_condition_node(node: Any, path: str = "condition_expression") -> None:
    """Recursively validate a condition tree structure.

    Valid shapes:
      - Leaf:  {"field": str, "operator": str, "value": ...}
      - Group: {"all": [nodes...]} or {"any": [nodes...]}

    Raises ValueError with a human-readable path on failure.
    """
    if not isinstance(node, dict):
        raise ValueError(f"{path}: must be an object, got {type(node).__name__}.")

    if not node:
        raise ValueError(f"{path}: empty condition object.")

    # --- group node ---
    if "all" in node or "any" in node:
        group_key = "all" if "all" in node else "any"
        items = node[group_key]
        if not isinstance(items, list):
            raise ValueError(f"{path}.{group_key}: must be a list.")
        if not items:
            raise ValueError(f"{path}.{group_key}: must contain at least one condition.")
        for i, child in enumerate(items):
            _validate_condition_node(child, path=f"{path}.{group_key}[{i}]")
        return

    # --- leaf node ---
    if "field" not in node:
        raise ValueError(f"{path}: missing required key 'field'.")
    if "operator" not in node:
        raise ValueError(f"{path}: missing required key 'operator'.")

    if not isinstance(node["field"], str) or not node["field"].strip():
        raise ValueError(f"{path}.field: must be a non-empty string.")

    op = node["operator"]
    if op not in VALID_OPERATORS:
        raise ValueError(
            f"{path}.operator: unsupported operator {op!r}. "
            f"Valid: {', '.join(sorted(VALID_OPERATORS))}."
        )

    # is_empty / not_empty don't need a value key
    if op not in ("is_empty", "not_empty") and "value" not in node:
        raise ValueError(f"{path}: operator {op!r} requires a 'value' key.")


class RuleBase(BaseModel):
    rule_code: str
    jurisdiction: str
    category: RuleCategory
    condition_expression: dict[str, Any]
    description: str
    risk_level: RiskLevel
    confidence_level: ConfidenceLevel
    source_id: int
    section_reference: str | None = None
    version: int = 1
    effective_from: date
    effective_to: date | None = None


class RuleCreate(RuleBase):
    @model_validator(mode="after")
    def validate_condition_and_dates(self) -> "RuleCreate":
        # Structural validation of the condition tree
        _validate_condition_node(self.condition_expression)

        # Date range sanity
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise ValueError(
                f"effective_to ({self.effective_to}) must not be before "
                f"effective_from ({self.effective_from})."
            )
        return self


class RuleRead(RuleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_deleted: bool
    created_at: datetime


class RuleWithSourceRead(RuleRead):
    source: KnowledgeSourceRead
