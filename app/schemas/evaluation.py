from typing import Any

from pydantic import BaseModel, field_validator


class EvaluationRequest(BaseModel):
    assessment_label: str | None = None
    client_data: dict[str, Any]
    # Optional list of jurisdiction codes (e.g. ["AU", "SG"]). When provided,
    # only rules from those jurisdictions are evaluated. Generic worksheet
    # fields such as days_in_country describe "the relevant country", so
    # scoping prevents another jurisdiction's rules from reading them as its
    # own day counts. None/empty means evaluate every active rule.
    jurisdiction_scope: list[str] | None = None
    # Honoured by /evaluate/private/report only — adds an AI executive summary section.
    include_ai_summary: bool = False

    @field_validator("client_data")
    @classmethod
    def limit_payload_size(cls, v: dict[str, Any]) -> dict[str, Any]:
        if len(v) > 200:
            raise ValueError("client_data exceeds maximum of 200 fields.")
        return v

    @field_validator("jurisdiction_scope")
    @classmethod
    def normalise_scope(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return None
        cleaned = [code.strip().upper() for code in v if code and code.strip()]
        return cleaned or None


class TriggeredRule(BaseModel):
    rule_code: str
    description: str
    risk_level: str
    confidence_level: str
    jurisdiction: str
    category: str
    rule_score: float
    source_id: int
    source_title: str
    source_url: str
    section_reference: str | None
    review_status: str = "verified_current"


class CategoryScore(BaseModel):
    score: float
    triggered_count: int
    max_risk: str


class JurisdictionScore(BaseModel):
    score: float
    triggered_count: int


class Citation(BaseModel):
    rule_code: str
    source_title: str
    source_url: str
    jurisdiction: str
    section_reference: str | None


class RuleMatchDetail(BaseModel):
    rule_code: str
    description: str
    risk_level: str
    jurisdiction: str
    category: str
    version: int
    matched: bool
    reason: str
    review_status: str = "verified_current"


class IncompleteRule(BaseModel):
    rule_code: str
    description: str
    risk_level: str
    jurisdiction: str
    category: str
    missing_fields: list[str]
    reason: str


class RuleInteractionRead(BaseModel):
    primary_rule_code: str
    related_rule_code: str
    interaction_type: str
    note: str


class EvaluationResponse(BaseModel):
    client_id: int | None
    assessment_label: str | None = None
    overall_risk: str
    score: float
    triggered_rules: list[str]
    summary: list[TriggeredRule]
    category_breakdown: dict[str, CategoryScore]
    jurisdiction_breakdown: dict[str, JurisdictionScore]
    citations: list[Citation]
    incomplete_rules: list[IncompleteRule] = []
    rule_interactions: list[RuleInteractionRead] = []
    warnings: list[str] = []


class PreviewResponse(BaseModel):
    client_id: int | None
    assessment_label: str | None = None
    total_active_rules: int
    matched_count: int
    rules: list[RuleMatchDetail]


class RuleVersionRead(BaseModel):
    id: int
    rule_code: str
    version: int
    jurisdiction: str
    category: str
    risk_level: str
    confidence_level: str
    effective_from: str
    effective_to: str | None
    is_deleted: bool
    description: str
