"""Rule 3: Impossible Geographical Location / Impossible Travel Rule."""
import logging
import math
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from app.engine.base import Rule, RuleResult
from app.engine.registry import register_rule

if TYPE_CHECKING:
    from app.engine.context import RuleContext
    from app.models import Transaction

logger = logging.getLogger(__name__)


def ensure_utc(dt: datetime) -> datetime:
    """Ensure datetime is timezone-aware in UTC to prevent naive/aware comparison issues."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points on Earth using Haversine formula."""
    r = 6371.0  # Earth radius in kilometers

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    return r * c


@register_rule
class ImpossibleTravelRule(Rule):
    """Detects physically impossible movement between sequential transactions.
    
    Trigger:
        Implied speed between prior transaction location and current transaction
        location exceeds velocity threshold V km/h (default 900 km/h, commercial jet).
    Score:
        90 if implied speed > 2 * V km/h (e.g. supersonic or instant teleportation),
        otherwise 70.
    Evidence:
        previous_location, current_location, distance_km, elapsed_hours, implied_speed_kmh.
    """
    name = "impossible_travel"
    weight = 1.0
    default_params = {
        "speed_limit_kmh": 900.0,
        "min_distance_km": 50.0  # Minimum distance to ignore micro-GPS jitter
    }

    def evaluate(self, txn: "Transaction", ctx: "RuleContext") -> RuleResult:
        # Check current transaction coordinates
        if txn.lat is None or txn.lon is None:
            return RuleResult(
                rule_name=self.name,
                triggered=False,
                score=0,
                reason="Current transaction missing geographic coordinates; evaluation skipped",
                evidence={"skipped": True, "reason": "missing_current_coordinates"}
            )

        speed_limit = float(ctx.get_rule_param(self.name, "speed_limit_kmh", self.default_params["speed_limit_kmh"]))
        min_distance = float(ctx.get_rule_param(self.name, "min_distance_km", self.default_params["min_distance_km"]))

        # Retrieve previous geotagged transaction
        prev_txn = ctx.get_last_geotagged_transaction(
            account_id=txn.account_id,
            before_time=txn.timestamp,
            exclude_id=txn.id
        )

        if not prev_txn:
            return RuleResult(
                rule_name=self.name,
                triggered=False,
                score=0,
                reason="No prior geotagged transaction found for baseline comparison",
                evidence={
                    "skipped": True,
                    "reason": "no_prior_geotagged_transaction",
                    "current_location": {
                        "lat": txn.lat,
                        "lon": txn.lon,
                        "country": txn.country
                    }
                }
            )

        # Calculate geographical distance
        distance_km = haversine_distance_km(prev_txn["lat"], prev_txn["lon"], txn.lat, txn.lon)

        # Ensure both datetimes are comparable timezone-aware UTC
        curr_time = ensure_utc(txn.timestamp)
        prev_time = ensure_utc(prev_txn["timestamp"])

        # Elapsed time in hours
        time_diff = curr_time - prev_time
        elapsed_seconds = max(1.0, time_diff.total_seconds())  # Prevent division by zero
        elapsed_hours = elapsed_seconds / 3600.0

        implied_speed = distance_km / elapsed_hours

        evidence = {
            "previous_location": {
                "id": prev_txn["id"],
                "lat": prev_txn["lat"],
                "lon": prev_txn["lon"],
                "country": prev_txn["country"],
                "merchant": prev_txn["merchant"],
                "timestamp": prev_time.isoformat()
            },
            "current_location": {
                "lat": txn.lat,
                "lon": txn.lon,
                "country": txn.country,
                "merchant": txn.merchant,
                "timestamp": curr_time.isoformat()
            },
            "distance_km": round(distance_km, 2),
            "elapsed_hours": round(elapsed_hours, 3),
            "elapsed_minutes": round(elapsed_seconds / 60.0, 1),
            "implied_speed_kmh": round(implied_speed, 1),
            "speed_limit_kmh": speed_limit
        }

        # Ignore tiny distance jitter under minimum threshold
        if distance_km < min_distance:
            return RuleResult(
                rule_name=self.name,
                triggered=False,
                score=0,
                reason=f"Distance ({distance_km:.1f} km) below GPS jitter threshold ({min_distance} km)",
                evidence=evidence
            )

        if implied_speed > speed_limit:
            # Score logic: 90 if speed > 2V, otherwise 70
            score = 90 if implied_speed > (2.0 * speed_limit) else 70
            reason = (
                f"Impossible travel: {distance_km:.1f} km traversed in {elapsed_hours:.2f}h "
                f"implies {implied_speed:.1f} km/h (exceeds {speed_limit:.0f} km/h threshold)"
            )
            return RuleResult(
                rule_name=self.name,
                triggered=True,
                score=score,
                reason=reason,
                evidence=evidence
            )

        return RuleResult(
            rule_name=self.name,
            triggered=False,
            score=0,
            reason=f"Travel speed feasible: {implied_speed:.1f} km/h <= {speed_limit:.0f} km/h limit",
            evidence=evidence
        )
