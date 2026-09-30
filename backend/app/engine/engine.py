"""Core Rule Engine orchestrating dynamic rule execution, isolation, and score aggregation."""
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from app.config import settings
from app.engine.base import Rule, RuleResult
from app.engine.context import RuleContext
from app.engine.registry import load_rules
from app.models import RuleConfigModel, Transaction

logger = logging.getLogger(__name__)


@dataclass
class EngineEvaluation:
    score: int
    rule_results: List[RuleResult]
    flagged: bool
    high_risk: bool
    decision: str  # "ALLOW", "FLAGGED_FOR_REVIEW", "HIGH_RISK_ALERT"


class RuleEngine:
    """Pluggable, isolated rule evaluation engine."""

    def __init__(self, rules: Optional[List[Rule]] = None):
        """Initialize engine. If rules is None, auto-discover all rules from app.rules."""
        self.rules: List[Rule] = rules if rules is not None else load_rules()
        logger.info(f"Initialized RuleEngine with {len(self.rules)} rules: {[r.name for r in self.rules]}")

    def reload_rules(self, package: str = "app.rules"):
        """Reload all rules dynamically from the rules package."""
        self.rules = load_rules(package)

    def evaluate(self, txn: Transaction, db: Session) -> EngineEvaluation:
        """Evaluate a transaction against all enabled rules with strict isolation.
        
        Args:
            txn: The transaction to evaluate.
            db: Database session for context lookups.
            
        Returns:
            EngineEvaluation with final aggregated score, rule results, and decision.
        """
        # Load rule configs from database (or fall back to defaults)
        configs_query = db.query(RuleConfigModel).all()
        configs_by_name: Dict[str, RuleConfigModel] = {cfg.rule_name: cfg for cfg in configs_query}

        ctx = RuleContext(db=db, configs=configs_by_name)
        results: List[RuleResult] = []

        for rule in self.rules:
            cfg = configs_by_name.get(rule.name)
            
            # Skip disabled rules
            if cfg is not None and not cfg.enabled:
                logger.debug(f"Rule '{rule.name}' is disabled in configuration. Skipping.")
                continue

            # FR-2: Run each enabled rule inside try/except; one failing rule never breaks others
            try:
                result = rule.evaluate(txn, ctx)
                results.append(result)
            except Exception as ex:
                logger.error(f"Rule '{rule.name}' failed with unhandled exception: {ex}", exc_info=True)
                results.append(
                    RuleResult(
                        rule_name=rule.name,
                        triggered=False,
                        score=0,
                        reason=f"Rule evaluation error: {str(ex)}",
                        evidence={"error": str(ex), "status": "evaluation_exception"}
                    )
                )

        # FR-5: Aggregate score calculation
        # Formula: aggregate score = min(100, max(scores) + 0.25 * sum(other scores))
        # Factoring in rule weight when configured
        final_score = self._aggregate_scores(results, configs_by_name)

        flagged = final_score >= settings.FLAG_THRESHOLD
        high_risk = final_score >= settings.HIGH_RISK_THRESHOLD

        if high_risk:
            decision = "HIGH_RISK_ALERT"
        elif flagged:
            decision = "FLAGGED_FOR_REVIEW"
        else:
            decision = "ALLOW"

        return EngineEvaluation(
            score=final_score,
            rule_results=results,
            flagged=flagged,
            high_risk=high_risk,
            decision=decision
        )

    def _aggregate_scores(
        self,
        results: List[RuleResult],
        configs: Dict[str, RuleConfigModel]
    ) -> int:
        """Combine triggered rule scores using weighted max + residual sum capped at 100."""
        triggered_scores: List[float] = []

        for r in results:
            if r.triggered and r.score > 0:
                cfg = configs.get(r.rule_name)
                weight = cfg.weight if cfg else 1.0
                effective_score = r.score * weight
                triggered_scores.append(effective_score)

        if not triggered_scores:
            return 0

        # Sort descending
        triggered_scores.sort(reverse=True)
        max_score = triggered_scores[0]
        other_scores = triggered_scores[1:]

        aggregated = max_score + 0.25 * sum(other_scores)
        return min(100, max(0, int(round(aggregated))))
