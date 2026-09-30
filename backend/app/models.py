"""SQLAlchemy database models for the Fraud Rule Engine."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    Index
)
from sqlalchemy.orm import relationship
from app.db import Base


def utc_now():
    return datetime.now(timezone.utc)


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    account_id = Column(String(64), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    merchant = Column(String(128), nullable=False)
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    country = Column(String(64), nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=utc_now, index=True)
    risk_score = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    # Relationships
    rule_results = relationship("RuleResultModel", back_populates="transaction", cascade="all, delete-orphan")
    fraud_flag = relationship("FraudFlag", back_populates="transaction", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_txn_account_timestamp", "account_id", "timestamp"),
    )


class RuleResultModel(Base):
    __tablename__ = "rule_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String(36), ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_name = Column(String(64), nullable=False)
    triggered = Column(Boolean, nullable=False, default=False)
    score = Column(Integer, nullable=False, default=0)
    reason = Column(String(512), nullable=False, default="")
    evidence = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    transaction = relationship("Transaction", back_populates="rule_results")


class FraudFlag(Base):
    __tablename__ = "fraud_flags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    transaction_id = Column(String(36), ForeignKey("transactions.id", ondelete="CASCADE"), unique=True, nullable=False)
    score = Column(Integer, nullable=False, index=True)
    status = Column(String(20), nullable=False, default="PENDING", index=True)  # PENDING, REVIEWED, CLEARED
    notified_at = Column(DateTime(timezone=True), nullable=True)
    reviewed_by = Column(String(64), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_note = Column(String(1024), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)

    transaction = relationship("Transaction", back_populates="fraud_flag")

    __table_args__ = (
        Index("idx_flag_status_score", "status", "score"),
    )


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity = Column(String(64), nullable=False, index=True)
    entity_id = Column(String(64), nullable=False, index=True)
    action = Column(String(64), nullable=False)
    actor = Column(String(64), nullable=False, default="system")
    payload = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)


class RuleConfigModel(Base):
    __tablename__ = "rule_config"

    rule_name = Column(String(64), primary_key=True)
    enabled = Column(Boolean, nullable=False, default=True)
    params = Column(JSON, nullable=False, default=dict)
    weight = Column(Float, nullable=False, default=1.0)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)
