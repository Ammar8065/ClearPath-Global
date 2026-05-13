from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.rule import RuleCreate, RuleWithSourceRead
from app.services.rules import create_rule, list_rules, soft_delete_rule

router = APIRouter(prefix="/rules", tags=["Rules"])


@router.post("", response_model=RuleWithSourceRead, status_code=status.HTTP_201_CREATED)
def create_rule_endpoint(payload: RuleCreate, db: Session = Depends(get_db)) -> RuleWithSourceRead:
    try:
        rule = create_rule(db, payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    db.refresh(rule, attribute_names=["source"])
    return rule


@router.get("", response_model=list[RuleWithSourceRead])
def list_rules_endpoint(db: Session = Depends(get_db)) -> list[RuleWithSourceRead]:
    return list_rules(db)


@router.delete("/{rule_id}", response_model=RuleWithSourceRead)
def soft_delete_rule_endpoint(rule_id: int, db: Session = Depends(get_db)) -> RuleWithSourceRead:
    try:
        rule = soft_delete_rule(db, rule_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    db.refresh(rule, attribute_names=["source"])
    return rule
