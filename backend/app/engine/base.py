"""Base classes and data structures for the Rule Engine."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from app.engine.context import RuleContext
    from app.models import Transaction


@dataclass
class RuleResult:
    """Represents the output of evaluating a single rule against a transaction."""
    rule_name: str
    triggered: bool
    score: int = 0  # 0 to 100
    reason: str = ""
    evidence: Dict[str, Any] = field(default_factory=dict)


class Rule(ABC):
    """Abstract base class for all fraud detection rules.
    
    Implementing classes must define `name` and implement `evaluate`.
    New rules can be registered using `@register_rule` without modifying
    the core engine.
    """
    name: str
    weight: float = 1.0
    default_params: Dict[str, Any] = {}

    @abstractmethod
    def evaluate(self, txn: "Transaction", ctx: "RuleContext") -> RuleResult:
        """Evaluate the rule against the transaction within the given context.
        
        Args:
            txn: The transaction being evaluated.
            ctx: History query interface and configuration context.
            
        Returns:
            RuleResult indicating if the rule triggered, score, reason and evidence.
        """
        pass
