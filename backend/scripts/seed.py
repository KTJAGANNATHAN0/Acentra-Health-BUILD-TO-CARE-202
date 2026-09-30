"""Seed database with realistic baseline transactions and injected fraud patterns."""
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import settings
from app.db import SessionLocal, init_db
from app.models import Transaction, RuleResultModel, FraudFlag, AuditLog
from app.engine.engine import RuleEngine

engine = RuleEngine()


def seed_database():
    print("Initializing database...")
    init_db()
    db = SessionLocal()

    print("Clearing existing data...")
    db.query(AuditLog).delete()
    db.query(FraudFlag).delete()
    db.query(RuleResultModel).delete()
    db.query(Transaction).delete()
    db.commit()

    now = datetime.now(timezone.utc)
    print("Seeding baseline legitimate transactions...")

    # 1. Normal users with 10-15 regular transactions over the past 2 weeks
    normal_merchants = [
        ("Whole Foods Market", 65.40, 40.7128, -74.0060, "US"),
        ("Starbucks Coffee", 8.75, 40.7150, -74.0020, "US"),
        ("Uber Trip", 24.20, 40.7200, -73.9950, "US"),
        ("Amazon.com", 42.10, 40.7128, -74.0060, "US"),
        ("Netflix Subscription", 19.99, None, None, "US"),
        ("Chevron Gas Station", 45.00, 40.7100, -74.0100, "US"),
        ("Target Store", 88.30, 40.7180, -74.0010, "US"),
    ]

    for user_idx in range(1, 6):
        account_id = f"acc_legit_{user_idx:03d}"
        for day in range(14, 0, -2):
            merchant, amt, lat, lon, country = normal_merchants[(user_idx + day) % len(normal_merchants)]
            t_time = now - timedelta(days=day, hours=user_idx * 2)
            txn = Transaction(
                id=str(uuid.uuid4()),
                account_id=account_id,
                amount=amt,
                currency="USD",
                merchant=merchant,
                lat=lat,
                lon=lon,
                country=country,
                timestamp=t_time,
                risk_score=0
            )
            db.add(txn)
    db.commit()

    def process_and_persist(txn_obj):
        db.add(txn_obj)
        db.flush()
        res = engine.evaluate(txn_obj, db)
        txn_obj.risk_score = res.score
        
        for r in res.rule_results:
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
        if res.flagged:
            flag = FraudFlag(
                transaction_id=txn_obj.id,
                score=res.score,
                status="PENDING",
                notified_at=now if res.high_risk else None
            )
            db.add(flag)
            db.flush()
            flag_id = flag.id
            
        audit = AuditLog(
            entity="transaction",
            entity_id=txn_obj.id,
            action="EVALUATED",
            actor="seed_script",
            payload={"score": res.score, "decision": res.decision}
        )
        db.add(audit)
        db.commit()
        return txn_obj, flag_id

    print("Injecting Fraud Pattern 1: Velocity Burst...")
    # Account executes 7 transactions within 6 minutes
    vel_account = "acc_fraud_velocity_88"
    for i in range(7):
        t_time = now - timedelta(minutes=(7 - i), seconds=20)
        txn = Transaction(
            id=str(uuid.uuid4()),
            account_id=vel_account,
            amount=49.99 + (i * 5),
            currency="USD",
            merchant=f"Digital Goods Store #{i+1}",
            lat=37.7749,
            lon=-122.4194,
            country="US",
            timestamp=t_time
        )
        process_and_persist(txn)

    print("Injecting Fraud Pattern 2: Statistical Amount Anomaly...")
    amt_account = "acc_fraud_amount_99"
    # Seed 10 small baseline transactions around $30
    for i in range(10, 0, -1):
        t_time = now - timedelta(days=i)
        t_base = Transaction(
            id=str(uuid.uuid4()),
            account_id=amt_account,
            amount=30.0 + (i % 5),
            currency="USD",
            merchant="Local Grocery",
            lat=34.0522,
            lon=-118.2437,
            country="US",
            timestamp=t_time,
            risk_score=0
        )
        db.add(t_base)
    db.commit()

    # The anomaly: sudden $4,850 charge
    spike_txn = Transaction(
        id=str(uuid.uuid4()),
        account_id=amt_account,
        amount=4850.00,
        currency="USD",
        merchant="Rolex Geneva Online Store",
        lat=34.0522,
        lon=-118.2437,
        country="US",
        timestamp=now - timedelta(minutes=45)
    )
    process_and_persist(spike_txn)

    print("Injecting Fraud Pattern 3: Impossible Travel (Teleportation)...")
    geo_account = "acc_fraud_travel_77"
    # Transaction in New York City 20 minutes ago
    geo_1 = Transaction(
        id=str(uuid.uuid4()),
        account_id=geo_account,
        amount=12.50,
        currency="USD",
        merchant="Manhattan Cafe",
        lat=40.7128,
        lon=-74.0060,
        country="US",
        timestamp=now - timedelta(minutes=20)
    )
    process_and_persist(geo_1)

    # Transaction in London 2 minutes ago (5,570 km away in 18 mins -> speed ~18,500 km/h)
    geo_2 = Transaction(
        id=str(uuid.uuid4()),
        account_id=geo_account,
        amount=650.00,
        currency="GBP",
        merchant="Harrods Department Store London",
        lat=51.5074,
        lon=-0.1278,
        country="GB",
        timestamp=now - timedelta(minutes=2)
    )
    _, flag2_id = process_and_persist(geo_2)

    print("Injecting Fraud Pattern 4: Combined Multi-Rule High-Risk Fraud...")
    combined_account = "acc_fraud_combo_01"
    comb_1 = Transaction(
        id=str(uuid.uuid4()),
        account_id=combined_account,
        amount=35.00,
        currency="USD",
        merchant="San Francisco Diner",
        lat=37.7749,
        lon=-122.4194,
        country="US",
        timestamp=now - timedelta(minutes=30)
    )
    process_and_persist(comb_1)

    # Teleport to Paris + huge amount ($9,200) + fast velocity
    comb_2 = Transaction(
        id=str(uuid.uuid4()),
        account_id=combined_account,
        amount=9200.00,
        currency="EUR",
        merchant="Galeries Lafayette Paris",
        lat=48.8566,
        lon=2.3522,
        country="FR",
        timestamp=now - timedelta(minutes=5)
    )
    _, comb_flag_id = process_and_persist(comb_2)

    # Mark one of the flags as REVIEWED and another as CLEARED for queue demo variety
    if flag2_id:
        f = db.query(FraudFlag).filter_by(id=flag2_id).first()
        if f:
            f.status = "REVIEWED"
            f.reviewed_by = "sarah.chen@fraud-ops.com"
            f.reviewed_at = now - timedelta(minutes=1)
            f.review_note = "Confirmed compromised card token. Card blocked and customer notified."
            db.add(AuditLog(
                entity="fraud_flag",
                entity_id=str(f.id),
                action="STATUS_CHANGE_REVIEWED",
                actor=f.reviewed_by,
                payload={"note": f.review_note}
            ))

    db.commit()
    print("Seed complete! Database populated with realistic legitimate and fraudulent traffic.")
    db.close()


if __name__ == "__main__":
    seed_database()
