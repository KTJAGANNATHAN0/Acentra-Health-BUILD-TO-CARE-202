"""Read-only history query context passed to rules during evaluation."""
from datetime import datetime, timedelta, timezone
import math
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Transaction, RuleConfigModel


class RuleContext:
    """Encapsulates read-only account history queries and rule parameter resolution.
    
    Provides high-performance, indexed queries to extract the necessary contextual
    signals (recent transaction volume, rolling statistical baseline, previous geo coordinate)
    strictly before the evaluated transaction timestamp to prevent lookahead leakage.
    """

    def __init__(self, db: Session, configs: Optional[Dict[str, RuleConfigModel]] = None):
        self.db = db
        self.configs = configs or {}

    def get_rule_param(self, rule_name: str, key: str, default: Any) -> Any:
        """Fetch custom parameter from rule configuration or return default."""
        config = self.configs.get(rule_name)
        if config and config.params and key in config.params:
            return config.params[key]
        return default

    def count_recent(
        self,
        account_id: str,
        minutes: int = 10,
        before_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Count transactions made by this account in the lookback window.
        
        Args:
            account_id: Account identifier.
            minutes: Lookback duration in minutes.
            before_time: Reference timestamp (defaults to now).
            
        Returns:
            Dict containing 'count' and 'transaction_ids'.
        """
        if before_time is None:
            before_time = datetime.now(timezone.utc)
            
        start_time = before_time - timedelta(minutes=minutes)
        
        query = (
            self.db.query(Transaction.id, Transaction.amount, Transaction.timestamp)
            .filter(
                Transaction.account_id == account_id,
                Transaction.timestamp >= start_time,
                Transaction.timestamp <= before_time
            )
            .order_by(Transaction.timestamp.desc())
        )
        
        rows = query.all()
        return {
            "count": len(rows),
            "window_minutes": minutes,
            "start_time": start_time.isoformat(),
            "end_time": before_time.isoformat(),
            "transaction_ids": [r[0] for r in rows],
            "recent_items": [{"id": r[0], "amount": r[1], "timestamp": r[2].isoformat()} for r in rows]
        }

    def get_history_stats(
        self,
        account_id: str,
        days: int = 30,
        before_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Compute rolling mean, standard deviation, and count for the account.
        
        Args:
            account_id: Account identifier.
            days: Lookback duration in days (default 30).
            before_time: Reference timestamp.
            
        Returns:
            Dict containing 'count', 'mean', 'std', and sample amounts.
        """
        if before_time is None:
            before_time = datetime.now(timezone.utc)
            
        start_time = before_time - timedelta(days=days)
        
        # Fetch amounts in lookback window
        query = (
            self.db.query(Transaction.amount)
            .filter(
                Transaction.account_id == account_id,
                Transaction.timestamp >= start_time,
                Transaction.timestamp < before_time  # strictly prior
            )
        )
        
        amounts = [r[0] for r in query.all()]
        count = len(amounts)
        
        if count == 0:
            return {
                "count": 0,
                "mean": 0.0,
                "std": 0.0,
                "min": 0.0,
                "max": 0.0,
                "days": days
            }
            
        mean = sum(amounts) / count
        
        if count > 1:
            variance = sum((x - mean) ** 2 for x in amounts) / (count - 1)
            std = math.sqrt(variance)
        else:
            std = 0.0
            
        return {
            "count": count,
            "mean": round(mean, 2),
            "std": round(std, 2),
            "min": round(min(amounts), 2),
            "max": round(max(amounts), 2),
            "days": days
        }

    def get_last_geotagged_transaction(
        self,
        account_id: str,
        before_time: Optional[datetime] = None,
        exclude_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Retrieve the most recent transaction with valid latitude/longitude.
        
        Args:
            account_id: Account identifier.
            before_time: Reference timestamp.
            exclude_id: Transaction ID to exclude (e.g. current if already inserted).
            
        Returns:
            Dict with lat, lon, country, timestamp, and id, or None if not found.
        """
        if before_time is None:
            before_time = datetime.now(timezone.utc)
            
        query = (
            self.db.query(Transaction)
            .filter(
                Transaction.account_id == account_id,
                Transaction.lat.isnot(None),
                Transaction.lon.isnot(None),
                Transaction.timestamp <= before_time
            )
        )
        
        if exclude_id:
            query = query.filter(Transaction.id != exclude_id)
            
        prev_txn = query.order_by(Transaction.timestamp.desc()).first()
        
        if not prev_txn:
            return None
            
        return {
            "id": prev_txn.id,
            "lat": prev_txn.lat,
            "lon": prev_txn.lon,
            "country": prev_txn.country,
            "merchant": prev_txn.merchant,
            "amount": prev_txn.amount,
            "timestamp": prev_txn.timestamp
        }
