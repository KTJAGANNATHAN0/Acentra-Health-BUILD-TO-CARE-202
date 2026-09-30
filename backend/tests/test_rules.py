"""Unit tests for individual fraud rules."""
from datetime import datetime, timedelta, timezone
import pytest
from app.engine.context import RuleContext
from app.models import Transaction, RuleConfigModel
from app.rules.velocity import VelocityRule
from app.rules.amount import UnusualAmountRule
from app.rules.geo import ImpossibleTravelRule, haversine_distance_km


def create_txn(db, account_id="acc_123", amount=100.0, lat=40.7128, lon=-74.0060, country="US", minutes_ago=0, txn_id=None):
    ts = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
    txn = Transaction(
        id=txn_id or f"txn_{account_id}_{minutes_ago}_{amount}",
        account_id=account_id,
        amount=amount,
        currency="USD",
        merchant="Test Merchant",
        lat=lat,
        lon=lon,
        country=country,
        timestamp=ts,
        risk_score=0
    )
    db.add(txn)
    db.commit()
    db.refresh(txn)
    return txn


class TestVelocityRule:
    """R1: Velocity Rule Tests"""

    def test_velocity_under_threshold(self, db_session):
        rule = VelocityRule()
        ctx = RuleContext(db_session)
        
        # 3 previous transactions in last 5 minutes
        for i in range(1, 4):
            create_txn(db_session, account_id="user_vel_1", amount=50.0, minutes_ago=i)
            
        current = create_txn(db_session, account_id="user_vel_1", amount=50.0, minutes_ago=0)
        res = rule.evaluate(current, ctx)
        
        assert res.triggered is False
        assert res.score == 0
        assert res.evidence["total_count"] == 4  # 3 prior + current = 4 <= 5

    def test_velocity_exactly_at_threshold(self, db_session):
        rule = VelocityRule()
        ctx = RuleContext(db_session)
        
        # 4 previous transactions + current = exactly 5
        for i in range(1, 5):
            create_txn(db_session, account_id="user_vel_2", amount=50.0, minutes_ago=i)
            
        current = create_txn(db_session, account_id="user_vel_2", amount=50.0, minutes_ago=0)
        res = rule.evaluate(current, ctx)
        
        assert res.triggered is False
        assert res.score == 0
        assert res.evidence["total_count"] == 5

    def test_velocity_exceeds_threshold(self, db_session):
        rule = VelocityRule()
        ctx = RuleContext(db_session)
        
        # 5 previous transactions + current = 6 (overage 1)
        for i in range(1, 6):
            create_txn(db_session, account_id="user_vel_3", amount=50.0, minutes_ago=i)
            
        current = create_txn(db_session, account_id="user_vel_3", amount=50.0, minutes_ago=0)
        res = rule.evaluate(current, ctx)
        
        assert res.triggered is True
        assert res.score == 40 + 15 * 1  # 55
        assert res.evidence["total_count"] == 6
        assert res.evidence["overage"] == 1

    def test_velocity_ignores_outside_window(self, db_session):
        rule = VelocityRule()
        ctx = RuleContext(db_session)
        
        # 10 transactions but 8 of them are 20+ minutes ago
        for i in range(15, 25):
            create_txn(db_session, account_id="user_vel_4", amount=50.0, minutes_ago=i)
            
        create_txn(db_session, account_id="user_vel_4", amount=50.0, minutes_ago=2)
        current = create_txn(db_session, account_id="user_vel_4", amount=50.0, minutes_ago=0)
        res = rule.evaluate(current, ctx)
        
        assert res.triggered is False
        assert res.evidence["total_count"] == 2


