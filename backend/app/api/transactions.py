"""Transaction ingestion and evaluation API endpoints."""
import logging
from datetime import datetime, timezone
import uuid
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.engine.engine import RuleEngine
from app.models import Transaction, RuleResultModel, FraudFlag, AuditLog
from app.notifications.service import notification_service
from app.schemas import (
    TransactionCreate,
    TransactionEvaluationResponse,
    TransactionResponse,
    RuleResultSchema
)

router = APIRouter(prefix="/transactions", tags=["Transactions"])
logger = logging.getLogger(__name__)

engine = RuleEngine()


@router.post("", response_model=TransactionEvaluationResponse, status_code=status.HTTP_201_CREATED)
def ingest_and_evaluate_transaction(
    payload: TransactionCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """FR-1: Ingest transaction, run rule engine, persist results and flags, and trigger alerts."""
    txn_id = payload.id or str(uuid.uuid4())
    txn_timestamp = payload.timestamp or datetime.now(timezone.utc)

    # 1. Create Transaction entity
    txn = Transaction(
        id=txn_id,
        account_id=payload.account_id,
        amount=payload.amount,
        currency=payload.currency.upper(),
        merchant=payload.merchant,
        lat=payload.lat,
        lon=payload.lon,
        country=payload.country,
        timestamp=txn_timestamp,
        risk_score=0  # updated after evaluation
    )
    db.add(txn)
    db.flush()

    # 2. Evaluate against enabled rules
    eval_result = engine.evaluate(txn, db)
    txn.risk_score = eval_result.score

    # 3. Store Rule Results
    rule_results_models = []
    for r in eval_result.rule_results:
        rr = RuleResultModel(
            transaction_id=txn.id,
            rule_name=r.rule_name,
            triggered=r.triggered,
            score=r.score,
            reason=r.reason,
            evidence=r.evidence
        )
        db.add(rr)
        rule_results_models.append(rr)

    flag_id = None
    # 4. FR-6: Create FraudFlag if score >= FLAG_THRESHOLD
    if eval_result.flagged:
        flag = FraudFlag(
            transaction_id=txn.id,
            score=eval_result.score,
            status="PENDING"
        )
        db.add(flag)
        db.flush()
        flag_id = flag.id

        # 5. FR-7: Score >= HIGH_RISK_THRESHOLD triggers SNS/SES notification asynchronously
        if eval_result.high_risk:
            background_tasks.add_task(
                notification_service.process_high_risk_alert,
                transaction_id=txn.id,
                flag_id=flag.id
            )

    # 6. Audit log for ingestion
    audit = AuditLog(
        entity="transaction",
        entity_id=txn.id,
        action="EVALUATED",
        actor="system",
        payload={
            "score": eval_result.score,
            "decision": eval_result.decision,
            "triggered_rules": [r.rule_name for r in eval_result.rule_results if r.triggered]
        }
    )
    db.add(audit)
    db.commit()
    db.refresh(txn)

    return TransactionEvaluationResponse(
        transaction=TransactionResponse.model_validate(txn),
        risk_score=eval_result.score,
        flagged=eval_result.flagged,
        high_risk=eval_result.high_risk,
        decision=eval_result.decision,
        flag_id=flag_id,
        rule_results=[RuleResultSchema.model_validate(r) for r in eval_result.rule_results]
    )


@router.post("/{txn_id}/re-evaluate", response_model=TransactionEvaluationResponse)
def re_evaluate_transaction(
    txn_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """FR-12: Re-evaluate a transaction on demand (e.g. after rule tuning)."""
    txn = db.query(Transaction).filter_by(id=txn_id).first()
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    # Evaluate with current rules
    eval_result = engine.evaluate(txn, db)
    txn.risk_score = eval_result.score

    # Clear old rule results
    db.query(RuleResultModel).filter_by(transaction_id=txn.id).delete()

    # Store new rule results
    for r in eval_result.rule_results:
        rr = RuleResultModel(
            transaction_id=txn.id,
            rule_name=r.rule_name,
            triggered=r.triggered,
            score=r.score,
            reason=r.reason,
            evidence=r.evidence
        )
        db.add(rr)

    # Check or update fraud flag
    flag = db.query(FraudFlag).filter_by(transaction_id=txn.id).first()
    if eval_result.flagged:
        if not flag:
            flag = FraudFlag(
                transaction_id=txn.id,
                score=eval_result.score,
                status="PENDING"
            )
            db.add(flag)
            db.flush()
        else:
            flag.score = eval_result.score
            # If was CLEARED and re-evaluated, keep current status or update score
            flag.updated_at = datetime.now(timezone.utc)

        # Trigger notification only if high risk and not yet notified (idempotent)
        if eval_result.high_risk and flag.notified_at is None:
            background_tasks.add_task(
                notification_service.process_high_risk_alert,
                transaction_id=txn.id,
                flag_id=flag.id
            )
    else:
        # If no longer flagged and was pending, mark cleared or delete
        if flag and flag.status == "PENDING":
            flag.status = "CLEARED"
            flag.review_note = "Auto-cleared via re-evaluation: score dropped below threshold"
            flag.reviewed_by = "system"
            flag.reviewed_at = datetime.now(timezone.utc)

    # Audit log
    audit = AuditLog(
        entity="transaction",
        entity_id=txn.id,
        action="RE_EVALUATED",
        actor="system",
        payload={
            "new_score": eval_result.score,
            "decision": eval_result.decision
        }
    )
    db.add(audit)
    db.commit()
    db.refresh(txn)

    flag_id = flag.id if flag else None

    return TransactionEvaluationResponse(
        transaction=TransactionResponse.model_validate(txn),
        risk_score=eval_result.score,
        flagged=eval_result.flagged,
        high_risk=eval_result.high_risk,
        decision=eval_result.decision,
        flag_id=flag_id,
        rule_results=[RuleResultSchema.model_validate(r) for r in eval_result.rule_results]
    )
