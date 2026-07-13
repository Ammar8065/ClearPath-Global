from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.schemas.evaluation import EvaluationResponse


class AIStatusResponse(BaseModel):
    enabled: bool
    model: str


class ExtractionRequest(BaseModel):
    notes: str = Field(min_length=1, max_length=50_000)

    @field_validator("notes")
    @classmethod
    def notes_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("notes must not be blank.")
        return v


class ExtractedFactRead(BaseModel):
    field: str
    label: str
    value: bool | float | str
    evidence: str


class ExtractionResponse(BaseModel):
    client_data: dict[str, Any]
    facts: list[ExtractedFactRead]
    unmapped_notes: list[str]
    warnings: list[str]
    model: str


class SummariseRequest(BaseModel):
    evaluation: EvaluationResponse


class RuleExplanationRead(BaseModel):
    rule_code: str
    explanation: str


class AISummaryRead(BaseModel):
    headline: str
    overview: str
    key_risks: list[str]
    recommended_actions: list[str]
    rule_explanations: list[RuleExplanationRead]


class SummariseResponse(BaseModel):
    summary: AISummaryRead
    model: str
