"""Rule 1: Transaction Velocity Rule."""
import logging
from typing import TYPE_CHECKING
from app.engine.base import Rule, RuleResult
from app.engine.registry import register_rule

if TYPE_CHECKING:
    from app.engine.context import RuleContext
    from app.models import Transaction

logger = logging.getLogger(__name__)


@register_rule
class VelocityRule(Rule):
    """Flags high-frequency transaction bursts by the same account.
    
    Trigger:
        More than N transactions (default 5) within W minutes (default 10).
    Score:
        Scales with overage: min(100, 40 + 15 * (count - N)).
    Evidence:
        count, window_minutes, threshold, transaction_ids, timestamps.
    """
    name = "velocity"
    weight = 1.0
    default_params = {
        "max_count": 5,
        "window_minutes": 10
    }

    def evaluate(self, txn: "Transaction", ctx: "RuleContext") -> RuleResult:
        max_count = ctx.get_rule_param(self.name, "max_count", self.default_params["max_count"])
        window_minutes = ctx.get_rule_param(self.name, "window_minutes", self.default_params["window_minutes"])

        # Fetch recent transactions strictly prior to or up to this transaction
        recent_data = ctx.count_recent(
            account_id=txn.account_id,
            minutes=window_minutes,
            before_time=txn.timestamp
        )

        # Total count including the incoming transaction
        # If the incoming transaction isn't in DB yet, recent_data['count'] is the prior count.
        # But if it's already in DB, recent_data['transaction_ids'] may include txn.id.
        prior_ids = [tid for tid in recent_data["transaction_ids"] if tid != txn.id]
        total_count = len(prior_ids) + 1  # incoming transaction is the +1

        if total_count > max_count:
            overage = total_count - max_count
            score = min(100, max(40, 40 + 15 * overage))
            reason = (
                f"High velocity: account executed {total_count} transactions in "
                f"{window_minutes} minutes (limit: {max_count})"
            )
            return RuleResult(
                rule_name=self.name,
                triggered=True,
                score=score,
                reason=reason,
                evidence={
                    "total_count": total_count,
                    "prior_count": len(prior_ids),
                    "threshold_max_count": max_count,
                    "window_minutes": window_minutes,
                    "recent_transaction_ids": prior_ids[:10],
                    "overage": overage
                }
            )

        return RuleResult(
            rule_name=self.name,
            triggered=False,
            score=0,
            reason=f"Velocity normal: {total_count} transactions within {window_minutes}m (limit {max_count})",
            evidence={
                "total_count": total_count,
                "threshold_max_count": max_count,
                "window_minutes": window_minutes
            }
        )
