"""Pydantic request and response schemas."""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


# Rule Schemas
class RuleResultSchema(BaseModel):
    rule_name: str
    triggered: bool
    score: int = Field(ge=0, le=100)
    reason: str = ""
    evidence: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class RuleConfigSchema(BaseModel):
    rule_name: str
    enabled: bool
    params: Dict[str, Any]
    weight: float = 1.0
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class RuleConfigUpdate(BaseModel):
    enabled: Optional[bool] = None
    params: Optional[Dict[str, Any]] = None
    weight: Optional[float] = None


# Transaction Schemas
class TransactionCreate(BaseModel):
    id: Optional[str] = None
    account_id: str = Field(..., min_length=1, max_length=64)
    amount: float = Field(..., gt=0)
    currency: str = Field("USD", min_length=3, max_length=3)
    merchant: str = Field(..., min_length=1, max_length=128)
    lat: Optional[float] = Field(None, ge=-90.0, le=90.0)
    lon: Optional[float] = Field(None, ge=-180.0, le=180.0)
    country: Optional[str] = None
    timestamp: Optional[datetime] = None


class TransactionResponse(BaseModel):
    id: str
    account_id: str
    amount: float
    currency: str
    merchant: str
    lat: Optional[float]
    lon: Optional[float]
    country: Optional[str]
    timestamp: datetime
    risk_score: int
    created_at: datetime
    rule_results: List[RuleResultSchema] = []

    model_config = ConfigDict(from_attributes=True)


class TransactionEvaluationResponse(BaseModel):
    transaction: TransactionResponse
    risk_score: int
    flagged: bool
    high_risk: bool
    decision: str  # "ALLOW", "FLAGGED_FOR_REVIEW", "HIGH_RISK_ALERT"
    flag_id: Optional[int] = None
    rule_results: List[RuleResultSchema]


# Fraud Flag Schemas
class FraudFlagResponse(BaseModel):
    id: int
    transaction_id: str
    score: int
    status: str  # PENDING, REVIEWED, CLEARED
    notified_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_note: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    transaction: Optional[TransactionResponse] = None

    model_config = ConfigDict(from_attributes=True)


class FraudFlagUpdate(BaseModel):
    status: str = Field(..., pattern="^(REVIEWED|CLEARED|PENDING)$")
    note: Optional[str] = None
    reviewer: Optional[str] = "fraud_reviewer"


class PaginatedFlagsResponse(BaseModel):
    items: List[FraudFlagResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# Audit Log Schemas
class AuditLogResponse(BaseModel):
    id: int
    entity: str
    entity_id: str
    action: str
    actor: str
    payload: Dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Detailed Flag View
class FraudFlagDetailResponse(BaseModel):
    flag: FraudFlagResponse
    rule_results: List[RuleResultSchema]
    audit_logs: List[AuditLogResponse]


# Stats Schema
class FraudStatsResponse(BaseModel):
    total_transactions: int
    total_flagged: int
    pending_flags: int
    reviewed_flags: int
    cleared_flags: int
    high_risk_alerts_sent: int
    avg_risk_score: float
    rule_trigger_counts: Dict[str, int]
