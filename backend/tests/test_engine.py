"""Tests for RuleEngine: aggregation, isolation, dynamic registration (FR-2, FR-4, FR-5)."""
import pytest
from app.engine.base import Rule, RuleResult
from app.engine.engine import RuleEngine
from app.engine.registry import register_rule, _REGISTRY
from app.models import Transaction, RuleConfigModel


class MockPassingRule(Rule):
    name = "mock_passing"
    def evaluate(self, txn, ctx):
        return RuleResult(rule_name=self.name, triggered=True, score=60, reason="Mock pass")


class MockSecondaryRule(Rule):
    name = "mock_secondary"
    def evaluate(self, txn, ctx):
        return RuleResult(rule_name=self.name, triggered=True, score=40, reason="Mock secondary")


class MockExplodingRule(Rule):
    name = "mock_exploding"
    def evaluate(self, txn, ctx):
        raise ZeroDivisionError("Simulated unexpected crash in third-party rule logic")


def test_score_aggregation_formula(db_session):
    """FR-5: Aggregate score = weighted combination, capped at 100: min(100, max(scores) + 0.25 * sum(others))."""
    engine = RuleEngine(rules=[MockPassingRule(), MockSecondaryRule()])
    txn = Transaction(id="t1", account_id="acc", amount=10, merchant="m", risk_score=0)
    db_session.add(txn)
    db_session.commit()

    evaluation = engine.evaluate(txn, db_session)
    # Expected: max is 60, other is 40 -> 60 + 0.25 * 40 = 70
    assert evaluation.score == 70
    assert evaluation.flagged is True  # 70 >= 50
    assert evaluation.high_risk is False  # 70 < 80
    assert evaluation.decision == "FLAGGED_FOR_REVIEW"


def test_rule_isolation_fault_tolerance(db_session):
    """FR-2: Rule engine runs all enabled rules independently; one failing rule never breaks the others."""
    engine = RuleEngine(rules=[MockPassingRule(), MockExplodingRule(), MockSecondaryRule()])
    txn = Transaction(id="t2", account_id="acc", amount=10, merchant="m", risk_score=0)
    db_session.add(txn)
    db_session.commit()

    evaluation = engine.evaluate(txn, db_session)
    
    # Engine must not raise ZeroDivisionError!
    assert len(evaluation.rule_results) == 3
    
    exploding_result = next(r for r in evaluation.rule_results if r.rule_name == "mock_exploding")
    assert exploding_result.triggered is False
    assert exploding_result.score == 0
    assert "Simulated unexpected crash" in exploding_result.evidence["error"]
    
    # The valid rules evaluated successfully and contributed to score
    assert evaluation.score == 70


def test_disabled_rule_skipped(db_session):
    """Rules disabled in DB configuration must be skipped."""
    engine = RuleEngine(rules=[MockPassingRule(), MockSecondaryRule()])
    
    # Disable MockPassingRule in DB
    cfg = RuleConfigModel(rule_name="mock_passing", enabled=False, params={}, weight=1.0)
    db_session.add(cfg)
    db_session.commit()

    txn = Transaction(id="t3", account_id="acc", amount=10, merchant="m", risk_score=0)
    db_session.add(txn)
    db_session.commit()

    evaluation = engine.evaluate(txn, db_session)
    # Only MockSecondaryRule ran
    assert len(evaluation.rule_results) == 1
    assert evaluation.rule_results[0].rule_name == "mock_secondary"
    assert evaluation.score == 40


def test_dynamic_rule_registration_open_closed_principle():
    """FR-4: New rule = new file/class + @register_rule; no edits to engine code."""
    initial_registry_count = len(_REGISTRY)

    @register_rule
    class BrandNewCustomRule(Rule):
        name = "brand_new_custom_rule"
        def evaluate(self, txn, ctx):
            return RuleResult(rule_name=self.name, triggered=True, score=99, reason="Custom detection")

    assert "brand_new_custom_rule" in _REGISTRY
    assert len(_REGISTRY) == initial_registry_count + 1

    # Instantiate fresh engine and verify the new rule is active without modifying engine.py!
    new_engine = RuleEngine()
    rule_names = [r.name for r in new_engine.rules]
    assert "brand_new_custom_rule" in rule_names
