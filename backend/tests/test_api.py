"""Integration tests for all REST API endpoints."""
import pytest
from app.models import Transaction, FraudFlag, AuditLog


def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "velocity" in data["rules_registered"]
    assert "unusual_amount" in data["rules_registered"]
    assert "impossible_travel" in data["rules_registered"]


def test_post_transaction_normal(client):
    payload = {
        "account_id": "acc_norm_1",
        "amount": 25.50,
        "currency": "USD",
        "merchant": "Coffee Shop",
        "lat": 40.7128,
        "lon": -74.0060,
        "country": "US"
    }
    response = client.post("/api/transactions", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["risk_score"] == 0
    assert data["flagged"] is False
    assert data["high_risk"] is False
    assert data["decision"] == "ALLOW"
    assert data["flag_id"] is None
    assert len(data["rule_results"]) == 3


def test_post_transaction_high_risk_flagged(client):
    # First transaction in NYC
    t1 = {
        "account_id": "acc_high_risk",
        "amount": 50.0,
        "currency": "USD",
        "merchant": "Coffee Shop",
        "lat": 40.7128,
        "lon": -74.0060,
        "country": "US"
    }
    r1 = client.post("/api/transactions", json=t1)
    assert r1.status_code == 201

    # Second transaction in London 1 minute later -> Impossible travel triggers!
    t2 = {
        "account_id": "acc_high_risk",
        "amount": 80.0,
        "currency": "USD",
        "merchant": "London Jeweler",
        "lat": 51.5074,
        "lon": -0.1278,
        "country": "GB"
    }
    r2 = client.post("/api/transactions", json=t2)
    assert r2.status_code == 201
    data2 = r2.json()
    assert data2["risk_score"] >= 80
    assert data2["flagged"] is True
    assert data2["high_risk"] is True
    assert data2["decision"] == "HIGH_RISK_ALERT"
    assert data2["flag_id"] is not None


def test_flag_listing_and_filtering(client):
    # Ingest a flagged transaction
    t = {
        "account_id": "acc_filter_test",
        "amount": 8500.0,  # High amount trigger on new account
        "currency": "USD",
        "merchant": "Luxury Watch Boutique",
        "lat": 34.0522,
        "lon": -118.2437
    }
    r = client.post("/api/transactions", json=t)
    assert r.status_code == 201
    flag_id = r.json()["flag_id"]
    assert flag_id is not None

    # List flags
    res = client.get("/api/flags")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1
    assert any(item["id"] == flag_id for item in data["items"])

    # Filter by status PENDING
    res_pending = client.get("/api/flags?status=PENDING")
    assert res_pending.status_code == 200
    assert all(item["status"] == "PENDING" for item in res_pending.json()["items"])


def test_flag_detail_and_patch_status(client, db_session):
    # Ingest large amount transaction
    t = {
        "account_id": "acc_review_test",
        "amount": 7500.0,
        "currency": "USD",
        "merchant": "Gold Exchange",
        "lat": 34.0522,
        "lon": -118.2437
    }
    r = client.post("/api/transactions", json=t)
    flag_id = r.json()["flag_id"]

    # Get Flag Detail
    detail_res = client.get(f"/api/flags/{flag_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["flag"]["id"] == flag_id
    assert len(detail["rule_results"]) > 0

    # Mark as REVIEWED
    patch_res = client.patch(
        f"/api/flags/{flag_id}",
        json={"status": "REVIEWED", "note": "Customer verified via phone call", "reviewer": "alice@fraud.com"}
    )
    assert patch_res.status_code == 200
    updated = patch_res.json()
    assert updated["status"] == "REVIEWED"
    assert updated["reviewed_by"] == "alice@fraud.com"
    assert updated["review_note"] == "Customer verified via phone call"

    # Verify audit log was written
    audit = db_session.query(AuditLog).filter_by(entity_id=str(flag_id), action="STATUS_CHANGE_REVIEWED").first()
    assert audit is not None
    assert audit.actor == "alice@fraud.com"


def test_re_evaluate_endpoint(client):
    # Ingest normal
    t = {
        "account_id": "acc_reeval",
        "amount": 100.0,
        "merchant": "Store",
        "currency": "USD"
    }
    r = client.post("/api/transactions", json=t)
    txn_id = r.json()["transaction"]["id"]
    assert r.json()["risk_score"] == 0

    # Re-evaluate
    re_res = client.post(f"/api/transactions/{txn_id}/re-evaluate")
    assert re_res.status_code == 200
    assert re_res.json()["transaction"]["id"] == txn_id


def test_rule_config_get_and_put(client):
    # GET rules
    r = client.get("/api/rules")
    assert r.status_code == 200
    rules = r.json()
    assert len(rules) >= 3

    # PUT rule
    update_res = client.put(
        "/api/rules/velocity",
        json={"weight": 1.5, "params": {"max_count": 8, "window_minutes": 15}}
    )
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["weight"] == 1.5
    assert updated["params"]["max_count"] == 8


def test_dashboard_stats(client):
    res = client.get("/api/stats")
    assert res.status_code == 200
    stats = res.json()
    assert "total_transactions" in stats
    assert "pending_flags" in stats
    assert "rule_trigger_counts" in stats
