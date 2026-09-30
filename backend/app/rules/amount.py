"""Rule 2: Unusual Transaction Amount Rule."""
import logging
from typing import TYPE_CHECKING
from app.engine.base import Rule, RuleResult
from app.engine.registry import register_rule

if TYPE_CHECKING:
    from app.engine.context import RuleContext
    from app.models import Transaction

logger = logging.getLogger(__name__)


@register_rule
class UnusualAmountRule(Rule):
    """Detects statistically anomalous transaction amounts based on account history.
    
    Trigger:
        - When history >= thin_threshold (default 5):
          amount exceeds mean + k * std (z-score >= k, default k=3.0) of last 30 days.
        - When history is thin (< thin_threshold):
          amount exceeds M * account average (default M=3.0), or large initial purchase.
    Score:
        Proportional to z-score or amount multiple, capped at 100.
    Evidence:
        amount, mean, std, z-score, history_count, ratio.
    """
    name = "unusual_amount"
    weight = 1.0
    default_params = {
        "k_std": 3.0,
        "thin_multiplier": 3.0,
        "thin_threshold": 5,
        "lookback_days": 30,
        "new_account_large_amount": 5000.0
    }

    def evaluate(self, txn: "Transaction", ctx: "RuleContext") -> RuleResult:
        k_std = float(ctx.get_rule_param(self.name, "k_std", self.default_params["k_std"]))
        thin_mult = float(ctx.get_rule_param(self.name, "thin_multiplier", self.default_params["thin_multiplier"]))
        thin_thresh = int(ctx.get_rule_param(self.name, "thin_threshold", self.default_params["thin_threshold"]))
        lookback_days = int(ctx.get_rule_param(self.name, "lookback_days", self.default_params["lookback_days"]))
        new_account_large_amt = float(ctx.get_rule_param(self.name, "new_account_large_amount", self.default_params["new_account_large_amount"]))

        stats = ctx.get_history_stats(
            account_id=txn.account_id,
            days=lookback_days,
            before_time=txn.timestamp,
            exclude_id=txn.id
        )

        count = stats["count"]
        mean = stats["mean"]
        std = stats["std"]
        amount = txn.amount

        # Case 1: Thin history (< thin_threshold transactions)
        if count < thin_thresh:
            if count == 0:
                if amount >= new_account_large_amt:
                    return RuleResult(
                        rule_name=self.name,
                        triggered=True,
                        score=65,
                        reason=f"High initial transaction of ${amount:.2f} on account with no prior history",
                        evidence={
                            "amount": amount,
                            "history_count": 0,
                            "threshold": new_account_large_amt,
                            "mode": "new_account_threshold"
                        }
                    )
                return RuleResult(
                    rule_name=self.name,
                    triggered=False,
                    score=0,
                    reason=f"First transaction of ${amount:.2f} within normal initial bounds",
                    evidence={"amount": amount, "history_count": 0}
                )

            # Thin history with prior transactions
            if mean > 0 and amount >= (thin_mult * mean):
                ratio = round(amount / mean, 2)
                score = min(100, max(50, int(45 + 15 * (ratio - thin_mult + 1))))
                return RuleResult(
                    rule_name=self.name,
                    triggered=True,
                    score=score,
                    reason=(
                        f"Unusual amount on thin history: ${amount:.2f} is {ratio}x "
                        f"prior average (${mean:.2f}, {count} prior transactions)"
                    ),
                    evidence={
                        "amount": amount,
                        "mean": mean,
                        "ratio": ratio,
                        "multiplier_threshold": thin_mult,
                        "history_count": count,
                        "mode": "thin_history_multiplier"
                    }
                )

            return RuleResult(
                rule_name=self.name,
                triggered=False,
                score=0,
                reason=f"Amount ${amount:.2f} within thin history multiplier threshold ({thin_mult}x of ${mean:.2f})",
                evidence={"amount": amount, "mean": mean, "history_count": count}
            )

        # Case 2: Established history (>= thin_threshold transactions)
        if std > 0:
            z_score = (amount - mean) / std
        else:
            z_score = 5.0 if amount > mean else 0.0

        if z_score >= k_std:
            # Score scales proportionally with z-score (e.g. z=3 -> 65, z=4 -> 80, z>=5.3 -> 100)
            score = min(100, max(50, int(50 + 15 * (z_score - k_std + 1))))
            return RuleResult(
                rule_name=self.name,
                triggered=True,
                score=score,
                reason=(
                    f"Statistically anomalous amount: ${amount:.2f} has z-score of {z_score:.2f} "
                    f"(exceeds {k_std} std threshold; 30d mean: ${mean:.2f}, std: ${std:.2f})"
                ),
                evidence={
                    "amount": amount,
                    "mean": mean,
                    "std": std,
                    "z_score": round(z_score, 2),
                    "k_threshold": k_std,
                    "history_count": count,
                    "mode": "z_score"
                }
            )

        return RuleResult(
            rule_name=self.name,
            triggered=False,
            score=0,
            reason=f"Amount ${amount:.2f} normal (z-score {z_score:.2f} < {k_std} std, mean: ${mean:.2f})",
            evidence={
                "amount": amount,
                "mean": mean,
                "std": std,
                "z_score": round(z_score, 2),
                "history_count": count
            }
        )
