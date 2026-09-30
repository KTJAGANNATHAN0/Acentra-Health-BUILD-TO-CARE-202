"""Fraud flags and reviewer console API endpoints."""
import logging
import math
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, asc

from app.db import get_db
from app.models import FraudFlag, Transaction, RuleResultModel, AuditLog
from app.schemas import (
    FraudFlagResponse,
    FraudFlagDetailResponse,
    FraudFlagUpdate,
    PaginatedFlagsResponse,
    RuleResultSchema,
    AuditLogResponse
)

router = APIRouter(prefix="/flags", tags=["Fraud Flags"])
logger = logging.getLogger(__name__)


@router.get("", response_model=PaginatedFlagsResponse)
def list_fraud_flags(
    status: Optional[str] = Query(None, description="Filter by status: PENDING, REVIEWED, CLEARED"),
    min_score: Optional[int] = Query(None, ge=0, le=100, description="Minimum risk score"),
    max_score: Optional[int] = Query(None, ge=0, le=100, description="Maximum risk score"),
    account_id: Optional[str] = Query(None, description="Filter by account ID"),
    sort_by: str = Query("score", description="Sort by field: score, created_at, updated_at"),
    sort_dir: str = Query("desc", description="Sort direction: asc or desc"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(15, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """FR-8: Console lists flagged transactions with filters and sorting."""
    query = (
        db.query(FraudFlag)
        .join(Transaction)
        .options(
            joinedload(FraudFlag.transaction).joinedload(Transaction.rule_results)
        )
    )

    if status and status.upper() != "ALL":
        query = query.filter(FraudFlag.status == status.upper())

    if min_score is not None:
        query = query.filter(FraudFlag.score >= min_score)

    if max_score is not None:
        query = query.filter(FraudFlag.score <= max_score)

    if account_id:
        query = query.filter(Transaction.account_id.ilike(f"%{account_id}%"))

    total = query.count()

    # Sorting
    sort_column = FraudFlag.score
    if sort_by == "created_at":
        sort_column = FraudFlag.created_at
    elif sort_by == "updated_at":
        sort_column = FraudFlag.updated_at
    elif sort_by == "score":
        sort_column = FraudFlag.score

    if sort_dir.lower() == "asc":
        query = query.order_by(asc(sort_column))
    else:
        query = query.order_by(desc(sort_column))

    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()
    total_pages = math.ceil(total / page_size) if page_size else 1

    return PaginatedFlagsResponse(
        items=[FraudFlagResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{flag_id}", response_model=FraudFlagDetailResponse)
def get_fraud_flag_detail(
    flag_id: int,
    db: Session = Depends(get_db)
):
    """FR-9: Console detail view shows transaction, triggered rules, reasons, evidence, and audit trail."""
    flag = (
        db.query(FraudFlag)
        .options(
            joinedload(FraudFlag.transaction).joinedload(Transaction.rule_results)
        )
        .filter(FraudFlag.id == flag_id)
        .first()
    )
    if not flag:
        raise HTTPException(status_code=404, detail="Fraud flag not found")

    # Fetch rule results
    rule_results = (
        db.query(RuleResultModel)
        .filter_by(transaction_id=flag.transaction_id)
        .all()
    )

    # Fetch audit logs for this flag and transaction
    audit_logs = (
        db.query(AuditLog)
        .filter(
            (AuditLog.entity_id == str(flag.id)) | (AuditLog.entity_id == flag.transaction_id)
        )
        .order_by(AuditLog.created_at.desc())
        .all()
    )

    return FraudFlagDetailResponse(
        flag=FraudFlagResponse.model_validate(flag),
        rule_results=[RuleResultSchema.model_validate(r) for r in rule_results],
        audit_logs=[AuditLogResponse.model_validate(a) for a in audit_logs]
    )


@router.patch("/{flag_id}", response_model=FraudFlagResponse)
def update_fraud_flag_status(
    flag_id: int,
    payload: FraudFlagUpdate,
    db: Session = Depends(get_db)
):
    """FR-10: Reviewer can mark a flag REVIEWED or CLEARED with an optional note; action is audit-logged."""
    flag = db.query(FraudFlag).filter_by(id=flag_id).first()
    if not flag:
        raise HTTPException(status_code=404, detail="Fraud flag not found")

    old_status = flag.status
    now = datetime.now(timezone.utc)

    flag.status = payload.status
    flag.reviewed_by = payload.reviewer or "fraud_reviewer"
    flag.reviewed_at = now
    if payload.note:
        flag.review_note = payload.note
    flag.updated_at = now

    # Audit log
    audit = AuditLog(
        entity="fraud_flag",
        entity_id=str(flag.id),
        action=f"STATUS_CHANGE_{payload.status}",
        actor=flag.reviewed_by,
        payload={
            "old_status": old_status,
            "new_status": payload.status,
            "note": payload.note,
            "timestamp": now.isoformat()
        }
    )
    db.add(audit)
    db.commit()
    db.refresh(flag)

    return FraudFlagResponse.model_validate(flag)
