from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.config import privacy_mode_enabled
from app.database.session import get_db
from app.schemas.evaluation import (
    EvaluationRequest,
    EvaluationResponse,
    PreviewResponse,
    RuleVersionRead,
)
from app.services.evaluation import (
    evaluate_client,
    evaluate_private_assessment,
    preview_client,
    preview_private_assessment,
)
from app.services.report_html import generate_report_html
from app.engine.scorer import _normalize
from app.services.rules import get_rule_versions

router = APIRouter(prefix="/evaluate", tags=["Evaluation"])


def _ensure_client_eval_allowed() -> None:
    if privacy_mode_enabled():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Client-based evaluation is disabled in privacy mode. Use /evaluate/private instead.",
        )


@router.post("/private", response_model=EvaluationResponse)
def evaluate_private_endpoint(
    payload: EvaluationRequest,
    db: Session = Depends(get_db),
) -> EvaluationResponse:
    return evaluate_private_assessment(
        db,
        payload.client_data,
        assessment_label=payload.assessment_label,
    )


@router.post("/private/preview", response_model=PreviewResponse)
def preview_private_endpoint(
    payload: EvaluationRequest,
    db: Session = Depends(get_db),
) -> PreviewResponse:
    return preview_private_assessment(
        db,
        payload.client_data,
        assessment_label=payload.assessment_label,
    )


@router.post("/private/report")
def report_private_endpoint(
    payload: EvaluationRequest,
    db: Session = Depends(get_db),
) -> Response:
    result = evaluate_private_assessment(
        db,
        payload.client_data,
        assessment_label=payload.assessment_label,
    )
    fact_count = sum(
        1 for v in payload.client_data.values()
        if v is not None and v != "" and v is not False
    )
    html = generate_report_html(result, fact_count=fact_count)
    return Response(content=html, media_type="text/html")


@router.post("/{client_id}", response_model=EvaluationResponse)
def evaluate_client_endpoint(
    client_id: int,
    payload: EvaluationRequest,
    db: Session = Depends(get_db),
) -> EvaluationResponse:
    _ensure_client_eval_allowed()
    try:
        return evaluate_client(db, client_id, payload.client_data, assessment_label=payload.assessment_label)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{client_id}/preview", response_model=PreviewResponse)
def preview_client_endpoint(
    client_id: int,
    payload: EvaluationRequest,
    db: Session = Depends(get_db),
) -> PreviewResponse:
    _ensure_client_eval_allowed()
    try:
        return preview_client(db, client_id, payload.client_data)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/rules/{rule_code}/versions", response_model=list[RuleVersionRead])
def rule_versions_endpoint(
    rule_code: str,
    db: Session = Depends(get_db),
) -> list[RuleVersionRead]:
    rules = get_rule_versions(db, rule_code)
    return [
        RuleVersionRead(
            id=r.id,
            rule_code=r.rule_code,
            version=r.version,
            jurisdiction=r.jurisdiction,
            category=_normalize(r.category),
            risk_level=_normalize(r.risk_level),
            confidence_level=_normalize(r.confidence_level),
            effective_from=str(r.effective_from),
            effective_to=str(r.effective_to) if r.effective_to else None,
            is_deleted=r.is_deleted,
            description=r.description,
        )
        for r in rules
    ]
