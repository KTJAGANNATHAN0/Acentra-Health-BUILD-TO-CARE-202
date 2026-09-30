"""Test fixtures and database configuration."""
import os
import sys
from datetime import datetime, timezone
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# Ensure app is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db import Base, get_db
from app.main import app
from app.models import RuleConfigModel
from app.engine.registry import load_rules
from app.notifications.base import Notifier, AlertPayload

# StaticPool ensures in-memory SQLite tables are preserved across all threads/sessions
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


class MockNotifier(Notifier):
    """Captures alerts in-memory for assertion in tests."""
    def __init__(self):
        self.alerts: list[AlertPayload] = []

    def send_alert(self, payload: AlertPayload) -> bool:
        self.alerts.append(payload)
        return True


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    
    # Initialize rule configs
    rules = load_rules()
    for rule in rules:
        existing = session.query(RuleConfigModel).filter_by(rule_name=rule.name).first()
        if not existing:
            cfg = RuleConfigModel(
                rule_name=rule.name,
                enabled=True,
                params=rule.default_params,
                weight=rule.weight
            )
            session.add(cfg)
    session.commit()
    
    yield session
    
    session.close()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient with overridden get_db dependency."""
    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def mock_notifier():
    return MockNotifier()
