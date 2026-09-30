"""Notification service managing dispatch, retries, and idempotency."""
import logging
import time
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session

from app.config import settings
from app.db import SessionLocal
from app.models import FraudFlag, Transaction, RuleResultModel, AuditLog
from app.notifications.base import Notifier, AlertPayload
from app.notifications.log import LogNotifier
from app.notifications.sns import SNSNotifier
from app.notifications.ses import SESNotifier

logger = logging.getLogger(__name__)


def get_notifier() -> Notifier:
    """Notifier factory based on settings.NOTIFIER."""
    mode = (settings.NOTIFIER or "log").lower()
    if mode == "sns":
        return SNSNotifier()
    elif mode == "ses":
        return SESNotifier()
    else:
        return LogNotifier()


class NotificationService:
    """Handles alert dispatching with idempotency and retry logic."""

    def __init__(self, notifier: Optional[Notifier] = None):
        self.notifier = notifier or get_notifier()

    def process_high_risk_alert(self, transaction_id: str, flag_id: int):
        """Asynchronously dispatch high-risk notification if not already notified.
        
        Runs in background task. Manages its own database session.
        Guarantees idempotency via fraud_flags.notified_at.
        Retries up to 3 times on transient failure.
        """
        db: Session = SessionLocal()
        try:
            flag = db.query(FraudFlag).filter_by(id=flag_id).first()
            if not flag:
                logger.warning(f"Flag ID {flag_id} not found for notification")
                return

            # Idempotency check: only send if notified_at IS NULL
            if flag.notified_at is not None:
                logger.info(f"Flag {flag_id} already notified at {flag.notified_at}. Skipping alert.")
                return

            txn = db.query(Transaction).filter_by(id=transaction_id).first()
            if not txn:
                logger.warning(f"Transaction ID {transaction_id} not found for notification")
                return

            # Get triggered rule results
            results = (
                db.query(RuleResultModel)
                .filter_by(transaction_id=transaction_id, triggered=True)
                .all()
            )

            payload = AlertPayload(
                transaction_id=txn.id,
                flag_id=flag.id,
                account_id=txn.account_id,
                amount=txn.amount,
                currency=txn.currency,
                merchant=txn.merchant,
                score=flag.score,
                triggered_rules=[r.rule_name for r in results],
                rule_reasons=[r.reason for r in results],
                console_link=f"{settings.CONSOLE_URL}/flags/{flag.id}",
                timestamp=txn.timestamp
            )

            # Retry up to 3 times with exponential backoff
            max_attempts = 3
            success = False
            for attempt in range(1, max_attempts + 1):
                try:
                    success = self.notifier.send_alert(payload)
                    if success:
                        break
                except Exception as ex:
                    logger.warning(f"Alert attempt {attempt}/{max_attempts} failed: {ex}")
                
                if attempt < max_attempts:
                    time.sleep(0.5 * (2 ** (attempt - 1)))

            if success:
                # Mark as notified for idempotency
                now = datetime.now(timezone.utc)
                flag.notified_at = now
                
                # Write to audit log
                audit = AuditLog(
                    entity="fraud_flag",
                    entity_id=str(flag.id),
                    action="ALERT_DISPATCHED",
                    actor="notification_service",
                    payload={
                        "notifier": settings.NOTIFIER,
                        "score": flag.score,
                        "transaction_id": txn.id,
                        "notified_at": now.isoformat()
                    }
                )
                db.add(audit)
                db.commit()
                logger.info(f"Successfully notified high risk alert for flag {flag.id}")
            else:
                logger.error(f"Failed to dispatch alert for flag {flag.id} after {max_attempts} attempts")
        except Exception as e:
            logger.error(f"Error in process_high_risk_alert: {e}", exc_info=True)
        finally:
            db.close()


notification_service = NotificationService()
