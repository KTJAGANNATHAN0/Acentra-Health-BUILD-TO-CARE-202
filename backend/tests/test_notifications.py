"""Tests for Notification Service and Idempotency Guard."""
from datetime import datetime, timezone
import pytest
from app.models import Transaction, FraudFlag, RuleResultModel
from app.notifications.base import Notifier, AlertPayload
from app.notifications.service import NotificationService
from tests.conftest import TestingSessionLocal


class DummyTestNotifier(Notifier):
    def __init__(self, should_fail=False):
        self.should_fail = should_fail
        self.call_count = 0
        self.dispatched_payloads = []

    def send_alert(self, payload: AlertPayload) -> bool:
        self.call_count += 1
        if self.should_fail:
            raise RuntimeError("Network timeout to AWS SNS endpoint")
        self.dispatched_payloads.append(payload)
        return True


def test_notification_idempotency(db_session, monkeypatch):
    """Notification must be sent strictly once; re-evaluation must not duplicate alerts."""
    # Setup test transaction and flag
    txn = Transaction(
        id="txn_alert_test",
        account_id="acc_alert_1",
        amount=1200.0,
        merchant="High Roller Casino",
        currency="USD",
        risk_score=95
    )
    flag = FraudFlag(
        id=999,
        transaction_id=txn.id,
        score=95,
        status="PENDING",
        notified_at=None  # not yet notified
    )
    rr = RuleResultModel(
        transaction_id=txn.id,
        rule_name="impossible_travel",
        triggered=True,
        score=95,
        reason="Impossible travel detected"
    )
    db_session.add(txn)
    db_session.add(flag)
    db_session.add(rr)
    db_session.commit()

    dummy_notifier = DummyTestNotifier()
    service = NotificationService(notifier=dummy_notifier)

    # Patch SessionLocal to use TestingSessionLocal
    monkeypatch.setattr("app.notifications.service.SessionLocal", TestingSessionLocal)

    # First dispatch -> should notify
    service.process_high_risk_alert(transaction_id=txn.id, flag_id=flag.id)
    assert dummy_notifier.call_count == 1
    assert len(dummy_notifier.dispatched_payloads) == 1
    
    # Expire cached state and verify flag.notified_at is now set in db
    db_session.expire_all()
    refreshed_flag = db_session.query(FraudFlag).filter_by(id=flag.id).first()
    assert refreshed_flag.notified_at is not None

    # Second dispatch (e.g. re-evaluation or duplicate call) -> should be skipped due to idempotency guard!
    service.process_high_risk_alert(transaction_id=txn.id, flag_id=flag.id)
    assert dummy_notifier.call_count == 1  # Unchanged!
