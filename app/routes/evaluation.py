from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

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
from app.services.rules import get_rule_versions

router = APIRouter(prefix="/evaluate", tags=["Evaluation"])


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


@router.post("/{client_id}", response_model=EvaluationResponse)
def evaluate_client_endpoint(
    client_id: int,
    payload: EvaluationRequest,
    db: Session = Depends(get_db),
) -> EvaluationResponse:
    return evaluate_client(db, client_id, payload.client_data)


@router.post("/{client_id}/preview", response_model=PreviewResponse)
def preview_client_endpoint(
    client_id: int,
    payload: EvaluationRequest,
    db: Session = Depends(get_db),
) -> PreviewResponse:
    return preview_client(db, client_id, payload.client_data)


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
            category=str(getattr(r.category, "value", r.category)),
            risk_level=str(getattr(r.risk_level, "value", r.risk_level)),
            confidence_level=str(getattr(r.confidence_level, "value", r.confidence_level)),
            effective_from=str(r.effective_from),
            effective_to=str(r.effective_to) if r.effective_to else None,
            is_deleted=r.is_deleted,
            description=r.description,
        )
        for r in rules
    ]
