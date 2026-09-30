"""Simulator API router for generating live fraud scenarios from the console."""
from datetime import datetime, timedelta, timezone
import random
import uuid
from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.engine.engine import RuleEngine
from app.models import Transaction, RuleResultModel, FraudFlag, AuditLog
from app.notifications.service import notification_service
from app.schemas import TransactionEvaluationResponse, TransactionResponse, RuleResultSchema

router = APIRouter(prefix="/simulator", tags=["Simulator"])
engine = RuleEngine()


@router.post("/scenario/{scenario_name}")
def trigger_scenario(
    scenario_name: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Trigger realistic fraud patterns or normal traffic for live console demonstration."""
    now = datetime.now(timezone.utc)
    account_suffix = random.randint(100, 999)

    def evaluate_and_persist(txn_obj):
        db.add(txn_obj)
        db.flush()
        eval_result = engine.evaluate(txn_obj, db)
        txn_obj.risk_score = eval_result.score

        for r in eval_result.rule_results:
            rr = RuleResultModel(
                transaction_id=txn_obj.id,
                rule_name=r.rule_name,
                triggered=r.triggered,
                score=r.score,
                reason=r.reason,
                evidence=r.evidence
            )
            db.add(rr)

        flag_id = None
        if eval_result.flagged:
            flag = FraudFlag(
                transaction_id=txn_obj.id,
                score=eval_result.score,
                status="PENDING"
            )
            db.add(flag)
            db.flush()
            flag_id = flag.id

            if eval_result.high_risk:
                background_tasks.add_task(
                    notification_service.process_high_risk_alert,
                    transaction_id=txn_obj.id,
                    flag_id=flag.id
                )

        audit = AuditLog(
            entity="transaction",
            entity_id=txn_obj.id,
            action="SIMULATED_INGESTION",
            actor="console_simulator",
            payload={"scenario": scenario_name, "score": eval_result.score}
        )
        db.add(audit)
        db.commit()
        db.refresh(txn_obj)

        return TransactionEvaluationResponse(
            transaction=TransactionResponse.model_validate(txn_obj),
            risk_score=eval_result.score,
            flagged=eval_result.flagged,
            high_risk=eval_result.high_risk,
            decision=eval_result.decision,
            flag_id=flag_id,
            rule_results=[RuleResultSchema.model_validate(r) for r in eval_result.rule_results]
        )

    if scenario_name == "velocity_burst":
        account_id = f"sim_vel_{account_suffix}"
        # Create 5 prior transactions within 4 minutes
        for i in range(5, 0, -1):
            prior = Transaction(
                id=str(uuid.uuid4()),
                account_id=account_id,
                amount=round(random.uniform(15.0, 60.0), 2),
                currency="USD",
                merchant="QuickPay Terminal",
                lat=37.7749,
                lon=-122.4194,
                country="US",
                timestamp=now - timedelta(minutes=i)
            )
            evaluate_and_persist(prior)

        # Triggering 6th transaction
        burst_txn = Transaction(
            id=str(uuid.uuid4()),
            account_id=account_id,
            amount=85.00,
            currency="USD",
            merchant="Digital Gift Card Central",
            lat=37.7749,
            lon=-122.4194,
            country="US",
            timestamp=now
        )
        return evaluate_and_persist(burst_txn)

    elif scenario_name == "impossible_travel":
        account_id = f"sim_travel_{account_suffix}"
        # Prior transaction in Tokyo, Japan 10 minutes ago
        t1 = Transaction(
            id=str(uuid.uuid4()),
            account_id=account_id,
            amount=42.00,
            currency="USD",
            merchant="Tokyo Metro Station Kiosk",
            lat=35.6762,
            lon=139.6503,
            country="JP",
            timestamp=now - timedelta(minutes=10)
        )
        evaluate_and_persist(t1)

        # Current transaction in New York, USA (10,800 km away in 10 minutes -> 64,800 km/h)
        t2 = Transaction(
            id=str(uuid.uuid4()),
            account_id=account_id,
            amount=210.00,
            currency="USD",
            merchant="Fifth Avenue Electronics NYC",
            lat=40.7128,
            lon=-74.0060,
            country="US",
            timestamp=now
        )
        return evaluate_and_persist(t2)

    elif scenario_name == "amount_spike":
        account_id = f"sim_amt_{account_suffix}"
        # 6 baseline transactions averaging $20
        for i in range(6, 0, -1):
            base = Transaction(
                id=str(uuid.uuid4()),
                account_id=account_id,
                amount=round(random.uniform(18.0, 24.0), 2),
                currency="USD",
                merchant="Neighborhood Bakery",
                lat=41.8781,
                lon=-87.6298,
                country="US",
                timestamp=now - timedelta(days=i)
            )
            db.add(base)
        db.commit()

        # Extreme spike: $5,400 purchase
        spike_txn = Transaction(
            id=str(uuid.uuid4()),
            account_id=account_id,
            amount=5400.00,
            currency="USD",
            merchant="Diamond Jewelers International",
            lat=41.8781,
            lon=-87.6298,
            country="US",
            timestamp=now
        )
        return evaluate_and_persist(spike_txn)

    else:  # normal
        account_id = f"sim_legit_{account_suffix}"
        norm_txn = Transaction(
            id=str(uuid.uuid4()),
            account_id=account_id,
            amount=round(random.uniform(12.0, 45.0), 2),
            currency="USD",
            merchant=random.choice(["Starbucks Coffee", "Target Express", "Trader Joe's", "Shell Gas"]),
            lat=40.7128,
            lon=-74.0060,
            country="US",
            timestamp=now
        )
        return evaluate_and_persist(norm_txn)