class TestAmountRule:
    """R2: Unusual Amount Rule Tests"""

    def test_thin_history_normal_amount(self, db_session):
        rule = UnusualAmountRule()
        ctx = RuleContext(db_session)
        
        # 2 transactions averaging $100
        create_txn(db_session, account_id="user_amt_1", amount=100.0, minutes_ago=200)
        create_txn(db_session, account_id="user_amt_1", amount=100.0, minutes_ago=100)
        
        # $150 is under 3x ($300)
        current = create_txn(db_session, account_id="user_amt_1", amount=150.0, minutes_ago=0)
        res = rule.evaluate(current, ctx)
        assert res.triggered is False

    def test_thin_history_spike_amount(self, db_session):
        rule = UnusualAmountRule()
        ctx = RuleContext(db_session)
        
        # 2 transactions averaging $100
        create_txn(db_session, account_id="user_amt_2", amount=100.0, minutes_ago=200)
        create_txn(db_session, account_id="user_amt_2", amount=100.0, minutes_ago=100)
        
        # $500 is 5x average
        current = create_txn(db_session, account_id="user_amt_2", amount=500.0, minutes_ago=0)
        res = rule.evaluate(current, ctx)
        assert res.triggered is True
        assert res.score >= 50
        assert res.evidence["mode"] == "thin_history_multiplier"
        assert res.evidence["ratio"] == 5.0

    def test_established_history_z_score_trigger(self, db_session):
        rule = UnusualAmountRule()
        ctx = RuleContext(db_session)
        
        # 10 prior transactions all around $100 (std ~ 2)
        for i in range(1, 11):
            create_txn(db_session, account_id="user_amt_3", amount=100.0 + (i % 3), minutes_ago=i * 60)
            
        # Current txn is $500 -> huge z-score
        current = create_txn(db_session, account_id="user_amt_3", amount=500.0, minutes_ago=0)
        res = rule.evaluate(current, ctx)
        assert res.triggered is True
        assert res.score >= 70
        assert res.evidence["z_score"] > 3.0

    def test_new_account_large_purchase(self, db_session):
        rule = UnusualAmountRule()
        ctx = RuleContext(db_session)
        
        current = create_txn(db_session, account_id="user_amt_new", amount=6500.0, minutes_ago=0)
        res = rule.evaluate(current, ctx)
        assert res.triggered is True
        assert res.evidence["mode"] == "new_account_threshold"


class TestImpossibleTravelRule:
    """R3: Impossible Travel Rule Tests"""

    def test_haversine_formula(self):
        # NYC (40.7128, -74.0060) to London (51.5074, -0.1278) ~ 5570 km
        dist = haversine_distance_km(40.7128, -74.0060, 51.5074, -0.1278)
        assert 5500 < dist < 5650

    def test_normal_commute_not_triggered(self, db_session):
        rule = ImpossibleTravelRule()
        ctx = RuleContext(db_session)
        
        # Prior txn in NYC 1 hour ago
        create_txn(db_session, account_id="user_geo_1", lat=40.7128, lon=-74.0060, country="US", minutes_ago=60)
        # Current txn in Newark (approx 15 km away)
        current = create_txn(db_session, account_id="user_geo_1", lat=40.7357, lon=-74.1724, country="US", minutes_ago=0)
        
        res = rule.evaluate(current, ctx)
        assert res.triggered is False

    def test_subsonic_commercial_flight_not_triggered(self, db_session):
        rule = ImpossibleTravelRule()
        ctx = RuleContext(db_session)
        
        # NYC to Chicago (~1150 km) in 3 hours -> ~383 km/h (< 900 km/h)
        create_txn(db_session, account_id="user_geo_2", lat=40.7128, lon=-74.0060, country="US", minutes_ago=180)
        current = create_txn(db_session, account_id="user_geo_2", lat=41.8781, lon=-87.6298, country="US", minutes_ago=0)
        
        res = rule.evaluate(current, ctx)
        assert res.triggered is False
        assert res.evidence["implied_speed_kmh"] < 900.0

    def test_impossible_travel_teleportation_triggered_high(self, db_session):
        rule = ImpossibleTravelRule()
        ctx = RuleContext(db_session)
        
        # NYC to London (~5570 km) in 15 minutes! Speed > 20,000 km/h (> 2 * 900)
        create_txn(db_session, account_id="user_geo_3", lat=40.7128, lon=-74.0060, country="US", minutes_ago=15)
        current = create_txn(db_session, account_id="user_geo_3", lat=51.5074, lon=-0.1278, country="GB", minutes_ago=0)
        
        res = rule.evaluate(current, ctx)
        assert res.triggered is True
        assert res.score == 90  # > 2 * V
        assert res.evidence["implied_speed_kmh"] > 1800.0

    def test_impossible_travel_moderate_triggered_70(self, db_session):
        rule = ImpossibleTravelRule()
        ctx = RuleContext(db_session)
        
        # NYC to London (~5570 km) in 5 hours -> ~1114 km/h (between 900 and 1800)
        create_txn(db_session, account_id="user_geo_4", lat=40.7128, lon=-74.0060, country="US", minutes_ago=300)
        current = create_txn(db_session, account_id="user_geo_4", lat=51.5074, lon=-0.1278, country="GB", minutes_ago=0)
        
        res = rule.evaluate(current, ctx)
        assert res.triggered is True
        assert res.score == 70  # > 900 and <= 1800

    def test_missing_coordinates_gracefully_skipped(self, db_session):
        rule = ImpossibleTravelRule()
        ctx = RuleContext(db_session)
        
        current = create_txn(db_session, account_id="user_geo_none", lat=None, lon=None, minutes_ago=0)
        res = rule.evaluate(current, ctx)
        assert res.triggered is False
        assert res.evidence.get("skipped") is True
