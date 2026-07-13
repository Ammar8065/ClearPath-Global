from fastapi import APIRouter, HTTPException, status

from app.config import ai_enabled, ai_model
from app.schemas.ai import (
    AIStatusResponse,
    ExtractionRequest,
    ExtractionResponse,
    SummariseRequest,
    SummariseResponse,
)
from app.services.ai.client import call_ai
from app.services.ai.extraction import extract_client_data
from app.services.ai.summarisation import summarise_evaluation

router = APIRouter(prefix="/ai", tags=["AI Assist"])


def _ensure_ai_enabled() -> None:
    if not ai_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI assist is not configured. Set ANTHROPIC_API_KEY to enable extraction and summarisation.",
        )


@router.get("/status", response_model=AIStatusResponse)
def ai_status_endpoint() -> AIStatusResponse:
    return AIStatusResponse(enabled=ai_enabled(), model=ai_model())


@router.post("/extract", response_model=ExtractionResponse)
def extract_endpoint(payload: ExtractionRequest) -> ExtractionResponse:
    _ensure_ai_enabled()
    return call_ai(extract_client_data, payload.notes)


@router.post("/summarise", response_model=SummariseResponse)
def summarise_endpoint(payload: SummariseRequest) -> SummariseResponse:
    _ensure_ai_enabled()
    return call_ai(summarise_evaluation, payload.evaluation.model_dump())
