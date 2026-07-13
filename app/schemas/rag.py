from typing import Literal

from pydantic import BaseModel, Field, field_validator


class RAGStatusResponse(BaseModel):
    vector_db_available: bool
    ai_enabled: bool
    rule_count: int
    source_chunk_count: int


class RAGQueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)

    @field_validator("question")
    @classmethod
    def question_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("question must not be blank.")
        return v


class RAGCitation(BaseModel):
    type: Literal["rule", "source"]
    key: str
    title: str
    url: str
    jurisdiction: str


class RAGQueryResponse(BaseModel):
    answer: str
    caveat: str | None
    citations: list[RAGCitation]
    model: str
