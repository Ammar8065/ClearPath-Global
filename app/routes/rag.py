from fastapi import APIRouter, HTTPException, status

from app.config import ai_enabled
from app.schemas.rag import RAGQueryRequest, RAGQueryResponse, RAGStatusResponse
from app.services.ai.client import call_ai
from app.services.rag.answer import answer_question
from app.services.rag.retrieval import collection_counts, vector_db_available

router = APIRouter(prefix="/rag", tags=["RAG"])


@router.get("/status", response_model=RAGStatusResponse)
def rag_status_endpoint() -> RAGStatusResponse:
    available = vector_db_available()
    rule_count, chunk_count = collection_counts() if available else (0, 0)
    return RAGStatusResponse(
        vector_db_available=available,
        ai_enabled=ai_enabled(),
        rule_count=rule_count,
        source_chunk_count=chunk_count,
    )


@router.post("/query", response_model=RAGQueryResponse)
def rag_query_endpoint(payload: RAGQueryRequest) -> RAGQueryResponse:
    if not vector_db_available():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The rules/sources vector database has not been built. Run rag/build_vector_db.py.",
        )
    if not ai_enabled():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI assist is not configured. Set ANTHROPIC_API_KEY to enable RAG answers.",
        )
    return call_ai(answer_question, payload.question)
