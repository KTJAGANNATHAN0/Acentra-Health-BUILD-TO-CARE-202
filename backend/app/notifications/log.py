"""Local log-based notifier for testing and development without AWS dependencies."""
import json
import logging
from app.notifications.base import Notifier, AlertPayload

logger = logging.getLogger("fraud_engine.alerts")


class LogNotifier(Notifier):
    """Outputs high-risk fraud alerts to structured application logs."""

    def send_alert(self, payload: AlertPayload) -> bool:
        alert_dict = {
            "EVENT": "HIGH_RISK_FRAUD_ALERT",
            "transaction_id": payload.transaction_id,
            "flag_id": payload.flag_id,
            "account_id": payload.account_id,
            "amount": f"{payload.amount} {payload.currency}",
            "merchant": payload.merchant,
            "risk_score": payload.score,
            "triggered_rules": payload.triggered_rules,
            "reasons": payload.rule_reasons,
            "console_link": payload.console_link,
            "timestamp": payload.timestamp.isoformat()
        }
        
        logger.warning(
            f"[FRAUD ALERT - SCORE {payload.score}] Account: {payload.account_id}, "
            f"Txn: {payload.transaction_id} -> {json.dumps(alert_dict, indent=2)}"
        )
        return True
