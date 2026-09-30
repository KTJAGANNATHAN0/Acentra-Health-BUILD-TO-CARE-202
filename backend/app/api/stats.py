"""Dashboard statistics and metrics API router."""
import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db import get_db
from app.models import Transaction, FraudFlag, RuleResultModel
from app.schemas import FraudStatsResponse

router = APIRouter(prefix="/stats", tags=["Statistics"])
logger = logging.getLogger(__name__)


@router.get("", response_model=FraudStatsResponse)
def get_fraud_stats(db: Session = Depends(get_db)):
    """Aggregate dashboard metrics for reviewer console."""
    total_txns = db.query(func.count(Transaction.id)).scalar() or 0
    total_flags = db.query(func.count(FraudFlag.id)).scalar() or 0
    pending_flags = db.query(func.count(FraudFlag.id)).filter(FraudFlag.status == "PENDING").scalar() or 0
    reviewed_flags = db.query(func.count(FraudFlag.id)).filter(FraudFlag.status == "REVIEWED").scalar() or 0
    cleared_flags = db.query(func.count(FraudFlag.id)).filter(FraudFlag.status == "CLEARED").scalar() or 0
    alerts_sent = db.query(func.count(FraudFlag.id)).filter(FraudFlag.notified_at.isnot(None)).scalar() or 0
    avg_score = db.query(func.avg(Transaction.risk_score)).scalar() or 0.0

    # Rule trigger distribution
    rule_counts = {}
    rule_aggregates = (
        db.query(RuleResultModel.rule_name, func.count(RuleResultModel.id))
        .filter(RuleResultModel.triggered == True)
        .group_by(RuleResultModel.rule_name)
        .all()
    )
    for rule_name, count in rule_aggregates:
        rule_counts[rule_name] = count

    return FraudStatsResponse(
        total_transactions=total_txns,
        total_flagged=total_flags,
        pending_flags=pending_flags,
        reviewed_flags=reviewed_flags,
        cleared_flags=cleared_flags,
        high_risk_alerts_sent=alerts_sent,
        avg_risk_score=round(float(avg_score), 1),
        rule_trigger_counts=rule_counts
    )
