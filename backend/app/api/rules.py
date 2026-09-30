"""Rule configuration management API endpoints."""
import logging
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.engine.registry import get_registered_rules
from app.models import RuleConfigModel, AuditLog
from app.schemas import RuleConfigSchema, RuleConfigUpdate

router = APIRouter(prefix="/rules", tags=["Rules Configuration"])
logger = logging.getLogger(__name__)


@router.get("", response_model=List[RuleConfigSchema])
def list_rules(db: Session = Depends(get_db)):
    """FR-11: List all fraud rules and their dynamic configuration parameters."""
    registered = get_registered_rules()
    configs = {c.rule_name: c for c in db.query(RuleConfigModel).all()}

    results = []
    for name, rule_cls in registered.items():
        if name in configs:
            results.append(configs[name])
        else:
            # Create default entry if not in DB
            rule_inst = rule_cls()
            cfg = RuleConfigModel(
                rule_name=name,
                enabled=True,
                params=rule_inst.default_params,
                weight=rule_inst.weight
            )
            db.add(cfg)
            db.commit()
            db.refresh(cfg)
            results.append(cfg)

    return [RuleConfigSchema.model_validate(r) for r in results]


@router.put("/{rule_name}", response_model=RuleConfigSchema)
def update_rule_config(
    rule_name: str,
    payload: RuleConfigUpdate,
    db: Session = Depends(get_db)
):
    """FR-11: Update rule enabled state, weights, and detection thresholds."""
    cfg = db.query(RuleConfigModel).filter_by(rule_name=rule_name).first()
    if not cfg:
        # Check if registered rule
        registered = get_registered_rules()
        if rule_name not in registered:
            raise HTTPException(status_code=404, detail=f"Rule '{rule_name}' does not exist")
        rule_inst = registered[rule_name]()
        cfg = RuleConfigModel(
            rule_name=rule_name,
            enabled=True,
            params=rule_inst.default_params,
            weight=rule_inst.weight
        )
        db.add(cfg)

    changes = {}
    if payload.enabled is not None:
        changes["enabled"] = {"old": cfg.enabled, "new": payload.enabled}
        cfg.enabled = payload.enabled
    if payload.weight is not None:
        changes["weight"] = {"old": cfg.weight, "new": payload.weight}
        cfg.weight = payload.weight
    if payload.params is not None:
        changes["params"] = {"old": cfg.params, "new": payload.params}
        cfg.params = payload.params

    cfg.updated_at = datetime.now(timezone.utc)

    # Audit log
    audit = AuditLog(
        entity="rule_config",
        entity_id=rule_name,
        action="UPDATE_RULE_CONFIG",
        actor="admin",
        payload=changes
    )
    db.add(audit)
    db.commit()
    db.refresh(cfg)

    return RuleConfigSchema.model_validate(cfg)
