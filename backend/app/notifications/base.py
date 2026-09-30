"""Notifier abstraction and notification payload."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List


@dataclass
class AlertPayload:
    transaction_id: str
    flag_id: int
    account_id: str
    amount: float
    currency: str
    merchant: str
    score: int
    triggered_rules: List[str]
    rule_reasons: List[str]
    console_link: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


class Notifier(ABC):
    """Abstract interface for dispatching high-risk fraud alerts."""

    @abstractmethod
    def send_alert(self, payload: AlertPayload) -> bool:
        """Send high-risk alert. Returns True if succeeded, False otherwise."""
        pass
